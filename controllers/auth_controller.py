"""
Controlador de autenticación.

Aplica las reglas de negocio del inicio de sesión: valida los datos del
formulario, busca al usuario, verifica la contraseña con bcrypt y guarda
quién es el usuario de la sesión actual.

Las vistas solo deben llamar a este controlador y capturar ``AuthError``;
no necesitan saber nada de MySQL ni de bcrypt.
"""

from __future__ import annotations

from typing import Optional

from config.db_connection import DatabaseConnectionError
from controllers.exceptions import ControllerError
from models.usuario import Usuario
from repositories.exceptions import RepositoryError
from repositories.usuario_repository import UsuarioRepository
from utils.security import PasswordError, hash_password, verify_password

MENSAJE_CREDENCIALES_INVALIDAS: str = "Correo o contraseña incorrectos."

# Hash de una contraseña aleatoria. Se usa para gastar el mismo tiempo en
# verificar cuando el correo no existe (ver ``iniciar_sesion``).
_HASH_SENUELO: str = hash_password("senuelo-sin-usuario-2026")


class AuthError(ControllerError):
    """
    Error de autenticación con un mensaje apto para mostrarse al usuario.
    """


class AuthController:
    """
    Gestiona el inicio y cierre de sesión.

    Attributes:
        usuario_actual: Usuario autenticado, o ``None`` si no hay sesión.
    """

    def __init__(self, repositorio: Optional[UsuarioRepository] = None) -> None:
        """
        Args:
            repositorio: Repositorio de usuarios. Se puede inyectar uno
                distinto (por ejemplo, un simulado) para hacer pruebas.
        """
        self._repositorio: UsuarioRepository = repositorio or UsuarioRepository()
        self.usuario_actual: Optional[Usuario] = None

    def iniciar_sesion(self, email: str, password: str) -> Usuario:
        """
        Autentica a un usuario con su correo y contraseña.

        Por seguridad, el mensaje de error es el mismo si el correo no existe
        o si la contraseña es incorrecta; así no se revela qué correos están
        registrados. Por la misma razón, cuando el correo no existe se
        verifica un hash señuelo, para que la respuesta tarde lo mismo en
        ambos casos.

        Args:
            email: Correo escrito en el formulario.
            password: Contraseña escrita en el formulario.

        Returns:
            Usuario: El usuario autenticado (también queda en
            ``usuario_actual``).

        Raises:
            AuthError: Si faltan datos, las credenciales no son válidas,
                el usuario está inactivo o no hay acceso a la base de datos.
        """
        email = email.strip().lower()
        if not email or not password:
            raise AuthError("Ingrese su correo y su contraseña.")

        try:
            usuario = self._repositorio.obtener_por_email(email)
        except (DatabaseConnectionError, RepositoryError) as err:
            raise AuthError(f"No fue posible validar el acceso. {err}") from err

        hash_guardado = usuario.password_hash if usuario else _HASH_SENUELO
        password_valida = verify_password(password, hash_guardado)

        if usuario is None or not password_valida:
            raise AuthError(MENSAJE_CREDENCIALES_INVALIDAS)

        if not usuario.activo:
            raise AuthError("Su cuenta está desactivada. Contacte al administrador.")

        self.usuario_actual = usuario
        return usuario

    def cerrar_sesion(self) -> None:
        """Olvida al usuario de la sesión actual."""
        self.usuario_actual = None

    @property
    def hay_sesion(self) -> bool:
        """Indica si hay un usuario autenticado."""
        return self.usuario_actual is not None

    def cambiar_password(
        self,
        password_actual: str,
        password_nueva: str,
        confirmacion: Optional[str] = None,
    ) -> None:
        """
        Cambia la contraseña del usuario que tiene la sesión abierta.

        Args:
            password_actual: Contraseña vigente, para confirmar identidad.
            password_nueva: Contraseña nueva; debe cumplir la política
                de ``utils.security.validar_politica``.
            confirmacion: Si se indica, debe ser igual a ``password_nueva``.

        Raises:
            AuthError: Si no hay sesión, la contraseña actual es incorrecta,
                la nueva no cumple las reglas o falla la base de datos.
        """
        usuario = self.usuario_actual
        if usuario is None or usuario.id is None:
            raise AuthError("No hay una sesión activa.")
        if not verify_password(password_actual, usuario.password_hash):
            raise AuthError("La contraseña actual es incorrecta.")
        if password_actual == password_nueva:
            raise AuthError("La contraseña nueva debe ser distinta de la actual.")
        if confirmacion is not None and confirmacion != password_nueva:
            raise AuthError("La confirmación no coincide con la contraseña nueva.")

        try:
            nuevo_hash = hash_password(password_nueva)
            self._repositorio.actualizar_password(usuario.id, nuevo_hash)
        except PasswordError as err:
            raise AuthError(str(err)) from err
        except (DatabaseConnectionError, RepositoryError) as err:
            raise AuthError(f"No fue posible cambiar la contraseña. {err}") from err

        usuario.password_hash = nuevo_hash
