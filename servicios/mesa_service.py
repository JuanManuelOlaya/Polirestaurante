from dao.mesa_dao import MesaDAO


class MesaService:
    def __init__(self, bd):
        self.bd = bd
        self.dao = MesaDAO()

    def listar(self):
        with self.bd.lectura() as con:
            return self.dao.listar(con)

    def asignar(self, con, id_mesa):
        self.dao.actualizar_estado(con, id_mesa, "OCUPADA")

    def liberar_si_corresponde(self, con, id_mesa):
        """Solo se libera si no quedan pedidos sin pagar (CU-05 y CU-06)."""
        if id_mesa and not self.dao.tiene_pedidos_activos(con, id_mesa):
            self.dao.actualizar_estado(con, id_mesa, "DISPONIBLE")
