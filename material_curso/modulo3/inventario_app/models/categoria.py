"""Entidad Categoria (Módulo 2)."""


class Categoria:
    """Agrupa productos del mismo tipo."""

    def __init__(self, nombre: str, descripcion: str = "") -> None:
        self.nombre = nombre.strip()
        self.descripcion = descripcion.strip()

    def __str__(self) -> str:
        """Texto para el usuario: print(categoria)."""
        return self.nombre

    def __repr__(self) -> str:
        """Texto para el programador: consola y depuración."""
        return f"Categoria(nombre={self.nombre!r})"

    def __eq__(self, otra: object) -> bool:
        """Dos categorías son iguales si tienen el mismo nombre (sin distinguir mayúsculas)."""
        if not isinstance(otra, Categoria):
            return NotImplemented
        return self.nombre.lower() == otra.nombre.lower()

    def __hash__(self) -> int:
        """Necesario al definir __eq__ para poder usarla en conjuntos y como clave."""
        return hash(self.nombre.lower())
