"""
Entidad de dominio ``Usuario``.

Representa un registro de la tabla ``usuarios``. Guarda únicamente el hash
de la contraseña; generar y verificar ese hash es tarea de
``utils.security``, que invocarán los controladores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from models.rol import Rol


@dataclass
class Usuario:
    """
    Usuario que puede iniciar sesión en la aplicación.

    Attributes:
        rol_id: Clave foránea hacia ``roles.id``.
        nombre: Nombre completo (máx. 100 caracteres).
        email: Correo único que funciona como nombre de acceso.
        password_hash: Hash bcrypt de la contraseña. Se excluye de ``repr``
            para que no aparezca en logs ni en mensajes de depuración.
        activo: Si es ``False``, el usuario no puede iniciar sesión.
        id: Clave primaria. Es ``None`` mientras no se ha insertado.
        created_at: Fecha de creación asignada por MySQL.
        rol: Objeto ``Rol`` completo, disponible cuando el repositorio
            hace un ``JOIN`` con la tabla ``roles``.
    """

    rol_id: int
    nombre: str
    email: str
    password_hash: str = field(default="", repr=False)
    activo: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    rol: Optional[Rol] = None

    @classmethod
    def from_row(cls, fila: dict[str, Any]) -> Usuario:
        """
        Construye un ``Usuario`` a partir de una fila de MySQL.

        Si la consulta incluyó las columnas ``rol_nombre`` (y opcionalmente
        ``rol_descripcion``) mediante un ``JOIN``, también se arma el objeto
        ``Rol`` asociado.

        Args:
            fila: Diccionario con las columnas de la tabla ``usuarios``.

        Returns:
            Usuario: Instancia con los datos de la fila.
        """
        rol: Optional[Rol] = None
        if fila.get("rol_nombre") is not None:
            rol = Rol(
                id=fila["rol_id"],
                nombre=fila["rol_nombre"],
                descripcion=fila.get("rol_descripcion"),
            )

        return cls(
            id=fila.get("id"),
            rol_id=fila["rol_id"],
            nombre=fila["nombre"],
            email=fila["email"],
            password_hash=fila.get("password_hash", ""),
            # MySQL guarda BOOLEAN como TINYINT(1): llega como 0 o 1.
            activo=bool(fila.get("activo", True)),
            created_at=fila.get("created_at"),
            rol=rol,
        )

    @property
    def es_administrador(self) -> bool:
        """Indica si el usuario tiene el rol "Administrador"."""
        return self.rol is not None and self.rol.nombre == "Administrador"
