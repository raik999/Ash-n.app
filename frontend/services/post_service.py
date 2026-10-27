from __future__ import annotations

from typing import Any

from services.api_client import api

async def create_post(
    title: str | None = None,
    description: str | None = None,
    tag_ids: list[int] | None = None,
) -> dict[str, Any]:
    return await api.post(
        "/api/posts",
        {"title": title, "description": description, "tag_ids": tag_ids or []},
    )

async def update_post(
    post_id: int,
    title: str | None = None,
    description: str | None = None,
    tag_ids: list[int] | None = None,
) -> dict[str, Any]:
    return await api.patch(
        f"/api/posts/{post_id}",
        {"title": title, "description": description, "tag_ids": tag_ids or []},
    )

async def publish_post(post_id: int) -> dict[str, Any]:
    return await api.post(f"/api/posts/{post_id}/publish")

async def delete_post(post_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/posts/{post_id}")

async def get_post(post_id: int) -> dict[str, Any]:
    return await api.get(f"/api/posts/{post_id}")

async def list_user_posts(username: str) -> list[dict[str, Any]]:
    return await api.get(f"/api/users/{username}/posts")

async def upload_file(
    post_id: int, filename: str, content: bytes, mime: str
) -> dict[str, Any]:
    return await api.upload(f"/api/posts/{post_id}/files", "file", filename, content, mime)

async def delete_file(post_id: int, file_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/posts/{post_id}/files/{file_id}")

async def like(post_id: int) -> dict[str, Any]:
    return await api.post(f"/api/posts/{post_id}/like")

async def unlike(post_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/posts/{post_id}/like")

async def list_comments(post_id: int) -> list[dict[str, Any]]:
    return await api.get(f"/api/posts/{post_id}/comments")

async def add_comment(post_id: int, text: str) -> dict[str, Any]:
    return await api.post(f"/api/posts/{post_id}/comments", {"text": text})

async def delete_comment(post_id: int, comment_id: int) -> dict[str, Any]:
    return await api.delete(f"/api/posts/{post_id}/comments/{comment_id}")
