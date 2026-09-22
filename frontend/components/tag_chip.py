from __future__ import annotations

from typing import Any, Callable

import flet as ft

from style.theme import Colors, TextSizes


def _chip_label(name: str, size: int = TextSizes.LABEL) -> ft.Text:
    return ft.Text(
        f"#{name}",
        size=size,
        color=Colors.TEXT_ON_DARK,
        weight=ft.FontWeight.W_500,
    )


def selectable_chip(
    tag: dict[str, Any],
    *,
    selected: bool,
    on_toggle: Callable[[dict[str, Any]], None],
) -> ft.Container:
    color = tag.get("color") or Colors.CHIP_FALLBACK

    return ft.Container(
        content=_chip_label(tag["name"]),
        bgcolor=color,
        opacity=0.45 if selected else 1.0,
        padding=ft.padding.symmetric(horizontal=16, vertical=9),
        border_radius=20,
        on_click=lambda e: on_toggle(tag),
        ink=True,
        tooltip=f"Tocar para {'quitar' if selected else 'agregar'}",
        animate_opacity=150,
    )


def removable_chip(
    tag: dict[str, Any],
    *,
    on_remove: Callable[[dict[str, Any]], None],
) -> ft.Container:
    color = tag.get("color") or Colors.CHIP_FALLBACK

    return ft.Container(
        content=ft.Row(
            tight=True,
            spacing=0,
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CLOSE,
                        size=16,
                        color=Colors.BRAND_DARK,
                    ),
                    bgcolor="#8A8A8A",
                    width=30,
                    height=30,
                    border_radius=20,
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=_chip_label(tag["name"]),
                    bgcolor=color,
                    padding=ft.padding.symmetric(horizontal=14, vertical=7),
                    border_radius=20,
                    margin=ft.margin.only(left=-15),
                ),
            ],
        ),
        on_click=lambda e: on_remove(tag),
        ink=False,
        tooltip="Quitar esta especialidad",
    )


def display_chip(tag: dict[str, Any]) -> ft.Container:
    return ft.Container(
        content=_chip_label(tag["name"], size=TextSizes.SMALL + 1),
        bgcolor=tag.get("color") or Colors.CHIP_FALLBACK,
        padding=ft.padding.symmetric(horizontal=14, vertical=7),
        border_radius=20,
    )
