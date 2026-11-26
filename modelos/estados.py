"""PATRÓN STATE: cada estado conoce a cuáles puede pasar el pedido."""


class EstadoPedido:
    codigo = ""
    nombre = ""
    siguientes: tuple = ()
    mensaje_no_cancelable = ""

    def puede_pasar_a(self, destino: str) -> bool:
        return destino in self.siguientes

    @property
    def cancelable(self) -> bool:
        return self.puede_pasar_a("CANCELADO")

    @property
    def activo(self) -> bool:
        """Un pedido activo mantiene ocupada la mesa (no está pagado ni cancelado)."""
        return bool(self.siguientes)


class EstadoRecibido(EstadoPedido):
    codigo, nombre = "RECIBIDO", "Recibido"
    siguientes = ("EN_PREPARACION", "CANCELADO")


class EstadoEnPreparacion(EstadoPedido):
    codigo, nombre = "EN_PREPARACION", "En preparación"
    siguientes = ("LISTO", "CANCELADO")


class EstadoListo(EstadoPedido):
    codigo, nombre = "LISTO", "Listo"
    # Puede devolverse a preparación si se marcó por error (CU-03)
    siguientes = ("ENTREGADO", "EN_PREPARACION", "CANCELADO")


class EstadoEntregado(EstadoPedido):
    codigo, nombre = "ENTREGADO", "Entregado"
    siguientes = ("PAGADO",)
    mensaje_no_cancelable = "pedido entregado, no se puede cancelar"


class EstadoPagado(EstadoPedido):
    codigo, nombre = "PAGADO", "Pagado"
    mensaje_no_cancelable = "pedido pagado, no se puede cancelar"


class EstadoCancelado(EstadoPedido):
    codigo, nombre = "CANCELADO", "Cancelado"
    mensaje_no_cancelable = "pedido ya cancelado"


ESTADOS = {c.codigo: c() for c in (EstadoRecibido, EstadoEnPreparacion, EstadoListo,
                                   EstadoEntregado, EstadoPagado, EstadoCancelado)}
