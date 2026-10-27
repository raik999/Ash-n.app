from __future__ import annotations

import flet as ft

from context.app_state import AppState
from pages import (
    account_page,
    avatar_page,
    birthdate_page,
    comments_page,
    login_page,
    post_editor_page,
    post_page,
    post_settings_page,
    profile_page,
    public_profile_page,
    register_page,
    search_page,
    settings_page,
    tags_page,
)
from style.theme import Colors, app_theme

FONTS = {
    "Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
}

async def main(page: ft.Page) -> None:
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
    await state.start()

    async def route_change(e: ft.RouteChangeEvent) -> None:
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
            "/settings": lambda: settings_page.view(page, state),
            "/settings/account": lambda: account_page.view(page, state),
            "/settings/account/avatar": lambda: avatar_page.view(
                page, state, "/settings/account"
            ),
            "/search": lambda: search_page.view(page, state),
            "/post/new": lambda: post_editor_page.view(page, state),
        }

        public_routes = {"/login", "/register"}
        es_publica = (
            route in public_routes
            or route.startswith("/user/")
            or (route.startswith("/post/") and route != "/post/new")
        )
        if not es_publica and not state.is_authenticated:
            await page.push_route("/login")
            return

        if route.startswith("/post/") and route != "/post/new":
            partes = route.strip("/").split("/")
            if len(partes) >= 2 and partes[1].isdigit():
                post_id = int(partes[1])
                seccion = partes[2] if len(partes) > 2 else ""

                if seccion == "comments":
                    vista = await comments_page.view(page, state, post_id)
                elif seccion == "settings":
                    vista = await post_settings_page.view(page, state, post_id)
                elif seccion == "edit":
                    vista = await post_editor_page.view(page, state, post_id)
                else:
                    vista = await post_page.view(page, state, post_id)

                page.views.clear()
                page.views.append(vista)
                page.update()
                return

        if route.startswith("/user/"):
            target_username = route.removeprefix("/user/")
            if target_username:
                page.views.clear()
                page.views.append(
                    await public_profile_page.view(page, state, target_username)
                )
                page.update()
                return

        builder = routes.get(route)
        if builder is None:
            await page.push_route("/login")
            return

        page.views.clear()
        page.views.append(await builder())
        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        if len(page.views) > 1:
            page.views.pop()

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

    if await state.try_restore_session():
        await page.push_route("/profile")
    else:
        await page.push_route("/login")
