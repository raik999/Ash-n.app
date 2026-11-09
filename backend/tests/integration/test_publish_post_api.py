import pytest

DESCRIPCION_VALIDA = "Un cuadro al oleo que pinte este verano"

def test_publish_makes_the_post_visible(crear_borrador, autenticado):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/publish")
    assert respuesta.status_code == 200, respuesta.text

def test_publish_rejects_a_post_with_no_content(crear_borrador, autenticado):
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
    crear_borrador, autenticado, descripcion, se_publica
):
    borrador = crear_borrador(autenticado, description=descripcion)

    respuesta = autenticado.post(f"/api/posts/{borrador['id']}/publish")

    if se_publica:
        assert respuesta.status_code == 200, respuesta.text
    else:
        assert respuesta.status_code == 422

def test_publish_returns_403_for_another_user(crear_borrador, autenticado, otro_usuario):
    borrador = crear_borrador(autenticado, description=DESCRIPCION_VALIDA)

    respuesta = otro_usuario.post(f"/api/posts/{borrador['id']}/publish")
    assert respuesta.status_code == 403
