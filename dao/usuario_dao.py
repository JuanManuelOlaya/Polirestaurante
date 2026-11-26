from modelos.entidades import Rol, Usuario

TABLAS = {Rol.ADMINISTRADOR: "administrador", Rol.COCINA: "cocinero", Rol.MESERO: "mesero"}


class UsuarioDAO:
    @staticmethod
    def _crear(fila, rol):
        return Usuario(fila["id"], fila["nombre"], fila["username"], fila["password"],
                       bool(fila["activo"]), rol)

    def buscar_por_username(self, con, username):
        for rol, tabla in TABLAS.items():
            f = con.execute(f"SELECT * FROM {tabla} WHERE lower(username)=lower(?)", (username,)).fetchone()
            if f:
                return self._crear(f, rol)
        return None

    def buscar_por_id(self, con, rol, id_):
        f = con.execute(f"SELECT * FROM {TABLAS[Rol(rol)]} WHERE id=?", (id_,)).fetchone()
        return self._crear(f, Rol(rol)) if f else None

    def listar(self, con):
        return [self._crear(f, rol) for rol, t in TABLAS.items()
                for f in con.execute(f"SELECT * FROM {t} ORDER BY username")]

    def insertar(self, con, rol, nombre, username, password):
        con.execute(f"INSERT INTO {TABLAS[rol]}(nombre,username,password) VALUES(?,?,?)",
                    (nombre, username, password))

    def cambiar_activo(self, con, rol, id_, activo):
        con.execute(f"UPDATE {TABLAS[rol]} SET activo=? WHERE id=?", (int(activo), id_))

    def cambiar_password(self, con, rol, id_, password):
        con.execute(f"UPDATE {TABLAS[rol]} SET password=? WHERE id=?", (password, id_))

    def administradores_activos(self, con):
        return [self._crear(f, Rol.ADMINISTRADOR)
                for f in con.execute("SELECT * FROM administrador WHERE activo=1")]


class AccesoDAO:
    """Intentos fallidos, bloqueos y registro de inicios de sesión."""

    def obtener_intento(self, con, clave):
        return con.execute("SELECT * FROM intento WHERE clave=?", (clave,)).fetchone()

    def guardar_intento(self, con, clave, fallidos, bloqueado_hasta=None):
        con.execute("INSERT OR REPLACE INTO intento VALUES(?,?,?)", (clave, fallidos, bloqueado_hasta))

    def borrar_intento(self, con, clave):
        con.execute("DELETE FROM intento WHERE clave=?", (clave,))

    def registrar(self, con, username, resultado, fecha):
        con.execute("INSERT INTO registro_acceso(username,resultado,fecha) VALUES(?,?,?)",
                    (username, resultado, fecha))
