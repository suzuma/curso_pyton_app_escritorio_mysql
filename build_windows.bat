@echo off
REM Genera dist\Inventario\Inventario.exe en Windows.
REM Uso, desde la raiz del proyecto:  build_windows.bat
setlocal
cd /d "%~dp0"

if not exist .venv (
    echo Creando entorno virtual...
    py -3 -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat || goto :error
pip install -q -r requirements-dev.txt || goto :error

python -m PyInstaller --noconfirm --clean inventario.spec || goto :error

REM Plantilla de configuracion junto al ejecutable.
copy /Y .env.example dist\Inventario\.env.example >nul

echo.
echo Listo: dist\Inventario\Inventario.exe
echo Antes de abrirlo, copie su .env a una de estas ubicaciones:
echo   * dist\Inventario\.env           (junto a Inventario.exe)
echo   * %%APPDATA%%\Inventario\.env
echo Para distribuirlo, comprima la carpeta dist\Inventario completa.
exit /b 0

:error
echo.
echo ERROR: la compilacion fallo. Revise los mensajes anteriores.
exit /b 1
