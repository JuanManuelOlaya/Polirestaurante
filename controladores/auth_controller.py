from flask import Blueprint, g, redirect, render_template, request, session, url_for

from controladores.comun import requiere, servicio
from servicios.errores import ErrorNegocio

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error, username = None, ""
    if request.method == "POST":
        username = request.form.get("usuario", "")
        try:
            u = servicio("auth").autenticar(username, request.form.get("password", ""))
        except ErrorNegocio as e:
            error = e.mensaje
        else:
            session.clear()
            session.update(uid=u.id, rol=u.rol.value)
            return redirect(url_for("auth.inicio"))
    return render_template("auth/login.html", error=error, username=username)


@bp.route("/")
@requiere()
def inicio():
    """Menú según el rol (mockup CU-01)."""
    contador = 0
    return render_template("auth/inicio.html", contador=contador)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
