"""PoliRestaurante - punto de entrada.  Ejecutar:  python app.py"""
import os
import secrets
import sys

from flask import Flask

import config
from controladores import admin_controller, api_controller, auth_controller
from controladores import cocina_controller, mesero_controller, pedido_controller
from controladores.comun import registrar_comunes
from database import datos_iniciales
from database.conexion import BaseDatos
from servicios.auth_service import AuthService
from servicios.mesa_service import MesaService
from servicios.pago_service import PagoService
from servicios.pedido_service import PedidoService
from servicios.producto_service import ProductoService
from servicios.reporte_service import ReporteService


def _clave_secreta(carpeta):
    ruta = os.path.join(carpeta, "clave_secreta")
    if not os.path.exists(ruta):
        with open(ruta, "w") as f:
            f.write(secrets.token_hex(32))
    with open(ruta) as f:
        return f.read()


def crear_app(ruta_bd=config.RUTA_BD):
    app = Flask(__name__, template_folder="vistas", static_folder="static")
    bd = BaseDatos(ruta_bd)
    bd.crear_esquema()
    datos_iniciales.cargar(bd)
    app.secret_key = _clave_secreta(os.path.dirname(os.path.abspath(ruta_bd)))
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

    mesas = MesaService(bd)
    pedidos = PedidoService(bd, mesas)
    app.extensions["servicios"] = {
        "auth": AuthService(bd), "mesas": mesas, "pedidos": pedidos,
        "productos": ProductoService(bd), "pagos": PagoService(bd, pedidos, mesas),
        "reportes": ReporteService(bd),
    }
    registrar_comunes(app)
    for modulo in (auth_controller, mesero_controller, cocina_controller,
                   admin_controller, pedido_controller, api_controller):
        app.register_blueprint(modulo.bp)
    return app


if __name__ == "__main__":
    puerto = int(os.environ.get("PUERTO", 5000))
    # --red permite entrar desde los celulares conectados al mismo WiFi
    host = "0.0.0.0" if "--red" in sys.argv else "127.0.0.1"
    crear_app().run(host=host, port=puerto, threaded=True)
