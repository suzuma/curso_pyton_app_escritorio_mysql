"""
Entidad de dominio ``Producto``.

Representa un registro de la tabla ``productos``. El precio se maneja con
``decimal.Decimal`` y no con ``float``: los números de punto flotante no
pueden representar exactamente valores como 0.10, y en cálculos de dinero
esos pequeños errores se acumulan. La columna es ``DECIMAL(10, 2)`` y el
driver de MySQL la entrega directamente como ``Decimal``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional


@dataclass
class Producto:
    """
    Artículo del inventario.

    Attributes:
        categoria_id: Clave foránea hacia ``categorias.id``.
        sku: Código único del producto (Stock Keeping Unit), p. ej. ``PROD-001``.
        nombre: Nombre descriptivo (máx. 150 caracteres).
        precio: Precio unitario, con dos decimales.
        stock: Unidades disponibles; nunca negativo.
        activo: Si es ``False``, el producto está dado de baja lógica.
        id: Clave primaria. Es ``None`` mientras no se ha insertado.
        created_at: Fecha de creación asignada por MySQL.
        categoria_nombre: Nombre de la categoría. Solo se llena cuando la
            consulta hace ``JOIN`` con ``categorias``.
    """

    categoria_id: int
    sku: str
    nombre: str
    precio: Decimal
    stock: int = 0
    activo: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    categoria_nombre: Optional[str] = None

    @classmethod
    def from_row(cls, fila: dict[str, Any]) -> Producto:
        """
        Construye un ``Producto`` a partir de una fila de MySQL.

        Args:
            fila: Diccionario con las columnas de ``productos`` y,
                opcionalmente, ``categoria_nombre``.

        Returns:
            Producto: Instancia con los datos de la fila.
        """
        return cls(
            id=fila.get("id"),
            categoria_id=fila["categoria_id"],
            sku=fila["sku"],
            nombre=fila["nombre"],
            # str() evita errores si el valor llegara como float.
            precio=Decimal(str(fila["precio"])),
            stock=int(fila["stock"]),
            activo=bool(fila.get("activo", True)),
            created_at=fila.get("created_at"),
            categoria_nombre=fila.get("categoria_nombre"),
        )

    @property
    def valor_inventario(self) -> Decimal:
        """Valor total de las existencias: precio × stock."""
        return self.precio * self.stock
