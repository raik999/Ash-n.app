def test_el_recorrido_social_completo_funciona(recorrido):
    resultado = recorrido("social")

    assert resultado["ok"] is True

    pasos = [paso["nombre"] for paso in resultado["pasos"]]
    assert pasos == [
        "Ana crea su cuenta",
        "Ana publica su obra",
        "Ana cierra sesion y entra Beto",
        "Beto busca a Ana",
        "Beto entra al perfil de Ana",
        "Beto abre la publicacion",
        "Beto da me gusta",
        "Beto comenta",
        "Beto cierra sesion y vuelve Ana",
        "Ana ve el me gusta y el comentario",
        "Ana borra el comentario de Beto",
    ]

    assert all(paso["estado"] == "ok" for paso in resultado["pasos"])

def test_el_recorrido_pasa_por_el_buscador_y_el_perfil_ajeno(recorrido):
    resultado = recorrido("social")
    rutas = resultado["rutas"]
    ana = resultado["datos"]["ana"]["username"]

    assert "/search" in rutas
    assert f"/user/{ana}" in rutas

    orden = [
        rutas.index("/search"),
        rutas.index(f"/user/{ana}"),
        rutas.index(f"/post/{resultado['datos']['post_id']}"),
    ]
    assert orden == sorted(orden), (
        f"Beto no llego a la publicacion por el buscador.\nFui por {rutas}"
    )

def test_el_me_gusta_quedo_a_nombre_de_beto(recorrido, api):
    resultado = recorrido("social")
    datos = resultado["datos"]
    post_id = datos["post_id"]

    def token_de(persona: dict) -> str:
        respuesta = api.post(
            "/api/auth/login",
            json={"identifier": persona["username"], "password": persona["password"]},
        )
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()["access_token"]

    api.headers["Authorization"] = f"Bearer {token_de(datos['beto'])}"
    como_beto = api.get(f"/api/posts/{post_id}").json()

    assert como_beto["likes_count"] == 1
    assert como_beto["liked_by_me"] is True
    assert como_beto["can_edit"] is False

    api.headers["Authorization"] = f"Bearer {token_de(datos['ana'])}"
    como_ana = api.get(f"/api/posts/{post_id}").json()

    assert como_ana["likes_count"] == 1
    assert como_ana["liked_by_me"] is False
    assert como_ana["can_edit"] is True

def test_la_publicacion_quedo_con_el_titulo_y_la_descripcion(recorrido, api):
    resultado = recorrido("social")
    datos = resultado["datos"]

    publicacion = api.get(f"/api/posts/{datos['post_id']}").json()

    assert publicacion["title"] == datos["titulo"]
    assert publicacion["description"] == datos["descripcion"]
    assert publicacion["author"]["username"] == datos["ana"]["username"]

    assert publicacion["files"] == []

def test_el_comentario_de_beto_se_borro_de_verdad(recorrido, api):
    resultado = recorrido("social")
    datos = resultado["datos"]
    post_id = datos["post_id"]

    comentarios = api.get(f"/api/posts/{post_id}/comments")
    assert comentarios.status_code == 200, comentarios.text
    assert comentarios.json() == []

    publicacion = api.get(f"/api/posts/{post_id}").json()
    assert publicacion["comments_count"] == 0

    assert publicacion["likes_count"] == 1

def test_el_recorrido_social_no_toca_el_perfil(recorrido, api):
    resultado = recorrido("social")
    datos = resultado["datos"]

    for persona in (datos["ana"], datos["beto"]):
        login = api.post(
            "/api/auth/login",
            json={"identifier": persona["username"], "password": persona["password"]},
        )
        api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

        perfil = api.get("/api/auth/me").json()

        assert perfil["birthdate"] is None
        assert perfil["bio"] is None
        assert perfil["tipo"] == []
        assert perfil["avatar_url"] is None

def test_la_publicacion_rechazada_no_quedo_guardada(recorrido, api):
    resultado = recorrido("social")
    ana = resultado["datos"]["ana"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": ana["username"], "password": ana["password"]},
    )
    api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    publicaciones = api.get(f"/api/users/{ana['username']}/posts").json()

    assert len(publicaciones) == 1, (
        f"Deberia haber una sola publicacion y hay {len(publicaciones)}: "
        f"{[p.get('description') for p in publicaciones]}"
    )
    assert publicaciones[0]["description"] == resultado["datos"]["descripcion"]

def test_el_comentario_vacio_no_se_guardo(recorrido, api):
    resultado = recorrido("social")
    post_id = resultado["datos"]["post_id"]

    comentarios = api.get(f"/api/posts/{post_id}/comments")

    assert comentarios.status_code == 200, comentarios.text
    assert comentarios.json() == []
