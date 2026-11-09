import pytest

MAX_COMENTARIO = 800

def comentar(cliente, post_id, texto):
    respuesta = cliente.post(f"/api/posts/{post_id}/comments", json={"text": texto})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()

def test_add_comment_returns_201(autenticado, publicada):
    respuesta = autenticado.post(
        f"/api/posts/{publicada['id']}/comments",
        json={"text": "Que buen uso del color"},
    )

    assert respuesta.status_code == 201, respuesta.text

    cuerpo = respuesta.json()
    assert cuerpo["text"] == "Que buen uso del color"
    assert cuerpo["id"] > 0

    assert cuerpo["author"]["username"] == "autor"

def test_anyone_logged_in_can_comment(otro_usuario, publicada):
    comentario = comentar(otro_usuario, publicada["id"], "Me encanta, Ana")

    assert comentario["author"]["username"] == "intrusa"

def test_add_comment_requires_authentication(client, publicada):
    client.headers.pop("Authorization", None)

    respuesta = client.post(
        f"/api/posts/{publicada['id']}/comments", json={"text": "Hola"}
    )

    assert respuesta.status_code == 401

def test_the_comment_text_is_trimmed(autenticado, publicada):
    comentario = comentar(autenticado, publicada["id"], "   Muy bueno   ")

    assert comentario["text"] == "Muy bueno"

@pytest.mark.parametrize("vacio", ["", "   ", "\n\t "])
def test_a_blank_comment_is_rejected(autenticado, publicada, vacio):
    respuesta = autenticado.post(
        f"/api/posts/{publicada['id']}/comments", json={"text": vacio}
    )

    assert respuesta.status_code == 422

def test_a_comment_of_exactly_800_characters_is_accepted(autenticado, publicada):
    largo = "a" * MAX_COMENTARIO

    comentario = comentar(autenticado, publicada["id"], largo)

    assert len(comentario["text"]) == MAX_COMENTARIO

def test_a_comment_longer_than_800_characters_is_rejected(autenticado, publicada):
    respuesta = autenticado.post(
        f"/api/posts/{publicada['id']}/comments",
        json={"text": "a" * (MAX_COMENTARIO + 1)},
    )

    assert respuesta.status_code == 422

def test_commenting_updates_the_counter(autenticado, publicada):
    assert autenticado.get(f"/api/posts/{publicada['id']}").json()["comments_count"] == 0

    comentar(autenticado, publicada["id"], "Primero")
    comentar(autenticado, publicada["id"], "Segundo")

    assert autenticado.get(f"/api/posts/{publicada['id']}").json()["comments_count"] == 2

def test_commenting_on_a_post_that_does_not_exist_returns_404(autenticado):
    respuesta = autenticado.post("/api/posts/999999/comments", json={"text": "Hola"})

    assert respuesta.status_code == 404

def test_you_cannot_comment_someone_elses_draft(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description="Todavia no la publico")

    respuesta = otro_usuario.post(
        f"/api/posts/{borrador['id']}/comments", json={"text": "Hola"}
    )

    assert respuesta.status_code == 404

def test_comments_come_back_oldest_first(autenticado, publicada):
    for texto in ["Primero", "Segundo", "Tercero"]:
        comentar(autenticado, publicada["id"], texto)

    respuesta = autenticado.get(f"/api/posts/{publicada['id']}/comments")

    assert respuesta.status_code == 200, respuesta.text
    assert [c["text"] for c in respuesta.json()] == ["Primero", "Segundo", "Tercero"]

def test_a_post_with_no_comments_returns_an_empty_list(autenticado, publicada):
    respuesta = autenticado.get(f"/api/posts/{publicada['id']}/comments")

    assert respuesta.status_code == 200
    assert respuesta.json() == []

def test_comments_can_be_read_without_logging_in(autenticado, client, publicada):
    comentar(autenticado, publicada["id"], "Un comentario publico")

    client.headers.pop("Authorization", None)
    respuesta = client.get(f"/api/posts/{publicada['id']}/comments")

    assert respuesta.status_code == 200, respuesta.text
    assert len(respuesta.json()) == 1

    assert respuesta.json()[0]["can_delete"] is False

def test_can_delete_is_true_for_the_comment_author(otro_usuario, publicada):
    comentar(otro_usuario, publicada["id"], "Mi comentario")

    comentarios = otro_usuario.get(f"/api/posts/{publicada['id']}/comments").json()

    assert comentarios[0]["can_delete"] is True

def test_can_delete_is_true_for_the_post_owner(autenticado, otro_usuario, publicada):
    comentar(otro_usuario, publicada["id"], "Comentario de intrusa")

    comentarios = autenticado.get(f"/api/posts/{publicada['id']}/comments").json()

    assert comentarios[0]["author"]["username"] == "intrusa"
    assert comentarios[0]["can_delete"] is True

def test_can_delete_is_false_for_everyone_else(autenticado, otro_usuario, publicada):
    comentar(autenticado, publicada["id"], "Comentario del autor")

    comentarios = otro_usuario.get(f"/api/posts/{publicada['id']}/comments").json()

    assert comentarios[0]["can_delete"] is False

def test_the_comment_author_can_delete_their_own(otro_usuario, publicada):
    comentario = comentar(otro_usuario, publicada["id"], "Me arrepenti")

    respuesta = otro_usuario.delete(
        f"/api/posts/{publicada['id']}/comments/{comentario['id']}"
    )

    assert respuesta.status_code == 200, respuesta.text
    assert otro_usuario.get(f"/api/posts/{publicada['id']}/comments").json() == []

def test_the_post_owner_can_delete_any_comment(autenticado, otro_usuario, publicada):
    comentario = comentar(otro_usuario, publicada["id"], "Comentario de intrusa")

    respuesta = autenticado.delete(
        f"/api/posts/{publicada['id']}/comments/{comentario['id']}"
    )

    assert respuesta.status_code == 200, respuesta.text
    assert autenticado.get(f"/api/posts/{publicada['id']}/comments").json() == []

def test_a_third_person_cannot_delete_a_comment(
    crear_borrador, autenticado, otro_usuario, client
):
    from fastapi.testclient import TestClient

    from index import app

    tercera = TestClient(app)
    alta = tercera.post(
        "/api/auth/register",
        json={
            "email": "tercera@ubiobio.cl",
            "name": "Tercera Persona",
            "username": "tercera",
            "password": "Secreta789",
            "confirm_password": "Secreta789",
        },
    )
    assert alta.status_code == 201, alta.text
    tercera.headers.update({"Authorization": f"Bearer {alta.json()['access_token']}"})

    borrador = crear_borrador(autenticado, description="Una obra del verano pasado")
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    comentario = comentar(autenticado, borrador["id"], "Comentario del autor")

    respuesta = tercera.delete(
        f"/api/posts/{borrador['id']}/comments/{comentario['id']}"
    )

    assert respuesta.status_code == 403

    assert len(autenticado.get(f"/api/posts/{borrador['id']}/comments").json()) == 1

def test_delete_comment_requires_authentication(autenticado, client, publicada):
    comentario = comentar(autenticado, publicada["id"], "Un comentario")

    client.headers.pop("Authorization", None)
    respuesta = client.delete(
        f"/api/posts/{publicada['id']}/comments/{comentario['id']}"
    )

    assert respuesta.status_code == 401

def test_deleting_a_comment_that_does_not_exist_returns_404(autenticado, publicada):
    respuesta = autenticado.delete(f"/api/posts/{publicada['id']}/comments/999999")

    assert respuesta.status_code == 404

def test_you_cannot_delete_a_comment_from_another_post(
    crear_borrador, autenticado, publicada
):
    otra = crear_borrador(autenticado, description="Otra obra completamente distinta")
    autenticado.post(f"/api/posts/{otra['id']}/publish")

    comentario = comentar(autenticado, otra["id"], "Comentario de la otra")

    respuesta = autenticado.delete(
        f"/api/posts/{publicada['id']}/comments/{comentario['id']}"
    )

    assert respuesta.status_code == 404

    assert len(autenticado.get(f"/api/posts/{otra['id']}/comments").json()) == 1

def test_deleting_a_comment_lowers_the_counter(autenticado, publicada):
    primero = comentar(autenticado, publicada["id"], "Primero")
    comentar(autenticado, publicada["id"], "Segundo")

    assert autenticado.get(f"/api/posts/{publicada['id']}").json()["comments_count"] == 2

    autenticado.delete(f"/api/posts/{publicada['id']}/comments/{primero['id']}")

    assert autenticado.get(f"/api/posts/{publicada['id']}").json()["comments_count"] == 1

def test_deleting_the_post_takes_its_comments_with_it(autenticado, publicada):
    comentar(autenticado, publicada["id"], "Un comentario")

    assert autenticado.delete(f"/api/posts/{publicada['id']}").status_code == 200

    nueva = autenticado.post(
        "/api/posts", json={"description": "Otra obra distinta del verano"}
    ).json()

    assert nueva["comments_count"] == 0
