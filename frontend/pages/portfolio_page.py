from __future__ import annotations

from functools import partial

import flet as ft

from components.feedback import confirm_dialog, show_error, show_success
from components.layout import estado_vacio, safe_update
from components.post_media import grid_cell
from components.profile_scroll import grilla_fija
from components.settings_row import boton_barra, screen_header
from context.app_state import AppState
from services import portfolio_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, Fonts, LineHeight, Radius, Sizes, Space, TextSizes

async def view(page: ft.Page, state: AppState, portfolio_id: int) -> ft.View:
    ruta = f"/portfolio/{portfolio_id}"
    medidas = pantalla()

    try:
        portafolio = await portfolio_service.get_portfolio(portfolio_id)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route("/profile")
        return ft.View(route=ruta, controls=[])

    puedo_editar = bool(portafolio.get("can_edit"))
    publicaciones = portafolio.get("posts") or []
    color = portafolio.get("color") or portfolio_service.COLOR_POR_DEFECTO

    async def volver(e) -> None:
        await page.push_route("/profile" if puedo_editar else "/search")

    async def abrir_publicacion(post_id: int) -> None:
        await page.push_route(f"/post/{post_id}")

    async def organizar(e) -> None:
        await page.push_route(f"/portfolio/{portfolio_id}/posts")

    async def editar(e) -> None:
        await page.push_route(f"/portfolio/{portfolio_id}/edit")

    async def eliminar_de_verdad(cerrar) -> None:
        try:
            await portfolio_service.delete_portfolio(portfolio_id)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Portafolio eliminado")
        await page.push_route("/profile")

    def eliminar(e) -> None:
        confirm_dialog(
            page,
            title="Eliminar portafolio",
            message=(
                f'Se elimina "{portafolio["title"]}".\n\n'
                "Tus publicaciones NO se eliminan: siguen en tu perfil y en "
                "los otros portafolios donde esten."
            ),
            confirm_text="Eliminar",
            on_confirm=eliminar_de_verdad,
            danger=True,
        )

    def abrir_menu(e) -> None:
        page.show_dialog(menu)

    def cerrar_menu(e=None) -> None:
        page.pop_dialog()

    async def pedir_eliminar(e) -> None:
        eliminar(e)

    def opcion(icono: str, texto: str, accion, peligro: bool = False) -> ft.Control:
        async def manejar(evento) -> None:
            cerrar_menu()
            await accion(evento)

        return ft.Container(
            on_click=manejar,
            ink=True,
            border_radius=Radius.SM,
            padding=ft.Padding.symmetric(horizontal=Space.SM, vertical=Space.SM),
            content=ft.Row(
                spacing=Space.SM,
                controls=[
                    ft.Icon(
                        icono,
                        size=Sizes.ICON_MD,
                        color=Colors.BRAND_RED if peligro else Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        texto,
                        size=medidas.texto(TextSizes.BODY),
                        color=Colors.BRAND_RED if peligro else Colors.TEXT_BODY,
                    ),
                ],
            ),
        )

    menu = ft.AlertDialog(
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        bgcolor=Colors.BACKGROUND,
        content=ft.Container(
            width=min(300, medidas.ancho - 80),
            content=ft.Column(
                tight=True,
                spacing=2,
                controls=[
                    opcion(ft.Icons.PHOTO_LIBRARY_OUTLINED, "Organizar publicaciones", organizar),
                    opcion(ft.Icons.EDIT, "Editar portafolio", editar),
                    opcion(
                        ft.Icons.DELETE_OUTLINE,
                        "Eliminar portafolio",
                        pedir_eliminar,
                        peligro=True,
                    ),
                ],
            ),
        ),
    )

    lineas: list[ft.Control] = [
        ft.Text(
            portafolio["title"],
            size=medidas.texto(TextSizes.HEADING),
            color=Colors.TEXT_ON_DARK,
            font_family=Fonts.HEADING,
        )
    ]

    descripcion = (portafolio.get("description") or "").strip()
    if descripcion:
        lineas.append(
            ft.Text(
                descripcion,
                size=medidas.texto(TextSizes.LABEL),
                color=Colors.TEXT_ON_DARK_SOFT,
                style=ft.TextStyle(height=LineHeight.BODY),
            )
        )

    cantidad = len(publicaciones)
    detalle = f"{cantidad} {'publicacion' if cantidad == 1 else 'publicaciones'}"
    if portafolio.get("is_private"):
        detalle += "  ·  Privado"

    lineas.append(
        ft.Text(
            detalle,
            size=medidas.texto(TextSizes.SMALL),
            color=Colors.TEXT_ON_DARK_SOFT,
        )
    )

    cabecera_color = ft.Container(
        bgcolor=color,
        padding=ft.Padding.only(
            left=medidas.padding,
            right=medidas.padding,
            top=Space.MD,
            bottom=Space.LG,
        ),
        content=ft.Column(spacing=Space.XXS + 2, tight=True, controls=lineas),
    )

    RELLENO = Space.XS

    if publicaciones:
        celdas = [
            grid_cell(p, partial(abrir_publicacion, p["id"])) for p in publicaciones
        ]
        contenido: ft.Control = grilla_fija(
            celdas, ancho_disponible=medidas.ancho - RELLENO * 2
        )
    elif puedo_editar:
        contenido = estado_vacio(
            ft.Icons.PHOTO_LIBRARY_OUTLINED,
            "Este portafolio esta vacio",
            "Toca los tres puntos de arriba y elegi Organizar publicaciones "
            "para meter obras aqui.",
        )
    else:
        contenido = estado_vacio(
            ft.Icons.PHOTO_LIBRARY_OUTLINED,
            "Todavia no hay nada aqui",
            "Este portafolio no tiene publicaciones que mostrar.",
        )

    acciones = (
        [boton_barra(ft.Icons.MORE_HORIZ, "Opciones del portafolio", abrir_menu)]
        if puedo_editar
        else None
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
                    screen_header("Portafolio", volver, acciones=acciones),
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            controls=[
                                cabecera_color,
                                ft.Container(
                                    padding=ft.Padding.only(
                                        left=RELLENO,
                                        right=RELLENO,
                                        top=Space.SM,
                                        bottom=Space.XL,
                                    ),
                                    content=contenido,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
