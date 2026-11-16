from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from controller import portfolio_controller
from entities.user import User
from middleware.auth_middleware import get_current_user, get_current_user_optional
from validations.auth_validation import MessageResponse
from validations.portfolio_validation import (
    CreatePortfolioRequest,
    PortfolioResponse,
    PortfolioSummaryResponse,
    SetPostsRequest,
    TituloRepetidoResponse,
    UpdatePortfolioRequest,
)
from services import portfolio_service

router = APIRouter(prefix="/api/portfolios", tags=["Portafolios"])

@router.get(
    "/titulo-repetido",
    response_model=TituloRepetidoResponse,
    summary="Si ya tengo un portafolio con ese titulo",
)
def titulo_repetido(
    title: str = Query(..., min_length=1),
    excluir: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TituloRepetidoResponse:
    return portfolio_controller.titulo_repetido(db, current_user, title, excluir)

@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=201,
    summary="Crear un portafolio",
)
def crear(
    payload: CreatePortfolioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.create_portfolio(db, current_user, payload)

@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Un portafolio con sus publicaciones",
)
def ver(
    portfolio_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.get_portfolio(db, portfolio_id, viewer)

@router.patch(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Editar titulo, descripcion, color o privacidad",
)
def editar(
    portfolio_id: int,
    payload: UpdatePortfolioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.update_portfolio(
        db, current_user, portfolio_id, payload
    )

@router.delete(
    "/{portfolio_id}",
    response_model=MessageResponse,
    summary="Eliminar un portafolio",
)
def eliminar(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    portfolio_service.delete_portfolio(db, current_user, portfolio_id)
    return MessageResponse(detail="Portafolio eliminado")

@router.put(
    "/{portfolio_id}/posts",
    response_model=PortfolioResponse,
    summary="Dejar el portafolio con exactamente estas publicaciones",
)
def organizar(
    portfolio_id: int,
    payload: SetPostsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.set_posts(
        db, current_user, portfolio_id, payload.post_ids
    )

@router.post(
    "/{portfolio_id}/posts/{post_id}",
    response_model=PortfolioResponse,
    summary="Agregar una publicacion",
)
def agregar(
    portfolio_id: int,
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.add_post(db, current_user, portfolio_id, post_id)

@router.delete(
    "/{portfolio_id}/posts/{post_id}",
    response_model=PortfolioResponse,
    summary="Sacar una publicacion del portafolio",
)
def sacar(
    portfolio_id: int,
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    return portfolio_controller.remove_post(db, current_user, portfolio_id, post_id)
