"""PATRÓN STRATEGY: una estrategia por método de pago (CU-05)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class PagoRechazado(Exception):
    pass


@dataclass
class ResultadoPago:
    metodo: str
    monto: int            # lo que abona a la cuenta
    valor_recibido: int
    cambio: int


class MetodoPagoStrategy(ABC):
    codigo = ""
    nombre = ""

    @abstractmethod
    def procesar_pago(self, saldo: int, valor: int, completado: bool) -> ResultadoPago:
        """saldo: lo que falta por pagar. valor: lo que entrega el cliente."""


class PagoEfectivoStrategy(MetodoPagoStrategy):
    codigo, nombre = "EFECTIVO", "Efectivo"

    def procesar_pago(self, saldo, valor, completado=True):
        monto = min(valor, saldo)
        return ResultadoPago(self.codigo, monto, valor, valor - monto)


class _PagoElectronico(MetodoPagoStrategy):
    def procesar_pago(self, saldo, valor, completado=True):
        if not completado:
            raise PagoRechazado("pago no completado, elija otro método")
        if valor > saldo:
            raise PagoRechazado(f"el valor con {self.nombre} no puede superar el saldo")
        return ResultadoPago(self.codigo, valor, valor, 0)


class PagoTarjetaStrategy(_PagoElectronico):
    codigo, nombre = "TARJETA", "Tarjeta"


class PagoNequiStrategy(_PagoElectronico):
    codigo, nombre = "NEQUI", "Nequi"


# Para aceptar un método nuevo basta crear su clase y agregarla aquí
# (y al CHECK de la tabla pago).
ESTRATEGIAS = {c.codigo: c() for c in (PagoEfectivoStrategy, PagoTarjetaStrategy, PagoNequiStrategy)}
