from __future__ import annotations
from typing import Any
from services.api_client import api


def register(
    email: str, name: str, username: str, password: str, confirm_password: str
) -> dict[str, Any]:
    return api.post(
        "/api/auth/register",
        {
            "email": email,
            "name": name,
            "username": username,
            "password": password,
            "confirm_password": confirm_password,
        },
    )


def login(identifier: str, password: str) -> dict[str, Any]:
    return api.post("/api/auth/login", {"identifier": identifier, "password": password})


def get_me() -> dict[str, Any]:
    return api.get("/api/auth/me")
