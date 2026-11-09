from __future__ import annotations
from typing import Any

import flet as ft

from services import auth_service
from services.api_client import ApiError, api
from services.realtime_service import ConexionEnVivo

STORAGE_TOKEN_KEY = "ashun.token"
LEGACY_RECENTS_KEY = "ashun.recents"

class AppState:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user: dict[str, Any] | None = None
        self.tags: list[dict[str, Any]] = []
        self._recents: list[dict[str, str]] | None = None

        self.prefs = ft.SharedPreferences()

        self.vivo = ConexionEnVivo()

        self.sin_leer: dict[str, int] = {"chats": 0, "notifications": 0}

    async def start(self) -> None:
        await self._drop_legacy_recents()

    async def save_session(self, token: str, user: dict[str, Any]) -> None:
        self.user = user
        api.set_token(token)
        await self.prefs.set(STORAGE_TOKEN_KEY, token)
        self._recents = None

        self.vivo.arrancar(token)
        await self.refrescar_sin_leer()

    async def clear_session(self) -> None:
        self.user = None
        api.set_token(None)
        await self.prefs.remove(STORAGE_TOKEN_KEY)
        self._recents = None

        self.vivo.detener()
        self.sin_leer = {"chats": 0, "notifications": 0}

    async def try_restore_session(self) -> bool:
        token = await self.prefs.get(STORAGE_TOKEN_KEY)

        if not token:
            return False

        api.set_token(token)

        try:
            self.user = await auth_service.get_me()
        except ApiError:
            await self.clear_session()
            return False

        self.vivo.arrancar(token)
        await self.refrescar_sin_leer()
        return True

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

    async def load_recents(self, force: bool = False) -> list[dict[str, str]]:
        if self._recents is not None and not force:
            return self._recents

        if not self.is_authenticated:
            self._recents = []
            return self._recents

        from services import search_service

        try:
            entries = await search_service.list_history()
        except ApiError:
            return []

        self._recents = [
            {"kind": entry["kind"], "value": entry["value"]} for entry in entries
        ]
        return self._recents

    async def add_recent(self, kind: str, value: str) -> None:
        value = value.strip()
        if not value:
            return

        if not self.is_authenticated:
            return

        from services import search_service

        try:
            entries = await search_service.add_history(kind, value)
        except ApiError:
            self._recents = None
            return

        self._recents = [
            {"kind": entry["kind"], "value": entry["value"]} for entry in entries
        ]

    async def clear_recents(self) -> None:
        if not self.is_authenticated:
            self._recents = []
            return

        from services import search_service

        await search_service.clear_history()
        self._recents = []

    async def _drop_legacy_recents(self) -> None:
        try:
            await self.prefs.remove(LEGACY_RECENTS_KEY)
        except Exception:
            pass

    async def load_tags(self, force: bool = False) -> list[dict[str, Any]]:
        if self.tags and not force:
            return self.tags

        from services import tag_service

        self.tags = await tag_service.list_tags()
        return self.tags

    async def refrescar_sin_leer(self) -> None:
        if not self.is_authenticated:
            self.sin_leer = {"chats": 0, "notifications": 0}
            return

        from services import chat_service

        try:
            datos = await chat_service.unread_counts()
        except ApiError:
            return

        self.sin_leer = {
            "chats": int(datos.get("chats") or 0),
            "notifications": int(datos.get("notifications") or 0),
        }

    @property
    def chats_sin_leer(self) -> int:
        return self.sin_leer.get("chats", 0)

    @property
    def notificaciones_sin_ver(self) -> int:
        return self.sin_leer.get("notifications", 0)
