from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from config.database import get_db
from entities.user import User
from middleware.auth_middleware import get_current_user
from middleware.error_middleware import NotFoundError
from services import admin_service, email_service, report_service
from validations.admin_validation import (
    EstadoDeReporte,
    ReportRequest,
    ReportResponse,
)

router = APIRouter(prefix="/api/reports", tags=["Reportes"])

def _avisar_a_los_admins(
    db: Session, tareas: BackgroundTasks, asunto: str, cuerpo: str
) -> None:
    destinos = admin_service.correos_de_admins(db)
    if destinos:
        tareas.add_task(email_service.enviar, destinos, asunto, cuerpo)

@router.post(
    "/posts/{post_id}",
    response_model=ReportResponse,
    status_code=201,
    summary="Reportar una publicacion",
)
def reportar_publicacion(
    post_id: int,
    payload: ReportRequest,
    tareas: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    reporte, (asunto, cuerpo) = report_service.reportar_publicacion(
        db, current_user, post_id, payload.motivo
    )

    _avisar_a_los_admins(db, tareas, asunto, cuerpo)

    return ReportResponse.model_validate(reporte)

@router.post(
    "/users/{username}",
    response_model=ReportResponse,
    status_code=201,
    summary="Reportar una cuenta",
)
def reportar_usuario(
    username: str,
    payload: ReportRequest,
    tareas: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    reporte, (asunto, cuerpo) = report_service.reportar_usuario(
        db, current_user, username, payload.motivo
    )

    _avisar_a_los_admins(db, tareas, asunto, cuerpo)

    return ReportResponse.model_validate(reporte)

@router.get(
    "/posts/{post_id}",
    response_model=EstadoDeReporte,
    summary="Si ya reporte esta publicacion",
)
def estado_de_publicacion(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EstadoDeReporte:
    return EstadoDeReporte(
        ya_reportado=report_service.ya_reporto_publicacion(db, current_user, post_id)
    )

@router.get(
    "/users/{username}",
    response_model=EstadoDeReporte,
    summary="Si ya reporte esta cuenta",
)
def estado_de_usuario(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EstadoDeReporte:
    objetivo = db.scalar(select(User).where(User.username == username.lower().strip()))
    if objetivo is None:
        raise NotFoundError("Ese usuario no existe")

    return EstadoDeReporte(
        ya_reportado=report_service.ya_reporto_usuario(db, current_user, objetivo.id)
    )
