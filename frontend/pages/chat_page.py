from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import flet as ft

from components.feedback import avatar_view, show_error
from components.layout import safe_update
from context.app_state import AppState
from services import chat_service
from services.chat_service import MAX_MENSAJE
from services.api_client import ApiError, api
from services.realtime_service import EVENTO_CHAT_ELIMINADO, EVENTO_MENSAJE
from style.theme import Colors, Fonts, Sizes, TextSizes

def hora_corta(cuando: str | None) -> str:
    if not cuando:
        return ""

    try:
        momento = datetime.fromisoformat(cuando.replace("Z", "+00:00"))
    except ValueError:
        return ""

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    return momento.astimezone().strftime("%H:%M")

async def view(page: ft.Page, state: AppState, chat_id: int) -> ft.View:
    ruta = f"/chat/{chat_id}"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        chat: dict[str, Any] = await chat_service.get_chat(chat_id)
    except ApiError as error:
        return ft.View(
            route=ruta,
            padding=0,
            bgcolor=Colors.BACKGROUND,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ft.Container(
                            padding=ft.Padding.only(left=6, top=10),
                            content=ft.IconButton(
                                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                                icon_size=20,
                                icon_color=Colors.TEXT_PRIMARY,
                                on_click=lambda e: None,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                error.message,
                                size=TextSizes.BODY,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ],
                )
            ],
        )

    otro = chat["other"]

    async def volver(e) -> None:
        await page.push_route("/chats")

    async def ir_al_perfil(e) -> None:
        await page.push_route(f"/user/{otro['username']}")

    async def ir_a_configuracion(e) -> None:
        await page.push_route(f"/chat/{chat_id}/settings")

    mensajes = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    dibujados: set[int] = set()

    def burbuja(mensaje: dict[str, Any]) -> ft.Control:
        mio = bool(mensaje.get("mine"))

        cuerpo = ft.Container(
            bgcolor=Colors.BRAND_DARK if mio else Colors.SURFACE,
            border_radius=ft.BorderRadius(
                top_left=14,
                top_right=14,
                bottom_left=4 if not mio else 14,
                bottom_right=4 if mio else 14,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=(
                    ft.CrossAxisAlignment.END if mio else ft.CrossAxisAlignment.START
                ),
                controls=[
                    ft.Text(
                        mensaje["text"],
                        size=TextSizes.BODY,
                        color=Colors.TEXT_ON_DARK if mio else Colors.TEXT_BODY,
                        selectable=True,
                    ),
                    ft.Text(
                        hora_corta(mensaje.get("created_at")),
                        size=TextSizes.SMALL - 2,
                        color=(
                            "#FFFFFFAA" if mio else Colors.TEXT_MUTED
                        ),
                    ),
                ],
            ),
        )

        return ft.Row(
            alignment=(
                ft.MainAxisAlignment.END if mio else ft.MainAxisAlignment.START
            ),
            controls=[
                ft.Container(content=cuerpo, width=None, expand=False),
            ],
        )

    def agregar(mensaje: dict[str, Any]) -> bool:
        identificador = mensaje.get("id")

        if identificador in dibujados:
            return False

        dibujados.add(identificador)
        mensajes.controls.append(burbuja(mensaje))
        return True

    def vacio() -> ft.Control:
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Text(
                f"Escribile a {otro['username']} para empezar",
                size=TextSizes.BODY,
                color=Colors.TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    for mensaje in chat.get("messages") or []:
        agregar(mensaje)

    if not mensajes.controls:
        mensajes.controls.append(vacio())

    campo = ft.TextField(
        hint_text="Escribe un mensaje",
        border=ft.InputBorder.NONE,
        filled=False,
        dense=True,
        expand=True,
        max_length=MAX_MENSAJE,
        multiline=True,
        min_lines=1,
        max_lines=5,
        text_size=TextSizes.BODY,
        text_style=ft.TextStyle(color=Colors.TEXT_BODY),
        cursor_color=Colors.TEXT_PRIMARY,
        counter="",
    )

    async def enviar(e=None) -> None:
        texto = (campo.value or "").strip()

        if not texto:
            return

        try:
            mensaje = await chat_service.send_message(chat_id, texto)
        except ApiError as error:
            show_error(page, error.message)
            return

        if not dibujados:
            mensajes.controls.clear()

        agregar(mensaje)

        campo.value = ""
        safe_update(campo, mensajes)

    def limpiar(e) -> None:
        campo.value = ""
        safe_update(campo)

    campo.on_submit = enviar

    barra_escritura = ft.Container(
        bgcolor=Colors.BACKGROUND,
        padding=ft.Padding.symmetric(horizontal=Sizes.PAGE_PADDING, vertical=10),
        content=ft.Container(
            bgcolor="#D6D6D6",
            border_radius=22,
            padding=ft.Padding.only(left=16, right=4),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    campo,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=18,
                        icon_color=Colors.TEXT_PRIMARY,
                        tooltip="Borrar lo escrito",
                        on_click=limpiar,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SEND,
                        icon_size=20,
                        icon_color=Colors.TEXT_PRIMARY,
                        tooltip="Enviar",
                        on_click=enviar,
                    ),
                ],
            ),
        ),
    )

    async def al_recibir(tipo: str, datos: Any) -> None:
        if tipo == EVENTO_MENSAJE:
            if int(datos.get("chat_id") or 0) != chat_id:
                return

            if not dibujados:
                mensajes.controls.clear()

            if agregar(datos):
                safe_update(mensajes)

                try:
                    await chat_service.mark_read(chat_id)
                except ApiError:
                    pass

        elif tipo == EVENTO_CHAT_ELIMINADO:
            if int(datos.get("id") or 0) != chat_id:
                return

            show_error(page, "El otro usuario elimino este chat")
            await page.push_route("/chats")

    state.vivo.suscribir("chat", al_recibir)

    cabecera = ft.Container(
        padding=ft.Padding.only(left=4, right=6, top=6, bottom=6),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW,
                    icon_size=20,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Volver",
                    on_click=volver,
                ),
                ft.Container(
                    expand=True,
                    ink=True,
                    border_radius=10,
                    on_click=ir_al_perfil,
                    tooltip=f"Ver el perfil de {otro['username']}",
                    padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                content=avatar_view(
                                    api.absolute_url(otro.get("avatar_url")), 38
                                ),
                            ),
                            ft.Text(
                                otro["username"],
                                size=TextSizes.SUBTITLE,
                                color=Colors.TEXT_PRIMARY,
                                weight=ft.FontWeight.W_600,
                                font_family=Fonts.BODY,
                            ),
                        ],
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.MORE_HORIZ,
                    icon_size=26,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Configuracion del chat",
                    on_click=ir_a_configuracion,
                ),
            ],
        ),
    )

    return ft.View(
        route=ruta,
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    cabecera,
                    ft.Divider(height=1, color=Colors.SURFACE),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=Sizes.PAGE_PADDING, vertical=12
                        ),
                        content=mensajes,
                    ),
                    barra_escritura,
                ],
            )
        ],
    )
