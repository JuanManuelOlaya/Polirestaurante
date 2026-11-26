class MesaDAO:
    def listar(self, con):
        return con.execute("SELECT * FROM mesa ORDER BY numero").fetchall()

    def buscar(self, con, id_):
        return con.execute("SELECT * FROM mesa WHERE id=?", (id_,)).fetchone()

    def actualizar_estado(self, con, id_, estado):
        con.execute("UPDATE mesa SET estado=? WHERE id=?", (estado, id_))

    def tiene_pedidos_activos(self, con, id_):
        return con.execute("SELECT 1 FROM pedido WHERE id_mesa=? AND estado NOT IN "
                           "('PAGADO','CANCELADO')", (id_,)).fetchone() is not None
