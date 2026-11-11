from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view, foto_de, show_error
from components.settings_row import boton_barra, encabezado_principal
from components.layout import bottom_nav, estado_vacio, safe_update, tarjeta
from context.app_state import AppState
from services import chat_service
from services.api_client import ApiError, api
from services.realtime_service import (
    EVENTO_CHAT_ELIMINADO,
    EVENTO_CHAT_NUEVO,
    EVENTO_MENSAJE,
)
from style.responsive import pantalla
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

    campana = boton_barra(ft.Icons.CAMPAIGN, "Notificaciones")

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

        return tarjeta(
            bgcolor=Colors.SURFACE,
            on_click=partial(abrir_chat, chat["id"]),
            tooltip=f"Abrir el chat con {otro['username']}",
            contenido=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Container(
                        width=48,
                        height=48,
                        content=avatar_view(foto_de(otro), 48),
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
        return estado_vacio(
            ft.Icons.FORUM_OUTLINED,
            "Todavia no tienes chats",
            "Entra al perfil de un artista y toca el globo para "
            "empezar a hablar.",
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
                    encabezado_principal(
                        "Chats",
                        acciones=[
                            ft.Stack(
                                width=Sizes.TOUCH_MIN,
                                height=Sizes.TOUCH_MIN,
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
                            )
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=pantalla().padding),
                        content=lista,
                    ),
                ],
            )
        ],
    )
