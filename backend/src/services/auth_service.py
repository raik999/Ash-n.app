from __future__ import annotations
from sqlalchemy.orm import Session
from entities.user import User
from services import user_service
from services.security_service import create_access_token, get_token_expiration_seconds
from validations.auth_validation import RegisterRequest, TokenResponse
from validations.user_validation import UserResponse


def _build_token_response(user: User) -> TokenResponse:
    token = create_access_token(
        user_id=user.id,
        extra_claims={"role": user.role.value, "username": user.username},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=get_token_expiration_seconds(),
        user=UserResponse.model_validate(user).model_dump(by_alias=True, mode="json"),
    )


def register(db: Session, data: RegisterRequest) -> TokenResponse:
    user = user_service.create_user(db, data)
    return _build_token_response(user)


def login(db: Session, identifier: str, password: str) -> TokenResponse:
    user = user_service.authenticate(db, identifier, password)
    return _build_token_response(user)
