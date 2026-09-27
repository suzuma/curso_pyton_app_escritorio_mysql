"""
Pantalla de gestión de productos.

Sigue el mismo esquema que la de categorías: tabla con filtros a la
izquierda y formulario a la derecha. Además:

* una lista desplegable para elegir la categoría del producto;
* filtros por texto, por categoría y para mostrar los productos inactivos;
* resaltado de los productos con stock bajo;
* baja lógica (activar/desactivar) en lugar de eliminar.

La vista solo llama a ``ProductoController``; no importa nada de MySQL.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

import customtkinter as ctk

from controllers.exceptions import ControllerError, ValidationError
from controllers.producto_controller import STOCK_MINIMO, ProductoController
from models.producto import Producto
from models.usuario import Usuario
from views.components.tabla import Columna, Tabla

ANCHO_FORMULARIO: int = 320
ESPERA_BUSQUEDA_MS: int = 300
TODAS_LAS_CATEGORIAS: str = "Todas las categorías"
SIN_SELECCION: str = "Seleccione…"

COLOR_ERROR: tuple[str, str] = ("#C62828", "#EF5350")
COLOR_EXITO: tuple[str, str] = ("#2E7D32", "#66BB6A")
COLOR_STOCK_BAJO: tuple[str, str] = ("#E65100", "#FFB74D")
COLOR_INACTIVO: tuple[str, str] = ("gray55", "gray50")
COLOR_TEXTO: tuple[str, str] = ("gray10", "gray90")

ETIQUETA_STOCK_BAJO: str = "stock_bajo"
ETIQUETA_INACTIVO: str = "inactivo"

COLUMNAS: tuple[Columna, ...] = (
    Columna("sku", "SKU", ancho=85),
    Columna("nombre", "Nombre", ancho=150, expandir=True),
    Columna("categoria", "Categoría", ancho=100),
    Columna("precio", "Precio", ancho=90, alineacion="e"),
    Columna("stock", "Stock", ancho=80, alineacion="center"),
)


def formatear_moneda(valor: Decimal) -> str:
    """Da formato de moneda: ``Decimal('1250.5')`` → ``'$1,250.50'``."""
    return f"${valor:,.2f}"


class ProductosView(ctk.CTkFrame):
    """
    CRUD de productos.

    Args:
        master: Contenedor padre.
        usuario: Usuario de la sesión (el controlador verifica sus permisos).
        controlador: Controlador de productos; se crea uno si no se indica.
    """

    def __init__(
        self,
        master: Any,
        usuario: Usuario,
        controlador: Optional[ProductoController] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._controlador = controlador or ProductoController(usuario)
        self._productos: dict[int, Producto] = {}
        self._categorias_por_nombre: dict[str, int] = {}
        self._id_edicion: Optional[int] = None
        self._busqueda_pendiente: Optional[str] = None

        self._crear_widgets()
        self._cargar_categorias()
        self._nuevo()
        self._cargar_productos()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Productos", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        self._crear_panel_lista().grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        self._crear_panel_formulario().grid(row=0, column=1, rowspan=2, sticky="ns")

    def _crear_panel_lista(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        self.entry_buscar = ctk.CTkEntry(panel, placeholder_text="Buscar por SKU o nombre…")
        self.entry_buscar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.entry_buscar.bind("<KeyRelease>", self._programar_busqueda)

        filtros = ctk.CTkFrame(panel, fg_color="transparent")
        filtros.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.menu_filtro_categoria = ctk.CTkOptionMenu(
            filtros,
            values=[TODAS_LAS_CATEGORIAS],
            width=200,
            command=lambda _valor: self._aplicar_filtros(),
        )
        self.menu_filtro_categoria.pack(side="left")

        self.var_inactivos = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filtros,
            text="Mostrar inactivos",
            variable=self.var_inactivos,
            command=self._aplicar_filtros,
            checkbox_width=18,
            checkbox_height=18,
        ).pack(side="left", padx=(16, 0))

        self.tabla = Tabla(panel, COLUMNAS, on_seleccion=self._al_seleccionar)
        self.tabla.configurar_etiqueta(ETIQUETA_STOCK_BAJO, COLOR_STOCK_BAJO)
        self.tabla.configurar_etiqueta(ETIQUETA_INACTIVO, COLOR_INACTIVO)
        self.tabla.grid(row=2, column=0, sticky="nsew")

        self.label_resumen = ctk.CTkLabel(panel, text="", text_color="gray", anchor="w")
        self.label_resumen.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        return panel

    def _crear_panel_formulario(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, width=ANCHO_FORMULARIO, corner_radius=10)
        panel.grid_propagate(False)
        panel.grid_columnconfigure((0, 1), weight=1, uniform="mitad")
        ancho = ANCHO_FORMULARIO - 40
        fila = 0

        self.label_titulo_form = ctk.CTkLabel(
            panel, text="", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_titulo_form.grid(
            row=fila, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 0)
        )
        fila += 1
        self.label_estado = ctk.CTkLabel(panel, text="", text_color="gray", height=18)
        self.label_estado.grid(row=fila, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 10))
        fila += 1

        self.entry_sku = self._campo(panel, "SKU *", fila, placeholder="PROD-004")
        fila += 2
        self.entry_nombre = self._campo(panel, "Nombre *", fila)
        fila += 2

        ctk.CTkLabel(panel, text="Categoría *").grid(
            row=fila, column=0, columnspan=2, sticky="w", padx=20
        )
        self.menu_categoria = ctk.CTkOptionMenu(panel, values=[SIN_SELECCION], width=ancho)
        self.menu_categoria.grid(
            row=fila + 1, column=0, columnspan=2, sticky="ew", padx=20, pady=(2, 10)
        )
        fila += 2

        # Precio y stock en la misma fila para ahorrar espacio vertical.
        ctk.CTkLabel(panel, text="Precio *").grid(row=fila, column=0, sticky="w", padx=(20, 6))
        ctk.CTkLabel(panel, text="Stock *").grid(row=fila, column=1, sticky="w", padx=(6, 20))
        self.entry_precio = ctk.CTkEntry(panel, placeholder_text="0.00")
        self.entry_precio.grid(row=fila + 1, column=0, sticky="ew", padx=(20, 6), pady=(2, 10))
        self.entry_stock = ctk.CTkEntry(panel, placeholder_text="0")
        self.entry_stock.grid(row=fila + 1, column=1, sticky="ew", padx=(6, 20), pady=(2, 10))
        fila += 2

        for entrada in (self.entry_sku, self.entry_nombre, self.entry_precio, self.entry_stock):
            entrada.bind("<Return>", lambda _e: self._guardar())

        self.label_mensaje = ctk.CTkLabel(
            panel, text="", wraplength=ancho, justify="left", anchor="w"
        )
        self.label_mensaje.grid(
            row=fila, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10)
        )
        fila += 1

        ctk.CTkButton(panel, text="Guardar", command=self._guardar).grid(
            row=fila, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8)
        )
        fila += 1
        ctk.CTkButton(
            panel,
            text="Nuevo",
            fg_color="transparent",
            border_width=1,
            text_color=COLOR_TEXTO,
            command=self._nuevo,
        ).grid(row=fila, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        fila += 1

        self.boton_estado = ctk.CTkButton(
            panel,
            text="Desactivar",
            fg_color="transparent",
            border_width=1,
            text_color=COLOR_TEXTO,
            command=self._cambiar_estado,
        )
        # Solo se muestra a quien tiene permiso (el controlador también lo verifica).
        if self._controlador.puede_cambiar_estado:
            self.boton_estado.grid(
                row=fila, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20)
            )
        return panel

    @staticmethod
    def _campo(
        panel: ctk.CTkFrame, etiqueta: str, fila: int, placeholder: str = ""
    ) -> ctk.CTkEntry:
        """Crea una etiqueta y, debajo, un campo de texto de ancho completo."""
        ctk.CTkLabel(panel, text=etiqueta).grid(
            row=fila, column=0, columnspan=2, sticky="w", padx=20
        )
        entrada = ctk.CTkEntry(panel, placeholder_text=placeholder)
        entrada.grid(row=fila + 1, column=0, columnspan=2, sticky="ew", padx=20, pady=(2, 10))
        return entrada

    # ------------------------------------------------------------------
    # Carga de datos y filtros
    # ------------------------------------------------------------------
    def _cargar_categorias(self) -> None:
        """Llena las dos listas desplegables con las categorías actuales."""
        try:
            categorias = self._controlador.listar_categorias()
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return
        self._categorias_por_nombre = {c.nombre: c.id for c in categorias if c.id is not None}
        nombres = list(self._categorias_por_nombre)
        self.menu_filtro_categoria.configure(values=[TODAS_LAS_CATEGORIAS, *nombres])
        self.menu_categoria.configure(values=nombres or [SIN_SELECCION])

    def _cargar_productos(self, seleccionar_id: Optional[int] = None) -> None:
        """Consulta los productos con los filtros actuales y llena la tabla."""
        filtro = self.menu_filtro_categoria.get()
        try:
            productos = self._controlador.listar(
                texto=self.entry_buscar.get(),
                categoria_id=self._categorias_por_nombre.get(filtro),
                incluir_inactivos=self.var_inactivos.get(),
            )
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._productos = {p.id: p for p in productos if p.id is not None}
        filas: list[tuple[int, tuple[Any, ...]]] = []
        etiquetas: dict[int, str] = {}
        for p in self._productos.values():
            bajo = self._controlador.es_stock_bajo(p)
            nombre = p.nombre if p.activo else f"{p.nombre} (inactivo)"
            stock = f"{p.stock} (bajo)" if bajo and p.activo else str(p.stock)
            filas.append(
                (p.id, (p.sku, nombre, p.categoria_nombre or "", formatear_moneda(p.precio), stock))
            )
            if not p.activo:
                etiquetas[p.id] = ETIQUETA_INACTIVO
            elif bajo:
                etiquetas[p.id] = ETIQUETA_STOCK_BAJO
        self.tabla.cargar(filas, etiquetas)
        self._actualizar_resumen(list(self._productos.values()))

        if seleccionar_id is not None:
            self.tabla.seleccionar(seleccionar_id)

    def _actualizar_resumen(self, productos: list[Producto]) -> None:
        """Muestra total de productos, cuántos tienen stock bajo y el valor del inventario."""
        activos = [p for p in productos if p.activo]
        bajos = sum(1 for p in activos if self._controlador.es_stock_bajo(p))
        valor = sum((p.valor_inventario for p in activos), Decimal("0"))
        partes = [f"{len(productos)} producto{'s' if len(productos) != 1 else ''}"]
        if bajos:
            partes.append(f"{bajos} con stock bajo (≤ {STOCK_MINIMO})")
        partes.append(f"valor en inventario: {formatear_moneda(valor)}")
        self.label_resumen.configure(text="  ·  ".join(partes))

    def _programar_busqueda(self, _evento: object) -> None:
        """Espera una pausa al escribir antes de consultar la base de datos."""
        if self._busqueda_pendiente is not None:
            self.after_cancel(self._busqueda_pendiente)
        self._busqueda_pendiente = self.after(ESPERA_BUSQUEDA_MS, self._aplicar_filtros)

    def _aplicar_filtros(self) -> None:
        self._busqueda_pendiente = None
        self._nuevo()
        self._cargar_productos()

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def _al_seleccionar(self, producto_id: Optional[int]) -> None:
        """Pasa el producto seleccionado al formulario."""
        producto = self._productos.get(producto_id) if producto_id is not None else None
        if producto is None or producto.id == self._id_edicion:
            # Ya está en edición; también evita que el evento tardío
            # <<TreeviewSelect>> borre el mensaje de "guardado".
            return
        self._id_edicion = producto.id
        self._llenar_formulario(
            sku=producto.sku,
            nombre=producto.nombre,
            categoria=producto.categoria_nombre or SIN_SELECCION,
            precio=f"{producto.precio:.2f}",
            stock=str(producto.stock),
        )
        self.label_titulo_form.configure(text="Editar producto")
        self._mostrar_estado(producto.activo)
        self._mostrar_mensaje("")

    def _nuevo(self) -> None:
        """Deja el formulario vacío para registrar un producto."""
        self._id_edicion = None
        self.tabla.limpiar_seleccion()
        self._llenar_formulario("", "", SIN_SELECCION, "", "")
        self.label_titulo_form.configure(text="Nuevo producto")
        self.label_estado.configure(text="")
        self.boton_estado.configure(state="disabled", text="Desactivar")
        self._mostrar_mensaje("")
        self.entry_sku.focus_set()

    def _guardar(self) -> None:
        """Crea o actualiza según si hay un producto en edición."""
        datos = {
            "sku": self.entry_sku.get(),
            "nombre": self.entry_nombre.get(),
            "precio": self.entry_precio.get(),
            "stock": self.entry_stock.get(),
            "categoria_id": self._categorias_por_nombre.get(self.menu_categoria.get()),
        }
        try:
            if self._id_edicion is None:
                producto = self._controlador.crear(**datos)
                mensaje = f"Producto {producto.sku} registrado."
            else:
                producto = self._controlador.actualizar(self._id_edicion, **datos)
                mensaje = "Cambios guardados."
        except ValidationError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            self._enfocar_campo(err.campo)
            return
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        self._id_edicion = None  # fuerza a recargar el formulario con lo guardado
        self._cargar_productos(seleccionar_id=producto.id)
        if producto.id in self._productos:
            self._al_seleccionar(producto.id)
        else:
            # Quedó fuera de los filtros actuales (p. ej., otra categoría).
            self._nuevo()
            mensaje += " No aparece en la lista por los filtros aplicados."
        self._mostrar_mensaje(mensaje, COLOR_EXITO)

    def _cambiar_estado(self) -> None:
        """Activa o desactiva el producto en edición."""
        producto = self._productos.get(self._id_edicion) if self._id_edicion else None
        if producto is None or producto.id is None:
            return
        nuevo_estado = not producto.activo
        try:
            self._controlador.cambiar_estado(producto.id, nuevo_estado)
        except ControllerError as err:
            self._mostrar_mensaje(str(err), COLOR_ERROR)
            return

        accion = "activado" if nuevo_estado else "desactivado"
        self._id_edicion = None
        self._cargar_productos(seleccionar_id=producto.id)
        if producto.id in self._productos:
            self._al_seleccionar(producto.id)
        else:
            self._nuevo()  # los inactivos están ocultos
        self._mostrar_mensaje(f"Producto {producto.sku} {accion}.", COLOR_EXITO)

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _llenar_formulario(
        self, sku: str, nombre: str, categoria: str, precio: str, stock: str
    ) -> None:
        for entrada, valor in (
            (self.entry_sku, sku),
            (self.entry_nombre, nombre),
            (self.entry_precio, precio),
            (self.entry_stock, stock),
        ):
            entrada.delete(0, "end")
            if valor:
                entrada.insert(0, valor)
        self.menu_categoria.set(categoria)

    def _mostrar_estado(self, activo: bool) -> None:
        self.label_estado.configure(
            text="Estado: activo" if activo else "Estado: inactivo",
            text_color="gray" if activo else COLOR_ERROR,
        )
        self.boton_estado.configure(state="normal", text="Desactivar" if activo else "Activar")

    def _enfocar_campo(self, campo: Optional[str]) -> None:
        campos = {
            "sku": self.entry_sku,
            "nombre": self.entry_nombre,
            "precio": self.entry_precio,
            "stock": self.entry_stock,
            "categoria": self.menu_categoria,
        }
        widget = campos.get(campo or "", self.entry_sku)
        widget.focus_set()

    def _mostrar_mensaje(self, texto: str, color: tuple[str, str] = COLOR_TEXTO) -> None:
        self.label_mensaje.configure(text=texto, text_color=color)
