"""Observadores concretos del gestor de pedidos."""
from dao.pedido_dao import NotificacionDAO
from database.conexion import ahora
from modelos.observador import Observador


def destino(p):
    return f"Mesa {p['mesa_numero']:02d}" if p["mesa_numero"] else f"Para llevar · {p['cliente']}"


class AlertaMesero(Observador):
    MENSAJES = {
        "EN_PREPARACION": "Pedido #{id} en preparación ({destino})",
        "LISTO": "¡Pedido #{id} listo! {destino}",
        "DEVUELTO": "Pedido #{id} volvió a preparación ({destino})",
    }

    def __init__(self):
        self.dao = NotificacionDAO()

    def actualizar(self, con, evento, p):
        if evento in self.MENSAJES:
            texto = self.MENSAJES[evento].format(id=p["id"], destino=destino(p))
            if evento == "LISTO" and p["tipo_servicio"] == "LLEVAR":
                texto += " (entregar en mostrador)"
            self.dao.guardar(con, "MESERO", p["id_mesero"], texto, ahora())


class AlertaCocina(Observador):
    def __init__(self):
        self.dao = NotificacionDAO()

    def actualizar(self, con, evento, p):
        if evento == "CANCELADO":
            self.dao.guardar(con, "COCINA", None, f"El pedido #{p['id']} fue cancelado", ahora())
        elif evento == "RECIBIDO":
            self.dao.guardar(con, "COCINA", None, f"Nuevo pedido #{p['id']} · {destino(p)}", ahora())
