SELECT = """SELECT p.*, c.nombre AS categoria, r.nombre AS presentacion
            FROM producto p JOIN categoria c ON c.id=p.id_categoria
            JOIN presentacion r ON r.id=p.id_presentacion"""


class ProductoDAO:
    def listar(self, con, solo_activos=True):
        filtro = " WHERE p.activo=1" if solo_activos else ""
        return con.execute(SELECT + filtro + " ORDER BY c.nombre, p.nombre").fetchall()

    def buscar(self, con, id_):
        return con.execute(SELECT + " WHERE p.id=?", (id_,)).fetchone()

    def insertar(self, con, d):
        con.execute("INSERT INTO producto(id,nombre,id_categoria,id_presentacion,unidades,precio)"
                    " VALUES(:id,:nombre,:id_categoria,:id_presentacion,:unidades,:precio)", d)

    def actualizar(self, con, d):
        con.execute("UPDATE producto SET nombre=:nombre,id_categoria=:id_categoria,"
                    "id_presentacion=:id_presentacion,unidades=:unidades,precio=:precio WHERE id=:id", d)

    def cambiar_campo(self, con, id_, campo, valor):
        if campo not in ("activo", "disponible"):
            raise ValueError(campo)
        con.execute(f"UPDATE producto SET {campo}=? WHERE id=?", (int(valor), id_))

    def mover_unidades(self, con, id_, delta):
        con.execute("UPDATE producto SET unidades=unidades+? WHERE id=?", (delta, id_))


class CategoriaDAO:
    def listar(self, con):
        return con.execute("SELECT * FROM categoria ORDER BY nombre").fetchall()

    def listar_presentaciones(self, con):
        return con.execute("SELECT * FROM presentacion ORDER BY id").fetchall()

    def insertar(self, con, nombre):
        con.execute("INSERT INTO categoria(nombre) VALUES(?)", (nombre,))
