from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session
from config.database import get_db
from controller import user_controller
from entities.user import User
from middleware.auth_middleware import get_current_user
from validations.auth_validation import MessageResponse
from validations.user_validation import (
    AvatarResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    PublicUserResponse,
    UpdateProfileRequest,
    UserResponse,
    UserSummaryResponse,
)

router = APIRouter(prefix="/api/users", tags=["Usuarios"])


@router.patch(
    "/me",
    response_model=UserResponse,
    response_model_by_alias=True,
    summary="Actualizar mi perfil",
)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_controller.update_my_profile(db, current_user, payload)


@router.post(
    "/me/avatar",
    response_model=AvatarResponse,
    summary="Subir mi foto de perfil",
)
async def upload_my_avatar(
    file: UploadFile = File(..., description="Imagen JPG, PNG, WEBP o GIF"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarResponse:
    content = await file.read()

    return user_controller.upload_my_avatar(
        db=db,
        current_user=current_user,
        filename=file.filename or "avatar",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )


@router.patch(
    "/me/password",
    response_model=MessageResponse,
    summary="Cambiar mi contrasena",
)
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return user_controller.change_my_password(
        db, current_user, payload.current_password, payload.new_password
    )


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Eliminar mi cuenta (irreversible)",
)
def delete_my_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return user_controller.delete_my_account(db, current_user, payload.password)


@router.delete(
    "/me/avatar",
    response_model=UserResponse,
    response_model_by_alias=True,
    summary="Quitar mi foto de perfil",
)
def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_controller.delete_my_avatar(db, current_user)


@router.get(
    "",
    response_model=list[UserSummaryResponse],
    summary="Buscar artistas por nombre de usuario",
)
def search_users(
    q: str = Query(default="", max_length=30, description="Inicio del nombre de usuario"),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserSummaryResponse]:
    return user_controller.search_users(db, q, limit)


@router.get(
    "/{username}",
    response_model=PublicUserResponse,
    response_model_by_alias=True,
    summary="Ver el perfil publico de un artista",
)
def get_user_profile(
    username: str,
    db: Session = Depends(get_db),
) -> PublicUserResponse:
    return user_controller.get_user_profile(db, username)
