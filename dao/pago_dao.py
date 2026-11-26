class PagoDAO:
    def registrar(self, con, id_pedido, r, fecha, id_admin):
        con.execute("INSERT INTO pago(id_pedido,metodo,monto,valor_recibido,cambio,fecha_pago,"
                    "id_administrador) VALUES(?,?,?,?,?,?,?)",
                    (id_pedido, r.metodo, r.monto, r.valor_recibido, r.cambio, fecha, id_admin))

    def obtener_por_pedido(self, con, id_pedido):
        return con.execute("SELECT g.*, a.nombre AS administrador FROM pago g JOIN administrador a "
                           "ON a.id=g.id_administrador WHERE id_pedido=? ORDER BY g.id",
                           (id_pedido,)).fetchall()

    def ventas_por_metodo(self, con, desde, hasta):
        return con.execute("SELECT metodo, COUNT(*) AS pagos, SUM(monto) AS total FROM pago "
                           "WHERE date(fecha_pago) BETWEEN ? AND ? GROUP BY metodo", (desde, hasta)).fetchall()

    def productos_vendidos(self, con, desde, hasta):
        return con.execute(
            "SELECT d.nombre_producto AS nombre, SUM(d.cantidad) AS cantidad, "
            "SUM(d.cantidad*d.precio_unitario) AS total FROM detalle_pedido d "
            "JOIN pedido p ON p.id=d.id_pedido WHERE p.estado='PAGADO' AND p.id IN "
            "(SELECT id_pedido FROM pago WHERE date(fecha_pago) BETWEEN ? AND ?) "
            "GROUP BY d.nombre_producto ORDER BY cantidad DESC", (desde, hasta)).fetchall()
