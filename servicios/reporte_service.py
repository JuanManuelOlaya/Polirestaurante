from dao.pago_dao import PagoDAO


class ReporteService:
    def __init__(self, bd):
        self.bd = bd
        self.dao = PagoDAO()

    def ventas(self, desde, hasta):
        with self.bd.lectura() as con:
            metodos = self.dao.ventas_por_metodo(con, desde, hasta)
            productos = self.dao.productos_vendidos(con, desde, hasta)
        return metodos, productos, sum(m["total"] for m in metodos)
