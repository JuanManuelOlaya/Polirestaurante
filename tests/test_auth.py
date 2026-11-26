from database.datos_iniciales import CLAVE_DEMO as CLAVE
from tests.base import Base


class HU1Login(Base):
    def test_roles_y_obligatorios(self):
        self.assertEqual(self.auth.autenticar("mesero4", CLAVE).rol.value, "MESERO")
        self.assertEqual(self.cocina.rol.value, "COCINA")
        self.assertEqual(self.admin.rol.value, "ADMINISTRADOR")
        self.falla("usuario es obligatorio", self.auth.autenticar, "", CLAVE)
        self.falla("contraseña es obligatoria", self.auth.autenticar, "mesero7", "")
        self.falla("usuario o contraseña incorrectos, intento 1 de 3", self.auth.autenticar, "noexiste", "x")
        self.falla("cuenta inactiva, contacte al administrador", self.auth.autenticar, "mesero5", CLAVE)

    def test_bloqueo(self):
        for n in (1, 2):
            self.falla(f"usuario o contraseña incorrectos, intento {n} de 3", self.auth.autenticar, "mesero2", "mala")
        self.falla("cuenta bloqueada por intentos fallidos", self.auth.autenticar, "mesero2", "mala")
        self.falla("cuenta bloqueada por intentos fallidos", self.auth.autenticar, "mesero2", CLAVE)

