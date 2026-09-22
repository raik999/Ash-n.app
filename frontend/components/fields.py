from __future__ import annotations

import flet as ft

from style.theme import Colors, TextSizes


def underline_field(
    label: str,
    *,
    password: bool = False,
    can_reveal: bool = False,
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
    helper: str | None = None,
    value: str = "",
    on_submit=None,
    multiline: bool = False,
    max_lines: int = 1,
) -> ft.TextField:
    return ft.TextField(
        label=label,
        value=value,
        password=password,
        can_reveal_password=can_reveal,
        keyboard_type=keyboard_type,
        helper_text=helper,
        multiline=multiline,
        max_lines=max_lines,
        border=ft.InputBorder.UNDERLINE,
        filled=False,
        dense=True,
        content_padding=ft.padding.only(top=14, bottom=8),
        label_style=ft.TextStyle(color=Colors.TEXT_MUTED, size=TextSizes.BODY),
        text_style=ft.TextStyle(color=Colors.TEXT_BODY, size=TextSizes.BODY),
        helper_style=ft.TextStyle(color=Colors.TEXT_MUTED, size=TextSizes.SMALL),
        cursor_color=Colors.TEXT_PRIMARY,
        border_color=Colors.TEXT_PRIMARY,
        focused_border_color=Colors.TEXT_PRIMARY,
        border_width=1,
        focused_border_width=2,
        on_submit=on_submit,
    )


def clear_errors(*fields: ft.TextField) -> None:
    for field in fields:
        if field.error_text:
            field.error_text = None
            field.update()


def mark_error(field: ft.TextField, message: str) -> None:
    field.error_text = message
    field.update()
