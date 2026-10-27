import pytest

EMAIL = "nuevo.artista@ubiobio.cl"
USERNAME = "nuevoartista"
PASSWORD = "Secreta123"

DESCRIPCION = "Mi primera obra en Ashun, pintada este verano"

def test_register_login_and_create_a_post(api):
    registro = api.post(
        "/api/auth/register",
        json={
            "email": EMAIL,
            "name": "Artista Nuevo",
            "username": USERNAME,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )

    assert registro.status_code == 201, registro.text

    assert "access_token" in registro.json()
    assert registro.json()["user"]["username"] == USERNAME

    assert "password" not in registro.json()["user"]
    assert "password_hash" not in registro.json()["user"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": EMAIL, "password": PASSWORD},
    )

    assert login.status_code == 200, login.text

    token = login.json()["access_token"]
    assert token

    api.headers["Authorization"] = f"Bearer {token}"

    yo = api.get("/api/auth/me")
    assert yo.status_code == 200, yo.text
    assert yo.json()["username"] == USERNAME

    borrador = api.post(
        "/api/posts",
        json={"title": "Mi primera obra", "description": DESCRIPCION},
    )

    assert borrador.status_code == 201, borrador.text
    post_id = borrador.json()["id"]

    publicada = api.post(f"/api/posts/{post_id}/publish")
    assert publicada.status_code == 200, publicada.text

    perfil = api.get(f"/api/users/{USERNAME}/posts")
    assert perfil.status_code == 200, perfil.text

    publicaciones = perfil.json()
    assert len(publicaciones) == 1
    assert publicaciones[0]["id"] == post_id
    assert publicaciones[0]["title"] == "Mi primera obra"

def test_the_login_also_works_with_the_username(api):
    api.post(
        "/api/auth/register",
        json={
            "email": EMAIL,
            "name": "Artista Nuevo",
            "username": USERNAME,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )

    login = api.post(
        "/api/auth/login",
        json={"identifier": USERNAME, "password": PASSWORD},
    )

    assert login.status_code == 200, login.text
    assert login.json()["user"]["email"] == EMAIL

def test_the_login_ignores_capital_letters_in_the_email(api):
    api.post(
        "/api/auth/register",
        json={
            "email": EMAIL,
            "name": "Artista Nuevo",
            "username": USERNAME,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )

    login = api.post(
        "/api/auth/login",
        json={"identifier": EMAIL.upper(), "password": PASSWORD},
    )

    assert login.status_code == 200, login.text

def test_you_cannot_create_a_post_without_logging_in(api):
    respuesta = api.post("/api/posts", json={"description": DESCRIPCION})
    assert respuesta.status_code == 401

def test_the_same_email_cannot_register_twice(api):
    datos = {
        "email": EMAIL,
        "name": "Artista Nuevo",
        "username": USERNAME,
        "password": PASSWORD,
        "confirm_password": PASSWORD,
    }

    assert api.post("/api/auth/register", json=datos).status_code == 201

    datos_repetidos = dict(datos, username="otronombre")
    respuesta = api.post("/api/auth/register", json=datos_repetidos)

    assert respuesta.status_code == 409
    assert "correo" in respuesta.json()["detail"]

@pytest.mark.parametrize(
    "identifier, password",
    [
        (EMAIL, "ContrasenaEquivocada"),
        ("no.existe@ubiobio.cl", PASSWORD),
    ],
)
def test_a_failed_login_returns_401(api, identifier, password):
    api.post(
        "/api/auth/register",
        json={
            "email": EMAIL,
            "name": "Artista Nuevo",
            "username": USERNAME,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )

    respuesta = api.post(
        "/api/auth/login", json={"identifier": identifier, "password": password}
    )

    assert respuesta.status_code == 401

def test_a_post_with_no_content_never_becomes_visible(api):
    registro = api.post(
        "/api/auth/register",
        json={
            "email": EMAIL,
            "name": "Artista Nuevo",
            "username": USERNAME,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
    )
    api.headers["Authorization"] = f"Bearer {registro.json()['access_token']}"

    borrador = api.post("/api/posts", json={})
    assert borrador.status_code == 201

    publicar = api.post(f"/api/posts/{borrador.json()['id']}/publish")
    assert publicar.status_code == 422

    mio = api.get(f"/api/users/{USERNAME}/posts")
    assert len(mio.json()) == 1

    del api.headers["Authorization"]
    de_visita = api.get(f"/api/users/{USERNAME}/posts")

    assert de_visita.status_code == 200, de_visita.text
    assert de_visita.json() == []
