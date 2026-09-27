"""
Repositorio de la entidad ``Usuario``.

Contiene todas las sentencias SQL de la tabla ``usuarios``. Cada consulta
usa parámetros ``%s`` con una tupla de valores: el driver se encarga de
escaparlos, lo que impide la inyección SQL. Nunca se construye una
sentencia concatenando texto que venga del usuario.

La conexión, la confirmación de transacciones y la traducción de errores
las hereda de ``BaseRepository``.
"""

from __future__ import annotations

from typing import Any, Optional

from mysql.connector import errorcode

from models.usuario import Usuario
from repositories.base_repository import BaseRepository

# Consulta base: trae el usuario junto con el nombre de su rol.
_SELECT_BASE: str = """
    SELECT u.id, u.rol_id, u.nombre, u.email, u.password_hash,
           u.activo, u.created_at,
           r.nombre AS rol_nombre, r.descripcion AS rol_descripcion
    FROM usuarios AS u
    INNER JOIN roles AS r ON r.id = u.rol_id
"""


class UsuarioRepository(BaseRepository[Usuario]):
    """Acceso a datos de la tabla ``usuarios``."""

    NOMBRE_TABLA = "usuarios"
    MENSAJES_ERROR = {
        errorcode.ER_DUP_ENTRY: "El correo electrónico ya está registrado.",
        errorcode.ER_NO_REFERENCED_ROW_2: "El rol seleccionado no existe.",
        errorcode.ER_ROW_IS_REFERENCED_2: "El usuario tiene registros asociados.",
    }

    # ------------------------------------------------------------------
    # Consultas (SELECT)
    # ------------------------------------------------------------------
    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """
        Busca un usuario por su clave primaria.

        Args:
            usuario_id: Identificador del usuario.

        Returns:
            Optional[Usuario]: El usuario encontrado o ``None``.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        fila = self._consultar_uno(_SELECT_BASE + " WHERE u.id = %s", (usuario_id,))
        return Usuario.from_row(fila) if fila else None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """
        Busca un usuario por su correo. Es la consulta que usa el login.

        La comparación no distingue mayúsculas porque la columna usa la
        intercalación ``utf8mb4_unicode_ci`` (*case insensitive*).

        Args:
            email: Correo a buscar.

        Returns:
            Optional[Usuario]: El usuario encontrado o ``None``.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        fila = self._consultar_uno(_SELECT_BASE + " WHERE u.email = %s", (email,))
        return Usuario.from_row(fila) if fila else None

    def listar(self, solo_activos: bool = False, texto: str = "") -> list[Usuario]:
        """
        Devuelve los usuarios ordenados por nombre.

        Args:
            solo_activos: Si es ``True``, omite los usuarios desactivados.
            texto: Coincidencia parcial en nombre o correo.

        Returns:
            list[Usuario]: Lista (posiblemente vacía) de usuarios.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        condiciones: list[str] = []
        parametros: list[Any] = []
        if solo_activos:
            condiciones.append("u.activo = %s")
            parametros.append(True)
        if texto:
            patron = f"%{self._escapar_like(texto)}%"
            condiciones.append("(u.nombre LIKE %s OR u.email LIKE %s)")
            parametros += [patron, patron]

        sql = _SELECT_BASE
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY u.nombre"
        return [Usuario.from_row(f) for f in self._consultar_todos(sql, tuple(parametros))]

    def contar_activos_por_rol(self, nombre_rol: str, excluir_id: Optional[int] = None) -> int:
        """
        Cuenta los usuarios activos que tienen un rol determinado.

        Se usa para no dejar el sistema sin administradores: antes de
        desactivar a uno o cambiarle el rol, el controlador verifica que
        quede al menos otro.

        Args:
            nombre_rol: Nombre del rol (p. ej. ``"Administrador"``).
            excluir_id: Id de un usuario que no debe contarse.

        Returns:
            int: Número de usuarios activos con ese rol.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = """
            SELECT COUNT(*) AS total
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id = u.rol_id
            WHERE r.nombre = %s AND u.activo = %s
        """
        parametros: list[Any] = [nombre_rol, True]
        if excluir_id is not None:
            sql += " AND u.id <> %s"
            parametros.append(excluir_id)
        fila = self._consultar_uno(sql, tuple(parametros))
        return int(fila["total"]) if fila else 0

    def existe_email(self, email: str, excluir_id: Optional[int] = None) -> bool:
        """
        Indica si un correo ya está registrado.

        Args:
            email: Correo a comprobar.
            excluir_id: Id a ignorar; sirve al editar un usuario para que
                su propio correo no cuente como duplicado.

        Returns:
            bool: ``True`` si otro usuario ya usa ese correo.

        Raises:
            RepositoryError: Si la consulta falla.
        """
        sql = "SELECT 1 FROM usuarios WHERE email = %s"
        parametros: tuple[Any, ...] = (email,)
        if excluir_id is not None:
            sql += " AND id <> %s"
            parametros = (email, excluir_id)
        return self._consultar_uno(sql + " LIMIT 1", parametros) is not None

    # ------------------------------------------------------------------
    # Escritura (INSERT / UPDATE / DELETE)
    # ------------------------------------------------------------------
    def crear(self, usuario: Usuario) -> int:
        """
        Inserta un usuario nuevo.

        El objeto debe traer ya el ``password_hash``; este repositorio no
        hashea contraseñas (eso es responsabilidad del controlador).

        Args:
            usuario: Usuario a insertar (su ``id`` se ignora).

        Returns:
            int: Id asignado por ``AUTO_INCREMENT``. También se guarda
            en ``usuario.id``.

        Raises:
            DuplicateEntryError: Si el email ya existe.
            ForeignKeyError: Si ``rol_id`` no corresponde a un rol.
            RepositoryError: Ante cualquier otro error.
        """
        sql = """
            INSERT INTO usuarios (rol_id, nombre, email, password_hash, activo)
            VALUES (%s, %s, %s, %s, %s)
        """
        usuario.id = self._insertar(
            sql,
            (
                usuario.rol_id,
                usuario.nombre,
                usuario.email,
                usuario.password_hash,
                usuario.activo,
            ),
        )
        return usuario.id

    def actualizar(self, usuario: Usuario) -> bool:
        """
        Actualiza rol, nombre, email y estado de un usuario.

        La contraseña no se modifica aquí; para eso existe
        ``actualizar_password``, lo que evita sobrescribir el hash por error.

        Args:
            usuario: Usuario con ``id`` y los datos nuevos.

        Returns:
            bool: ``True`` si existía un usuario con ese id.

        Raises:
            DuplicateEntryError: Si el nuevo email pertenece a otro usuario.
            ForeignKeyError: Si ``rol_id`` no corresponde a un rol.
            RepositoryError: Ante cualquier otro error.
        """
        sql = """
            UPDATE usuarios
            SET rol_id = %s, nombre = %s, email = %s, activo = %s
            WHERE id = %s
        """
        parametros = (
            usuario.rol_id,
            usuario.nombre,
            usuario.email,
            usuario.activo,
            usuario.id,
        )
        return self._ejecutar_escritura(sql, parametros) > 0

    def actualizar_password(self, usuario_id: int, password_hash: str) -> bool:
        """
        Reemplaza el hash de la contraseña de un usuario.

        Args:
            usuario_id: Id del usuario.
            password_hash: Hash bcrypt ya generado.

        Returns:
            bool: ``True`` si el usuario existía.

        Raises:
            RepositoryError: Si la sentencia falla.
        """
        sql = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
        return self._ejecutar_escritura(sql, (password_hash, usuario_id)) > 0

    def cambiar_estado(self, usuario_id: int, activo: bool) -> bool:
        """
        Activa o desactiva un usuario (baja lógica).

        Desactivar es preferible a borrar: conserva el historial y se
        puede revertir.

        Args:
            usuario_id: Id del usuario.
            activo: Nuevo estado.

        Returns:
            bool: ``True`` si el usuario existía.

        Raises:
            RepositoryError: Si la sentencia falla.
        """
        sql = "UPDATE usuarios SET activo = %s WHERE id = %s"
        return self._ejecutar_escritura(sql, (activo, usuario_id)) > 0

    def eliminar(self, usuario_id: int) -> bool:
        """
        Borra físicamente un usuario.

        Args:
            usuario_id: Id del usuario.

        Returns:
            bool: ``True`` si se borró un registro.

        Raises:
            ForeignKeyError: Si otra tabla hace referencia al usuario.
            RepositoryError: Ante cualquier otro error.
        """
        sql = "DELETE FROM usuarios WHERE id = %s"
        return self._ejecutar_escritura(sql, (usuario_id,)) > 0
