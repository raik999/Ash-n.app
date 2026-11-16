from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from entities.portfolio import COLORES, MAX_TITULO, Portfolio, portfolio_posts
from entities.post import Post
from entities.user import User
from middleware.error_middleware import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from services.post_service import puede_ver_publicacion

def _get_or_404(db: Session, portfolio_id: int) -> Portfolio:
    portafolio = db.get(Portfolio, portfolio_id)
    if portafolio is None:
        raise NotFoundError("Ese portafolio no existe")
    return portafolio

def puede_ver(portafolio: Portfolio, viewer: User | None) -> bool:
    if viewer is not None and viewer.id == portafolio.user_id:
        return True
    if viewer is not None and viewer.is_admin:
        return True
    return not portafolio.is_private

def _require_owner(portafolio: Portfolio, user: User) -> None:
    if portafolio.user_id != user.id:
        raise ForbiddenError("Solo su autor puede modificar este portafolio")

def _limpiar_titulo(titulo: str) -> str:
    texto = (titulo or "").strip()
    if not texto:
        raise ValidationError("El portafolio necesita un titulo", field="title")
    if len(texto) > MAX_TITULO:
        raise ValidationError(
            f"El titulo no puede pasar de {MAX_TITULO} caracteres", field="title"
        )
    return texto

def _validar_color(color: str | None) -> str:
    if color is None:
        return COLORES[3]
    if color not in COLORES:
        raise ValidationError("Ese color no esta en la paleta", field="color")
    return color

def titulo_repetido(
    db: Session, user: User, titulo: str, excluir_id: int | None = None
) -> bool:
    texto = (titulo or "").strip().lower()
    if not texto:
        return False

    consulta = select(Portfolio.id).where(
        Portfolio.user_id == user.id,
        func.lower(func.trim(Portfolio.title)) == texto,
    )
    if excluir_id is not None:
        consulta = consulta.where(Portfolio.id != excluir_id)

    return db.scalar(consulta) is not None

def _exigir_que_tenga_publicaciones(db: Session, user: User) -> None:
    tiene = db.scalar(
        select(Post.id).where(Post.user_id == user.id, Post.published.is_(True)).limit(1)
    )
    if tiene is None:
        raise ValidationError(
            "Necesitas al menos una publicacion para crear un portafolio"
        )

def create_portfolio(
    db: Session,
    user: User,
    titulo: str,
    descripcion: str | None,
    color: str | None,
    privado: bool,
) -> Portfolio:
    _exigir_que_tenga_publicaciones(db, user)

    portafolio = Portfolio(
        user_id=user.id,
        title=_limpiar_titulo(titulo),
        description=(descripcion or "").strip() or None,
        color=_validar_color(color),
        is_private=bool(privado),
    )

    db.add(portafolio)
    db.commit()
    db.refresh(portafolio)
    return portafolio

def update_portfolio(
    db: Session,
    user: User,
    portfolio_id: int,
    titulo: str | None = None,
    descripcion: str | None = None,
    color: str | None = None,
    privado: bool | None = None,
) -> Portfolio:
    portafolio = _get_or_404(db, portfolio_id)
    _require_owner(portafolio, user)

    if titulo is not None:
        portafolio.title = _limpiar_titulo(titulo)

    if descripcion is not None:
        portafolio.description = descripcion.strip() or None

    if color is not None:
        portafolio.color = _validar_color(color)

    if privado is not None:
        portafolio.is_private = bool(privado)

    db.commit()
    db.refresh(portafolio)
    return portafolio

def delete_portfolio(db: Session, user: User, portfolio_id: int) -> None:
    portafolio = _get_or_404(db, portfolio_id)
    _require_owner(portafolio, user)

    db.delete(portafolio)
    db.commit()

def get_portfolio(db: Session, portfolio_id: int, viewer: User | None) -> Portfolio:
    portafolio = _get_or_404(db, portfolio_id)

    if not puede_ver(portafolio, viewer):
        raise NotFoundError("Ese portafolio no existe")

    return portafolio

def list_portfolios(db: Session, owner: User, viewer: User | None) -> list[Portfolio]:
    consulta = select(Portfolio).where(Portfolio.user_id == owner.id)

    es_el_dueno = viewer is not None and viewer.id == owner.id
    es_admin = viewer is not None and viewer.is_admin

    if not es_el_dueno and not es_admin:
        consulta = consulta.where(Portfolio.is_private.is_(False))

    return list(db.scalars(consulta.order_by(Portfolio.id.desc())).all())

def list_posts(
    db: Session, portafolio: Portfolio, viewer: User | None
) -> list[Post]:
    return [p for p in portafolio.posts if puede_ver_publicacion(p, viewer)]

def contar_publicaciones(
    db: Session, portafolios: list[Portfolio], viewer: User | None
) -> dict[int, int]:
    return {
        p.id: sum(1 for post in p.posts if puede_ver_publicacion(post, viewer))
        for p in portafolios
    }

def _mis_publicaciones(db: Session, user: User, post_ids: list[int]) -> list[Post]:
    if not post_ids:
        return []

    encontradas = list(
        db.scalars(
            select(Post).where(Post.id.in_(set(post_ids)), Post.user_id == user.id)
        ).all()
    )

    if len(encontradas) != len(set(post_ids)):
        raise ValidationError("Alguna de esas publicaciones no es tuya")

    return encontradas

def set_posts(
    db: Session, user: User, portfolio_id: int, post_ids: list[int]
) -> Portfolio:
    portafolio = _get_or_404(db, portfolio_id)
    _require_owner(portafolio, user)

    portafolio.posts = _mis_publicaciones(db, user, post_ids)

    db.commit()
    db.refresh(portafolio)
    return portafolio

def add_post(db: Session, user: User, portfolio_id: int, post_id: int) -> Portfolio:
    portafolio = _get_or_404(db, portfolio_id)
    _require_owner(portafolio, user)

    publicacion = _mis_publicaciones(db, user, [post_id])[0]

    if publicacion not in portafolio.posts:
        portafolio.posts.append(publicacion)
        db.commit()
        db.refresh(portafolio)

    return portafolio

def remove_post(db: Session, user: User, portfolio_id: int, post_id: int) -> Portfolio:
    portafolio = _get_or_404(db, portfolio_id)
    _require_owner(portafolio, user)

    publicacion = db.get(Post, post_id)
    if publicacion is not None and publicacion in portafolio.posts:
        portafolio.posts.remove(publicacion)
        db.commit()
        db.refresh(portafolio)

    return portafolio

def portafolios_con(db: Session, user: User, post_id: int) -> set[int]:
    return set(
        db.scalars(
            select(portfolio_posts.c.portfolio_id)
            .join(Portfolio, Portfolio.id == portfolio_posts.c.portfolio_id)
            .where(
                portfolio_posts.c.post_id == post_id,
                Portfolio.user_id == user.id,
            )
        ).all()
    )
