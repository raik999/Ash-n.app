from __future__ import annotations
from typing import Any
from urllib.parse import urlencode
from services.api_client import api

async def search_users(query: str, limit: int = 20) -> list[dict[str, Any]]:
    query_string = urlencode({"q": query, "limit": limit})
    return await api.get(f"/api/users?{query_string}")

async def list_history() -> list[dict[str, Any]]:
    return await api.get("/api/users/me/searches")

async def add_history(kind: str, value: str) -> list[dict[str, Any]]:
    return await api.post("/api/users/me/searches", {"kind": kind, "value": value})

async def clear_history() -> dict[str, Any]:
    return await api.delete("/api/users/me/searches")
