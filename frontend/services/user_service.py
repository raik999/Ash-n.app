from __future__ import annotations

from datetime import date
from typing import Any

from services.api_client import api


def update_profile(
    *,
    name: str | None = None,
    bio: str | None = None,
    birthdate: date | None = None,
    tag_ids: list[int] | None = None,
    include_bio: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if name is not None:
        payload["name"] = name

    if include_bio:
        payload["bio"] = bio
    elif bio is not None:
        payload["bio"] = bio

    if birthdate is not None:
        payload["birthdate"] = birthdate.isoformat()

    if tag_ids is not None:
        payload["tag_ids"] = tag_ids

    return api.patch("/api/users/me", payload)


def upload_avatar(filename: str, content: bytes, mime: str) -> dict[str, Any]:
    return api.upload("/api/users/me/avatar", "file", filename, content, mime)


def delete_avatar() -> dict[str, Any]:
    return api.delete("/api/users/me/avatar")


def get_public_profile(username: str) -> dict[str, Any]:
    return api.get(f"/api/users/{username}")
