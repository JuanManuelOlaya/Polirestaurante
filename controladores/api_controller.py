"""API REST / JSON que consumen los clientes web (ADR-004 y ADR-005)."""
from flask import Blueprint, g, jsonify, request

from controladores.comun import requiere, servicio
from servicios.pedido_service import validar_nota

bp = Blueprint("api", __name__, url_prefix="/api")


def _cuerpo():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


@bp.route("/ping")
def ping():
    return jsonify(ok=True)


@bp.route("/cambios")
@requiere()
def cambios():
    return jsonify(servicio("pedidos").cambios(g.usuario, request.args.get("desde", type=int)))


@bp.route("/productos")
@requiere("MESERO")
def productos():
    return jsonify([{k: p[k] for k in ("id", "nombre", "categoria", "precio", "unidades", "agotado")}
                    for p in servicio("productos").listar()])


@bp.route("/mesas")
@requiere("MESERO")
def mesas():
    return jsonify([dict(m) for m in servicio("mesas").listar()])


@bp.route("/notas/validar", methods=["POST"])
@requiere("MESERO")
def nota():
    return jsonify(nota=validar_nota(str(_cuerpo().get("nota") or "")), mensaje="nota guardada")


@bp.route("/pedidos", methods=["POST"])
@requiere("MESERO")
def crear_pedido():
    p = servicio("pedidos").crear_pedido(_cuerpo(), g.usuario)
    return jsonify(id=p["id"], numero_llegada=p["numero_llegada"], total=p["total"],
                   mensaje="pedido enviado a cocina"), 201
