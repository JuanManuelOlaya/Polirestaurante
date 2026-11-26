from flask import Blueprint, g, redirect, render_template, request, url_for

from controladores.comun import ejecutar, requiere, servicio

bp = Blueprint("cocina", __name__, url_prefix="/cocina")


@bp.route("/")
@requiere("COCINA")
def pedidos():
    lista = servicio("pedidos").listar(["RECIBIDO", "EN_PREPARACION", "LISTO"])
    activos = sum(p["estado"] != "LISTO" for p in lista)
    return render_template("cocina/kds.html", pedidos=lista, activos=activos)


@bp.route("/pedidos/<int:id_>")
@requiere("COCINA")
def detalle(id_):
    return render_template("cocina/detalle.html", p=servicio("pedidos").obtener(id_))


@bp.route("/pedidos/<int:id_>/<accion>", methods=["POST"])
@requiere("COCINA")
def cambiar(id_, accion):
    s = servicio("pedidos")
    acciones = {
        "iniciar": (s.iniciar_preparacion, "Preparación iniciada"),
        "listo": (s.marcar_listo, "Pedido marcado como Listo"),
        "devolver": (s.devolver_a_preparacion, "Pedido devuelto a preparación"),
    }
    if accion in acciones:
        funcion, mensaje = acciones[accion]
        ejecutar(lambda: funcion(id_, g.usuario), mensaje)
    if request.form.get("volver") == "detalle":
        return redirect(url_for("cocina.detalle", id_=id_))
    return redirect(url_for("cocina.pedidos"))
