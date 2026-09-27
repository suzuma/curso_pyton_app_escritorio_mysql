"""
Pantalla de inicio de sesión.

La vista solo se ocupa de la interfaz: leer los campos, mostrar mensajes y
avisar cuando el acceso fue correcto. Toda la validación de credenciales
la hace ``AuthController``. Esta vista no importa nada de MySQL ni de bcrypt.

La verificación se ejecuta en un hilo secundario, porque bcrypt tarda unas
décimas de segundo a propósito y la conexión puede tardar más si el servidor
no responde. Si se hiciera en el hilo principal, la ventana se congelaría.
Tkinter no es seguro para usarse desde varios hilos, así que el hilo
secundario solo deja el resultado en una cola (``queue.Queue``) y el hilo
principal la revisa periódicamente con ``after()``.
"""

from __future__ import annotations

import queue
import threading
from typing import Callable, Union

import customtkinter as ctk

from config.settings import APP_NAME
from controllers.auth_controller import AuthController, AuthError
from models.usuario import Usuario

INTERVALO_REVISION_MS: int = 50
ANCHO_CAMPOS: int = 280
COLOR_ERROR: tuple[str, str] = ("#C62828", "#EF5350")  # (tema claro, tema oscuro)

ResultadoLogin = Union[Usuario, AuthError]


class LoginView(ctk.CTkFrame):
    """
    Formulario de acceso con correo y contraseña.

    Args:
        master: Ventana o contenedor padre.
        auth_controller: Controlador que valida las credenciales.
        on_login_exitoso: Función que se llama con el ``Usuario``
            autenticado cuando el acceso es correcto.
    """

    def __init__(
        self,
        master: ctk.CTk,
        auth_controller: AuthController,
        on_login_exitoso: Callable[[Usuario], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._auth = auth_controller
        self._on_login_exitoso = on_login_exitoso
        self._resultados: queue.Queue[ResultadoLogin] = queue.Queue()

        self._crear_widgets()
        self.entry_email.focus_set()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        """Crea y acomoda los controles del formulario."""
        # Tarjeta centrada: place() con rel=0.5 la mantiene en el centro
        # aunque se cambie el tamaño de la ventana.
        tarjeta = ctk.CTkFrame(self, corner_radius=12)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            tarjeta, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")
        ).pack(padx=40, pady=(32, 4))
        ctk.CTkLabel(
            tarjeta, text="Inicie sesión para continuar", text_color="gray"
        ).pack(padx=40, pady=(0, 24))

        self.entry_email = ctk.CTkEntry(
            tarjeta, width=ANCHO_CAMPOS, placeholder_text="Correo electrónico"
        )
        self.entry_email.pack(padx=40, pady=(0, 12))

        self.entry_password = ctk.CTkEntry(
            tarjeta, width=ANCHO_CAMPOS, placeholder_text="Contraseña", show="•"
        )
        self.entry_password.pack(padx=40, pady=(0, 8))

        self.var_mostrar = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            tarjeta,
            text="Mostrar contraseña",
            variable=self.var_mostrar,
            command=self._alternar_password,
            checkbox_width=18,
            checkbox_height=18,
        ).pack(padx=40, pady=(0, 16), anchor="w")

        self.label_error = ctk.CTkLabel(
            tarjeta,
            text="",
            text_color=COLOR_ERROR,
            wraplength=ANCHO_CAMPOS,
            justify="left",
        )
        self.label_error.pack(padx=40, pady=(0, 8))

        self.boton_ingresar = ctk.CTkButton(
            tarjeta, text="Iniciar sesión", width=ANCHO_CAMPOS, command=self._iniciar_sesion
        )
        self.boton_ingresar.pack(padx=40, pady=(0, 32))

        # Enter en cualquiera de los dos campos equivale a pulsar el botón.
        self.entry_email.bind("<Return>", lambda _evento: self.entry_password.focus_set())
        self.entry_password.bind("<Return>", lambda _evento: self._iniciar_sesion())

    def _alternar_password(self) -> None:
        """Muestra u oculta los caracteres de la contraseña."""
        self.entry_password.configure(show="" if self.var_mostrar.get() else "•")

    # ------------------------------------------------------------------
    # Flujo de inicio de sesión
    # ------------------------------------------------------------------
    def _iniciar_sesion(self) -> None:
        """Lee los campos y lanza la verificación en un hilo secundario."""
        if str(self.boton_ingresar.cget("state")) == "disabled":
            return  # Ya hay una verificación en curso.

        email = self.entry_email.get()
        password = self.entry_password.get()

        self._mostrar_error("")
        self._set_ocupado(True)

        hilo = threading.Thread(
            target=self._verificar_en_segundo_plano, args=(email, password), daemon=True
        )
        hilo.start()
        self.after(INTERVALO_REVISION_MS, self._revisar_resultado)

    def _verificar_en_segundo_plano(self, email: str, password: str) -> None:
        """
        Llama al controlador fuera del hilo de la interfaz.

        No toca ningún widget: solo deja el resultado en la cola.
        """
        try:
            resultado: ResultadoLogin = self._auth.iniciar_sesion(email, password)
        except AuthError as err:
            resultado = err
        except Exception as err:  # noqa: BLE001 - la GUI no debe cerrarse por un error inesperado
            resultado = AuthError(f"Error inesperado: {err}")
        self._resultados.put(resultado)

    def _revisar_resultado(self) -> None:
        """Revisa la cola desde el hilo principal hasta que llegue la respuesta."""
        try:
            resultado = self._resultados.get_nowait()
        except queue.Empty:
            self.after(INTERVALO_REVISION_MS, self._revisar_resultado)
            return

        self._set_ocupado(False)
        if isinstance(resultado, AuthError):
            self._mostrar_error(str(resultado))
            self.entry_password.delete(0, "end")
            self.entry_password.focus_set()
        else:
            self._on_login_exitoso(resultado)

    # ------------------------------------------------------------------
    # Auxiliares de interfaz
    # ------------------------------------------------------------------
    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra (o borra, si ``mensaje`` está vacío) el texto de error."""
        self.label_error.configure(text=mensaje)

    def _set_ocupado(self, ocupado: bool) -> None:
        """Bloquea el formulario mientras se verifica el acceso."""
        estado = "disabled" if ocupado else "normal"
        self.entry_email.configure(state=estado)
        self.entry_password.configure(state=estado)
        self.boton_ingresar.configure(
            state=estado, text="Verificando…" if ocupado else "Iniciar sesión"
        )
