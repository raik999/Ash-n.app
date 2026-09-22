from __future__ import annotations

from typing import Any

from services.api_client import api


def list_tags() -> list[dict[str, Any]]:
    return api.get("/api/tags")
