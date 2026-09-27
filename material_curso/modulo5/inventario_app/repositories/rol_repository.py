"""
Repositorio de la entidad ``Rol``.

Los roles se crean con el script SQL y la aplicación solo los consulta
(para llenar la lista desplegable del formulario de usuarios).
"""

from __future__ import annotations

from typing import Optional

from models.rol import Rol
from repositories.base_repository import BaseRepository


class RolRepository(BaseRepository[Rol]):
    """Acceso de solo lectura a la tabla ``roles``."""

    NOMBRE_TABLA = "roles"

    def listar(self) -> list[Rol]:
        """
        Devuelve todos los roles ordenados por id.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = "SELECT id, nombre, descripcion, created_at FROM roles ORDER BY id"
        return [Rol.from_row(fila) for fila in self._consultar_todos(sql)]

    def obtener_por_id(self, rol_id: int) -> Optional[Rol]:
        """
        Busca un rol por su clave primaria.

        Returns:
            Optional[Rol]: El rol o ``None`` si no existe.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = "SELECT id, nombre, descripcion, created_at FROM roles WHERE id = %s"
        fila = self._consultar_uno(sql, (rol_id,))
        return Rol.from_row(fila) if fila else None
