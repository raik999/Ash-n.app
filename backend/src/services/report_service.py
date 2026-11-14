from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from entities.post import Post
from entities.report import MAX_MOTIVO, TIPO_PUBLICACION, TIPO_USUARIO, Report
from entities.user import User
from middleware.error_middleware import ForbiddenError, NotFoundError, ValidationError
from services import email_service

def _limpiar_motivo(motivo: str | None) -> str | None:
    texto = (motivo or "").strip()
    if not texto:
        return None
    if len(texto) > MAX_MOTIVO:
        raise ValidationError(
            f"El motivo no puede pasar de {MAX_MOTIVO} caracteres", field="motivo"
        )
    return texto

def _guardar(db: Session, reporte: Report) -> Report:
    db.add(reporte)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValidationError("Ya reportaste esto antes") from None

    db.refresh(reporte)
    return reporte

def reportar_publicacion(
    db: Session, usuario: User, post_id: int, motivo: str | None
) -> tuple[Report, tuple[str, str]]:
    publicacion = db.get(Post, post_id)
    if publicacion is None:
        raise NotFoundError("Esa publicacion no existe")

    if publicacion.user_id == usuario.id:
        raise ForbiddenError("No puedes reportar tu propia publicacion")

    reporte = _guardar(
        db,
        Report(
            reporter_id=usuario.id,
            kind=TIPO_PUBLICACION,
            post_id=publicacion.id,
            motivo=_limpiar_motivo(motivo),
        ),
    )

    referencia = (publicacion.title or publicacion.description or "").strip()
    if len(referencia) > 120:
        referencia = referencia[:117] + "..."

    correo = email_service.aviso_de_reporte(
        quien_reporta=usuario.username,
        que_es="una publicacion",
        detalle=(
            f"Publicacion #{publicacion.id} de @{publicacion.author.username}\n"
            f'Contenido: "{referencia}"'
            if referencia
            else f"Publicacion #{publicacion.id} de @{publicacion.author.username}"
        ),
        motivo=reporte.motivo,
    )

    return reporte, correo

def reportar_usuario(
    db: Session, usuario: User, username: str, motivo: str | None
) -> tuple[Report, tuple[str, str]]:
    objetivo = db.scalar(select(User).where(User.username == username.lower().strip()))
    if objetivo is None:
        raise NotFoundError("Ese usuario no existe")

    if objetivo.id == usuario.id:
        raise ForbiddenError("No puedes reportarte a ti mismo")

    reporte = _guardar(
        db,
        Report(
            reporter_id=usuario.id,
            kind=TIPO_USUARIO,
            target_user_id=objetivo.id,
            motivo=_limpiar_motivo(motivo),
        ),
    )

    correo = email_service.aviso_de_reporte(
        quien_reporta=usuario.username,
        que_es="una cuenta",
        detalle=f"Cuenta reportada: @{objetivo.username} ({objetivo.name})",
        motivo=reporte.motivo,
    )

    return reporte, correo

def ya_reporto_publicacion(db: Session, usuario: User, post_id: int) -> bool:
    return (
        db.scalar(
            select(Report.id).where(
                Report.reporter_id == usuario.id, Report.post_id == post_id
            )
        )
        is not None
    )

def ya_reporto_usuario(db: Session, usuario: User, target_id: int) -> bool:
    return (
        db.scalar(
            select(Report.id).where(
                Report.reporter_id == usuario.id, Report.target_user_id == target_id
            )
        )
        is not None
    )
