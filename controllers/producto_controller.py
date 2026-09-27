"""
Controlador de productos.

El formulario entrega todo como texto. Este controlador convierte cada campo
al tipo correcto (``Decimal`` para el precio, ``int`` para el stock), aplica
las reglas de negocio y solo entonces llama al repositorio.

Validar aquí, aunque la tabla tenga restricciones ``CHECK`` y ``UNIQUE``,
permite dar mensajes claros por campo y evita viajes innecesarios a la base
de datos. Las restricciones de MySQL siguen siendo la última línea de defensa.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from config.db_connection import DatabaseConnectionError
from controllers.exceptions import ControllerError, ValidationError
from controllers.permisos import Permiso, exigir_permiso, tiene_permiso
from models.categoria import Categoria
from models.producto import Producto
from models.usuario import Usuario
from repositories.categoria_repository import CategoriaRepository
from repositories.exceptions import RepositoryError
from repositories.producto_repository import ProductoRepository

# Reglas derivadas de la tabla: sku VARCHAR(50), nombre VARCHAR(150),
# precio DECIMAL(10, 2), stock INT.
SKU_PATRON: re.Pattern[str] = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,49}$")
# Número con comas de miles: 1,250 | 1,250.50 | 12,345,678.9
MILES_PATRON: re.Pattern[str] = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")
NOMBRE_MIN: int = 2
NOMBRE_MAX: int = 150
PRECIO_MAX: Decimal = Decimal("99999999.99")
STOCK_MAX: int = 2_147_483_647

# Regla de negocio: con esta cantidad o menos se considera stock bajo.
STOCK_MINIMO: int = 5

_ERRORES_BD = (DatabaseConnectionError, RepositoryError)


class ProductoController:
    """Casos de uso de la gestión de productos."""

    def __init__(
        self,
        usuario_actual: Usuario,
        repositorio: Optional[ProductoRepository] = None,
        repositorio_categorias: Optional[CategoriaRepository] = None,
    ) -> None:
        """
        Args:
            usuario_actual: Usuario de la sesión, para comprobar permisos.
            repositorio: Repositorio de productos (inyectable para pruebas).
            repositorio_categorias: Repositorio de categorías, usado para
                llenar la lista desplegable y validar la categoría elegida.
        """
        self._actual = usuario_actual
        self._repositorio = repositorio or ProductoRepository()
        self._categorias = repositorio_categorias or CategoriaRepository()

    @property
    def puede_cambiar_estado(self) -> bool:
        """Indica si el usuario actual puede activar o desactivar productos."""
        return tiene_permiso(self._actual, Permiso.CAMBIAR_ESTADO_PRODUCTOS)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def listar(
        self,
        texto: str = "",
        categoria_id: Optional[int] = None,
        incluir_inactivos: bool = False,
    ) -> list[Producto]:
        """
        Devuelve los productos filtrados.

        Raises:
            ControllerError: Si no se pudo consultar la base de datos.
        """
        try:
            return self._repositorio.listar(texto.strip(), categoria_id, incluir_inactivos)
        except _ERRORES_BD as err:
            raise ControllerError(f"No se pudieron cargar los productos. {err}") from err

    def listar_categorias(self) -> list[Categoria]:
        """
        Devuelve las categorías para las listas desplegables.

        Raises:
            ControllerError: Si no se pudo consultar la base de datos.
        """
        try:
            return self._categorias.listar()
        except _ERRORES_BD as err:
            raise ControllerError(f"No se pudieron cargar las categorías. {err}") from err

    @staticmethod
    def es_stock_bajo(producto: Producto) -> bool:
        """Indica si el producto está en el nivel mínimo de existencias o por debajo."""
        return producto.stock <= STOCK_MINIMO

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def crear(
        self,
        sku: str,
        nombre: str,
        precio: str,
        stock: str,
        categoria_id: Optional[int],
    ) -> Producto:
        """
        Valida y registra un producto nuevo.

        Args:
            sku: Código escrito en el formulario.
            nombre: Nombre del producto.
            precio: Precio como texto (p. ej. ``"85.50"`` o ``"$1,250.00"``).
            stock: Existencias como texto.
            categoria_id: Id de la categoría elegida, o ``None``.

        Returns:
            Producto: El producto creado, ya con su ``id``.

        Raises:
            ValidationError: Si algún dato es inválido.
            ControllerError: Si el SKU ya existe o falla la base de datos.
            PermisoDenegadoError: Si el usuario no puede gestionar productos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_PRODUCTOS)
        producto = self._construir(None, sku, nombre, precio, stock, categoria_id)
        try:
            self._repositorio.crear(producto)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        return producto

    def actualizar(
        self,
        producto_id: int,
        sku: str,
        nombre: str,
        precio: str,
        stock: str,
        categoria_id: Optional[int],
    ) -> Producto:
        """
        Valida y guarda los cambios de un producto.

        Raises:
            ValidationError: Si algún dato es inválido.
            ControllerError: Si el producto ya no existe, el SKU está
                repetido o falla la base de datos.
            PermisoDenegadoError: Si el usuario no puede gestionar productos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_PRODUCTOS)
        producto = self._construir(producto_id, sku, nombre, precio, stock, categoria_id)
        try:
            existia = self._repositorio.actualizar(producto)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        if not existia:
            raise ControllerError("El producto ya no existe; actualice la lista.")
        return producto

    def cambiar_estado(self, producto_id: int, activo: bool) -> None:
        """
        Activa o desactiva un producto.

        Raises:
            ControllerError: Si el producto ya no existe o falla la base de datos.
            PermisoDenegadoError: Si el rol del usuario no lo permite.
        """
        exigir_permiso(self._actual, Permiso.CAMBIAR_ESTADO_PRODUCTOS)
        try:
            existia = self._repositorio.cambiar_estado(producto_id, activo)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        if not existia:
            raise ControllerError("El producto ya no existe; actualice la lista.")

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    def _construir(
        self,
        producto_id: Optional[int],
        sku: str,
        nombre: str,
        precio: str,
        stock: str,
        categoria_id: Optional[int],
    ) -> Producto:
        """
        Valida todos los campos y arma el objeto ``Producto``.

        Los argumentos se evalúan de arriba hacia abajo, así que el orden
        coincide con el del formulario: el usuario ve primero el error del
        campo que aparece más arriba.
        """
        return Producto(
            id=producto_id,
            sku=self._validar_sku(sku),
            nombre=self._validar_nombre(nombre),
            categoria_id=self._validar_categoria(categoria_id),
            precio=self._validar_precio(precio),
            stock=self._validar_stock(stock),
        )

    @staticmethod
    def _validar_sku(sku: str) -> str:
        """
        Normaliza el SKU a mayúsculas y comprueba su formato.

        Se aceptan letras sin acentos, números y guiones; debe empezar con
        letra o número y medir entre 2 y 50 caracteres.
        """
        limpio = sku.strip().upper()
        if not limpio:
            raise ValidationError("El SKU es obligatorio.", campo="sku")
        if not SKU_PATRON.fullmatch(limpio):
            raise ValidationError(
                "El SKU solo admite letras, números y guiones (2 a 50 caracteres), "
                "p. ej. PROD-004.",
                campo="sku",
            )
        return limpio

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        """Quita espacios sobrantes y valida la longitud del nombre."""
        limpio = " ".join(nombre.split())
        if len(limpio) < NOMBRE_MIN:
            raise ValidationError(
                f"El nombre debe tener al menos {NOMBRE_MIN} caracteres.", campo="nombre"
            )
        if len(limpio) > NOMBRE_MAX:
            raise ValidationError(
                f"El nombre admite como máximo {NOMBRE_MAX} caracteres.", campo="nombre"
            )
        return limpio

    @staticmethod
    def _validar_precio(texto: str) -> Decimal:
        """
        Convierte el precio a ``Decimal`` y valida su rango.

        Acepta el signo ``$`` y comas como separador de miles
        (``"$1,250.50"``). El punto es el separador decimal.
        """
        limpio = texto.strip().replace("$", "").replace(" ", "")
        if not limpio:
            raise ValidationError("El precio es obligatorio.", campo="precio")
        if "," in limpio:
            # Solo se aceptan comas como separador de miles bien formado
            # ("1,250.50"). Un texto como "85,50" es ambiguo: quitar la coma
            # lo convertiría en 8550, así que se rechaza.
            if not MILES_PATRON.fullmatch(limpio):
                raise ValidationError(
                    "Use punto como separador decimal, p. ej. 85.50.", campo="precio"
                )
            limpio = limpio.replace(",", "")
        try:
            precio = Decimal(limpio)
        except InvalidOperation as exc:
            raise ValidationError(
                "El precio debe ser un número, p. ej. 85.50.", campo="precio"
            ) from exc

        if not precio.is_finite():
            raise ValidationError("El precio debe ser un número, p. ej. 85.50.", campo="precio")
        if precio < 0:
            raise ValidationError("El precio no puede ser negativo.", campo="precio")
        if precio > PRECIO_MAX:
            raise ValidationError(f"El precio máximo es {PRECIO_MAX:,}.", campo="precio")
        # as_tuple().exponent indica cuántos decimales tiene: -2 → dos decimales.
        exponente = precio.as_tuple().exponent
        if isinstance(exponente, int) and exponente < -2:
            raise ValidationError("El precio admite como máximo dos decimales.", campo="precio")
        return precio.quantize(Decimal("0.01"))

    @staticmethod
    def _validar_stock(texto: str) -> int:
        """Convierte el stock a entero y valida que no sea negativo."""
        limpio = texto.strip()
        if not limpio:
            raise ValidationError("El stock es obligatorio.", campo="stock")
        if "," in limpio and MILES_PATRON.fullmatch(limpio):
            limpio = limpio.replace(",", "")
        if not limpio.lstrip("-").isdigit():
            raise ValidationError(
                "El stock debe ser un número entero, sin decimales.", campo="stock"
            )
        stock = int(limpio)
        if stock < 0:
            raise ValidationError("El stock no puede ser negativo.", campo="stock")
        if stock > STOCK_MAX:
            raise ValidationError("El stock excede el máximo permitido.", campo="stock")
        return stock

    @staticmethod
    def _validar_categoria(categoria_id: Optional[int]) -> int:
        """Exige que se haya elegido una categoría."""
        if categoria_id is None:
            raise ValidationError("Seleccione una categoría.", campo="categoria")
        return categoria_id
