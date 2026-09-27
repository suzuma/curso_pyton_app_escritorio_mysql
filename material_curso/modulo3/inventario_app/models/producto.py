"""
Entidades Producto y ProductoPerecedero (Módulo 2).

Muestra encapsulamiento con @property, atributos de clase, métodos de clase
y estáticos, herencia simple y múltiple, polimorfismo y métodos especiales.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from models.categoria import Categoria


class SerializableMixin:
    """
    Mixin: agrega una capacidad a cualquier clase que lo herede.

    Convierte las propiedades públicas del objeto en un diccionario.
    """

    CAMPOS: tuple[str, ...] = ()

    def a_dict(self) -> dict[str, Any]:
        return {campo: getattr(self, campo) for campo in self.CAMPOS}


class Producto(SerializableMixin):
    """Artículo del inventario con precio y stock validados."""

    # Atributos de clase: compartidos por todas las instancias.
    STOCK_MINIMO = 5
    CAMPOS = ("sku", "nombre", "categoria", "precio", "stock")
    _PATRON_SKU = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,49}$")

    def __init__(
        self, sku: str, nombre: str, categoria: Categoria, precio: Any, stock: int = 0
    ) -> None:
        if not Producto.sku_valido(sku):
            raise ValueError(f"SKU inválido: {sku!r}")
        self._sku = sku.strip().upper()   # solo lectura: no tiene setter
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio               # pasa por el setter y se valida
        self.stock = stock

    # ------------------------------------------------ encapsulamiento
    @property
    def sku(self) -> str:
        return self._sku

    @property
    def precio(self) -> Decimal:
        return self._precio

    @precio.setter
    def precio(self, valor: Any) -> None:
        try:
            # str() evita arrastrar el error de float: Decimal(0.1) ≠ Decimal("0.1")
            precio = Decimal(str(valor)).quantize(Decimal("0.01"))
        except InvalidOperation as exc:
            raise ValueError(f"Precio inválido: {valor!r}") from exc
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self._precio = precio

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, valor: int) -> None:
        if not isinstance(valor, int) or valor < 0:
            raise ValueError("El stock debe ser un entero mayor o igual a 0.")
        self._stock = valor

    # ------------------------------------------------ propiedades calculadas
    @property
    def valor_inventario(self) -> Decimal:
        return self.precio * self.stock

    @property
    def stock_bajo(self) -> bool:
        return self.stock <= self.STOCK_MINIMO

    # ------------------------------------------------ métodos de clase y estáticos
    @staticmethod
    def sku_valido(sku: str) -> bool:
        """No usa self ni cls: es una utilidad relacionada con la clase."""
        return bool(Producto._PATRON_SKU.fullmatch(sku.strip().upper()))

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> Producto:
        """Constructor alternativo. Con cls, también sirve para las subclases."""
        return cls(
            sku=datos["sku"],
            nombre=datos["nombre"],
            categoria=Categoria(datos["categoria"]),
            precio=datos["precio"],
            stock=datos.get("stock", 0),
        )

    # ------------------------------------------------ comportamiento
    def descripcion(self) -> str:
        return f"{self.nombre} ({self.categoria})"

    def ajustar_stock(self, cantidad: int) -> None:
        """Suma (entrada) o resta (salida) unidades; el setter impide quedar en negativo."""
        self.stock = self.stock + cantidad

    # ------------------------------------------------ métodos especiales
    def __str__(self) -> str:
        return f"{self.sku} · {self.descripcion()} · ${self.precio:,.2f} · {self.stock} u."

    def __repr__(self) -> str:
        return f"{type(self).__name__}(sku={self.sku!r}, precio={self.precio!r}, stock={self.stock})"

    def __eq__(self, otro: object) -> bool:
        """Dos productos son el mismo si tienen el mismo SKU."""
        if not isinstance(otro, Producto):
            return NotImplemented
        return self.sku == otro.sku

    def __hash__(self) -> int:
        return hash(self.sku)


class ProductoPerecedero(Producto):
    """Producto con fecha de caducidad (herencia simple)."""

    CAMPOS = Producto.CAMPOS + ("caducidad",)

    def __init__(
        self,
        sku: str,
        nombre: str,
        categoria: Categoria,
        precio: Any,
        stock: int = 0,
        caducidad: date | None = None,
    ) -> None:
        super().__init__(sku, nombre, categoria, precio, stock)  # reutiliza la validación
        self.caducidad = caducidad or date.today()

    def vencido(self, hoy: date | None = None) -> bool:
        return (hoy or date.today()) > self.caducidad

    def descripcion(self) -> str:
        """Polimorfismo: sobrescribe el método de la clase padre y lo amplía."""
        estado = "VENCIDO" if self.vencido() else f"caduca {self.caducidad:%d/%m/%Y}"
        return f"{super().descripcion()} [{estado}]"
