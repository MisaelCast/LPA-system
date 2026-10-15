"""JWT token generation and validation utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.config import settings


TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    """Generate a signed JWT for the given subject and type."""
    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str, expires_delta: timedelta | None = None
) -> str:
    """Generate a signed JWT access token for the given subject.

    Args:
        subject: Identifier to store in the ``sub`` claim.
        expires_delta: Optional custom expiration offset. Falls back to
            ``ACCESS_TOKEN_EXPIRE_MINUTES`` when not provided.

    Returns:
        Encoded JWT string.
    """
    delta = expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return _create_token(subject, "access", delta)


def create_refresh_token(subject: str) -> str:
    """Generate a long-lived JWT refresh token for the given subject."""
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The encoded JWT string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token signature is invalid or the
            token cannot be parsed.
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT refresh token.

    Raises ``InvalidTokenError`` if the token is not a refresh token or is
    otherwise invalid.
    """
    payload = decode_access_token(token)
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("El token no es de tipo refresh.")
    return payload
