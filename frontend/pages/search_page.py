from __future__ import annotations
from typing import Any

import flet as ft

from components.feedback import avatar_view, show_error
from components.layout import bottom_nav
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, Sizes, TextSizes

BLOCK_COLORS = [
    "#2E9E27",
    "#F0743C",
    "#BE2EDD",
    "#4D7CFE",
    "#F03C3C",
    "#17B8C4",
    "#E8A317",
    "#E0457B",
]

LEFT_HEIGHTS = [210, 190, 230]
RIGHT_HEIGHTS = [250, 200, 180]


def plural(name: str) -> str:
    if not name:
        return name
    return name + "s" if name[-1].lower() in "aeiou" else name + "es"


def safe_update(control: ft.Control) -> None:
    if control.page:
        control.update()


def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        page.go("/login")
        return ft.View(route="/search", controls=[])

    ui: dict[str, Any] = {"mode": "inicial", "results": []}

    search_field = ft.TextField(
        hint_text="",
        border=ft.InputBorder.NONE,
        filled=False,
        dense=True,
        content_padding=ft.padding.symmetric(vertical=10),
        text_size=TextSizes.BODY,
        text_style=ft.TextStyle(color=Colors.TEXT_PRIMARY),
        cursor_color=Colors.TEXT_PRIMARY,
        on_submit=lambda e: do_search(),
        on_focus=lambda e: enter_recents(),
    )

    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK_IOS_NEW,
        icon_size=20,
        icon_color=Colors.TEXT_PRIMARY,
        tooltip="Volver",
        visible=False,
        on_click=lambda e: exit_search(),
    )

    search_bar = ft.Container(
        bgcolor="#D6D6D6",
        border_radius=22,
        height=46,
        expand=True,
        padding=ft.padding.only(left=16, right=4),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                ft.Container(expand=True, content=search_field),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=20,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Borrar",
                    on_click=lambda e: clear_text(),
                ),
                ft.Container(width=1, height=22, bgcolor="#8C8C8C"),
                ft.IconButton(
                    icon=ft.Icons.SEARCH,
                    icon_size=20,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Buscar",
                    on_click=lambda e: do_search(),
                ),
            ],
        ),
    )

    body = ft.Container(expand=True)

    def build_initial() -> ft.Control:
        try:
            tags = state.load_tags()
        except ApiError as error:
            show_error(page, error.message)
            tags = []

        left_column = ft.Column(spacing=10, expand=True)
        right_column = ft.Column(spacing=10, expand=True)

        for index, tag in enumerate(tags):
            is_left = index % 2 == 0
            column = left_column if is_left else right_column
            heights = LEFT_HEIGHTS if is_left else RIGHT_HEIGHTS

            column.controls.append(
                ft.Container(
                    height=heights[(index // 2) % len(heights)],
                    bgcolor=BLOCK_COLORS[index % len(BLOCK_COLORS)],
                    border_radius=4,
                    alignment=ft.alignment.center,
                    on_click=None,
                    content=ft.Text(
                        f"#{plural(tag['name'])}",
                        size=TextSizes.BODY,
                        color=Colors.TEXT_ON_DARK,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=10,
                    controls=[left_column, right_column],
                )
            ],
        )

    def build_recents() -> ft.Control:
        recents = state.load_recents()

        if not recents:
            return ft.Container(
                alignment=ft.alignment.center,
                padding=40,
                content=ft.Text(
                    "Todavia no has buscado nada",
                    size=TextSizes.BODY,
                    color=Colors.TEXT_MUTED,
                ),
            )

        rows: list[ft.Control] = [
            ft.Container(
                padding=ft.padding.only(left=4, bottom=6),
                content=ft.Text(
                    "Recientes",
                    size=TextSizes.SUBTITLE,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
            )
        ]
        rows.extend(recent_row(item) for item in recents)

        rows.append(ft.Container(height=24))
        rows.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.TextButton(
                        content=ft.Text(
                            "Eliminar búsquedas",
                            size=TextSizes.SUBTITLE,
                            color=Colors.TEXT_BODY,
                        ),
                        on_click=lambda e: wipe_recents(),
                        style=ft.ButtonStyle(
                            bgcolor="#D6D6D6",
                            shape=ft.RoundedRectangleBorder(radius=20),
                            padding=ft.padding.symmetric(horizontal=22, vertical=14),
                        ),
                    )
                ],
            )
        )

        return ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True, controls=rows)

    def build_results() -> ft.Control:
        text = (search_field.value or "").strip().lower()

        matching_recents = [
            item
            for item in state.load_recents()
            if item["kind"] == "query" and item["value"].lower().startswith(text)
        ]

        rows: list[ft.Control] = [recent_row(item) for item in matching_recents]
        rows.extend(user_row(user) for user in ui["results"])

        if not rows:
            return ft.Container(
                alignment=ft.alignment.top_center,
                padding=ft.padding.only(top=40),
                content=ft.Text(
                    "No se encontraron artistas",
                    size=TextSizes.BODY,
                    color=Colors.TEXT_MUTED,
                ),
            )

        return ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True, controls=rows)

    def circle_icon(icon: str) -> ft.Container:
        return ft.Container(
            content=ft.Icon(icon, size=20, color=Colors.TEXT_PRIMARY),
            width=44,
            height=44,
            bgcolor="#B8B8B8",
            border_radius=22,
            alignment=ft.alignment.center,
        )

    def row_shell(leading: ft.Control, label: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    leading,
                    ft.Text(label, size=TextSizes.BODY, color=Colors.TEXT_BODY),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=4, vertical=6),
            border_radius=8,
            ink=True,
            on_click=on_click,
        )

    def recent_row(item: dict[str, str]) -> ft.Container:
        if item["kind"] == "query":
            return row_shell(
                circle_icon(ft.Icons.SEARCH),
                item["value"],
                lambda e, v=item["value"]: repeat_search(v),
            )

        return row_shell(
            circle_icon(ft.Icons.PERSON),
            item["value"],
            lambda e, v=item["value"]: open_profile(v),
        )

    def user_row(user: dict[str, Any]) -> ft.Container:
        from services.api_client import api

        return row_shell(
            ft.Container(
                width=44,
                height=44,
                content=avatar_view(api.absolute_url(user.get("avatar_url")), 44),
            ),
            user["username"],
            lambda e, u=user["username"]: open_profile(u),
        )

    def render() -> None:
        mode = ui["mode"]

        if mode == "inicial":
            body.content = build_initial()
        elif mode == "recientes":
            body.content = build_recents()
        else:
            body.content = build_results()

        back_button.visible = mode != "inicial"

        safe_update(body)
        safe_update(back_button)

    def enter_recents() -> None:
        if ui["mode"] == "inicial":
            ui["mode"] = "recientes"
            render()

    def exit_search() -> None:
        search_field.value = ""
        ui["mode"] = "inicial"
        ui["results"] = []
        safe_update(search_field)
        render()

    def clear_text() -> None:
        search_field.value = ""
        safe_update(search_field)
        ui["mode"] = "recientes"
        ui["results"] = []
        render()

    def do_search() -> None:
        text = (search_field.value or "").strip()

        if not text:
            ui["mode"] = "recientes"
            render()
            return

        try:
            ui["results"] = user_service.search_users(text)
        except ApiError as error:
            show_error(page, error.message)
            ui["results"] = []

        ui["mode"] = "resultados"
        render()

        state.add_recent("query", text)

    def repeat_search(text: str) -> None:
        search_field.value = text
        safe_update(search_field)
        do_search()

    def open_profile(username: str) -> None:
        state.add_recent("user", username)
        page.go(f"/user/{username}")

    def wipe_recents() -> None:
        state.clear_recents()
        render()

    render()

    return ft.View(
        route="/search",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=1),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(left=6, right=Sizes.PAGE_PADDING, top=10, bottom=8),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                            controls=[back_button, search_bar],
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=Sizes.PAGE_PADDING),
                        content=body,
                    ),
                ],
            )
        ],
    )
