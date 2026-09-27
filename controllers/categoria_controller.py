"""
Controlador de categorías.

Recibe los datos tal como vienen del formulario (texto), los limpia y valida,
y solo entonces llama al repositorio. Convierte los errores de persistencia
en ``ControllerError`` para que la vista solo tenga que mostrar el mensaje.
"""

from __future__ import annotations

from typing import Optional

from config.db_connection import DatabaseConnectionError
from controllers.exceptions import ControllerError, ValidationError
from controllers.permisos import Permiso, exigir_permiso
from models.categoria import Categoria
from models.usuario import Usuario
from repositories.categoria_repository import CategoriaRepository
from repositories.exceptions import RepositoryError

NOMBRE_MAX: int = 100  # VARCHAR(100) en la tabla
NOMBRE_MIN: int = 2
DESCRIPCION_MAX: int = 500  # la columna es TEXT; el límite es una regla de negocio


class CategoriaController:
    """Casos de uso de la gestión de categorías."""

    def __init__(
        self, usuario_actual: Usuario, repositorio: Optional[CategoriaRepository] = None
    ) -> None:
        """
        Args:
            usuario_actual: Usuario de la sesión, para comprobar permisos.
            repositorio: Repositorio a usar; se puede inyectar uno simulado
                para pruebas.
        """
        self._actual = usuario_actual
        self._repositorio = repositorio or CategoriaRepository()

    def listar(self, texto: str = "") -> list[Categoria]:
        """
        Devuelve las categorías, opcionalmente filtradas.

        Args:
            texto: Texto a buscar en nombre o descripción.

        Raises:
            ControllerError: Si no se pudo consultar la base de datos.
        """
        try:
            return self._repositorio.listar(texto.strip())
        except (DatabaseConnectionError, RepositoryError) as err:
            raise ControllerError(f"No se pudieron cargar las categorías. {err}") from err

    def crear(self, nombre: str, descripcion: str = "") -> Categoria:
        """
        Valida y registra una categoría nueva.

        Args:
            nombre: Nombre escrito en el formulario.
            descripcion: Descripción escrita en el formulario.

        Returns:
            Categoria: La categoría creada, ya con su ``id``.

        Raises:
            ValidationError: Si algún dato es inválido.
            ControllerError: Si el nombre ya existe o falla la base de datos.
            PermisoDenegadoError: Si el usuario no es administrador.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_CATEGORIAS)
        categoria = Categoria(
            nombre=self._validar_nombre(nombre),
            descripcion=self._validar_descripcion(descripcion),
        )
        try:
            self._repositorio.crear(categoria)
        except (DatabaseConnectionError, RepositoryError) as err:
            raise ControllerError(str(err)) from err
        return categoria

    def actualizar(self, categoria_id: int, nombre: str, descripcion: str = "") -> Categoria:
        """
        Valida y guarda los cambios de una categoría existente.

        Args:
            categoria_id: Id de la categoría a modificar.
            nombre: Nombre nuevo.
            descripcion: Descripción nueva.

        Returns:
            Categoria: La categoría con los datos actualizados.

        Raises:
            ValidationError: Si algún dato es inválido.
            ControllerError: Si la categoría ya no existe, el nombre está
                repetido o falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_CATEGORIAS)
        categoria = Categoria(
            id=categoria_id,
            nombre=self._validar_nombre(nombre),
            descripcion=self._validar_descripcion(descripcion),
        )
        try:
            existia = self._repositorio.actualizar(categoria)
        except (DatabaseConnectionError, RepositoryError) as err:
            raise ControllerError(str(err)) from err
        if not existia:
            raise ControllerError("La categoría ya no existe; actualice la lista.")
        return categoria

    def eliminar(self, categoria_id: int) -> None:
        """
        Elimina una categoría sin productos.

        Args:
            categoria_id: Id de la categoría.

        Raises:
            ControllerError: Si la categoría tiene productos, ya no existe
                o falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_CATEGORIAS)
        try:
            eliminada = self._repositorio.eliminar(categoria_id)
        except (DatabaseConnectionError, RepositoryError) as err:
            raise ControllerError(str(err)) from err
        if not eliminada:
            raise ControllerError("La categoría ya no existe; actualice la lista.")

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        """
        Limpia espacios sobrantes y valida la longitud del nombre.

        ``" ".join(nombre.split())`` quita espacios al inicio y al final y
        convierte los espacios repetidos intermedios en uno solo.
        """
        limpio = " ".join(nombre.split())
        if not limpio:
            raise ValidationError("El nombre es obligatorio.", campo="nombre")
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
    def _validar_descripcion(descripcion: str) -> Optional[str]:
        """Devuelve ``None`` si la descripción está vacía y valida su longitud."""
        limpia = descripcion.strip()
        if len(limpia) > DESCRIPCION_MAX:
            raise ValidationError(
                f"La descripción admite como máximo {DESCRIPCION_MAX} caracteres.",
                campo="descripcion",
            )
        return limpia or None
