"""
Pantalla de administración de usuarios (solo administradores).

A la izquierda está la tabla con buscador; a la derecha, un formulario
organizado en pestañas con ``CTkTabview``:

* **Datos**: nombre, correo y rol.
* **Contraseña**: al crear un usuario, su contraseña inicial; al editarlo,
  permite restablecerla (por ejemplo, si la olvidó).

Las reglas (no desactivarse a sí mismo, conservar al menos un
administrador, política de contraseñas) viven en ``UsuarioController``;
la vista solo muestra los mensajes y lleva el foco al campo con el error.
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk

from controllers.exceptions import ControllerError, ValidationError
from controllers.usuario_controller import UsuarioController
from models.usuario import Usuario
from views.components.tabla import Columna, Tabla

ANCHO_FORMULARIO: int = 320
ESPERA_BUSQUEDA_MS: int = 300
SIN_SELECCION: str = "Seleccione…"
PESTANA_DATOS: str = "Datos"
PESTANA_PASSWORD: str = "Contraseña"

COLOR_ERROR: tuple[str, str] = ("#C62828", "#EF5350")
COLOR_EXITO: tuple[str, str] = ("#2E7D32", "#66BB6A")
COLOR_INACTIVO: tuple[str, str] = ("gray55", "gray50")
COLOR_TEXTO: tuple[str, str] = ("gray10", "gray90")
ETIQUETA_INACTIVO: str = "inactivo"

COLUMNAS: tuple[Columna, ...] = (
    Columna("nombre", "Nombre", ancho=165, expandir=True),
    Columna("email", "Correo", ancho=145),
    Columna("rol", "Rol", ancho=115),
    Columna("estado", "Estado", ancho=80, alineacion="center"),
)


class UsuariosView(ctk.CTkFrame):
    """
    CRUD de usuarios.

    Args:
        master: Contenedor padre.
        usuario: Administrador que tiene la sesión abierta.
        controlador: Controlador de usuarios; se crea uno si no se indica.
    """

    def __init__(
        self,
        master: Any,
        usuario: Usuario,
        controlador: Optional[UsuarioController] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._controlador = controlador or UsuarioController(usuario)
        self._usuarios: dict[int, Usuario] = {}
        self._roles_por_nombre: dict[str, int] = {}
        self._id_edicion: Optional[int] = None
        self._busqueda_pendiente: Optional[str] = None

        self._crear_widgets()
        self._cargar_roles()
        self._nuevo()
        self._cargar_usuarios()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Usuarios", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        self._crear_panel_lista().grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._crear_panel_formulario().grid(row=0, column=1, rowspan=2, sticky="ns")

    def _crear_panel_lista(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        self.entry_buscar = ctk.CTkEntry(panel, placeholder_text="Buscar por nombre o correo…")
        self.entry_buscar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.entry_buscar.bind("<KeyRelease>", self._programar_busqueda)

        self.var_inactivos = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            panel,
            text="Mostrar inactivos",
            variable=self.var_inactivos,
            command=self._aplicar_filtros,
            checkbox_width=18,
            checkbox_height=18,
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.tabla = Tabla(panel, COLUMNAS, on_seleccion=self._al_seleccionar)
        self.tabla.configurar_etiqueta(ETIQUETA_INACTIVO, COLOR_INACTIVO)
        self.tabla.grid(row=2, column=0, sticky="nsew")

        self.label_total = ctk.CTkLabel(panel, text="", text_color="gray", anchor="w")
        self.label_total.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        return panel

    def _crear_panel_formulario(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, width=ANCHO_FORMULARIO, corner_radius=10)
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        ancho = ANCHO_FORMULARIO - 40

        self.label_titulo_form = ctk.CTkLabel(
            panel, text="", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_titulo_form.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 0))
        self.label_estado = ctk.CTkLabel(panel, text="", text_color="gray", height=18)
        self.label_estado.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 4))

        self.tabs = ctk.CTkTabview(panel, width=ancho, height=250)
        self.tabs.grid(row=2, column=0, sticky="ew", padx=14)
        self._crear_pestana_datos(self.tabs.add(PESTANA_DATOS))
        self._crear_pestana_password(self.tabs.add(PESTANA_PASSWORD))

        self.label_mensaje = ctk.CTkLabel(
            panel, text="", wraplength=ancho, justify="left", anchor="w"
        )
        self.label_mensaje.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 8))

        ctk.CTkButton(panel, text="Guardar", command=self._guardar).grid(
            row=4, column=0, sticky="ew", padx=20, pady=(0, 8)
        )
        ctk.CTkButton(
            panel,
            text="Nuevo",
            fg_color="transparent",
            border_width=1,
            text_color=COLOR_TEXTO,
            command=self._nuevo,
        ).grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.boton_estado = ctk.CTkButton(
            panel,
            text="Desactivar",
            fg_color="transparent",
            border_width=1,
            text_color=COLOR_TEXTO,
            command=self._cambiar_estado,
        )
        self.boton_estado.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 20))
        return panel

    def _crear_pestana_datos(self, pestana: ctk.CTkFrame) -> None:
        ctk.CTkLabel(pestana, text="Nombre *").pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(pestana)
        self.entry_nombre.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(pestana, text="Correo *").pack(anchor="w")
        self.entry_email = ctk.CTkEntry(pestana, placeholder_text="nombre@escuela.edu")
        self.entry_email.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(pestana, text="Rol *").pack(anchor="w")
        self.menu_rol = ctk.CTkOptionMenu(pestana, values=[SIN_SELECCION])
        self.menu_rol.pack(fill="x", pady=(2, 0))

        for entrada in (self.entry_nombre, self.entry_email):
            entrada.bind("<Return>", lambda _e: self._guardar())

    def _crear_pestana_password(self, pestana: ctk.CTkFrame) -> None:
        self.label_ayuda_password = ctk.CTkLabel(
            pestana, text="", text_color="gray", wraplength=ANCHO_FORMULARIO - 70, justify="left"
        )
        self.label_ayuda_password.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(pestana, text="Contraseña").pack(anchor="w")
        self.entry_password = ctk.CTkEntry(pestana, show="•")
        self.entry_password.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(pestana, text="Confirmar contraseña").pack(anchor="w")
        self.entry_confirmacion = ctk.CTkEntry(pestana, show="•")
        self.entry_confirmacion.pack(fill="x", pady=(2, 8))

        # Solo visible al editar: al crear, la contraseña se guarda con "Guardar".
        self.boton_restablecer = ctk.CTkButton(
            pestana, text="Restablecer contraseña", command=self._restablecer_password
        )

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def _cargar_roles(self) -> None:
        try:
            roles = self._controlador.listar_roles()
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return
        self._roles_por_nombre = {r.nombre: r.id for r in roles if r.id is not None}
        self.menu_rol.configure(values=list(self._roles_por_nombre) or [SIN_SELECCION])

    def _cargar_usuarios(self, seleccionar_id: Optional[int] = None) -> None:
        try:
            usuarios = self._controlador.listar(
                texto=self.entry_buscar.get(), incluir_inactivos=self.var_inactivos.get()
            )
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._usuarios = {u.id: u for u in usuarios if u.id is not None}
        filas = []
        etiquetas: dict[int, str] = {}
        for u in self._usuarios.values():
            es_yo = self._controlador.es_usuario_actual(u.id)
            nombre = f"{u.nombre} (usted)" if es_yo else u.nombre
            rol = u.rol.nombre if u.rol else ""
            filas.append((u.id, (nombre, u.email, rol, "Activo" if u.activo else "Inactivo")))
            if not u.activo:
                etiquetas[u.id] = ETIQUETA_INACTIVO
        self.tabla.cargar(filas, etiquetas)

        activos = sum(1 for u in usuarios if u.activo)
        self.label_total.configure(text=f"{len(usuarios)} usuarios  ·  {activos} activos")
        if seleccionar_id is not None:
            self.tabla.seleccionar(seleccionar_id)

    def _programar_busqueda(self, _evento: object) -> None:
        if self._busqueda_pendiente is not None:
            self.after_cancel(self._busqueda_pendiente)
        self._busqueda_pendiente = self.after(ESPERA_BUSQUEDA_MS, self._aplicar_filtros)

    def _aplicar_filtros(self) -> None:
        self._busqueda_pendiente = None
        self._nuevo()
        self._cargar_usuarios()

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def _al_seleccionar(self, usuario_id: Optional[int]) -> None:
        usuario = self._usuarios.get(usuario_id) if usuario_id is not None else None
        if usuario is None or usuario.id == self._id_edicion:
            return  # ya está en edición (evita que el evento tardío borre mensajes)
        self._id_edicion = usuario.id
        self._llenar_formulario(
            usuario.nombre, usuario.email, usuario.rol.nombre if usuario.rol else SIN_SELECCION
        )
        es_yo = self._controlador.es_usuario_actual(usuario.id)
        self.label_titulo_form.configure(text="Editar usuario")
        self.label_estado.configure(
            text=("Estado: activo" if usuario.activo else "Estado: inactivo")
            + ("  ·  su cuenta" if es_yo else ""),
            text_color="gray" if usuario.activo else COLOR_ERROR,
        )
        # Sobre su propia cuenta no puede cambiar el rol ni el estado.
        self.menu_rol.configure(state="disabled" if es_yo else "normal")
        self.boton_estado.configure(
            state="disabled" if es_yo else "normal",
            text="Desactivar" if usuario.activo else "Activar",
        )
        self.label_ayuda_password.configure(
            text="Escriba una contraseña nueva para este usuario y pulse «Restablecer»."
            if not es_yo
            else "Para cambiar su propia contraseña use «Mi cuenta»."
        )
        if es_yo:
            self.boton_restablecer.pack_forget()
        else:
            self.boton_restablecer.pack(fill="x", pady=(4, 0))
        self.tabs.set(PESTANA_DATOS)
        self._mostrar_mensaje("")

    def _nuevo(self) -> None:
        self._id_edicion = None
        self.tabla.limpiar_seleccion()
        self._llenar_formulario("", "", SIN_SELECCION)
        self.label_titulo_form.configure(text="Nuevo usuario")
        self.label_estado.configure(text="")
        self.menu_rol.configure(state="normal")
        self.boton_estado.configure(state="disabled", text="Desactivar")
        self.label_ayuda_password.configure(
            text="Contraseña inicial: mínimo 8 caracteres, con letras y números."
        )
        self.boton_restablecer.pack_forget()
        self.tabs.set(PESTANA_DATOS)
        self._mostrar_mensaje("")
        self.entry_nombre.focus_set()

    def _guardar(self) -> None:
        nombre = self.entry_nombre.get()
        email = self.entry_email.get()
        rol_id = self._roles_por_nombre.get(self.menu_rol.get())
        try:
            if self._id_edicion is None:
                usuario = self._controlador.crear(
                    nombre,
                    email,
                    rol_id,
                    self.entry_password.get(),
                    self.entry_confirmacion.get(),
                )
                mensaje = f"Usuario {usuario.email} creado."
            else:
                usuario = self._controlador.actualizar(self._id_edicion, nombre, email, rol_id)
                mensaje = "Cambios guardados."
        except ValidationError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            self._enfocar_campo(err.campo)
            return
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return
        self._recargar_y_mostrar(usuario.id, mensaje)

    def _cambiar_estado(self) -> None:
        usuario = self._usuarios.get(self._id_edicion) if self._id_edicion else None
        if usuario is None or usuario.id is None:
            return
        try:
            self._controlador.cambiar_estado(usuario.id, not usuario.activo)
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return
        accion = "activado" if not usuario.activo else "desactivado"
        self._recargar_y_mostrar(usuario.id, f"Usuario {usuario.email} {accion}.")

    def _restablecer_password(self) -> None:
        if self._id_edicion is None:
            return
        try:
            self._controlador.restablecer_password(
                self._id_edicion, self.entry_password.get(), self.entry_confirmacion.get()
            )
        except ValidationError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            self._enfocar_campo(err.campo)
            return
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return
        self.entry_password.delete(0, "end")
        self.entry_confirmacion.delete(0, "end")
        self._mostrar_mensaje("Contraseña restablecida.", COLOR_EXITO)

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _recargar_y_mostrar(self, usuario_id: Optional[int], mensaje: str) -> None:
        """Recarga la tabla, deja seleccionado el usuario y muestra el mensaje."""
        self._id_edicion = None
        self._cargar_usuarios(seleccionar_id=usuario_id)
        if usuario_id in self._usuarios:
            self._al_seleccionar(usuario_id)
        else:
            self._nuevo()
        self._mostrar_mensaje(mensaje, COLOR_EXITO)

    def _llenar_formulario(self, nombre: str, email: str, rol: str) -> None:
        for entrada, valor in (
            (self.entry_nombre, nombre),
            (self.entry_email, email),
            (self.entry_password, ""),
            (self.entry_confirmacion, ""),
        ):
            entrada.delete(0, "end")
            if valor:
                entrada.insert(0, valor)
        self.menu_rol.set(rol)

    def _enfocar_campo(self, campo: Optional[str]) -> None:
        """Cambia a la pestaña que contiene el campo con error y lo enfoca."""
        if campo in ("password", "confirmacion"):
            self.tabs.set(PESTANA_PASSWORD)
            destino = self.entry_password if campo == "password" else self.entry_confirmacion
        else:
            self.tabs.set(PESTANA_DATOS)
            destino = {"email": self.entry_email, "rol": self.menu_rol}.get(
                campo or "", self.entry_nombre
            )
        destino.focus_set()

    def _mostrar_mensaje(self, texto: str, color: tuple[str, str] = COLOR_TEXTO) -> None:
        self.label_mensaje.configure(text=texto, text_color=color)
