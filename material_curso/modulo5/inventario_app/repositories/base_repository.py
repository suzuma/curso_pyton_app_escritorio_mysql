"""
Clase base abstracta para todos los repositorios.

Reúne el código que se repetiría en cada repositorio: pedir una conexión,
ejecutar la sentencia con sus parámetros, confirmar la transacción, cerrar
el cursor y traducir los errores de MySQL. Las subclases solo escriben su
SQL y deciden qué mensaje mostrar para cada tipo de error.

Dos conceptos de POO aparecen aquí:

* **Abstracción** (``abc.ABC`` + ``@abstractmethod``): ``BaseRepository`` no
  representa ninguna tabla, así que no tiene sentido crear objetos de ella.
  Python lo impide: ``BaseRepository()`` lanza ``TypeError``. Además, obliga
  a que cada subclase implemente ``obtener_por_id``.
* **Genéricos** (``Generic[T]``): ``BaseRepository[Producto]`` indica que ese
  repositorio trabaja con objetos ``Producto``. Los editores y herramientas
  como *mypy* usan esa información para detectar errores de tipo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Optional, TypeVar

import mysql.connector
from mysql.connector import errorcode

from config.db_connection import DatabaseConnection
from repositories.exceptions import (
    DuplicateEntryError,
    ForeignKeyError,
    RepositoryError,
)

Parametros = tuple[Any, ...]
Fila = dict[str, Any]

T = TypeVar("T")  # tipo de entidad que maneja cada repositorio


class BaseRepository(ABC, Generic[T]):
    """
    Operaciones genéricas de lectura y escritura con consultas parametrizadas.

    Attributes:
        NOMBRE_TABLA: Se usa en el mensaje de errores no previstos.
        MENSAJES_ERROR: Mensajes propios de la subclase, indexados por el
            código de error de MySQL (por ejemplo, ``errorcode.ER_DUP_ENTRY``).
    """

    NOMBRE_TABLA: ClassVar[str] = ""
    MENSAJES_ERROR: ClassVar[dict[int, str]] = {}

    @abstractmethod
    def obtener_por_id(self, registro_id: int) -> Optional[T]:
        """
        Busca un registro por su clave primaria.

        Toda subclase debe implementarlo; si no lo hace, Python no permitirá
        crear objetos de ella.

        Args:
            registro_id: Valor de la clave primaria.

        Returns:
            Optional[T]: La entidad encontrada o ``None``.
        """

    def _consultar_uno(self, sql: str, parametros: Parametros = ()) -> Optional[Fila]:
        """
        Ejecuta un SELECT y devuelve la primera fila.

        Returns:
            Optional[Fila]: Diccionario columna → valor, o ``None`` si no hay filas.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        try:
            with DatabaseConnection.obtener_conexion() as conexion:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute(sql, parametros)
                fila = cursor.fetchone()
                cursor.close()
        except mysql.connector.Error as err:
            raise self._traducir_error(err) from err
        return fila

    def _consultar_todos(self, sql: str, parametros: Parametros = ()) -> list[Fila]:
        """
        Ejecuta un SELECT y devuelve todas las filas.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        try:
            with DatabaseConnection.obtener_conexion() as conexion:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute(sql, parametros)
                filas = cursor.fetchall()
                cursor.close()
        except mysql.connector.Error as err:
            raise self._traducir_error(err) from err
        return filas

    def _insertar(self, sql: str, parametros: Parametros) -> int:
        """
        Ejecuta un INSERT, confirma la transacción y devuelve el id generado.

        Returns:
            int: Valor asignado por ``AUTO_INCREMENT``.

        Raises:
            RepositoryError: O una de sus subclases, según el error de MySQL.
        """
        try:
            with DatabaseConnection.obtener_conexion() as conexion:
                cursor = conexion.cursor()
                cursor.execute(sql, parametros)
                conexion.commit()
                nuevo_id = int(cursor.lastrowid)
                cursor.close()
        except mysql.connector.Error as err:
            raise self._traducir_error(err) from err
        return nuevo_id

    def _ejecutar_escritura(self, sql: str, parametros: Parametros) -> int:
        """
        Ejecuta un UPDATE o DELETE y confirma la transacción.

        Returns:
            int: Número de filas que coincidieron con la condición ``WHERE``.

        Raises:
            RepositoryError: O una de sus subclases, según el error de MySQL.
        """
        try:
            with DatabaseConnection.obtener_conexion() as conexion:
                cursor = conexion.cursor()
                cursor.execute(sql, parametros)
                conexion.commit()
                afectadas = int(cursor.rowcount)
                cursor.close()
        except mysql.connector.Error as err:
            raise self._traducir_error(err) from err
        return afectadas

    def _traducir_error(self, err: mysql.connector.Error) -> RepositoryError:
        """
        Convierte un error de MySQL en la excepción de repositorio adecuada.

        Args:
            err: Error original del driver.

        Returns:
            RepositoryError: ``DuplicateEntryError`` para violaciones de
            UNIQUE, ``ForeignKeyError`` para llaves foráneas y
            ``RepositoryError`` para lo demás.
        """
        mensaje = self.MENSAJES_ERROR.get(err.errno)
        if err.errno == errorcode.ER_DUP_ENTRY:
            return DuplicateEntryError(mensaje or "El registro ya existe.")
        if err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return ForeignKeyError(mensaje or "Se hace referencia a un registro inexistente.")
        if err.errno == errorcode.ER_ROW_IS_REFERENCED_2:
            return ForeignKeyError(mensaje or "El registro está en uso y no puede eliminarse.")
        return RepositoryError(
            mensaje or f"Error en la tabla {self.NOMBRE_TABLA} ({err.errno}): {err.msg}"
        )

    @staticmethod
    def _escapar_like(texto: str) -> str:
        r"""
        Escapa los comodines de ``LIKE`` para que se busquen literalmente.

        Sin esto, escribir ``%`` o ``_`` en el buscador coincidiría con
        cualquier texto. MySQL usa ``\`` como carácter de escape por defecto.
        """
        return texto.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
