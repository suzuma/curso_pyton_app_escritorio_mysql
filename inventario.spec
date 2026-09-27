# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de PyInstaller para el Sistema de Gestión de Inventario.

Uso (con el entorno virtual activado, desde la raíz del proyecto):

    python -m PyInstaller --noconfirm --clean inventario.spec

Resultado:
    macOS    dist/Inventario.app
    Windows  dist/Inventario/Inventario.exe
    Linux    dist/Inventario/Inventario

PyInstaller no compila para otro sistema: el .exe se genera en Windows y la
.app en macOS.

Se usa el modo "carpeta" (onedir) en lugar de "un solo archivo" (onefile):
arranca más rápido, porque no descomprime todo en una carpeta temporal cada
vez, y es el formato que macOS necesita para crear la .app.

El archivo .env NO se incluye. Las credenciales quedarían dentro del
ejecutable y cualquiera podría extraerlas. La aplicación busca el .env
afuera (ver config/settings.py).
"""

import sys

from PyInstaller.utils.hooks import collect_submodules

NOMBRE_APP = "Inventario"
VERSION = "1.0.0"

# mysql-connector carga en tiempo de ejecución, por nombre, el plugin de
# autenticación que pide el servidor (MySQL 8 usa caching_sha2_password) y el
# archivo con los textos de sus mensajes de error. Como no hay un "import"
# explícito, PyInstaller no los detecta solo y hay que declararlos.
modulos_ocultos = [
    "mysql.connector.plugins.caching_sha2_password",
    "mysql.connector.plugins.mysql_native_password",
    "mysql.connector.plugins.sha256_password",
    "mysql.connector.plugins.mysql_clear_password",
    *collect_submodules("mysql.connector.locales"),
]

# CustomTkinter (temas JSON, fuentes) y bcrypt ya tienen "hooks" en
# pyinstaller-hooks-contrib, que se instala junto con PyInstaller.

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=modulos_ocultos,
    hookspath=[],
    runtime_hooks=[],
    # Módulos que no usa la aplicación; excluirlos reduce el tamaño.
    excludes=["pytest", "unittest", "pydoc", "mysql.connector.django"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOMBRE_APP,
    console=False,  # aplicación de ventana: sin terminal detrás
    debug=False,
    strip=False,
    upx=False,
)

coleccion = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=NOMBRE_APP,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coleccion,
        name=f"{NOMBRE_APP}.app",
        bundle_identifier="edu.curso.inventario",
        version=VERSION,
        info_plist={
            "CFBundleDisplayName": "Inventario",
            "CFBundleShortVersionString": VERSION,
            "NSHighResolutionCapable": True,  # texto nítido en pantallas Retina
        },
    )
