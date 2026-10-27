from __future__ import annotations
from functools import partial
from typing import Any

import flet as ft

from components.feedback import avatar_view
from components.layout import bottom_nav
from components.post_media import grid_cell
from components.tag_chip import display_chip
from context.app_state import AppState
from services import post_service, user_service
from services.api_client import ApiError, api
from style.theme import Colors, Fonts, Sizes, TextSizes

async def view(page: ft.Page, state: AppState, username: str) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route=f"/user/{username}", controls=[])

    async def go_back(e: ft.ControlEvent) -> None:
        await page.push_route("/search")

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
                    content=avatar_view(api.absolute_url(profile.get("avatar_url")), 150),
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
                    content=ft.Container(
                        content=ft.Icon(
                            ft.Icons.FAVORITE, size=22, color=Colors.TEXT_ON_DARK
                        ),
                        bgcolor=Colors.BRAND_DARK,
                        width=78,
                        height=38,
                        border_radius=19,
                        alignment=ft.Alignment.CENTER,
                        on_click=None,
                        tooltip="Seguir (proximamente)",
                    ),
                    left=14,
                    bottom=4,
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

    def posts_grid() -> ft.Control:
        if not publicaciones:
            return empty_tab(f"@{profile['username']} todavia no tiene publicaciones")

        return ft.GridView(
            controls=[
                grid_cell(pub, partial(abrir_publicacion, pub["id"]))
                for pub in publicaciones
            ],
            runs_count=3,
            child_aspect_ratio=1.0,
            spacing=6,
            run_spacing=6,
            padding=ft.Padding.all(6),
            expand=True,
        )

    def empty_tab(message: str) -> ft.Container:
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Text(message, size=TextSizes.BODY, color=Colors.TEXT_MUTED),
        )

    tabs = ft.Tabs(
        selected_index=0,
        length=2,
        expand=True,
        content=ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Publicaciones"),
                        ft.Tab(label="Portafolios"),
                    ],
                    label_color=Colors.TEXT_PRIMARY,
                    unselected_label_color=Colors.TEXT_MUTED,
                    indicator_color=Colors.BRAND_DARK,
                    indicator_thickness=3,
                    divider_color=ft.Colors.TRANSPARENT,
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        posts_grid(),
                        empty_tab("Todavia no tiene portafolios"),
                    ],
                ),
            ],
        ),
    )

    bio = profile.get("bio")

    return ft.View(
        route=f"/user/{username}",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=1),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    header,
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=Sizes.PAGE_PADDING, vertical=14),
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Text(
                                    profile.get("name") or "",
                                    size=26,
                                    weight=ft.FontWeight.W_600,
                                    color=Colors.TEXT_PRIMARY,
                                    font_family=Fonts.HEADING,
                                ),
                                ft.Text(
                                    f"@{profile.get('username', '')}",
                                    size=TextSizes.BODY,
                                    color=Colors.TEXT_MUTED,
                                ),
                                tags_row,
                                ft.Text(
                                    bio or "Este artista todavia no escribio su presentacion.",
                                    size=TextSizes.BODY,
                                    color=Colors.TEXT_BODY if bio else Colors.TEXT_MUTED,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        content=tabs,
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=8),
                    ),
                ],
            )
        ],
    )
