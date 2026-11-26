"""CU-06: lo solicita el mesero (o el administrador) y lo autoriza la clave del administrador."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from controladores.comun import requiere, servicio
from modelos.estados import ESTADOS
from servicios.errores import ErrorNegocio

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _pedido_permitido(id_):
    p = servicio("pedidos").obtener(id_)
    if g.usuario.rol.value == "MESERO" and p["id_mesero"] != g.usuario.id:
        abort(403)
    return p


def _volver(id_):
    if g.usuario.rol.value == "MESERO":
        return url_for("mesero.detalle", id_=id_)
    return url_for("admin.cancelaciones")


@bp.route("/<int:id_>/cancelar", methods=["GET", "POST"])
@requiere("MESERO", "ADMINISTRADOR")
def cancelar(id_):
    p = _pedido_permitido(id_)
    if not ESTADOS[p["estado"]].cancelable:
        flash(ESTADOS[p["estado"]].mensaje_no_cancelable, "error")
        return redirect(_volver(id_))
    motivo = request.form.get("motivo", "").strip()
    if request.method == "POST":
        confirmado = request.form.get("confirmado") == "1"
        try:
            p = servicio("pedidos").validar_cancelacion(id_, motivo, confirmado)
        except ErrorNegocio as e:
            flash(e.mensaje, "error")
        else:
            return render_template("autorizacion.html", p=p, motivo=motivo,
                                   confirmado=confirmado, volver=_volver(id_))
    return render_template("cancelar.html", p=p, motivo=motivo, volver=_volver(id_))


@bp.route("/<int:id_>/autorizar", methods=["POST"])
@requiere("MESERO", "ADMINISTRADOR")
def autorizar(id_):
    _pedido_permitido(id_)
    motivo = request.form.get("motivo", "")
    confirmado = request.form.get("confirmado") == "1"
    try:
        mensaje = servicio("pedidos").cancelar(id_, motivo, request.form.get("clave", ""),
                                               g.usuario, confirmado)
    except ErrorNegocio as e:
        flash(e.mensaje, "error")
        p = servicio("pedidos").obtener(id_)
        if e.codigo == "CONFIRMAR":
            return render_template("cancelar.html", p=p, motivo=motivo, volver=_volver(id_))
        if not ESTADOS[p["estado"]].cancelable:
            return redirect(_volver(id_))
        return render_template("autorizacion.html", p=p, motivo=motivo,
                               confirmado=confirmado, volver=_volver(id_))
    flash(mensaje, "ok")
    return redirect(_volver(id_))
