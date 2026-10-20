from __future__ import annotations
from typing import Any
from urllib.parse import urlencode
from services.api_client import api


def search_users(query: str, limit: int = 20) -> list[dict[str, Any]]:
    query_string = urlencode({"q": query, "limit": limit})
    return api.get(f"/api/users?{query_string}")

def list_history() -> list[dict[str, Any]]:
    return api.get("/api/users/me/searches")

def add_history(kind: str, value: str) -> list[dict[str, Any]]:
    return api.post("/api/users/me/searches", {"kind": kind, "value": value})

def clear_history() -> dict[str, Any]:
    return api.delete("/api/users/me/searches")
