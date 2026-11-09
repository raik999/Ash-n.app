DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def test_update_post_changes_the_title(crear_borrador, autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Titulo nuevo"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] == "Titulo nuevo"

def test_update_post_only_changes_what_was_sent(crear_borrador, autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Titulo nuevo"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] == "Titulo nuevo"
    assert respuesta.json()["description"] == DESCRIPCION_VALIDA

def test_update_post_can_clear_the_title_on_purpose(crear_borrador, autenticado):
    borrador = crear_borrador(
        autenticado, title="Titulo viejo", description=DESCRIPCION_VALIDA
    )

    respuesta = autenticado.patch(f"/api/posts/{borrador['id']}", json={"title": ""})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["title"] is None

def test_update_cannot_leave_a_published_post_empty(crear_borrador, autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    respuesta = autenticado.patch(
        f"/api/posts/{borrador['id']}", json={"description": "corta"}
    )

    assert respuesta.status_code == 422

def test_update_post_returns_403_for_another_user(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = otro_usuario.patch(
        f"/api/posts/{borrador['id']}", json={"title": "Secuestrada"}
    )

    assert respuesta.status_code == 403

    assert autenticado.get(f"/api/posts/{borrador['id']}").json()["title"] is None

def test_update_post_returns_404_if_not_found(autenticado):
    respuesta = autenticado.patch("/api/posts/999999", json={"title": "x"})
    assert respuesta.status_code == 404

def test_update_post_requires_authentication(crear_borrador, autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    client.headers.pop("Authorization", None)
    respuesta = client.patch(f"/api/posts/{borrador['id']}", json={"title": "x"})

    assert respuesta.status_code == 401
