from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from config.database import get_db
from controllers import user_controller
from entities.user import User
from middleware.auth_middleware import get_current_user
from validations.user_validation import AvatarResponse, UpdateProfileRequest, UserResponse

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
    "/{username}",
    response_model=UserResponse,
    response_model_by_alias=True,
    summary="Ver el perfil publico de un artista",
)
def get_user_profile(
    username: str,
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_controller.get_user_profile(db, username)
