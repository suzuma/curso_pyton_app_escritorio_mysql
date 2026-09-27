"""
Control de acceso basado en roles (RBAC, *Role-Based Access Control*).

Cada rol tiene un conjunto de permisos. Tanto la interfaz (para decidir qué
opciones mostrar) como los controladores (para rechazar operaciones no
autorizadas) consultan este módulo, de modo que las reglas están escritas
en un solo lugar.

Ocultar un botón no basta como medida de seguridad: si mañana otra pantalla
llamara al mismo controlador, la regla debe seguir cumpliéndose. Por eso los
controladores también verifican los permisos.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from controllers.exceptions import PermisoDenegadoError
from models.usuario import Usuario

ROL_ADMINISTRADOR: str = "Administrador"
ROL_OPERADOR: str = "Operador"


class Permiso(Enum):
    """Acciones del sistema que requieren autorización."""

    GESTIONAR_CATEGORIAS = "gestionar_categorias"
    GESTIONAR_PRODUCTOS = "gestionar_productos"
    CAMBIAR_ESTADO_PRODUCTOS = "cambiar_estado_productos"
    GESTIONAR_USUARIOS = "gestionar_usuarios"


PERMISOS_POR_ROL: dict[str, frozenset[Permiso]] = {
    ROL_ADMINISTRADOR: frozenset(Permiso),  # todos los permisos
    ROL_OPERADOR: frozenset({Permiso.GESTIONAR_PRODUCTOS}),
}


def tiene_permiso(usuario: Optional[Usuario], permiso: Permiso) -> bool:
    """
    Indica si un usuario puede realizar una acción.

    Args:
        usuario: Usuario autenticado; ``None`` nunca tiene permisos.
        permiso: Acción a comprobar.

    Returns:
        bool: ``True`` si el rol del usuario incluye el permiso.
    """
    if usuario is None or usuario.rol is None or not usuario.activo:
        return False
    return permiso in PERMISOS_POR_ROL.get(usuario.rol.nombre, frozenset())


def exigir_permiso(usuario: Optional[Usuario], permiso: Permiso) -> None:
    """
    Lanza ``PermisoDenegadoError`` si el usuario no tiene el permiso.

    Raises:
        PermisoDenegadoError: Si la acción no está autorizada.
    """
    if not tiene_permiso(usuario, permiso):
        raise PermisoDenegadoError("No tiene permisos para realizar esta operación.")
