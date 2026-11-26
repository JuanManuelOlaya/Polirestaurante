from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

import config
from dao.usuario_dao import AccesoDAO, UsuarioDAO
from database.conexion import ahora
from modelos.entidades import Rol
from servicios.errores import ErrorNegocio


class ControlIntentos:
    """Bloqueo temporal tras 3 intentos fallidos (CU-01 y CU-06)."""

    def __init__(self):
        self.dao = AccesoDAO()

    def esta_bloqueado(self, con, clave):
        i = self.dao.obtener_intento(con, clave)
        if i and i["bloqueado_hasta"]:
            if i["bloqueado_hasta"] > ahora():
                return True
            self.dao.borrar_intento(con, clave)
        return False

    def fallar(self, con, clave):
        i = self.dao.obtener_intento(con, clave)
        n = (i["fallidos"] if i else 0) + 1
        hasta = None
        if n >= config.MAX_INTENTOS:
            fin = datetime.now() + timedelta(minutes=config.MINUTOS_BLOQUEO)
            hasta = fin.isoformat(sep=" ", timespec="seconds")
        self.dao.guardar_intento(con, clave, n, hasta)
        return n

    def limpiar(self, con, clave):
        self.dao.borrar_intento(con, clave)


class AuthService:
    def __init__(self, bd):
        self.bd = bd
        self.usuarios = UsuarioDAO()
        self.accesos = AccesoDAO()
        self.intentos = ControlIntentos()

    def autenticar(self, username, password):
        username = (username or "").strip()
        if not username:
            raise ErrorNegocio("usuario es obligatorio")
        if not password:
            raise ErrorNegocio("contraseña es obligatoria")
        if len(username) > 70:
            raise ErrorNegocio("usuario admite máximo 70 caracteres")
        clave = f"login:{username.lower()}"
        error = usuario = None
        # El error se lanza fuera de la transacción para que el intento quede guardado
        with self.bd.transaccion(avisar=False) as con:
            u = self.usuarios.buscar_por_username(con, username)
            if self.intentos.esta_bloqueado(con, clave):
                error, resultado = "cuenta bloqueada por intentos fallidos", "BLOQUEADO"
            elif not u or not check_password_hash(u.password, password):
                n = self.intentos.fallar(con, clave)
                resultado = "FALLIDO"
                error = ("cuenta bloqueada por intentos fallidos" if n >= config.MAX_INTENTOS
                         else f"usuario o contraseña incorrectos, intento {n} de {config.MAX_INTENTOS}")
            elif not u.activo:
                error, resultado = "cuenta inactiva, contacte al administrador", "INACTIVA"
            else:
                self.intentos.limpiar(con, clave)
                usuario, resultado = u, "EXITOSO"
            self.accesos.registrar(con, username, resultado, ahora())
        if error:
            raise ErrorNegocio(error)
        return usuario

    def usuario_vigente(self, rol, id_):
        with self.bd.lectura() as con:
            u = self.usuarios.buscar_por_id(con, rol, id_)
        return u if u and u.activo else None

    # ----- Gestión de usuarios (BPMN de administración) -----
    def listar_usuarios(self):
        with self.bd.lectura() as con:
            return self.usuarios.listar(con)

    @staticmethod
    def _validar_clave(password):
        if len(password or "") < config.MIN_CLAVE:
            raise ErrorNegocio(f"la contraseña debe tener mínimo {config.MIN_CLAVE} caracteres")

    def crear_usuario(self, nombre, username, password, rol):
        nombre, username = (nombre or "").strip(), (username or "").strip()
        if not nombre or not username:
            raise ErrorNegocio("nombre y usuario son obligatorios")
        if len(username) > 70:
            raise ErrorNegocio("usuario admite máximo 70 caracteres")
        if rol not in [r.value for r in Rol]:
            raise ErrorNegocio("rol no válido")
        self._validar_clave(password)
        with self.bd.transaccion() as con:
            if self.usuarios.buscar_por_username(con, username):
                raise ErrorNegocio("el usuario ya existe")
            self.usuarios.insertar(con, Rol(rol), nombre, username, generate_password_hash(password))

    def cambiar_activo(self, rol, id_, activo, actual):
        if not activo and Rol(rol) == actual.rol and id_ == actual.id:
            raise ErrorNegocio("no puede desactivar su propia cuenta")
        with self.bd.transaccion() as con:
            self.usuarios.cambiar_activo(con, Rol(rol), id_, activo)

    def restablecer_clave(self, rol, id_, password):
        self._validar_clave(password)
        with self.bd.transaccion() as con:
            u = self.usuarios.buscar_por_id(con, rol, id_)
            if not u:
                raise ErrorNegocio("usuario no encontrado")
            self.usuarios.cambiar_password(con, Rol(rol), id_, generate_password_hash(password))
            self.intentos.limpiar(con, f"login:{u.username.lower()}")
