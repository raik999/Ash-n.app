from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import flet as ft

from components.feedback import avatar_view, foto_de, show_error
from components.compose_bar import barra_de_escritura, vaciar
from components.layout import safe_update
from components.settings_row import boton_barra, screen_header
from context.app_state import AppState
from services import chat_service
from services.chat_service import MAX_MENSAJE
from services.api_client import ApiError, api
from services.realtime_service import EVENTO_CHAT_ELIMINADO, EVENTO_MENSAJE
from style.responsive import pantalla
from style.theme import Colors, Fonts, Radius, Space, Sizes, TextSizes

def hora_corta(cuando: str | None) -> str:
    if not cuando:
        return ""

    try:
        momento = datetime.fromisoformat(cuando.replace("Z", "+00:00"))
    except ValueError:
        return ""

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    return momento.astimezone().strftime("%H:%M")

async def view(page: ft.Page, state: AppState, chat_id: int) -> ft.View:
    ruta = f"/chat/{chat_id}"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    try:
        chat: dict[str, Any] = await chat_service.get_chat(chat_id)
    except ApiError as error:
        return ft.View(
            route=ruta,
            padding=0,
            bgcolor=Colors.BACKGROUND,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ft.Container(
                            padding=ft.Padding.only(left=6, top=10),
                            content=ft.IconButton(
                                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                                icon_size=20,
                                icon_color=Colors.TEXT_PRIMARY,
                                on_click=lambda e: None,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                error.message,
                                size=TextSizes.BODY,
                                color=Colors.TEXT_MUTED,
                            ),
                        ),
                    ],
                )
            ],
        )

    otro = chat["other"]

    async def volver(e) -> None:
        await page.push_route("/chats")

    async def ir_al_perfil(e) -> None:
        await page.push_route(f"/user/{otro['username']}")

    async def ir_a_configuracion(e) -> None:
        await page.push_route(f"/chat/{chat_id}/settings")

    mensajes = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    dibujados: set[int] = set()

    def burbuja(mensaje: dict[str, Any]) -> ft.Control:
        mio = bool(mensaje.get("mine"))

        cuerpo = ft.Container(
            bgcolor=Colors.BRAND_DARK if mio else Colors.SURFACE,
            border_radius=ft.BorderRadius(
                top_left=14,
                top_right=14,
                bottom_left=4 if not mio else 14,
                bottom_right=4 if mio else 14,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=(
                    ft.CrossAxisAlignment.END if mio else ft.CrossAxisAlignment.START
                ),
                controls=[
                    ft.Text(
                        mensaje["text"],
                        size=TextSizes.BODY,
                        color=Colors.TEXT_ON_DARK if mio else Colors.TEXT_BODY,
                        selectable=True,
                    ),
                    ft.Text(
                        hora_corta(mensaje.get("created_at")),
                        size=pantalla().texto(TextSizes.SMALL),
                        color=(
                            Colors.TEXT_ON_DARK_SOFT if mio else Colors.TEXT_MUTED
                        ),
                    ),
                ],
            ),
        )

        return ft.Row(
            alignment=(
                ft.MainAxisAlignment.END if mio else ft.MainAxisAlignment.START
            ),
            controls=[
                ft.Container(content=cuerpo, width=None, expand=False),
            ],
        )

    def agregar(mensaje: dict[str, Any]) -> bool:
        identificador = mensaje.get("id")

        if identificador in dibujados:
            return False

        dibujados.add(identificador)
        mensajes.controls.append(burbuja(mensaje))
        return True

    def vacio() -> ft.Control:
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=40,
            content=ft.Text(
                f"Escribile a {otro['username']} para empezar",
                size=TextSizes.BODY,
                color=Colors.TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    for mensaje in chat.get("messages") or []:
        agregar(mensaje)

    if not mensajes.controls:
        mensajes.controls.append(vacio())

    async def enviar(e=None) -> None:
        texto = (campo.value or "").strip()

        if not texto:
            return

        try:
            mensaje = await chat_service.send_message(chat_id, texto)
        except ApiError as error:
            show_error(page, error.message)
            return

        if not dibujados:
            mensajes.controls.clear()

        agregar(mensaje)

        vaciar(campo)
        safe_update(mensajes)

    barra_escritura, campo = barra_de_escritura(
        hint="Escribe un mensaje",
        maximo=MAX_MENSAJE,
        al_enviar=enviar,
        tooltip_enviar=f"Enviar a {otro['username']}",
    )

    async def al_recibir(tipo: str, datos: Any) -> None:
        if tipo == EVENTO_MENSAJE:
            if int(datos.get("chat_id") or 0) != chat_id:
                return

            if not dibujados:
                mensajes.controls.clear()

            if agregar(datos):
                safe_update(mensajes)

                try:
                    await chat_service.mark_read(chat_id)
                except ApiError:
                    pass

        elif tipo == EVENTO_CHAT_ELIMINADO:
            if int(datos.get("id") or 0) != chat_id:
                return

            show_error(page, "El otro usuario elimino este chat")
            await page.push_route("/chats")

    state.vivo.suscribir("chat", al_recibir)

    titulo_tocable = ft.Container(
        ink=True,
        border_radius=Radius.SM,
        on_click=ir_al_perfil,
        tooltip=f"Ver el perfil de {otro['username']}",
        padding=ft.Padding.symmetric(horizontal=Space.XS, vertical=Space.XXS),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Space.XS + 2,
            controls=[
                ft.Container(
                    width=pantalla().avatar(38),
                    height=pantalla().avatar(38),
                    content=avatar_view(
                        foto_de(otro),
                        pantalla().avatar(38),
                    ),
                ),
                ft.Text(
                    otro["username"],
                    size=pantalla().texto(TextSizes.SUBTITLE),
                    color=Colors.TEXT_PRIMARY,
                    font_family=Fonts.HEADING,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )

    cabecera = screen_header(
        otro["username"],
        volver,
        principal=titulo_tocable,
        acciones=[
            boton_barra(
                ft.Icons.MORE_HORIZ,
                "Configuracion del chat",
                ir_a_configuracion,
            )
        ],
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
                    cabecera,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(
                            horizontal=pantalla().padding, vertical=12
                        ),
                        content=mensajes,
                    ),
                    barra_escritura,
                ],
            )
        ],
    )
