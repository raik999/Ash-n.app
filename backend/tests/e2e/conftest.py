import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

CARPETA_SRC = Path(__file__).resolve().parents[2] / "src"

def puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def servidor(base_de_pruebas):
    puerto = puerto_libre()

    import os

    entorno = os.environ.copy()
    entorno["DATABASE"] = "ashun_test"
    entorno["DATABASE_URL"] = ""
    entorno["PORT"] = str(puerto)
    entorno["DEBUG"] = "false"

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
        ],
        cwd=CARPETA_SRC,
        env=entorno,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    base_url = f"http://127.0.0.1:{puerto}"

    inicio = time.monotonic()
    ultimo_error = None

    while time.monotonic() - inicio < 30:
        if proceso.poll() is not None:
            salida = proceso.stdout.read() if proceso.stdout else ""
            pytest.fail(f"El servidor no arranco.\n\nSalida de uvicorn:\n{salida}")

        try:
            respuesta = httpx.get(f"{base_url}/health", timeout=1.0)
            if respuesta.status_code == 200:
                break
        except httpx.HTTPError as error:
            ultimo_error = error

        time.sleep(0.2)
    else:
        proceso.terminate()
        pytest.fail(f"El servidor no respondio en 30 segundos. Ultimo error: {ultimo_error}")

    yield base_url

    proceso.terminate()
    try:
        proceso.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait()

@pytest.fixture
def api(servidor):
    with httpx.Client(base_url=servidor, timeout=10.0) as cliente:
        yield cliente

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
