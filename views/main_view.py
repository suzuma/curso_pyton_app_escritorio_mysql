"""
Ventana principal con menú lateral.

La barra superior muestra el usuario de la sesión. El menú de la izquierda
cambia el contenido del área central y solo incluye los módulos que el rol
del usuario tiene permitidos (ver ``controllers.permisos``).

Para agregar un módulo nuevo basta con añadir una entrada a
``_registrar_modulos`` indicando, si hace falta, el permiso que exige.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import customtkinter as ctk

from controllers.auth_controller import AuthController
from controllers.permisos import Permiso, tiene_permiso
from models.usuario import Usuario
from views.categorias_view import CategoriasView
from views.mi_cuenta_view import MiCuentaView
from views.productos_view import ProductosView
from views.usuarios_view import UsuariosView

ANCHO_MENU: int = 200
COLOR_BOTON_ACTIVO: tuple[str, str] = ("gray75", "gray25")

FabricaPantalla = Callable[[ctk.CTkFrame], ctk.CTkFrame]


@dataclass(frozen=True)
class Modulo:
    """
    Opción del menú lateral.

    Attributes:
        fabrica: Función que crea la pantalla dentro del contenedor dado.
        permiso: Permiso requerido para verla; ``None`` si es para todos.
    """

    fabrica: FabricaPantalla
    permiso: Optional[Permiso] = None


class MainView(ctk.CTkFrame):
    """
    Pantalla que se muestra después de un inicio de sesión correcto.

    Args:
        master: Ventana o contenedor padre.
        auth_controller: Controlador de sesión; contiene al usuario actual
            y se usa en "Mi cuenta" para cambiar la contraseña.
        on_cerrar_sesion: Función que se llama al pulsar "Cerrar sesión".
    """

    def __init__(
        self,
        master: ctk.CTk,
        auth_controller: AuthController,
        on_cerrar_sesion: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        if auth_controller.usuario_actual is None:
            raise ValueError("MainView requiere un usuario autenticado.")
        self._auth = auth_controller
        self._usuario: Usuario = auth_controller.usuario_actual
        self._on_cerrar_sesion = on_cerrar_sesion
        self._modulos: dict[str, Modulo] = {}
        self._botones_menu: dict[str, ctk.CTkButton] = {}
        self._pantalla_actual: Optional[ctk.CTkFrame] = None

        self._registrar_modulos()
        self._crear_widgets()
        self.mostrar_modulo("Inicio")

    def _registrar_modulos(self) -> None:
        """Define las opciones del menú, la pantalla y el permiso de cada una."""
        todos = {
            "Inicio": Modulo(self._crear_inicio),
            "Categorías": Modulo(
                lambda c: CategoriasView(c, self._usuario), Permiso.GESTIONAR_CATEGORIAS
            ),
            "Productos": Modulo(
                lambda c: ProductosView(c, self._usuario), Permiso.GESTIONAR_PRODUCTOS
            ),
            "Usuarios": Modulo(
                lambda c: UsuariosView(c, self._usuario), Permiso.GESTIONAR_USUARIOS
            ),
            "Mi cuenta": Modulo(lambda c: MiCuentaView(c, self._auth)),
        }
        self._modulos = {
            nombre: modulo
            for nombre, modulo in todos.items()
            if modulo.permiso is None or tiene_permiso(self._usuario, modulo.permiso)
        }

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        self._crear_barra_superior()

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True)

        menu = ctk.CTkFrame(cuerpo, width=ANCHO_MENU, corner_radius=0)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        for nombre in self._modulos:
            boton = ctk.CTkButton(
                menu,
                text=nombre,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=COLOR_BOTON_ACTIVO,
                corner_radius=6,
                command=lambda n=nombre: self.mostrar_modulo(n),
            )
            boton.pack(fill="x", padx=10, pady=(10 if not self._botones_menu else 2, 0))
            self._botones_menu[nombre] = boton

        self._contenido = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self._contenido.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    def _crear_barra_superior(self) -> None:
        barra = ctk.CTkFrame(self, corner_radius=0, height=56)
        barra.pack(fill="x")
        barra.pack_propagate(False)  # respeta la altura fija de la barra

        self.label_usuario = ctk.CTkLabel(
            barra, text="", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_usuario.pack(side="left", padx=20)
        self.actualizar_encabezado()

        ctk.CTkButton(
            barra,
            text="Cerrar sesión",
            width=120,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._on_cerrar_sesion,
        ).pack(side="right", padx=20)

    def actualizar_encabezado(self) -> None:
        """Refresca nombre y rol en la barra (p. ej., si el usuario editó su nombre)."""
        nombre_rol = self._usuario.rol.nombre if self._usuario.rol else "Sin rol"
        self.label_usuario.configure(text=f"{self._usuario.nombre}  ·  {nombre_rol}")

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def mostrar_modulo(self, nombre: str) -> None:
        """
        Reemplaza el contenido central por la pantalla del módulo indicado.

        Args:
            nombre: Clave del módulo en ``_modulos``.
        """
        if nombre not in self._modulos:
            return  # módulo inexistente o sin permiso
        if self._pantalla_actual is not None:
            self._pantalla_actual.destroy()
        self.actualizar_encabezado()
        self._pantalla_actual = self._modulos[nombre].fabrica(self._contenido)
        self._pantalla_actual.pack(fill="both", expand=True)

        for clave, boton in self._botones_menu.items():
            boton.configure(fg_color=COLOR_BOTON_ACTIVO if clave == nombre else "transparent")

    def _crear_inicio(self, contenedor: ctk.CTkFrame) -> ctk.CTkFrame:
        """Pantalla de bienvenida."""
        marco = ctk.CTkFrame(contenedor, fg_color="transparent")
        ctk.CTkLabel(
            marco,
            text=f"Bienvenido, {self._usuario.nombre}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            marco,
            text="Seleccione un módulo en el menú de la izquierda.",
            text_color="gray",
        ).pack()
        return marco
