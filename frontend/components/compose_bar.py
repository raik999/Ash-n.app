from __future__ import annotations
from typing import Callable

import flet as ft

from components.layout import safe_update
from style.responsive import pantalla
from style.theme import Colors, Radius, Sizes, Space, TextSizes

def barra_de_escritura(
    *,
    hint: str,
    maximo: int,
    al_enviar: Callable,
    tooltip_enviar: str = "Enviar",
) -> tuple[ft.Container, ft.TextField]:
    medidas = pantalla()

    campo = ft.TextField(
        hint_text=hint,
        border=ft.InputBorder.NONE,
        filled=False,
        dense=True,
        expand=True,
        max_length=maximo,
        multiline=True,
        min_lines=1,
        max_lines=4,
        text_size=medidas.texto(TextSizes.BODY),
        text_style=ft.TextStyle(color=Colors.TEXT_BODY, height=1.3),
        hint_style=ft.TextStyle(color=Colors.TEXT_FAINT),
        cursor_color=Colors.TEXT_PRIMARY,
        counter="",
    )

    def limpiar(e=None) -> None:
        campo.value = ""
        boton_borrar.visible = False
        safe_update(campo, boton_borrar)

    boton_borrar = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_size=Sizes.ICON_SM,
        icon_color=Colors.TEXT_MUTED,
        tooltip="Borrar lo escrito",
        on_click=limpiar,
        visible=False,
        width=Sizes.TOUCH_MIN - 8,
        height=Sizes.TOUCH_MIN - 8,
    )

    def al_escribir(e) -> None:
        hay_texto = bool((campo.value or "").strip())
        if boton_borrar.visible != hay_texto:
            boton_borrar.visible = hay_texto
            safe_update(boton_borrar)

    campo.on_change = al_escribir
    campo.on_submit = al_enviar

    boton_enviar = ft.Container(
        width=38,
        height=38,
        bgcolor=Colors.BRAND_DARK,
        border_radius=Radius.PILL,
        alignment=ft.Alignment.CENTER,
        ink=True,
        on_click=al_enviar,
        tooltip=tooltip_enviar,
        content=ft.Icon(
            ft.Icons.ARROW_UPWARD,
            size=Sizes.ICON_SM,
            color=Colors.TEXT_ON_DARK,
        ),
    )

    barra = ft.Container(
        bgcolor=Colors.BACKGROUND,
        padding=ft.Padding.only(
            left=medidas.padding,
            right=medidas.padding,
            top=Space.XS,
            bottom=Space.XS,
        ),
        border=ft.Border(top=ft.BorderSide(1, Colors.DIVIDER)),
        content=ft.Container(
            bgcolor=Colors.SURFACE_STRONG,
            border_radius=Radius.PILL,
            padding=ft.Padding.only(left=Space.MD, right=Space.XXS + 1),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Space.XXS,
                controls=[campo, boton_borrar, boton_enviar],
            ),
        ),
    )

    return barra, campo

def vaciar(campo: ft.TextField) -> None:
    campo.value = ""
    if campo.on_change is not None:
        campo.on_change(None)
    safe_update(campo)
