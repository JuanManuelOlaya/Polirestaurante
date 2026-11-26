from database.datos_iniciales import CLAVE_DEMO as CLAVE
from tests.base import Base


class HU4Pagos(Base):
    def calcular(self, *pagos, dividido=False):
        return self.pagos.calcular(43000, [{"metodo": m, "valor": v} for m, v in pagos], dividido)

    def test_mazo(self):
        self.assertEqual(self.calcular(("EFECTIVO", "50000"))[0].cambio, 7000)
        self.assertEqual(self.calcular(("EFECTIVO", "43.000"))[0].cambio, 0)
        self.falla("valor recibido es menor al total, faltan $3.000", self.calcular, ("EFECTIVO", "40000"))
        self.falla("valor recibido es numérico", self.calcular, ("EFECTIVO", "aa"))
        self.falla("valor recibido es numérico positivo", self.calcular, ("EFECTIVO", "-5"))
        self.assertTrue(self.calcular(("TARJETA", None)))
        self.assertTrue(self.calcular(("NEQUI", None)))
        self.falla("pago no completado, elija otro método", self.pagos.calcular, 43000,
                   [{"metodo": "TARJETA", "completado": False}])
        self.assertEqual(len(self.calcular(("EFECTIVO", "20000"), ("TARJETA", "23000"), dividido=True)), 2)
        self.falla("saldo pendiente $23.000, no se puede confirmar", self.calcular, ("EFECTIVO", "20000"), dividido=True)

    def test_cobro_libera_mesa(self):
        p = self.pedido("ENTREGADO")
        msg = self.pagos.procesar_pago(p["id"], [{"metodo": "EFECTIVO", "valor": "50000"}], self.admin)
        self.assertEqual(msg, "pago registrado, cambio $7.000")
        self.assertEqual(self.pedidos.obtener(p["id"])["estado"], "PAGADO")
        self.assertEqual(self.estado_mesa(), "DISPONIBLE")
        self.assertEqual(self.app.extensions["servicios"]["reportes"].ventas("2000-01-01", "2999-01-01")[2], 43000)

    def test_mesa_con_otro_pedido_sigue_ocupada(self):
        p = self.pedido("ENTREGADO")
        self.pedido(confirmar_ocupada=True)
        self.pagos.procesar_pago(p["id"], [{"metodo": "NEQUI"}], self.admin)
        self.assertEqual(self.estado_mesa(), "OCUPADA")


class NoCancelables(Base):
    def cancelar(self, p, motivo="Error en el pedido"):
        return self.pedidos.cancelar(p["id"], motivo, CLAVE, self.mesero)

    def test_no_cancelables_y_motivo(self):
        p = self.pedido("ENTREGADO")
        self.falla("pedido entregado, no se puede cancelar", self.cancelar, p)
        self.pagos.procesar_pago(p["id"], [{"metodo": "TARJETA"}], self.admin)
        self.falla("pedido pagado, no se puede cancelar", self.cancelar, p)
        self.falla("motivo es obligatorio", self.cancelar, self.pedido(), motivo=" ")


class Web(Base):
    def test_paginas_roles_y_csrf(self):
        p = self.pedido("ENTREGADO")
        listo = self.pedido("LISTO", id_mesa=5)
        rutas = {
            "mesero1": ["/", "/mesero/nuevo", "/mesero/mesas", "/mesero/menu", "/mesero/pedidos",
                        f"/mesero/pedidos/{listo['id']}", f"/pedidos/{listo['id']}/cancelar"],
            "cocina1": ["/", "/cocina/", f"/cocina/pedidos/{listo['id']}"],
            "admi2": ["/", "/admin/caja", f"/admin/caja/{p['id']}", "/admin/cancelaciones", "/admin/menu",
                      "/admin/menu/nuevo", "/admin/menu/1", "/admin/usuarios", "/admin/reportes"],
        }
        for usuario, lista in rutas.items():
            c = self.app.test_client()
            c.get("/login")
            with c.session_transaction() as s:
                token = s["csrf"]
            self.assertEqual(c.post("/login", data={"usuario": usuario, "password": CLAVE, "csrf": token}).status_code, 302)
            for ruta in lista:
                self.assertEqual(c.get(ruta).status_code, 200, ruta)
            if usuario != "admi2":
                self.assertEqual(c.get("/admin/caja").status_code, 403)
            self.assertEqual(c.post("/api/pedidos", json={}).status_code, 400)  # sin token

