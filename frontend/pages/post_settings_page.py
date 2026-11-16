from __future__ import annotations

import flet as ft

from components.feedback import confirm_dialog, show_error, show_success
from components.layout import safe_update
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from services import moderation_service, portfolio_service, post_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, Radius, Space, TextSizes

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

    mis_portafolios: list[dict] = []
    ya_dentro: set[int] = set()
    if soy_el_autor:
        try:
            mis_portafolios = await portfolio_service.list_portfolios(
                state.user["username"]
            )
            ya_dentro = set(await portfolio_service.portafolios_de(post_id))
        except ApiError:
            pass

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

    es_privada = bool(publicacion.get("is_private"))

    async def cambiar_privacidad_de_verdad(cerrar) -> None:
        try:
            await portfolio_service.set_privacidad(post_id, not es_privada)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(
            page,
            "Ahora solo la ves vos" if not es_privada else "Ahora la puede ver cualquiera",
        )
        await page.push_route(f"/post/{post_id}/settings")

    def cambiar_privacidad(e) -> None:
        if es_privada:
            mensaje = (
                "Va a volver a aparecer en tu perfil y cualquiera va a poder "
                "verla, darle me gusta y comentarla.\n\n"
                "Los me gusta y comentarios que tenia antes de esconderla "
                "vuelven con ella."
            )
            titulo = "Hacerla publica"
            boton = "Hacerla publica"
        else:
            mensaje = (
                "Deja de aparecer en tu perfil, en el buscador y en los "
                "portafolios. Nadie mas va a poder abrirla.\n\n"
                "Sus me gusta y comentarios no se borran: quedan guardados y "
                "vuelven si la haces publica otra vez."
            )
            titulo = "Hacerla privada"
            boton = "Hacerla privada"

        confirm_dialog(
            page,
            title=titulo,
            message=mensaje,
            confirm_text=boton,
            on_confirm=cambiar_privacidad_de_verdad,
            danger=False,
        )

    def abrir_portafolios(e) -> None:
        page.show_dialog(dialogo_portafolios)

    def cerrar_portafolios(e=None) -> None:
        page.pop_dialog()

    def fila_de_portafolio(portafolio: dict) -> ft.Control:
        pid = portafolio["id"]
        dentro = pid in ya_dentro

        marca = ft.Icon(
            ft.Icons.CHECK_CIRCLE if dentro else ft.Icons.RADIO_BUTTON_UNCHECKED,
            size=22,
            color=Colors.BRAND_DARK if dentro else Colors.TEXT_FAINT,
        )

        async def alternar(evento) -> None:
            try:
                if pid in ya_dentro:
                    await portfolio_service.remove_post(pid, post_id)
                    ya_dentro.discard(pid)
                else:
                    await portfolio_service.add_post(pid, post_id)
                    ya_dentro.add(pid)
            except ApiError as error:
                show_error(page, error.message)
                return

            esta = pid in ya_dentro
            marca.name = (
                ft.Icons.CHECK_CIRCLE if esta else ft.Icons.RADIO_BUTTON_UNCHECKED
            )
            marca.color = Colors.BRAND_DARK if esta else Colors.TEXT_FAINT
            safe_update(marca)

        return ft.Container(
            on_click=alternar,
            ink=True,
            border_radius=Radius.SM,
            padding=ft.Padding.symmetric(horizontal=Space.XS, vertical=Space.XS),
            content=ft.Row(
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=28,
                        height=28,
                        bgcolor=portafolio.get("color") or Colors.CHIP_FALLBACK,
                        border_radius=Radius.XS,
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            portafolio.get("title") or "",
                            size=pantalla().texto(TextSizes.BODY),
                            color=Colors.TEXT_BODY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    marca,
                ],
            ),
        )

    dialogo_portafolios = ft.AlertDialog(
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        bgcolor=Colors.BACKGROUND,
        title=ft.Text(
            "Agregar a portafolio",
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY,
            size=pantalla().texto(TextSizes.SUBTITLE),
        ),
        content=ft.Container(
            width=min(320, pantalla().ancho - 80),
            content=ft.Column(
                tight=True,
                spacing=2,
                scroll=ft.ScrollMode.AUTO,
                controls=[fila_de_portafolio(p) for p in mis_portafolios],
            ),
        ),
        actions=[ft.TextButton("Listo", on_click=cerrar_portafolios)],
        actions_alignment=ft.MainAxisAlignment.END,
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
                    ft.Icons.LOCK_OUTLINE if es_privada else ft.Icons.PUBLIC,
                    "Privada" if es_privada else "Publica",
                    subtitulo=(
                        "Solo la ves vos. Toca para hacerla publica"
                        if es_privada
                        else "Cualquiera la puede ver. Toca para hacerla privada"
                    ),
                    on_click=cambiar_privacidad,
                    show_chevron=False,
                ),
                settings_row(
                    ft.Icons.COLLECTIONS_OUTLINED,
                    "Agregar a portafolio",
                    subtitulo=(
                        f"Esta en {len(ya_dentro)} de tus {len(mis_portafolios)}"
                        if mis_portafolios
                        else "Todavia no tienes portafolios"
                    ),
                    on_click=abrir_portafolios if mis_portafolios else None,
                    enabled=bool(mis_portafolios),
                ),
                ft.Container(height=Space.XS),
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
