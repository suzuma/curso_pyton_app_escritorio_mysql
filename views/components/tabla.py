"""
Componente de tabla reutilizable.

CustomTkinter no incluye un widget de tabla, así que se usa ``ttk.Treeview``
de Tkinter estándar y se le aplican colores parecidos a los del tema de
CustomTkinter (claro u oscuro). Las pantallas de categorías, productos y
usuarios usan este mismo componente.
"""

from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Callable, Literal, Optional, Sequence

import customtkinter as ctk

NOMBRE_ESTILO: str = "Tabla.Treeview"
ALTO_FILA: int = 28

# Colores por tema: (claro, oscuro)
_COLORES: dict[str, tuple[str, str]] = {
    "fondo": ("#FFFFFF", "#2B2B2B"),
    "texto": ("#1A1A1A", "#DCE4EE"),
    "encabezado": ("#E4E4E4", "#333333"),
    "seleccion": ("#3A7EBF", "#1F538D"),
    "fila_alterna": ("#F4F6F8", "#303030"),
}

Alineacion = Literal["w", "center", "e"]


@dataclass(frozen=True)
class Columna:
    """
    Definición de una columna de la tabla.

    Attributes:
        clave: Identificador interno de la columna.
        titulo: Texto del encabezado.
        ancho: Ancho inicial en píxeles.
        alineacion: ``"w"`` (izquierda), ``"center"`` o ``"e"`` (derecha).
        expandir: Si es ``True``, la columna ocupa el espacio sobrante.
    """

    clave: str
    titulo: str
    ancho: int = 120
    alineacion: Alineacion = "w"
    expandir: bool = False


class Tabla(ctk.CTkFrame):
    """
    ``Treeview`` con barra de desplazamiento y colores según el tema.

    Cada fila se identifica con el ``id`` del registro (se usa como ``iid``
    del Treeview), de modo que la vista puede saber qué registro eligió el
    usuario sin depender de la posición de la fila.

    Args:
        master: Contenedor padre.
        columnas: Columnas a mostrar, en orden.
        on_seleccion: Función que recibe el id seleccionado (o ``None``)
            cada vez que cambia la selección.
    """

    def __init__(
        self,
        master: Any,
        columnas: Sequence[Columna],
        on_seleccion: Optional[Callable[[Optional[int]], None]] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_seleccion = on_seleccion
        self._aplicar_estilo()

        claves = [c.clave for c in columnas]
        self.tree = ttk.Treeview(
            self, columns=claves, show="headings", selectmode="browse", style=NOMBRE_ESTILO
        )
        for col in columnas:
            self.tree.heading(col.clave, text=col.titulo, anchor=col.alineacion)
            self.tree.column(
                col.clave,
                width=col.ancho,
                minwidth=40,
                anchor=col.alineacion,
                stretch=col.expandir,
            )
        self.tree.tag_configure("alterna", background=self._color("fila_alterna"))

        barra = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def cargar(
        self,
        filas: Sequence[tuple[int, Sequence[Any]]],
        etiquetas: Optional[dict[int, str]] = None,
    ) -> None:
        """
        Reemplaza el contenido de la tabla.

        Args:
            filas: Pares ``(id, valores)``; ``valores`` debe tener un
                elemento por columna.
            etiquetas: Opcional. Asocia el id de un registro con una
                etiqueta definida con ``configurar_etiqueta`` (por ejemplo,
                para pintar de otro color los productos con stock bajo).
        """
        etiquetas = etiquetas or {}
        self.tree.delete(*self.tree.get_children())
        for indice, (registro_id, valores) in enumerate(filas):
            tags: list[str] = ["alterna"] if indice % 2 else []
            if registro_id in etiquetas:
                tags.append(etiquetas[registro_id])
            self.tree.insert("", "end", iid=str(registro_id), values=list(valores), tags=tags)

    def configurar_etiqueta(self, nombre: str, color_texto: tuple[str, str]) -> None:
        """
        Define una etiqueta que cambia el color del texto de las filas.

        Args:
            nombre: Nombre de la etiqueta.
            color_texto: Color para el tema claro y para el oscuro.
        """
        claro, oscuro = color_texto
        color = oscuro if ctk.get_appearance_mode() == "Dark" else claro
        self.tree.tag_configure(nombre, foreground=color)

    def id_seleccionado(self) -> Optional[int]:
        """Devuelve el id de la fila seleccionada, o ``None``."""
        seleccion = self.tree.selection()
        return int(seleccion[0]) if seleccion else None

    def seleccionar(self, registro_id: int) -> None:
        """Selecciona y hace visible la fila del registro indicado, si existe."""
        iid = str(registro_id)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    def limpiar_seleccion(self) -> None:
        """Quita la selección actual."""
        self.tree.selection_remove(*self.tree.selection())

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _al_seleccionar(self, _evento: object) -> None:
        if self._on_seleccion is not None:
            self._on_seleccion(self.id_seleccionado())

    @staticmethod
    def _color(nombre: str) -> str:
        """Elige el color claro u oscuro según el modo de apariencia activo."""
        claro, oscuro = _COLORES[nombre]
        return oscuro if ctk.get_appearance_mode() == "Dark" else claro

    def _aplicar_estilo(self) -> None:
        """Configura el estilo ttk compartido por todas las tablas."""
        estilo = ttk.Style(self)
        # "clam" es el tema de ttk que permite cambiar colores en todas
        # las plataformas (los temas nativos de Windows/macOS los ignoran).
        estilo.theme_use("clam")
        fondo, texto = self._color("fondo"), self._color("texto")
        # Sin marco: el tema "clam" dibuja un borde claro alrededor del área.
        estilo.layout(NOMBRE_ESTILO, [("Treeview.treearea", {"sticky": "nswe"})])
        estilo.configure(
            NOMBRE_ESTILO,
            background=fondo,
            fieldbackground=fondo,
            foreground=texto,
            rowheight=ALTO_FILA,
            borderwidth=0,
        )
        estilo.map(
            NOMBRE_ESTILO,
            background=[("selected", self._color("seleccion"))],
            foreground=[("selected", "#FFFFFF")],
        )
        estilo.configure(
            f"{NOMBRE_ESTILO}.Heading",
            background=self._color("encabezado"),
            foreground=texto,
            relief="flat",
            padding=(8, 6),
        )
        estilo.map(f"{NOMBRE_ESTILO}.Heading", background=[("active", self._color("encabezado"))])
