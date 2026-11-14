from __future__ import annotations

from typing import Any

from services.api_client import api

async def reportar_publicacion(post_id: int, motivo: str | None = None) -> dict[str, Any]:
    return await api.post(f"/api/reports/posts/{post_id}", {"motivo": motivo})

async def reportar_usuario(username: str, motivo: str | None = None) -> dict[str, Any]:
    return await api.post(f"/api/reports/users/{username}", {"motivo": motivo})

async def ya_reporte_publicacion(post_id: int) -> bool:
    try:
        datos = await api.get(f"/api/reports/posts/{post_id}")
        return bool(datos.get("ya_reportado"))
    except Exception:
        return False

async def ya_reporte_usuario(username: str) -> bool:
    try:
        datos = await api.get(f"/api/reports/users/{username}")
        return bool(datos.get("ya_reportado"))
    except Exception:
        return False

async def sancionar(username: str, dias: int, motivo: str | None = None) -> dict[str, Any]:
    return await api.post(
        f"/api/admin/users/{username}/sancion", {"dias": dias, "motivo": motivo}
    )

async def levantar_sancion(username: str) -> dict[str, Any]:
    return await api.delete(f"/api/admin/users/{username}/sancion")

async def eliminar_cuenta(username: str) -> dict[str, Any]:
    return await api.delete(f"/api/admin/users/{username}")
