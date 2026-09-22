import flet as ft


class Colors:
    BRAND_RED = "#E63946"
    BRAND_DARK = "#1A1A1A"

    TEXT_PRIMARY = "#2E3142"
    TEXT_BODY = "#3D3D3D"
    TEXT_MUTED = "#9A9A9A"
    TEXT_ON_DARK = "#FFFFFF"

    BACKGROUND = "#FFFFFF"
    PEACH = "#F9DFC0"
    PEACH_SOFT = "#FDF0E2"
    SURFACE = "#F5F5F5"
    PLACEHOLDER = "#A8A8A8"

    ERROR = "#D64545"
    SUCCESS = "#2E9E5B"
    DIVIDER = "#E0E0E0"

    CHIP_FALLBACK = "#7C7C7C"


class Fonts:
    HEADING = "Poppins"
    BODY = "Poppins"


class TextSizes:
    DISPLAY = 40
    TITLE = 32
    HEADING = 22
    SUBTITLE = 17
    BODY = 15
    LABEL = 14
    SMALL = 12


def page_gradient() -> ft.LinearGradient:
    return ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[
            Colors.PEACH,
            Colors.PEACH_SOFT,
            Colors.BACKGROUND,
            Colors.BACKGROUND,
            Colors.PEACH_SOFT,
            Colors.PEACH,
        ],
        stops=[0.0, 0.08, 0.22, 0.78, 0.92, 1.0],
    )


def app_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=Colors.BRAND_DARK,
            on_primary=Colors.TEXT_ON_DARK,
            secondary=Colors.BRAND_RED,
            surface=Colors.BACKGROUND,
            error=Colors.ERROR,
        ),
        font_family=Fonts.BODY,
    )


class Sizes:
    CONTENT_MAX_WIDTH = 420

    PAGE_PADDING = 24
    FIELD_SPACING = 6
    SECTION_SPACING = 28

    BUTTON_HEIGHT = 48
    BUTTON_RADIUS = 2

    AVATAR_LARGE = 110
    AVATAR_PROFILE = 78
