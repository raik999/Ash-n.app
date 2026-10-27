from __future__ import annotations
from functools import partial

import flet as ft

from components.feedback import avatar_view, show_error, show_success
from components.fields import underline_field
from components.layout import bottom_nav
from components.post_media import grid_cell, new_post_cell
from components.tag_chip import display_chip
from context.app_state import AppState
from services import post_service, user_service
from services.api_client import ApiError
from style.theme import Colors, Fonts, Sizes, TextSizes

BIO_PLACEHOLDER = "Agrega una presentacion para que otros artistas sepan quien eres."

async def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route="/profile", controls=[])

    user = state.user

    publicaciones: list[dict] = []
    try:
        publicaciones = await post_service.list_user_posts(user["username"])
    except ApiError as error:
        show_error(page, error.message)

    async def go_to_settings(e: ft.ControlEvent) -> None:
        await page.push_route("/settings")

    async def go_to_tags(e: ft.ControlEvent) -> None:
        await page.push_route("/profile/tags")

    header = ft.Container(
        bgcolor=Colors.PEACH_SOFT,
        height=250,
        content=ft.Stack(
            controls=[
                ft.Container(
                    content=avatar_view(state.avatar_url, 150),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.only(top=20),
                    width=10000,
                    height=210,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_color=Colors.BRAND_DARK,
                        icon_size=30,
                        tooltip="Configuración",
                        on_click=go_to_settings,
                    ),
                    right=8,
                    top=8,
                ),
            ]
        ),
    )

    bio_text = ft.Text(
        user.get("bio") or BIO_PLACEHOLDER,
        size=TextSizes.BODY,
        color=Colors.TEXT_BODY if user.get("bio") else Colors.TEXT_MUTED,
    )

    user_tags = user.get("tipo") or []

    tag_controls: list[ft.Control] = [display_chip(tag) for tag in user_tags]
    tag_controls.append(
        ft.Container(
            content=ft.Icon(ft.Icons.ADD, size=20, color=Colors.BRAND_DARK),
            bgcolor="#A8A8A8",
            padding=ft.Padding.symmetric(horizontal=18, vertical=6),
            border_radius=20,
            on_click=go_to_tags,
            ink=True,
            tooltip="Editar mis especialidades",
        )
    )

    tags_row = ft.Row(wrap=True, spacing=8, run_spacing=8, controls=tag_controls)

    bio_field = underline_field(
        "Presentacion",
        value=user.get("bio") or "",
        multiline=True,
        max_lines=4,
        helper="Cuentale al mundo quien eres (maximo 500 caracteres)",
    )

    def close_dialog(e: ft.ControlEvent | None = None) -> None:
        page.pop_dialog()

    async def save_profile(e: ft.ControlEvent) -> None:
        new_bio = (bio_field.value or "").strip()
        bio_field.error = None

        if len(new_bio) > 500:
            bio_field.error = "Maximo 500 caracteres"
            bio_field.update()
            return

        try:
            updated_user = await user_service.update_profile(
                bio=new_bio,
                include_bio=True,
            )
            state.set_user(updated_user)

            bio_value = updated_user.get("bio")
            bio_text.value = bio_value or BIO_PLACEHOLDER
            bio_text.color = Colors.TEXT_BODY if bio_value else Colors.TEXT_MUTED

            bio_text.update()

            close_dialog()
            show_success(page, "Presentación actualizada")

        except ApiError as error:
            show_error(page, error.message)

    edit_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Editar presentación", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY
        ),
        content=ft.Container(
            width=340,
            content=ft.Column(tight=True, spacing=14, controls=[bio_field]),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.TextButton("Guardar", on_click=save_profile),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_edit_dialog(e: ft.ControlEvent) -> None:
        bio_field.value = (state.user or {}).get("bio") or ""
        bio_field.error = None
        page.show_dialog(edit_dialog)

    async def abrir_publicacion(post_id: int) -> None:
        await page.push_route(f"/post/{post_id}")

    async def crear_publicacion(e) -> None:
        await page.push_route("/post/new")

    def posts_grid() -> ft.GridView:
        tiles: list[ft.Control] = [new_post_cell(crear_publicacion)]

        for publicacion in publicaciones:
            tiles.append(
                grid_cell(publicacion, partial(abrir_publicacion, publicacion["id"]))
            )

        return ft.GridView(
            controls=tiles,
            runs_count=3,
            child_aspect_ratio=1.0,
            spacing=6,
            run_spacing=6,
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
                        empty_tab("Todavia no tienes portafolios"),
                    ],
                ),
            ],
        ),
    )

    return ft.View(
        route="/profile",
        padding=0,
        spacing=0,
        navigation_bar=bottom_nav(page, selected=3),
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
                                    user.get("name") or "",
                                    size=26,
                                    weight=ft.FontWeight.W_600,
                                    color=Colors.TEXT_PRIMARY,
                                    font_family=Fonts.HEADING,
                                ),
                                ft.Text(
                                    f"@{user.get('username', '')}",
                                    size=TextSizes.BODY,
                                    color=Colors.TEXT_MUTED,
                                ),
                                tags_row,
                                ft.Row(
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        ft.Container(expand=True, content=bio_text),
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT_SQUARE,
                                            icon_color=Colors.BRAND_DARK,
                                            icon_size=24,
                                            tooltip="Editar presentación",
                                            on_click=open_edit_dialog,
                                        ),
                                    ],
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
