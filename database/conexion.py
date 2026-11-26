"""Conexión a la base de datos relacional y manejo de transacciones (ADR-003)."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime


def ahora() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


class BaseDatos:
    def __init__(self, ruta: str):
        self.ruta = ruta
        os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)

    def _conectar(self):
        con = sqlite3.connect(self.ruta, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    @contextmanager
    def lectura(self):
        con = self._conectar()
        try:
            yield con
        finally:
            con.close()

    @contextmanager
    def transaccion(self, avisar=True):
        """Todo o nada. Bloquea otras escrituras mientras se valida y guarda."""
        con = self._conectar()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            if avisar:
                con.execute("UPDATE version SET numero = numero + 1")
            con.execute("COMMIT")
        except BaseException:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def crear_esquema(self):
        ruta_sql = os.path.join(os.path.dirname(__file__), "esquema.sql")
        con = self._conectar()
        with open(ruta_sql, encoding="utf-8") as f:
            con.executescript(f.read())
        con.close()
