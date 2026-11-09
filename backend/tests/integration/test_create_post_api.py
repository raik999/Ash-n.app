DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def test_create_post_returns_201_as_a_draft(autenticado):
    respuesta = autenticado.post(
        "/api/posts",
        json={"title": "Mi cuadro", "description": DESCRIPCION_VALIDA},
    )

    assert respuesta.status_code == 201, respuesta.text

    cuerpo = respuesta.json()
    assert cuerpo["title"] == "Mi cuadro"
    assert cuerpo["description"] == DESCRIPCION_VALIDA
    assert cuerpo["id"] > 0

    assert cuerpo["likes_count"] == 0
    assert cuerpo["comments_count"] == 0
    assert cuerpo["author"]["username"] == "autor"

    assert cuerpo["can_edit"] is True

def test_create_post_requires_authentication(client):
    respuesta = client.post("/api/posts", json={"title": "Intento"})
    assert respuesta.status_code == 401

def test_create_post_accepts_an_empty_body(autenticado):
    respuesta = autenticado.post("/api/posts", json={})

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["title"] is None
    assert respuesta.json()["description"] is None

def test_create_post_trims_the_title(crear_borrador, autenticado):
    cuerpo = crear_borrador(autenticado, title="   Mi cuadro   ")
    assert cuerpo["title"] == "Mi cuadro"

def test_create_post_turns_an_empty_title_into_null(crear_borrador, autenticado):
    cuerpo = crear_borrador(autenticado, title="     ")
    assert cuerpo["title"] is None

def test_create_post_rejects_more_than_10_tags(autenticado):
    respuesta = autenticado.post("/api/posts", json={"tag_ids": list(range(1, 12))})
    assert respuesta.status_code == 422
