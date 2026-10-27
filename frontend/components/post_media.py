from __future__ import annotations
from typing import Any

import flet as ft
import flet_audio as fa
import flet_video as fv

from services.api_client import api
from style.theme import Colors, TextSizes

KIND_IMAGE = "image"
KIND_VIDEO = "video"
KIND_AUDIO = "audio"

EXTENSIONES = {
    KIND_IMAGE: {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    KIND_VIDEO: {".mp4", ".webm", ".avi", ".mov", ".mkv"},
    KIND_AUDIO: {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"},
}

def kind_from_name(filename: str) -> str:
    punto = filename.rfind(".")
    extension = filename[punto:].lower() if punto >= 0 else ""
    for kind, extensiones in EXTENSIONES.items():
        if extension in extensiones:
            return kind
    return KIND_IMAGE

def _tarjeta(icono: str, texto: str, color_fondo: str, pequena: bool) -> ft.Container:
    return ft.Container(
        bgcolor=color_fondo,
        alignment=ft.Alignment.CENTER,
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            tight=True,
            controls=[
                ft.Icon(icono, size=28 if pequena else 54, color=Colors.TEXT_ON_DARK),
                ft.Text(
                    texto,
                    size=TextSizes.SMALL if pequena else TextSizes.BODY,
                    color=Colors.TEXT_ON_DARK,
                ),
            ],
        ),
    )

def _tarjeta_texto(description: str | None, title: str | None, pequena: bool) -> ft.Container:
    cuerpo = (description or title or "Sin texto").strip()

    return ft.Container(
        bgcolor=Colors.PEACH_SOFT,
        padding=10,
        expand=True,
        content=ft.Column(
            spacing=4,
            tight=True,
            controls=[
                ft.Text(
                    cuerpo,
                    size=TextSizes.SMALL if pequena else TextSizes.BODY,
                    color=Colors.TEXT_BODY,
                    max_lines=5 if pequena else 12,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )

def grid_cell(post: dict[str, Any], on_click) -> ft.Container:
    preview = post.get("preview")

    if preview is None:
        contenido: ft.Control = _tarjeta_texto(
            post.get("description"), post.get("title"), pequena=True
        )
    elif preview["kind"] == KIND_IMAGE:
        contenido = ft.Image(
            src=api.absolute_url(preview["url"]),
            fit=ft.BoxFit.COVER,
            expand=True,
            error_content=ft.Container(bgcolor=Colors.SURFACE, expand=True),
        )
    elif preview["kind"] == KIND_VIDEO:
        contenido = _tarjeta(ft.Icons.PLAY_CIRCLE_OUTLINE, "Video", "#2B2B2B", pequena=True)
    else:
        contenido = _tarjeta(ft.Icons.MUSIC_NOTE, "Audio", "#5B3DA8", pequena=True)

    capas: list[ft.Control] = [ft.Container(content=contenido, expand=True)]
    if (post.get("files_count") or 0) > 1:
        capas.append(
            ft.Container(
                right=6,
                top=6,
                bgcolor="#000000AA",
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                content=ft.Text(
                    f"{post['files_count']}",
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_ON_DARK,
                ),
            )
        )

    return ft.Container(
        bgcolor=Colors.SURFACE,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        on_click=on_click,
        ink=True,
        content=ft.Stack(controls=capas, expand=True),
    )

def new_post_cell(on_click) -> ft.Container:
    return ft.Container(
        bgcolor=Colors.SURFACE,
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        ink=True,
        tooltip="Crear una publicacion",
        content=ft.Icon(ft.Icons.ADD, size=44, color=Colors.TEXT_PRIMARY),
    )

def audio_player(url: str) -> ft.Control:
    estado = {"sonando": False, "empezado": False}

    boton = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,
        icon_size=40,
        icon_color=Colors.TEXT_ON_DARK,
    )

    def on_state_change(e) -> None:
        terminada = str(getattr(e, "state", "")).upper().endswith("COMPLETED")
        if terminada:
            estado["sonando"] = False
            estado["empezado"] = False
            boton.icon = ft.Icons.PLAY_ARROW
            try:
                boton.update()
            except Exception:
                pass

    audio = fa.Audio(src=api.absolute_url(url), autoplay=False, on_state_change=on_state_change)

    async def alternar(e) -> None:
        if estado["sonando"]:
            await audio.pause()
            estado["sonando"] = False
            boton.icon = ft.Icons.PLAY_ARROW
        else:
            if estado["empezado"]:
                await audio.resume()
            else:
                await audio.play()
                estado["empezado"] = True
            estado["sonando"] = True
            boton.icon = ft.Icons.PAUSE
        boton.update()

    boton.on_click = alternar

    return ft.Container(
        bgcolor="#5B3DA8",
        alignment=ft.Alignment.CENTER,
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
            controls=[
                ft.Icon(ft.Icons.MUSIC_NOTE, size=44, color="#FFFFFF88"),
                boton,
                ft.Text("Cancion", size=TextSizes.SMALL, color=Colors.TEXT_ON_DARK),
            ],
        ),
    )

def text_panel(texto: str | None, alto: int = 200) -> ft.Container:
    return ft.Container(
        bgcolor=Colors.PEACH_SOFT,
        padding=ft.Padding.symmetric(horizontal=18, vertical=20),
        alignment=ft.Alignment.CENTER,
        height=alto,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            tight=True,
            controls=[
                ft.Text(
                    (texto or "").strip(),
                    size=TextSizes.SUBTITLE,
                    color=Colors.TEXT_BODY,
                    text_align=ft.TextAlign.CENTER,
                )
            ],
        ),
    )

def media_item(archivo: dict[str, Any]) -> ft.Control:
    es_local = bool(archivo.get("local"))
    url = archivo["url"] if es_local else api.absolute_url(archivo["url"])
    kind = archivo.get("kind")

    if es_local and kind == KIND_VIDEO:
        return _tarjeta(ft.Icons.PLAY_CIRCLE_OUTLINE, "Video listo para subir", "#2B2B2B", False)
    if es_local and kind == KIND_AUDIO:
        return _tarjeta(ft.Icons.MUSIC_NOTE, "Cancion lista para subir", "#5B3DA8", False)

    if kind == KIND_VIDEO:
        return fv.Video(
            playlist=[fv.VideoMedia(resource=url)],
            autoplay=False,
            controls=True,
            muted=False,
            fit=ft.BoxFit.CONTAIN,
            expand=True,
        )

    if kind == KIND_AUDIO:
        return audio_player(archivo["url"])

    return ft.Image(
        src=url,
        fit=ft.BoxFit.CONTAIN,
        expand=True,
        error_content=ft.Container(
            bgcolor=Colors.SURFACE,
            alignment=ft.Alignment.CENTER,
            content=ft.Text("No se pudo cargar", color=Colors.TEXT_MUTED),
        ),
    )

def media_carousel(archivos: list[dict[str, Any]], alto: int = 300) -> ft.Control:
    if not archivos:
        return ft.Container(height=0)

    puntos = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=6, controls=[])

    def pintar_puntos(actual: int) -> None:
        puntos.controls = [
            ft.Container(
                width=7,
                height=7,
                border_radius=4,
                bgcolor=Colors.BRAND_DARK if i == actual else "#C9C9C9",
            )
            for i in range(len(archivos))
        ]

    pintar_puntos(0)

    def on_change(e) -> None:
        pintar_puntos(e.control.selected_index or 0)
        try:
            puntos.update()
        except Exception:
            pass

    vista = ft.PageView(
        controls=[media_item(a) for a in archivos],
        selected_index=0,
        on_change=on_change,
        expand=True,
    )

    hijos: list[ft.Control] = [ft.Container(content=vista, height=alto, bgcolor=Colors.SURFACE)]
    if len(archivos) > 1:
        hijos.append(ft.Container(content=puntos, padding=ft.Padding.only(top=8)))

    return ft.Column(spacing=0, tight=True, controls=hijos)
