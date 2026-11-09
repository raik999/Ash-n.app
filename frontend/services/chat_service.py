from __future__ import annotations

from typing import Any

from services.api_client import api

MAX_MENSAJE = 1000

async def list_chats() -> list[dict[str, Any]]:
    return await api.get("/api/chats")

async def open_chat_with(username: str) -> dict[str, Any]:
    return await api.post("/api/chats", {"username": username})

async def get_chat(chat_id: int) -> dict[str, Any]:
    return await api.get(f"/api/chats/{chat_id}")

async def send_message(chat_id: int, text: str) -> dict[str, Any]:
    return await api.post(f"/api/chats/{chat_id}/messages", {"text": text})

async def mark_read(chat_id: int) -> dict[str, Any]:
    return await api.post(f"/api/chats/{chat_id}/read")

async def delete_chat(chat_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/chats/{chat_id}")

async def unread_counts() -> dict[str, int]:
    return await api.get("/api/chats/unread")

async def list_notifications() -> dict[str, Any]:
    return await api.get("/api/notifications")

async def mark_notifications_seen() -> dict[str, Any]:
    return await api.post("/api/notifications/seen")
