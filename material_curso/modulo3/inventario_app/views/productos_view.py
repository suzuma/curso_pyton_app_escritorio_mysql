"""
Pantalla de productos con datos en memoria (Módulo 3).

Izquierda: filtros y tabla (ttk.Treeview). Derecha: un CTkTabview con el
formulario de captura y una pestaña de estadísticas. La validación no está
aquí: la hacen las propiedades de Producto (Módulo 2), y la vista solo
muestra el mensaje de la excepción.
"""

from __future__ import annotations

from tkinter import ttk
from typing import Optional

import customtkinter as ctk

from models.categoria import Categoria
from models.producto import Producto
from repositories.producto_repository import RepositorioProductos
from utils.estadistica import estadisticas

TODAS = "Todas"
COLOR_ERROR = ("#C62828", "#EF5350")
COLOR_EXITO = ("#2E7D32", "#66BB6A")


class ProductosView(ctk.CTkFrame):
    """Captura, validación y filtrado de productos."""

    def __init__(self, master: ctk.CTk, repositorio: RepositorioProductos) -> None:
        super().__init__(master, fg_color="transparent")
        self.repo = repositorio
        self._crear_filtros()
        self._crear_tabla()
        self._crear_panel()
        # grid: la columna 0 (tabla) crece; la 1 (panel) conserva su ancho.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.refrescar()

    # ------------------------------------------------------------ interfaz
    def _crear_filtros(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.entry_buscar = ctk.CTkEntry(barra, placeholder_text="Buscar por SKU o nombre…", width=240)
        self.entry_buscar.pack(side="left")
        # Evento de teclado: se filtra al soltar cada tecla.
        self.entry_buscar.bind("<KeyRelease>", lambda _evento: self.refrescar())

        self.menu_categoria = ctk.CTkOptionMenu(barra, values=[TODAS], command=lambda _v: self.refrescar())
        self.menu_categoria.pack(side="left", padx=8)

        self.var_bajo = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(barra, text="Solo stock bajo", variable=self.var_bajo,
                        command=self.refrescar).pack(side="left")

    def _crear_tabla(self) -> None:
        columnas = ("sku", "nombre", "categoria", "precio", "stock")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=14)
        for col, titulo, ancho, alinear in (
            ("sku", "SKU", 90, "w"), ("nombre", "Nombre", 200, "w"), ("categoria", "Categoría", 110, "w"),
            ("precio", "Precio", 90, "e"), ("stock", "Stock", 60, "center"),
        ):
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor=alinear)
        self.tabla.tag_configure("bajo", foreground="#E65100")
        self.tabla.grid(row=1, column=0, sticky="nsew")
        # Evento de selección: carga el producto en el formulario.
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        self.label_resumen = ctk.CTkLabel(self, text="", anchor="w", text_color="gray")
        self.label_resumen.grid(row=2, column=0, sticky="ew", pady=(6, 0))

    def _crear_panel(self) -> None:
        self.tabs = ctk.CTkTabview(self, width=300)
        self.tabs.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(16, 0))
        self._crear_formulario(self.tabs.add("Producto"))
        self._crear_estadisticas(self.tabs.add("Estadísticas"))

    def _crear_formulario(self, pestana: ctk.CTkFrame) -> None:
        self.campos: dict[str, ctk.CTkEntry] = {}
        for clave, etiqueta in (("sku", "SKU"), ("nombre", "Nombre"), ("categoria", "Categoría"),
                                ("precio", "Precio"), ("stock", "Stock")):
            ctk.CTkLabel(pestana, text=etiqueta).pack(anchor="w")
            entrada = ctk.CTkEntry(pestana)
            entrada.pack(fill="x", pady=(0, 6))
            entrada.bind("<Return>", lambda _e: self._guardar())
            self.campos[clave] = entrada

        self.label_mensaje = ctk.CTkLabel(pestana, text="", wraplength=250, justify="left")
        self.label_mensaje.pack(fill="x", pady=4)
        ctk.CTkButton(pestana, text="Guardar", command=self._guardar).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(pestana, text="Limpiar", fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), command=self._limpiar).pack(fill="x")

    def _crear_estadisticas(self, pestana: ctk.CTkFrame) -> None:
        ctk.CTkLabel(pestana, text="Precios de los productos visibles",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 8))
        self.label_estadisticas = ctk.CTkLabel(pestana, text="", justify="left", anchor="w")
        self.label_estadisticas.pack(fill="x")

    # ------------------------------------------------------------ datos
    def _filtrados(self) -> list[Producto]:
        """Aplica los tres filtros con una comprensión de lista."""
        texto = self.entry_buscar.get().strip().lower()
        categoria = self.menu_categoria.get()
        return [
            p for p in self.repo.listar()
            if (texto in p.sku.lower() or texto in p.nombre.lower())
            and (categoria == TODAS or str(p.categoria) == categoria)
            and (not self.var_bajo.get() or p.stock_bajo)
        ]

    def refrescar(self) -> None:
        """Vuelve a dibujar la tabla, el resumen y las estadísticas."""
        categorias = sorted({str(p.categoria) for p in self.repo.listar()})
        self.menu_categoria.configure(values=[TODAS, *categorias])

        self.tabla.delete(*self.tabla.get_children())
        productos = self._filtrados()
        for p in productos:
            self.tabla.insert("", "end", iid=p.sku, tags=("bajo",) if p.stock_bajo else (),
                              values=(p.sku, p.nombre, p.categoria, f"${p.precio:,.2f}", p.stock))

        total = sum((p.valor_inventario for p in productos), start=0)
        self.label_resumen.configure(text=f"{len(productos)} productos  ·  valor: ${total:,.2f}")

        if productos:
            datos = estadisticas(*(p.precio for p in productos))
            texto = "\n".join(f"{nombre:<9} ${valor:,.2f}" for nombre, valor in datos.items())
        else:
            texto = "Sin productos para calcular."
        self.label_estadisticas.configure(text=texto)

    # ------------------------------------------------------------ eventos
    def _al_seleccionar(self, _evento: object) -> None:
        seleccion = self.tabla.selection()
        producto: Optional[Producto] = self.repo.obtener(seleccion[0]) if seleccion else None
        if producto is None:
            return
        for clave, valor in (("sku", producto.sku), ("nombre", producto.nombre),
                             ("categoria", str(producto.categoria)), ("precio", str(producto.precio)),
                             ("stock", str(producto.stock))):
            self.campos[clave].delete(0, "end")
            self.campos[clave].insert(0, valor)
        self.tabs.set("Producto")

    def _guardar(self) -> None:
        """Crea el producto o, si el SKU ya existe, lo reemplaza con los datos nuevos."""
        valores = {clave: entrada.get() for clave, entrada in self.campos.items()}
        try:
            stock = int(valores["stock"])
        except ValueError:
            self._mensaje("El stock debe ser un número entero.", COLOR_ERROR)
            return
        try:
            producto = Producto(valores["sku"], valores["nombre"], Categoria(valores["categoria"]),
                                valores["precio"], stock)
        except ValueError as err:          # la validación vive en Producto
            self._mensaje(str(err), COLOR_ERROR)
            return
        existia = self.repo.eliminar(producto.sku)
        self.repo.agregar(producto)
        self.refrescar()
        self.tabla.selection_set(producto.sku)
        self._mensaje("Cambios guardados." if existia else "Producto agregado.", COLOR_EXITO)

    def _limpiar(self) -> None:
        for entrada in self.campos.values():
            entrada.delete(0, "end")
        self.tabla.selection_remove(*self.tabla.selection())
        self._mensaje("")

    def _mensaje(self, texto: str, color: tuple[str, str] = ("gray10", "gray90")) -> None:
        self.label_mensaje.configure(text=texto, text_color=color)
