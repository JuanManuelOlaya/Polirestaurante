"""Modelo de dominio (diagrama de clases)."""
from dataclasses import dataclass
from enum import Enum


class Rol(str, Enum):
    MESERO = "MESERO"
    COCINA = "COCINA"
    ADMINISTRADOR = "ADMINISTRADOR"


class TipoServicio(str, Enum):
    SALON = "SALON"
    LLEVAR = "LLEVAR"


@dataclass(frozen=True)
class Usuario:
    id: int
    nombre: str
    username: str
    password: str
    activo: bool
    rol: Rol
