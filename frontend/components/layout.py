from __future__ import annotations

import flet as ft

from style.responsive import pantalla
from style.theme import Colors, Radius, Sizes, Space, TextSizes, page_gradient

MARCA_ZONA_SEGURA = "ashun.zona_segura"

def safe_update(*controls: ft.Control) -> None:
    for control in controls:
        try:
            control.update()
        except (RuntimeError, AssertionError):
            pass

def zona_segura(
    contenido: ft.Control,
    *,
    con_barra_inferior: bool = False,
    arriba: bool = True,
) -> ft.SafeArea:
    return ft.SafeArea(
        content=contenido,
        avoid_intrusions_top=arriba,
        avoid_intrusions_bottom=not con_barra_inferior,
        avoid_intrusions_left=True,
        avoid_intrusions_right=True,
        expand=True,
    )

def screen(
    *controls: ft.Control,
    scroll: bool = True,
    spacing: int = 0,
    vertical_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START,
    padding: int | None = None,
) -> ft.Container:
    medidas = pantalla()

    if scroll:
        for control in controls:
            if getattr(control, "expand", None):
                control.expand = None

    content_column = ft.Column(
        controls=list(controls),
        spacing=spacing,
        alignment=vertical_alignment,
        scroll=ft.ScrollMode.AUTO if scroll else None,
        expand=True,
    )

    return ft.Container(
        content=ft.Container(
            content=content_column,
            width=Sizes.CONTENT_MAX_WIDTH,
            padding=ft.Padding.symmetric(
                horizontal=medidas.padding if padding is None else padding,
            ),
            expand=True,
        ),
        alignment=ft.Alignment.TOP_CENTER,
        gradient=page_gradient(medidas.ligero),
        bgcolor=Colors.PEACH_SOFT if medidas.ligero else None,
        expand=True,
    )

def full_width(control: ft.Control) -> ft.Row:
    control.expand = True
    return ft.Row(controls=[control])

def vspace(height: int) -> ft.Container:
    return ft.Container(height=height)

def asegurar_zona(vista_: ft.View) -> ft.View:
    if vista_.data == MARCA_ZONA_SEGURA or vista_.scroll is not None:
        return vista_

    contenido = list(vista_.controls)
    if not contenido:
        return vista_

    vista_.controls = [
        zona_segura(
            ft.Column(spacing=0, expand=True, controls=contenido),
            con_barra_inferior=vista_.navigation_bar is not None,
        )
    ]
    vista_.data = MARCA_ZONA_SEGURA
    return vista_

def vista(
    route: str,
    *,
    cuerpo: ft.Control,
    encabezado: ft.Control | None = None,
    barra_inferior: ft.NavigationBar | None = None,
    bgcolor: str = Colors.BACKGROUND,
    arriba_seguro: bool = True,
) -> ft.View:
    columna: list[ft.Control] = []

    if encabezado is not None:
        columna.append(encabezado)

    cuerpo.expand = True
    columna.append(cuerpo)

    contenido = ft.Column(spacing=0, expand=True, controls=columna)

    return ft.View(
        route=route,
        padding=0,
        spacing=0,
        bgcolor=bgcolor,
        navigation_bar=barra_inferior,
        controls=[
            zona_segura(
                contenido,
                con_barra_inferior=barra_inferior is not None,
                arriba=arriba_seguro,
            )
        ],
    )

def cuerpo_scroll(
    *controls: ft.Control,
    spacing: int = Space.XS,
    padding_horizontal: int | None = None,
    padding_vertical: int = Space.SM,
) -> ft.Container:
    for control in controls:
        if getattr(control, "expand", None):
            control.expand = None

    medidas = pantalla()

    return ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(
            horizontal=medidas.padding if padding_horizontal is None else padding_horizontal,
            vertical=padding_vertical,
        ),
        content=ft.Column(
            controls=list(controls),
            spacing=spacing,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )

def bottom_nav(
    page: ft.Page,
    selected: int = 3,
    on_change=None,
    sin_leer: int = 0,
) -> ft.NavigationBar:
    DESTINATIONS = {1: "/search", 2: "/chats", 3: "/profile"}

    async def handle_change(e: ft.ControlEvent) -> None:
        index = e.control.selected_index

        if index == selected:
            return

        target = DESTINATIONS.get(index)
        if target is not None:
            await page.push_route(target)
            return

        e.control.selected_index = selected
        e.control.update()

    def icono(nombre: str) -> ft.Icon:
        return ft.Icon(nombre, size=Sizes.ICON_LG, color=Colors.TEXT_PRIMARY)

    def globito() -> ft.Badge | None:
        if sin_leer <= 0:
            return None
        return ft.Badge(
            label=str(sin_leer) if sin_leer < 100 else "99+",
            bgcolor=Colors.BRAND_RED,
            text_color=Colors.TEXT_ON_DARK,
        )

    return ft.NavigationBar(
        selected_index=selected,
        bgcolor=Colors.PEACH_SOFT,
        indicator_color=ft.Colors.TRANSPARENT,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
        height=Sizes.NAV_BAR_HEIGHT,
        on_change=on_change or handle_change,
        destinations=[
            ft.NavigationBarDestination(icono(ft.Icons.HOME_OUTLINED), label="Inicio"),
            ft.NavigationBarDestination(icono(ft.Icons.SEARCH), label="Buscar"),
            ft.NavigationBarDestination(
                icono(ft.Icons.CHAT_BUBBLE_OUTLINE),
                label="Mensajes",
                badge=globito(),
            ),
            ft.NavigationBarDestination(icono(ft.Icons.PERSON_OUTLINE), label="Perfil"),
        ],
    )

def tarjeta(
    contenido: ft.Control,
    *,
    on_click=None,
    tooltip: str | None = None,
    bgcolor: str = Colors.SURFACE,
    padding_horizontal: int = Space.SM,
    padding_vertical: int = Space.SM - 2,
) -> ft.Container:
    return ft.Container(
        bgcolor=bgcolor,
        border_radius=Radius.MD,
        padding=ft.Padding.symmetric(
            horizontal=padding_horizontal, vertical=padding_vertical
        ),
        ink=on_click is not None,
        on_click=on_click,
        tooltip=tooltip,
        content=contenido,
    )

def estado_vacio(icono: str, titulo: str, detalle: str) -> ft.Container:
    medidas = pantalla()

    return ft.Container(
        alignment=ft.Alignment.CENTER,
        padding=Space.HUGE,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Space.XS + 2,
            tight=True,
            controls=[
                ft.Icon(icono, size=medidas.avatar(52), color=Colors.TEXT_FAINT),
                ft.Text(
                    titulo,
                    size=medidas.texto(TextSizes.SUBTITLE),
                    color=Colors.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    detalle,
                    size=medidas.texto(TextSizes.LABEL),
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                    style=ft.TextStyle(height=1.4),
                ),
            ],
        ),
    )
