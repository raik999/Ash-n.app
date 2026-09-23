from __future__ import annotations

import json

from typing import Any

import flet as ft

from services import auth_service
from services.api_client import ApiError, api

STORAGE_TOKEN_KEY = "ashun.token"
STORAGE_RECENTS_KEY = "ashun.recents"
MAX_RECENTS = 12


class AppState:
    def __init__(self, page: ft.Page):
        self.page = page

        self.user: dict[str, Any] | None = None

        self.tags: list[dict[str, Any]] = []

    def save_session(self, token: str, user: dict[str, Any]) -> None:
        self.user = user
        api.set_token(token)
        self.page.client_storage.set(STORAGE_TOKEN_KEY, token)

    def clear_session(self) -> None:
        self.user = None
        api.set_token(None)
        self.page.client_storage.remove(STORAGE_TOKEN_KEY)

    def try_restore_session(self) -> bool:
        token = self.page.client_storage.get(STORAGE_TOKEN_KEY)

        if not token:
            return False

        api.set_token(token)

        try:
            self.user = auth_service.get_me()
            return True
        except ApiError:
            self.clear_session()
            return False

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    def set_user(self, user: dict[str, Any]) -> None:
        self.user = user

    @property
    def user_tag_ids(self) -> list[int]:
        if not self.user:
            return []
        return [tag["id"] for tag in (self.user.get("tipo") or [])]

    @property
    def avatar_url(self) -> str | None:
        if not self.user:
            return None
        return api.absolute_url(self.user.get("avatar_url"))


    def load_recents(self) -> list[dict[str, str]]:
        raw = self.page.client_storage.get(STORAGE_RECENTS_KEY)

        if not raw:
            return []

        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict) and "kind" in item and "value" in item
        ]

    def add_recent(self, kind: str, value: str) -> None:
        value = value.strip()
        if not value:
            return

        recents = self.load_recents()

        recents = [r for r in recents if not (r["kind"] == kind and r["value"] == value)]
        recents.insert(0, {"kind": kind, "value": value})

        self.page.client_storage.set(STORAGE_RECENTS_KEY, json.dumps(recents[:MAX_RECENTS]))

    def clear_recents(self) -> None:
        self.page.client_storage.remove(STORAGE_RECENTS_KEY)

    def load_tags(self, force: bool = False) -> list[dict[str, Any]]:
        if self.tags and not force:
            return self.tags

        from services import tag_service

        self.tags = tag_service.list_tags()
        return self.tags
