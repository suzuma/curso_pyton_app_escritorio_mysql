"""
Entidad de dominio ``Categoria``.

Representa un registro de la tabla ``categorias``, que agrupa productos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Categoria:
    """
    Categoría de productos (por ejemplo, Electrónica u Oficina).

    Attributes:
        nombre: Nombre único de la categoría (máx. 100 caracteres).
        descripcion: Texto libre opcional.
        id: Clave primaria. Es ``None`` mientras no se ha insertado.
        created_at: Fecha de creación asignada por MySQL.
        total_productos: Cantidad de productos que pertenecen a la
            categoría. Solo se llena cuando la consulta los cuenta; no
            es una columna de la tabla.
    """

    nombre: str
    descripcion: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    total_productos: Optional[int] = None

    @classmethod
    def from_row(cls, fila: dict[str, Any]) -> Categoria:
        """
        Construye una ``Categoria`` a partir de una fila de MySQL.

        Args:
            fila: Diccionario con las columnas de ``categorias`` y,
                opcionalmente, ``total_productos``.

        Returns:
            Categoria: Instancia con los datos de la fila.
        """
        total = fila.get("total_productos")
        return cls(
            id=fila.get("id"),
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion"),
            created_at=fila.get("created_at"),
            total_productos=int(total) if total is not None else None,
        )

    def __str__(self) -> str:
        """Devuelve el nombre; útil para listas desplegables de la GUI."""
        return self.nombre
