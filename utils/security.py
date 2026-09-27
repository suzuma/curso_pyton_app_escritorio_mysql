"""
Utilidades de seguridad: hash y verificación de contraseñas con bcrypt.

bcrypt es una función de derivación de claves diseñada para ser lenta a
propósito. Cada hash incluye una "sal" aleatoria y un factor de costo
(``rounds``), de modo que dos contraseñas iguales producen hashes distintos
y un ataque de fuerza bruta resulta costoso.

Formato de un hash bcrypt (60 caracteres)::

    $2b$12$<22 caracteres de sal><31 caracteres de hash>
     |   |
     |   +-- factor de costo: 2^12 iteraciones
     +------ versión del algoritmo

La base de datos solo almacena este hash (columna ``usuarios.password_hash``);
la contraseña en texto plano nunca se guarda.
"""

from __future__ import annotations

import bcrypt

BCRYPT_ROUNDS: int = 12
BCRYPT_MAX_BYTES: int = 72  # bcrypt solo procesa los primeros 72 bytes
MIN_PASSWORD_LENGTH: int = 8


class PasswordError(ValueError):
    """Se lanza cuando una contraseña no cumple las reglas para ser hasheada."""


def _a_bytes(password: str) -> bytes:
    """
    Convierte la contraseña a bytes UTF-8 y valida su longitud.

    Args:
        password: Contraseña en texto plano.

    Returns:
        bytes: Contraseña codificada en UTF-8.

    Raises:
        PasswordError: Si la contraseña está vacía o excede 72 bytes.
    """
    if not password:
        raise PasswordError("La contraseña no puede estar vacía.")
    datos = password.encode("utf-8")
    if len(datos) > BCRYPT_MAX_BYTES:
        # Una "ñ" o una vocal acentuada ocupan 2 bytes en UTF-8.
        raise PasswordError(
            f"La contraseña excede el límite de {BCRYPT_MAX_BYTES} bytes de bcrypt."
        )
    return datos


def validar_politica(password: str) -> None:
    """
    Comprueba la política mínima de contraseñas del sistema.

    Reglas: al menos ``MIN_PASSWORD_LENGTH`` caracteres, al menos una letra
    y al menos un número. Se valida antes de hashear porque, una vez guardado
    el hash, ya no es posible saber cómo era la contraseña original.

    Args:
        password: Contraseña en texto plano.

    Raises:
        PasswordError: Con un mensaje que indica la regla incumplida.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise PasswordError("La contraseña debe combinar letras y números.")
    _a_bytes(password)  # también valida el límite de 72 bytes


def hash_password(password: str) -> str:
    """
    Genera el hash bcrypt de una contraseña.

    Args:
        password: Contraseña en texto plano.

    Returns:
        str: Hash de 60 caracteres, listo para guardarse en ``password_hash``.

    Raises:
        PasswordError: Si la contraseña no cumple la política
            (ver ``validar_politica``) o excede 72 bytes.
    """
    validar_politica(password)
    sal = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(_a_bytes(password), sal).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Comprueba si una contraseña corresponde a un hash bcrypt almacenado.

    bcrypt extrae la sal y el costo del propio hash, por lo que no es
    necesario guardarlos por separado.

    Args:
        password: Contraseña escrita por el usuario en el formulario de login.
        password_hash: Hash leído de la base de datos.

    Returns:
        bool: ``True`` si coinciden; ``False`` si no coinciden o si el hash
        almacenado está mal formado.
    """
    try:
        return bcrypt.checkpw(_a_bytes(password), password_hash.encode("utf-8"))
    except (PasswordError, ValueError):
        # ValueError: el hash guardado no tiene formato bcrypt válido.
        return False


if __name__ == "__main__":
    # Generador de hashes para datos semilla:  python -m utils.security
    from getpass import getpass

    texto = getpass("Contraseña a hashear: ")
    try:
        print(hash_password(texto))
    except PasswordError as err:
        print(f"[ERROR] {err}")
