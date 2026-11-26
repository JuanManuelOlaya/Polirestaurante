from flask import Blueprint, g, redirect, render_template, request, url_for

from controladores.comun import ejecutar, requiere, servicio

bp = Blueprint("admin", __name__, url_prefix="/admin")
solo_admin = requiere("ADMINISTRADOR")


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
