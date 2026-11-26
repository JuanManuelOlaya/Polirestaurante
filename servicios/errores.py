class ErrorNegocio(Exception):
    """Regla de negocio incumplida. El mensaje se muestra al usuario."""

    def __init__(self, mensaje, codigo="VALIDACION", **datos):
        super().__init__(mensaje)
        self.mensaje, self.codigo, self.datos = mensaje, codigo, datos


def entero(valor, campo, minimo=1):
    """Mensajes del mazo de pruebas: 'X es numérico' / 'X es numérico positivo'."""
    texto = str(valor if valor is not None else "").strip()
    try:
        numero = int(texto)
    except ValueError:
        raise ErrorNegocio(f"{campo} es numérico")
    if numero < minimo or numero > 1_000_000_000:
        raise ErrorNegocio(f"{campo} es numérico positivo")
    return numero


def pesos(valor):
    return "$" + f"{int(valor):,}".replace(",", ".")
