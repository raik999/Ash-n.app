from __future__ import annotations

import flet as ft

class Colors:
    BRAND_RED = "#E63946"
    BRAND_DARK = "#1A1A1A"

    BRAND_RED_SOFT = "#FDECEE"

    TEXT_PRIMARY = "#2E3142"
    TEXT_BODY = "#3D3D3D"

    TEXT_MUTED = "#6B6D76"

    TEXT_FAINT = "#9A9BA2"

    TEXT_ON_DARK = "#FFFFFF"

    TEXT_ON_DARK_SOFT = "#FFFFFFB8"

    BACKGROUND = "#FFFFFF"
    PEACH = "#F9DFC0"
    PEACH_SOFT = "#FDF0E2"

    NEUTRAL_50 = "#FAF9F8"
    SURFACE = "#F4F2F0"
    SURFACE_STRONG = "#EAE7E3"
    DIVIDER = "#E4E0DC"

    DISABLED_BG = "#F1EFED"
    DISABLED_FG = "#A9A6A2"

    PLACEHOLDER = "#A8A8A8"

    ERROR = "#C73B3B"
    SUCCESS = "#1F7A43"

    ERROR_SOFT = "#FBEAEA"
    SUCCESS_SOFT = "#E8F5ED"

    CHIP_FALLBACK = "#7C7C7C"

    MEDIA_VIDEO = "#2B2B2B"
    MEDIA_AUDIO = "#5B3DA8"

    PALETA_AVATARES = (
        "#2E9E27",
        "#F0743C",
        "#BE2EDD",
        "#4D7CFE",
        "#F03C3C",
        "#17B8C4",
        "#E8A317",
        "#E0457B",
    )

    SHADOW = "#14000000"

class Fonts:
    BODY = "Poppins"
    MEDIUM = "Poppins Medium"
    HEADING = "Poppins SemiBold"
    STRONG = "Poppins Bold"

    FALLBACK = "Roboto"

class TextSizes:
    DISPLAY = 38
    TITLE = 30
    HEADING = 24
    SUBTITLE = 18
    BODY = 15
    LABEL = 13
    SMALL = 12

class LineHeight:
    TIGHT = 1.08
    HEADING = 1.25
    BODY = 1.45

class Radius:
    XS = 6
    SM = 10
    MD = 14
    LG = 20
    PILL = 999

class Space:
    XXS = 4
    XS = 8
    SM = 12
    MD = 16
    LG = 20
    XL = 24
    XXL = 32
    HUGE = 40

class Motion:
    FAST = 140
    BASE = 220
    SLOW = 320

class Sizes:
    CONTENT_MAX_WIDTH = 480

    PAGE_PADDING = Space.XL
    FIELD_SPACING = Space.XXS + 2
    SECTION_SPACING = 28

    BUTTON_HEIGHT = 48
    BUTTON_RADIUS = Radius.SM

    TOUCH_MIN = 48

    ICON_SM = 18
    ICON_MD = 22
    ICON_LG = 28

    AVATAR_SM = 44
    AVATAR_MD = 48
    AVATAR_LARGE = 110
    AVATAR_PROFILE = 78

    NAV_BAR_HEIGHT = 64

def sombra_suave(elevada: bool = False) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=18 if elevada else 10,
        spread_radius=0,
        offset=ft.Offset(0, 6 if elevada else 2),
        color=Colors.SHADOW,
    )

def page_gradient(ligero: bool = False) -> ft.LinearGradient | None:
    if ligero:
        return None

    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=[
            Colors.PEACH,
            Colors.PEACH_SOFT,
            Colors.BACKGROUND,
            Colors.BACKGROUND,
            Colors.PEACH_SOFT,
            Colors.PEACH,
        ],
        stops=[0.0, 0.12, 0.30, 0.70, 0.88, 1.0],
    )

def app_theme(ligero: bool = False) -> ft.Theme:
    transicion_android = (
        ft.PageTransitionTheme.NONE
        if ligero
        else ft.PageTransitionTheme.FADE_FORWARDS
    )

    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=Colors.BRAND_DARK,
            on_primary=Colors.TEXT_ON_DARK,
            secondary=Colors.BRAND_RED,
            on_secondary=Colors.TEXT_ON_DARK,
            surface=Colors.BACKGROUND,
            on_surface=Colors.TEXT_PRIMARY,
            error=Colors.ERROR,
            on_error=Colors.TEXT_ON_DARK,
            outline=Colors.DIVIDER,
        ),
        font_family=Fonts.BODY,
        visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        page_transitions=ft.PageTransitionsTheme(
            android=transicion_android,
            ios=ft.PageTransitionTheme.CUPERTINO,
            windows=ft.PageTransitionTheme.FADE_FORWARDS,
            macos=ft.PageTransitionTheme.CUPERTINO,
            linux=ft.PageTransitionTheme.FADE_FORWARDS,
        ),
        system_overlay_style=ft.SystemOverlayStyle(
            status_bar_color=ft.Colors.TRANSPARENT,
            status_bar_icon_brightness=ft.Brightness.DARK,
            system_navigation_bar_color=Colors.PEACH_SOFT,
            system_navigation_bar_icon_brightness=ft.Brightness.DARK,
            system_navigation_bar_divider_color=Colors.PEACH_SOFT,
            enforce_system_navigation_bar_contrast=False,
        ),
        navigation_bar_theme=ft.NavigationBarTheme(
            bgcolor=Colors.PEACH_SOFT,
            indicator_color=ft.Colors.TRANSPARENT,
            elevation=0,
            height=Sizes.NAV_BAR_HEIGHT,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_visibility=False,
            thickness=4,
            radius=Radius.XS,
            thumb_color=Colors.DIVIDER,
        ),
        divider_color=Colors.DIVIDER,
        hint_color=Colors.TEXT_FAINT,
    )
