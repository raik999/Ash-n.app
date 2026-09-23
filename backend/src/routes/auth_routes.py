from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from config.database import get_db
from controller import auth_controller
from entities.user import User
from middleware.auth_middleware import get_current_user
from validations.auth_validation import LoginRequest, RegisterRequest, TokenResponse
from validations.user_validation import UserResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario nuevo",
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_controller.register(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_controller.login(db, payload)


@router.get(
    "/me",
    response_model=UserResponse,
    response_model_by_alias=True,
    summary="Datos del usuario de la sesion actual",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return auth_controller.get_me(current_user)
