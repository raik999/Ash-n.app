from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from config.settings import settings
from services.storage_service import (
    THUMB_SUFIJO,
    crear_miniatura,
    ruta_de_miniatura,
)

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def es_candidata(ruta: Path) -> bool:
    if not ruta.is_file():
        return False
    if ruta.suffix.lower() not in EXTENSIONES:
        return False
    if ruta.stem.endswith(THUMB_SUFIJO):
        return False
    return True

def procesar(carpeta: Path, nombre_legible: str) -> tuple[int, int, int]:
    if not carpeta.is_dir():
        print(f"  {nombre_legible}: la carpeta no existe, se salta")
        return 0, 0, 0

    creadas = ya_estaban = fallaron = 0

    for ruta in sorted(carpeta.iterdir()):
        if not es_candidata(ruta):
            continue

        if ruta_de_miniatura(ruta).is_file():
            ya_estaban += 1
            continue

        if crear_miniatura(ruta) is None:
            fallaron += 1
            print(f"    no se pudo: {ruta.name}")
        else:
            creadas += 1

    print(
        f"  {nombre_legible}: {creadas} creadas, {ya_estaban} que ya estaban, "
        f"{fallaron} con problemas"
    )
    return creadas, ya_estaban, fallaron

def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print(
            "Falta Pillow. Instalalo con el venv activado:\n"
            "\n"
            "    pip install Pillow\n"
        )
        return 1

    print("Generando miniaturas...\n")

    a = procesar(settings.upload_dir, "avatares")
    b = procesar(settings.posts_dir, "publicaciones")

    total = a[0] + b[0]
    print(f"\nListo. {total} miniaturas nuevas.")

    if a[2] + b[2]:
        print(
            "Las que fallaron se siguen entregando en tamano completo, "
            "asi que no se rompe nada."
        )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
