from __future__ import annotations
from typing import Callable

import flet as ft

from style.theme import Colors, TextSizes

ICON_BG = "#E6E6E6"


def settings_row(
    icon: str,
    label: str | ft.Control,
    *,
    on_click: Callable | None = None,
    trailing: ft.Control | None = None,
    enabled: bool = True,
    danger: bool = False,
    show_chevron: bool = True,
) -> ft.Container:
    if danger:
        circle_bg = Colors.BRAND_RED
        icon_color = Colors.TEXT_ON_DARK
        text_color = Colors.BRAND_RED
    elif enabled:
        circle_bg = ICON_BG
        icon_color = Colors.TEXT_PRIMARY
        text_color = Colors.TEXT_BODY
    else:
        circle_bg = "#F0F0F0"
        icon_color = Colors.TEXT_MUTED
        text_color = Colors.TEXT_MUTED

    if trailing is None and show_chevron and not danger:
        trailing = ft.Icon(
            ft.Icons.CHEVRON_RIGHT,
            size=22,
            color=Colors.TEXT_MUTED if enabled else "#D5D5D5",
        )

    controls: list[ft.Control] = [
        ft.Container(
            content=ft.Icon(icon, size=20, color=icon_color),
            width=38,
            height=38,
            bgcolor=circle_bg,
            border_radius=19,
            alignment=ft.alignment.center,
        ),
        ft.Container(
            expand=True,
            content=(
                label
                if isinstance(label, ft.Control)
                else ft.Text(label, size=TextSizes.BODY, color=text_color)
            ),
        ),
    ]

    if trailing is not None:
        controls.append(trailing)

    return ft.Container(
        content=ft.Row(controls=controls, spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=4, vertical=10),
        on_click=on_click,
        ink=on_click is not None,
        border_radius=8,
    )


def section_title(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(text, size=TextSizes.SUBTITLE, color=Colors.TEXT_PRIMARY),
        padding=ft.padding.only(top=18, bottom=6, left=4),
    )


def screen_header(title: str, on_back: Callable) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_IOS_NEW,
                            icon_size=20,
                            icon_color=Colors.TEXT_PRIMARY,
                            tooltip="Volver",
                            on_click=on_back,
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                title,
                                size=22,
                                color=Colors.TEXT_PRIMARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ),
                        ft.Container(width=48),
                    ],
                ),
                ft.Divider(height=1, thickness=1, color="#E4E4E4"),
            ],
        ),
        padding=ft.padding.only(top=6),
    )
