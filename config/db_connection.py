"""
Módulo de conexión a la base de datos MySQL.

Centraliza la lectura de credenciales desde variables de entorno (archivo .env)
y la creación de conexiones con ``mysql-connector-python``. El resto de las capas
(en particular los repositorios) deben obtener sus conexiones únicamente a través
de este módulo; así, las credenciales y los detalles del driver quedan aislados
en un solo lugar.

Las conexiones se toman de un *pool* (``MySQLConnectionPool``): un conjunto
de conexiones que se abren una sola vez y se reutilizan. Abrir una conexión
TCP y autenticarse cuesta tiempo; con el pool, ese costo se paga al inicio y
cada operación solo "pide prestada" una conexión y la devuelve al terminar.

Ejemplo de uso desde un repositorio::

    from config.db_connection import DatabaseConnection

    with DatabaseConnection.obtener_conexion() as conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productos WHERE id = %s", (1,))
        fila = cursor.fetchone()
        cursor.close()
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Any, ClassVar, Iterator, Optional

import mysql.connector
from mysql.connector import errorcode, pooling
from mysql.connector.constants import ClientFlag
from mysql.connector.pooling import PooledMySQLConnection

# Importar settings carga el archivo .env dentro de os.environ antes de que
# se lean las variables DB_*; también informa dónde lo buscó.
from config import settings

REQUIRED_ENV_VARS: tuple[str, ...] = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
DEFAULT_DB_PORT: int = 3306
CONNECTION_TIMEOUT: int = 10  # segundos
POOL_NAME: str = "inventario_pool"
DEFAULT_POOL_SIZE: int = 5
MAX_POOL_SIZE: int = 32  # límite de mysql-connector-python


class DatabaseConnectionError(Exception):
    """
    Excepción propia de la capa de configuración.

    Envuelve los errores de ``mysql.connector`` con un mensaje comprensible
    para el usuario final. De esta forma, las capas superiores (controladores
    y vistas) pueden capturar este error sin depender directamente del driver.
    """


class DatabaseConnection:
    """
    Punto único de acceso a las conexiones MySQL, respaldado por un pool.

    El pool se crea la primera vez que se necesita (*lazy initialization*) y
    se comparte entre todos los repositorios. Si el servidor no está
    disponible en ese momento, no se crea y se vuelve a intentar en la
    siguiente operación.

    Attributes:
        _pool: Pool compartido; ``None`` hasta la primera conexión.
        _candado: Evita que dos hilos (por ejemplo, el del login) creen
            el pool al mismo tiempo.
    """

    _pool: ClassVar[Optional[pooling.MySQLConnectionPool]] = None
    _candado: ClassVar[threading.Lock] = threading.Lock()

    @staticmethod
    def _leer_configuracion() -> dict[str, Any]:
        """
        Construye el diccionario de parámetros de conexión.

        Returns:
            dict[str, Any]: Parámetros aceptados por ``mysql.connector.connect``.

        Raises:
            DatabaseConnectionError: Si falta alguna variable obligatoria
                o si ``DB_PORT`` no es un número entero.
        """
        faltantes = [var for var in REQUIRED_ENV_VARS if os.getenv(var) is None]
        if faltantes:
            if settings.ARCHIVO_ENV is None:
                rutas = "\n".join(f"  • {r}" for r in settings.RUTAS_ENV_BUSCADAS)
                raise DatabaseConnectionError(
                    "No se encontró el archivo .env con los datos de conexión. "
                    f"Se buscó en:\n{rutas}\n"
                    "Cree uno a partir de .env.example en cualquiera de esas ubicaciones."
                )
            raise DatabaseConnectionError(
                "Faltan variables de entorno para la base de datos: "
                + ", ".join(faltantes)
                + f". Revise el archivo {settings.ARCHIVO_ENV}."
            )

        puerto_texto = os.getenv("DB_PORT", str(DEFAULT_DB_PORT))
        try:
            puerto = int(puerto_texto)
        except ValueError as exc:
            raise DatabaseConnectionError(
                f"DB_PORT debe ser un número entero; se recibió '{puerto_texto}'."
            ) from exc

        return {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": puerto,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "connection_timeout": CONNECTION_TIMEOUT,
            # Las transacciones se confirman explícitamente en los repositorios.
            "autocommit": False,
            # Por defecto, MySQL informa en rowcount solo las filas que un UPDATE
            # realmente modificó; si se guardan los mismos valores, devuelve 0.
            # FOUND_ROWS hace que informe las filas que cumplieron el WHERE, que
            # es lo que los repositorios usan para saber si el registro existe.
            "client_flags": [ClientFlag.FOUND_ROWS],
            # Usa la implementación del driver escrita en Python, no su
            # extensión en C. La extensión carga los plugins de autenticación
            # (p. ej. caching_sha2_password de MySQL 8) como bibliotecas del
            # sistema, que PyInstaller no incluye; la versión en Python los
            # trae como módulos y funciona igual en desarrollo y empaquetada.
            "use_pure": True,
        }

    @staticmethod
    def _leer_tamano_pool() -> int:
        """
        Lee ``DB_POOL_SIZE`` (opcional) y valida que esté entre 1 y 32.

        Raises:
            DatabaseConnectionError: Si el valor no es válido.
        """
        texto = os.getenv("DB_POOL_SIZE", str(DEFAULT_POOL_SIZE))
        try:
            tamano = int(texto)
        except ValueError as exc:
            raise DatabaseConnectionError(
                f"DB_POOL_SIZE debe ser un número entero; se recibió '{texto}'."
            ) from exc
        if not 1 <= tamano <= MAX_POOL_SIZE:
            raise DatabaseConnectionError(
                f"DB_POOL_SIZE debe estar entre 1 y {MAX_POOL_SIZE}; se recibió {tamano}."
            )
        return tamano

    @classmethod
    def _obtener_pool(cls) -> pooling.MySQLConnectionPool:
        """
        Devuelve el pool compartido, creándolo si todavía no existe.

        Raises:
            DatabaseConnectionError: Si la configuración es inválida o el
                servidor no responde al crear las conexiones iniciales.
        """
        with cls._candado:
            if cls._pool is None:
                parametros = cls._leer_configuracion()
                tamano = cls._leer_tamano_pool()
                try:
                    cls._pool = pooling.MySQLConnectionPool(
                        pool_name=POOL_NAME,
                        pool_size=tamano,
                        # Al devolver una conexión se limpia su sesión
                        # (variables, tablas temporales, transacción abierta).
                        pool_reset_session=True,
                        **parametros,
                    )
                except mysql.connector.Error as err:
                    raise DatabaseConnectionError(cls._traducir_error(err)) from err
            return cls._pool

    @classmethod
    def conectar(cls) -> PooledMySQLConnection:
        """
        Toma una conexión del pool.

        Quien llama a este método debe invocar ``close()`` al terminar: en
        una conexión del pool, ``close()`` no la cierra, sino que la devuelve
        para que otra operación la reutilice. Siempre que sea posible,
        prefiera ``obtener_conexion()``, que lo hace automáticamente.

        Returns:
            PooledMySQLConnection: Conexión lista para usarse.

        Raises:
            DatabaseConnectionError: Si la configuración es inválida, el
                servidor no responde o todas las conexiones están ocupadas.
        """
        pool = cls._obtener_pool()
        try:
            # Si una conexión del pool se había caído (p. ej., porque se
            # reinició MySQL), get_connection() la reconecta antes de darla.
            return pool.get_connection()
        except mysql.connector.errors.PoolError as err:
            raise DatabaseConnectionError(
                "Todas las conexiones a la base de datos están ocupadas. "
                "Intente de nuevo en unos segundos."
            ) from err
        except mysql.connector.Error as err:
            raise DatabaseConnectionError(cls._traducir_error(err)) from err

    @classmethod
    def cerrar_pool(cls) -> None:
        """
        Descarta el pool actual para que la próxima operación cree uno nuevo.

        Útil en pruebas o si cambió la configuración del ``.env`` mientras
        la aplicación estaba abierta. Las conexiones que estén en uso se
        cierran cuando sus operaciones terminan.
        """
        with cls._candado:
            cls._pool = None

    @classmethod
    @contextmanager
    def obtener_conexion(cls) -> Iterator[PooledMySQLConnection]:
        """
        Administrador de contexto que entrega una conexión y garantiza su cierre.

        Si ocurre un error de MySQL dentro del bloque ``with``, se ejecuta un
        ``rollback`` para no dejar transacciones a medias y el error se vuelve
        a lanzar para que la capa que llamó decida cómo manejarlo.

        Yields:
            PooledMySQLConnection: Conexión tomada del pool.

        Raises:
            DatabaseConnectionError: Si no fue posible obtener la conexión.
            mysql.connector.Error: Si falla una operación dentro del bloque.
        """
        conexion = cls.conectar()
        try:
            yield conexion
        except Exception:
            # Cualquier error deja la transacción sin confirmar: se revierte.
            try:
                conexion.rollback()
            except mysql.connector.Error:
                pass  # la conexión ya no responde; el pool la reconectará
            raise
        finally:
            # Siempre se llama a close(): devuelve la conexión al pool. Si no
            # se hiciera, el pool se quedaría sin conexiones disponibles.
            conexion.close()

    @classmethod
    def probar_conexion(cls) -> tuple[bool, str]:
        """
        Verifica que la base de datos sea accesible.

        Útil al iniciar la aplicación (``main.py``) para avisar al usuario
        antes de mostrar la ventana principal.

        Returns:
            tuple[bool, str]: ``(True, versión del servidor)`` si la conexión
            funciona, o ``(False, mensaje de error)`` en caso contrario.
        """
        try:
            with cls.obtener_conexion() as conexion:
                cursor = conexion.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                cursor.close()
                return True, f"Conectado a MySQL {version[0] if version else ''}".strip()
        except DatabaseConnectionError as err:
            return False, str(err)
        except mysql.connector.Error as err:
            return False, cls._traducir_error(err)

    @staticmethod
    def _traducir_error(err: mysql.connector.Error) -> str:
        """
        Convierte los códigos de error más comunes de MySQL en mensajes claros.

        Args:
            err: Error original lanzado por ``mysql.connector``.

        Returns:
            str: Mensaje descriptivo en español.
        """
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return "Usuario o contraseña de MySQL incorrectos (revise DB_USER y DB_PASSWORD)."
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            return (
                f"La base de datos '{os.getenv('DB_NAME')}' no existe. "
                "Ejecute primero el script database/mysql_DDL.sql."
            )
        sin_conexion = err.errno in (
            errorcode.CR_CONN_HOST_ERROR,
            errorcode.CR_UNKNOWN_HOST,
            errorcode.CR_CONNECTION_ERROR,
            errorcode.CR_SERVER_GONE_ERROR,
            errorcode.CR_SERVER_LOST,
        )
        # Cuando el pool intenta reconectar una conexión y falla, el driver
        # informa errno -1 con el texto "Can not reconnect...".
        reconexion_fallida = err.errno == -1 and "reconnect" in str(err.msg).lower()
        if sin_conexion or reconexion_fallida:
            return (
                f"No se pudo contactar al servidor MySQL en "
                f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', DEFAULT_DB_PORT)}. "
                "Verifique que el servicio esté en ejecución."
            )
        return f"Error de base de datos ({err.errno}): {err.msg}"


if __name__ == "__main__":
    # Prueba rápida desde la raíz del proyecto:  python -m config.db_connection
    exito, mensaje = DatabaseConnection.probar_conexion()
    print(("[OK] " if exito else "[ERROR] ") + mensaje)
