import flet as ft

from style.responsive import pantalla
from style.theme import Colors, Fonts, LineHeight, Space, TextSizes

def brand_header(
    *,
    size: int = TextSizes.HEADING,
    logo_size: int = 44,
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.END,
) -> ft.Row:
    return ft.Row(
        alignment=alignment,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[
            ft.Text(
                "Ashün",
                size=pantalla().texto(size),
                color=Colors.TEXT_PRIMARY,
                font_family=Fonts.HEADING,
            ),
            ft.Image(
                src="logo.png",
                width=pantalla().avatar(logo_size),
                height=pantalla().avatar(logo_size),
                fit=ft.BoxFit.CONTAIN,
            ),
        ],
    )

def screen_title(text: str, subtitle: str | None = None) -> ft.Column:
    controls: list[ft.Control] = [
        ft.Text(
            text.upper(),
            size=pantalla().texto(TextSizes.TITLE),
            weight=ft.FontWeight.W_700,
            color=Colors.TEXT_PRIMARY,
            font_family=Fonts.HEADING,
            style=ft.TextStyle(height=LineHeight.TIGHT, letter_spacing=-0.5),
        )
    ]

    if subtitle:
        controls.append(
            ft.Text(
                subtitle,
                size=pantalla().texto(TextSizes.LABEL),
                color=Colors.TEXT_MUTED,
                style=ft.TextStyle(height=LineHeight.BODY),
            )
        )

    return ft.Column(controls=controls, spacing=Space.XS + 2)
