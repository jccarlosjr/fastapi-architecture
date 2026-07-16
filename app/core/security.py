import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import structlog
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerifyMismatchError

from .config import settings

logger = structlog.get_logger("app.security")

password_hasher = PasswordHasher(
    time_cost=2,        # tiempo de ejecucion
    memory_cost=65536,  # uso de ram
    parallelism=2,       # uso de nucleos
    hash_len=32,        # longitud del hash
    salt_len=16,        # longitud de la sal
)


def hash_password(password: str) -> str:
    """
    Generate a hash Argon2id from a plain text password.
    
    Args:
        password: The password to hash.

    Returns:
        The hashed password.
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: The password to verify.
        hashed_password: The hashed password to verify against.

    Returns:
        True if the password is correct, False otherwise.
    """
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, HashingError) as e:
        logger.error("argon2_hash_error", error=str(e))
        return False


def create_access_token(subject: str, role: str) -> str:
    """
    Create a short duration JWT access token.

    Args:
        subject: The subject of the token.
        role: The role of the subject.

    Returns:
        The access token.
    """
    expire = datetime.now(UTC) + timedelta (
        minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": expire
    }
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode an access token.
    
    Args:
        token: The access token to decode.

    Returns:
        The decoded token.
    """
    from app.core.exceptions import AuthenticationError

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError("Access token has expired") from e
    except jwt.PyJWTError as e:
        raise AuthenticationError("Invalid access token") from e
