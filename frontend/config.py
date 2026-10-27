from __future__ import annotations

import os

API_URL = "http://localhost:8000"

API_URL_PRODUCCION = ""

def api_base_url() -> str:
    desde_entorno = os.getenv("ASHUN_API_URL")
    if desde_entorno:
        return desde_entorno.rstrip("/")

    if API_URL_PRODUCCION:
        return API_URL_PRODUCCION.rstrip("/")

    return API_URL.rstrip("/")
