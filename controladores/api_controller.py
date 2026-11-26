"""API REST / JSON que consumen los clientes web (ADR-004 y ADR-005)."""
from flask import Blueprint, jsonify

from controladores.comun import requiere

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/ping")
def ping():
    return jsonify(ok=True)


@bp.route("/cambios")
@requiere()
def cambios():
    # Versión temporal: se completa cuando exista el módulo de pedidos
    return jsonify(version=0, ultimo=0, avisos=[])
