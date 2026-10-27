from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

import flet as ft

from components.buttons import loading_button
from components.feedback import show_error, show_success
from components.layout import safe_update, vspace
from components.post_media import kind_from_name, media_carousel
from components.tag_chip import selectable_chip
from context.app_state import AppState
from services import post_service
from services.api_client import ApiError
from style.theme import Colors, Sizes, TextSizes

MAX_ARCHIVOS = 10

MIN_DESCRIPCION = 10

async def view(
    page: ft.Page, state: AppState, post_id: int | None = None
) -> ft.View:
    ruta = "/post/new" if post_id is None else f"/post/{post_id}/edit"

    if not state.user:
        await page.push_route("/login")
        return ft.View(route=ruta, controls=[])

    datos: dict[str, Any] = {
        "nuevos": [],
        "existentes": [],
        "a_borrar": [],
        "indice": 0,
    }

    seleccionados: list[int] = []

    titulo_field = ft.TextField(
        hint_text="Titulo",
        border=ft.InputBorder.NONE,
        filled=True,
        fill_color=Colors.SURFACE,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        text_size=TextSizes.BODY,
        max_length=120,
        text_style=ft.TextStyle(color=Colors.TEXT_BODY),
        cursor_color=Colors.TEXT_PRIMARY,
    )

    descripcion_field = ft.TextField(
        hint_text="Descripcion",
        border=ft.InputBorder.NONE,
        filled=True,
        fill_color=Colors.SURFACE,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        text_size=TextSizes.BODY,
        multiline=True,
        min_lines=4,
        max_lines=8,
        text_style=ft.TextStyle(color=Colors.TEXT_BODY),
        cursor_color=Colors.TEXT_PRIMARY,
    )

    media_box = ft.Container(
        height=260,
        bgcolor=Colors.SURFACE,
        border_radius=10,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )
    chips_row = ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[])
    contador = ft.Text("", size=TextSizes.SMALL, color=Colors.TEXT_MUTED)

    tags_disponibles: list[dict[str, Any]] = []
    try:
        tags_disponibles = await state.load_tags()
    except ApiError as error:
        show_error(page, error.message)

    if post_id is not None:
        try:
            publicacion = await post_service.get_post(post_id)
        except ApiError as error:
            show_error(page, error.message)
            await page.push_route("/profile")
            return ft.View(route=ruta, controls=[])

        titulo_field.value = publicacion.get("title") or ""
        descripcion_field.value = publicacion.get("description") or ""
        datos["existentes"] = list(publicacion.get("files") or [])
        seleccionados.extend(t["id"] for t in (publicacion.get("tags") or []))

    def archivos_visibles() -> list[dict[str, Any]]:
        vivos = [f for f in datos["existentes"] if f["id"] not in datos["a_borrar"]]
        return vivos + datos["nuevos"]

    def pintar_media() -> None:
        visibles = archivos_visibles()
        contador.value = f"{len(visibles)} de {MAX_ARCHIVOS} archivos"

        if not visibles:
            media_box.content = ft.Container(
                alignment=ft.Alignment.CENTER,
                on_click=elegir_archivos,
                ink=True,
                content=ft.Icon(ft.Icons.ADD, size=70, color=Colors.TEXT_PRIMARY),
            )
        else:
            media_box.content = ft.Stack(
                expand=True,
                controls=[
                    media_carousel(visibles, alto=260),
                    ft.Container(
                        right=6,
                        top=6,
                        content=ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=18,
                            icon_color=Colors.TEXT_ON_DARK,
                            bgcolor="#000000AA",
                            tooltip="Quitar el primero",
                            on_click=quitar_primero,
                        ),
                    ),
                    ft.Container(
                        right=6,
                        bottom=6,
                        content=ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_size=18,
                            icon_color=Colors.TEXT_ON_DARK,
                            bgcolor="#000000AA",
                            tooltip="Agregar otro archivo",
                            on_click=elegir_archivos,
                        ),
                    ),
                ],
            )

        safe_update(media_box, contador)

    def pintar_chips() -> None:
        chips_row.controls = [
            selectable_chip(
                tag,
                selected=tag["id"] in seleccionados,
                on_toggle=alternar_tag,
            )
            for tag in tags_disponibles
        ]
        safe_update(chips_row)

    def alternar_tag(tag: dict[str, Any]) -> None:
        if tag["id"] in seleccionados:
            seleccionados.remove(tag["id"])
        else:
            if len(seleccionados) >= 10:
                show_error(page, "Puedes elegir como maximo 10 especialidades")
                return
            seleccionados.append(tag["id"])
        pintar_chips()

    selector = ft.FilePicker()

    async def elegir_archivos(e) -> None:
        libres = MAX_ARCHIVOS - len(archivos_visibles())
        if libres <= 0:
            show_error(page, f"Ya tienes el maximo de {MAX_ARCHIVOS} archivos")
            return

        elegidos = await selector.pick_files(
            dialog_title="Elige los archivos de tu publicacion",
            allow_multiple=True,
        )

        if not elegidos:
            return

        if len(elegidos) > libres:
            show_error(page, f"Solo caben {libres} archivo(s) mas")
            elegidos = elegidos[:libres]

        for archivo in elegidos:
            if not archivo.path:
                show_error(
                    page,
                    "Para elegir archivos, ejecuta la app en modo escritorio "
                    "(python main.py) en vez del navegador",
                )
                return

            ruta_local = Path(archivo.path)
            try:
                contenido = ruta_local.read_bytes()
            except OSError:
                show_error(page, f"No se pudo leer {ruta_local.name}")
                continue

            datos["nuevos"].append(
                {
                    "name": ruta_local.name,
                    "bytes": contenido,
                    "kind": kind_from_name(ruta_local.name),
                    "url": str(ruta_local),
                }
            )

        pintar_media()

    def quitar_primero(e) -> None:
        visibles = archivos_visibles()
        if not visibles:
            return

        primero = visibles[0]
        if "id" in primero:
            datos["a_borrar"].append(primero["id"])
        else:
            datos["nuevos"].remove(primero)

        pintar_media()

    def falta_contenido() -> bool:
        if archivos_visibles():
            return False
        return len((descripcion_field.value or "").strip()) < MIN_DESCRIPCION

    async def guardar(e) -> None:
        if falta_contenido():
            show_error(
                page,
                f"Una publicacion sin archivos necesita una descripcion de al "
                f"menos {MIN_DESCRIPCION} caracteres",
            )
            return

        set_loading(True)
        titulo = (titulo_field.value or "").strip() or None
        descripcion = (descripcion_field.value or "").strip() or None

        try:
            if post_id is None:
                publicacion = await post_service.create_post(
                    title=titulo, description=descripcion, tag_ids=seleccionados
                )
                nuevo_id = publicacion["id"]

                await subir_pendientes(nuevo_id)

                await post_service.publish_post(nuevo_id)
                show_success(page, "Publicacion creada")
                await page.push_route("/profile")
            else:
                await post_service.update_post(
                    post_id, title=titulo, description=descripcion, tag_ids=seleccionados
                )

                for file_id in datos["a_borrar"]:
                    await post_service.delete_file(post_id, file_id)

                await subir_pendientes(post_id)

                show_success(page, "Publicacion actualizada")
                await page.push_route(f"/post/{post_id}")

        except ApiError as error:
            show_error(page, error.message)
        finally:
            set_loading(False)

    async def subir_pendientes(destino: int) -> None:
        for archivo in datos["nuevos"]:
            mime, _ = mimetypes.guess_type(archivo["name"])
            await post_service.upload_file(
                destino,
                archivo["name"],
                archivo["bytes"],
                mime or "application/octet-stream",
            )
        datos["nuevos"] = []

    async def volver(e) -> None:
        if post_id is None:
            await page.push_route("/profile")
        else:
            await page.push_route(f"/post/{post_id}")

    boton_guardar, set_loading = loading_button("Publicar", guardar)

    pintar_media()
    pintar_chips()

    encabezado = ft.Container(
        padding=ft.Padding.only(left=4, right=10, top=6, bottom=4),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW,
                    icon_size=20,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Volver",
                    on_click=volver,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CHECK,
                    icon_size=26,
                    icon_color=Colors.TEXT_PRIMARY,
                    tooltip="Publicar",
                    on_click=guardar,
                ),
            ],
        ),
    )

    return ft.View(
        route=ruta,
        padding=0,
        spacing=0,
        bgcolor=Colors.BACKGROUND,
        services=[selector],
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    encabezado,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=Sizes.PAGE_PADDING),
                        content=ft.Column(
                            spacing=12,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                media_box,
                                contador,
                                chips_row,
                                vspace(2),
                                titulo_field,
                                descripcion_field,
                                vspace(6),
                                boton_guardar,
                                vspace(20),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
