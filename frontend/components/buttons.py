from __future__ import annotations

import flet as ft

from style.theme import Colors, Sizes, TextSizes


def primary_button(text: str, on_click, *, width: int | None = None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Text(
            text,
            size=TextSizes.SUBTITLE,
            color=Colors.TEXT_ON_DARK,
            weight=ft.FontWeight.W_500,
        ),
        on_click=on_click,
        width=width,
        height=Sizes.BUTTON_HEIGHT,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: Colors.BRAND_DARK,
                ft.ControlState.DISABLED: Colors.TEXT_MUTED,
            },
            color=Colors.TEXT_ON_DARK,
            shape=ft.RoundedRectangleBorder(radius=Sizes.BUTTON_RADIUS),
            elevation=0,
            padding=ft.padding.symmetric(horizontal=20),
        ),
    )


def link_button(text: str, on_click, *, bold: bool = True, size: int | None = None) -> ft.TextButton:
    return ft.TextButton(
        content=ft.Text(
            text,
            size=size or TextSizes.BODY,
            color=Colors.TEXT_PRIMARY,
            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
            style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
        ),
        on_click=on_click,
        style=ft.ButtonStyle(
            overlay_color=ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
        ),
    )


def loading_button(text: str, on_click) -> tuple[ft.ElevatedButton, callable]:
    label = ft.Text(
        text,
        size=TextSizes.SUBTITLE,
        color=Colors.TEXT_ON_DARK,
        weight=ft.FontWeight.W_500,
    )

    spinner = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        color=Colors.TEXT_ON_DARK,
        visible=False,
    )

    button = ft.ElevatedButton(
        content=ft.Row(
            controls=[spinner, label],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            tight=True,
        ),
        on_click=on_click,
        height=Sizes.BUTTON_HEIGHT,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: Colors.BRAND_DARK,
                ft.ControlState.DISABLED: Colors.TEXT_MUTED,
            },
            color=Colors.TEXT_ON_DARK,
            shape=ft.RoundedRectangleBorder(radius=Sizes.BUTTON_RADIUS),
            elevation=0,
        ),
    )

    def set_loading(is_loading: bool) -> None:
        spinner.visible = is_loading
        button.disabled = is_loading
        if button.page:
            button.update()

    return button, set_loading
