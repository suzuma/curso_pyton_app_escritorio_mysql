"""
Excepciones de la capa de controladores.

Son las únicas excepciones que las vistas necesitan capturar. Su mensaje
está redactado para mostrarse directamente al usuario.
"""

from typing import Optional


class ControllerError(Exception):
    """Error de una operación de negocio, con mensaje apto para la interfaz."""


class PermisoDenegadoError(ControllerError):
    """El usuario de la sesión no tiene autorización para la operación."""


class ValidationError(ControllerError):
    """
    Un dato del formulario no cumple las reglas de negocio.

    Attributes:
        campo: Nombre del campo con el problema (por ejemplo, ``"nombre"``).
            Permite a la vista resaltar o enfocar ese control.
    """

    def __init__(self, mensaje: str, campo: Optional[str] = None) -> None:
        super().__init__(mensaje)
        self.campo = campo
