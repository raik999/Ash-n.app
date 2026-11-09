from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import traceback

from typing import Any

MARCA_INICIO = "<<<RESULTADO>>>"
MARCA_FIN = "<<<FIN>>>"

async def correr(nombre: str, url: str | None, sufijo: str, pausa: float) -> dict[str, Any]:
    if url:
        os.environ["ASHUN_API_URL"] = url

    from pruebas.piloto import piloto_sin_pantalla
    from pruebas.recorridos import RECORRIDOS

    if nombre not in RECORRIDOS:
        disponibles = ", ".join(sorted(RECORRIDOS))
        raise SystemExit(f"No conozco el recorrido '{nombre}'. Hay: {disponibles}")

    receta = RECORRIDOS[nombre]

    piloto = await piloto_sin_pantalla(nombre, pausa=pausa)

    resultado: dict[str, Any] = {
        "recorrido": nombre,
        "titulo": receta["titulo"],
        "ok": False,
        "pasos": [],
        "datos": {},
        "error": None,
        "traza": None,
        "url": os.getenv("ASHUN_API_URL", "(la de config.py)"),
    }

    try:
        resultado["datos"] = await receta["funcion"](piloto, sufijo)
        resultado["ok"] = True
    except BaseException as error:
        resultado["error"] = f"{type(error).__name__}: {error}"
        resultado["traza"] = traceback.format_exc()
    finally:
        resultado["pasos"] = [
            {
                "numero": paso.numero,
                "nombre": paso.nombre,
                "estado": paso.estado,
                "detalle": paso.detalle,
            }
            for paso in piloto.pasos
        ]
        resultado["rutas"] = list(piloto.rutas)
        resultado["avisos"] = piloto.avisos()

    return resultado

def imprimir_para_leer(resultado: dict[str, Any]) -> None:
    print()
    print(f"  {resultado['titulo']}")
    print(f"  servidor: {resultado['url']}")
    print()

    simbolos = {"ok": "[ok]   ", "fallo": "[FALLO]", "pendiente": "[  -  ]"}

    for paso in resultado["pasos"]:
        print(f"  {simbolos.get(paso['estado'], '')} {paso['numero']}. {paso['nombre']}")
        if paso["detalle"]:
            for linea in paso["detalle"].splitlines():
                print(f"              {linea}")

    print()
    if resultado["ok"]:
        print(f"  Recorrido completo: {len(resultado['pasos'])} pasos.")
    else:
        print(f"  Se corto: {resultado['error']}")
        if resultado["traza"]:
            print()
            print(resultado["traza"])
    print()

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ejecuta un recorrido de extremo a extremo de Ashun, sin pantalla."
    )
    parser.add_argument("recorrido", help="onboarding | social")
    parser.add_argument(
        "--url",
        default=None,
        help="Direccion del backend. Si no se pasa, se usa la de config.py.",
    )
    parser.add_argument(
        "--sufijo",
        default="",
        help=(
            "Se le pega al nombre de usuario de los personajes. Sirve para "
            "ejecutarlo varias veces contra la misma base sin que choquen "
            "los correos repetidos."
        ),
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=0.0,
        help="Segundos entre acciones. 0 para que corra lo mas rapido posible.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime solo la linea del resultado, sin el informe legible.",
    )

    args = parser.parse_args()

    resultado = asyncio.run(
        correr(args.recorrido, args.url, args.sufijo, args.pausa)
    )

    if not args.json:
        imprimir_para_leer(resultado)

    print(MARCA_INICIO)
    print(json.dumps(resultado, ensure_ascii=False))
    print(MARCA_FIN)

    return 0 if resultado["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
