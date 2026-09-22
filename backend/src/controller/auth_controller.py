from __future__ import annotations

from sqlalchemy.orm import Session

from entities.user import User
from services import auth_service
from validations.auth_validation import LoginRequest, RegisterRequest, TokenResponse
from validations.user_validation import UserResponse


def register(db: Session, payload: RegisterRequest) -> TokenResponse:
    return auth_service.register(db, payload)


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    return auth_service.login(db, payload.identifier, payload.password)


def get_me(current_user: User) -> UserResponse:
    return UserResponse.model_validate(current_user)
