from __future__ import annotations

import flet as ft

from context.app_state import AppState
from pages import avatar_page, birthdate_page, login_page, profile_page, register_page, tags_page
from style.theme import Colors, app_theme

FONTS = {
    "Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
}


def main(page: ft.Page) -> None:
    page.title = "Ashün"
    page.theme = app_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = Colors.BACKGROUND
    page.padding = 0
    page.fonts = FONTS

    page.window.width = 414
    page.window.height = 896
    page.window.min_width = 360
    page.window.min_height = 640

    state = AppState(page)

    def route_change(e: ft.RouteChangeEvent) -> None:
        route = page.route

        routes = {
            "/login": lambda: login_page.view(page, state),
            "/register": lambda: register_page.view(page, state),
            "/onboarding/birthdate": lambda: birthdate_page.view(page, state),
            "/onboarding/tags": lambda: tags_page.view(page, state, "/onboarding/avatar"),
            "/onboarding/avatar": lambda: avatar_page.view(page, state, "/profile"),
            "/profile/tags": lambda: tags_page.view(page, state, "/profile"),
            "/profile/avatar": lambda: avatar_page.view(page, state, "/profile"),
            "/profile": lambda: profile_page.view(page, state),
        }

        public_routes = {"/login", "/register"}
        if route not in public_routes and not state.is_authenticated:
            page.go("/login")
            return

        builder = routes.get(route)
        if builder is None:
            page.go("/login")
            return

        page.views.clear()
        page.views.append(builder())
        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route or "/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.views.append(
        ft.View(
            route="/loading",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.ProgressRing(color=Colors.BRAND_DARK),
                ft.Container(height=16),
                ft.Text("Cargando Ashün...", color=Colors.TEXT_MUTED),
            ],
        )
    )
    page.update()

    if state.try_restore_session():
        page.go("/profile")
    else:
        page.go("/login")
