from __future__ import annotations

import flet as ft

from services.api_client import api
from style.responsive import pantalla
from style.theme import Colors, Radius, Sizes, Space, TextSizes

def _aviso(mensaje: str, color: str, duracion: int) -> ft.SnackBar:
    return ft.SnackBar(
        content=ft.Text(
            mensaje,
            color=Colors.TEXT_ON_DARK,
            size=pantalla().texto(TextSizes.BODY),
        ),
        bgcolor=color,
        duration=duracion,
        behavior=ft.SnackBarBehavior.FLOATING,
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        margin=ft.Margin.only(
            left=Space.MD, right=Space.MD, bottom=Sizes.NAV_BAR_HEIGHT + Space.XS
        ),
    )

def show_error(page: ft.Page, message: str) -> None:
    page.show_dialog(_aviso(message, Colors.ERROR, 4000))

def show_success(page: ft.Page, message: str) -> None:
    page.show_dialog(_aviso(message, Colors.SUCCESS, 2500))

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
        page.pop_dialog()

    async def handle_confirm(e) -> None:
        await on_confirm(close)

    content_controls: list[ft.Control] = [
        ft.Text(
            message,
            size=pantalla().texto(TextSizes.BODY),
            color=Colors.TEXT_BODY,
            style=ft.TextStyle(height=1.4),
        )
    ]
    if extra is not None:
        content_controls.append(ft.Container(height=10))
        content_controls.append(extra)

    dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        bgcolor=Colors.BACKGROUND,
        title=ft.Text(
            title,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY,
            size=pantalla().texto(TextSizes.SUBTITLE),
        ),
        content=ft.Container(
            width=min(320, pantalla().ancho - 80),
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

    page.show_dialog(dialog)
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
                    border_radius=ft.BorderRadius.only(
                        top_left=body_width / 2,
                        top_right=body_width / 2,
                    ),
                    left=(size - body_width) / 2,
                    top=size * 0.62,
                ),
            ]
        ),
    )

def foto_de(usuario: dict | None) -> str | None:
    if not usuario:
        return None

    return api.absolute_url(
        usuario.get("avatar_thumb_url") or usuario.get("avatar_url")
    )

def avatar_view(url: str | None, size: int = Sizes.AVATAR_LARGE) -> ft.Control:
    if not url:
        return default_avatar(size)

    pixeles = pantalla().pixeles_para(size)

    return ft.Container(
        width=size,
        height=size,
        border_radius=Radius.PILL,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Image(
            src=url,
            width=size,
            height=size,
            cache_width=pixeles,
            cache_height=pixeles,
            fit=ft.BoxFit.COVER,
            error_content=default_avatar(size),
        ),
    )
