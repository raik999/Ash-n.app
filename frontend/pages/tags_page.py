from __future__ import annotations

from typing import Any

import flet as ft

from components.brand_header import brand_header, screen_title
from components.buttons import loading_button
from components.feedback import show_error
from components.layout import full_width, screen, vspace
from components.tag_chip import removable_chip, selectable_chip
from context.app_state import AppState
from services import user_service
from services.api_client import ApiError
from style.theme import Colors, Fonts, TextSizes


def view(page: ft.Page, state: AppState, next_route: str = "/onboarding/avatar") -> ft.View:
    selected_ids: list[int] = list(state.user_tag_ids)

    available_wrap = ft.Row(wrap=True, spacing=10, run_spacing=10)
    selected_wrap = ft.Row(wrap=True, spacing=10, run_spacing=10)

    def refresh_chips() -> None:
        available_wrap.controls.clear()
        selected_wrap.controls.clear()

        for tag in state.tags:
            is_selected = tag["id"] in selected_ids
            available_wrap.controls.append(
                selectable_chip(tag, selected=is_selected, on_toggle=toggle_tag)
            )

        for tag_id in selected_ids:
            tag = _find_tag(state.tags, tag_id)
            if tag:
                selected_wrap.controls.append(removable_chip(tag, on_remove=remove_tag))

        if not selected_ids:
            selected_wrap.controls.append(
                ft.Text(
                    "Todavia no has elegido ninguna. Puedes omitir este paso.",
                    size=TextSizes.SMALL,
                    color=Colors.TEXT_MUTED,
                )
            )

        if available_wrap.page:
            available_wrap.update()
            selected_wrap.update()

    def toggle_tag(tag: dict[str, Any]) -> None:
        tag_id = tag["id"]

        if tag_id in selected_ids:
            selected_ids.remove(tag_id)
        else:
            if len(selected_ids) >= 10:
                show_error(page, "Puedes elegir como maximo 10 especialidades")
                return
            selected_ids.append(tag_id)

        refresh_chips()

    def remove_tag(tag: dict[str, Any]) -> None:
        if tag["id"] in selected_ids:
            selected_ids.remove(tag["id"])
            refresh_chips()

    def do_save(e: ft.ControlEvent | None = None) -> None:
        set_loading(True)
        try:
            updated_user = user_service.update_profile(tag_ids=selected_ids)
            state.set_user(updated_user)
            page.go(next_route)
        except ApiError as error:
            show_error(page, error.message)
        finally:
            set_loading(False)

    done_button, set_loading = loading_button("Listo", do_save)

    try:
        state.load_tags()
    except ApiError as error:
        show_error(page, error.message)

    refresh_chips()

    return ft.View(
        route="/onboarding/tags",
        padding=0,
        controls=[
            screen(
                vspace(28),
                brand_header(),
                vspace(36),
                screen_title(
                    "En que tipo de artes te especializas?",
                    "Selecciona las especialidades que manejes",
                ),
                vspace(26),
                available_wrap,
                vspace(40),
                ft.Text(
                    "MIS ESPECIALIDADES",
                    size=TextSizes.HEADING,
                    weight=ft.FontWeight.W_900,
                    color=Colors.TEXT_PRIMARY,
                    font_family=Fonts.HEADING,
                ),
                vspace(16),
                selected_wrap,
                ft.Container(expand=True),
                vspace(24),
                full_width(done_button),
                vspace(40),
            )
        ],
    )


def _find_tag(tags: list[dict[str, Any]], tag_id: int) -> dict[str, Any] | None:
    return next((tag for tag in tags if tag["id"] == tag_id), None)
