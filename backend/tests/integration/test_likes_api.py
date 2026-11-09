def test_like_returns_the_new_count(autenticado, publicada):
    respuesta = autenticado.post(f"/api/posts/{publicada['id']}/like")

    assert respuesta.status_code == 200, respuesta.text

    cuerpo = respuesta.json()
    assert cuerpo["likes_count"] == 1
    assert cuerpo["liked_by_me"] is True

def test_the_like_survives_in_the_post(autenticado, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")

    publicacion = autenticado.get(f"/api/posts/{publicada['id']}").json()

    assert publicacion["likes_count"] == 1
    assert publicacion["liked_by_me"] is True

def test_liking_twice_does_not_count_twice(autenticado, publicada):
    primera = autenticado.post(f"/api/posts/{publicada['id']}/like")
    segunda = autenticado.post(f"/api/posts/{publicada['id']}/like")

    assert primera.status_code == 200
    assert segunda.status_code == 200

    assert primera.json()["likes_count"] == 1
    assert segunda.json()["likes_count"] == 1

def test_liking_many_times_still_counts_one(autenticado, publicada):
    for _ in range(10):
        autenticado.post(f"/api/posts/{publicada['id']}/like")

    publicacion = autenticado.get(f"/api/posts/{publicada['id']}").json()
    assert publicacion["likes_count"] == 1

def test_two_people_can_like_the_same_post(autenticado, otro_usuario, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")
    respuesta = otro_usuario.post(f"/api/posts/{publicada['id']}/like")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["likes_count"] == 2

def test_the_author_can_like_their_own_post(autenticado, publicada):
    respuesta = autenticado.post(f"/api/posts/{publicada['id']}/like")

    assert respuesta.status_code == 200
    assert respuesta.json()["likes_count"] == 1

def test_liked_by_me_is_true_only_for_who_liked(autenticado, otro_usuario, publicada):
    otro_usuario.post(f"/api/posts/{publicada['id']}/like")

    como_intrusa = otro_usuario.get(f"/api/posts/{publicada['id']}").json()
    como_autor = autenticado.get(f"/api/posts/{publicada['id']}").json()

    assert como_intrusa["likes_count"] == 1
    assert como_intrusa["liked_by_me"] is True

    assert como_autor["likes_count"] == 1
    assert como_autor["liked_by_me"] is False

def test_liked_by_me_is_false_without_logging_in(autenticado, client, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")

    client.headers.pop("Authorization", None)
    publicacion = client.get(f"/api/posts/{publicada['id']}").json()

    assert publicacion["likes_count"] == 1
    assert publicacion["liked_by_me"] is False

def test_unlike_removes_the_like(autenticado, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")

    respuesta = autenticado.delete(f"/api/posts/{publicada['id']}/like")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["likes_count"] == 0
    assert respuesta.json()["liked_by_me"] is False

def test_unliking_without_having_liked_is_not_an_error(autenticado, publicada):
    respuesta = autenticado.delete(f"/api/posts/{publicada['id']}/like")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["likes_count"] == 0

def test_unliking_only_removes_your_own_like(autenticado, otro_usuario, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")
    otro_usuario.post(f"/api/posts/{publicada['id']}/like")

    respuesta = autenticado.delete(f"/api/posts/{publicada['id']}/like")

    assert respuesta.json()["likes_count"] == 1
    assert otro_usuario.get(f"/api/posts/{publicada['id']}").json()["liked_by_me"] is True

def test_like_and_unlike_can_be_repeated(autenticado, publicada):
    for _ in range(3):
        assert autenticado.post(f"/api/posts/{publicada['id']}/like").json()["likes_count"] == 1
        assert autenticado.delete(f"/api/posts/{publicada['id']}/like").json()["likes_count"] == 0

def test_like_requires_authentication(client, publicada):
    client.headers.pop("Authorization", None)

    assert client.post(f"/api/posts/{publicada['id']}/like").status_code == 401
    assert client.delete(f"/api/posts/{publicada['id']}/like").status_code == 401

def test_liking_a_post_that_does_not_exist_returns_404(autenticado):
    respuesta = autenticado.post("/api/posts/999999/like")

    assert respuesta.status_code == 404

def test_you_cannot_like_someone_elses_draft(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description="Todavia no la publico, es mia")

    assert otro_usuario.post(f"/api/posts/{borrador['id']}/like").status_code == 404

def test_the_author_can_like_their_own_draft(crear_borrador, autenticado):
    borrador = crear_borrador(autenticado, description="Todavia no la publico, es mia")

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/like")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["likes_count"] == 1

def test_deleting_the_post_takes_its_likes_with_it(autenticado, otro_usuario, publicada):
    autenticado.post(f"/api/posts/{publicada['id']}/like")
    otro_usuario.post(f"/api/posts/{publicada['id']}/like")

    assert autenticado.delete(f"/api/posts/{publicada['id']}").status_code == 200

    nueva = autenticado.post(
        "/api/posts", json={"description": "Otra obra distinta del verano"}
    ).json()

    assert nueva["likes_count"] == 0
