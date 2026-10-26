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
        helper=helper,
        multiline=multiline,
        max_lines=max_lines,
        filled=False,
        dense=True,
        border={
            ft.ControlState.DEFAULT: ft.UnderlineInputBorder(
                side=ft.BorderSide(width=1, color=Colors.TEXT_PRIMARY)
            ),
            ft.ControlState.FOCUSED: ft.UnderlineInputBorder(
                side=ft.BorderSide(width=2, color=Colors.TEXT_PRIMARY)
            ),
        },
        content_padding=ft.Padding.only(top=14, bottom=8),
        label_style=ft.TextStyle(color=Colors.TEXT_MUTED, size=TextSizes.BODY),
        text_style=ft.TextStyle(color=Colors.TEXT_BODY, size=TextSizes.BODY),
        helper_style=ft.TextStyle(color=Colors.TEXT_MUTED, size=TextSizes.SMALL),
        cursor_color=Colors.TEXT_PRIMARY,
        on_submit=on_submit,
    )

def clear_errors(*fields: ft.TextField) -> None:
    for field in fields:
        if field.error:
            field.error = None
            field.update()

def mark_error(field: ft.TextField, message: str) -> None:
    field.error = message
    field.update()
