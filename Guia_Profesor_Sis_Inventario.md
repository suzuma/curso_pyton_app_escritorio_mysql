# Guía del profesor: construcción paso a paso del sistema de inventario

Sep 27, 2026 · @Noe Cazarez Camargo

Esta guía lleva al profesor, en 16 pasos, desde una carpeta vacía hasta la aplicación de inventario terminada y empaquetada. Cada paso dice qué archivos se crean, qué código escribir, cómo comprobar que funciona antes de avanzar, qué explicar al grupo y qué errores esperar. Complementa al *Manual del curso*: el manual explica los temas; esta guía es el guion para construir la aplicación frente al grupo.

## Antes de clase

El profesor necesita tres cosas antes de la primera sesión: el proyecto de referencia funcionando en su equipo, un entorno limpio para construir en vivo y un plan para los alumnos que se atrasen.

- [ ] Descomprimir `material_curso.zip` y ejecutar el proyecto de referencia (`material_curso/modulo5/inventario_app`) siguiendo su `README.md`. Si arranca y permite iniciar sesión con `admin@escuela.edu` / `Admin123`, el equipo está listo.
- [ ] Crear una carpeta vacía aparte para construir en clase. Nunca construya dentro de la carpeta de referencia: la necesitará para comparar.
- [ ] Confirmar que Python tiene Tkinter: `python3 -c "import tkinter; print(tkinter.TkVersion)"`.
- [ ] Tener Docker Desktop abierto y la imagen `mysql:8.4` ya descargada (`docker pull mysql:8.4`). La descarga tarda minutos y no conviene hacerla en clase.
- [ ] Aumentar el tamaño de letra del editor y de la terminal para la proyección (18 a 20 puntos).
- [ ] Crear un repositorio Git y hacer un *commit* al terminar cada paso, con el número del paso en el mensaje (`paso 06: repositorios`). Si un alumno se pierde, puede partir del *commit* de ese paso.

**Formato de cada paso.** Todos siguen el mismo orden: objetivo, tiempo, archivos, código, punto de verificación, qué explicar y errores frecuentes. El **punto de verificación** es un comando con su resultado esperado; no avance al siguiente paso hasta que todo el grupo lo tenga.

**Sobre el código.** Los archivos cortos aparecen completos. De los largos (pantallas y controladores) se muestra la estructura y los métodos que conviene escribir en vivo; el archivo completo está en el proyecto de referencia, con el mismo nombre y la misma ruta. Una técnica que funciona bien: escribir en vivo la parte que enseña algo nuevo y copiar del proyecto de referencia la parte repetitiva, explicándola.

## Mapa de la construcción

Los 16 pasos suman unas 24 horas de clase, contando explicación y práctica. Encajan en los módulos 4 y 5 del manual (pasos 1 a 6 en el Módulo 4, pasos 7 a 16 en el Módulo 5). Si el tiempo no alcanza, entregue los pasos 12 a 14 como código base y dedique la clase a comentarlos.

| Paso | Tema | Tiempo | Archivos principales | Punto de verificación |
| --- | --- | --- | --- | --- |
| 1 | Entorno y estructura | 1 h | `requirements.txt`, `.gitignore`, carpetas | Las cuatro librerías se importan |
| 2 | Base de datos con Docker | 1.5 h | `.env`, `docker-compose.yml`, `database/mysql_DDL.sql` | `docker compose ps` muestra `healthy` |
| 3 | Configuración y conexión | 1.5 h | `config/settings.py`, `config/db_connection.py` | `[OK] Conectado a MySQL 8.4.x` |
| 4 | Modelos | 1 h | `models/*.py` | `Usuario.from_row()` arma el objeto con su rol |
| 5 | Excepciones y `BaseRepository` | 1.5 h | `repositories/exceptions.py`, `base_repository.py` | `BaseRepository()` lanza `TypeError` |
| 6 | Repositorios concretos | 2 h | `repositories/*_repository.py` | `prueba_persistencia.py`: 12 de 12 |
| 7 | Seguridad con bcrypt | 1 h | `utils/security.py` | El hash del seed valida `Admin123` |
| 8 | Permisos y `AuthController` | 1.5 h | `controllers/exceptions.py`, `permisos.py`, `auth_controller.py` | Login correcto y rechazo con el mismo mensaje |
| 9 | Controladores de negocio | 2 h | `controllers/categoria_controller.py`, `producto_controller.py`, `usuario_controller.py` | Validaciones y permisos desde la consola |
| 10 | Ventana, login y `main.py` | 1.5 h | `views/app.py`, `views/login_view.py`, `main.py` | Se abre el login y se inicia sesión |
| 11 | Menú y componente `Tabla` | 1.5 h | `views/main_view.py`, `views/components/tabla.py` | El menú cambia según el rol |
| 12 | Pantalla de categorías | 1.5 h | `views/categorias_view.py` | CRUD completo desde la ventana |
| 13 | Pantalla de productos | 2 h | `views/productos_view.py` | Filtros, stock bajo y desactivar |
| 14 | Usuarios y *Mi cuenta* | 2 h | `views/usuarios_view.py`, `views/mi_cuenta_view.py` | El operador ve un menú reducido |
| 15 | Verificación de calidad | 1 h | — | Sin SQL en `views/`; PEP 8 sin advertencias |
| 16 | Ejecutable, README y diagramas | 1.5 h | `inventario.spec`, `README.md`, `docs/` | El ejecutable abre e inicia sesión |

El orden va de abajo hacia arriba en la arquitectura: primero la base de datos, luego la persistencia, después el negocio y al final la interfaz. Así, cada capa se prueba desde la consola antes de construir la que depende de ella, y cuando llega la interfaz ya no hay errores de SQL que depurar a través de una ventana.

## Paso 1 · Entorno y estructura del proyecto

**Objetivo:** dejar creadas todas las carpetas del proyecto, el entorno virtual y las dependencias instaladas. **Tiempo:** 1 hora.

**Archivos:** `requirements.txt`, `.gitignore` y un `__init__.py` vacío en cada paquete.

```bash
mkdir inventario_app && cd inventario_app
git init

# Carpetas de las capas
mkdir -p config models repositories controllers utils views/components database docs
touch config/__init__.py models/__init__.py repositories/__init__.py \
      controllers/__init__.py utils/__init__.py views/__init__.py views/components/__init__.py

# Entorno virtual
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

En Windows, `mkdir -p` y `touch` no existen en `cmd`. Cree las carpetas desde VS Code o use PowerShell: `New-Item -ItemType File config/__init__.py`.

`requirements.txt`:

```text
customtkinter>=5.2
mysql-connector-python>=8.3
python-dotenv>=1.0
bcrypt>=4.1
```

`.gitignore`:

```text
.env
__pycache__/
*.pyc
.venv/
venv/

# PyInstaller
build/
dist/
```

```bash
pip install -r requirements.txt
```

**Punto de verificación**

```bash
python -c "import customtkinter, mysql.connector, bcrypt, dotenv; print('ok')"
```

Resultado esperado: `ok`.

**Qué explicar**

- Dibuje en el pizarrón las capas y la carpeta de cada una: `views/` → `controllers/` → `repositories/` → `config/` → MySQL, con `models/` al costado porque todas lo usan. Deje el dibujo a la vista durante todo el curso.
- `__init__.py` convierte una carpeta en paquete, y eso permite escribir `from models.usuario import Usuario`.
- `.env` va en `.gitignore` desde el primer minuto: si alguna vez se sube una contraseña a Git, queda en el historial aunque después se borre.

**Errores frecuentes**

- `No module named '_tkinter'`: Python de Homebrew sin Tkinter. Se corrige con `brew install python-tk@<versión>` y recreando el `.venv`.
- `pip` instala en el Python del sistema: el entorno no estaba activo. La terminal debe mostrar `(.venv)`.

## Paso 2 · Base de datos con Docker

**Objetivo:** tener MySQL 8.4 funcionando con las cuatro tablas y los datos de prueba. **Tiempo:** 1.5 horas.

**Archivos:** `.env.example`, `.env`, `docker-compose.yml` y `database/mysql_DDL.sql`.

`.env.example` es la plantilla que sí va al repositorio:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=app_inventario
DB_PASSWORD=cambia_esta_contrasena
DB_NAME=curso_python_db
DB_POOL_SIZE=5
DB_ROOT_PASSWORD=cambia_esta_contrasena_root
APP_NAME=Sistema de Gestión de Inventario
APP_THEME=dark
```

Cada alumno lo copia como `.env` y cambia las contraseñas, usando solo letras, números, `_` y `-`.

`docker-compose.yml`:

```yaml
services:
  db:
    image: mysql:8.4
    container_name: inventario_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:?Defina DB_ROOT_PASSWORD en .env}
      MYSQL_DATABASE: ${DB_NAME:?Defina DB_NAME en .env}
      MYSQL_USER: ${DB_USER:?Defina DB_USER en .env}
      MYSQL_PASSWORD: ${DB_PASSWORD:?Defina DB_PASSWORD en .env}
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    ports:
      - "${DB_PORT:-3306}:3306"
    volumes:
      - ./database:/docker-entrypoint-initdb.d:ro   # el .sql se ejecuta en el primer arranque
      - mysql_datos:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -p$${MYSQL_ROOT_PASSWORD} --silent"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 20s

  adminer:                       # administrador web opcional: http://localhost:8080
    image: adminer:latest
    ports:
      - "8080:8080"
    environment:
      ADMINER_DEFAULT_SERVER: db
    depends_on:
      db:
        condition: service_healthy

volumes:
  mysql_datos:
```

`database/mysql_DDL.sql` se copia del proyecto de referencia. Muestre en pantalla estas partes:

- La primera línea, `SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;`. Sin ella, los acentos del seed se guardan dañados.
- La tabla `productos`: `DECIMAL(10, 2)`, los dos `CHECK`, el `UNIQUE` del SKU y la llave foránea con `ON DELETE RESTRICT`.
- El usuario administrador del seed, cuya contraseña es `Admin123`. El hash es real y se comprueba en el paso 7.

```bash
cp .env.example .env              # y editar las contraseñas
docker compose up -d
docker compose ps
```

**Punto de verificación:** `docker compose ps` muestra el servicio `db` como `running (healthy)`. En <http://localhost:8080> (servidor `db`, usuario y contraseña del `.env`) se ven las cuatro tablas, dos categorías y tres productos con los acentos correctos.

**Qué explicar**

- Docker y la aplicación leen el mismo `.env`; por eso las credenciales siempre coinciden.
- `MYSQL_USER` crea un usuario con permisos solo sobre esta base. La aplicación nunca usa `root`.
- El script SQL y las credenciales se aplican **solo** la primera vez que arranca el volumen. Si después se cambia cualquiera de los dos, hay que recrear: `docker compose down -v && docker compose up -d`.

**Errores frecuentes**

- `Cannot connect to the Docker daemon`: Docker Desktop cerrado.
- `required variable DB_NAME is missing a value`: Docker no encontró el `.env` (otra carpeta, nombre `.env.txt` o archivo guardado en UTF-16).
- `port is already allocated`: otro MySQL usa el 3306; cambie `DB_PORT=3307`.

## Paso 3 · Configuración y conexión

**Objetivo:** que Python lea el `.env` y se conecte a MySQL por un único punto de acceso. **Tiempo:** 1.5 horas.

**Archivos:** `config/settings.py` y `config/db_connection.py`.

**Estrategia en clase.** Construya `db_connection.py` en dos versiones. Primero, una sencilla que abre una conexión nueva en cada operación. Cuando funcione, reemplácela por la versión con *pool*. Ver la mejora sobre código que ya funciona se entiende mejor que recibir el *pool* desde el principio.

Primera versión de `config/settings.py` (en el paso 16 se amplía para el ejecutable):

```python
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR: Path = Path(__file__).resolve().parent.parent   # carpeta que contiene main.py
load_dotenv(BASE_DIR / ".env")

APP_NAME: str = os.getenv("APP_NAME", "Sistema de Gestión de Inventario")
APP_THEME: str = os.getenv("APP_THEME", "dark")
```

Primera versión de `config/db_connection.py`:

```python
import os
from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector import errorcode
from mysql.connector.constants import ClientFlag

from config import settings  # noqa: F401  (importarlo carga el .env)

REQUIRED_ENV_VARS = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")


class DatabaseConnectionError(Exception):
    """Error de conexión con un mensaje apto para el usuario."""


class DatabaseConnection:
    @staticmethod
    def _leer_configuracion() -> dict[str, Any]:
        faltantes = [v for v in REQUIRED_ENV_VARS if os.getenv(v) is None]
        if faltantes:
            raise DatabaseConnectionError(
                "Faltan variables en el .env: " + ", ".join(faltantes))
        return {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "autocommit": False,
            "client_flags": [ClientFlag.FOUND_ROWS],
            "use_pure": True,
        }

    @classmethod
    def conectar(cls):
        try:
            return mysql.connector.connect(**cls._leer_configuracion())
        except mysql.connector.Error as err:
            raise DatabaseConnectionError(cls._traducir_error(err)) from err

    @classmethod
    @contextmanager
    def obtener_conexion(cls) -> Iterator:
        conexion = cls.conectar()
        try:
            yield conexion
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @classmethod
    def probar_conexion(cls) -> tuple[bool, str]:
        try:
            with cls.obtener_conexion() as conexion:
                cursor = conexion.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()
                return True, f"Conectado a MySQL {version}"
        except DatabaseConnectionError as err:
            return False, str(err)

    @staticmethod
    def _traducir_error(err: mysql.connector.Error) -> str:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return "Usuario o contraseña de MySQL incorrectos (revise DB_USER y DB_PASSWORD)."
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            return f"La base de datos '{os.getenv('DB_NAME')}' no existe."
        if err.errno in (errorcode.CR_CONN_HOST_ERROR, errorcode.CR_UNKNOWN_HOST):
            return "No se pudo contactar al servidor MySQL. Verifique que esté en ejecución."
        return f"Error de base de datos ({err.errno}): {err.msg}"


if __name__ == "__main__":
    exito, mensaje = DatabaseConnection.probar_conexion()
    print(("[OK] " if exito else "[ERROR] ") + mensaje)
```

**Segunda versión: el *pool*.** Agregue un atributo de clase con el *pool* y un candado, y cambie `conectar()` para que pida la conexión al *pool*. `obtener_conexion()` no cambia: en una conexión del *pool*, `close()` la devuelve en lugar de cerrarla.

```python
import threading
from mysql.connector import pooling


class DatabaseConnection:
    _pool = None
    _candado = threading.Lock()

    @classmethod
    def _obtener_pool(cls) -> pooling.MySQLConnectionPool:
        with cls._candado:                       # el hilo del login y la ventana
            if cls._pool is None:
                try:
                    cls._pool = pooling.MySQLConnectionPool(
                        pool_name="inventario_pool",
                        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
                        pool_reset_session=True,
                        **cls._leer_configuracion(),
                    )
                except mysql.connector.Error as err:
                    raise DatabaseConnectionError(cls._traducir_error(err)) from err
            return cls._pool

    @classmethod
    def conectar(cls):
        try:
            return cls._obtener_pool().get_connection()
        except mysql.connector.errors.PoolError as err:
            raise DatabaseConnectionError("Todas las conexiones están ocupadas.") from err
        except mysql.connector.Error as err:
            raise DatabaseConnectionError(cls._traducir_error(err)) from err
```

La versión de referencia agrega validación de `DB_PORT` y `DB_POOL_SIZE`, un mensaje que indica dónde se buscó el `.env` y el caso en que el *pool* no logra reconectar. Puede copiarla completa al terminar la explicación.

**Punto de verificación**

```bash
python -m config.db_connection
```

Resultado esperado: `[OK] Conectado a MySQL 8.4.x`. Pruebe también los errores: detenga Docker (`docker compose stop`) y vuelva a ejecutar; debe aparecer el mensaje de servidor no disponible, no un *traceback*.

**Qué explicar**

- Por qué cada opción de conexión: `autocommit=False` obliga a confirmar cada escritura; `FOUND_ROWS` hace que un `UPDATE` sin cambios informe que encontró la fila; `use_pure=True` usa el *driver* en Python, que el ejecutable necesita (paso 16).
- El administrador de contexto: `with DatabaseConnection.obtener_conexion() as c:` garantiza `rollback` ante errores y la devolución de la conexión.
- `python -m config.db_connection` ejecuta el módulo como programa sin romper los `import` del paquete.

**Errores frecuentes**

- `Usuario o contraseña incorrectos` aunque el `.env` parece bien: el contenedor se creó con otras credenciales. `docker compose exec db printenv MYSQL_PASSWORD` muestra con cuáles; si difieren, `docker compose down -v && docker compose up -d`.
- `No module named 'config'`: el comando se ejecutó desde otra carpeta.

## Paso 4 · Modelos

**Objetivo:** representar cada tabla con una clase de datos pura, sin SQL ni interfaz. **Tiempo:** 1 hora.

**Archivos:** `models/rol.py`, `models/usuario.py`, `models/categoria.py` y `models/producto.py`.

Escriba `Usuario` en vivo y copie los otros tres, que siguen el mismo patrón:

```python
# models/usuario.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from models.rol import Rol


@dataclass
class Usuario:
    rol_id: int
    nombre: str
    email: str
    password_hash: str = field(default="", repr=False)   # no aparece al imprimir
    activo: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    rol: Optional[Rol] = None                             # se llena con un JOIN

    @classmethod
    def from_row(cls, fila: dict[str, Any]) -> Usuario:
        rol: Optional[Rol] = None
        if fila.get("rol_nombre") is not None:
            rol = Rol(id=fila["rol_id"], nombre=fila["rol_nombre"],
                      descripcion=fila.get("rol_descripcion"))
        return cls(
            id=fila.get("id"),
            rol_id=fila["rol_id"],
            nombre=fila["nombre"],
            email=fila["email"],
            password_hash=fila.get("password_hash", ""),
            activo=bool(fila.get("activo", True)),   # MySQL devuelve BOOLEAN como 0/1
            created_at=fila.get("created_at"),
            rol=rol,
        )

    @property
    def es_administrador(self) -> bool:
        return self.rol is not None and self.rol.nombre == "Administrador"
```

En `Producto`, el precio es `Decimal` y la conversión pasa por `str` (`precio=Decimal(str(fila["precio"]))`). Tiene además una propiedad calculada, `valor_inventario`, que devuelve `precio * stock`. `Categoria` agrega `total_productos`, un dato que no es columna de la tabla sino un `COUNT` que calcula la consulta.

**Punto de verificación**

```bash
python -c "from models.usuario import Usuario; print(Usuario.from_row({'id': 1, 'rol_id': 1, 'nombre': 'Ana', 'email': 'ana@x.edu', 'password_hash': 'secreto', 'activo': 1, 'rol_nombre': 'Administrador'}))"
```

Resultado esperado: el objeto impreso, con `activo=True`, su `rol=Rol(nombre='Administrador', ...)` y **sin** el `password_hash`.

**Qué explicar**

- `@dataclass` genera `__init__`, `__repr__` y `__eq__` a partir de los atributos anotados.
- `field(repr=False)` evita que el hash aparezca en *logs* o mensajes de depuración.
- `from_row` es un constructor alternativo (`@classmethod`) que traduce una fila de MySQL al objeto. Es el mismo patrón que `desde_dict` del Módulo 2 del manual.
- Aquí los modelos no validan: esa tarea es de los controladores (paso 9), porque varias reglas dependen de la base de datos o del usuario que hace el cambio.

**Errores frecuentes**

- `non-default argument follows default argument`: en un `dataclass`, los campos sin valor por defecto van primero.
- `NameError: Usuario` en la anotación de retorno: falta `from __future__ import annotations`.

## Paso 5 · Excepciones y `BaseRepository`

**Objetivo:** escribir una sola vez el código que todos los repositorios repiten: pedir la conexión, ejecutar, confirmar y traducir errores. **Tiempo:** 1.5 horas.

**Archivos:** `repositories/exceptions.py` y `repositories/base_repository.py`.

```python
# repositories/exceptions.py
class RepositoryError(Exception):
    """Error general al ejecutar una operación en la base de datos."""


class DuplicateEntryError(RepositoryError):
    """Se violó una restricción UNIQUE (por ejemplo, un email repetido)."""


class ForeignKeyError(RepositoryError):
    """Se referenció un registro inexistente o se intentó borrar uno en uso."""
```

```python
# repositories/base_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Optional, TypeVar

import mysql.connector
from mysql.connector import errorcode

from config.db_connection import DatabaseConnection
from repositories.exceptions import DuplicateEntryError, ForeignKeyError, RepositoryError

Parametros = tuple[Any, ...]
Fila = dict[str, Any]
T = TypeVar("T")                      # entidad que maneja cada repositorio


class BaseRepository(ABC, Generic[T]):
    NOMBRE_TABLA: ClassVar[str] = ""
    MENSAJES_ERROR: ClassVar[dict[int, str]] = {}

    @abstractmethod
    def obtener_por_id(self, registro_id: int) -> Optional[T]:
        """Toda subclase debe implementarlo."""

    def _consultar_uno(self, sql: str, parametros: Parametros = ()) -> Optional[Fila]:
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
        mensaje = self.MENSAJES_ERROR.get(err.errno)
        if err.errno == errorcode.ER_DUP_ENTRY:
            return DuplicateEntryError(mensaje or "El registro ya existe.")
        if err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return ForeignKeyError(mensaje or "Se hace referencia a un registro inexistente.")
        if err.errno == errorcode.ER_ROW_IS_REFERENCED_2:
            return ForeignKeyError(mensaje or "El registro está en uso y no puede eliminarse.")
        return RepositoryError(
            mensaje or f"Error en la tabla {self.NOMBRE_TABLA} ({err.errno}): {err.msg}")

    @staticmethod
    def _escapar_like(texto: str) -> str:
        """Hace que % y _ escritos por el usuario se busquen literalmente."""
        return texto.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
```

**Punto de verificación**

```bash
python -c "from repositories.base_repository import BaseRepository; BaseRepository()"
```

Resultado esperado: `TypeError: Can't instantiate abstract class BaseRepository without an implementation for abstract method 'obtener_por_id'`. Ese error es la prueba de que la abstracción funciona.

**Qué explicar**

- Los métodos con guión bajo son «protegidos»: los usan las subclases, no el resto del programa.
- Solo las escrituras llaman a `commit()`. Si algo falla antes, `obtener_conexion()` hace `rollback()`.
- `_traducir_error` convierte códigos de MySQL (1062, 1451, 1452) en excepciones con nombre. Desde aquí hacia arriba, ninguna capa necesita conocer esos números.
- `Generic[T]` permite escribir `ProductoRepository(BaseRepository[Producto])`, y el editor sabe que `obtener_por_id` devuelve un `Producto`.

**Errores frecuentes**

- Olvidar `conexion.commit()` en una escritura: el `INSERT` «funciona», pero el registro no aparece después.
- `cursor(dictionary=True)` solo en las lecturas; sin él, las filas llegan como tuplas y `from_row` falla con `TypeError`.

## Paso 6 · Repositorios concretos

**Objetivo:** un repositorio por tabla, con SQL parametrizado. **Tiempo:** 2 horas.

**Archivos:** `repositories/categoria_repository.py`, `producto_repository.py`, `usuario_repository.py` y `rol_repository.py`.

Escriba `CategoriaRepository` completo en vivo. Es el más corto e incluye las cinco operaciones:

```python
# repositories/categoria_repository.py
from __future__ import annotations

from typing import Any, Optional

from mysql.connector import errorcode

from models.categoria import Categoria
from repositories.base_repository import BaseRepository

# LEFT JOIN: incluye las categorías sin productos (con INNER JOIN desaparecerían).
_SELECT_CON_TOTAL = """
    SELECT c.id, c.nombre, c.descripcion, c.created_at,
           COUNT(p.id) AS total_productos
    FROM categorias AS c
    LEFT JOIN productos AS p ON p.categoria_id = c.id
"""
_GROUP_BY = " GROUP BY c.id, c.nombre, c.descripcion, c.created_at"


class CategoriaRepository(BaseRepository[Categoria]):
    NOMBRE_TABLA = "categorias"
    MENSAJES_ERROR = {
        errorcode.ER_DUP_ENTRY: "Ya existe una categoría con ese nombre.",
        errorcode.ER_ROW_IS_REFERENCED_2:
            "No se puede eliminar la categoría porque tiene productos asociados.",
    }

    def listar(self, texto: str = "") -> list[Categoria]:
        sql = _SELECT_CON_TOTAL
        parametros: tuple[Any, ...] = ()
        if texto:
            patron = f"%{self._escapar_like(texto)}%"   # el comodín va en el valor
            sql += " WHERE c.nombre LIKE %s OR c.descripcion LIKE %s"
            parametros = (patron, patron)
        sql += _GROUP_BY + " ORDER BY c.nombre"
        return [Categoria.from_row(f) for f in self._consultar_todos(sql, parametros)]

    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        sql = _SELECT_CON_TOTAL + " WHERE c.id = %s" + _GROUP_BY
        fila = self._consultar_uno(sql, (categoria_id,))
        return Categoria.from_row(fila) if fila else None

    def crear(self, categoria: Categoria) -> int:
        sql = "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)"
        categoria.id = self._insertar(sql, (categoria.nombre, categoria.descripcion))
        return categoria.id

    def actualizar(self, categoria: Categoria) -> bool:
        sql = "UPDATE categorias SET nombre = %s, descripcion = %s WHERE id = %s"
        parametros = (categoria.nombre, categoria.descripcion, categoria.id)
        return self._ejecutar_escritura(sql, parametros) > 0

    def eliminar(self, categoria_id: int) -> bool:
        sql = "DELETE FROM categorias WHERE id = %s"
        return self._ejecutar_escritura(sql, (categoria_id,)) > 0
```

`ProductoRepository.listar` muestra cómo armar un `WHERE` con filtros opcionales sin perder la parametrización. Lo que se concatena son fragmentos de SQL escritos en el código; los valores siempre van en la lista de parámetros:

```python
def listar(self, texto="", categoria_id=None, incluir_inactivos=False) -> list[Producto]:
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

    sql = _SELECT_BASE                      # SELECT … FROM productos p INNER JOIN categorias c …
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY p.nombre"
    return [Producto.from_row(f) for f in self._consultar_todos(sql, tuple(parametros))]
```

Copie del proyecto de referencia `UsuarioRepository` y `RolRepository`. De `UsuarioRepository` destaque dos métodos: `actualizar` no toca la contraseña (para eso existe `actualizar_password`), y `contar_activos_por_rol` servirá en el paso 9 para no dejar el sistema sin administradores.

**Punto de verificación:** copie `prueba_persistencia.py` de `material_curso/modulo4/inventario_app/` a la raíz del proyecto y ejecútelo.

```bash
python prueba_persistencia.py
```

Resultado esperado: `12 de 12 pruebas correctas`. El script prueba el CRUD, el `Decimal` exacto, el `JOIN`, el `UNIQUE`, la llave foránea, un intento de inyección, el *rollback* y `FOUND_ROWS`, y deja la base como estaba.

**Qué explicar**

- Demostración de inyección SQL: cambie un momento `listar` para concatenar el texto con un *f-string* y busque `' OR '1'='1`. Luego regrese a `%s` y repita. La diferencia se ve en la tabla de resultados.
- `(categoria_id,)` con coma: sin ella no es una tupla, sino un número entre paréntesis.
- `eliminar` no pregunta si hay productos: la llave foránea con `RESTRICT` lo impide y `MENSAJES_ERROR` da el mensaje.

**Errores frecuentes**

- `Not enough parameters for the SQL statement` (o, si sobran, Not all parameters were used): la cantidad de `%s` no coincide con la de parámetros.
- Guardar sin cambios devuelve `False` («el registro ya no existe»): falta `FOUND_ROWS` en la conexión (paso 3).

## Paso 7 · Seguridad con bcrypt

**Objetivo:** generar y verificar *hashes* de contraseña con una política mínima. **Tiempo:** 1 hora.

**Archivo:** `utils/security.py` (y `utils/__init__.py`).

```python
# utils/security.py
import bcrypt

BCRYPT_ROUNDS = 12
BCRYPT_MAX_BYTES = 72          # bcrypt solo procesa los primeros 72 bytes
MIN_PASSWORD_LENGTH = 8


class PasswordError(ValueError):
    """La contraseña no cumple las reglas para ser hasheada."""


def _a_bytes(password: str) -> bytes:
    if not password:
        raise PasswordError("La contraseña no puede estar vacía.")
    datos = password.encode("utf-8")
    if len(datos) > BCRYPT_MAX_BYTES:          # una "ñ" ocupa 2 bytes
        raise PasswordError(f"La contraseña excede el límite de {BCRYPT_MAX_BYTES} bytes.")
    return datos


def validar_politica(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise PasswordError("La contraseña debe combinar letras y números.")
    _a_bytes(password)


def hash_password(password: str) -> str:
    validar_politica(password)
    sal = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(_a_bytes(password), sal).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_a_bytes(password), password_hash.encode("utf-8"))
    except (PasswordError, ValueError):        # hash con formato inválido
        return False


if __name__ == "__main__":                      # python -m utils.security
    from getpass import getpass
    try:
        print(hash_password(getpass("Contraseña a hashear: ")))
    except PasswordError as err:
        print(f"[ERROR] {err}")
```

**Punto de verificación.** El *hash* del administrador en el seed debe validar `Admin123` (use comillas simples por fuera: el `$` tiene significado en la terminal).

```bash
python -c 'from utils.security import verify_password; print(verify_password("Admin123", "$2b$12$GbU6spXHM6SzD9RKidrIketco.0unEaobDVEobRxS8SzScb0.MVnS"))'
```

Resultado esperado: `True`. Después ejecute dos veces `python -m utils.security` con la misma contraseña.

**Qué explicar**

- Las dos ejecuciones dan *hashes* distintos para la misma contraseña: cada uno lleva su propia sal. `checkpw` la lee del propio *hash*, por eso no hay que guardarla aparte.
- Anatomía del *hash*: `$2b$` (versión), `12$` (costo: 2¹² iteraciones), 22 caracteres de sal y 31 de *hash*.
- bcrypt es lento a propósito (unos 0.25 s con costo 12). Para un usuario es imperceptible; para quien prueba millones de contraseñas, es un obstáculo enorme.
- La política se valida antes de hashear, porque después ya no se puede saber cómo era la contraseña.

**Errores frecuentes**

- `verify_password` devuelve `False` con la contraseña correcta: el *hash* del seed se copió incompleto (debe medir 60 caracteres).
- `TypeError: argument 'password': 'str' object cannot be converted to 'PyBytes'`: se pasó `str` a bcrypt en lugar de `bytes`.

## Paso 8 · Excepciones de negocio, permisos y `AuthController`

**Objetivo:** definir los errores que verá la interfaz, los permisos por rol y el inicio de sesión. **Tiempo:** 1.5 horas.

**Archivos:** `controllers/exceptions.py`, `controllers/permisos.py` y `controllers/auth_controller.py`.

```python
# controllers/exceptions.py
from typing import Optional


class ControllerError(Exception):
    """Error de negocio con un mensaje apto para la interfaz."""


class PermisoDenegadoError(ControllerError):
    """El usuario de la sesión no tiene autorización."""


class ValidationError(ControllerError):
    def __init__(self, mensaje: str, campo: Optional[str] = None) -> None:
        super().__init__(mensaje)
        self.campo = campo            # la vista lo usa para enfocar el control
```

```python
# controllers/permisos.py
from enum import Enum
from typing import Optional

from controllers.exceptions import PermisoDenegadoError
from models.usuario import Usuario

ROL_ADMINISTRADOR = "Administrador"
ROL_OPERADOR = "Operador"


class Permiso(Enum):
    GESTIONAR_CATEGORIAS = "gestionar_categorias"
    GESTIONAR_PRODUCTOS = "gestionar_productos"
    CAMBIAR_ESTADO_PRODUCTOS = "cambiar_estado_productos"
    GESTIONAR_USUARIOS = "gestionar_usuarios"


PERMISOS_POR_ROL: dict[str, frozenset[Permiso]] = {
    ROL_ADMINISTRADOR: frozenset(Permiso),                  # todos
    ROL_OPERADOR: frozenset({Permiso.GESTIONAR_PRODUCTOS}),
}


def tiene_permiso(usuario: Optional[Usuario], permiso: Permiso) -> bool:
    if usuario is None or usuario.rol is None or not usuario.activo:
        return False
    return permiso in PERMISOS_POR_ROL.get(usuario.rol.nombre, frozenset())


def exigir_permiso(usuario: Optional[Usuario], permiso: Permiso) -> None:
    if not tiene_permiso(usuario, permiso):
        raise PermisoDenegadoError("No tiene permisos para realizar esta operación.")
```

El corazón de `AuthController` es `iniciar_sesion`:

```python
MENSAJE_CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos."
_HASH_SENUELO = hash_password("senuelo-sin-usuario-2026")


class AuthError(ControllerError):
    """Error de autenticación."""


class AuthController:
    def __init__(self, repositorio: Optional[UsuarioRepository] = None) -> None:
        self._repositorio = repositorio or UsuarioRepository()
        self.usuario_actual: Optional[Usuario] = None

    def iniciar_sesion(self, email: str, password: str) -> Usuario:
        email = email.strip().lower()
        if not email or not password:
            raise AuthError("Ingrese su correo y su contraseña.")
        try:
            usuario = self._repositorio.obtener_por_email(email)
        except (DatabaseConnectionError, RepositoryError) as err:
            raise AuthError(f"No fue posible validar el acceso. {err}") from err

        # Si el correo no existe se verifica un hash señuelo: la respuesta tarda lo mismo.
        hash_guardado = usuario.password_hash if usuario else _HASH_SENUELO
        if usuario is None or not verify_password(password, hash_guardado):
            raise AuthError(MENSAJE_CREDENCIALES_INVALIDAS)
        if not usuario.activo:
            raise AuthError("Su cuenta está desactivada. Contacte al administrador.")
        self.usuario_actual = usuario
        return usuario
```

Copie del proyecto de referencia `cerrar_sesion`, la propiedad `hay_sesion` y `cambiar_password(actual, nueva, confirmacion)`, que se usará en la pantalla *Mi cuenta*.

**Punto de verificación.** Guarde este código como `prueba_login.py` en la raíz y ejecútelo:

```python
from controllers.auth_controller import AuthController, AuthError

auth = AuthController()
usuario = auth.iniciar_sesion("  ADMIN@escuela.edu ", "Admin123")
print("Sesión:", usuario.nombre, "·", usuario.rol.nombre)

for email, clave in [("admin@escuela.edu", "otra"), ("nadie@escuela.edu", "Admin123")]:
    try:
        auth.iniciar_sesion(email, clave)
    except AuthError as err:
        print(f"{email}: {err}")
```

Resultado esperado:

```text
Sesión: Admin Sistema · Administrador
admin@escuela.edu: Correo o contraseña incorrectos.
nadie@escuela.edu: Correo o contraseña incorrectos.
```

**Qué explicar**

- El mismo mensaje para «correo inexistente» y «contraseña incorrecta» impide averiguar qué correos están registrados. El *hash* señuelo cierra la otra vía: medir cuánto tarda la respuesta. En las pruebas del proyecto, ambos casos tardaron 0.280 s y 0.276 s.
- Todas las excepciones que llegan a la vista heredan de `ControllerError`; la vista solo necesita capturar esa.
- Los permisos viven en un solo diccionario. Agregar un rol nuevo es agregar una línea.

**Errores frecuentes**

- `ImportError` circular entre `permisos.py` y `exceptions.py`: `exceptions.py` no debe importar nada de `controllers/`.
- El correo con mayúsculas no entra: falta `.lower()` antes de buscarlo.

## Paso 9 · Controladores de categorías, productos y usuarios

**Objetivo:** concentrar validaciones, reglas y permisos en la capa de negocio. **Tiempo:** 2 horas.

**Archivos:** `controllers/categoria_controller.py`, `controllers/producto_controller.py` y `controllers/usuario_controller.py`.

Los tres siguen el mismo esquema, que conviene escribir en vivo con `CategoriaController`:

```python
class CategoriaController:
    def __init__(self, usuario_actual: Usuario, repositorio=None) -> None:
        self._actual = usuario_actual
        self._repositorio = repositorio or CategoriaRepository()

    def crear(self, nombre: str, descripcion: str = "") -> Categoria:
        exigir_permiso(self._actual, Permiso.GESTIONAR_CATEGORIAS)      # 1. permiso
        categoria = Categoria(nombre=self._validar_nombre(nombre),      # 2. validación
                              descripcion=self._validar_descripcion(descripcion))
        try:
            self._repositorio.crear(categoria)                           # 3. persistencia
        except (DatabaseConnectionError, RepositoryError) as err:
            raise ControllerError(str(err)) from err                     # 4. traducción
        return categoria

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        limpio = " ".join(nombre.split())           # quita espacios sobrantes
        if not limpio:
            raise ValidationError("El nombre es obligatorio.", campo="nombre")
        if not 2 <= len(limpio) <= 100:
            raise ValidationError("El nombre debe tener entre 2 y 100 caracteres.", campo="nombre")
        return limpio
```

Copie `ProductoController` y `UsuarioController` del proyecto de referencia y recórralos con el grupo. Las reglas que conviene señalar:

| Controlador | Regla | Dónde está |
| --- | --- | --- |
| Productos | SKU en mayúsculas: letras, números y guiones | `_validar_sku` |
| Productos | Precio `Decimal`, máximo dos decimales; `85,50` se rechaza para no guardar 8550 | `_validar_precio` |
| Productos | Stock entero no negativo | `_validar_stock` |
| Productos | Los errores se revisan en el orden del formulario | `_construir` |
| Productos | Solo el administrador activa o desactiva | `cambiar_estado` y la propiedad `puede_cambiar_estado` |
| Usuarios | Nadie se desactiva ni se quita el rol de administrador a sí mismo | `actualizar`, `cambiar_estado` |
| Usuarios | Siempre queda al menos un administrador activo | `_exigir_otro_admin` |
| Usuarios | La contraseña cumple la política y coincide con la confirmación | `_hash_validado` |

**Punto de verificación.** Este script prueba validaciones y permisos sin interfaz. Primero crea un operador de prueba; al terminar, bórrelo desde Adminer.

```python
from controllers.auth_controller import AuthController
from controllers.categoria_controller import CategoriaController
from controllers.exceptions import ControllerError, ValidationError
from controllers.producto_controller import ProductoController
from controllers.usuario_controller import UsuarioController

admin = AuthController().iniciar_sesion("admin@escuela.edu", "Admin123")
productos = ProductoController(admin)
UsuarioController(admin).crear("Luis Pérez", "luis@escuela.edu", 2, "Operador1", "Operador1")
operador = AuthController().iniciar_sesion("luis@escuela.edu", "Operador1")

pruebas = [
    ("precio con coma decimal", lambda: productos.crear("P-10", "Mouse", "85,50", "3", 1)),
    ("stock con decimales", lambda: productos.crear("P-10", "Mouse", "85.50", "2.5", 1)),
    ("SKU repetido", lambda: productos.crear("prod-001", "Mouse", "85.50", "3", 1)),
    ("borrar categoría con productos", lambda: CategoriaController(admin).eliminar(1)),
    ("operador crea categoría", lambda: CategoriaController(operador).crear("Limpieza")),
    ("admin se desactiva", lambda: UsuarioController(admin).cambiar_estado(admin.id, False)),
]
for nombre, accion in pruebas:
    try:
        accion()
    except ValidationError as err:
        print(f"{nombre}: {err} (campo: {err.campo})")
    except ControllerError as err:
        print(f"{nombre}: {err}")
```

Resultado esperado:

```text
precio con coma decimal: Use punto como separador decimal, p. ej. 85.50. (campo: precio)
stock con decimales: El stock debe ser un número entero, sin decimales. (campo: stock)
SKU repetido: Ya existe un producto con ese SKU.
borrar categoría con productos: No se puede eliminar la categoría porque tiene productos asociados.
operador crea categoría: No tiene permisos para realizar esta operación.
admin se desactiva: No puede desactivar su propia cuenta.
```

**Qué explicar**

- Los cuatro pasos de cada operación: permiso, validación, persistencia, traducción del error.
- El controlador recibe texto (lo que da un formulario) y devuelve objetos. Por eso se puede probar sin ventana, como en este script.
- El caso `85,50` salió al probar el proyecto: la primera versión quitaba todas las comas y guardaba $8,550.00. Es un buen ejemplo de por qué las pruebas deben incluir los errores de un usuario real.

**Errores frecuentes**

- Validar solo en la vista: la regla se pierde en cuanto otra pantalla llama al controlador.
- Capturar `Exception` en el controlador: oculta errores de programación. Capture solo `DatabaseConnectionError` y `RepositoryError`.

## Paso 10 · Ventana raíz, login y `main.py`

**Objetivo:** abrir la aplicación, verificar la base de datos al arrancar e iniciar sesión sin congelar la ventana. **Tiempo:** 1.5 horas.

**Archivos:** `views/app.py`, `views/login_view.py` y `main.py`.

`App` es la única ventana raíz. En lugar de abrir ventanas nuevas, cambia una pantalla (`CTkFrame`) por otra:

```python
# views/app.py (sin imports ni docstrings)
TAMANO_LOGIN = "480x520"
TAMANO_PRINCIPAL = "1100x680"


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.minsize(420, 480)
        self.auth_controller = AuthController()
        self._pantalla_actual: Optional[ctk.CTkFrame] = None
        self.mostrar_login()

    def _cambiar_pantalla(self, pantalla: ctk.CTkFrame, tamano: str) -> None:
        if self._pantalla_actual is not None:
            self._pantalla_actual.destroy()
        self._pantalla_actual = pantalla
        self.geometry(tamano)
        pantalla.pack(fill="both", expand=True)

    def mostrar_login(self) -> None:
        self._cambiar_pantalla(
            LoginView(self, self.auth_controller, on_login_exitoso=self._al_iniciar_sesion),
            TAMANO_LOGIN)

    def _al_iniciar_sesion(self, usuario: Usuario) -> None:
        self._cambiar_pantalla(
            MainView(self, self.auth_controller, on_cerrar_sesion=self._al_cerrar_sesion),
            TAMANO_PRINCIPAL)

    def _al_cerrar_sesion(self) -> None:
        self.auth_controller.cerrar_sesion()
        self.mostrar_login()
```

`MainView` se construye en el paso 11. Mientras tanto, para probar, `_al_iniciar_sesion` puede mostrar una pantalla provisional: `ctk.CTkLabel(frame, text=f"Bienvenido, {usuario.nombre}")` dentro de un `CTkFrame`.

```python
# main.py
import sys
from tkinter import messagebox

import customtkinter as ctk

from config.db_connection import DatabaseConnection
from config.settings import APP_NAME, APP_THEME
from views.app import App


def main() -> int:
    ctk.set_appearance_mode(APP_THEME)
    ctk.set_default_color_theme("blue")

    conectado, mensaje = DatabaseConnection.probar_conexion()
    if not conectado:                               # avisar antes de abrir un login inútil
        raiz = ctk.CTk()
        raiz.withdraw()
        messagebox.showerror(f"{APP_NAME} - Base de datos", mensaje, parent=raiz)
        raiz.destroy()
        return 1

    App().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**`LoginView` en dos versiones.** Primero haga que el botón llame directamente a `self._auth.iniciar_sesion(email, password)`. Funciona, pero detenga Docker y pruebe: la ventana se congela hasta 10 segundos mientras espera al servidor. Entonces reemplácelo por la versión con hilo:

```python
def _iniciar_sesion(self) -> None:
    if str(self.boton_ingresar.cget("state")) == "disabled":
        return                                           # ya hay una verificación en curso
    email, password = self.entry_email.get(), self.entry_password.get()
    self._mostrar_error("")
    self._set_ocupado(True)                              # deshabilita campos y botón
    threading.Thread(target=self._verificar_en_segundo_plano,
                     args=(email, password), daemon=True).start()
    self.after(50, self._revisar_resultado)

def _verificar_en_segundo_plano(self, email: str, password: str) -> None:
    """Corre en otro hilo: NO toca ningún widget, solo deja el resultado en la cola."""
    try:
        resultado = self._auth.iniciar_sesion(email, password)
    except AuthError as err:
        resultado = err
    self._resultados.put(resultado)

def _revisar_resultado(self) -> None:
    """Corre en el hilo de la ventana, cada 50 ms, hasta que llegue la respuesta."""
    try:
        resultado = self._resultados.get_nowait()
    except queue.Empty:
        self.after(50, self._revisar_resultado)
        return
    self._set_ocupado(False)
    if isinstance(resultado, AuthError):
        self._mostrar_error(str(resultado))
        self.entry_password.delete(0, "end")
    else:
        self._on_login_exitoso(resultado)
```

El resto de `LoginView` (la tarjeta centrada con `place(relx=0.5, rely=0.5, anchor="center")`, la casilla *Mostrar contraseña* y Enter para pasar de un campo a otro) se copia del proyecto de referencia.

**Punto de verificación**

```bash
python main.py
```

Se abre el login. Con `admin@escuela.edu` / `Admin123` aparece la pantalla de bienvenida; con una contraseña incorrecta, el mensaje en rojo y el campo de contraseña vacío. Con Docker detenido, `main.py` muestra un cuadro de error y termina.

**Qué explicar**

- Tkinter no es seguro con varios hilos: solo el hilo principal puede tocar widgets. La cola (`queue.Queue`) es el único canal entre los dos hilos.
- `after(50, función)` programa una llamada sin bloquear el ciclo de eventos. Es la forma correcta de «esperar» en una interfaz.
- `App` recibe callbacks (`on_login_exitoso`, `on_cerrar_sesion`) en lugar de que las pantallas se conozcan entre sí.

**Errores frecuentes**

- `RuntimeError: main thread is not in main loop`: el hilo secundario tocó un widget.
- Dos ventanas abiertas: se creó un segundo `ctk.CTk()` en lugar de cambiar de pantalla.

## Paso 11 · Menú principal y componente `Tabla`

**Objetivo:** un menú lateral que muestra solo los módulos del rol, y una tabla reutilizable con los colores del tema. **Tiempo:** 1.5 horas.

**Archivos:** `views/main_view.py` y `views/components/tabla.py`.

El menú se arma a partir de un registro de módulos. Cada módulo tiene una función que crea su pantalla y, opcionalmente, el permiso que exige:

```python
@dataclass(frozen=True)
class Modulo:
    fabrica: Callable[[ctk.CTkFrame], ctk.CTkFrame]
    permiso: Optional[Permiso] = None


class MainView(ctk.CTkFrame):
    def _registrar_modulos(self) -> None:
        todos = {
            "Inicio": Modulo(self._crear_inicio),
            "Categorías": Modulo(lambda c: CategoriasView(c, self._usuario),
                                 Permiso.GESTIONAR_CATEGORIAS),
            "Productos": Modulo(lambda c: ProductosView(c, self._usuario),
                                Permiso.GESTIONAR_PRODUCTOS),
            "Usuarios": Modulo(lambda c: UsuariosView(c, self._usuario),
                               Permiso.GESTIONAR_USUARIOS),
            "Mi cuenta": Modulo(lambda c: MiCuentaView(c, self._auth)),
        }
        self._modulos = {
            nombre: modulo for nombre, modulo in todos.items()
            if modulo.permiso is None or tiene_permiso(self._usuario, modulo.permiso)
        }

    def mostrar_modulo(self, nombre: str) -> None:
        if nombre not in self._modulos:
            return                                   # inexistente o sin permiso
        if self._pantalla_actual is not None:
            self._pantalla_actual.destroy()
        self._pantalla_actual = self._modulos[nombre].fabrica(self._contenido)
        self._pantalla_actual.pack(fill="both", expand=True)
```

En este paso registre solo *Inicio*. Cada módulo se agrega al diccionario cuando su pantalla existe (pasos 12 a 14). La barra superior con nombre, rol y *Cerrar sesión*, y los botones del menú, se copian del proyecto de referencia.

CustomTkinter no incluye tabla, y `ttk.Treeview` no sigue el tema claro u oscuro. `Tabla` envuelve un `Treeview` y le aplica colores:

```python
def _aplicar_estilo(self) -> None:
    estilo = ttk.Style(self)
    estilo.theme_use("clam")            # el único tema de ttk que acepta colores en todos los sistemas
    fondo, texto = self._color("fondo"), self._color("texto")
    estilo.layout("Tabla.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])   # sin borde
    estilo.configure("Tabla.Treeview", background=fondo, fieldbackground=fondo,
                     foreground=texto, rowheight=28, borderwidth=0)
    estilo.map("Tabla.Treeview", background=[("selected", self._color("seleccion"))],
               foreground=[("selected", "#FFFFFF")])

def cargar(self, filas, etiquetas=None) -> None:
    """filas = [(id, (valor1, valor2, ...)), ...]; etiquetas = {id: "stock_bajo"}."""
    etiquetas = etiquetas or {}
    self.tree.delete(*self.tree.get_children())
    for indice, (registro_id, valores) in enumerate(filas):
        tags = ["alterna"] if indice % 2 else []          # filas alternadas
        if registro_id in etiquetas:
            tags.append(etiquetas[registro_id])
        self.tree.insert("", "end", iid=str(registro_id), values=list(valores), tags=tags)
```

Cada fila usa el `id` del registro como `iid`. Así, `id_seleccionado()` devuelve el registro elegido sin depender de la posición de la fila.

**Punto de verificación.** Con `python main.py`, al iniciar sesión aparece la barra superior con *Admin Sistema · Administrador*, el menú con *Inicio* y la bienvenida. *Cerrar sesión* vuelve al login.

**Qué explicar**

- El menú usa `tiene_permiso()` para decidir qué mostrar; los controladores usan `exigir_permiso()` para decidir qué permitir. Son dos protecciones distintas.
- Agregar un módulo nuevo es agregar una línea al diccionario.
- `lambda c: CategoriasView(c, self._usuario)` crea la pantalla hasta que el usuario la elige, no al construir el menú.

**Errores frecuentes**

- La tabla se ve blanca en tema oscuro: falta `theme_use("clam")`; los temas nativos de Windows y macOS ignoran los colores.
- Todos los botones del menú abren el último módulo: la `lambda` dentro del ciclo no fija el valor (`command=lambda n=nombre: self.mostrar_modulo(n)`).

## Paso 12 · Pantalla de categorías

**Objetivo:** el primer CRUD completo desde la ventana. Sirve de plantilla para productos y usuarios. **Tiempo:** 1.5 horas.

**Archivo:** `views/categorias_view.py`, y la línea de *Categorías* en el registro de módulos de `MainView`.

**Estructura de la pantalla.** Con `grid()`: título arriba, a la izquierda el buscador y la `Tabla`, a la derecha un panel de ancho fijo con el formulario (nombre, descripción en un `CTkTextbox`, mensaje y tres botones: *Guardar*, *Nueva*, *Eliminar*). La vista guarda `_id_edicion`: `None` significa «creando»; un número, «editando esa categoría».

Escriba en vivo `_guardar`, que muestra cómo la vista usa las excepciones del controlador:

```python
def _guardar(self) -> None:
    nombre = self.entry_nombre.get()
    descripcion = self.text_descripcion.get("1.0", "end-1c")     # sin el salto final
    try:
        if self._id_edicion is None:
            categoria = self._controlador.crear(nombre, descripcion)
            mensaje = f"Categoría «{categoria.nombre}» creada."
        else:
            categoria = self._controlador.actualizar(self._id_edicion, nombre, descripcion)
            mensaje = "Cambios guardados."
    except ValidationError as err:
        self._mostrar_mensaje(str(err), COLOR_ERROR)
        self._enfocar_campo(err.campo)                             # cursor al campo con error
        return
    except ControllerError as err:
        self._mostrar_mensaje(str(err), COLOR_ERROR)
        return

    self._id_edicion = None
    self._cargar_categorias(seleccionar_id=categoria.id)
    self._al_seleccionar(categoria.id)                             # formulario en modo edición
    self._mostrar_mensaje(mensaje, COLOR_EXITO)


def _al_seleccionar(self, categoria_id: Optional[int]) -> None:
    categoria = self._categorias.get(categoria_id) if categoria_id is not None else None
    if categoria is None or categoria.id == self._id_edicion:
        return      # ver «Qué explicar»: evita que un evento tardío borre el mensaje
    self._id_edicion = categoria.id
    self._llenar_formulario(categoria.nombre, categoria.descripcion or "")
    self.label_titulo_form.configure(text="Editar categoría")
    self._activar_eliminar(True)
    self._mostrar_mensaje("")
```

`_eliminar` revisa `total_productos` antes de preguntar. Si la categoría tiene productos, lo explica sin mostrar la confirmación; si no, pide confirmación con `messagebox.askyesno` antes de llamar al controlador. El buscador filtra al escribir, pero espera 300 ms de pausa (`after` + `after_cancel`) para no consultar MySQL en cada tecla.

**Punto de verificación**

1. Guardar con el nombre vacío muestra *El nombre es obligatorio.* y deja el cursor en ese campo.
2. Crear «  Limpieza   y hogar » guarda «Limpieza y hogar», la selecciona en la tabla y muestra el mensaje verde.
3. Guardar sin cambiar nada muestra *Cambios guardados.* (si dice que el registro no existe, falta `FOUND_ROWS`).
4. Crear «OFICINA» muestra *Ya existe una categoría con ese nombre.*
5. Seleccionar Electrónica y pulsar *Eliminar* explica que tiene 2 productos.
6. Eliminar «Limpieza y hogar» pide confirmación y la quita de la tabla.
7. Buscar `%` no muestra nada: el comodín se busca como texto.

**Qué explicar**

- La vista no valida ni conoce MySQL: llama al controlador y muestra lo que este responde.
- El detalle de `_al_seleccionar`: al seleccionar una fila por código, Tkinter entrega el evento `<<TreeviewSelect>>` un instante después. Sin la condición `categoria.id == self._id_edicion`, ese evento tardío recargaría el formulario y borraría el mensaje de éxito. Este error apareció al probar el proyecto; vale la pena mostrarlo quitando la condición.
- Retroalimentación en cada acción: mensaje verde o rojo, fila seleccionada, botón *Eliminar* gris cuando no hay nada que eliminar.

**Errores frecuentes**

- La descripción se guarda con un salto de línea al final: se leyó con `"end"` en lugar de `"end-1c"`.
- La columna *Productos* queda fuera de la vista: los anchos iniciales de las columnas suman más que el espacio disponible.

## Paso 13 · Pantalla de productos

**Objetivo:** aplicar la plantilla de categorías a una entidad con más campos, filtros y reglas por rol. **Tiempo:** 2 horas.

**Archivo:** `views/productos_view.py`, y la línea de *Productos* en `MainView`.

Como la estructura ya es conocida, conviene copiar el archivo del proyecto de referencia y dedicar la clase a sus cuatro novedades:

1. **Lista desplegable de categorías.** `CTkOptionMenu` trabaja con textos, así que la vista guarda un diccionario `nombre → id` y envía al controlador el id: `self._categorias_por_nombre.get(self.menu_categoria.get())`. Si no hay selección, envía `None` y el controlador responde *Seleccione una categoría.*
2. **Filtros combinados.** Buscador, categoría y *Mostrar inactivos* se pasan juntos a `ProductoController.listar()`, que los traduce al `WHERE` del paso 6.
3. **Colores por fila.** Se usan las etiquetas de `Tabla`:

```python
for p in productos:
    bajo = self._controlador.es_stock_bajo(p)
    nombre = p.nombre if p.activo else f"{p.nombre} (inactivo)"
    stock = f"{p.stock} (bajo)" if bajo and p.activo else str(p.stock)
    filas.append((p.id, (p.sku, nombre, p.categoria_nombre, f"${p.precio:,.2f}", stock)))
    if not p.activo:
        etiquetas[p.id] = "inactivo"          # gris
    elif bajo:
        etiquetas[p.id] = "stock_bajo"        # naranja
self.tabla.cargar(filas, etiquetas)
```

El texto «(bajo)» acompaña al color para que la información no dependa solo del color.

4. **Botón según el rol.** *Desactivar* / *Activar* solo se coloca en la pantalla si `self._controlador.puede_cambiar_estado`. El controlador vuelve a verificar el permiso al ejecutar la acción.

**Punto de verificación**

1. Con los datos del seed, el resumen al pie dice *3 productos · 1 con stock bajo (≤ 5) · valor en inventario: $3,902.50*, y la Silla ergonómica aparece en naranja con «5 (bajo)».
2. Crear un producto sin categoría muestra *Seleccione una categoría.*; con precio `85,50`, *Use punto como separador decimal*.
3. Crear `prod-004` con precio `$1,250.5` lo guarda como `PROD-004` a $1,250.50.
4. Desactivar ese producto lo quita de la lista; con *Mostrar inactivos* aparece en gris con «(inactivo)».
5. Filtrar por Oficina muestra solo la Silla ergonómica.

**Qué explicar**

- Desactivar en lugar de borrar (baja lógica): conserva el historial y, cuando existan ventas o movimientos, evita dejarlos sin producto.
- `Decimal` de punta a punta: MySQL `DECIMAL(10,2)` → `Producto.precio` → formato `f"${precio:,.2f}"`.
- Una categoría con productos inactivos tampoco se puede eliminar: la llave foránea los sigue contando, y es lo correcto.

**Errores frecuentes**

- Después de guardar, el producto no aparece: quedó fuera de los filtros activos. La vista de referencia lo avisa en el mensaje.
- El botón *Desactivar* aparece para el operador: se ocultó con `configure(state="disabled")` en lugar de no colocarlo con `grid()`.

## Paso 14 · Usuarios y *Mi cuenta*

**Objetivo:** que el administrador gestione usuarios y que cada usuario cambie su propia contraseña. **Tiempo:** 2 horas.

**Archivos:** `views/usuarios_view.py`, `views/mi_cuenta_view.py`, y las líneas de *Usuarios* y *Mi cuenta* en `MainView`.

`UsuariosView` sigue la misma plantilla, pero su formulario usa un `CTkTabview` con dos pestañas: *Datos* (nombre, correo, rol) y *Contraseña*. Al crear un usuario, la contraseña inicial se escribe en la segunda pestaña y se guarda con *Guardar*. Al editar, esa pestaña muestra el botón *Restablecer contraseña*.

El método que conviene escribir en vivo es el que lleva al usuario hasta el error, aunque esté en la otra pestaña:

```python
def _enfocar_campo(self, campo: Optional[str]) -> None:
    if campo in ("password", "confirmacion"):
        self.tabs.set("Contraseña")
        destino = self.entry_password if campo == "password" else self.entry_confirmacion
    else:
        self.tabs.set("Datos")
        destino = {"email": self.entry_email, "rol": self.menu_rol}.get(campo or "", self.entry_nombre)
    destino.focus_set()
```

En la fila del propio usuario, la vista muestra «(usted)» y bloquea el rol y el botón de estado. El controlador ya lo impide; la vista solo evita que el usuario lo intente.

`MiCuentaView` es la pantalla más corta: muestra nombre, correo y rol, y un formulario de tres campos que llama a `AuthController.cambiar_password(actual, nueva, confirmacion)`.

**Punto de verificación**

1. Como administrador, crear «Luis Pérez» (`LUIS@escuela.edu`, rol Operador) sin contraseña: la vista cambia sola a la pestaña *Contraseña* con el mensaje de la política.
2. Con contraseña `Operador1` en ambos campos, se crea con el correo en minúsculas.
3. En la fila *Admin Sistema (usted)*, el rol y el botón *Desactivar* están bloqueados.
4. Cerrar sesión y entrar como `luis@escuela.edu`: el menú solo tiene *Inicio*, *Productos* y *Mi cuenta*, y en *Productos* no aparece *Desactivar*.
5. En *Mi cuenta*, cambiar la contraseña con una confirmación distinta muestra *La confirmación no coincide con la contraseña nueva.*; con la correcta, el mensaje verde.

**Qué explicar**

- `CTkTabview` agrupa campos relacionados sin agrandar la ventana. El costo es que un error puede quedar en una pestaña oculta; por eso la vista cambia de pestaña.
- Restablecer (administrador, sin conocer la anterior) y cambiar (el propio usuario, con la actual) son operaciones distintas, en controladores distintos.
- Las reglas «no desactivarse a sí mismo» y «al menos un administrador» evitan que el sistema quede sin nadie que pueda gestionarlo.

**Errores frecuentes**

- Un usuario desactivado sigue trabajando: la sesión ya estaba abierta. Al volver a iniciar sesión, el login lo rechaza.
- *Mi cuenta* acepta cualquier contraseña nueva: se llamó al repositorio directamente en lugar de a `cambiar_password`, que valida la política.

## Paso 15 · Verificación de calidad

**Objetivo:** comprobar con herramientas, no a ojo, que la aplicación cumple la arquitectura y el estilo. **Tiempo:** 1 hora.

Ejecute estas revisiones frente al grupo. Son las mismas que se usan para calificar el proyecto final.

```bash
# 1. Ninguna vista usa MySQL ni repositorios, ni contiene SQL
grep -rn "mysql\|db_connection\|repositories" views/          # no debe imprimir nada
grep -rniE "\b(SELECT|INSERT|UPDATE|DELETE) " views/           # no debe imprimir nada

# 2. Ningún controlador importa el driver
grep -rln "import mysql" controllers/                         # no debe imprimir nada

# 3. Estilo y errores comunes
pip install pycodestyle pyflakes
pycodestyle --max-line-length=100 --exclude=.venv,build,dist .
pyflakes config models repositories controllers utils views main.py

# 4. Pruebas de las capas
python prueba_persistencia.py                                  # 12 de 12
python prueba_login.py
```

En Windows, `grep` no existe en `cmd`. Use `findstr /S /N "mysql repositories db_connection" views\*.py` o la búsqueda de VS Code (Ctrl+Shift+F) limitada a la carpeta `views`.

Si todavía usa la versión sencilla de `db_connection.py` del paso 3, `pyflakes` avisará que `config.settings` se importa sin usarse. Es intencional: importarlo carga el `.env`, y el comentario `# noqa: F401` documenta esa decisión. En la versión final el módulo sí se usa (para indicar dónde se buscó el `.env`) y el aviso desaparece. En el proyecto de referencia, las cuatro revisiones terminan sin ningún mensaje.

**Recorrido manual.** Además de los comandos, recorra la aplicación con esta lista:

- [ ] Arrancar con Docker detenido: aparece un cuadro de error claro y la aplicación termina.
- [ ] Iniciar sesión con correo en mayúsculas y espacios: entra.
- [ ] Operador: menú reducido y sin *Desactivar* en productos.
- [ ] Cada formulario: un error por campo, con el cursor en ese campo.
- [ ] Tema claro y oscuro (`APP_THEME` en `.env`): todo se lee, incluida la tabla.
- [ ] Ninguna acción muestra un *traceback* ni un código de MySQL.

**Punto de verificación:** los tres `grep` no imprimen nada, `pycodestyle` no da advertencias, las pruebas pasan y la lista manual está completa.

**Qué explicar**

- Una regla de arquitectura que se puede verificar con un comando es una regla que se puede exigir. Es el argumento para escribirlas así.
- Las pruebas de consola de los pasos 6, 8 y 9 siguen siendo útiles: si una pantalla falla, dicen en segundos si el problema está en la interfaz o en las capas de abajo.

## Paso 16 · Ejecutable, README y diagramas

**Objetivo:** empaquetar la aplicación, documentar cómo instalarla y generar los diagramas del entregable. **Tiempo:** 1.5 horas.

**Archivos:** versión final de `config/settings.py`, `inventario.spec`, `requirements-dev.txt`, `build_mac.sh`, `build_windows.bat`, `README.md` y `docs/`.

**1. Dónde busca el ejecutable su `.env`.** Dentro de un ejecutable, `__file__` apunta a una carpeta interna, y el `.env` no debe empaquetarse (cualquiera podría extraer las contraseñas). Reemplace `settings.py` por la versión del proyecto de referencia. Su idea central es esta:

```python
EMPAQUETADO = bool(getattr(sys, "frozen", False))     # solo existe dentro del ejecutable
BASE_DIR = Path(sys.executable).resolve().parent if EMPAQUETADO \
    else Path(__file__).resolve().parent.parent

# Se usa el primero que exista: INVENTARIO_ENV, junto al ejecutable,
# junto a la .app (macOS) o la carpeta de configuración del usuario.
RUTAS_ENV_BUSCADAS = _rutas_candidatas()
ARCHIVO_ENV = next((r for r in RUTAS_ENV_BUSCADAS if r.is_file()), None)
if ARCHIVO_ENV is not None:
    load_dotenv(ARCHIVO_ENV)
```

**2. La especificación de PyInstaller.** Lo más importante de `inventario.spec` son los módulos que PyInstaller no detecta solo:

```python
from PyInstaller.utils.hooks import collect_submodules

modulos_ocultos = [
    "mysql.connector.plugins.caching_sha2_password",   # autenticación de MySQL 8
    "mysql.connector.plugins.mysql_native_password",
    "mysql.connector.plugins.sha256_password",
    "mysql.connector.plugins.mysql_clear_password",
    *collect_submodules("mysql.connector.locales"),    # textos de los mensajes de error
]
```

El resto del archivo se copia del proyecto de referencia: modo carpeta (*onedir*), sin consola y, en macOS, el bloque `BUNDLE` que crea la `.app`.

```bash
pip install -r requirements-dev.txt          # agrega PyInstaller
./build_mac.sh                                # macOS → dist/Inventario.app
build_windows.bat                             # Windows → dist\Inventario\Inventario.exe
```

**Punto de verificación:** copie el `.env` junto al ejecutable (en macOS, junto a `Inventario.app`), abra la aplicación con doble clic e inicie sesión. Sin `.env`, debe aparecer un mensaje con las rutas donde lo buscó.

**3. README y diagramas.** Tome como modelo el `README.md` del proyecto de referencia: requisitos, variables del `.env`, instalación con Docker, cómo compilar, estructura y problemas frecuentes. Los diagramas ER y UML están en `docs/diagramas/` como archivos Mermaid (`.mmd`); se ven en <https://mermaid.live> y se regeneran con `mmdc -i archivo.mmd -o archivo.png -b white` (paquete `@mermaid-js/mermaid-cli` de npm).

**Qué explicar**

- PyInstaller no compila para otro sistema operativo: la `.app` se genera en macOS y el `.exe` en Windows.
- Por qué `use_pure=True` desde el paso 3: la primera prueba del ejecutable falló con *Authentication plugin … cannot be loaded*, porque la extensión en C del *driver* busca sus plugins como bibliotecas del sistema, que no se empaquetan. Es un buen caso para mostrar cómo un error del ejecutable se rastrea hasta una decisión de configuración.
- Para distribuir en Windows se comprime la carpeta `dist\Inventario` completa: el `.exe` necesita la carpeta `_internal` que está a su lado.

**Errores frecuentes**

- La `.app` se abre y se cierra sin ventana: Python de Homebrew con Tk 9. Compile con el Python 3.12 de python.org, que trae Tk 8.6.
- macOS dice que la aplicación «no se puede abrir» al copiarla a otra Mac: no está firmada. Clic derecho → *Abrir* la primera vez.
