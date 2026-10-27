from __future__ import annotations
from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view, show_error
from components.layout import safe_update
from components.settings_row import screen_header
from context.app_state import AppState
from services import post_service
from services.api_client import ApiError, api
from style.theme import Colors, Sizes, TextSizes

MAX_COMENTARIO = 800

async def view(page: ft.Page, state: AppState, post_id: int) -> ft.View:
    ruta = f"/post/{post_id}/comments"

    lista = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    campo = ft.TextField(
        hint_text="Escribe un comentario",
        border=ft.InputBorder.NONE,
        filled=False,
        dense=True,
        expand=True,
        max_length=MAX_COMENTARIO,
        multiline=True,
        min_lines=1,
        max_lines=4,
        text_size=TextSizes.BODY,
        text_style=ft.TextStyle(color=Colors.TEXT_BODY),
        cursor_color=Colors.TEXT_PRIMARY,
    )

    async def borrar(comment_id: int) -> None:
        try:
            await post_service.delete_comment(post_id, comment_id)
        except ApiError as error:
            show_error(page, error.message)
            return
        await cargar()

    def fila(comentario: dict[str, Any]) -> ft.Control:
        autor = comentario["author"]

        cabecera: list[ft.Control] = [
            ft.Container(
                width=26,
                height=26,
                content=avatar_view(api.absolute_url(autor.get("avatar_url")), 26),
            ),
            ft.Text(
                autor["username"],
                size=TextSizes.SMALL,
                color=Colors.TEXT_MUTED,
            ),
            ft.Container(expand=True),
        ]

        if comentario.get("can_delete"):
            cabecera.append(
                ft.TextButton(
                    content=ft.Text(
                        "Eliminar",
                        size=TextSizes.SMALL,
                        color=Colors.BRAND_RED,
                    ),
                    on_click=partial(borrar, comentario["id"]),
                    style=ft.ButtonStyle(
                        padding=ft.Padding.symmetric(horizontal=6, vertical=0),
                        overlay_color=ft.Colors.TRANSPARENT,
                    ),
                )
            )

        return ft.Column(
            spacing=4,
            tight=True,
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=cabecera,
                ),
                ft.Container(
                    bgcolor=Colors.SURFACE,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    content=ft.Text(
                        comentario["text"],
                        size=TextSizes.BODY,
                        color=Colors.TEXT_BODY,
                    ),
                ),
            ],
        )

    async def cargar() -> None:
        try:
            comentarios = await post_service.list_comments(post_id)
        except ApiError as error:
            show_error(page, error.message)
            return

        if not comentarios:
            lista.controls = [
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=40,
                    content=ft.Text(
                        "Todavia no hay comentarios",
                        size=TextSizes.BODY,
                        color=Colors.TEXT_MUTED,
                    ),
                )
            ]
        else:
            lista.controls = [fila(c) for c in comentarios]

        safe_update(lista)

    async def enviar(e=None) -> None:
        texto = (campo.value or "").strip()

        if not texto:
            return

        if not state.is_authenticated:
            show_error(page, "Inicia sesion para comentar")
            return

        try:
            await post_service.add_comment(post_id, texto)
        except ApiError as error:
            show_error(page, error.message)
            return

        campo.value = ""
        safe_update(campo)
        await cargar()

    def limpiar(e) -> None:
        campo.value = ""
        safe_update(campo)

    async def volver(e) -> None:
        await page.push_route(f"/post/{post_id}")

    campo.on_submit = enviar

    await cargar()

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
                        icon=ft.Icons.KEYBOARD_ARROW_UP,
                        icon_size=22,
                        icon_color=Colors.TEXT_PRIMARY,
                        tooltip="Enviar",
                        on_click=enviar,
                    ),
                ],
            ),
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
                    screen_header("Comentarios", volver),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=Sizes.PAGE_PADDING, vertical=12
                        ),
                        content=lista,
                    ),
                    barra_escritura,
                ],
            )
        ],
    )
