from __future__ import annotations
from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view, foto_de, show_error
from components.layout import bottom_nav, estado_vacio
from components.profile_scroll import grilla_fija, perfil_desplazable
from components.post_media import grid_cell
from components.tag_chip import display_chip
from context.app_state import AppState
from services import post_service, user_service
from services.api_client import ApiError, api
from style.responsive import pantalla
from style.theme import Colors, Fonts, LineHeight, Radius, Sizes, Space, TextSizes

async def view(page: ft.Page, state: AppState, username: str) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route=f"/user/{username}", controls=[])

    async def go_back(e: ft.ControlEvent) -> None:
        await page.push_route("/search")

    async def abrir_chat(e: ft.ControlEvent) -> None:
        from services import chat_service

        try:
            chat = await chat_service.open_chat_with(username)
        except ApiError as error:
            show_error(page, error.message)
            return

        await page.push_route(f"/chat/{chat['id']}")

    if username == (state.user or {}).get("username"):
        await page.push_route("/profile")
        return ft.View(route=f"/user/{username}", controls=[])

    profile: dict[str, Any] | None = None
    error_message: str | None = None

    try:
        profile = await user_service.get_public_profile(username)
    except ApiError as error:
        error_message = error.message

    if profile is None:
        return ft.View(
            route=f"/user/{username}",
            padding=0,
            bgcolor=Colors.BACKGROUND,
            navigation_bar=bottom_nav(page, selected=1),
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
                                on_click=go_back,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                error_message or "No se pudo cargar el perfil",
                                size=TextSizes.BODY,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ],
                )
            ],
        )

    header = ft.Container(
        bgcolor=Colors.SURFACE,
        height=250,
        content=ft.Stack(
            controls=[
                ft.Container(
                    content=avatar_view(foto_de(profile), 150),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.only(top=20),
                    width=10000,
                    height=210,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_IOS_NEW,
                        icon_size=22,
                        icon_color=Colors.BRAND_DARK,
                        tooltip="Volver",
                        on_click=go_back,
                    ),
                    left=6,
                    top=8,
                ),
                ft.Container(
                    left=14,
                    bottom=4,
                    content=ft.Row(
                        spacing=10,
                        tight=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.FAVORITE,
                                    size=22,
                                    color=Colors.TEXT_ON_DARK,
                                ),
                                bgcolor=Colors.BRAND_DARK,
                                width=78,
                                height=38,
                                border_radius=19,
                                alignment=ft.Alignment.CENTER,
                                on_click=None,
                                tooltip="Seguir (proximamente)",
                            ),
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.MARK_UNREAD_CHAT_ALT,
                                    size=22,
                                    color=Colors.TEXT_ON_DARK,
                                ),
                                bgcolor=Colors.BRAND_DARK,
                                width=62,
                                height=38,
                                border_radius=19,
                                alignment=ft.Alignment.CENTER,
                                on_click=abrir_chat,
                                ink=True,
                                tooltip=f"Enviar un mensaje a {username}",
                            ),
                        ],
                    ),
                ),
            ]
        ),
    )

    user_tags = profile.get("tipo") or []
    tags_row = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[display_chip(tag) for tag in user_tags],
    )

    publicaciones: list[dict] = []
    try:
        publicaciones = await post_service.list_user_posts(username)
    except ApiError:
        publicaciones = []

    async def abrir_publicacion(post_id: int) -> None:
        await page.push_route(f"/post/{post_id}")

    RELLENO = Space.XS
    ancho_grilla = pantalla().ancho - RELLENO * 2

    def grilla_publicaciones() -> ft.Control:
        if not publicaciones:
            return estado_vacio(
                ft.Icons.PHOTO_LIBRARY_OUTLINED,
                "Todavia no hay publicaciones",
                f"Cuando @{profile['username']} publique algo, va a aparecer aqui.",
            )

        celdas = [
            grid_cell(pub, partial(abrir_publicacion, pub["id"]))
            for pub in publicaciones
        ]
        return grilla_fija(celdas, ancho_disponible=ancho_grilla)

    def pestana_portafolios() -> ft.Control:
        return estado_vacio(
            ft.Icons.COLLECTIONS_OUTLINED,
            "Todavia no hay portafolios",
            f"@{profile['username']} aun no agrupo sus publicaciones.",
        )

    bio = profile.get("bio")

    bloque_superior = ft.Column(
        spacing=0,
        controls=[
            header,
            ft.Container(
                padding=ft.Padding.only(
                    left=pantalla().padding,
                    right=pantalla().padding,
                    top=Space.SM + 2,
                    bottom=Space.MD,
                ),
                content=ft.Column(
                    spacing=Space.XS + 2,
                    controls=[
                        ft.Text(
                            profile.get("name") or "",
                            size=pantalla().texto(TextSizes.HEADING + 2),
                            color=Colors.TEXT_PRIMARY,
                            font_family=Fonts.HEADING,
                        ),
                        ft.Text(
                            f"@{profile.get('username', '')}",
                            size=pantalla().texto(TextSizes.BODY),
                            color=Colors.TEXT_MUTED,
                        ),
                        tags_row,
                        ft.Text(
                            bio or "Este artista todavia no escribio su presentacion.",
                            size=pantalla().texto(TextSizes.BODY),
                            color=Colors.TEXT_BODY if bio else Colors.TEXT_MUTED,
                            style=ft.TextStyle(height=LineHeight.BODY),
                        ),
                    ],
                ),
            ),
        ],
    )

    return ft.View(
        route=f"/user/{username}",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=1, sin_leer=state.chats_sin_leer),
        controls=[
            perfil_desplazable(
                encabezado=bloque_superior,
                etiquetas=["Publicaciones", "Portafolios"],
                contenidos=[grilla_publicaciones, pestana_portafolios],
                relleno_horizontal=RELLENO,
            )
        ],
    )
