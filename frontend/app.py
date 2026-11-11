from __future__ import annotations

import traceback
import flet as ft

from components.layout import asegurar_zona
from context.app_state import AppState
from pages import (
    account_page,
    avatar_page,
    birthdate_page,
    chat_page,
    chat_settings_page,
    chats_page,
    comments_page,
    login_page,
    notifications_page,
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
from style import responsive
from style.theme import Colors, Fonts, Space, TextSizes, app_theme

FONTS = {
    "Poppins": "fonts/Poppins-Regular.ttf",
    "Poppins Medium": "fonts/Poppins-Medium.ttf",
    "Poppins SemiBold": "fonts/Poppins-SemiBold.ttf",
    "Poppins Bold": "fonts/Poppins-Bold.ttf",
}

RUTAS_RAIZ = {"/login", "/profile", "/search", "/chats"}

def apilar(page: ft.Page, vista: ft.View) -> None:
    asegurar_zona(vista)

    ruta = vista.route

    if ruta in RUTAS_RAIZ:
        page.views.clear()
    else:
        rutas = [v.route for v in page.views]
        if ruta in rutas:
            del page.views[rutas.index(ruta) :]

    page.views.append(vista)
    page.update()

def _vista_de_error(route: str, error: Exception) -> ft.View:
    detalle = traceback.format_exc()

    return ft.View(
        route=route,
        padding=Space.MD,
        bgcolor=Colors.BACKGROUND,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text(
                "Esta pantalla no se pudo abrir",
                size=TextSizes.SUBTITLE + 2,
                weight=ft.FontWeight.BOLD,
                color=Colors.BRAND_RED,
            ),
            ft.Container(height=Space.XXS + 2),
            ft.Text(f"Ruta: {route}", size=TextSizes.LABEL, color=Colors.TEXT_MUTED),
            ft.Text(
                f"{type(error).__name__}: {error}",
                size=TextSizes.LABEL,
                color=Colors.TEXT_BODY,
            ),
            ft.Container(height=Space.XS + 2),
            ft.Text(
                detalle,
                size=10,
                color=Colors.TEXT_MUTED,
                selectable=True,
                font_family="monospace",
            ),
        ],
    )

async def main(page: ft.Page) -> None:
    page.title = "Ashün"
    page.bgcolor = Colors.BACKGROUND
    page.padding = 0
    page.fonts = FONTS

    page.window.width = 414
    page.window.height = 896
    page.window.min_width = 360
    page.window.min_height = 640

    state = AppState(page)

    await state.start()
    medidas = responsive.medir(page)
    page.theme = app_theme(medidas.ligero)
    page.theme_mode = ft.ThemeMode.LIGHT

    async def al_cambiar_tamano(e) -> None:
        responsive.medir(page)

    page.on_resize = al_cambiar_tamano

    async def route_change(e: ft.RouteChangeEvent) -> None:
        route = page.route

        state.vivo.limpiar_pantalla()

        responsive.medir(page)

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
            "/chats": lambda: chats_page.view(page, state),
            "/notifications": lambda: notifications_page.view(page, state),
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

        vista = None

        if route.startswith("/post/") and route != "/post/new":
            partes = route.strip("/").split("/")
            if len(partes) >= 2 and partes[1].isdigit():
                post_id = int(partes[1])
                seccion = partes[2] if len(partes) > 2 else ""
                try:
                    if seccion == "comments":
                        vista = await comments_page.view(page, state, post_id)
                    elif seccion == "settings":
                        vista = await post_settings_page.view(page, state, post_id)
                    elif seccion == "edit":
                        vista = await post_editor_page.view(page, state, post_id)
                    else:
                        vista = await post_page.view(page, state, post_id)
                except Exception as error:
                    vista = _vista_de_error(route, error)

        elif route.startswith("/chat/"):
            partes = route.strip("/").split("/")
            if len(partes) >= 2 and partes[1].isdigit():
                chat_id = int(partes[1])
                seccion = partes[2] if len(partes) > 2 else ""
                try:
                    if seccion == "settings":
                        vista = await chat_settings_page.view(page, state, chat_id)
                    else:
                        vista = await chat_page.view(page, state, chat_id)
                except Exception as error:
                    vista = _vista_de_error(route, error)

        elif route.startswith("/user/"):
            target_username = route.removeprefix("/user/")
            if target_username:
                try:
                    vista = await public_profile_page.view(page, state, target_username)
                except Exception as error:
                    vista = _vista_de_error(route, error)

        else:
            builder = routes.get(route)
            if builder is None:
                await page.push_route("/login")
                return
            try:
                vista = await builder()
            except Exception as error:
                vista = _vista_de_error(route, error)

        if vista is None:
            await page.push_route("/login")
            return

        if not vista.controls:
            return

        apilar(page, vista)

    async def view_pop(e: ft.ViewPopEvent) -> None:
        if len(page.views) <= 1:
            return

        page.views.pop()
        anterior = page.views[-1]
        await page.push_route(anterior.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.views.append(
        ft.View(
            route="/loading",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            bgcolor=Colors.BACKGROUND,
            controls=[
                ft.ProgressRing(color=Colors.BRAND_DARK),
                ft.Container(height=Space.MD),
                ft.Text(
                    "Cargando Ashün...",
                    color=Colors.TEXT_MUTED,
                    font_family=Fonts.BODY,
                ),
            ],
        )
    )
    page.update()

    if await state.try_restore_session():
        await page.push_route("/profile")
    else:
        await page.push_route("/login")
