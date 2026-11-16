from __future__ import annotations

from sqlalchemy.orm import Session

from entities.portfolio import Portfolio
from entities.post import Post
from entities.user import User
from middleware.error_middleware import NotFoundError
from services import portfolio_service, post_service, user_service
from validations.portfolio_validation import (
    PortfolioResponse,
    PortfolioSummaryResponse,
    TituloRepetidoResponse,
)
from validations.post_validation import PostFileResponse, PostSummaryResponse

def _resumen_de_publicacion(post: Post, likes: int, comments: int) -> PostSummaryResponse:
    return PostSummaryResponse(
        id=post.id,
        title=post.title,
        description=post.description,
        preview=PostFileResponse.model_validate(post.files[0]) if post.files else None,
        files_count=len(post.files),
        likes_count=likes,
        comments_count=comments,
        is_private=post.is_private,
        published=post.published,
    )

def _preview_de(posts: list[Post]) -> PostFileResponse | None:
    for post in posts:
        if post.files:
            return PostFileResponse.model_validate(post.files[0])
    return None

def _resumen(
    db: Session, portafolio: Portfolio, viewer: User | None
) -> PortfolioSummaryResponse:
    visibles = portfolio_service.list_posts(db, portafolio, viewer)

    return PortfolioSummaryResponse(
        id=portafolio.id,
        title=portafolio.title,
        description=portafolio.description,
        color=portafolio.color,
        is_private=portafolio.is_private,
        posts_count=len(visibles),
        preview=_preview_de(visibles),
        created_at=portafolio.created_at,
    )

def list_portfolios(
    db: Session, username: str, viewer: User | None
) -> list[PortfolioSummaryResponse]:
    duenio = user_service.get_user_by_username(db, username)
    if duenio is None:
        raise NotFoundError("Ese usuario no existe")

    portafolios = portfolio_service.list_portfolios(db, duenio, viewer)
    return [_resumen(db, p, viewer) for p in portafolios]

def get_portfolio(
    db: Session, portfolio_id: int, viewer: User | None
) -> PortfolioResponse:
    portafolio = portfolio_service.get_portfolio(db, portfolio_id, viewer)
    visibles = portfolio_service.list_posts(db, portafolio, viewer)

    conteos = post_service.counts_for(db, [p.id for p in visibles])

    return PortfolioResponse(
        id=portafolio.id,
        title=portafolio.title,
        description=portafolio.description,
        color=portafolio.color,
        is_private=portafolio.is_private,
        posts_count=len(visibles),
        preview=_preview_de(visibles),
        created_at=portafolio.created_at,
        posts=[
            _resumen_de_publicacion(p, *conteos.get(p.id, (0, 0))) for p in visibles
        ],
        can_edit=viewer is not None and viewer.id == portafolio.user_id,
    )

def create_portfolio(db: Session, user: User, payload) -> PortfolioResponse:
    portafolio = portfolio_service.create_portfolio(
        db,
        user,
        payload.title,
        payload.description,
        payload.color,
        payload.is_private,
    )
    return get_portfolio(db, portafolio.id, user)

def update_portfolio(
    db: Session, user: User, portfolio_id: int, payload
) -> PortfolioResponse:
    portfolio_service.update_portfolio(
        db,
        user,
        portfolio_id,
        titulo=payload.title,
        descripcion=payload.description,
        color=payload.color,
        privado=payload.is_private,
    )
    return get_portfolio(db, portfolio_id, user)

def set_posts(
    db: Session, user: User, portfolio_id: int, post_ids: list[int]
) -> PortfolioResponse:
    portfolio_service.set_posts(db, user, portfolio_id, post_ids)
    return get_portfolio(db, portfolio_id, user)

def add_post(
    db: Session, user: User, portfolio_id: int, post_id: int
) -> PortfolioResponse:
    portfolio_service.add_post(db, user, portfolio_id, post_id)
    return get_portfolio(db, portfolio_id, user)

def remove_post(
    db: Session, user: User, portfolio_id: int, post_id: int
) -> PortfolioResponse:
    portfolio_service.remove_post(db, user, portfolio_id, post_id)
    return get_portfolio(db, portfolio_id, user)

def titulo_repetido(
    db: Session, user: User, titulo: str, excluir_id: int | None
) -> TituloRepetidoResponse:
    return TituloRepetidoResponse(
        repetido=portfolio_service.titulo_repetido(db, user, titulo, excluir_id)
    )
