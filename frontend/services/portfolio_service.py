from __future__ import annotations
from typing import Any
from services.api_client import api

COLORES = (
    "#2E9E27",
    "#F0743C",
    "#BE2EDD",
    "#4D7CFE",
    "#F03C3C",
    "#17B8C4",
    "#E8A317",
    "#E0457B",
)

COLOR_POR_DEFECTO = COLORES[3]

MAX_TITULO = 60
MAX_DESCRIPCION = 300

async def list_portfolios(username: str) -> list[dict[str, Any]]:
    return await api.get(f"/api/users/{username}/portfolios")

async def get_portfolio(portfolio_id: int) -> dict[str, Any]:
    return await api.get(f"/api/portfolios/{portfolio_id}")

async def create_portfolio(
    titulo: str,
    descripcion: str | None,
    color: str,
    privado: bool,
) -> dict[str, Any]:
    return await api.post(
        "/api/portfolios",
        {
            "title": titulo,
            "description": descripcion,
            "color": color,
            "is_private": privado,
        },
    )

async def update_portfolio(
    portfolio_id: int,
    *,
    titulo: str | None = None,
    descripcion: str | None = None,
    color: str | None = None,
    privado: bool | None = None,
) -> dict[str, Any]:
    cuerpo: dict[str, Any] = {}
    if titulo is not None:
        cuerpo["title"] = titulo
    if descripcion is not None:
        cuerpo["description"] = descripcion
    if color is not None:
        cuerpo["color"] = color
    if privado is not None:
        cuerpo["is_private"] = privado

    return await api.patch(f"/api/portfolios/{portfolio_id}", cuerpo)

async def delete_portfolio(portfolio_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/portfolios/{portfolio_id}")

async def titulo_repetido(titulo: str, excluir: int | None = None) -> bool:
    ruta = f"/api/portfolios/titulo-repetido?title={titulo}"
    if excluir is not None:
        ruta += f"&excluir={excluir}"

    try:
        datos = await api.get(ruta)
        return bool(datos.get("repetido"))
    except Exception:
        return False

async def set_posts(portfolio_id: int, post_ids: list[int]) -> dict[str, Any]:
    return await api.put(f"/api/portfolios/{portfolio_id}/posts", {"post_ids": post_ids})

async def add_post(portfolio_id: int, post_id: int) -> dict[str, Any]:
    return await api.post(f"/api/portfolios/{portfolio_id}/posts/{post_id}")

async def remove_post(portfolio_id: int, post_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/portfolios/{portfolio_id}/posts/{post_id}")

async def portafolios_de(post_id: int) -> list[int]:
    try:
        return await api.get(f"/api/posts/{post_id}/portfolios") or []
    except Exception:
        return []

async def set_privacidad(post_id: int, privada: bool) -> dict[str, Any]:
    return await api.patch(f"/api/posts/{post_id}/privacidad", {"is_private": privada})
