import pytest

DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def crear_borrador(cliente, **campos):
    respuesta = cliente.post("/api/posts", json=campos)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()

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

def test_create_post_trims_the_title(autenticado):
    cuerpo = crear_borrador(autenticado, title="   Mi cuadro   ")
    assert cuerpo["title"] == "Mi cuadro"

def test_create_post_turns_an_empty_title_into_null(autenticado):
    cuerpo = crear_borrador(autenticado, title="     ")
    assert cuerpo["title"] is None

def test_create_post_rejects_more_than_10_tags(autenticado):
    respuesta = autenticado.post("/api/posts", json={"tag_ids": list(range(1, 12))})
    assert respuesta.status_code == 422

def test_publish_makes_the_post_visible(autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/publish")
    assert respuesta.status_code == 200, respuesta.text

def test_publish_rejects_a_post_with_no_content(autenticado):
    borrador = crear_borrador(autenticado)

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/publish")

    assert respuesta.status_code == 422
    assert "descripcion" in respuesta.json()["detail"]

@pytest.mark.parametrize(
    "descripcion, se_publica",
    [
        ("", False),
        ("corta", False),
        ("123456789", False),
        ("1234567890", True),
        (DESCRIPCION_VALIDA, True),
    ],
)
def test_the_minimum_description_is_exactly_10_characters(
    autenticado, descripcion, se_publica
):
    borrador = crear_borrador(autenticado, description=descripcion)

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/publish")

    if se_publica:
        assert respuesta.status_code == 200, respuesta.text
    else:
        assert respuesta.status_code == 422

def test_publish_returns_403_for_another_user(autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = otro_usuario.post(f"/api/posts/{borrador['id']}/publish")
    assert respuesta.status_code == 403

def test_get_post_returns_the_post(autenticado):
    borrador = crear_borrador(
        autenticado, title="Mi cuadro", description=DESCRIPCION_VALIDA
    )
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    respuesta = autenticado.get(f"/api/posts/{borrador['id']}")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["id"] == borrador["id"]
    assert cuerpo["title"] == "Mi cuadro"
    assert cuerpo["author"]["username"] == "autor"

def test_get_post_returns_404_if_not_found(client):
    respuesta = client.get("/api/posts/999999")
    assert respuesta.status_code == 404

def test_a_published_post_is_visible_without_logging_in(autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    client.headers.pop("Authorization", None)

    respuesta = client.get(f"/api/posts/{borrador['id']}")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["liked_by_me"] is False
    assert respuesta.json()["can_edit"] is False

def test_a_draft_is_invisible_to_everyone_but_its_author(autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 200

    assert otro_usuario.get(f"/api/posts/{borrador['id']}").status_code == 404

def test_can_edit_is_true_only_for_the_author(autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    mia = autenticado.get(f"/api/posts/{borrador['id']}").json()
    ajena = otro_usuario.get(f"/api/posts/{borrador['id']}").json()

    assert mia["can_edit"] is True
    assert ajena["can_edit"] is False

def test_update_post_changes_the_title(autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Titulo nuevo"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] == "Titulo nuevo"

def test_update_post_only_changes_what_was_sent(autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Titulo nuevo"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] == "Titulo nuevo"
    assert respuesta.json()["description"] == DESCRIPCION_VALIDA

def test_update_post_can_clear_the_title_on_purpose(autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(f"/api/posts/{borrador['id']}", json={"title": ""})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] is None

def test_update_cannot_leave_a_published_post_empty(autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"description": "corta"}
    )

    assert respuesta.status_code == 422

def test_update_post_returns_403_for_another_user(autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = otro_usuario.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Secuestrada"}
    )

    assert respuesta.status_code == 403

    assert autenticado.get(f"/api/posts/{borrador['id']}").json()["title"] is None

def test_update_post_returns_404_if_not_found(autenticado):
    respuesta = autenticado.patch("/api/posts/999999", json={"title": "x"})
    assert respuesta.status_code == 404

def test_update_post_requires_authentication(autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    client.headers.pop("Authorization", None)
    respuesta = client.patch(f"/api/posts/{borrador['id']}", json={"title": "x"})

    assert respuesta.status_code == 401

def test_delete_post_removes_it(autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    respuesta = autenticado.delete(f"/api/posts/{borrador['id']}")
    assert respuesta.status_code == 200, respuesta.text

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 404

def test_delete_post_returns_403_for_another_user(autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    assert otro_usuario.delete(f"/api/posts/{borrador['id']}").status_code == 403

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 200

def test_delete_post_returns_404_the_second_time(autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    assert autenticado.delete(f"/api/posts/{borrador['id']}").status_code == 200
    assert autenticado.delete(f"/api/posts/{borrador['id']}").status_code == 404

def test_delete_post_requires_authentication(autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    client.headers.pop("Authorization", None)
    assert client.delete(f"/api/posts/{borrador['id']}").status_code == 401

def test_the_full_lifecycle_of_a_post(autenticado):
    creado = autenticado.post(
        "/api/posts",
        json={"title": "Mi obra", "description": DESCRIPCION_VALIDA},
    )
    assert creado.status_code == 201, creado.text
    post_id = creado.json()["id"]

    publicado = autenticado.post(f"/api/posts/{post_id}/publish")
    assert publicado.status_code == 200, publicado.text

    obtenido = autenticado.get(f"/api/posts/{post_id}")
    assert obtenido.status_code == 200, obtenido.text
    assert obtenido.json()["title"] == "Mi obra"

    editado = autenticado.patch(
        f"/api/posts/{post_id}", json={"title": "Mi obra (corregida)"}
    )
    assert editado.status_code == 200, editado.text
    assert editado.json()["title"] == "Mi obra (corregida)"

    assert autenticado.get(f"/api/posts/{post_id}").json()["title"] == "Mi obra (corregida)"

    assert autenticado.delete(f"/api/posts/{post_id}").status_code == 200
    assert autenticado.get(f"/api/posts/{post_id}").status_code == 404
