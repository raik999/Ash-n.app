from __future__ import annotations

import flet as ft

from style.theme import Colors, Sizes, TextSizes


def show_error(page: ft.Page, message: str) -> None:
    page.open(
        ft.SnackBar(
            content=ft.Text(message, color=Colors.TEXT_ON_DARK, size=TextSizes.BODY),
            bgcolor=Colors.ERROR,
            duration=4000,
        )
    )


def show_success(page: ft.Page, message: str) -> None:
    page.open(
        ft.SnackBar(
            content=ft.Text(message, color=Colors.TEXT_ON_DARK, size=TextSizes.BODY),
            bgcolor=Colors.SUCCESS,
            duration=2500,
        )
    )


def confirm_dialog(
    page: ft.Page,
    *,
    title: str,
    message: str,
    on_confirm,
    confirm_text: str = "Confirmar",
    cancel_text: str = "Cancelar",
    danger: bool = True,
    extra: ft.Control | None = None,
) -> ft.AlertDialog:
    def close(e=None) -> None:
        page.close(dialog)

    def handle_confirm(e) -> None:
        on_confirm(close)

    content_controls: list[ft.Control] = [
        ft.Text(message, size=TextSizes.BODY, color=Colors.TEXT_BODY)
    ]
    if extra is not None:
        content_controls.append(ft.Container(height=10))
        content_controls.append(extra)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
        content=ft.Container(
            width=320,
            content=ft.Column(tight=True, spacing=0, controls=content_controls),
        ),
        actions=[
            ft.TextButton(cancel_text, on_click=close),
            ft.TextButton(
                content=ft.Text(
                    confirm_text,
                    color=Colors.BRAND_RED if danger else Colors.TEXT_PRIMARY,
                    weight=ft.FontWeight.BOLD,
                ),
                on_click=handle_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.open(dialog)
    return dialog


def default_avatar(size: int = Sizes.AVATAR_LARGE) -> ft.Container:
    head_size = size * 0.42
    body_width = size * 0.72
    body_height = size * 0.40

    return ft.Container(
        width=size,
        height=size,
        bgcolor=Colors.SURFACE,
        border_radius=size / 2,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Stack(
            controls=[
                ft.Container(
                    width=head_size,
                    height=head_size,
                    bgcolor=Colors.PLACEHOLDER,
                    border_radius=head_size / 2,
                    left=(size - head_size) / 2,
                    top=size * 0.14,
                ),
                ft.Container(
                    width=body_width,
                    height=body_height,
                    bgcolor=Colors.PLACEHOLDER,
                    border_radius=ft.border_radius.only(
                        top_left=body_width / 2,
                        top_right=body_width / 2,
                    ),
                    left=(size - body_width) / 2,
                    top=size * 0.62,
                ),
            ]
        ),
    )


def avatar_view(url: str | None, size: int = Sizes.AVATAR_LARGE) -> ft.Control:
    if not url:
        return default_avatar(size)

    return ft.Container(
        width=size,
        height=size,
        border_radius=size / 2,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Image(
            src=url,
            width=size,
            height=size,
            fit=ft.ImageFit.COVER,
            error_content=default_avatar(size),
        ),
    )
