"""
Pantalla de gestión de categorías.

A la izquierda está la tabla con buscador y a la derecha el formulario.
Al seleccionar una fila, sus datos pasan al formulario para editarlos;
"Nueva" limpia el formulario para dar de alta otra categoría.

La vista solo llama a ``CategoriaController`` y captura sus excepciones.
Las operaciones son consultas cortas, así que se ejecutan en el hilo
principal (a diferencia del login, donde bcrypt tarda a propósito).
"""

from __future__ import annotations

from tkinter import messagebox
from typing import Any, Optional

import customtkinter as ctk

from controllers.categoria_controller import CategoriaController
from controllers.exceptions import ControllerError, ValidationError
from models.categoria import Categoria
from models.usuario import Usuario
from views.components.tabla import Columna, Tabla

ANCHO_FORMULARIO: int = 320
ESPERA_BUSQUEDA_MS: int = 300
COLOR_ERROR: tuple[str, str] = ("#C62828", "#EF5350")
COLOR_EXITO: tuple[str, str] = ("#2E7D32", "#66BB6A")
COLOR_PELIGRO: tuple[str, str] = ("#C62828", "#B71C1C")
COLOR_PELIGRO_HOVER: tuple[str, str] = ("#8E0000", "#7F0000")
COLOR_DESACTIVADO: tuple[str, str] = ("gray70", "gray30")

COLUMNAS: tuple[Columna, ...] = (
    Columna("id", "ID", ancho=45, alineacion="center"),
    Columna("nombre", "Nombre", ancho=140),
    Columna("descripcion", "Descripción", ancho=120, expandir=True),
    Columna("productos", "Productos", ancho=110, alineacion="center"),
)


class CategoriasView(ctk.CTkFrame):
    """
    CRUD de categorías.

    Args:
        master: Contenedor padre.
        usuario: Usuario de la sesión (el controlador verifica sus permisos).
        controlador: Controlador de categorías; se crea uno si no se indica.
    """

    def __init__(
        self,
        master: Any,
        usuario: Usuario,
        controlador: Optional[CategoriaController] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._controlador = controlador or CategoriaController(usuario)
        self._categorias: dict[int, Categoria] = {}
        self._id_edicion: Optional[int] = None
        self._busqueda_pendiente: Optional[str] = None

        self._crear_widgets()
        self._nueva()
        self._cargar_categorias()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Categorías", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        self._crear_panel_lista().grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._crear_panel_formulario().grid(row=0, column=1, rowspan=2, sticky="ns")

    def _crear_panel_lista(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        self.entry_buscar = ctk.CTkEntry(
            panel, placeholder_text="Buscar por nombre o descripción…"
        )
        self.entry_buscar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        # Busca mientras se escribe, pero espera una pausa para no consultar
        # la base de datos en cada tecla.
        self.entry_buscar.bind("<KeyRelease>", self._programar_busqueda)

        self.tabla = Tabla(panel, COLUMNAS, on_seleccion=self._al_seleccionar)
        self.tabla.grid(row=1, column=0, sticky="nsew")

        self.label_total = ctk.CTkLabel(panel, text="", text_color="gray")
        self.label_total.grid(row=2, column=0, sticky="w", pady=(6, 0))
        return panel

    def _crear_panel_formulario(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, width=ANCHO_FORMULARIO, corner_radius=10)
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        ancho = ANCHO_FORMULARIO - 40

        self.label_titulo_form = ctk.CTkLabel(
            panel, text="", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_titulo_form.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 16))

        ctk.CTkLabel(panel, text="Nombre *").grid(row=1, column=0, sticky="w", padx=20)
        self.entry_nombre = ctk.CTkEntry(panel, width=ancho)
        self.entry_nombre.grid(row=2, column=0, sticky="ew", padx=20, pady=(2, 12))
        self.entry_nombre.bind("<Return>", lambda _e: self._guardar())

        ctk.CTkLabel(panel, text="Descripción").grid(row=3, column=0, sticky="w", padx=20)
        self.text_descripcion = ctk.CTkTextbox(panel, width=ancho, height=120, border_width=2)
        self.text_descripcion.grid(row=4, column=0, sticky="ew", padx=20, pady=(2, 12))

        self.label_mensaje = ctk.CTkLabel(
            panel, text="", wraplength=ancho, justify="left", anchor="w"
        )
        self.label_mensaje.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.boton_guardar = ctk.CTkButton(panel, text="Guardar", command=self._guardar)
        self.boton_guardar.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 8))

        ctk.CTkButton(
            panel,
            text="Nueva",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._nueva,
        ).grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 8))

        self.boton_eliminar = ctk.CTkButton(
            panel,
            text="Eliminar",
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_PELIGRO_HOVER,
            command=self._eliminar,
        )
        self.boton_eliminar.grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 20))
        return panel

    # ------------------------------------------------------------------
    # Carga y búsqueda
    # ------------------------------------------------------------------
    def _cargar_categorias(self, seleccionar_id: Optional[int] = None) -> None:
        """Consulta las categorías (con el filtro actual) y llena la tabla."""
        try:
            categorias = self._controlador.listar(self.entry_buscar.get())
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._categorias = {c.id: c for c in categorias if c.id is not None}
        self.tabla.cargar(
            [
                (c.id, (c.id, c.nombre, self._resumir(c.descripcion), c.total_productos or 0))
                for c in categorias
                if c.id is not None
            ]
        )
        total = len(categorias)
        self.label_total.configure(text=f"{total} categoría{'s' if total != 1 else ''}")
        if seleccionar_id is not None:
            self.tabla.seleccionar(seleccionar_id)

    def _programar_busqueda(self, _evento: object) -> None:
        """Reinicia la espera cada vez que se pulsa una tecla en el buscador."""
        if self._busqueda_pendiente is not None:
            self.after_cancel(self._busqueda_pendiente)
        self._busqueda_pendiente = self.after(ESPERA_BUSQUEDA_MS, self._ejecutar_busqueda)

    def _ejecutar_busqueda(self) -> None:
        self._busqueda_pendiente = None
        self._nueva()
        self._cargar_categorias()

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def _al_seleccionar(self, categoria_id: Optional[int]) -> None:
        """Pasa la categoría seleccionada al formulario para editarla."""
        categoria = self._categorias.get(categoria_id) if categoria_id is not None else None
        if categoria is None or categoria.id == self._id_edicion:
            # Nada que hacer si ya está en edición. Esto también evita que el
            # evento <<TreeviewSelect>>, que Tkinter entrega un instante después
            # de seleccionar una fila por código, borre el mensaje de "guardado".
            return
        self._id_edicion = categoria.id
        self._llenar_formulario(categoria.nombre, categoria.descripcion or "")
        self.label_titulo_form.configure(text="Editar categoría")
        self._activar_eliminar(True)
        self._mostrar_mensaje("")

    def _nueva(self) -> None:
        """Deja el formulario vacío, listo para dar de alta una categoría."""
        self._id_edicion = None
        self.tabla.limpiar_seleccion()
        self._llenar_formulario("", "")
        self.label_titulo_form.configure(text="Nueva categoría")
        self._activar_eliminar(False)
        self._mostrar_mensaje("")
        self.entry_nombre.focus_set()

    def _guardar(self) -> None:
        """Crea o actualiza según si hay una categoría en edición."""
        nombre = self.entry_nombre.get()
        # "end-1c" excluye el salto de línea que CTkTextbox agrega al final.
        descripcion = self.text_descripcion.get("1.0", "end-1c")

        try:
            if self._id_edicion is None:
                categoria = self._controlador.crear(nombre, descripcion)
                mensaje = f"Categoría «{categoria.nombre}» creada."
            else:
                categoria = self._controlador.actualizar(self._id_edicion, nombre, descripcion)
                mensaje = "Cambios guardados."
        except ValidationError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            self._enfocar_campo(err.campo)
            return
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._id_edicion = None  # fuerza a recargar el formulario con lo guardado
        self._cargar_categorias(seleccionar_id=categoria.id)
        self._al_seleccionar(categoria.id)
        self._mostrar_mensaje(mensaje, COLOR_EXITO)

    def _eliminar(self) -> None:
        """Pide confirmación y elimina la categoría en edición."""
        categoria = self._categorias.get(self._id_edicion) if self._id_edicion else None
        if categoria is None or categoria.id is None:
            return

        if categoria.total_productos:
            self._mostrar_mensaje(
                f"«{categoria.nombre}» tiene {categoria.total_productos} producto(s). "
                "Muévalos a otra categoría antes de eliminarla.",
                COLOR_ERROR,
            )
            return

        confirmar = messagebox.askyesno(
            "Eliminar categoría",
            f"¿Eliminar la categoría «{categoria.nombre}»?\nEsta acción no se puede deshacer.",
            icon="warning",
            parent=self,
        )
        if not confirmar:
            return

        try:
            self._controlador.eliminar(categoria.id)
        except ControllerError as err:
            # Por ejemplo, si otro usuario le asignó productos mientras tanto.
            self._cargar_categorias(seleccionar_id=categoria.id)
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._nueva()
        self._cargar_categorias()
        self._mostrar_mensaje(f"Categoría «{categoria.nombre}» eliminada.", COLOR_EXITO)

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _llenar_formulario(self, nombre: str, descripcion: str) -> None:
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, nombre)
        self.text_descripcion.delete("1.0", "end")
        self.text_descripcion.insert("1.0", descripcion)

    def _activar_eliminar(self, activo: bool) -> None:
        """Habilita el botón Eliminar; desactivado se muestra en gris, no en rojo."""
        self.boton_eliminar.configure(
            state="normal" if activo else "disabled",
            fg_color=COLOR_PELIGRO if activo else COLOR_DESACTIVADO,
        )

    def _enfocar_campo(self, campo: Optional[str]) -> None:
        if campo == "descripcion":
            self.text_descripcion.focus_set()
        else:
            self.entry_nombre.focus_set()

    def _mostrar_mensaje(
        self, texto: str, color: tuple[str, str] = ("gray10", "gray90")
    ) -> None:
        self.label_mensaje.configure(text=texto, text_color=color)

    @staticmethod
    def _resumir(texto: Optional[str], limite: int = 60) -> str:
        """Acorta textos largos y los deja en una sola línea para la tabla."""
        if not texto:
            return ""
        linea = " ".join(texto.split())
        return linea if len(linea) <= limite else linea[: limite - 1] + "…"
