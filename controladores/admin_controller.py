from flask import Blueprint, g, redirect, render_template, request, url_for

from controladores.comun import ejecutar, requiere, servicio

bp = Blueprint("admin", __name__, url_prefix="/admin")
solo_admin = requiere("ADMINISTRADOR")


@bp.route("/cancelaciones")
@solo_admin
def cancelaciones():
    return render_template("admin/cancelaciones.html",
                           pedidos=servicio("pedidos").listar(["RECIBIDO", "EN_PREPARACION", "LISTO"]))


# ---------- Menú (HU-8 y HU-12) ----------
@bp.route("/menu")
@solo_admin
def menu():
    return render_template("admin/menu.html",
                           productos=servicio("productos").listar(solo_activos=False))


@bp.route("/menu/nuevo", methods=["GET", "POST"], defaults={"id_": None})
@bp.route("/menu/<int:id_>", methods=["GET", "POST"])
@solo_admin
def producto(id_):
    s = servicio("productos")
    datos = dict(s.buscar(id_) or {}) if id_ is not None else {}
    if id_ is not None and not datos:
        return redirect(url_for("admin.menu"))
    if request.method == "POST":
        datos = request.form.to_dict()
        if id_ is not None:
            datos["id"] = id_
        if ejecutar(lambda: s.guardar(datos, nuevo=id_ is None)):
            return redirect(url_for("admin.menu"))
    categorias, presentaciones = s.opciones()
    return render_template("admin/producto.html", d=datos, id_=id_,
                           categorias=categorias, presentaciones=presentaciones)


@bp.route("/menu/<int:id_>/<campo>/<int:valor>", methods=["POST"])
@solo_admin
def cambiar_producto(id_, campo, valor):
    s = servicio("productos")
    if campo == "activo":
        ejecutar(lambda: s.cambiar_activo(id_, bool(valor)), "producto actualizado")
    elif campo == "disponible":
        ejecutar(lambda: s.cambiar_disponibilidad(id_, bool(valor)), "disponibilidad actualizada")
    return redirect(url_for("admin.menu"))


@bp.route("/categorias", methods=["POST"])
@solo_admin
def crear_categoria():
    ejecutar(lambda: servicio("productos").crear_categoria(request.form.get("nombre")),
             "categoría guardada")
    return redirect(url_for("admin.menu"))


# ---------- Usuarios y reportes ----------
@bp.route("/usuarios", methods=["GET", "POST"])
@solo_admin
def usuarios():
    s = servicio("auth")
    if request.method == "POST":
        f = request.form
        if ejecutar(lambda: s.crear_usuario(f.get("nombre"), f.get("username"),
                                            f.get("password"), f.get("rol")), "usuario guardado"):
            return redirect(url_for("admin.usuarios"))
    return render_template("admin/usuarios.html", usuarios=s.listar_usuarios())


@bp.route("/usuarios/<rol>/<int:id_>", methods=["POST"])
@solo_admin
def modificar_usuario(rol, id_):
    s = servicio("auth")
    if rol in ("MESERO", "COCINA", "ADMINISTRADOR"):
        if request.form.get("accion") == "clave":
            ejecutar(lambda: s.restablecer_clave(rol, id_, request.form.get("password")),
                     "contraseña actualizada")
        else:
            activo = request.form.get("accion") == "activar"
            ejecutar(lambda: s.cambiar_activo(rol, id_, activo, g.usuario), "usuario actualizado")
    return redirect(url_for("admin.usuarios"))
