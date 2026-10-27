from __future__ import annotations

from typing import Any

import flet as ft

from components.feedback import avatar_view, show_error
from components.layout import bottom_nav, safe_update
from components.post_media import media_carousel
from components.tag_chip import display_chip
from context.app_state import AppState
from services import post_service
from services.api_client import ApiError, api
from style.theme import Colors, Fonts, Sizes, TextSizes

async def view(page: ft.Page, state: AppState, post_id: int) -> ft.View:
    ruta = f"/post/{post_id}"

    try:
        publicacion: dict[str, Any] = await post_service.get_post(post_id)
    except ApiError as error:
        return ft.View(
            route=ruta,
            padding=0,
            bgcolor=Colors.BACKGROUND,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ft.Container(
                            padding=ft.Padding.only(left=6, top=10),
                            content=ft.IconButton(
                                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                                icon_size=20,
                                icon_color=Colors.TEXT_PRIMARY,
                                on_click=lambda e: None,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                error.message,
                                size=TextSizes.BODY,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ],
                )
            ],
        )

    autor = publicacion["author"]
    soy_el_autor = bool(publicacion.get("can_edit"))

    async def volver(e) -> None:
        await page.push_route("/profile")

    async def ir_a_comentarios(e) -> None:
        await page.push_route(f"/post/{post_id}/comments")

    async def ir_a_configuracion(e) -> None:
        await page.push_route(f"/post/{post_id}/settings")

    async def ir_al_perfil(e) -> None:
        mio = (state.user or {}).get("username")
        if autor["username"] == mio:
            await page.push_route("/profile")
        else:
            await page.push_route(f"/user/{autor['username']}")

    estado = {
        "liked": bool(publicacion.get("liked_by_me")),
        "count": int(publicacion.get("likes_count") or 0),
    }

    corazon = ft.IconButton(
        icon=ft.Icons.FAVORITE,
        icon_size=30,
        icon_color=Colors.BRAND_RED if estado["liked"] else "#B5B5B5",
        tooltip="Me gusta",
    )
    contador_likes = ft.Text(
        str(estado["count"]),
        size=TextSizes.SMALL,
        color=Colors.TEXT_MUTED,
        text_align=ft.TextAlign.CENTER,
    )

    async def alternar_like(e) -> None:
        if not state.is_authenticated:
            show_error(page, "Inicia sesion para dar me gusta")
            return

        try:
            if estado["liked"]:
                respuesta = await post_service.unlike(post_id)
            else:
                respuesta = await post_service.like(post_id)
        except ApiError as error:
            show_error(page, error.message)
            return

        estado["liked"] = bool(respuesta["liked_by_me"])
        estado["count"] = int(respuesta["likes_count"])

        corazon.icon_color = Colors.BRAND_RED if estado["liked"] else "#B5B5B5"
        contador_likes.value = str(estado["count"])
        safe_update(corazon, contador_likes)

    corazon.on_click = alternar_like

    acciones: list[ft.Control] = [
        ft.Column(
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[corazon, contador_likes],
        ),
        ft.Column(
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                    icon_size=26,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Comentarios",
                    on_click=ir_a_comentarios,
                ),
                ft.Text(
                    str(publicacion.get("comments_count") or 0),
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_MUTED,
                ),
            ],
        ),
        ft.Container(expand=True),
    ]

    if soy_el_autor:
        acciones.append(
            ft.IconButton(
                icon=ft.Icons.MORE_HORIZ,
                icon_size=28,
                icon_color=Colors.TEXT_PRIMARY,
                tooltip="Configuracion de la publicacion",
                on_click=ir_a_configuracion,
            )
        )

    archivos = publicacion.get("files") or []
    etiquetas = publicacion.get("tags") or []
    descripcion = publicacion.get("description")

    cuerpo: list[ft.Control] = []

    cuerpo.append(
        ft.Container(
            bgcolor=Colors.SURFACE,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            content=ft.Text(
                publicacion.get("title") or "Sin titulo",
                size=TextSizes.BODY,
                color=Colors.TEXT_BODY if publicacion.get("title") else Colors.TEXT_MUTED,
            ),
        )
    )

    if archivos:
        cuerpo.append(media_carousel(archivos, alto=330))

    cuerpo.append(
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=acciones,
            ),
        )
    )

    if etiquetas:
        cuerpo.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=14),
                content=ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[display_chip(t) for t in etiquetas],
                ),
            )
        )

    cuerpo.append(
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            content=ft.Text(
                f"Descripcion: {descripcion}" if descripcion else "Sin descripcion",
                size=TextSizes.BODY,
                color=Colors.TEXT_BODY if descripcion else Colors.TEXT_MUTED,
            ),
        )
    )

    cuerpo.append(
        ft.Container(
            margin=ft.Margin.symmetric(horizontal=10, vertical=8),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            bgcolor=Colors.SURFACE,
            border_radius=10,
            on_click=ir_al_perfil,
            ink=True,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        content=avatar_view(api.absolute_url(autor.get("avatar_url")), 42),
                    ),
                    ft.Text(
                        f"@{autor['username']}",
                        size=TextSizes.BODY,
                        color=Colors.TEXT_PRIMARY,
                        font_family=Fonts.BODY,
                    ),
                ],
            ),
        )
    )

    return ft.View(
        route=ruta,
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=3),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(left=4, top=6),
                        content=ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK_IOS_NEW,
                                    icon_size=20,
                                    icon_color=Colors.TEXT_PRIMARY,
                                    tooltip="Volver",
                                    on_click=volver,
                                )
                            ]
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                            controls=cuerpo,
                        ),
                    ),
                ],
            )
        ],
    )
