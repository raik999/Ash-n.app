from __future__ import annotations
from datetime import datetime, timezone
from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view, show_error
from components.layout import bottom_nav, safe_update
from context.app_state import AppState
from services import chat_service
from services.api_client import ApiError, api
from services.realtime_service import (
    EVENTO_CHAT_ELIMINADO,
    EVENTO_CHAT_NUEVO,
    EVENTO_MENSAJE,
)
from style.theme import Colors, Fonts, Sizes, TextSizes

def tiempo_corto(cuando: str | None) -> str:
    if not cuando:
        return ""

    try:
        momento = datetime.fromisoformat(cuando.replace("Z", "+00:00"))
    except ValueError:
        return ""

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    segundos = (datetime.now(timezone.utc) - momento).total_seconds()

    if segundos < 60:
        return "ahora"
    if segundos < 3600:
        return f"{int(segundos // 60)} m"
    if segundos < 86400:
        return f"{int(segundos // 3600)} h"
    if segundos < 604800:
        return f"{int(segundos // 86400)} d"

    return momento.strftime("%d/%m")

async def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route="/chats", controls=[])

    lista = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)

    campana = ft.IconButton(
        icon=ft.Icons.CAMPAIGN,
        icon_size=28,
        icon_color=Colors.TEXT_PRIMARY,
        tooltip="Notificaciones",
    )

    globo_campana = ft.Container(
        bgcolor=Colors.BRAND_RED,
        border_radius=10,
        padding=ft.Padding.symmetric(horizontal=6, vertical=1),
        visible=False,
        content=ft.Text("", size=TextSizes.SMALL - 1, color=Colors.TEXT_ON_DARK),
    )

    def pintar_campana() -> None:
        cantidad = state.notificaciones_sin_ver
        globo_campana.visible = cantidad > 0
        globo_campana.content.value = str(cantidad) if cantidad < 100 else "99+"
        safe_update(globo_campana)

    async def ir_a_notificaciones(e) -> None:
        await page.push_route("/notifications")

    async def abrir_chat(chat_id: int) -> None:
        await page.push_route(f"/chat/{chat_id}")

    campana.on_click = ir_a_notificaciones

    def fila(chat: dict[str, Any]) -> ft.Control:
        otro = chat["other"]
        no_leidos = int(chat.get("unread") or 0)

        vista_previa = (chat.get("last_message") or "").strip()
        if not vista_previa:
            vista_previa = "Todavia no se escribieron nada"
            color_previa = Colors.TEXT_MUTED
        else:
            color_previa = Colors.TEXT_PRIMARY if no_leidos else Colors.TEXT_MUTED

        derecha: list[ft.Control] = [
            ft.Text(
                tiempo_corto(chat.get("last_message_at")),
                size=TextSizes.SMALL,
                color=Colors.TEXT_MUTED,
            )
        ]

        if no_leidos:
            derecha.append(
                ft.Container(
                    bgcolor=Colors.BRAND_RED,
                    border_radius=11,
                    width=22,
                    height=22,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        str(no_leidos) if no_leidos < 100 else "99+",
                        size=TextSizes.SMALL - 1,
                        color=Colors.TEXT_ON_DARK,
                        weight=ft.FontWeight.BOLD,
                    ),
                )
            )

        return ft.Container(
            bgcolor=Colors.SURFACE,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            ink=True,
            on_click=partial(abrir_chat, chat["id"]),
            tooltip=f"Abrir el chat con {otro['username']}",
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Container(
                        width=48,
                        height=48,
                        content=avatar_view(api.absolute_url(otro.get("avatar_url")), 48),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            spacing=2,
                            tight=True,
                            controls=[
                                ft.Text(
                                    otro["username"],
                                    size=TextSizes.BODY,
                                    color=Colors.TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_600,
                                    font_family=Fonts.BODY,
                                ),
                                ft.Text(
                                    vista_previa,
                                    size=TextSizes.SMALL,
                                    color=color_previa,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    weight=(
                                        ft.FontWeight.W_600
                                        if no_leidos
                                        else ft.FontWeight.NORMAL
                                    ),
                                ),
                            ],
                        ),
                    ),
                    ft.Column(
                        spacing=4,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=derecha,
                    ),
                ],
            ),
        )

    def vacio() -> ft.Control:
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                tight=True,
                controls=[
                    ft.Icon(
                        ft.Icons.FORUM_OUTLINED, size=52, color=Colors.PLACEHOLDER
                    ),
                    ft.Text(
                        "Todavia no tienes chats",
                        size=TextSizes.SUBTITLE,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Entra al perfil de un artista y toca el globo que "
                        "esta junto a su foto para empezar a hablar.",
                        size=TextSizes.SMALL,
                        color=Colors.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    async def cargar() -> None:
        try:
            chats = await chat_service.list_chats()
        except ApiError as error:
            show_error(page, error.message)
            return

        lista.controls = [fila(chat) for chat in chats] if chats else [vacio()]
        safe_update(lista)

        await state.refrescar_sin_leer()
        pintar_campana()

    async def al_recibir(tipo: str, datos: Any) -> None:
        if tipo in (EVENTO_MENSAJE, EVENTO_CHAT_NUEVO, EVENTO_CHAT_ELIMINADO):
            await cargar()

    state.vivo.suscribir("chats", al_recibir)

    await cargar()

    return ft.View(
        route="/chats",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=2, sin_leer=state.chats_sin_leer),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(
                            left=Sizes.PAGE_PADDING, right=8, top=14, bottom=8
                        ),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "CHAT",
                                    size=TextSizes.TITLE,
                                    weight=ft.FontWeight.W_900,
                                    color=Colors.TEXT_PRIMARY,
                                    font_family=Fonts.HEADING,
                                ),
                                ft.Stack(
                                    width=48,
                                    height=48,
                                    controls=[
                                        ft.Container(
                                            content=campana,
                                            alignment=ft.Alignment.CENTER,
                                        ),
                                        ft.Container(
                                            content=globo_campana,
                                            right=0,
                                            top=2,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=Sizes.PAGE_PADDING),
                        content=lista,
                    ),
                ],
            )
        ],
    )
