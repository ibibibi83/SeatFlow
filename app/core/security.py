"""
Security utilities: password hashing and JWT token management.

Password hashing uses bcrypt directly (no passlib dependency).
Tokens are signed JWTs (HS256) with a configurable expiry.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenException, TokenExpiredException


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* password."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str | Any, extra_claims: dict | None = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:      Value stored in the 'sub' claim (typically the user id).
        extra_claims: Optional additional claims merged into the payload.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": str(subject), "iat": now, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Raises:
        TokenExpiredException:  If the token's 'exp' claim is in the past.
        InvalidTokenException:  If the token cannot be decoded or the signature is invalid.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except JWTError:
        raise InvalidTokenException()