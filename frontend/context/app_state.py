from __future__ import annotations
from typing import Any

import flet as ft

from services import auth_service
from services.api_client import ApiError, api

STORAGE_TOKEN_KEY = "ashun.token"
LEGACY_RECENTS_KEY = "ashun.recents"

class AppState:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user: dict[str, Any] | None = None
        self.tags: list[dict[str, Any]] = []
        self._recents: list[dict[str, str]] | None = None
        self._drop_legacy_recents()

    def save_session(self, token: str, user: dict[str, Any]) -> None:
        self.user = user
        api.set_token(token)
        self.page.client_storage.set(STORAGE_TOKEN_KEY, token)
        self._recents = None

    def clear_session(self) -> None:
        self.user = None
        api.set_token(None)
        self.page.client_storage.remove(STORAGE_TOKEN_KEY)
        self._recents = None

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


    def load_recents(self, force: bool = False) -> list[dict[str, str]]:
        if self._recents is not None and not force:
            return self._recents

        if not self.is_authenticated:
            self._recents = []
            return self._recents

        from services import search_service

        try:
            entries = search_service.list_history()
        except ApiError:
            return []

        self._recents = [
            {"kind": entry["kind"], "value": entry["value"]} for entry in entries
        ]
        return self._recents

    def add_recent(self, kind: str, value: str) -> None:
        value = value.strip()
        if not value:
            return
        
        if not self.is_authenticated:
            return
        
        from services import search_service

        try:
            entries = search_service.add_history(kind, value)
        except ApiError:
            self._recents = None
            return

        self._recents = [
            {"kind": entry["kind"], "value": entry["value"]} for entry in entries
        ]

    def clear_recents(self) -> None:
        if not self.is_authenticated:
            self._recents = []
            return

        from services import search_service

        search_service.clear_history()
        self._recents = []

    def _drop_legacy_recents(self) -> None:
        try:
            self.page.client_storage.remove(LEGACY_RECENTS_KEY)
        except Exception:
            pass

    def load_tags(self, force: bool = False) -> list[dict[str, Any]]:
        if self.tags and not force:
            return self.tags

        from services import tag_service

        self.tags = tag_service.list_tags()
        return self.tags
