from __future__ import annotations

import flet as ft

from components.layout import bottom_nav
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from style.theme import Colors, Sizes


def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        page.go("/login")
        return ft.View(route="/settings", controls=[])

    user = state.user

    def go_back(e: ft.ControlEvent) -> None:
        page.go("/profile")

    def go_to_account(e: ft.ControlEvent) -> None:
        page.go("/settings/account")

    dark_mode_switch = ft.Switch(
        value=False,
        disabled=True,
        active_color=Colors.BRAND_DARK,
    )

    return ft.View(
        route="/settings",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(selected=3),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header("Configuración", go_back),
                    ft.Container(
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=Sizes.PAGE_PADDING, vertical=10),
                        content=ft.Column(
                            spacing=2,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                settings_row(
                                    ft.Icons.PERSON_OUTLINE,
                                    user.get("username", ""),
                                    on_click=go_to_account,
                                ),
                                settings_row(
                                    ft.Icons.ADD,
                                    "Nueva cuenta",
                                    on_click=None,
                                ),
                                section_title("Ajustes"),
                                settings_row(
                                    ft.Icons.DARK_MODE_OUTLINED,
                                    "Modo Oscuro",
                                    trailing=dark_mode_switch,
                                    on_click=None,
                                ),
                                settings_row(
                                    ft.Icons.REMOVE_RED_EYE_OUTLINED,
                                    "Tu actividad",
                                    on_click=None,
                                ),
                                settings_row(
                                    ft.Icons.NOTIFICATIONS_NONE,
                                    "Notificaciones",
                                    on_click=None,
                                ),
                                settings_row(
                                    ft.Icons.ERROR_OUTLINE,
                                    "Terminos y condiciones",
                                    on_click=None,
                                ),
                                settings_row(
                                    ft.Icons.LOCK_OUTLINE,
                                    "Privacidad",
                                    on_click=None,
                                ),
                                settings_row(
                                    ft.Icons.HELP_OUTLINE,
                                    "Soporte",
                                    on_click=None,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
