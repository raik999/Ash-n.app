from __future__ import annotations
from typing import Callable

import flet as ft

from style.responsive import pantalla
from style.theme import Colors, Fonts, Radius, Sizes, Space, TextSizes

def settings_row(
    icon: str,
    label: str | ft.Control,
    *,
    on_click: Callable | None = None,
    trailing: ft.Control | None = None,
    enabled: bool = True,
    danger: bool = False,
    show_chevron: bool = True,
    subtitulo: str | None = None,
) -> ft.Container:
    medidas = pantalla()

    if danger:
        circle_bg = Colors.BRAND_RED
        icon_color = Colors.TEXT_ON_DARK
        text_color = Colors.BRAND_RED
    elif enabled:
        circle_bg = Colors.SURFACE_STRONG
        icon_color = Colors.TEXT_PRIMARY
        text_color = Colors.TEXT_BODY
    else:
        circle_bg = Colors.DISABLED_BG
        icon_color = Colors.DISABLED_FG
        text_color = Colors.DISABLED_FG

    if trailing is None and show_chevron and not danger and on_click is not None:
        trailing = ft.Icon(
            ft.Icons.CHEVRON_RIGHT,
            size=Sizes.ICON_MD,
            color=Colors.TEXT_MUTED if enabled else Colors.DISABLED_FG,
        )

    textos: list[ft.Control] = [
        label
        if isinstance(label, ft.Control)
        else ft.Text(
            label,
            size=medidas.texto(TextSizes.BODY),
            color=text_color,
        )
    ]

    if subtitulo:
        textos.append(
            ft.Text(
                subtitulo,
                size=medidas.texto(TextSizes.SMALL),
                color=Colors.TEXT_MUTED if enabled else Colors.DISABLED_FG,
            )
        )

    controls: list[ft.Control] = [
        ft.Container(
            content=ft.Icon(icon, size=Sizes.ICON_SM + 2, color=icon_color),
            width=40,
            height=40,
            bgcolor=circle_bg,
            border_radius=Radius.PILL,
            alignment=ft.Alignment.CENTER,
        ),
        ft.Container(
            expand=True,
            content=ft.Column(spacing=1, tight=True, controls=textos),
        ),
    ]

    if trailing is not None:
        controls.append(trailing)

    return ft.Container(
        content=ft.Row(
            controls=controls,
            spacing=Space.SM + 2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        height=Sizes.TOUCH_MIN + 8,
        padding=ft.Padding.symmetric(horizontal=Space.XS),
        on_click=on_click if enabled else None,
        ink=on_click is not None and enabled,
        border_radius=Radius.SM,
    )

def section_title(text: str) -> ft.Container:
    medidas = pantalla()

    return ft.Container(
        content=ft.Text(
            text,
            size=medidas.texto(TextSizes.LABEL),
            color=Colors.TEXT_MUTED,
            weight=ft.FontWeight.W_600,
            style=ft.TextStyle(letter_spacing=0.6),
        ),
        padding=ft.Padding.only(top=Space.LG, bottom=Space.XS, left=Space.XS),
    )

def screen_header(
    title: str,
    on_back: Callable,
    *,
    acciones: list[ft.Control] | None = None,
    principal: ft.Control | None = None,
    con_linea: bool = True,
) -> ft.Container:
    medidas = pantalla()

    derecha: list[ft.Control] = list(acciones or [])
    if not derecha:
        derecha = [ft.Container(width=Sizes.TOUCH_MIN)]

    centro = principal or ft.Text(
        title,
        size=medidas.texto(TextSizes.SUBTITLE + 2),
        color=Colors.TEXT_PRIMARY,
        font_family=Fonts.HEADING,
        text_align=ft.TextAlign.CENTER,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    fila = ft.Row(
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                icon_size=Sizes.ICON_SM,
                icon_color=Colors.TEXT_PRIMARY,
                tooltip="Volver",
                on_click=on_back,
                width=Sizes.TOUCH_MIN,
                height=Sizes.TOUCH_MIN,
            ),
            ft.Container(expand=True, content=centro),
            *derecha,
        ],
    )

    controles: list[ft.Control] = [fila]
    if con_linea:
        controles.append(
            ft.Divider(height=1, thickness=1, color=Colors.DIVIDER)
        )

    return ft.Container(
        content=ft.Column(spacing=0, controls=controles),
        padding=ft.Padding.only(top=Space.XXS),
    )

def encabezado_principal(
    titulo: str,
    *,
    acciones: list[ft.Control] | None = None,
) -> ft.Container:
    medidas = pantalla()

    return ft.Container(
        padding=ft.Padding.only(
            left=medidas.padding,
            right=Space.XS,
            top=Space.SM,
            bottom=Space.XS,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    titulo,
                    size=medidas.texto(TextSizes.HEADING + 2),
                    color=Colors.TEXT_PRIMARY,
                    font_family=Fonts.HEADING,
                    style=ft.TextStyle(letter_spacing=-0.4),
                ),
                *(acciones or []),
            ],
        ),
    )

def boton_barra(
    icon: str,
    tooltip: str,
    on_click: Callable | None = None,
    *,
    color: str | None = None,
) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        icon_size=Sizes.ICON_MD,
        icon_color=color or Colors.TEXT_PRIMARY,
        tooltip=tooltip,
        on_click=on_click,
        width=Sizes.TOUCH_MIN,
        height=Sizes.TOUCH_MIN,
    )
