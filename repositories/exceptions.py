"""
Excepciones de la capa de persistencia.

Los repositorios traducen los errores de ``mysql.connector`` a estas
excepciones. Así, los controladores no necesitan conocer los códigos
numéricos de MySQL: les basta con saber si el problema fue un dato
duplicado, una referencia inválida o un fallo general.
"""


class RepositoryError(Exception):
    """Error general al ejecutar una operación en la base de datos."""


class DuplicateEntryError(RepositoryError):
    """Se violó una restricción UNIQUE (por ejemplo, un email repetido)."""


class ForeignKeyError(RepositoryError):
    """Se referenció un registro inexistente o se intentó borrar uno en uso."""
