from __future__ import annotations

import flet as ft

from components.feedback import confirm_dialog, show_error, show_success
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from services import moderation_service, post_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, TextSizes

async def view(page: ft.Page, state: AppState, post_id: int) -> ft.View:
    ruta = f"/post/{post_id}/settings"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        publicacion = await post_service.get_post(post_id)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route("/profile")
        return ft.View(route=ruta, controls=[])

    soy_el_autor = bool(publicacion.get("can_edit"))
    puedo_eliminar = bool(publicacion.get("can_delete"))
    soy_admin = (state.user.get("role") or "user") == "admin"
    ya_reportado = (
        False if soy_el_autor else await moderation_service.ya_reporte_publicacion(post_id)
    )
    autor = (publicacion.get("author") or {}).get("username", "")

    async def volver(e) -> None:
        await page.push_route(f"/post/{post_id}")

    async def editar(e) -> None:
        await page.push_route(f"/post/{post_id}/edit")

    async def eliminar_de_verdad(cerrar) -> None:
        try:
            await post_service.delete_post(post_id)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Publicacion eliminada")
        await page.push_route("/profile" if soy_el_autor else "/search")

    def eliminar(e) -> None:
        confirm_dialog(
            page,
            title="Eliminar publicacion",
            message=(
                "Esta publicacion, sus archivos y todos sus comentarios se "
                "eliminaran para siempre. Esta accion no se puede deshacer."
                + (
                    ""
                    if soy_el_autor
                    else f" A @{autor} le va a llegar un correo avisandole."
                )
            ),
            confirm_text="Eliminar",
            on_confirm=eliminar_de_verdad,
            danger=True,
        )

    campo_motivo = ft.TextField(
        hint_text="Que esta pasando? (opcional)",
        multiline=True,
        min_lines=2,
        max_lines=4,
        max_length=300,
        dense=True,
        counter="",
        text_style=ft.TextStyle(
            color=Colors.TEXT_BODY, size=pantalla().texto(TextSizes.BODY)
        ),
        hint_style=ft.TextStyle(color=Colors.TEXT_FAINT),
        border_color=Colors.DIVIDER,
        focused_border_color=Colors.TEXT_PRIMARY,
        cursor_color=Colors.TEXT_PRIMARY,
    )

    async def reportar_de_verdad(cerrar) -> None:
        try:
            await moderation_service.reportar_publicacion(
                post_id, (campo_motivo.value or "").strip() or None
            )
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Gracias. Un administrador va a revisarlo.")
        await page.push_route(f"/post/{post_id}")

    def reportar(e) -> None:
        campo_motivo.value = ""
        confirm_dialog(
            page,
            title="Reportar publicacion",
            message=(
                "Los administradores de Ashun van a recibir este reporte y "
                "van a revisar la publicacion. Solo ellos lo ven."
            ),
            confirm_text="Enviar reporte",
            on_confirm=reportar_de_verdad,
            danger=False,
            extra=campo_motivo,
        )

    filas: list[ft.Control] = []

    if soy_el_autor:
        filas.extend(
            [
                settings_row(ft.Icons.EDIT, "Editar Publicacion", on_click=editar),
                settings_row(
                    ft.Icons.CLOSE,
                    "Eliminar publicacion",
                    on_click=eliminar,
                    danger=True,
                ),
            ]
        )
    else:
        filas.extend(
            [
                section_title("ESTA PUBLICACION"),
                settings_row(
                    ft.Icons.FLAG_OUTLINED,
                    "Ya reportaste esta publicacion"
                    if ya_reportado
                    else "Reportar publicacion",
                    subtitulo=(
                        "Un administrador ya tiene tu aviso"
                        if ya_reportado
                        else "Solo lo ven los administradores"
                    ),
                    on_click=None if ya_reportado else reportar,
                    enabled=not ya_reportado,
                ),
                settings_row(
                    ft.Icons.VISIBILITY_OFF_OUTLINED,
                    "No me interesa",
                    on_click=None,
                    enabled=False,
                ),
            ]
        )

        if soy_admin and puedo_eliminar:
            filas.extend(
                [
                    section_title("ADMINISTRACION"),
                    settings_row(
                        ft.Icons.DELETE_OUTLINE,
                        "Eliminar publicacion",
                        subtitulo=f"A @{autor} le llega un correo",
                        on_click=eliminar,
                        danger=True,
                    ),
                ]
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
                        "Configuracion de Publicacion"
                        if soy_el_autor
                        else "Opciones",
                        volver,
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=pantalla().padding, vertical=10
                        ),
                        content=ft.Column(
                            spacing=2,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            controls=filas,
                        ),
                    ),
                ],
            )
        ],
    )
