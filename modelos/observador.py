"""PATRÓN OBSERVER: el gestor de pedidos avisa sin conocer a quién (CU-03, CU-06)."""
from abc import ABC, abstractmethod


class Observador(ABC):
    @abstractmethod
    def actualizar(self, con, evento: str, pedido) -> None:
        ...


class Sujeto:
    def __init__(self):
        self._observadores = []

    def suscribir(self, observador: Observador):
        self._observadores.append(observador)

    def notificar(self, con, evento, pedido):
        for o in self._observadores:
            o.actualizar(con, evento, pedido)
