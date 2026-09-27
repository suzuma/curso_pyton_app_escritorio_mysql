"""
Pantalla "Mi cuenta".

Muestra los datos del usuario de la sesión y le permite cambiar su propia
contraseña. Está disponible para todos los roles.
"""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from controllers.auth_controller import AuthController, AuthError

ANCHO_TARJETA: int = 380
COLOR_ERROR: tuple[str, str] = ("#C62828", "#EF5350")
COLOR_EXITO: tuple[str, str] = ("#2E7D32", "#66BB6A")


class MiCuentaView(ctk.CTkFrame):
    """
    Datos de la cuenta y cambio de contraseña.

    Args:
        master: Contenedor padre.
        auth_controller: Controlador de sesión con el usuario actual.
    """

    def __init__(self, master: Any, auth_controller: AuthController) -> None:
        super().__init__(master, fg_color="transparent")
        self._auth = auth_controller
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        usuario = self._auth.usuario_actual
        ctk.CTkLabel(
            self, text="Mi cuenta", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 12))

        datos = ctk.CTkFrame(self, corner_radius=10)
        datos.pack(anchor="w", fill="x", pady=(0, 16))
        for etiqueta, valor in (
            ("Nombre", usuario.nombre if usuario else ""),
            ("Correo", usuario.email if usuario else ""),
            ("Rol", usuario.rol.nombre if usuario and usuario.rol else ""),
        ):
            fila = ctk.CTkFrame(datos, fg_color="transparent")
            fila.pack(fill="x", padx=20, pady=(12 if etiqueta == "Nombre" else 2, 2))
            ctk.CTkLabel(fila, text=f"{etiqueta}:", width=80, anchor="w", text_color="gray").pack(
                side="left"
            )
            ctk.CTkLabel(fila, text=valor, anchor="w").pack(side="left")
        ctk.CTkFrame(datos, height=10, fg_color="transparent").pack()

        tarjeta = ctk.CTkFrame(self, corner_radius=10, width=ANCHO_TARJETA)
        tarjeta.pack(anchor="w")
        ancho = ANCHO_TARJETA - 40

        ctk.CTkLabel(
            tarjeta, text="Cambiar contraseña", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(
            tarjeta,
            text="Mínimo 8 caracteres, con letras y números.",
            text_color="gray",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.entry_actual = self._campo(tarjeta, "Contraseña actual", ancho)
        self.entry_nueva = self._campo(tarjeta, "Contraseña nueva", ancho)
        self.entry_confirmacion = self._campo(tarjeta, "Confirmar contraseña nueva", ancho)
        self.entry_confirmacion.bind("<Return>", lambda _e: self._cambiar_password())

        self.label_mensaje = ctk.CTkLabel(
            tarjeta, text="", wraplength=ancho, justify="left", anchor="w"
        )
        self.label_mensaje.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(
            tarjeta, text="Cambiar contraseña", width=ancho, command=self._cambiar_password
        ).pack(padx=20, pady=(0, 20))

    @staticmethod
    def _campo(padre: ctk.CTkFrame, etiqueta: str, ancho: int) -> ctk.CTkEntry:
        ctk.CTkLabel(padre, text=etiqueta).pack(anchor="w", padx=20)
        entrada = ctk.CTkEntry(padre, width=ancho, show="•")
        entrada.pack(padx=20, pady=(2, 10))
        return entrada

    def _cambiar_password(self) -> None:
        try:
            self._auth.cambiar_password(
                self.entry_actual.get(),
                self.entry_nueva.get(),
                self.entry_confirmacion.get(),
            )
        except AuthError as err:
            self.label_mensaje.configure(text=str(err), text_color=COLOR_ERROR)
            return

        for entrada in (self.entry_actual, self.entry_nueva, self.entry_confirmacion):
            entrada.delete(0, "end")
        self.label_mensaje.configure(
            text="Contraseña actualizada. Úsela en su próximo inicio de sesión.",
            text_color=COLOR_EXITO,
        )
