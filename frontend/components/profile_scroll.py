from __future__ import annotations
from typing import Callable

import flet as ft

from components.layout import safe_update
from style.responsive import pantalla
from style.theme import Colors, Fonts, Radius, Space, TextSizes

def grilla_fija(
    celdas: list[ft.Control],
    *,
    columnas: int | None = None,
    ancho_disponible: float | None = None,
    espacio: int = Space.XXS + 2,
) -> ft.Column:
    medidas = pantalla()
    columnas = columnas or medidas.columnas
    ancho = ancho_disponible if ancho_disponible is not None else medidas.ancho

    lado = max(60.0, (ancho - espacio * (columnas - 1)) / columnas)

    filas: list[ft.Control] = []
    for inicio in range(0, len(celdas), columnas):
        grupo = celdas[inicio : inicio + columnas]

        controles = [
            ft.Container(width=lado, height=lado, content=celda) for celda in grupo
        ]
        while len(controles) < columnas:
            controles.append(ft.Container(width=lado, height=lado))

        filas.append(ft.Row(spacing=espacio, controls=controles))

    return ft.Column(spacing=espacio, controls=filas)

def perfil_desplazable(
    *,
    encabezado: ft.Control,
    etiquetas: list[str],
    contenidos: list[Callable[[], ft.Control]],
    relleno_horizontal: int = Space.XS,
) -> ft.Stack:
    medidas = pantalla()
    estado = {"pestana": 0, "alto_encabezado": 0.0, "pegada": False}

    contenedor = ft.Container(
        padding=ft.Padding.symmetric(horizontal=relleno_horizontal),
        content=contenidos[0](),
    )

    def fila_pestanas(al_elegir: Callable, con_sombra: bool) -> ft.Container:
        botones: list[ft.Control] = []

        for indice, etiqueta in enumerate(etiquetas):
            elegida = indice == estado["pestana"]
            botones.append(
                ft.Container(
                    expand=True,
                    on_click=al_elegir(indice),
                    ink=True,
                    border_radius=Radius.SM,
                    padding=ft.Padding.symmetric(vertical=Space.SM),
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border(
                        bottom=ft.BorderSide(
                            3,
                            Colors.BRAND_DARK if elegida else ft.Colors.TRANSPARENT,
                        )
                    ),
                    content=ft.Text(
                        etiqueta,
                        size=medidas.texto(TextSizes.BODY),
                        color=Colors.TEXT_PRIMARY if elegida else Colors.TEXT_MUTED,
                        font_family=Fonts.HEADING if elegida else Fonts.BODY,
                    ),
                )
            )

        return ft.Container(
            bgcolor=Colors.BACKGROUND,
            padding=ft.Padding.symmetric(horizontal=relleno_horizontal),
            border=(
                ft.Border(bottom=ft.BorderSide(1, Colors.DIVIDER))
                if con_sombra
                else None
            ),
            content=ft.Row(spacing=0, controls=botones),
        )

    normal = ft.Container()
    fija = ft.Container(visible=False)

    def elegir(indice: int) -> Callable:
        async def manejar(e) -> None:
            if indice == estado["pestana"]:
                return
            estado["pestana"] = indice
            contenedor.content = contenidos[indice]()
            redibujar_pestanas()
            safe_update(contenedor)

        return manejar

    def redibujar_pestanas() -> None:
        normal.content = fila_pestanas(elegir, con_sombra=False).content
        fija.content = fila_pestanas(elegir, con_sombra=True).content
        safe_update(normal, fija)

    base = fila_pestanas(elegir, con_sombra=False)
    normal.content = base.content
    normal.bgcolor = base.bgcolor
    normal.padding = base.padding

    copia = fila_pestanas(elegir, con_sombra=True)
    fija.content = copia.content
    fija.bgcolor = copia.bgcolor
    fija.padding = copia.padding
    fija.border = copia.border

    def medir_encabezado(e) -> None:
        try:
            estado["alto_encabezado"] = float(e.height)
        except (TypeError, ValueError):
            pass

    envoltorio = ft.Container(content=encabezado, on_size_change=medir_encabezado)

    def al_desplazar(e) -> None:
        alto = estado["alto_encabezado"]
        if alto <= 0:
            return

        debe_pegarse = float(e.pixels or 0) >= alto - 4

        if debe_pegarse != estado["pegada"]:
            estado["pegada"] = debe_pegarse
            fija.visible = debe_pegarse
            safe_update(fija)

    columna = ft.Column(
        spacing=0,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        on_scroll=al_desplazar,
        scroll_interval=100,
        controls=[
            envoltorio,
            normal,
            contenedor,
            ft.Container(height=Space.XL),
        ],
    )

    return ft.Stack(
        expand=True,
        controls=[
            columna,
            ft.Container(content=fija, left=0, right=0, top=0),
        ],
    )
