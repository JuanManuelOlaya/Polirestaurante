import os
import tempfile
import unittest

from app import crear_app
from database.datos_iniciales import CLAVE_DEMO as CLAVE
from servicios.errores import ErrorNegocio


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = crear_app(os.path.join(self.tmp.name, "prueba.db"))
        s = self.app.extensions["servicios"]
        self.auth = s["auth"]
        # .get(): cada módulo se agrega en una fase distinta
        self.pedidos, self.pagos = s.get("pedidos"), s.get("pagos")
        self.productos, self.mesas = s.get("productos"), s.get("mesas")
        self.mesero = self.auth.autenticar("mesero1", CLAVE)
        self.cocina = self.auth.autenticar("cocina1", CLAVE)
        self.admin = self.auth.autenticar("admi2", CLAVE)

    def tearDown(self):
        self.tmp.cleanup()

    def falla(self, mensaje, funcion, *args, **kwargs):
        with self.assertRaises(ErrorNegocio) as c:
            funcion(*args, **kwargs)
        self.assertEqual(c.exception.mensaje, mensaje)

    def datos(self, **cambios):
        d = {"tipo_servicio": "SALON", "id_mesa": 4,
             "items": [{"id_producto": 1, "cantidad": 2, "nota": "Sin cebolla"},
                       {"id_producto": 2, "cantidad": 1, "nota": "Masa delgada"}]}
        d.update(cambios)
        return d

    def pedido(self, estado="RECIBIDO", **cambios):
        p = self.pedidos.crear_pedido(self.datos(**cambios), self.mesero)
        pasos = [("EN_PREPARACION", self.pedidos.iniciar_preparacion, self.cocina),
                 ("LISTO", self.pedidos.marcar_listo, self.cocina),
                 ("ENTREGADO", self.pedidos.entregar, self.mesero)]
        for destino, funcion, quien in pasos:
            if self.pedidos.obtener(p["id"])["estado"] == estado:
                break
            funcion(p["id"], quien)
        return self.pedidos.obtener(p["id"])

    def estado_mesa(self, n=4):
        return next(m["estado"] for m in self.mesas.listar() if m["numero"] == n)
