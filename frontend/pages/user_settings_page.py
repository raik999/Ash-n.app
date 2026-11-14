from __future__ import annotations

import flet as ft

from components.feedback import (
    avatar_view,
    confirm_dialog,
    foto_de,
    show_error,
    show_success,
)
from components.settings_row import screen_header, section_title, settings_row
from context.app_state import AppState
from services import moderation_service, user_service
from services.api_client import ApiError
from style.responsive import pantalla
from style.theme import Colors, Radius, Space, TextSizes

DURACIONES = [
    ("1", "1 dia"),
    ("3", "3 dias"),
    ("7", "7 dias"),
    ("30", "30 dias"),
]

async def view(page: ft.Page, state: AppState, username: str) -> ft.View:
    ruta = f"/user/{username}/settings"
    medidas = pantalla()

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    if username.lower() == (state.user.get("username") or "").lower():
        await page.push_route("/settings")
        return ft.View(route=ruta, controls=[])

    try:
        perfil = await user_service.get_public_profile(username)
    except ApiError as error:
        show_error(page, error.message)
        await page.push_route(f"/user/{username}")
        return ft.View(route=ruta, controls=[])

    soy_admin = (state.user.get("role") or "user") == "admin"
    ya_reportado = await moderation_service.ya_reporte_usuario(username)

    async def volver(e) -> None:
        await page.push_route(f"/user/{username}")

    campo_motivo = ft.TextField(
        hint_text="Que esta pasando? (opcional)",
        multiline=True,
        min_lines=2,
        max_lines=4,
        max_length=300,
        dense=True,
        counter="",
        text_style=ft.TextStyle(
            color=Colors.TEXT_BODY, size=medidas.texto(TextSizes.BODY)
        ),
        hint_style=ft.TextStyle(color=Colors.TEXT_FAINT),
        border_color=Colors.DIVIDER,
        focused_border_color=Colors.TEXT_PRIMARY,
        cursor_color=Colors.TEXT_PRIMARY,
    )

    async def reportar_de_verdad(cerrar) -> None:
        try:
            await moderation_service.reportar_usuario(
                username, (campo_motivo.value or "").strip() or None
            )
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, "Gracias. Un administrador va a revisarlo.")
        await page.push_route(f"/user/{username}")

    def reportar(e) -> None:
        campo_motivo.value = ""
        confirm_dialog(
            page,
            title=f"Reportar a {perfil['username']}",
            message=(
                "Los administradores de Ashun van a recibir este reporte y "
                "van a revisar la cuenta. Solo ellos lo ven."
            ),
            confirm_text="Enviar reporte",
            on_confirm=reportar_de_verdad,
            danger=False,
            extra=campo_motivo,
        )

    dias_elegidos = ft.RadioGroup(
        value="7",
        content=ft.Row(
            wrap=True,
            spacing=0,
            run_spacing=0,
            controls=[
                ft.Radio(
                    value=clave,
                    label=etiqueta,
                    active_color=Colors.BRAND_DARK,
                    label_style=ft.TextStyle(
                        size=medidas.texto(TextSizes.LABEL), color=Colors.TEXT_BODY
                    ),
                )
                for clave, etiqueta in DURACIONES
            ],
        ),
    )

    campo_motivo_sancion = ft.TextField(
        hint_text="Motivo (le llega por correo)",
        multiline=True,
        min_lines=2,
        max_lines=3,
        max_length=300,
        dense=True,
        counter="",
        text_style=ft.TextStyle(
            color=Colors.TEXT_BODY, size=medidas.texto(TextSizes.BODY)
        ),
        hint_style=ft.TextStyle(color=Colors.TEXT_FAINT),
        border_color=Colors.DIVIDER,
        focused_border_color=Colors.TEXT_PRIMARY,
        cursor_color=Colors.TEXT_PRIMARY,
    )

    async def sancionar_de_verdad(cerrar) -> None:
        try:
            dias = int(dias_elegidos.value or "7")
        except ValueError:
            dias = 7

        try:
            resultado = await moderation_service.sancionar(
                username, dias, (campo_motivo_sancion.value or "").strip() or None
            )
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        restantes = resultado.get("dias_restantes", dias)
        show_success(
            page,
            f"@{username} no va a poder entrar durante {restantes} "
            f"{'dia' if restantes == 1 else 'dias'}",
        )
        await page.push_route(f"/user/{username}")

    def sancionar(e) -> None:
        campo_motivo_sancion.value = ""
        confirm_dialog(
            page,
            title=f"Suspender a {perfil['username']}",
            message=(
                "No va a poder iniciar sesion durante ese tiempo, y si esta "
                "dentro ahora mismo se le cierra la sesion. Le llega un "
                "correo con el motivo."
            ),
            confirm_text="Suspender",
            on_confirm=sancionar_de_verdad,
            extra=ft.Column(
                tight=True,
                spacing=Space.XS,
                controls=[dias_elegidos, campo_motivo_sancion],
            ),
        )

    async def levantar_de_verdad(cerrar) -> None:
        try:
            await moderation_service.levantar_sancion(username)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, f"@{username} ya puede volver a entrar")

    def levantar(e) -> None:
        confirm_dialog(
            page,
            title=f"Levantar la suspension de {perfil['username']}",
            message="Va a poder volver a entrar de inmediato.",
            confirm_text="Levantar",
            on_confirm=levantar_de_verdad,
            danger=False,
        )

    async def eliminar_de_verdad(cerrar) -> None:
        try:
            await moderation_service.eliminar_cuenta(username)
        except ApiError as error:
            cerrar()
            show_error(page, error.message)
            return

        cerrar()
        show_success(page, f"La cuenta de @{username} se elimino")
        await page.push_route("/search")

    def eliminar(e) -> None:
        confirm_dialog(
            page,
            title="Eliminar esta cuenta",
            message=(
                f"Se eliminan para siempre la cuenta de {perfil['name']}, sus "
                "publicaciones, sus comentarios y sus conversaciones. "
                "ESTA ACCION NO SE PUEDE DESHACER."
            ),
            confirm_text="Eliminar",
            on_confirm=eliminar_de_verdad,
            exigir_texto=f"@{perfil['username']}",
        )

    filas: list[ft.Control] = [
        ft.Container(
            bgcolor=Colors.SURFACE,
            border_radius=Radius.MD,
            padding=ft.Padding.symmetric(horizontal=Space.SM, vertical=Space.SM),
            content=ft.Row(
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=medidas.avatar(48),
                        height=medidas.avatar(48),
                        content=avatar_view(foto_de(perfil), medidas.avatar(48)),
                    ),
                    ft.Column(
                        spacing=0,
                        tight=True,
                        controls=[
                            ft.Text(
                                perfil.get("name") or "",
                                size=medidas.texto(TextSizes.BODY),
                                color=Colors.TEXT_PRIMARY,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                f"@{perfil.get('username', '')}",
                                size=medidas.texto(TextSizes.SMALL),
                                color=Colors.TEXT_MUTED,
                            ),
                        ],
                    ),
                ],
            ),
        ),
        section_title("ESTA CUENTA"),
        settings_row(
            ft.Icons.FLAG_OUTLINED,
            "Ya reportaste esta cuenta" if ya_reportado else "Reportar cuenta",
            subtitulo=(
                "Un administrador ya tiene tu aviso"
                if ya_reportado
                else "Solo lo ven los administradores"
            ),
            on_click=None if ya_reportado else reportar,
            enabled=not ya_reportado,
        ),
        settings_row(
            ft.Icons.BLOCK,
            "Bloquear usuario",
            on_click=None,
            enabled=False,
        ),
    ]

    if soy_admin:
        filas.extend(
            [
                section_title("ADMINISTRACION"),
                settings_row(
                    ft.Icons.TIMER_OUTLINED,
                    "Suspender cuenta",
                    subtitulo="No va a poder entrar durante los dias que elijas",
                    on_click=sancionar,
                ),
                settings_row(
                    ft.Icons.LOCK_OPEN,
                    "Levantar suspension",
                    subtitulo="Si la cuenta esta suspendida, vuelve a entrar",
                    on_click=levantar,
                ),
                ft.Container(height=Space.XS),
                settings_row(
                    ft.Icons.DELETE_OUTLINE,
                    "Eliminar cuenta",
                    on_click=eliminar,
                    danger=True,
                ),
                ft.Container(height=Space.XXS),
                ft.Text(
                    "Eliminar una cuenta borra tambien sus publicaciones, "
                    "comentarios y conversaciones. No se puede deshacer.",
                    size=medidas.texto(TextSizes.SMALL),
                    color=Colors.TEXT_MUTED,
                    style=ft.TextStyle(height=1.4),
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
                    screen_header("Opciones", volver),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=medidas.padding, vertical=Space.XS + 2
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
