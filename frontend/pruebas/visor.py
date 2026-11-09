from __future__ import annotations

import time

from typing import Any

import flet as ft

from pruebas.piloto import Paso, Piloto, enrutador_de_app
from pruebas.recorridos import RECORRIDOS
from style.theme import Colors, Fonts, TextSizes, app_theme

PAUSA = 0.6

class Barra:
    def __init__(self) -> None:
        self.titulo = ft.Text(
            "Ashün — visor de pruebas",
            size=TextSizes.BODY,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_ON_DARK,
        )
        self.detalle = ft.Text(
            "Elegí un recorrido",
            size=TextSizes.SMALL,
            color=Colors.TEXT_ON_DARK,
        )
        self.avance = ft.ProgressBar(
            value=0,
            height=3,
            color=Colors.TEXT_ON_DARK,
            bgcolor="#FFFFFF44",
        )

    def construir(self) -> ft.AppBar:
        return ft.AppBar(
            bgcolor=Colors.BRAND_DARK,
            toolbar_height=58,
            title=ft.Column(
                spacing=1,
                tight=True,
                controls=[self.titulo, self.detalle, self.avance],
            ),
            center_title=False,
        )

    def anunciar(self, titulo: str, detalle: str, avance: float) -> None:
        self.titulo.value = titulo
        self.detalle.value = detalle
        self.avance.value = avance

def vista_menu(barra: Barra, elegir: Any) -> ft.View:
    tarjetas: list[ft.Control] = []

    for clave, receta in RECORRIDOS.items():
        tarjetas.append(
            ft.Container(
                bgcolor=Colors.SURFACE,
                border_radius=12,
                padding=16,
                ink=True,
                on_click=lambda e, c=clave: elegir(c),
                content=ft.Column(
                    spacing=6,
                    tight=True,
                    controls=[
                        ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.Icon(
                                    ft.Icons.PLAY_CIRCLE_FILL,
                                    size=26,
                                    color=Colors.BRAND_DARK,
                                ),
                                ft.Text(
                                    receta["titulo"],
                                    size=TextSizes.SUBTITLE,
                                    weight=ft.FontWeight.BOLD,
                                    color=Colors.TEXT_PRIMARY,
                                ),
                            ],
                        ),
                        ft.Text(
                            receta["resumen"],
                            size=TextSizes.SMALL,
                            color=Colors.TEXT_MUTED,
                        ),
                    ],
                ),
            )
        )
        tarjetas.append(ft.Container(height=12))

    return ft.View(
        route="/visor",
        padding=20,
        bgcolor=Colors.BACKGROUND,
        appbar=barra.construir(),
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(height=10),
            ft.Text(
                "PRUEBAS DE EXTREMO A EXTREMO",
                size=TextSizes.TITLE,
                weight=ft.FontWeight.W_900,
                color=Colors.TEXT_PRIMARY,
                font_family=Fonts.HEADING,
            ),
            ft.Container(height=6),
            ft.Text(
                "Elegí un recorrido y mirá. La app se maneja sola: escribe en "
                "los campos, toca los botones y cambia de pantalla, igual que "
                "lo haría una persona.",
                size=TextSizes.BODY,
                color=Colors.TEXT_BODY,
            ),
            ft.Container(height=20),
            *tarjetas,
            ft.Container(height=10),
            ft.Text(
                "Son los mismos recorridos que ejecuta pytest en "
                "backend/tests/e2e/. Acá van despacio para que se vean.",
                size=TextSizes.SMALL,
                color=Colors.TEXT_MUTED,
            ),
        ],
    )

def vista_informe(barra: Barra, piloto: Piloto, titulo: str, error: str | None) -> ft.View:
    filas: list[ft.Control] = []

    for paso in piloto.pasos:
        if paso.estado == "ok":
            icono, color = ft.Icons.CHECK_CIRCLE, Colors.SUCCESS
        elif paso.estado == "fallo":
            icono, color = ft.Icons.CANCEL, Colors.BRAND_RED
        else:
            icono, color = ft.Icons.RADIO_BUTTON_UNCHECKED, Colors.TEXT_MUTED

        contenido: list[ft.Control] = [
            ft.Text(
                f"{paso.numero}. {paso.nombre}",
                size=TextSizes.BODY,
                color=Colors.TEXT_BODY,
            )
        ]

        if paso.detalle:
            contenido.append(
                ft.Text(
                    paso.detalle,
                    size=TextSizes.SMALL,
                    color=Colors.BRAND_RED,
                    selectable=True,
                )
            )

        filas.append(
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Icon(icono, size=20, color=color),
                    ft.Container(
                        expand=True,
                        content=ft.Column(spacing=2, tight=True, controls=contenido),
                    ),
                ],
            )
        )
        filas.append(ft.Container(height=10))

    completos = sum(1 for p in piloto.pasos if p.estado == "ok")
    todo_bien = error is None and completos == len(piloto.pasos)

    return ft.View(
        route="/visor/fin",
        padding=20,
        bgcolor=Colors.BACKGROUND,
        appbar=barra.construir(),
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(height=10),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if todo_bien else ft.Icons.ERROR,
                        size=30,
                        color=Colors.SUCCESS if todo_bien else Colors.BRAND_RED,
                    ),
                    ft.Text(
                        "Recorrido completo" if todo_bien else "El recorrido se cortó",
                        size=TextSizes.TITLE,
                        weight=ft.FontWeight.W_900,
                        color=Colors.TEXT_PRIMARY,
                        font_family=Fonts.HEADING,
                    ),
                ],
            ),
            ft.Container(height=4),
            ft.Text(
                f"{titulo} — {completos} de {len(piloto.pasos)} pasos",
                size=TextSizes.BODY,
                color=Colors.TEXT_MUTED,
            ),
            ft.Container(height=20),
            *filas,
            ft.Container(height=10),
            ft.Text(
                "Pantallas visitadas:",
                size=TextSizes.SMALL,
                weight=ft.FontWeight.BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Text(
                " → ".join(piloto.rutas) or "(ninguna)",
                size=TextSizes.SMALL,
                color=Colors.TEXT_MUTED,
                selectable=True,
            ),
        ],
    )

async def main(page: ft.Page) -> None:
    page.title = "Ashün — visor de pruebas E2E"
    page.theme = app_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = Colors.BACKGROUND
    page.padding = 0
    page.fonts = {
        "Poppins": (
            "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/"
            "Poppins-Regular.ttf"
        ),
    }
    page.window.width = 480
    page.window.height = 940

    from context.app_state import AppState

    state = AppState(page)
    await state.start()

    barra = Barra()

    enrutador = enrutador_de_app(page, state)

    piloto = Piloto(page, state, nombre="visor", pausa=PAUSA)

    actual: dict[str, Any] = {"clave": None, "titulo": "", "error": None}

    async def route_change(evento: Any) -> None:
        ruta = page.route

        if ruta == "/visor":
            page.views.clear()
            page.views.append(vista_menu(barra, elegir))
            page.update()
            return

        if ruta == "/visor/fin":
            page.views.clear()
            page.views.append(
                vista_informe(barra, piloto, actual["titulo"], actual["error"])
            )
            page.update()
            return

        await enrutador(evento)

        if page.views:
            page.views[-1].appbar = barra.construir()
            page.update()

    page.on_route_change = route_change

    def view_pop(evento: ft.ViewPopEvent) -> None:
        if len(page.views) > 1:
            page.views.pop()

    page.on_view_pop = view_pop

    def al_paso(paso: Paso) -> None:
        if paso.estado == "fallo":
            texto = f"Paso {paso.numero} FALLÓ: {paso.nombre}"
        elif paso.estado == "ok":
            texto = f"Paso {paso.numero} listo: {paso.nombre}"
        else:
            texto = f"Paso {paso.numero}: {paso.nombre}"

        barra.anunciar(actual["titulo"], texto, min(paso.numero / 11, 1.0))

        print(f"  [{paso.estado:9}] {paso.numero}. {paso.nombre}")
        if paso.detalle:
            print(f"               {paso.detalle}")

        try:
            page.update()
        except Exception:
            pass

    piloto.al_paso = al_paso

    def elegir(clave: str) -> None:
        page.run_task(ejecutar, clave)

    async def ejecutar(clave: str) -> None:
        receta = RECORRIDOS[clave]

        actual["clave"] = clave
        actual["titulo"] = receta["titulo"]
        actual["error"] = None

        piloto.pasos.clear()
        piloto.limpiar_avisos()

        barra.anunciar(receta["titulo"], "Arrancando...", 0)

        sufijo = str(int(time.time()))[-5:]

        try:
            await receta["funcion"](piloto, sufijo)
        except BaseException as error:
            actual["error"] = f"{type(error).__name__}: {error}"
            print(f"\n  El recorrido se corto: {actual['error']}\n")

        barra.anunciar(
            receta["titulo"],
            "Terminado" if actual["error"] is None else "Se cortó",
            1.0,
        )

        await page.push_route("/visor/fin")

    print()
    print("  Visor de pruebas E2E de Ashün")
    print("  Los pasos tambien se van imprimiendo aqui.")
    print()

    await page.push_route("/visor")

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
