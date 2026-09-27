"""
Repositorio de productos (Módulo 2): interfaz abstracta y versión en memoria.

La interfaz define QUÉ operaciones existen. La implementación en memoria
guarda los productos en un diccionario; en el Módulo 4 se escribirá otra
que los guarde en MySQL, y el resto del programa no tendrá que cambiar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from models.producto import Producto


class RepositorioProductos(ABC):
    """Interfaz: no se puede instanciar; obliga a implementar cada método."""

    @abstractmethod
    def agregar(self, producto: Producto) -> None: ...

    @abstractmethod
    def obtener(self, sku: str) -> Optional[Producto]: ...

    @abstractmethod
    def listar(self) -> list[Producto]: ...

    @abstractmethod
    def eliminar(self, sku: str) -> bool: ...


class RepositorioProductosMemoria(RepositorioProductos):
    """Guarda los productos en un diccionario {sku: producto}."""

    def __init__(self) -> None:
        self._productos: dict[str, Producto] = {}

    def agregar(self, producto: Producto) -> None:
        if producto.sku in self._productos:
            raise ValueError(f"Ya existe un producto con SKU {producto.sku}.")
        self._productos[producto.sku] = producto

    def obtener(self, sku: str) -> Optional[Producto]:
        return self._productos.get(sku.strip().upper())

    def listar(self) -> list[Producto]:
        return sorted(self._productos.values(), key=lambda p: p.nombre)

    def eliminar(self, sku: str) -> bool:
        return self._productos.pop(sku.strip().upper(), None) is not None

    def __len__(self) -> int:
        """Permite usar len(repositorio)."""
        return len(self._productos)
