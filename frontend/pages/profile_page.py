from __future__ import annotations

import flet as ft

from components.feedback import avatar_view, show_error, show_success
from components.fields import underline_field
from components.layout import bottom_nav
from components.tag_chip import display_chip
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, Fonts, Sizes, TextSizes


def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        page.go("/login")
        return ft.View(route="/profile", controls=[])

    user = state.user

    def go_to_avatar(e: ft.ControlEvent) -> None:
        page.go("/profile/avatar")

    def go_to_tags(e: ft.ControlEvent) -> None:
        page.go("/profile/tags")

    def do_logout(e: ft.ControlEvent) -> None:
        state.clear_session()
        page.go("/login")

    header = ft.Container(
        bgcolor=Colors.PEACH_SOFT,
        height=250,
        content=ft.Stack(
            controls=[
                ft.Container(
                    content=avatar_view(state.avatar_url, 150),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=20),
                    width=10000,
                    height=210,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_color=Colors.BRAND_DARK,
                        icon_size=30,
                        tooltip="Cerrar sesion",
                        on_click=do_logout,
                    ),
                    right=8,
                    top=8,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.EDIT_SQUARE,
                        icon_color=Colors.BRAND_DARK,
                        icon_size=26,
                        tooltip="Cambiar foto de perfil",
                        on_click=go_to_avatar,
                    ),
                    right=10,
                    bottom=6,
                ),
            ]
        ),
    )

    user_tags = user.get("tipo") or []

    tag_controls: list[ft.Control] = [display_chip(tag) for tag in user_tags]
    tag_controls.append(
        ft.Container(
            content=ft.Icon(ft.Icons.ADD, size=20, color=Colors.BRAND_DARK),
            bgcolor="#A8A8A8",
            padding=ft.padding.symmetric(horizontal=18, vertical=6),
            border_radius=20,
            on_click=go_to_tags,
            ink=True,
            tooltip="Editar mis especialidades",
        )
    )

    tags_row = ft.Row(wrap=True, spacing=8, run_spacing=8, controls=tag_controls)

    name_field = underline_field("Nombre completo", value=user.get("name") or "")
    bio_field = underline_field(
        "Presentacion",
        value=user.get("bio") or "",
        multiline=True,
        max_lines=4,
        helper="Cuentale al mundo quien eres (maximo 500 caracteres)",
    )

    def close_dialog(e: ft.ControlEvent | None = None) -> None:
        page.close(edit_dialog)

    def save_profile(e: ft.ControlEvent) -> None:
        new_name = (name_field.value or "").strip()
        new_bio = (bio_field.value or "").strip()

        if len(new_name) < 2:
            name_field.error_text = "Escribe tu nombre"
            name_field.update()
            return

        if len(new_bio) > 500:
            bio_field.error_text = "Maximo 500 caracteres"
            bio_field.update()
            return

        try:
            updated_user = user_service.update_profile(
                name=new_name,
                bio=new_bio,
                include_bio=True,
            )
            state.set_user(updated_user)
            close_dialog()
            show_success(page, "Perfil actualizado")
            page.go("/profile")
        except ApiError as error:
            show_error(page, error.message)

    edit_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Editar perfil", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        content=ft.Container(
            width=340,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[name_field, bio_field],
            ),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.TextButton("Guardar", on_click=save_profile),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_edit_dialog(e: ft.ControlEvent) -> None:
        name_field.error_text = None
        bio_field.error_text = None
        page.open(edit_dialog)

    def placeholder_tile() -> ft.Container:
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#CDE9F8", "#EAF6FC"],
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=46,
                        height=22,
                        bgcolor="#FFFFFF",
                        border_radius=14,
                        left=14,
                        top=18,
                    ),
                    ft.Container(
                        width=26,
                        height=26,
                        bgcolor="#FFFFFF",
                        border_radius=13,
                        left=26,
                        top=8,
                    ),
                    ft.Container(
                        width=10000,
                        height=42,
                        bgcolor="#A8D06A",
                        border_radius=ft.border_radius.only(top_left=40, top_right=10),
                        left=0,
                        bottom=0,
                    ),
                    ft.Container(
                        width=10000,
                        height=26,
                        bgcolor="#5E9E13",
                        border_radius=ft.border_radius.only(top_left=30, top_right=60),
                        left=0,
                        bottom=0,
                    ),
                ]
            ),
        )

    def new_post_tile() -> ft.Container:
        return ft.Container(
            bgcolor="#8A8A8A",
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.ADD, size=46, color=Colors.BRAND_DARK),
            on_click=lambda e: show_error(page, "Publicar aun no esta implementado"),
            ink=True,
        )

    def posts_grid() -> ft.GridView:
        tiles: list[ft.Control] = [new_post_tile()]
        tiles.extend(placeholder_tile() for _ in range(8))

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
            alignment=ft.alignment.center,
            padding=40,
            content=ft.Text(message, size=TextSizes.BODY, color=Colors.TEXT_MUTED),
        )

    tabs = ft.Tabs(
        selected_index=0,
        label_color=Colors.TEXT_PRIMARY,
        unselected_label_color=Colors.TEXT_MUTED,
        indicator_color=Colors.BRAND_DARK,
        indicator_thickness=3,
        divider_color=ft.Colors.TRANSPARENT,
        tabs=[
            ft.Tab(text="Publicaciones", content=posts_grid()),
            ft.Tab(text="Portafolios", content=empty_tab("Todavia no tienes portafolios")),
        ],
        expand=True,
    )

    def on_nav_change(e: ft.ControlEvent) -> None:
        index = e.control.selected_index
        if index == 3:
            return
        names = {0: "El feed", 1: "La busqueda", 2: "Los mensajes"}
        show_error(page, f"{names.get(index, 'Esa seccion')} aun no esta implementado")
        e.control.selected_index = 3
        e.control.update()

    return ft.View(
        route="/profile",
        padding=0,
        spacing=0,
        navigation_bar=bottom_nav(selected=3, on_change=on_nav_change),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    header,
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=Sizes.PAGE_PADDING, vertical=14),
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
                                        ft.Container(
                                            expand=True,
                                            content=ft.Text(
                                                user.get("bio")
                                                or "Agrega una presentacion para que otros "
                                                "artistas sepan quien eres.",
                                                size=TextSizes.BODY,
                                                color=(
                                                    Colors.TEXT_BODY
                                                    if user.get("bio")
                                                    else Colors.TEXT_MUTED
                                                ),
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT_SQUARE,
                                            icon_color=Colors.BRAND_DARK,
                                            icon_size=24,
                                            tooltip="Editar nombre y presentacion",
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
                        padding=ft.padding.symmetric(horizontal=8),
                    ),
                ],
            )
        ],
    )
