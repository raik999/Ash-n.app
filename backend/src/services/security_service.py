from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from config.settings import settings
from middleware.error_middleware import UnauthorizedError


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_expiration_minutes)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Tu sesion expiro, vuelve a iniciar sesion") from None
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Token invalido") from None


def get_token_expiration_seconds() -> int:
    return settings.jwt_expiration_minutes * 60
