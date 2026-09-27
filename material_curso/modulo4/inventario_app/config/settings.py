"""
Configuración global de la aplicación.

Este módulo es el único que carga el archivo ``.env``. Las credenciales de la
base de datos NO se exponen aquí como constantes: las lee
``config.db_connection``, que además valida que existan. Este archivo solo
guarda constantes generales y la ubicación del ``.env`` que se usó.

Dónde se busca el ``.env``
--------------------------
Al ejecutar con ``python main.py`` basta con la raíz del proyecto. En cambio,
cuando la aplicación se empaqueta con PyInstaller, el código queda dentro del
ejecutable y ``__file__`` apunta a una carpeta interna. Además, **el ``.env``
no debe empaquetarse**: cualquiera podría extraer las credenciales del
ejecutable. Por eso se buscan, en este orden:

1. La ruta indicada en la variable de entorno ``INVENTARIO_ENV``.
2. La carpeta del ejecutable (o del proyecto, si no está empaquetado).
3. En macOS, la carpeta que contiene ``Inventario.app``.
4. La carpeta de configuración del usuario:
   ``~/Library/Application Support/Inventario`` (macOS),
   ``%APPDATA%\\Inventario`` (Windows) o ``~/.config/inventario`` (Linux).

Se usa el primer archivo que exista. Las variables ya definidas en el sistema
operativo tienen prioridad sobre las del archivo.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

APP_ID: str = "Inventario"  # nombre de la carpeta de configuración y del ejecutable

# ``sys.frozen`` solo existe dentro de un ejecutable generado por PyInstaller.
EMPAQUETADO: bool = bool(getattr(sys, "frozen", False))

if EMPAQUETADO:
    # Carpeta donde está el ejecutable (en macOS: Inventario.app/Contents/MacOS).
    BASE_DIR: Path = Path(sys.executable).resolve().parent
else:
    # Raíz del proyecto (la carpeta que contiene main.py).
    BASE_DIR = Path(__file__).resolve().parent.parent


def _carpeta_config_usuario() -> Path:
    """Carpeta de configuración del usuario según el sistema operativo."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    if sys.platform.startswith("win"):
        return Path(os.getenv("APPDATA", Path.home())) / APP_ID
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_ID.lower()


def _rutas_candidatas() -> list[Path]:
    """Lista, en orden de prioridad, los lugares donde puede estar el .env."""
    rutas: list[Path] = []
    explicita = os.getenv("INVENTARIO_ENV")
    if explicita:
        rutas.append(Path(explicita).expanduser())
    rutas.append(BASE_DIR / ".env")
    if EMPAQUETADO and sys.platform == "darwin":
        # BASE_DIR = .../Inventario.app/Contents/MacOS → subir tres niveles.
        rutas.append(BASE_DIR.parents[2] / ".env")
    rutas.append(_carpeta_config_usuario() / ".env")
    return rutas


RUTAS_ENV_BUSCADAS: list[Path] = _rutas_candidatas()
ARCHIVO_ENV: Optional[Path] = next((r for r in RUTAS_ENV_BUSCADAS if r.is_file()), None)

if ARCHIVO_ENV is not None:
    load_dotenv(ARCHIVO_ENV)

# --- Aplicación ------------------------------------------------------------
APP_NAME: str = os.getenv("APP_NAME", "Sistema de Gestión de Inventario")
APP_THEME: str = os.getenv("APP_THEME", "dark")  # "dark", "light" o "system"
