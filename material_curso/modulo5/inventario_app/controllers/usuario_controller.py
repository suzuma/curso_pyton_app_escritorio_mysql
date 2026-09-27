"""
Controlador de gestión de usuarios.

Solo los administradores pueden usarlo. Además de validar los datos del
formulario, aplica reglas que protegen al propio sistema:

* un usuario no puede desactivarse ni quitarse el rol de administrador a sí
  mismo (se quedaría fuera en medio de su sesión);
* siempre debe quedar al menos un administrador activo; de lo contrario,
  nadie podría volver a gestionar usuarios.

Las contraseñas llegan en texto plano desde el formulario y se convierten en
hash bcrypt aquí; el repositorio solo recibe y guarda el hash.
"""

from __future__ import annotations

import re
from typing import Optional

from config.db_connection import DatabaseConnectionError
from controllers.exceptions import ControllerError, ValidationError
from controllers.permisos import ROL_ADMINISTRADOR, Permiso, exigir_permiso
from models.rol import Rol
from models.usuario import Usuario
from repositories.exceptions import DuplicateEntryError, RepositoryError
from repositories.rol_repository import RolRepository
from repositories.usuario_repository import UsuarioRepository
from utils.security import PasswordError, hash_password, validar_politica

NOMBRE_MIN: int = 2
NOMBRE_MAX: int = 100  # VARCHAR(100)
EMAIL_MAX: int = 120  # VARCHAR(120)
# Validación básica de formato: algo@algo.algo, sin espacios.
EMAIL_PATRON: re.Pattern[str] = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_ERRORES_BD = (DatabaseConnectionError, RepositoryError)


class UsuarioController:
    """
    Casos de uso de la administración de usuarios.

    Args:
        usuario_actual: Usuario que tiene la sesión abierta; se usa para
            comprobar permisos y para las reglas sobre la propia cuenta.
        repositorio: Repositorio de usuarios (inyectable para pruebas).
        repositorio_roles: Repositorio de roles.
    """

    def __init__(
        self,
        usuario_actual: Usuario,
        repositorio: Optional[UsuarioRepository] = None,
        repositorio_roles: Optional[RolRepository] = None,
    ) -> None:
        self._actual = usuario_actual
        self._repositorio = repositorio or UsuarioRepository()
        self._roles = repositorio_roles or RolRepository()

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def listar(self, texto: str = "", incluir_inactivos: bool = True) -> list[Usuario]:
        """
        Devuelve los usuarios, opcionalmente filtrados por nombre o correo.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ControllerError: Si falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        try:
            return self._repositorio.listar(
                solo_activos=not incluir_inactivos, texto=texto.strip()
            )
        except _ERRORES_BD as err:
            raise ControllerError(f"No se pudieron cargar los usuarios. {err}") from err

    def listar_roles(self) -> list[Rol]:
        """
        Devuelve los roles disponibles para la lista desplegable.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ControllerError: Si falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        try:
            return self._roles.listar()
        except _ERRORES_BD as err:
            raise ControllerError(f"No se pudieron cargar los roles. {err}") from err

    def es_usuario_actual(self, usuario_id: Optional[int]) -> bool:
        """Indica si el id corresponde a quien tiene la sesión abierta."""
        return usuario_id is not None and usuario_id == self._actual.id

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def crear(
        self,
        nombre: str,
        email: str,
        rol_id: Optional[int],
        password: str,
        confirmacion: str,
    ) -> Usuario:
        """
        Registra un usuario nuevo con su contraseña inicial.

        Returns:
            Usuario: El usuario creado, con ``id`` y rol.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ValidationError: Si algún dato es inválido.
            ControllerError: Si falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        usuario = Usuario(
            nombre=self._validar_nombre(nombre),
            email=self._validar_email(email),
            rol_id=self._validar_rol(rol_id).id or 0,
        )
        usuario.password_hash = self._hash_validado(password, confirmacion)

        try:
            self._repositorio.crear(usuario)
            creado = self._repositorio.obtener_por_id(usuario.id or 0)
        except DuplicateEntryError as err:
            raise ValidationError(str(err), campo="email") from err
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        return creado or usuario

    def actualizar(
        self, usuario_id: int, nombre: str, email: str, rol_id: Optional[int]
    ) -> Usuario:
        """
        Modifica nombre, correo y rol de un usuario.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ValidationError: Si algún dato es inválido o se incumple una
                regla sobre administradores.
            ControllerError: Si el usuario no existe o falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        existente = self._obtener(usuario_id)
        nombre_limpio = self._validar_nombre(nombre)
        email_limpio = self._validar_email(email)
        rol = self._validar_rol(rol_id)

        deja_de_ser_admin = self._es_admin(existente) and rol.nombre != ROL_ADMINISTRADOR
        if deja_de_ser_admin:
            if self.es_usuario_actual(usuario_id):
                raise ValidationError(
                    "No puede quitarse a sí mismo el rol de Administrador.", campo="rol"
                )
            if existente.activo:
                self._exigir_otro_admin(usuario_id)

        existente.nombre = nombre_limpio
        existente.email = email_limpio
        existente.rol_id = rol.id or existente.rol_id
        existente.rol = rol
        try:
            self._repositorio.actualizar(existente)
        except DuplicateEntryError as err:
            raise ValidationError(str(err), campo="email") from err
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err

        if self.es_usuario_actual(usuario_id):
            # Mantiene sincronizados los datos de la sesión.
            self._actual.nombre = existente.nombre
            self._actual.email = existente.email
        return existente

    def cambiar_estado(self, usuario_id: int, activo: bool) -> None:
        """
        Activa o desactiva un usuario.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ValidationError: Si intenta desactivarse a sí mismo o al último
                administrador activo.
            ControllerError: Si el usuario no existe o falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        existente = self._obtener(usuario_id)
        if not activo:
            if self.es_usuario_actual(usuario_id):
                raise ValidationError("No puede desactivar su propia cuenta.")
            if self._es_admin(existente) and existente.activo:
                self._exigir_otro_admin(usuario_id)
        try:
            self._repositorio.cambiar_estado(usuario_id, activo)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err

    def restablecer_password(self, usuario_id: int, password: str, confirmacion: str) -> None:
        """
        Asigna una contraseña nueva a otro usuario (por ejemplo, si la olvidó).

        El administrador no necesita conocer la contraseña anterior. Para
        cambiar la propia se usa ``AuthController.cambiar_password``, que sí
        la pide.

        Raises:
            PermisoDenegadoError: Si el usuario actual no es administrador.
            ValidationError: Si la contraseña no cumple la política o no
                coincide con la confirmación.
            ControllerError: Si el usuario no existe o falla la base de datos.
        """
        exigir_permiso(self._actual, Permiso.GESTIONAR_USUARIOS)
        self._obtener(usuario_id)
        nuevo_hash = self._hash_validado(password, confirmacion)
        try:
            self._repositorio.actualizar_password(usuario_id, nuevo_hash)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err

    # ------------------------------------------------------------------
    # Reglas y validaciones
    # ------------------------------------------------------------------
    def _obtener(self, usuario_id: int) -> Usuario:
        try:
            usuario = self._repositorio.obtener_por_id(usuario_id)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        if usuario is None:
            raise ControllerError("El usuario ya no existe; actualice la lista.")
        return usuario

    def _exigir_otro_admin(self, usuario_id: int) -> None:
        """Garantiza que, sin este usuario, quede otro administrador activo."""
        try:
            otros = self._repositorio.contar_activos_por_rol(ROL_ADMINISTRADOR, usuario_id)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        if otros == 0:
            raise ValidationError(
                "Debe quedar al menos un administrador activo en el sistema.", campo="rol"
            )

    @staticmethod
    def _es_admin(usuario: Usuario) -> bool:
        return usuario.rol is not None and usuario.rol.nombre == ROL_ADMINISTRADOR

    def _validar_rol(self, rol_id: Optional[int]) -> Rol:
        if rol_id is None:
            raise ValidationError("Seleccione un rol.", campo="rol")
        try:
            rol = self._roles.obtener_por_id(rol_id)
        except _ERRORES_BD as err:
            raise ControllerError(str(err)) from err
        if rol is None:
            raise ValidationError("El rol seleccionado no existe.", campo="rol")
        return rol

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
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
    def _validar_email(email: str) -> str:
        """Normaliza el correo a minúsculas y valida su formato."""
        limpio = email.strip().lower()
        if not limpio:
            raise ValidationError("El correo es obligatorio.", campo="email")
        if len(limpio) > EMAIL_MAX or not EMAIL_PATRON.fullmatch(limpio):
            raise ValidationError(
                "Escriba un correo válido, p. ej. nombre@escuela.edu.", campo="email"
            )
        return limpio

    @staticmethod
    def _hash_validado(password: str, confirmacion: str) -> str:
        """Valida la política y la confirmación, y devuelve el hash bcrypt."""
        try:
            validar_politica(password)
        except PasswordError as err:
            raise ValidationError(str(err), campo="password") from err
        if password != confirmacion:
            raise ValidationError("Las contraseñas no coinciden.", campo="confirmacion")
        return hash_password(password)
