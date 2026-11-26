from dao.pago_dao import PagoDAO
from database.conexion import ahora
from modelos.pagos import ESTRATEGIAS, PagoRechazado
from servicios.errores import ErrorNegocio, entero, pesos


class PagoService:
    def __init__(self, bd, pedido_service, mesa_service):
        self.bd = bd
        self.pedidos = pedido_service
        self.mesas = mesa_service
        self.dao = PagoDAO()

    def calcular(self, total, pagos, dividido=False):
        """pagos: lista de {'metodo', 'valor', 'completado'}. No guarda nada."""
        if not pagos:
            raise ErrorNegocio("elija un método de pago")
        saldo, resultados = total, []
        for pago in pagos:
            estrategia = ESTRATEGIAS.get(pago.get("metodo"))
            if not estrategia:
                raise ErrorNegocio("elija un método de pago")
            if saldo == 0:
                raise ErrorNegocio("la cuenta ya está cubierta, quite el método adicional")
            if estrategia.codigo != "EFECTIVO" and not dividido:
                valor = total        # con tarjeta o Nequi el valor es el total
            else:
                texto = str(pago.get("valor") or "").replace("$", "").replace(".", "").strip()
                valor = entero(texto, "valor recibido")
            try:
                r = estrategia.procesar_pago(saldo, valor, pago.get("completado", True))
            except PagoRechazado as e:
                raise ErrorNegocio(str(e))
            saldo -= r.monto
            resultados.append(r)
        if saldo > 0:
            if dividido:
                raise ErrorNegocio(f"saldo pendiente {pesos(saldo)}, no se puede confirmar")
            raise ErrorNegocio(f"valor recibido es menor al total, faltan {pesos(saldo)}")
        return resultados

    def procesar_pago(self, id_pedido, pagos, administrador, dividido=False):
        with self.bd.transaccion() as con:
            p = self.pedidos._vigente(con, id_pedido)
            if p["estado"] != "ENTREGADO":
                raise ErrorNegocio("solo se pueden cobrar pedidos en estado Entregado")
            resultados = self.calcular(p["total"], pagos, dividido)
            for r in resultados:
                self.dao.registrar(con, id_pedido, r, ahora(), administrador.id)
            self.pedidos._cambiar(con, p, "PAGADO", administrador)
            self.mesas.liberar_si_corresponde(con, p["id_mesa"])
        cambio = sum(r.cambio for r in resultados)
        return f"pago registrado, cambio {pesos(cambio)}"

    def pagos_de(self, id_pedido):
        with self.bd.lectura() as con:
            return self.dao.obtener_por_pedido(con, id_pedido)
