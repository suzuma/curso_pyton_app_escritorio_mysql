"""
Entidad de dominio ``Rol``.

Representa un registro de la tabla ``roles``. Es una clase de datos pura:
no conoce la base de datos ni la interfaz gráfica. Los repositorios la
construyen a partir de las filas que devuelve MySQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Rol:
    """
    Rol de acceso dentro del sistema (por ejemplo, Administrador u Operador).

    Attributes:
        nombre: Nombre único del rol (máx. 50 caracteres).
        descripcion: Texto opcional que explica los permisos del rol.
        id: Clave primaria. Es ``None`` mientras el rol no se ha insertado.
        created_at: Fecha de creación asignada por MySQL.
    """

    nombre: str
    descripcion: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, fila: dict[str, Any]) -> Rol:
        """
        Construye un ``Rol`` a partir de una fila obtenida con
        ``cursor(dictionary=True)``.

        Args:
            fila: Diccionario con las columnas de la tabla ``roles``.

        Returns:
            Rol: Instancia con los datos de la fila.
        """
        return cls(
            id=fila.get("id"),
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion"),
            created_at=fila.get("created_at"),
        )

    def __str__(self) -> str:
        """Devuelve el nombre del rol; útil para mostrarlo en combos de la GUI."""
        return self.nombre
