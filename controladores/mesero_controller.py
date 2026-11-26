from flask import Blueprint, abort, g, redirect, render_template, url_for

from controladores.comun import ejecutar, requiere, servicio

bp = Blueprint("mesero", __name__, url_prefix="/mesero")


@bp.route("/nuevo")
@requiere("MESERO")
def nuevo_pedido():
    return render_template("mesero/nuevo.html")


@bp.route("/mesas")
@requiere("MESERO")
def mesas():
    return render_template("mesero/mesas.html", mesas=servicio("mesas").listar())


@bp.route("/menu")
@requiere("MESERO")
def menu():
    return render_template("mesero/menu.html", productos=servicio("productos").listar())


@bp.route("/pedidos")
@requiere("MESERO")
def mis_pedidos():
    return render_template("mesero/mis_pedidos.html",
                           pedidos=servicio("pedidos").listar(id_mesero=g.usuario.id))


@bp.route("/pedidos/<int:id_>")
@requiere("MESERO")
def detalle(id_):
    p = servicio("pedidos").obtener(id_)
    if p["id_mesero"] != g.usuario.id:
        abort(403)
    return render_template("mesero/detalle.html", p=p)


@bp.route("/pedidos/<int:id_>/entregar", methods=["POST"])
@requiere("MESERO")
def entregar(id_):
    ejecutar(lambda: servicio("pedidos").entregar(id_, g.usuario), "Pedido Entregado")
    return redirect(url_for("mesero.detalle", id_=id_))
