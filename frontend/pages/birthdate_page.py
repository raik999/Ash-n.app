from __future__ import annotations

from datetime import date

import flet as ft

from components.brand_header import brand_header, screen_title
from components.buttons import loading_button
from components.feedback import show_error
from components.layout import full_width, screen, vspace
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, TextSizes


def _date_part_field(hint: str, width: int, max_length: int) -> ft.TextField:
    return ft.TextField(
        hint_text=hint,
        width=width,
        max_length=max_length,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.NumbersOnlyInputFilter(),
        text_align=ft.TextAlign.CENTER,
        text_size=30,
        border=ft.InputBorder.UNDERLINE,
        filled=False,
        border_color=Colors.TEXT_PRIMARY,
        focused_border_color=Colors.TEXT_PRIMARY,
        cursor_color=Colors.TEXT_PRIMARY,
        text_style=ft.TextStyle(color=Colors.TEXT_PRIMARY, size=30),
        hint_style=ft.TextStyle(color=Colors.TEXT_MUTED, size=30),
        counter_text="",
        content_padding=ft.padding.only(bottom=4),
    )


def view(page: ft.Page, state: AppState) -> ft.View:
    day_field = _date_part_field("DD", 76, 2)
    month_field = _date_part_field("MM", 76, 2)
    year_field = _date_part_field("AAAA", 116, 4)

    def slash() -> ft.Text:
        return ft.Text("/", size=34, color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.W_300)

    if state.user and state.user.get("birthdate"):
        parts = state.user["birthdate"].split("-")
        if len(parts) == 3:
            year_field.value, month_field.value, day_field.value = parts

    def do_save(e: ft.ControlEvent | None = None) -> None:
        day = (day_field.value or "").strip()
        month = (month_field.value or "").strip()
        year = (year_field.value or "").strip()

        if not any([day, month, year]):
            page.go("/onboarding/tags")
            return

        if not all([day, month, year]):
            show_error(page, "Completa el dia, el mes y el año, o deja los tres vacios")
            return

        try:
            birthdate = date(int(year), int(month), int(day))
        except ValueError:
            show_error(page, "Esa fecha no existe, revisala")
            return

        set_loading(True)
        try:
            updated_user = user_service.update_profile(birthdate=birthdate)
            state.set_user(updated_user)
            page.go("/onboarding/tags")
        except ApiError as error:
            show_error(page, error.message)
        finally:
            set_loading(False)

    done_button, set_loading = loading_button("Listo", do_save)
    year_field.on_submit = do_save

    return ft.View(
        route="/onboarding/birthdate",
        padding=0,
        controls=[
            screen(
                vspace(28),
                brand_header(),
                vspace(50),
                screen_title(
                    "Ingresa tu fecha de nacimiento",
                    "Este paso lo puedes omitir dejando los campos vacios",
                ),
                vspace(50),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    spacing=6,
                    controls=[day_field, slash(), month_field, slash(), year_field],
                ),
                vspace(20),
                ft.Text(
                    "Tu fecha de nacimiento no sera publica",
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(expand=True),
                full_width(done_button),
                vspace(40),
            )
        ],
    )
