#!/usr/bin/env bash
# Genera dist/Inventario.app en macOS.
# Uso, desde la raíz del proyecto:  ./build_mac.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements-dev.txt

python -c "import tkinter" 2>/dev/null || {
  echo "ERROR: este Python no tiene Tkinter. Con Homebrew: brew install python-tk@3.14" >&2
  exit 1
}

python -m PyInstaller --noconfirm --clean inventario.spec

# Plantilla de configuración junto a la aplicación.
cp .env.example dist/.env.example

echo
echo "Listo: dist/Inventario.app"
echo "Antes de abrirla, copie su .env a una de estas ubicaciones:"
echo "  • dist/.env                      (junto a Inventario.app)"
echo "  • ~/Library/Application Support/Inventario/.env"
