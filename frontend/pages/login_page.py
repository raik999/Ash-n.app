from __future__ import annotations

import flet as ft

from components.brand_header import brand_header
from components.buttons import link_button, loading_button
from components.feedback import show_error
from components.fields import clear_errors, mark_error, underline_field
from components.layout import full_width, screen, vspace
from context.app_state import AppState
from services import auth_service
from services.api_client import ApiError
from style.theme import Colors, TextSizes


def view(page: ft.Page, state: AppState) -> ft.View:
    identifier_field = underline_field("Nombre de Usuario o Mail")
    password_field = underline_field("Contraseña", password=True, can_reveal=True)

    remember_checkbox = ft.Checkbox(
        label="Recuerdame",
        value=True,
        label_style=ft.TextStyle(color=Colors.TEXT_BODY, size=TextSizes.BODY),
        fill_color={
            ft.ControlState.SELECTED: Colors.BRAND_DARK,
            ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
        },
        check_color=Colors.TEXT_ON_DARK,
    )

    def do_login(e: ft.ControlEvent | None = None) -> None:
        clear_errors(identifier_field, password_field)

        identifier = (identifier_field.value or "").strip()
        password = password_field.value or ""

        if not identifier:
            mark_error(identifier_field, "Escribe tu usuario o correo")
            return
        if not password:
            mark_error(password_field, "Escribe tu contraseña")
            return

        set_loading(True)
        try:
            data = auth_service.login(identifier, password)

            if remember_checkbox.value:
                state.save_session(data["access_token"], data["user"])
            else:
                state.set_user(data["user"])
                from services.api_client import api

                api.set_token(data["access_token"])

            page.go("/profile")

        except ApiError as error:
            if error.field == "identifier":
                mark_error(identifier_field, error.message)
            elif error.field == "password":
                mark_error(password_field, error.message)
            else:
                show_error(page, error.message)
        finally:
            set_loading(False)

    login_button, set_loading = loading_button("Iniciar Sesion", do_login)

    password_field.on_submit = do_login

    def go_to_register(e: ft.ControlEvent) -> None:
        page.go("/register")

    def forgot_password(e: ft.ControlEvent) -> None:
        show_error(page, "La recuperacion de contraseña aun no esta disponible")

    return ft.View(
        route="/login",
        padding=0,
        controls=[
            screen(
                vspace(70),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[brand_header(size=52, logo_size=92)],
                ),
                vspace(60),
                identifier_field,
                vspace(14),
                password_field,
                vspace(10),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        remember_checkbox,
                        link_button(
                            "Olvidaste tu contraseña ?",
                            forgot_password,
                            bold=False,
                        ),
                    ],
                ),
                vspace(26),
                full_width(login_button),
                vspace(90),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Aun no te has registrado ?",
                            size=TextSizes.BODY,
                            color=Colors.TEXT_MUTED,
                        ),
                        link_button("Regístrate", go_to_register),
                    ],
                ),
                vspace(24),
            )
        ],
    )
