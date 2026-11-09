DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def test_delete_post_removes_it(crear_borrador, autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    respuesta = autenticado.delete(f"/api/posts/{borrador['id']}")
    assert respuesta.status_code == 200, respuesta.text

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 404

def test_delete_post_returns_403_for_another_user(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)
    autenticado.post(f"/api/posts/{borrador['id']}/publish")

    assert otro_usuario.delete(f"/api/posts/{borrador['id']}").status_code == 403

    assert autenticado.get(f"/api/posts/{borrador['id']}").status_code == 200

def test_delete_post_returns_404_the_second_time(crear_borrador, autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    assert autenticado.delete(f"/api/posts/{borrador['id']}").status_code == 200
    assert autenticado.delete(f"/api/posts/{borrador['id']}").status_code == 404

def test_delete_post_requires_authentication(crear_borrador, autenticado, client):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    client.headers.pop("Authorization", None)
    assert client.delete(f"/api/posts/{borrador['id']}").status_code == 401
