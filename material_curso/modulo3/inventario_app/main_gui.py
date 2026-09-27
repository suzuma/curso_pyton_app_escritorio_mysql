"""
Punto de entrada de la interfaz gráfica (Módulo 3).

Ejecutar desde la carpeta inventario_app:  python main_gui.py
"""

import customtkinter as ctk

from main_consola import cargar_ejemplos
from repositories.producto_repository import RepositorioProductosMemoria
from views.productos_view import ProductosView


def main() -> None:
    ctk.set_appearance_mode("system")      # "light", "dark" o "system"
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()                        # única ventana raíz del programa
    app.title("Inventario · Módulo 3")
    app.geometry("1000x560")
    app.minsize(820, 480)

    repositorio = RepositorioProductosMemoria()
    cargar_ejemplos(repositorio)

    ProductosView(app, repositorio).pack(fill="both", expand=True, padx=16, pady=16)
    app.mainloop()                         # ciclo de eventos: espera clics y teclas


if __name__ == "__main__":
    main()
