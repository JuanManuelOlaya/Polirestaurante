"""Utilidades compartidas por los controladores: sesión, roles y errores."""
import secrets
from datetime import datetime
from functools import wraps

from flask import abort, current_app, flash, g, jsonify, redirect, request, session, url_for

from servicios.errores import ErrorNegocio, pesos


def servicio(nombre):
    return current_app.extensions["servicios"][nombre]


def requiere(*roles):
    def decorador(vista):
        @wraps(vista)
        def envuelta(*args, **kwargs):
            if not g.usuario:
                if request.path.startswith("/api/"):
                    return jsonify(error="sesión finalizada", codigo="SESION"), 401
                return redirect(url_for("auth.login"))
            if roles and g.usuario.rol.value not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envuelta
    return decorador


def ejecutar(accion, exito=None):
    """Ejecuta una acción de negocio y muestra el resultado como mensaje."""
    try:
        resultado = accion()
    except ErrorNegocio as e:
        flash(e.mensaje, "error")
        return False
    flash(exito or resultado, "ok")
    return True


def minutos(fecha):
    if not fecha:
        return 0
    return max(0, int((datetime.now() - datetime.fromisoformat(fecha)).total_seconds() // 60))


def registrar_comunes(app):
    @app.before_request
    def preparar():
        g.usuario = None
        if request.endpoint == "static":
            return
        if "uid" in session:
            g.usuario = servicio("auth").usuario_vigente(session["rol"], session["uid"])
            if not g.usuario:
                session.clear()
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        if request.method == "POST":
            enviado = request.headers.get("X-CSRF") or request.form.get("csrf", "")
            if not secrets.compare_digest(enviado, session["csrf"]):
                if request.path.startswith("/api/"):
                    return jsonify(error="la sesión cambió, recargue la página"), 400
                flash("la sesión expiró, intente de nuevo", "error")
                return redirect(url_for("auth.login"))

    @app.errorhandler(ErrorNegocio)
    def error_negocio(e):
        if request.path.startswith("/api/"):
            return jsonify(error=e.mensaje, codigo=e.codigo, **e.datos), 400
        flash(e.mensaje, "error")
        return redirect(url_for("auth.inicio"))

    @app.after_request
    def sin_cache(respuesta):
        if request.endpoint != "static":
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    app.jinja_env.filters.update(pesos=pesos, minutos=minutos, hora=lambda f: f[11:16] if f else "")
