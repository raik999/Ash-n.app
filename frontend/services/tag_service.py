from __future__ import annotations
from typing import Any
from services.api_client import api

async def list_tags() -> list[dict[str, Any]]:
    return await api.get("/api/tags")
