SELECT = """SELECT p.*, m.numero AS mesa_numero, c.nombre AS cliente, w.nombre AS mesero
            FROM pedido p LEFT JOIN mesa m ON m.id=p.id_mesa
            LEFT JOIN cliente c ON c.id=p.id_cliente JOIN mesero w ON w.id=p.id_mesero"""


class PedidoDAO:
    def siguiente_numero(self, con):
        return con.execute("SELECT COALESCE(MAX(numero_llegada),0)+1 FROM pedido").fetchone()[0]

    def guardar(self, con, d):
        columnas = ",".join(d)
        marcas = ",".join(f":{k}" for k in d)
        return con.execute(f"INSERT INTO pedido({columnas}) VALUES({marcas})", d).lastrowid

    def guardar_detalle(self, con, id_pedido, i):
        con.execute("INSERT INTO detalle_pedido(id_pedido,id_producto,nombre_producto,precio_unitario,"
                    "cantidad,nota) VALUES(?,?,?,?,?,?)",
                    (id_pedido, i["id_producto"], i["nombre"], i["precio"], i["cantidad"], i["nota"]))

    def _completar(self, con, fila):
        pedido = dict(fila)
        pedido["detalles"] = [dict(d) for d in con.execute(
            "SELECT * FROM detalle_pedido WHERE id_pedido=? ORDER BY id", (fila["id"],))]
        return pedido

    def buscar_por_id(self, con, id_):
        f = con.execute(SELECT + " WHERE p.id=?", (id_,)).fetchone()
        return self._completar(con, f) if f else None

    def buscar_por_clave_envio(self, con, clave):
        f = con.execute(SELECT + " WHERE p.clave_envio=?", (clave,)).fetchone()
        return self._completar(con, f) if f else None

    def listar(self, con, estados, id_mesero=None):
        sql = SELECT + f" WHERE p.estado IN ({','.join('?' * len(estados))})"
        args = list(estados)
        if id_mesero is not None:
            sql += " AND p.id_mesero=?"
            args.append(id_mesero)
        # El más antiguo primero (H6)
        return [self._completar(con, f) for f in con.execute(sql + " ORDER BY p.numero_llegada", args)]

    def actualizar(self, con, id_, **campos):
        asignaciones = ",".join(f"{k}=?" for k in campos)
        con.execute(f"UPDATE pedido SET {asignaciones} WHERE id=?", (*campos.values(), id_))

    def agregar_historial(self, con, id_pedido, estado, usuario, fecha, motivo=None, autorizado=None):
        con.execute("INSERT INTO historial_estado(id_pedido,estado,usuario,fecha,motivo,autorizado_por)"
                    " VALUES(?,?,?,?,?,?)", (id_pedido, estado, usuario, fecha, motivo, autorizado))

    def historial(self, con, id_pedido):
        return con.execute("SELECT * FROM historial_estado WHERE id_pedido=? ORDER BY id",
                           (id_pedido,)).fetchall()


class ClienteDAO:
    def guardar(self, con, nombre, fecha):
        return con.execute("INSERT INTO cliente(nombre,fecha_registro) VALUES(?,?)",
                           (nombre, fecha)).lastrowid


class NotificacionDAO:
    def guardar(self, con, rol, id_usuario, mensaje, fecha):
        con.execute("INSERT INTO notificacion(rol,id_usuario,mensaje,fecha) VALUES(?,?,?,?)",
                    (rol, id_usuario, mensaje, fecha))

    def nuevas(self, con, rol, id_usuario, desde):
        return con.execute("SELECT id,mensaje FROM notificacion WHERE id>? AND rol=? AND "
                           "(id_usuario IS NULL OR id_usuario=?) ORDER BY id",
                           (desde, rol, id_usuario)).fetchall()

    def ultimo_id(self, con):
        return con.execute("SELECT COALESCE(MAX(id),0) FROM notificacion").fetchone()[0]
