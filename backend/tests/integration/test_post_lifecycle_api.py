DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

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
