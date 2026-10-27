import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from config.database import engine
from index import app

TABLAS_A_VACIAR = [
    "post_comments",
    "post_likes",
    "post_files",
    "post_tags",
    "search_history",
    "user_tags",
    "posts",
    "users",
]

@pytest.fixture(autouse=True)
def base_limpia(base_de_pruebas):
    with engine.begin() as conexion:
        conexion.execute(
            text(f"TRUNCATE {', '.join(TABLAS_A_VACIAR)} RESTART IDENTITY CASCADE")
        )

    yield

@pytest.fixture
def client():
    with TestClient(app) as cliente:
        yield cliente

@pytest.fixture
def autenticado(client):
    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "autor@ubiobio.cl",
            "name": "Autor de Prueba",
            "username": "autor",
            "password": "Secreta123",
            "confirm_password": "Secreta123",
        },
    )
    assert respuesta.status_code == 201, respuesta.text

    client.headers.update({"Authorization": f"Bearer {respuesta.json()['access_token']}"})

    client.usuario = respuesta.json()["user"]

    return client

@pytest.fixture
def otro_usuario(client):
    cliente = TestClient(app)

    respuesta = cliente.post(
        "/api/auth/register",
        json={
            "email": "intrusa@ubiobio.cl",
            "name": "Otra Persona",
            "username": "intrusa",
            "password": "Secreta456",
            "confirm_password": "Secreta456",
        },
    )
    assert respuesta.status_code == 201, respuesta.text

    cliente.headers.update({"Authorization": f"Bearer {respuesta.json()['access_token']}"})
    cliente.usuario = respuesta.json()["user"]

    return cliente
