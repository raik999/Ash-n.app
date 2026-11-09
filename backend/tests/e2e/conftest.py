import json
import socket
import subprocess
import sys
import tempfile
import time

from pathlib import Path

import httpx
import pytest

CARPETA_SRC = Path(__file__).resolve().parents[2] / "src"
CARPETA_FRONTEND = Path(__file__).resolve().parents[3] / "frontend"

MARCA_INICIO = "<<<RESULTADO>>>"
MARCA_FIN = "<<<FIN>>>"

def puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def python_del_frontend() -> str:
    candidatos = [
        CARPETA_FRONTEND / "venv" / "Scripts" / "python.exe",
        CARPETA_FRONTEND / "venv" / "bin" / "python",
        CARPETA_FRONTEND / ".venv" / "Scripts" / "python.exe",
        CARPETA_FRONTEND / ".venv" / "bin" / "python",
    ]

    for candidato in candidatos:
        if candidato.is_file():
            return str(candidato)

    return sys.executable

@pytest.fixture(scope="session")
def servidor(base_de_pruebas):
    puerto = puerto_libre()

    import os

    entorno = os.environ.copy()
    entorno["DATABASE"] = "ashun_test"
    entorno["DATABASE_URL"] = ""
    entorno["PORT"] = str(puerto)
    entorno["DEBUG"] = "false"

    registro = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="ashun_uvicorn_",
        suffix=".log",
        delete=False,
    )

    def leer_registro() -> str:
        try:
            with open(registro.name, encoding="utf-8", errors="replace") as archivo:
                return archivo.read()
        except OSError as error:
            return f"(no se pudo leer el registro del servidor: {error})"

    proceso = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "index:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(puerto),
            "--log-level",
            "warning",
        ],
        cwd=CARPETA_SRC,
        env=entorno,
        stdout=registro,
        stderr=subprocess.STDOUT,
    )

    base_url = f"http://127.0.0.1:{puerto}"

    inicio = time.monotonic()
    ultimo_error = None

    while time.monotonic() - inicio < 30:
        if proceso.poll() is not None:
            pytest.fail(
                f"El servidor no arranco.\n\nSalida de uvicorn:\n{leer_registro()}"
            )

        try:
            respuesta = httpx.get(f"{base_url}/health", timeout=1.0)
            if respuesta.status_code == 200:
                break
        except httpx.HTTPError as error:
            ultimo_error = error

        time.sleep(0.2)
    else:
        proceso.terminate()
        pytest.fail(
            f"El servidor no respondio en 30 segundos. Ultimo error: {ultimo_error}"
            f"\n\nSalida de uvicorn:\n{leer_registro()}"
        )

    yield base_url

    proceso.terminate()
    try:
        proceso.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait()

    registro.close()
    Path(registro.name).unlink(missing_ok=True)

@pytest.fixture
def api(servidor):
    with httpx.Client(base_url=servidor, timeout=10.0) as cliente:
        yield cliente

@pytest.fixture
def recorrido(servidor):
    def ejecutar(nombre: str, sufijo: str = "") -> dict:
        comando = [
            python_del_frontend(),
            "-m",
            "pruebas.correr",
            nombre,
            "--url",
            servidor,
        ]
        if sufijo:
            comando += ["--sufijo", sufijo]

        proceso = subprocess.run(
            comando,
            cwd=CARPETA_FRONTEND,
            capture_output=True,
            text=True,
            timeout=180,
        )

        salida = proceso.stdout or ""

        if MARCA_INICIO not in salida or MARCA_FIN not in salida:
            pytest.fail(
                "El recorrido del frontend no llego a terminar.\n\n"
                f"comando: {' '.join(comando)}\n"
                f"carpeta: {CARPETA_FRONTEND}\n\n"
                f"--- salida ---\n{salida}\n"
                f"--- errores ---\n{proceso.stderr}"
            )

        bruto = salida.split(MARCA_INICIO, 1)[1].split(MARCA_FIN, 1)[0].strip()
        resultado = json.loads(bruto)

        if not resultado["ok"]:
            pytest.fail(_informe(resultado))

        return resultado

    return ejecutar

def _informe(resultado: dict) -> str:
    simbolos = {"ok": "[ok]   ", "fallo": "[FALLO]", "pendiente": "[  -  ]"}

    lineas = [
        "",
        f"El recorrido '{resultado['titulo']}' se corto.",
        "",
    ]

    for paso in resultado["pasos"]:
        lineas.append(
            f"  {simbolos.get(paso['estado'], '')} {paso['numero']}. {paso['nombre']}"
        )
        if paso["detalle"]:
            for linea in paso["detalle"].splitlines():
                lineas.append(f"              {linea}")

    lineas += ["", f"  Error: {resultado['error']}", ""]

    if resultado.get("rutas"):
        lineas.append(f"  Pantallas visitadas: {' -> '.join(resultado['rutas'])}")

    if resultado.get("avisos"):
        lineas.append(f"  Avisos que mostro la app: {resultado['avisos']}")

    if resultado.get("traza"):
        lineas += ["", "  --- traza completa ---", resultado["traza"]]

    return "\n".join(lineas)

@pytest.fixture(autouse=True)
def base_limpia_e2e(servidor):
    from sqlalchemy import text

    from config.database import engine

    tablas = [
        "post_comments",
        "post_likes",
        "post_files",
        "post_tags",
        "search_history",
        "user_tags",
        "posts",
        "users",
    ]

    with engine.begin() as conexion:
        conexion.execute(text(f"TRUNCATE {', '.join(tablas)} RESTART IDENTITY CASCADE"))

    yield
