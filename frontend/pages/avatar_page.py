from __future__ import annotations

import mimetypes
from pathlib import Path

import flet as ft

from components.brand_header import brand_header, screen_title
from components.buttons import link_button, loading_button
from components.feedback import avatar_view, show_error, show_success
from components.layout import full_width, screen, vspace
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, Sizes, TextSizes

MAX_FILE_SIZE = 5 * 1024 * 1024


def view(page: ft.Page, state: AppState, next_route: str = "/profile") -> ft.View:
    pending: dict[str, object] = {"path": None, "name": None}

    avatar_holder = ft.Container(
        content=avatar_view(state.avatar_url, Sizes.AVATAR_LARGE + 70),
        alignment=ft.alignment.center,
    )

    def on_file_selected(e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            return

        selected = e.files[0]

        if not selected.path:
            show_error(
                page,
                "Para elegir una foto, ejecuta la app en modo escritorio "
                "(python main.py) en vez del navegador",
            )
            return

        if selected.size and selected.size > MAX_FILE_SIZE:
            show_error(page, "La imagen no puede pesar mas de 5 MB")
            return

        pending["path"] = selected.path
        pending["name"] = selected.name

        avatar_holder.content = ft.Container(
            width=Sizes.AVATAR_LARGE + 70,
            height=Sizes.AVATAR_LARGE + 70,
            border_radius=(Sizes.AVATAR_LARGE + 70) / 2,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Image(src=selected.path, fit=ft.ImageFit.COVER),
        )
        avatar_holder.update()

    file_picker = ft.FilePicker(on_result=on_file_selected)

    if file_picker not in page.overlay:
        page.overlay.append(file_picker)
        page.update()

    def open_file_picker(e: ft.ControlEvent) -> None:
        file_picker.pick_files(
            dialog_title="Elige tu foto de perfil",
            file_type=ft.FilePickerFileType.IMAGE,
            allow_multiple=False,
        )

    def do_save(e: ft.ControlEvent | None = None) -> None:
        path = pending["path"]

        if not path:
            page.go(next_route)
            return

        set_loading(True)
        try:
            file_path = Path(str(path))

            content = file_path.read_bytes()

            mime, _ = mimetypes.guess_type(file_path.name)

            result = user_service.upload_avatar(
                filename=file_path.name,
                content=content,
                mime=mime or "image/png",
            )

            if state.user is not None:
                state.user["avatar_url"] = result["avatar_url"]

            show_success(page, "Foto de perfil actualizada")
            page.go(next_route)

        except FileNotFoundError:
            show_error(page, "No se encontro el archivo, vuelve a elegirlo")
        except ApiError as error:
            show_error(page, error.message)
        finally:
            set_loading(False)

    def do_skip(e: ft.ControlEvent) -> None:
        page.go(next_route)

    done_button, set_loading = loading_button("Listo", do_save)

    return ft.View(
        route=page.route,
        padding=0,
        controls=[
            screen(
                vspace(28),
                brand_header(),
                vspace(50),
                screen_title(
                    "Escoge tu foto de perfil",
                    "Selecciona una imagen que te identifique",
                ),
                vspace(50),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Stack(
                            width=Sizes.AVATAR_LARGE + 70,
                            height=Sizes.AVATAR_LARGE + 70,
                            controls=[
                                avatar_holder,
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.ADD,
                                        size=34,
                                        color=Colors.BRAND_DARK,
                                    ),
                                    width=58,
                                    height=58,
                                    bgcolor="#C4C4C4",
                                    border_radius=29,
                                    alignment=ft.alignment.center,
                                    on_click=open_file_picker,
                                    ink=True,
                                    right=0,
                                    bottom=8,
                                    tooltip="Elegir una foto",
                                ),
                            ],
                        )
                    ],
                ),
                vspace(20),
                ft.Text(
                    "JPG, PNG, WEBP o GIF. Maximo 5 MB.",
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(expand=True),
                full_width(done_button),
                vspace(10),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[link_button("Omitir", do_skip)],
                ),
                vspace(30),
            )
        ],
    )
