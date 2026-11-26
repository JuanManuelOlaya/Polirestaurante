from database.datos_iniciales import CLAVE_DEMO as CLAVE
from tests.base import Base


class CU03Y04(Base):
    def test_estados_y_avisos(self):
        desde = self.pedidos.cambios(self.mesero, None)["ultimo"]
        p = self.pedido("EN_PREPARACION")
        self.falla("Este pedido ya está siendo preparado", self.pedidos.iniciar_preparacion, p["id"], self.cocina)
        self.falla("no se puede entregar, el pedido está en estado En preparación",
                   self.pedidos.entregar, p["id"], self.mesero)
        self.pedidos.marcar_listo(p["id"], self.cocina)
        self.assertIn(f"¡Pedido #{p['id']} listo! Mesa 04", self.pedidos.cambios(self.mesero, desde)["avisos"])
        self.pedidos.devolver_a_preparacion(p["id"], self.cocina)
        self.pedidos.marcar_listo(p["id"], self.cocina)
        self.pedidos.entregar(p["id"], self.mesero)
        self.assertEqual(self.estado_mesa(), "OCUPADA")

