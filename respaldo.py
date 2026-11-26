"""Copia de seguridad de la base de datos (diagrama de despliegue).
Programar con el Programador de tareas de Windows o con cron."""
import os
import sqlite3
from datetime import datetime

import config

if __name__ == "__main__":
    if not os.path.exists(config.RUTA_BD):
        raise SystemExit("Aún no existe la base de datos. Ejecute primero: python app.py")
    carpeta = os.path.join(config.BASE, "respaldos")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, f"polirestaurante_{datetime.now():%Y%m%d_%H%M%S}.db")
    origen, copia = sqlite3.connect(config.RUTA_BD), sqlite3.connect(destino)
    origen.backup(copia)
    origen.close()
    copia.close()
    print("Respaldo creado:", destino)
