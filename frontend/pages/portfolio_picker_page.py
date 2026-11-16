from __future__ import annotations

from functools import partial

import flet as ft

from components.buttons import loading_button
from components.feedback import show_error, show_success
from components.layout import estado_vacio, safe_update
from components.post_media import grid_cell
from components.profile_scroll import grilla_fija
from components.settings_row import screen_header
from context.app_state import AppState
from services import portfolio_service, post_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, Radius, Sizes, Space, TextSizes

async def view(page: ft.Page, state: AppState, portfolio_id: int) -> ft.View:
    ruta = f"/portfolio/{portfolio_id}/posts"
    medidas = pantalla()

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        portafolio = await portfolio_service.get_portfolio(portfolio_id)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route("/profile")
        return ft.View(route=ruta, controls=[])

    if not portafolio.get("can_edit"):
        await page.push_route(f"/portfolio/{portfolio_id}")
        return ft.View(route=ruta, controls=[])

    try:
        mias = await post_service.list_user_posts(state.user["username"])
    except ApiError as error:
        show_error(page, error.message)
        mias = []

    mias = [p for p in mias if p.get("published", True)]

    dentro: set[int] = {p["id"] for p in (portafolio.get("posts") or [])}

    contador = ft.Text(
        "",
        size=medidas.texto(TextSizes.LABEL),
        color=Colors.TEXT_MUTED,
    )

    def pintar_contador() -> None:
        contador.value = (
            f"{len(dentro)} {'elegida' if len(dentro) == 1 else 'elegidas'} "
            f"de {len(mias)}"
        )
        safe_update(contador)

    marcas: dict[int, ft.Container] = {}

    def pintar_celda(post_id: int) -> None:
        marca = marcas.get(post_id)
        if marca is None:
            return
        marca.visible = post_id in dentro
        safe_update(marca)

    def alternar(post_id: int):
        def manejar(e) -> None:
            if post_id in dentro:
                dentro.discard(post_id)
            else:
                dentro.add(post_id)
            pintar_celda(post_id)
            pintar_contador()

        return manejar

    def celda(post: dict) -> ft.Control:
        post_id = post["id"]

        marca = ft.Container(
            width=26,
            height=26,
            bgcolor=Colors.BRAND_DARK,
            border_radius=Radius.PILL,
            alignment=ft.Alignment.CENTER,
            visible=post_id in dentro,
            content=ft.Icon(ft.Icons.CHECK, size=16, color=Colors.TEXT_ON_DARK),
        )
        marcas[post_id] = marca

        candado = (
            ft.Container(
                width=24,
                height=24,
                bgcolor=Colors.BRAND_DARK,
                border_radius=Radius.PILL,
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(
                    ft.Icons.LOCK, size=13, color=Colors.TEXT_ON_DARK
                ),
                tooltip="Esta publicacion es privada: los demas no la van a ver aqui",
            )
            if post.get("is_private")
            else None
        )

        capas: list[ft.Control] = [
            grid_cell(post, alternar(post_id)),
            ft.Container(content=marca, right=4, top=4),
        ]
        if candado is not None:
            capas.append(ft.Container(content=candado, left=4, top=4))

        return ft.Stack(controls=capas)

    RELLENO = Space.XS

    if mias:
        cuerpo: ft.Control = grilla_fija(
            [celda(p) for p in mias],
            ancho_disponible=medidas.ancho - RELLENO * 2,
        )
    else:
        cuerpo = estado_vacio(
            ft.Icons.PHOTO_LIBRARY_OUTLINED,
            "Todavia no tienes publicaciones",
            "Publica algo primero y despues vas a poder organizarlo aqui.",
        )

    pintar_contador()

    async def guardar(e) -> None:
        cambiar_estado(True)
        try:
            await portfolio_service.set_posts(portfolio_id, sorted(dentro))
        except ApiError as error:
            show_error(page, error.message)
            return
        finally:
            cambiar_estado(False)

        show_success(page, "Portafolio actualizado")
        await page.push_route(f"/portfolio/{portfolio_id}")

    boton, cambiar_estado = loading_button("Guardar", guardar)

    async def volver(e) -> None:
        await page.push_route(f"/portfolio/{portfolio_id}")

    return ft.View(
        route=ruta,
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header("Organizar", volver),
                    ft.Container(
                        padding=ft.Padding.only(
                            left=medidas.padding,
                            right=medidas.padding,
                            top=Space.XS,
                            bottom=Space.XS,
                        ),
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        "Toca una publicacion para meterla o sacarla",
                                        size=medidas.texto(TextSizes.SMALL),
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ),
                                contador,
                            ]
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=RELLENO),
                        content=ft.Column(
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            controls=[cuerpo, ft.Container(height=Space.MD)],
                        ),
                    ),
                    ft.Container(
                        bgcolor=Colors.BACKGROUND,
                        border=ft.Border(top=ft.BorderSide(1, Colors.DIVIDER)),
                        padding=ft.Padding.symmetric(
                            horizontal=medidas.padding, vertical=Space.XS
                        ),
                        content=ft.Row(
                            controls=[ft.Container(expand=True, content=boton)]
                        ),
                    ),
                ],
            )
        ],
    )
