from __future__ import annotations

from typing import Any

import flet as ft

from services.api_client import api
from style.responsive import pantalla
from style.theme import Colors, Fonts, LineHeight, Radius, Sizes, Space, TextSizes

def tarjeta_de_portafolio(portafolio: dict[str, Any], on_click) -> ft.Container:
    medidas = pantalla()

    preview = portafolio.get("preview") or {}
    url = preview.get("thumb_url") or preview.get("url")

    banda: list[ft.Control] = []
    if url and preview.get("kind") == "image":
        lado = medidas.avatar(64)
        banda.append(
            ft.Image(
                src=api.absolute_url(url),
                width=lado,
                height=lado,
                fit=ft.BoxFit.COVER,
                cache_width=medidas.pixeles_para(lado),
            )
        )

    cantidad = int(portafolio.get("posts_count") or 0)
    detalle = f"{cantidad} {'publicacion' if cantidad == 1 else 'publicaciones'}"

    titulo_y_candado: list[ft.Control] = [
        ft.Text(
            portafolio.get("title") or "",
            size=medidas.texto(TextSizes.BODY),
            color=Colors.TEXT_PRIMARY,
            weight=ft.FontWeight.W_600,
            font_family=Fonts.HEADING,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
    ]

    if portafolio.get("is_private"):
        titulo_y_candado.append(
            ft.Icon(ft.Icons.LOCK, size=14, color=Colors.TEXT_MUTED)
        )

    textos: list[ft.Control] = [
        ft.Row(spacing=Space.XXS + 2, tight=True, controls=titulo_y_candado)
    ]

    descripcion = (portafolio.get("description") or "").strip()
    if descripcion:
        textos.append(
            ft.Text(
                descripcion,
                size=medidas.texto(TextSizes.SMALL),
                color=Colors.TEXT_MUTED,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )

    textos.append(
        ft.Text(detalle, size=medidas.texto(TextSizes.SMALL), color=Colors.TEXT_FAINT)
    )

    lado = medidas.avatar(64)

    return ft.Container(
        bgcolor=Colors.SURFACE,
        border_radius=Radius.MD,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        ink=True,
        on_click=on_click,
        tooltip=f"Abrir {portafolio.get('title') or 'el portafolio'}",
        content=ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=lado,
                    height=lado,
                    bgcolor=portafolio.get("color") or Colors.CHIP_FALLBACK,
                    alignment=ft.Alignment.CENTER,
                    content=(
                        banda[0]
                        if banda
                        else ft.Icon(
                            ft.Icons.FOLDER_OUTLINED,
                            size=Sizes.ICON_LG,
                            color=Colors.TEXT_ON_DARK,
                        )
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(
                        horizontal=Space.SM, vertical=Space.XS
                    ),
                    content=ft.Column(spacing=1, tight=True, controls=textos),
                ),
                ft.Container(
                    padding=ft.Padding.only(right=Space.XS),
                    content=ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        size=Sizes.ICON_MD,
                        color=Colors.TEXT_MUTED,
                    ),
                ),
            ],
        ),
    )

def tarjeta_de_crear(on_click) -> ft.Container:
    medidas = pantalla()

    return ft.Container(
        border=ft.Border.all(1, Colors.DIVIDER),
        border_radius=Radius.MD,
        ink=True,
        on_click=on_click,
        tooltip="Crear un portafolio",
        padding=ft.Padding.symmetric(horizontal=Space.SM, vertical=Space.MD),
        content=ft.Row(
            spacing=Space.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=40,
                    height=40,
                    bgcolor=Colors.SURFACE_STRONG,
                    border_radius=Radius.PILL,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.ADD, size=Sizes.ICON_MD, color=Colors.TEXT_PRIMARY
                    ),
                ),
                ft.Container(
                    expand=True,
                    content=ft.Text(
                        "Crear un portafolio",
                        size=medidas.texto(TextSizes.BODY),
                        color=Colors.TEXT_PRIMARY,
                    ),
                ),
            ],
        ),
    )
