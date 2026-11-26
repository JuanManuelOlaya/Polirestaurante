import unittest

from database.datos_iniciales import CLAVE_DEMO as CLAVE
from tests.base import Base
from servicios.errores import ErrorNegocio
from servicios.pedido_service import validar_nota


class HU2Pedido(Base):
    def test_validaciones(self):
        crear = lambda **c: self.pedidos.crear_pedido(self.datos(**c), self.mesero)
        item = lambda **c: [{"id_producto": 5, "cantidad": 1, **c}]
        self.falla("tipo de servicio es obligatorio", crear, tipo_servicio=None)
        self.falla("mesa es obligatoria", crear, id_mesa=None)
        self.falla("nombre del cliente es obligatorio", crear, tipo_servicio="LLEVAR")
        self.falla("agregue al menos un producto", crear, items=[])
        self.falla("cantidad es numérico", crear, items=item(cantidad="aa"))
        self.falla("cantidad es numérico positivo", crear, items=item(cantidad=0))
        self.falla("producto agotado, quítelo o reemplácelo", crear, items=item(id_producto=6))
        self.assertEqual(self.estado_mesa(), "DISPONIBLE")

    def test_envio_mesa_ocupada_y_reintento(self):
        p = self.pedido(clave_envio="abc")
        self.assertEqual((p["estado"], p["total"], p["numero_llegada"]), ("RECIBIDO", 43000, 1))
        self.assertEqual(self.estado_mesa(), "OCUPADA")
        self.assertEqual(self.pedido(clave_envio="abc")["id"], p["id"])  # no duplica
        self.falla("mesa ocupada, confirme para continuar", self.pedidos.crear_pedido, self.datos(), self.mesero)
        self.assertTrue(self.pedidos.crear_pedido(self.datos(confirmar_ocupada=True), self.mesero))
        llevar = self.pedido(tipo_servicio="LLEVAR", id_mesa=None, nombre_cliente="Carlos")
        self.assertEqual(llevar["cliente"], "Carlos")


class HU8Productos(Base):
    def producto(self, i, nombre="aa", presentacion="1", unidades="5", precio="1000"):
        return self.productos.guardar({"id": i, "nombre": nombre, "id_presentacion": presentacion,
                                       "unidades": unidades, "precio": precio, "id_categoria": 1})

    def test_mazo(self):
        self.falla("id es numérico, presentación es numérico, unidades es numérico, precio es numérico",
                   self.producto, "aa", "aa", "aa", "aa", "aa")
        self.falla("unidades es numérico, precio es numérico", self.producto, "102", unidades="aa", precio="aa")
        self.falla("unidades es numérico positivo, precio es numérico positivo",
                   self.producto, "103", unidades="-5", precio="-5")
        self.assertEqual(self.producto("104"), "producto guardado")
        self.falla("nombre es obligatorio", self.producto, "105", nombre="")
        self.falla("precio es numérico positivo", self.producto, "106", precio="0")

    def test_precio_historico(self):
        p = self.pedido()
        self.productos.guardar({"id": 1, "nombre": "Nueva", "id_presentacion": 1, "unidades": 5,
                                "precio": 99999, "id_categoria": 1}, nuevo=False)
        self.productos.cambiar_activo(1, False)
        d = self.pedidos.obtener(p["id"])["detalles"][0]
        self.assertEqual((d["nombre_producto"], d["precio_unitario"]), ("Hamburguesa Angus", 12500))


class HU9Notas(unittest.TestCase):
    def test_mazo(self):
        for texto in ("Sin cebolla", "Masa delgada", "a" * 149, "a" * 150):
            self.assertEqual(validar_nota(texto), texto)
        for texto, msg in (("a" * 151, "nota supera los 150 caracteres, no se guardó"), ("", "nota es obligatoria")):
            with self.assertRaises(ErrorNegocio) as c:
                validar_nota(texto)
            self.assertEqual(c.exception.mensaje, msg)


class HU10Cancelar(Base):
    def cancelar(self, p, motivo="Error en el pedido", clave=CLAVE, confirmado=False):
        return self.pedidos.cancelar(p["id"], motivo, clave, self.mesero, confirmado)

    def test_recibido_y_listo(self):
        for estado in ("RECIBIDO", "LISTO"):
            self.assertEqual(self.cancelar(self.pedido(estado)), "pedido cancelado")
            self.assertEqual(self.estado_mesa(), "DISPONIBLE")

    def test_en_preparacion(self):
        p = self.pedido("EN_PREPARACION")
        self.falla("cocina ya inició la preparación, confirme para continuar", self.cancelar, p)
        self.assertEqual(self.cancelar(p, confirmado=True), "pedido cancelado")
        self.falla("pedido ya cancelado", self.cancelar, p)
        h = self.pedidos.historial(p["id"])[-1]
        self.assertEqual((h["motivo"], h["autorizado_por"]), ("Error en el pedido", "admin1"))

    def test_clave_incorrecta(self):
        p = self.pedido()
        for _ in range(2):
            self.falla("clave incorrecta, intente de nuevo", self.cancelar, p, clave="x")
        self.falla("clave incorrecta, acción bloqueada", self.cancelar, p, clave="x")
        self.falla("clave incorrecta, acción bloqueada", self.cancelar, p)
        self.assertEqual(self.pedidos.obtener(p["id"])["estado"], "RECIBIDO")

