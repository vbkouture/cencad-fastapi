"""Security utilities for password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to include in the token (e.g., {'sub': user_id, 'role': 'admin'})
        expires_delta: Token expiration time. If None, uses settings default.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode.

    Returns:
        Token claims as a dictionary, or None if token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.

    Returns:
        A 32-character hexadecimal token.
    """
    import secrets

    return secrets.token_hex(32)


def create_reset_token_expiry(hours: int = 1) -> datetime:
    """
    Calculate expiration time for password reset token.

    Args:
        hours: Number of hours until token expires (default: 1)

    Returns:
        Expiration datetime in UTC.
    """
    return datetime.now(UTC) + timedelta(hours=hours)
