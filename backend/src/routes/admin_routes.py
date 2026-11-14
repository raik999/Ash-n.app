from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from entities.user import User
from middleware.auth_middleware import get_current_user, require_admin
from services import admin_service, email_service
from validations.admin_validation import SancionRequest, SancionResponse
from validations.auth_validation import MessageResponse

router = APIRouter(
    prefix="/api/admin",
    tags=["Administracion"],
    dependencies=[Depends(require_admin)],
)

@router.post(
    "/users/{username}/sancion",
    response_model=SancionResponse,
    summary="Suspender una cuenta por unos dias",
)
def sancionar(
    username: str,
    payload: SancionRequest,
    tareas: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SancionResponse:
    objetivo, (asunto, cuerpo) = admin_service.sancionar(
        db, current_user, username, payload.dias, payload.motivo
    )

    tareas.add_task(email_service.enviar, [objetivo.email], asunto, cuerpo)

    return SancionResponse(
        username=objetivo.username,
        banned_until=objetivo.banned_until,
        banned_reason=objetivo.banned_reason,
        dias_restantes=objetivo.dias_de_sancion_restantes,
    )

@router.delete(
    "/users/{username}/sancion",
    response_model=SancionResponse,
    summary="Levantar la suspension de una cuenta",
)
def levantar_sancion(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SancionResponse:
    objetivo = admin_service.levantar_sancion(db, current_user, username)

    return SancionResponse(
        username=objetivo.username,
        banned_until=None,
        banned_reason=None,
        dias_restantes=0,
    )

@router.delete(
    "/users/{username}",
    response_model=MessageResponse,
    summary="Eliminar una cuenta definitivamente",
)
def eliminar_cuenta(
    username: str,
    tareas: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    destino, (asunto, cuerpo) = admin_service.eliminar_cuenta(
        db, current_user, username
    )

    tareas.add_task(email_service.enviar, [destino], asunto, cuerpo)

    return MessageResponse(detail="Cuenta eliminada")
