"""
Punto de entrada de la aplicación.

Ejecutar desde la carpeta raíz del proyecto:

    python main.py

Antes de abrir la interfaz se comprueba la conexión a la base de datos. Si
falla, se muestra el motivo en un cuadro de diálogo y el programa termina,
en lugar de dejar que el usuario llegue a un login que no podría funcionar.
"""

import sys
from tkinter import messagebox

import customtkinter as ctk

from config.db_connection import DatabaseConnection
from config.settings import APP_NAME, APP_THEME
from views.app import App


def main() -> int:
    """
    Configura la apariencia, verifica la base de datos y abre la ventana.

    Returns:
        int: Código de salida del proceso (0 = correcto, 1 = error).
    """
    ctk.set_appearance_mode(APP_THEME)
    ctk.set_default_color_theme("blue")

    conectado, mensaje = DatabaseConnection.probar_conexion()
    if not conectado:
        # messagebox necesita una ventana raíz; se crea una oculta.
        raiz = ctk.CTk()
        raiz.withdraw()
        messagebox.showerror(f"{APP_NAME} - Base de datos", mensaje, parent=raiz)
        raiz.destroy()
        return 1

    print(f"[INFO] {mensaje}")
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
