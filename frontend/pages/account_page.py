from __future__ import annotations

import flet as ft

from components.feedback import avatar_view, confirm_dialog, show_error, show_success
from components.fields import underline_field
from components.layout import bottom_nav
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, Fonts, Sizes, TextSizes


def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        page.go("/login")
        return ft.View(route="/settings/account", controls=[])

    user = state.user

    def go_back(e: ft.ControlEvent) -> None:
        page.go("/settings")

    def go_to_avatar(e: ft.ControlEvent) -> None:
        page.go("/settings/account/avatar")

    username_value = ft.Text(
        user.get("username", ""), size=TextSizes.BODY, color=Colors.TEXT_BODY
    )
    email_value = ft.Text(user.get("email", ""), size=TextSizes.BODY, color=Colors.TEXT_BODY)

    def open_field_dialog(title: str, field: ft.TextField, on_save) -> None:
        def close(e=None) -> None:
            page.close(dialog)

        def handle_save(e) -> None:
            on_save(close)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            content=ft.Container(
                width=320,
                content=ft.Column(tight=True, spacing=10, controls=[field]),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close),
                ft.TextButton("Guardar", on_click=handle_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialog)

    def edit_username(e: ft.ControlEvent) -> None:
        field = underline_field(
            "Nombre de usuario",
            value=(state.user or {}).get("username", ""),
            helper="Entre 3 y 30 caracteres: letras, numeros, punto y guion bajo",
        )

        def save(close) -> None:
            value = (field.value or "").strip().lower()

            if len(value) < 3:
                field.error_text = "Minimo 3 caracteres"
                field.update()
                return

            try:
                updated = user_service.update_profile(username=value)
                state.set_user(updated)
                username_value.value = updated.get("username", "")
                username_value.update()
                close()
                show_success(page, "Nombre de usuario actualizado")
            except ApiError as error:
                field.error_text = error.message
                field.update()

        open_field_dialog("Cambiar nombre de usuario", field, save)

    def edit_email(e: ft.ControlEvent) -> None:
        field = underline_field(
            "Correo",
            value=(state.user or {}).get("email", ""),
            keyboard_type=ft.KeyboardType.EMAIL,
        )

        def save(close) -> None:
            value = (field.value or "").strip().lower()

            if "@" not in value or "." not in value:
                field.error_text = "Ese correo no parece valido"
                field.update()
                return

            try:
                updated = user_service.update_profile(email=value)
                state.set_user(updated)
                email_value.value = updated.get("email", "")
                email_value.update()
                close()
                show_success(page, "Correo actualizado")
            except ApiError as error:
                field.error_text = error.message
                field.update()

        open_field_dialog("Cambiar correo", field, save)

    def edit_password(e: ft.ControlEvent) -> None:
        current_field = underline_field("Contraseña actual", password=True, can_reveal=True)
        new_field = underline_field(
            "Contraseña nueva",
            password=True,
            can_reveal=True,
            helper="Minimo 6 caracteres",
        )
        confirm_field = underline_field("Repetir contraseña nueva", password=True, can_reveal=True)

        def close(ev=None) -> None:
            page.close(dialog)

        def save(ev) -> None:
            current = current_field.value or ""
            new = new_field.value or ""
            confirm = confirm_field.value or ""

            for f in (current_field, new_field, confirm_field):
                f.error_text = None

            if not current:
                current_field.error_text = "Escribe tu contraseña actual"
                current_field.update()
                return
            if len(new) < 6:
                new_field.error_text = "Minimo 6 caracteres"
                new_field.update()
                return
            if new != confirm:
                confirm_field.error_text = "Las contraseñas no coinciden"
                confirm_field.update()
                return
            if new == current:
                new_field.error_text = "Debe ser distinta a la actual"
                new_field.update()
                return

            try:
                user_service.change_password(current, new, confirm)
                close()
                show_success(page, "Contraseña actualizada")
            except ApiError as error:
                target = current_field if error.field == "current_password" else new_field
                target.error_text = error.message
                target.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Cambiar contraseña", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY
            ),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[current_field, new_field, confirm_field],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close),
                ft.TextButton("Guardar", on_click=save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialog)

    def logout(e: ft.ControlEvent) -> None:
        def do_logout(close) -> None:
            close()
            state.clear_session()
            page.go("/login")

        confirm_dialog(
            page,
            title="Cerrar sesión",
            message=(
                "¿Seguro que quieres cerrar sesión? "
                "Tendrás que volver a escribir tu contraseña para entrar."
            ),
            confirm_text="Cerrar sesión",
            on_confirm=do_logout,
        )

    def delete_account(e: ft.ControlEvent) -> None:
        password_field = underline_field("Escribe tu contraseña", password=True, can_reveal=True)

        def do_delete(close) -> None:
            value = password_field.value or ""

            if not value:
                password_field.error_text = "Escribe tu contraseña"
                password_field.update()
                return

            try:
                user_service.delete_account(value)
            except ApiError as error:
                password_field.error_text = error.message
                password_field.update()
                return

            close()
            state.clear_session()
            page.go("/login")
            show_success(page, "Tu cuenta fue eliminada")

        confirm_dialog(
            page,
            title="Eliminar cuenta",
            message=(
                "Esta acción es permanente y no se puede deshacer. "
                "Se borrarán tu perfil, tu foto y tus especialidades. "
                "Escribe tu contraseña para confirmar."
            ),
            confirm_text="Eliminar cuenta",
            on_confirm=do_delete,
            extra=password_field,
        )

    def pencil(on_click, tooltip: str) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icons.EDIT_SQUARE,
            icon_size=22,
            icon_color=Colors.TEXT_PRIMARY,
            tooltip=tooltip,
            on_click=on_click,
        )

    password_trailing = ft.Row(
        tight=True,
        spacing=0,
        controls=[
            ft.IconButton(
                icon=ft.Icons.VISIBILITY_OUTLINED,
                icon_size=20,
                icon_color=Colors.TEXT_MUTED,
                tooltip="Por seguridad, la contraseña no se puede mostrar",
                on_click=None,
            ),
            pencil(edit_password, "Cambiar contraseña"),
        ],
    )

    return ft.View(
        route="/settings/account",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(selected=3),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header("Tu cuenta", go_back),
                    ft.Container(
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=Sizes.PAGE_PADDING),
                        content=ft.Column(
                            spacing=2,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                ft.Container(height=14),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Stack(
                                            width=120,
                                            height=110,
                                            controls=[
                                                ft.Container(
                                                    content=avatar_view(state.avatar_url, 100),
                                                    left=5,
                                                    top=0,
                                                ),
                                                ft.Container(
                                                    content=ft.IconButton(
                                                        icon=ft.Icons.EDIT_SQUARE,
                                                        icon_size=22,
                                                        icon_color=Colors.TEXT_PRIMARY,
                                                        tooltip="Cambiar foto de perfil",
                                                        on_click=go_to_avatar,
                                                    ),
                                                    right=-6,
                                                    bottom=-4,
                                                ),
                                            ],
                                        )
                                    ],
                                ),
                                ft.Container(
                                    alignment=ft.alignment.center,
                                    padding=ft.padding.only(top=4, bottom=4),
                                    content=ft.Text(
                                        user.get("name") or "",
                                        size=TextSizes.SUBTITLE,
                                        color=Colors.TEXT_PRIMARY,
                                        font_family=Fonts.HEADING,
                                    ),
                                ),
                                section_title("General Settings"),
                                settings_row(
                                    ft.Icons.PERSON,
                                    username_value,
                                    trailing=pencil(edit_username, "Cambiar nombre de usuario"),
                                    on_click=edit_username,
                                    show_chevron=False,
                                ),
                                settings_row(
                                    ft.Icons.MAIL_OUTLINE,
                                    email_value,
                                    trailing=pencil(edit_email, "Cambiar correo"),
                                    on_click=edit_email,
                                    show_chevron=False,
                                ),
                                settings_row(
                                    ft.Icons.KEY,
                                    "•" * 12,
                                    trailing=password_trailing,
                                    on_click=edit_password,
                                    show_chevron=False,
                                ),
                                ft.Container(height=8),
                                settings_row(
                                    ft.Icons.LOGOUT,
                                    "Cerrar sesión",
                                    on_click=logout,
                                    danger=True,
                                ),
                                settings_row(
                                    ft.Icons.CLOSE,
                                    "Eliminar cuenta",
                                    on_click=delete_account,
                                    danger=True,
                                ),
                                ft.Container(height=20),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
