from __future__ import annotations
from sqlalchemy.orm import Session
from entities.user import User
from middleware.error_middleware import NotFoundError
from services import storage_service, user_service
from validations.auth_validation import MessageResponse
from validations.user_validation import (
    AvatarResponse,
    PublicUserResponse,
    UpdateProfileRequest,
    UserResponse,
    UserSummaryResponse,
)


def update_my_profile(
    db: Session, current_user: User, payload: UpdateProfileRequest
) -> UserResponse:
    user = user_service.update_profile(db, current_user, payload)
    return UserResponse.model_validate(user)


def upload_my_avatar(
    db: Session,
    current_user: User,
    filename: str,
    content_type: str,
    content: bytes,
) -> AvatarResponse:
    avatar_url = storage_service.save_avatar(
        user_id=current_user.id,
        filename=filename,
        content_type=content_type,
        content=content,
    )
    user_service.set_avatar(db, current_user, avatar_url)
    return AvatarResponse(avatar_url=avatar_url)


def delete_my_avatar(db: Session, current_user: User) -> UserResponse:
    if current_user.avatar_url:
        storage_service.delete_avatar(current_user.avatar_url)
    current_user.avatar_url = None
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


def change_my_password(
    db: Session, current_user: User, current_password: str, new_password: str
) -> MessageResponse:
    user_service.change_password(db, current_user, current_password, new_password)
    return MessageResponse(detail="Contrasena actualizada correctamente")


def delete_my_account(db: Session, current_user: User, password: str) -> MessageResponse:
    user_service.delete_account(db, current_user, password)
    return MessageResponse(detail="Cuenta eliminada")


def search_users(db: Session, query: str, limit: int = 20) -> list[UserSummaryResponse]:
    users = user_service.search_users(db, query, limit)
    return [UserSummaryResponse.model_validate(user) for user in users]


def get_user_profile(db: Session, username: str) -> PublicUserResponse:
    user = user_service.get_user_by_username(db, username)
    if user is None:
        raise NotFoundError(f"No existe el usuario @{username}")
    return PublicUserResponse.model_validate(user)
