from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from entities.user import User, UserRole
from middleware.error_middleware import ForbiddenError, NotFoundError, ValidationError
from services import email_service

MIN_DIAS_SANCION = 1
MAX_DIAS_SANCION = 365

def _buscar_usuario(db: Session, username: str) -> User:
    usuario = db.scalar(select(User).where(User.username == username.lower().strip()))
    if usuario is None:
        raise NotFoundError("Ese usuario no existe")
    return usuario

def _exigir_que_se_pueda_moderar(admin: User, objetivo: User) -> None:
    if objetivo.id == admin.id:
        raise ForbiddenError("No puedes aplicarte esta accion a ti mismo")

    if objetivo.role == UserRole.ADMIN:
        raise ForbiddenError("No puedes aplicar esta accion a otro administrador")

def _formatear(momento: datetime) -> str:
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    return f"{momento.day} de {meses[momento.month - 1]} de {momento.year}"

def sancionar(
    db: Session,
    admin: User,
    username: str,
    dias: int,
    motivo: str | None,
) -> tuple[User, tuple[str, str]]:
    if dias < MIN_DIAS_SANCION or dias > MAX_DIAS_SANCION:
        raise ValidationError(
            f"La sancion tiene que ser de entre {MIN_DIAS_SANCION} y "
            f"{MAX_DIAS_SANCION} dias",
            field="dias",
        )

    objetivo = _buscar_usuario(db, username)
    _exigir_que_se_pueda_moderar(admin, objetivo)

    motivo_limpio = (motivo or "").strip() or None

    objetivo.banned_until = datetime.now(timezone.utc) + timedelta(days=dias)
    objetivo.banned_reason = motivo_limpio

    db.commit()
    db.refresh(objetivo)

    correo = email_service.aviso_de_sancion(
        nombre=objetivo.name,
        dias=dias,
        hasta=_formatear(objetivo.banned_until),
        motivo=motivo_limpio,
    )

    return objetivo, correo

def levantar_sancion(db: Session, admin: User, username: str) -> User:
    objetivo = _buscar_usuario(db, username)

    objetivo.banned_until = None
    objetivo.banned_reason = None

    db.commit()
    db.refresh(objetivo)
    return objetivo

def eliminar_cuenta(
    db: Session, admin: User, username: str
) -> tuple[str, tuple[str, str]]:
    objetivo = _buscar_usuario(db, username)
    _exigir_que_se_pueda_moderar(admin, objetivo)

    destino = objetivo.email
    correo = email_service.aviso_de_cuenta_eliminada(objetivo.name)

    if objetivo.avatar_url:
        from services import storage_service

        storage_service.delete_avatar(objetivo.avatar_url)

    db.delete(objetivo)
    db.commit()

    return destino, correo

def correos_de_admins(db: Session) -> list[str]:
    return list(
        db.scalars(select(User.email).where(User.role == UserRole.ADMIN)).all()
    )
