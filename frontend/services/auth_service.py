from __future__ import annotations
from typing import Any
from services.api_client import api

async def register(
    email: str, name: str, username: str, password: str, confirm_password: str
) -> dict[str, Any]:
    return await api.post(
        "/api/auth/register",
        {
            "email": email,
            "name": name,
            "username": username,
            "password": password,
            "confirm_password": confirm_password,
        },
    )

async def login(identifier: str, password: str) -> dict[str, Any]:
    return await api.post("/api/auth/login", {"identifier": identifier, "password": password})

async def get_me() -> dict[str, Any]:
    return await api.get("/api/auth/me")
