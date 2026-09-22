from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config.database import get_db
from entities.user import User, UserRole
from middleware.error_middleware import ForbiddenError, UnauthorizedError
from services.security_service import decode_access_token
from services.user_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False, description="Token JWT de Ashun")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Falta el token de autenticacion")

    payload = decode_access_token(credentials.credentials)

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise UnauthorizedError("Token malformado")

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise UnauthorizedError("Token malformado") from None

    user = get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("El usuario del token ya no existe")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials=credentials, db=db)
    except UnauthorizedError:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Esta accion es solo para administradores")
    return current_user
