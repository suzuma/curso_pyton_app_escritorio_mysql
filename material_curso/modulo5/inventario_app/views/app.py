"""
Ventana raíz de la aplicación.

Tkinter admite una sola ventana raíz (``CTk``) por programa. En lugar de
abrir y cerrar ventanas, ``App`` intercambia pantallas (``CTkFrame``) dentro
de la misma ventana: primero el login y, tras autenticarse, la principal.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from config.settings import APP_NAME
from controllers.auth_controller import AuthController
from models.usuario import Usuario
from views.login_view import LoginView
from views.main_view import MainView

TAMANO_LOGIN: str = "480x520"
TAMANO_PRINCIPAL: str = "1100x680"
TAMANO_MINIMO: tuple[int, int] = (420, 480)


class App(ctk.CTk):
    """
    Ventana principal que administra qué pantalla está visible.

    Attributes:
        auth_controller: Controlador de sesión compartido por las pantallas.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.minsize(*TAMANO_MINIMO)
        self.auth_controller = AuthController()
        self._pantalla_actual: Optional[ctk.CTkFrame] = None
        self.mostrar_login()

    def _cambiar_pantalla(self, pantalla: ctk.CTkFrame, tamano: str) -> None:
        """Destruye la pantalla visible y muestra la nueva."""
        if self._pantalla_actual is not None:
            self._pantalla_actual.destroy()
        self._pantalla_actual = pantalla
        self.geometry(tamano)
        pantalla.pack(fill="both", expand=True)

    def mostrar_login(self) -> None:
        """Muestra el formulario de inicio de sesión."""
        self._cambiar_pantalla(
            LoginView(self, self.auth_controller, on_login_exitoso=self._al_iniciar_sesion),
            TAMANO_LOGIN,
        )

    def _al_iniciar_sesion(self, usuario: Usuario) -> None:
        """Se ejecuta cuando el login es correcto."""
        self._cambiar_pantalla(
            MainView(self, self.auth_controller, on_cerrar_sesion=self._al_cerrar_sesion),
            TAMANO_PRINCIPAL,
        )

    def _al_cerrar_sesion(self) -> None:
        """Cierra la sesión y regresa al login."""
        self.auth_controller.cerrar_sesion()
        self.mostrar_login()
