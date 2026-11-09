from __future__ import annotations

import flet as ft

from components.feedback import show_success
from components.layout import bottom_nav
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from style import responsive
from style.responsive import pantalla
from style.theme import Colors, Radius, Space, TextSizes, app_theme

OPCIONES_LIGERO = [
    ("auto", "Automático", "La app decide mirando tu pantalla"),
    ("no", "Desactivado", "Degradados y animaciones siempre encendidos"),
    ("si", "Activado", "Sin degradados ni animaciones: va más fluido"),
]

async def view(page: ft.Page, state: AppState) -> ft.View:
    if not state.user:
        await page.push_route("/login")
        return ft.View(route="/settings", controls=[])

    user = state.user
    medidas = pantalla()

    async def go_back(e: ft.ControlEvent) -> None:
        await page.push_route("/profile")

    async def go_to_account(e: ft.ControlEvent) -> None:
        await page.push_route("/settings/account")

    async def elegir(e: ft.ControlEvent) -> None:
        valor = e.control.value
        await state.guardar_apariencia(valor)

        nuevas = responsive.medir(page)
        page.theme = app_theme(nuevas.ligero)
        page.update()

        show_success(
            page,
            "Modo ligero activado" if nuevas.ligero else "Modo ligero desactivado",
        )
        await page.push_route("/settings")

    preferencia = responsive.preferencia_ligero()

    selector_ligero = ft.RadioGroup(
        value=preferencia,
        on_change=elegir,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Radio(
                    value=clave,
                    label=f"{nombre} — {detalle}",
                    label_style=ft.TextStyle(
                        size=medidas.texto(TextSizes.LABEL),
                        color=Colors.TEXT_BODY,
                    ),
                    active_color=Colors.BRAND_DARK,
                )
                for clave, nombre, detalle in OPCIONES_LIGERO
            ],
        ),
    )

    estado_actual = ft.Container(
        bgcolor=Colors.SURFACE,
        border_radius=Radius.SM,
        padding=ft.Padding.symmetric(horizontal=Space.SM, vertical=Space.XS),
        content=ft.Text(
            (
                "Ahora mismo está encendido."
                if medidas.ligero
                else "Ahora mismo está apagado."
            )
            + f" Tu pantalla mide {int(medidas.ancho)} × {int(medidas.alto)} "
            f"y dibuja {medidas.megapixeles:.1f} millones de píxeles.",
            size=medidas.texto(TextSizes.SMALL),
            color=Colors.TEXT_MUTED,
            style=ft.TextStyle(height=1.4),
        ),
    )

    dark_mode_switch = ft.Switch(
        value=False,
        disabled=True,
        active_color=Colors.BRAND_DARK,
    )

    return ft.View(
        route="/settings",
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        navigation_bar=bottom_nav(page, selected=3, sin_leer=state.chats_sin_leer),
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header("Configuración", go_back),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=medidas.padding, vertical=Space.XS + 2
                        ),
                        content=ft.Column(
                            spacing=2,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            controls=[
                                settings_row(
                                    ft.Icons.PERSON_OUTLINE,
                                    user.get("username", ""),
                                    on_click=go_to_account,
                                ),
                                settings_row(
                                    ft.Icons.ADD,
                                    "Nueva cuenta",
                                    on_click=None,
                                    enabled=False,
                                ),
                                section_title("APARIENCIA"),
                                settings_row(
                                    ft.Icons.SPEED,
                                    "Modo ligero",
                                    subtitulo=(
                                        "Para que la app vaya más suelta en "
                                        "teléfonos modestos"
                                    ),
                                    on_click=None,
                                    show_chevron=False,
                                ),
                                ft.Container(
                                    padding=ft.Padding.only(
                                        left=Space.HUGE + Space.MD,
                                        right=Space.XS,
                                        bottom=Space.XS,
                                    ),
                                    content=ft.Column(
                                        spacing=Space.XS,
                                        controls=[selector_ligero, estado_actual],
                                    ),
                                ),
                                settings_row(
                                    ft.Icons.DARK_MODE_OUTLINED,
                                    "Modo Oscuro",
                                    trailing=dark_mode_switch,
                                    on_click=None,
                                    enabled=False,
                                ),
                                section_title("CUENTA"),
                                settings_row(
                                    ft.Icons.REMOVE_RED_EYE_OUTLINED,
                                    "Tu actividad",
                                    on_click=None,
                                    enabled=False,
                                ),
                                settings_row(
                                    ft.Icons.NOTIFICATIONS_NONE,
                                    "Notificaciones",
                                    on_click=None,
                                    enabled=False,
                                ),
                                section_title("INFORMACIÓN"),
                                settings_row(
                                    ft.Icons.ERROR_OUTLINE,
                                    "Terminos y condiciones",
                                    on_click=None,
                                    enabled=False,
                                ),
                                settings_row(
                                    ft.Icons.LOCK_OUTLINE,
                                    "Privacidad",
                                    on_click=None,
                                    enabled=False,
                                ),
                                settings_row(
                                    ft.Icons.HELP_OUTLINE,
                                    "Soporte",
                                    on_click=None,
                                    enabled=False,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
