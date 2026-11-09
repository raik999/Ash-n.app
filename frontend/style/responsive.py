from __future__ import annotations
from dataclasses import dataclass

import flet as ft

from style.theme import Space

ANCHO_ANGOSTO = 360
ANCHO_NORMAL = 400
ANCHO_TABLET = 600

MEGAPIXELES_GAMA_BAJA = 1.6

@dataclass(frozen=True)
class Pantalla:
    ancho: float
    alto: float
    ratio_pixeles: float

    seguro_arriba: float
    seguro_abajo: float

    teclado: float

    ligero: bool

    @property
    def angosta(self) -> bool:
        return self.ancho <= ANCHO_ANGOSTO

    @property
    def tablet(self) -> bool:
        return self.ancho >= ANCHO_TABLET

    @property
    def baja(self) -> bool:
        return self.alto <= 680

    @property
    def padding(self) -> int:
        if self.angosta:
            return Space.MD
        if self.ancho < ANCHO_NORMAL:
            return Space.LG
        return Space.XL

    @property
    def columnas(self) -> int:
        if self.tablet:
            return 4
        if self.angosta:
            return 2
        return 3

    def texto(self, tamano: int) -> int:
        if self.angosta:
            ajustado = round(tamano * 0.92)
        elif self.tablet:
            ajustado = round(tamano * 1.04)
        else:
            ajustado = tamano
        return max(11, ajustado)

    def avatar(self, tamano: int) -> int:
        if self.angosta:
            return max(32, round(tamano * 0.88))
        return tamano

    @property
    def megapixeles(self) -> float:
        return (self.ancho * self.ratio_pixeles * self.alto * self.ratio_pixeles) / 1_000_000

    @property
    def gama_baja(self) -> bool:
        return self.megapixeles <= MEGAPIXELES_GAMA_BAJA

    def pixeles_para(self, puntos: int) -> int:
        if self.ligero:
            return int(puntos)
        return int(puntos * min(self.ratio_pixeles, 2.0))

_ACTUAL = Pantalla(
    ancho=390,
    alto=844,
    ratio_pixeles=2.0,
    seguro_arriba=24,
    seguro_abajo=24,
    teclado=0,
    ligero=False,
)

_PREFERENCIA = "auto"

def pantalla() -> Pantalla:
    return _ACTUAL

def preferencia_ligero() -> str:
    return _PREFERENCIA

def elegir_ligero(valor: str) -> None:
    global _PREFERENCIA
    if valor in ("auto", "si", "no"):
        _PREFERENCIA = valor

def medir(page: ft.Page) -> Pantalla:
    global _ACTUAL

    ancho = _numero(getattr(page, "width", None), _ACTUAL.ancho)
    alto = _numero(getattr(page, "height", None), _ACTUAL.alto)

    media = getattr(page, "media", None)
    ratio = _numero(getattr(media, "device_pixel_ratio", None), _ACTUAL.ratio_pixeles)

    arriba = _borde(getattr(media, "padding", None), "top", _ACTUAL.seguro_arriba)
    abajo = _borde(getattr(media, "padding", None), "bottom", _ACTUAL.seguro_abajo)
    teclado = _borde(getattr(media, "view_insets", None), "bottom", 0)

    provisional = Pantalla(
        ancho=ancho,
        alto=alto,
        ratio_pixeles=max(1.0, ratio),
        seguro_arriba=arriba,
        seguro_abajo=abajo,
        teclado=teclado,
        ligero=False,
    )

    if _PREFERENCIA == "si":
        ligero = True
    elif _PREFERENCIA == "no":
        ligero = False
    else:
        ligero = provisional.gama_baja

    _ACTUAL = Pantalla(
        ancho=provisional.ancho,
        alto=provisional.alto,
        ratio_pixeles=provisional.ratio_pixeles,
        seguro_arriba=provisional.seguro_arriba,
        seguro_abajo=provisional.seguro_abajo,
        teclado=provisional.teclado,
        ligero=ligero,
    )
    return _ACTUAL

def duracion(ms: int) -> int:
    return 0 if _ACTUAL.ligero else ms

def _numero(valor, respaldo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return respaldo
    return numero if numero > 0 else respaldo

def _borde(padding, lado: str, respaldo: float) -> float:
    if padding is None:
        return respaldo
    try:
        return max(0.0, float(getattr(padding, lado)))
    except (TypeError, ValueError, AttributeError):
        return respaldo
