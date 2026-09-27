"""
Repositorio de la entidad ``Categoria``.

Todas las sentencias usan parámetros ``%s``. Incluso la búsqueda por texto:
el comodín ``%`` se agrega al valor en Python, no al SQL, así que lo que
escriba el usuario nunca forma parte de la sentencia.
"""

from __future__ import annotations

from typing import Any, Optional

from mysql.connector import errorcode

from models.categoria import Categoria
from repositories.base_repository import BaseRepository

# LEFT JOIN para incluir también las categorías que aún no tienen productos
# (con INNER JOIN desaparecerían del listado).
_SELECT_CON_TOTAL: str = """
    SELECT c.id, c.nombre, c.descripcion, c.created_at,
           COUNT(p.id) AS total_productos
    FROM categorias AS c
    LEFT JOIN productos AS p ON p.categoria_id = c.id
"""
_GROUP_BY: str = " GROUP BY c.id, c.nombre, c.descripcion, c.created_at"


class CategoriaRepository(BaseRepository[Categoria]):
    """Acceso a datos de la tabla ``categorias``."""

    NOMBRE_TABLA = "categorias"
    MENSAJES_ERROR = {
        errorcode.ER_DUP_ENTRY: "Ya existe una categoría con ese nombre.",
        errorcode.ER_ROW_IS_REFERENCED_2: (
            "No se puede eliminar la categoría porque tiene productos asociados."
        ),
    }

    def listar(self, texto: str = "") -> list[Categoria]:
        """
        Devuelve las categorías ordenadas por nombre, con su total de productos.

        Args:
            texto: Filtro opcional; busca coincidencias parciales en el
                nombre o la descripción.

        Returns:
            list[Categoria]: Lista (posiblemente vacía) de categorías.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = _SELECT_CON_TOTAL
        parametros: tuple[Any, ...] = ()
        if texto:
            patron = f"%{self._escapar_like(texto)}%"
            sql += " WHERE c.nombre LIKE %s OR c.descripcion LIKE %s"
            parametros = (patron, patron)
        sql += _GROUP_BY + " ORDER BY c.nombre"
        return [Categoria.from_row(f) for f in self._consultar_todos(sql, parametros)]

    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        """
        Busca una categoría por su clave primaria.

        Args:
            categoria_id: Identificador de la categoría.

        Returns:
            Optional[Categoria]: La categoría o ``None`` si no existe.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = _SELECT_CON_TOTAL + " WHERE c.id = %s" + _GROUP_BY
        fila = self._consultar_uno(sql, (categoria_id,))
        return Categoria.from_row(fila) if fila else None

    def crear(self, categoria: Categoria) -> int:
        """
        Inserta una categoría nueva.

        Args:
            categoria: Categoría a insertar (su ``id`` se ignora).

        Returns:
            int: Id asignado. También se guarda en ``categoria.id``.

        Raises:
            DuplicateEntryError: Si el nombre ya existe.
            RepositoryError: Ante cualquier otro error.
        """
        sql = "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)"
        categoria.id = self._insertar(sql, (categoria.nombre, categoria.descripcion))
        return categoria.id

    def actualizar(self, categoria: Categoria) -> bool:
        """
        Actualiza el nombre y la descripción de una categoría.

        Args:
            categoria: Categoría con ``id`` y los datos nuevos.

        Returns:
            bool: ``True`` si la categoría existía.

        Raises:
            DuplicateEntryError: Si el nombre pertenece a otra categoría.
            RepositoryError: Ante cualquier otro error.
        """
        sql = "UPDATE categorias SET nombre = %s, descripcion = %s WHERE id = %s"
        parametros = (categoria.nombre, categoria.descripcion, categoria.id)
        return self._ejecutar_escritura(sql, parametros) > 0

    def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina una categoría.

        La llave foránea ``fk_productos_categorias`` usa ``ON DELETE
        RESTRICT``, así que MySQL rechaza el borrado si hay productos
        en la categoría.

        Args:
            categoria_id: Id de la categoría.

        Returns:
            bool: ``True`` si se eliminó un registro.

        Raises:
            ForeignKeyError: Si la categoría tiene productos.
            RepositoryError: Ante cualquier otro error.
        """
        sql = "DELETE FROM categorias WHERE id = %s"
        return self._ejecutar_escritura(sql, (categoria_id,)) > 0
