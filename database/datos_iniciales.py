"""Datos de demostración. Solo se cargan si la base de datos está vacía."""
from werkzeug.security import generate_password_hash

CLAVE_DEMO = "Poli2026*"


def cargar(bd):
    with bd.transaccion() as con:
        if con.execute("SELECT 1 FROM administrador").fetchone():
            return
        clave = generate_password_hash(CLAVE_DEMO)
        usuarios = {
            "administrador": [("admin1", "Administrador Principal", 1), ("admi2", "Anderson L.", 1)],
            "cocinero": [("cocina1", "Chef Alejandra", 1), ("cocina2", "Chef Pedro", 1)],
            "mesero": [("mesero1", "Juan P.", 1), ("mesero2", "Ana M.", 1), ("mesero4", "Luis R.", 1),
                       ("mesero5", "Cuenta desactivada", 0), ("mesero7", "Sofía G.", 1)],
        }
        for tabla, lista in usuarios.items():
            for username, nombre, activo in lista:
                con.execute(f"INSERT INTO {tabla}(nombre,username,password,activo) VALUES(?,?,?,?)",
                            (nombre, username, clave, activo))
        for nombre in ("Plato fuerte", "Especialidad", "Bebida"):
            con.execute("INSERT INTO categoria(nombre) VALUES(?)", (nombre,))
        for nombre in ("Unidad", "Porción", "Vaso", "Botella"):
            con.execute("INSERT INTO presentacion(nombre) VALUES(?)", (nombre,))
        # id, nombre, categoría, presentación, unidades, precio, disponible
        productos = [
            (1, "Hamburguesa Angus", 1, 1, 40, 12500, 1), (2, "Pizza Pepperoni", 2, 1, 25, 18000, 1),
            (3, "Pasta Alfredo", 1, 2, 20, 22000, 1), (4, "Jugo natural", 3, 3, 60, 6000, 1),
            (5, "Hamburguesa Parrilla", 1, 1, 30, 15000, 1), (6, "Limonada de coco", 3, 3, 30, 8000, 0),
        ]
        for p in productos:
            con.execute("INSERT INTO producto(id,nombre,id_categoria,id_presentacion,unidades,precio,"
                        "disponible) VALUES(?,?,?,?,?,?,?)", p)
        for n in range(1, 11):
            con.execute("INSERT INTO mesa(numero) VALUES(?)", (n,))
