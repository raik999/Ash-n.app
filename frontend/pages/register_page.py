from __future__ import annotations

import flet as ft

from components.brand_header import brand_header, screen_title
from components.buttons import link_button, loading_button
from components.feedback import show_error
from components.fields import clear_errors, mark_error, underline_field
from components.layout import full_width, screen, vspace
from context.app_state import AppState
from services import auth_service
from services.api_client import ApiError
from style.theme import Colors, TextSizes


def view(page: ft.Page, state: AppState) -> ft.View:
    email_field = underline_field("Mail", keyboard_type=ft.KeyboardType.EMAIL)
    name_field = underline_field("Nombre completo")
    username_field = underline_field("Nombre de usuario")
    password_field = underline_field(
        "Contraseña",
        password=True,
        can_reveal=True,
        helper="Debe contener por lo menos 6 caracteres",
    )
    confirm_field = underline_field("Confirmar Contraseña", password=True, can_reveal=True)

    all_fields = [email_field, name_field, username_field, password_field, confirm_field]

    field_map = {
        "email": email_field,
        "name": name_field,
        "username": username_field,
        "password": password_field,
        "confirm_password": confirm_field,
    }

    def do_register(e: ft.ControlEvent | None = None) -> None:
        clear_errors(*all_fields)

        email = (email_field.value or "").strip()
        name = (name_field.value or "").strip()
        username = (username_field.value or "").strip()
        password = password_field.value or ""
        confirm = confirm_field.value or ""

        if not email:
            mark_error(email_field, "Escribe tu correo")
            return
        if "@" not in email or "." not in email:
            mark_error(email_field, "Ese correo no parece valido")
            return
        if len(name) < 2:
            mark_error(name_field, "Escribe tu nombre completo")
            return
        if len(username) < 3:
            mark_error(username_field, "Minimo 3 caracteres")
            return
        if len(password) < 6:
            mark_error(password_field, "Minimo 6 caracteres")
            return
        if password != confirm:
            mark_error(confirm_field, "Las contraseñas no coinciden")
            return

        set_loading(True)
        try:
            data = auth_service.register(
                email=email,
                name=name,
                username=username,
                password=password,
                confirm_password=confirm,
            )

            state.save_session(data["access_token"], data["user"])

            page.go("/onboarding/birthdate")

        except ApiError as error:
            target = field_map.get(error.field or "")
            if target is not None:
                mark_error(target, error.message)
            else:
                show_error(page, error.message)
        finally:
            set_loading(False)

    register_button, set_loading = loading_button("Iniciar Sesion", do_register)
    confirm_field.on_submit = do_register

    def go_to_login(e: ft.ControlEvent) -> None:
        page.go("/login")

    return ft.View(
        route="/register",
        padding=0,
        controls=[
            screen(
                vspace(28),
                brand_header(),
                vspace(40),
                screen_title(
                    "Bienvenido",
                    "Porfavor ingrese sus datos para poder empezar",
                ),
                vspace(34),
                email_field,
                vspace(8),
                name_field,
                vspace(8),
                username_field,
                vspace(8),
                password_field,
                vspace(8),
                confirm_field,
                vspace(30),
                full_width(register_button),
                vspace(50),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Ya tienes una cuenta ?",
                            size=TextSizes.BODY,
                            color=Colors.TEXT_MUTED,
                        ),
                        link_button("Inicia Sesion", go_to_login),
                    ],
                ),
                vspace(24),
            )
        ],
    )
