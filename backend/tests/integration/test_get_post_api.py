DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def test_get_post_returns_the_post(crear_borrador, autenticado):
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

def test_a_published_post_is_visible_without_logging_in(crear_borrador, autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    client.headers.pop("Authorization", None)

    respuesta = client.get(f"/api/posts/{borrador['id']}")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["liked_by_me"] is False
    assert respuesta.json()["can_edit"] is False

def test_a_draft_is_invisible_to_everyone_but_its_author(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 200

    assert otro_usuario.get(f"/api/posts/{borrador['id']}").status_code == 404

def test_can_edit_is_true_only_for_the_author(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    mia = autenticado.get(f"/api/posts/{borrador['id']}").json()
    ajena = otro_usuario.get(f"/api/posts/{borrador['id']}").json()

    assert mia["can_edit"] is True
    assert ajena["can_edit"] is False
