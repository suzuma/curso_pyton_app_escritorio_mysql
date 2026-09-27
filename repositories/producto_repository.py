"""
Repositorio de la entidad ``Producto``.

La consulta de listado arma el ``WHERE`` según los filtros que se reciban.
Aunque la sentencia cambie, los valores siempre viajan como parámetros
``%s``: lo único que se concatena son fragmentos de SQL fijos escritos en
este archivo, nunca texto que venga del usuario.
"""

from __future__ import annotations

from typing import Any, Optional

from mysql.connector import errorcode

from models.producto import Producto
from repositories.base_repository import BaseRepository

_SELECT_BASE: str = """
    SELECT p.id, p.categoria_id, p.sku, p.nombre, p.precio, p.stock,
           p.activo, p.created_at,
           c.nombre AS categoria_nombre
    FROM productos AS p
    INNER JOIN categorias AS c ON c.id = p.categoria_id
"""


class ProductoRepository(BaseRepository[Producto]):
    """Acceso a datos de la tabla ``productos``."""

    NOMBRE_TABLA = "productos"
    MENSAJES_ERROR = {
        errorcode.ER_DUP_ENTRY: "Ya existe un producto con ese SKU.",
        errorcode.ER_NO_REFERENCED_ROW_2: "La categoría seleccionada no existe.",
        # Violación de CHECK (precio >= 0 o stock >= 0) en MySQL 8.0.16+.
        errorcode.ER_CHECK_CONSTRAINT_VIOLATED: "El precio y el stock no pueden ser negativos.",
    }

    def listar(
        self,
        texto: str = "",
        categoria_id: Optional[int] = None,
        incluir_inactivos: bool = False,
    ) -> list[Producto]:
        """
        Devuelve los productos que cumplen los filtros, ordenados por nombre.

        Args:
            texto: Coincidencia parcial en SKU o nombre.
            categoria_id: Si se indica, solo productos de esa categoría.
            incluir_inactivos: Si es ``False``, omite los dados de baja.

        Returns:
            list[Producto]: Lista (posiblemente vacía) de productos.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        condiciones: list[str] = []
        parametros: list[Any] = []

        if texto:
            patron = f"%{self._escapar_like(texto)}%"
            condiciones.append("(p.sku LIKE %s OR p.nombre LIKE %s)")
            parametros += [patron, patron]
        if categoria_id is not None:
            condiciones.append("p.categoria_id = %s")
            parametros.append(categoria_id)
        if not incluir_inactivos:
            condiciones.append("p.activo = %s")
            parametros.append(True)

        sql = _SELECT_BASE
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY p.nombre"
        return [Producto.from_row(f) for f in self._consultar_todos(sql, tuple(parametros))]

    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        """
        Busca un producto por su clave primaria.

        Args:
            producto_id: Identificador del producto.

        Returns:
            Optional[Producto]: El producto o ``None`` si no existe.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        fila = self._consultar_uno(_SELECT_BASE + " WHERE p.id = %s", (producto_id,))
        return Producto.from_row(fila) if fila else None

    def crear(self, producto: Producto) -> int:
        """
        Inserta un producto nuevo.

        Args:
            producto: Producto a insertar (su ``id`` se ignora).

        Returns:
            int: Id asignado. También se guarda en ``producto.id``.

        Raises:
            DuplicateEntryError: Si el SKU ya existe.
            ForeignKeyError: Si la categoría no existe.
            RepositoryError: Ante cualquier otro error.
        """
        sql = """
            INSERT INTO productos (categoria_id, sku, nombre, precio, stock, activo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        producto.id = self._insertar(
            sql,
            (
                producto.categoria_id,
                producto.sku,
                producto.nombre,
                producto.precio,
                producto.stock,
                producto.activo,
            ),
        )
        return producto.id

    def actualizar(self, producto: Producto) -> bool:
        """
        Actualiza los datos de un producto (excepto su estado).

        Args:
            producto: Producto con ``id`` y los datos nuevos.

        Returns:
            bool: ``True`` si el producto existía.

        Raises:
            DuplicateEntryError: Si el SKU pertenece a otro producto.
            ForeignKeyError: Si la categoría no existe.
            RepositoryError: Ante cualquier otro error.
        """
        sql = """
            UPDATE productos
            SET categoria_id = %s, sku = %s, nombre = %s, precio = %s, stock = %s
            WHERE id = %s
        """
        parametros = (
            producto.categoria_id,
            producto.sku,
            producto.nombre,
            producto.precio,
            producto.stock,
            producto.id,
        )
        return self._ejecutar_escritura(sql, parametros) > 0

    def cambiar_estado(self, producto_id: int, activo: bool) -> bool:
        """
        Activa o desactiva un producto (baja lógica).

        Se prefiere a borrar el registro porque conserva el historial y,
        cuando existan ventas o movimientos, evita romper sus referencias.

        Args:
            producto_id: Id del producto.
            activo: Nuevo estado.

        Returns:
            bool: ``True`` si el producto existía.

        Raises:
            RepositoryError: Si la sentencia falla.
        """
        sql = "UPDATE productos SET activo = %s WHERE id = %s"
        return self._ejecutar_escritura(sql, (activo, producto_id)) > 0
