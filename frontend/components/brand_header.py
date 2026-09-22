import flet as ft

from style.theme import Colors, Fonts, TextSizes


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
                size=size,
                weight=ft.FontWeight.BOLD,
                color=Colors.TEXT_PRIMARY,
                font_family=Fonts.HEADING,
            ),
            ft.Image(
                src="logo.svg",
                width=logo_size,
                height=logo_size,
                fit=ft.ImageFit.CONTAIN,
            ),
        ],
    )


def screen_title(text: str, subtitle: str | None = None) -> ft.Column:
    controls: list[ft.Control] = [
        ft.Text(
            text.upper(),
            size=TextSizes.TITLE,
            weight=ft.FontWeight.W_900,
            color=Colors.TEXT_PRIMARY,
            font_family=Fonts.HEADING,
            style=ft.TextStyle(height=1.05),
        )
    ]

    if subtitle:
        controls.append(
            ft.Text(
                subtitle,
                size=TextSizes.LABEL,
                color=Colors.TEXT_MUTED,
            )
        )

    return ft.Column(controls=controls, spacing=10)
