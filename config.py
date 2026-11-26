"""Parámetros generales del sistema."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(BASE, "instance", "polirestaurante.db")

MAX_INTENTOS = 3          # CU-01 y CU-06
MINUTOS_BLOQUEO = 5       # Supuesto: el documento dice "por un tiempo"
MAX_NOTA = 150            # HU-9
MAX_NOTA_GENERAL = 200
MAX_MOTIVO = 200          # Mockup CU-06
MIN_CLAVE = 8             # Mockup CU-01 / ADR-006
