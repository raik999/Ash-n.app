from __future__ import annotations

import flet as ft

from components.feedback import confirm_dialog, show_error, show_success
from components.settings_row import screen_header, settings_row
from context.app_state import AppState
from services import chat_service
from services.api_client import ApiError
from style.theme import Colors, Sizes, TextSizes

async def view(page: ft.Page, state: AppState, chat_id: int) -> ft.View:
    ruta = f"/chat/{chat_id}/settings"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        chat = await chat_service.get_chat(chat_id)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route("/chats")
        return ft.View(route=ruta, controls=[])

    otro = chat["other"]

    async def volver(e) -> None:
        await page.push_route(f"/chat/{chat_id}")

    async def eliminar_de_verdad(cerrar) -> None:
        try:
            await chat_service.delete_chat(chat_id)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Chat eliminado")
        await page.push_route("/chats")

    def eliminar(e) -> None:
        confirm_dialog(
            page,
            title="Eliminar chat",
            message=(
                f"Esta conversacion con {otro['username']} y todos sus "
                "mensajes se eliminaran para siempre, TAMBIEN PARA LA OTRA "
                "PERSONA. Esta accion no se puede deshacer."
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
                    screen_header("Configuracion del Chat", volver),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=Sizes.PAGE_PADDING, vertical=10
                        ),
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                settings_row(
                                    ft.Icons.PERSON_OUTLINE,
                                    otro["username"],
                                    on_click=None,
                                    show_chevron=False,
                                ),
                                settings_row(
                                    ft.Icons.NOTIFICATIONS_OFF_OUTLINED,
                                    "Silenciar chat",
                                    on_click=None,
                                    enabled=False,
                                ),
                                settings_row(
                                    ft.Icons.BLOCK,
                                    "Bloquear usuario",
                                    on_click=None,
                                    enabled=False,
                                ),
                                ft.Container(height=10),
                                settings_row(
                                    ft.Icons.CLOSE,
                                    "Eliminar chat",
                                    on_click=eliminar,
                                    danger=True,
                                ),
                                ft.Container(height=6),
                                ft.Text(
                                    "Al eliminar el chat desaparece para los "
                                    "dos participantes.",
                                    size=TextSizes.SMALL,
                                    color=Colors.TEXT_MUTED,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
