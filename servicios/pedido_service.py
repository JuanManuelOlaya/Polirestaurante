from werkzeug.security import check_password_hash

import config
from dao.mesa_dao import MesaDAO
from dao.pedido_dao import ClienteDAO, NotificacionDAO, PedidoDAO
from dao.producto_dao import ProductoDAO
from dao.usuario_dao import UsuarioDAO
from database.conexion import ahora
from modelos.estados import ESTADOS
from modelos.observador import Sujeto
from servicios.auth_service import ControlIntentos
from servicios.errores import ErrorNegocio, entero
from servicios.notificaciones import AlertaCocina, AlertaMesero

ACTIVOS = [c for c, e in ESTADOS.items() if e.activo]


def validar_nota(nota):
    """HU-9: guardar una nota individual."""
    nota = (nota or "").strip()
    if not nota:
        raise ErrorNegocio("nota es obligatoria")
    if len(nota) > config.MAX_NOTA:
        raise ErrorNegocio(f"nota supera los {config.MAX_NOTA} caracteres, no se guardó")
    return nota


class PedidoService(Sujeto):
    def __init__(self, bd, mesa_service):
        super().__init__()
        self.bd = bd
        self.mesas = mesa_service
        self.dao = PedidoDAO()
        self.mesa_dao = MesaDAO()
        self.productos = ProductoDAO()
        self.clientes = ClienteDAO()
        self.usuarios = UsuarioDAO()
        self.notificaciones = NotificacionDAO()
        self.intentos = ControlIntentos()
        self.suscribir(AlertaMesero())
        self.suscribir(AlertaCocina())

    # ---------- Consultas ----------
    def obtener(self, id_):
        with self.bd.lectura() as con:
            p = self.dao.buscar_por_id(con, id_)
        if not p:
            raise ErrorNegocio("pedido no encontrado", "NO_EXISTE")
        return p

    def historial(self, id_):
        with self.bd.lectura() as con:
            return self.dao.historial(con, id_)

    def listar(self, estados=ACTIVOS, id_mesero=None):
        with self.bd.lectura() as con:
            return self.dao.listar(con, estados, id_mesero)

    def cambios(self, usuario, desde):
        """ADR-005: respuesta liviana para el polling."""
        with self.bd.lectura() as con:
            version = con.execute("SELECT numero FROM version").fetchone()[0]
            if desde is None:
                return {"version": version, "ultimo": self.notificaciones.ultimo_id(con), "avisos": []}
            avisos = self.notificaciones.nuevas(con, usuario.rol.value, usuario.id, desde)
        return {"version": version, "ultimo": avisos[-1]["id"] if avisos else desde,
                "avisos": [a["mensaje"] for a in avisos]}

    # ---------- CU-02: registrar y enviar a cocina ----------
    def crear_pedido(self, datos, mesero):
        tipo = datos.get("tipo_servicio")
        if tipo not in ("SALON", "LLEVAR"):
            raise ErrorNegocio("tipo de servicio es obligatorio")
        cliente = str(datos.get("nombre_cliente") or "").strip()[:70]
        id_mesa = None
        if tipo == "SALON":
            if not datos.get("id_mesa"):
                raise ErrorNegocio("mesa es obligatoria")
            id_mesa = entero(datos["id_mesa"], "mesa")
        elif not cliente:
            raise ErrorNegocio("nombre del cliente es obligatorio")
        items = datos.get("items") or []
        if not isinstance(items, list) or not items:
            raise ErrorNegocio("agregue al menos un producto")
        general = str(datos.get("nota_general") or "").strip()
        if len(general) > config.MAX_NOTA_GENERAL:
            raise ErrorNegocio(f"la nota general supera los {config.MAX_NOTA_GENERAL} caracteres")
        clave = str(datos.get("clave_envio") or "")[:64] or None

        with self.bd.transaccion() as con:
            if clave:
                previo = self.dao.buscar_por_clave_envio(con, clave)
                if previo:                       # reintento de un envío ya guardado
                    if previo["id_mesero"] != mesero.id:
                        raise ErrorNegocio("envío no válido")
                    return previo
            if id_mesa:
                mesa = self.mesa_dao.buscar(con, id_mesa)
                if not mesa:
                    raise ErrorNegocio("la mesa no existe")
                if mesa["estado"] == "OCUPADA" and datos.get("confirmar_ocupada") is not True:
                    raise ErrorNegocio("mesa ocupada, confirme para continuar", "MESA_OCUPADA")

            lineas, pedidas, agotados = [], {}, []
            for item in items:
                if not isinstance(item, dict):
                    raise ErrorNegocio("producto no válido")
                id_producto = entero(item.get("id_producto"), "producto")
                cantidad = entero(item.get("cantidad"), "cantidad")
                nota = str(item.get("nota") or "").strip()
                if nota:
                    nota = validar_nota(nota)
                p = self.productos.buscar(con, id_producto)
                if not p:
                    raise ErrorNegocio("producto no válido")
                pedidas[id_producto] = pedidas.get(id_producto, 0) + cantidad
                if not p["activo"] or not p["disponible"] or p["unidades"] < pedidas[id_producto]:
                    agotados.append(id_producto)
                lineas.append({"id_producto": id_producto, "nombre": p["nombre"],
                               "precio": p["precio"], "cantidad": cantidad, "nota": nota})
            if agotados:
                raise ErrorNegocio("producto agotado, quítelo o reemplácelo", "AGOTADO",
                                   productos=agotados)

            fecha = ahora()
            id_pedido = self.dao.guardar(con, {
                "numero_llegada": self.dao.siguiente_numero(con), "clave_envio": clave,
                "tipo_servicio": tipo, "id_mesa": id_mesa,
                "id_cliente": self.clientes.guardar(con, cliente, fecha) if tipo == "LLEVAR" else None,
                "id_mesero": mesero.id, "estado": "RECIBIDO", "nota_general": general,
                "total": sum(l["precio"] * l["cantidad"] for l in lineas), "fecha_creacion": fecha})
            for linea in lineas:
                self.dao.guardar_detalle(con, id_pedido, linea)
                self.productos.mover_unidades(con, linea["id_producto"], -linea["cantidad"])
            if id_mesa:
                self.mesas.asignar(con, id_mesa)
            self.dao.agregar_historial(con, id_pedido, "RECIBIDO", mesero.username, fecha)
            pedido = self.dao.buscar_por_id(con, id_pedido)
            self.notificar(con, "RECIBIDO", pedido)
        return pedido

    # ---------- Cambios de estado ----------
    def _vigente(self, con, id_):
        p = self.dao.buscar_por_id(con, id_)
        if not p:
            raise ErrorNegocio("pedido no encontrado", "NO_EXISTE")
        return p

    def _cambiar(self, con, pedido, destino, usuario, evento=None, **extra):
        if not ESTADOS[pedido["estado"]].puede_pasar_a(destino):
            actual = ESTADOS[pedido["estado"]].nombre
            raise ErrorNegocio(f"acción no permitida, el pedido está en estado {actual}")
        self.dao.actualizar(con, pedido["id"], estado=destino, **extra)
        self.dao.agregar_historial(con, pedido["id"], destino, usuario.username, ahora())
        self.notificar(con, evento or destino, self.dao.buscar_por_id(con, pedido["id"]))

    def iniciar_preparacion(self, id_, cocinero):
        with self.bd.transaccion() as con:
            p = self._vigente(con, id_)
            if p["estado"] == "CANCELADO":
                raise ErrorNegocio(f"El pedido #{id_} fue cancelado")
            if p["estado"] != "RECIBIDO":
                raise ErrorNegocio("Este pedido ya está siendo preparado")
            self._cambiar(con, p, "EN_PREPARACION", cocinero,
                          id_cocinero=cocinero.id, hora_inicio=ahora())

    def marcar_listo(self, id_, cocinero):
        with self.bd.transaccion() as con:
            p = self._vigente(con, id_)
            if p["estado"] == "CANCELADO":
                raise ErrorNegocio(f"El pedido #{id_} fue cancelado")
            if p["estado"] == "EN_PREPARACION" and p["id_cocinero"] != cocinero.id:
                raise ErrorNegocio("Este pedido ya está siendo preparado")
            self._cambiar(con, p, "LISTO", cocinero, hora_listo=ahora())

    def devolver_a_preparacion(self, id_, cocinero):
        with self.bd.transaccion() as con:
            p = self._vigente(con, id_)
            if p["estado"] != "LISTO":
                raise ErrorNegocio(f"el pedido está en estado {ESTADOS[p['estado']].nombre}")
            self._cambiar(con, p, "EN_PREPARACION", cocinero, evento="DEVUELTO",
                          id_cocinero=cocinero.id, hora_listo=None)

    def entregar(self, id_, mesero):
        """CU-04. La mesa sigue ocupada hasta el pago."""
        with self.bd.transaccion() as con:
            p = self._vigente(con, id_)
            if p["id_mesero"] != mesero.id:
                raise ErrorNegocio("el pedido pertenece a otro mesero")
            if p["estado"] != "LISTO":
                raise ErrorNegocio("no se puede entregar, el pedido está en estado "
                                   f"{ESTADOS[p['estado']].nombre}")
            self._cambiar(con, p, "ENTREGADO", mesero, hora_entrega=ahora())

    # ---------- CU-06: cancelar con autorización ----------
    def validar_cancelacion(self, id_, motivo, confirmado):
        p = self.obtener(id_)
        self._reglas_cancelacion(p, motivo, confirmado)
        return p

    @staticmethod
    def _reglas_cancelacion(p, motivo, confirmado):
        estado = ESTADOS[p["estado"]]
        if not estado.cancelable:
            raise ErrorNegocio(estado.mensaje_no_cancelable)
        if not (motivo or "").strip():
            raise ErrorNegocio("motivo es obligatorio")
        if len(motivo.strip()) > config.MAX_MOTIVO:
            raise ErrorNegocio(f"el motivo supera los {config.MAX_MOTIVO} caracteres")
        if p["estado"] == "EN_PREPARACION" and not confirmado:
            raise ErrorNegocio("cocina ya inició la preparación, confirme para continuar",
                               "CONFIRMAR")

    def cancelar(self, id_, motivo, clave_admin, solicitante, confirmado=False):
        error = None
        llave = f"cancelar:{solicitante.rol.value}:{solicitante.id}"
        with self.bd.transaccion() as con:
            p = self._vigente(con, id_)
            if solicitante.rol.value == "MESERO" and p["id_mesero"] != solicitante.id:
                raise ErrorNegocio("el pedido pertenece a otro mesero")
            self._reglas_cancelacion(p, motivo, confirmado)
            autoriza = None
            if self.intentos.esta_bloqueado(con, llave):
                error = "clave incorrecta, acción bloqueada"
            else:
                autoriza = next((a for a in self.usuarios.administradores_activos(con)
                                 if check_password_hash(a.password, clave_admin or "")), None)
                if not autoriza:
                    n = self.intentos.fallar(con, llave)
                    error = ("clave incorrecta, acción bloqueada" if n >= config.MAX_INTENTOS
                             else "clave incorrecta, intente de nuevo")
                    self.dao.agregar_historial(con, id_, "INTENTO_CANCELACION_FALLIDO",
                                               solicitante.username, ahora(), motivo.strip())
            if autoriza:
                self.intentos.limpiar(con, llave)
                self.dao.actualizar(con, id_, estado="CANCELADO")
                self.dao.agregar_historial(con, id_, "CANCELADO", solicitante.username, ahora(),
                                           motivo.strip(), autoriza.username)
                # Las unidades regresan solo si cocina no había empezado
                if p["estado"] == "RECIBIDO":
                    for d in p["detalles"]:
                        self.productos.mover_unidades(con, d["id_producto"], d["cantidad"])
                self.mesas.liberar_si_corresponde(con, p["id_mesa"])
                self.notificar(con, "CANCELADO", p)
        if error:   # fuera de la transacción: el intento fallido queda registrado
            raise ErrorNegocio(error)
        return "pedido cancelado"
