from __future__ import annotations

import flet as ft

from components.feedback import confirm_dialog, show_error, show_success
from components.settings_row import screen_header, settings_row
from context.app_state import AppState
from services import post_service
from services.api_client import ApiError
from style.theme import Colors, Sizes

async def view(page: ft.Page, state: AppState, post_id: int) -> ft.View:
    ruta = f"/post/{post_id}/settings"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        publicacion = await post_service.get_post(post_id)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route("/profile")
        return ft.View(route=ruta, controls=[])

    if not publicacion.get("can_edit"):
        await page.push_route(f"/post/{post_id}")
        return ft.View(route=ruta, controls=[])

    async def volver(e) -> None:
        await page.push_route(f"/post/{post_id}")

    async def editar(e) -> None:
        await page.push_route(f"/post/{post_id}/edit")

    async def eliminar_de_verdad(cerrar) -> None:
        try:
            await post_service.delete_post(post_id)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Publicacion eliminada")
        await page.push_route("/profile")

    def eliminar(e) -> None:
        confirm_dialog(
            page,
            title="Eliminar publicacion",
            message=(
                "Esta publicacion, sus archivos y todos sus comentarios se "
                "eliminaran para siempre. Esta accion no se puede deshacer."
            ),
            confirm_text="Eliminar",
            on_confirm=eliminar_de_verdad,
            danger=True,
        )

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
                    screen_header("Configuracion de Publicacion", volver),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=Sizes.PAGE_PADDING, vertical=10
                        ),
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                settings_row(
                                    ft.Icons.EDIT,
                                    "Editar Publicacion",
                                    on_click=editar,
                                ),
                                settings_row(
                                    ft.Icons.CLOSE,
                                    "Eliminar publicacion",
                                    on_click=eliminar,
                                    danger=True,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
