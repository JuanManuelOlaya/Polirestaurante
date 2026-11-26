from dao.producto_dao import CategoriaDAO, ProductoDAO
from servicios.errores import ErrorNegocio, entero


class ProductoService:
    def __init__(self, bd):
        self.bd = bd
        self.dao = ProductoDAO()
        self.categorias_dao = CategoriaDAO()

    def listar(self, solo_activos=True):
        with self.bd.lectura() as con:
            return [dict(p, agotado=not p["disponible"] or p["unidades"] == 0)
                    for p in self.dao.listar(con, solo_activos)]

    def buscar(self, id_):
        with self.bd.lectura() as con:
            return self.dao.buscar(con, id_)

    def opciones(self):
        with self.bd.lectura() as con:
            return self.categorias_dao.listar(con), self.categorias_dao.listar_presentaciones(con)

    def guardar(self, datos, nuevo=True):
        """HU-8: valida todos los campos y reporta juntos los errores."""
        errores, limpio = [], {}
        campos = [("id", "id", 1), ("id_presentacion", "presentación", 1),
                  ("unidades", "unidades", 1 if nuevo else 0), ("precio", "precio", 1)]
        nombre = (datos.get("nombre") or "").strip()
        if not nombre:
            errores.append("nombre es obligatorio")
        for llave, etiqueta, minimo in campos:
            try:
                limpio[llave] = entero(datos.get(llave), etiqueta, minimo)
            except ErrorNegocio as e:
                errores.append(e.mensaje)
        try:
            limpio["id_categoria"] = entero(datos.get("id_categoria"), "categoría")
        except ErrorNegocio:
            errores.append("categoría es obligatoria")
        if errores:
            raise ErrorNegocio(", ".join(errores))
        limpio["nombre"] = nombre[:80]
        with self.bd.transaccion() as con:
            existe = self.dao.buscar(con, limpio["id"])
            if nuevo and existe:
                raise ErrorNegocio("ya existe un producto con ese id")
            if not nuevo and not existe:
                raise ErrorNegocio("producto no encontrado")
            if limpio["id_categoria"] not in [c["id"] for c in self.categorias_dao.listar(con)]:
                raise ErrorNegocio("categoría no válida")
            if limpio["id_presentacion"] not in [p["id"] for p in self.categorias_dao.listar_presentaciones(con)]:
                raise ErrorNegocio("presentación no válida")
            (self.dao.insertar if nuevo else self.dao.actualizar)(con, limpio)
        return "producto guardado"

    def cambiar_activo(self, id_, activo):
        with self.bd.transaccion() as con:
            self.dao.cambiar_campo(con, id_, "activo", activo)

    def cambiar_disponibilidad(self, id_, disponible):
        """HU-12."""
        with self.bd.transaccion() as con:
            p = self.dao.buscar(con, id_)
            if not p:
                raise ErrorNegocio("producto no encontrado")
            if disponible and p["unidades"] == 0:
                raise ErrorNegocio("agregue unidades antes de marcarlo disponible")
            self.dao.cambiar_campo(con, id_, "disponible", disponible)

    def crear_categoria(self, nombre):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ErrorNegocio("nombre es obligatorio")
        with self.bd.transaccion() as con:
            if nombre.lower() in [c["nombre"].lower() for c in self.categorias_dao.listar(con)]:
                raise ErrorNegocio("la categoría ya existe")
            self.categorias_dao.insertar(con, nombre[:50])
