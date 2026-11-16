from __future__ import annotations

import flet as ft

from components.buttons import loading_button
from components.feedback import confirm_dialog, show_error, show_success
from components.fields import underline_field
from components.layout import safe_update, vspace
from components.settings_row import screen_header
from context.app_state import AppState
from services import portfolio_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, Radius, Sizes, Space, TextSizes

async def view(
    page: ft.Page, state: AppState, portfolio_id: int | None = None
) -> ft.View:
    ruta = "/portfolio/new" if portfolio_id is None else f"/portfolio/{portfolio_id}/edit"
    medidas = pantalla()

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    actual: dict = {}
    if portfolio_id is not None:
        try:
            actual = await portfolio_service.get_portfolio(portfolio_id)
        except ApiError as error:
            show_error(page, error.message)
            await page.push_route("/profile")
            return ft.View(route=ruta, controls=[])

        if not actual.get("can_edit"):
            await page.push_route(f"/portfolio/{portfolio_id}")
            return ft.View(route=ruta, controls=[])

    editando = portfolio_id is not None

    campo_titulo = underline_field(
        "Titulo del portafolio",
        value=actual.get("title") or "",
    )
    campo_descripcion = underline_field(
        "Descripcion",
        value=actual.get("description") or "",
        multiline=True,
        max_lines=3,
        helper="Opcional. Para que se sepa que hay dentro.",
    )

    elegido = {"color": actual.get("color") or portfolio_service.COLOR_POR_DEFECTO}
    circulos: dict[str, ft.Container] = {}

    def pintar_paleta() -> None:
        for color, circulo in circulos.items():
            marcado = color == elegido["color"]
            circulo.border = ft.Border.all(
                3 if marcado else 0,
                Colors.TEXT_PRIMARY if marcado else ft.Colors.TRANSPARENT,
            )
            circulo.scale = 1.0 if marcado else 0.86
        safe_update(*circulos.values())

    def elegir_color(color: str):
        def manejar(e) -> None:
            elegido["color"] = color
            pintar_paleta()

        return manejar

    for color in portfolio_service.COLORES:
        circulos[color] = ft.Container(
            width=42,
            height=42,
            bgcolor=color,
            border_radius=Radius.PILL,
            on_click=elegir_color(color),
            ink=True,
            tooltip="Usar este color",
            animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        )

    pintar_paleta()

    paleta = ft.Row(
        wrap=True,
        spacing=Space.SM,
        run_spacing=Space.SM,
        controls=list(circulos.values()),
    )

    interruptor = ft.Switch(
        value=bool(actual.get("is_private")),
        active_color=Colors.BRAND_DARK,
    )

    explicacion = ft.Text(
        "",
        size=medidas.texto(TextSizes.SMALL),
        color=Colors.TEXT_MUTED,
        style=ft.TextStyle(height=1.4),
    )

    def pintar_explicacion() -> None:
        explicacion.value = (
            "Solo vos lo vas a ver. No aparece en tu perfil para los demas."
            if interruptor.value
            else "Cualquiera que entre a tu perfil lo va a ver."
        )
        safe_update(explicacion)

    def al_cambiar_privacidad(e) -> None:
        pintar_explicacion()

    interruptor.on_change = al_cambiar_privacidad
    pintar_explicacion()

    async def guardar_de_verdad() -> None:
        titulo = (campo_titulo.value or "").strip()
        descripcion = (campo_descripcion.value or "").strip()

        try:
            if editando:
                await portfolio_service.update_portfolio(
                    portfolio_id,
                    titulo=titulo,
                    descripcion=descripcion,
                    color=elegido["color"],
                    privado=interruptor.value,
                )
                destino = f"/portfolio/{portfolio_id}"
                mensaje = "Portafolio actualizado"
            else:
                creado = await portfolio_service.create_portfolio(
                    titulo, descripcion or None, elegido["color"], interruptor.value
                )
                destino = f"/portfolio/{creado['id']}"
                mensaje = "Portafolio creado"
        except ApiError as error:
            show_error(page, error.message)
            return

        show_success(page, mensaje)
        await page.push_route(destino)

    async def guardar(e) -> None:
        titulo = (campo_titulo.value or "").strip()

        if not titulo:
            campo_titulo.error = "El portafolio necesita un titulo"
            safe_update(campo_titulo)
            return

        campo_titulo.error = None
        safe_update(campo_titulo)

        cambiar_estado(True)
        try:
            repetido = await portfolio_service.titulo_repetido(
                titulo, excluir=portfolio_id
            )
        finally:
            cambiar_estado(False)

        if not repetido:
            await guardar_de_verdad()
            return

        async def confirmar(cerrar) -> None:
            cerrar()
            await guardar_de_verdad()

        confirm_dialog(
            page,
            title="Ya tienes uno con ese nombre",
            message=(
                f'Ya tienes un portafolio llamado "{titulo}". Podes tener dos '
                "con el mismo nombre, pero despues puede costarte "
                "distinguirlos. Querés continuar?"
            ),
            confirm_text="Crear igual" if not editando else "Guardar igual",
            on_confirm=confirmar,
            danger=False,
        )

    boton, cambiar_estado = loading_button(
        "Guardar cambios" if editando else "Crear portafolio", guardar
    )

    async def volver(e) -> None:
        await page.push_route(
            f"/portfolio/{portfolio_id}" if editando else "/profile"
        )

    return ft.View(
        route=ruta,
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    screen_header(
                        "Editar portafolio" if editando else "Nuevo portafolio",
                        volver,
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=medidas.padding, vertical=Space.MD
                        ),
                        content=ft.Column(
                            spacing=Space.MD,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            controls=[
                                campo_titulo,
                                campo_descripcion,
                                vspace(Space.XS),
                                ft.Text(
                                    "COLOR",
                                    size=medidas.texto(TextSizes.LABEL),
                                    color=Colors.TEXT_MUTED,
                                    weight=ft.FontWeight.W_600,
                                    style=ft.TextStyle(letter_spacing=0.6),
                                ),
                                paleta,
                                vspace(Space.XS),
                                ft.Row(
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            expand=True,
                                            content=ft.Text(
                                                "Portafolio privado",
                                                size=medidas.texto(TextSizes.BODY),
                                                color=Colors.TEXT_PRIMARY,
                                            ),
                                        ),
                                        interruptor,
                                    ],
                                ),
                                explicacion,
                                vspace(Space.LG),
                                ft.Row(controls=[ft.Container(expand=True, content=boton)]),
                                vspace(Space.XL),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
