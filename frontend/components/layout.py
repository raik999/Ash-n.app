from __future__ import annotations

import flet as ft

from style.theme import Colors, Sizes, page_gradient


def screen(
    *controls: ft.Control,
    scroll: bool = True,
    spacing: int = 0,
    vertical_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START,
    padding: int | None = None,
) -> ft.Container:
    content_column = ft.Column(
        controls=list(controls),
        spacing=spacing,
        alignment=vertical_alignment,
        scroll=ft.ScrollMode.AUTO if scroll else None,
        expand=True,
    )

    return ft.Container(
        content=ft.Container(
            content=content_column,
            width=Sizes.CONTENT_MAX_WIDTH,
            padding=ft.padding.symmetric(
                horizontal=Sizes.PAGE_PADDING if padding is None else padding,
            ),
            expand=True,
        ),
        alignment=ft.alignment.top_center,
        gradient=page_gradient(),
        expand=True,
    )


def full_width(control: ft.Control) -> ft.Row:
    control.expand = True
    return ft.Row(controls=[control])


def vspace(height: int) -> ft.Container:
    return ft.Container(height=height)


def bottom_nav(selected: int = 3, on_change=None) -> ft.NavigationBar:
    return ft.NavigationBar(
        selected_index=selected,
        bgcolor=Colors.PEACH_SOFT,
        indicator_color=ft.Colors.TRANSPARENT,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, label="Inicio"),
            ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="Buscar"),
            ft.NavigationBarDestination(icon=ft.Icons.CHAT_BUBBLE_OUTLINE, label="Mensajes"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, label="Perfil"),
        ],
    )
