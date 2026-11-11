from __future__ import annotations

from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view, foto_de, show_error
from components.layout import estado_vacio, safe_update, tarjeta
from components.settings_row import screen_header
from context.app_state import AppState
from pages.chats_page import tiempo_corto
from services import chat_service
from services.api_client import ApiError, api
from style.responsive import pantalla
from style.theme import Colors, Fonts, Sizes, TextSizes

TIPO_LIKE = "like"

async def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route="/notifications", controls=[])

    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    async def volver(e) -> None:
        await page.push_route("/chats")

    async def abrir_post(post_id: int) -> None:
        await page.push_route(f"/post/{post_id}")

    async def abrir_perfil(username: str) -> None:
        await page.push_route(f"/user/{username}")

    def fila(aviso: dict[str, Any]) -> ft.Control:
        usuario = aviso["user"]
        es_like = aviso["kind"] == TIPO_LIKE
        es_nueva = bool(aviso.get("is_new"))

        icono = ft.Icons.FAVORITE if es_like else ft.Icons.CHAT_BUBBLE
        color_icono = Colors.BRAND_RED if es_like else Colors.BRAND_DARK
        que_hizo = (
            "le dio me gusta a tu publicacion"
            if es_like
            else "comento tu publicacion"
        )

        nombre = ft.Container(
            ink=True,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
            on_click=partial(abrir_perfil, usuario["username"]),
            tooltip=f"Ver el perfil de {usuario['username']}",
            content=ft.Text(
                usuario["username"],
                size=TextSizes.BODY,
                color=Colors.TEXT_PRIMARY,
                weight=ft.FontWeight.W_600,
                font_family=Fonts.BODY,
            ),
        )

        texto: list[ft.Control] = [
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                wrap=True,
                controls=[
                    nombre,
                    ft.Text(
                        f" {que_hizo}",
                        size=TextSizes.BODY,
                        color=Colors.TEXT_BODY,
                    ),
                ],
            )
        ]

        vista_previa = (aviso.get("post_preview") or "").strip()
        if vista_previa:
            texto.append(
                ft.Text(
                    f"“{vista_previa}”",
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_MUTED,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    italic=True,
                )
            )

        return tarjeta(
            bgcolor=Colors.PEACH_SOFT if es_nueva else Colors.SURFACE,
            on_click=partial(abrir_post, aviso["post_id"]),
            tooltip="Ver la publicacion",
            contenido=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        ink=True,
                        border_radius=22,
                        on_click=partial(abrir_perfil, usuario["username"]),
                        tooltip=f"Ver el perfil de {usuario['username']}",
                        content=avatar_view(
                            foto_de(usuario), 44
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column(spacing=2, tight=True, controls=texto),
                    ),
                    ft.Column(
                        spacing=6,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icono, size=20, color=color_icono),
                            ft.Text(
                                tiempo_corto(aviso.get("created_at")),
                                size=TextSizes.SMALL - 1,
                                color=Colors.TEXT_MUTED,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def vacio() -> ft.Control:
        return estado_vacio(
            ft.Icons.CAMPAIGN_OUTLINED,
            "Todavia no hay nada",
            "Aqui vas a ver quien le da me gusta y quien comenta "
            "tus publicaciones.",
        )

    try:
        datos = await chat_service.list_notifications()
    except ApiError as error:
        show_error(page, error.message)
        datos = {"items": [], "unseen": 0}

    avisos = datos.get("items") or []
    lista.controls = [fila(a) for a in avisos] if avisos else [vacio()]

    if avisos:
        try:
            await chat_service.mark_notifications_seen()
            await state.refrescar_sin_leer()
        except ApiError:
            pass

    safe_update(lista)

    return ft.View(
        route="/notifications",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header("Notificaciones", volver),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=pantalla().padding, vertical=10
                        ),
                        content=lista,
                    ),
                ],
            )
        ],
    )
