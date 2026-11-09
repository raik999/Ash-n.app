def test_el_recorrido_de_validaciones_completo_funciona(recorrido):
    resultado = recorrido("validaciones")

    assert resultado["ok"] is True

    pasos = [paso["nombre"] for paso in resultado["pasos"]]
    assert pasos == [
        "El formulario rechaza un correo mal escrito",
        "Rechaza una contrasena de menos de 6 caracteres",
        "Rechaza dos contrasenas que no coinciden",
        "Rechaza un nombre de usuario de menos de 3 caracteres",
        "Con todo correcto, la cuenta se crea",
        "Cerrar sesion",
        "El login rechaza una contrasena incorrecta",
        "El login rechaza un usuario que no existe",
        "Con las credenciales correctas, entra",
        "Crear la primera publicacion",
        "No se puede registrar el mismo correo dos veces",
    ]

    assert all(paso["estado"] == "ok" for paso in resultado["pasos"])

def test_los_rechazos_dejan_la_app_donde_estaba(recorrido):
    resultado = recorrido("validaciones")
    rutas = resultado["rutas"]

    assert rutas.count("/register") == 2, (
        f"Hubo 4 intentos de registro rechazados y no deberian haber navegado "
        f"a ningun lado.\nRutas: {rutas}"
    )

    assert rutas.index("/profile") < rutas.index("/post/new")

def test_solo_quedo_un_usuario_creado(recorrido, api):
    resultado = recorrido("validaciones")
    usuario = resultado["datos"]["usuario"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": usuario["username"], "password": usuario["password"]},
    )
    assert login.status_code == 200, login.text
    api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    def buscar(prefijo: str) -> list[str]:
        respuesta = api.get("/api/users", params={"q": prefijo, "limit": 50})
        assert respuesta.status_code == 200, respuesta.text
        return sorted(u["username"] for u in respuesta.json())

    assert buscar("rai") == [usuario["username"]]

    assert buscar("otro") == []

def test_el_usuario_quedo_bien_creado(recorrido, api):
    resultado = recorrido("validaciones")
    usuario = resultado["datos"]["usuario"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": usuario["email"], "password": usuario["password"]},
    )
    assert login.status_code == 200, login.text

    perfil = login.json()["user"]
    assert perfil["username"] == usuario["username"]
    assert perfil["name"] == usuario["name"]
    assert perfil["email"] == usuario["email"]

    assert "password" not in perfil
    assert "password_hash" not in perfil

def test_la_contrasena_equivocada_sigue_sin_servir(recorrido, api):
    resultado = recorrido("validaciones")
    usuario = resultado["datos"]["usuario"]

    mala = api.post(
        "/api/auth/login",
        json={"identifier": usuario["username"], "password": "ClaveEquivocada999"},
    )
    inexistente = api.post(
        "/api/auth/login",
        json={"identifier": "no.existe.nadie", "password": usuario["password"]},
    )

    assert mala.status_code == 401
    assert inexistente.status_code == 401
    assert mala.json()["detail"] == inexistente.json()["detail"]

def test_la_publicacion_quedo_publicada(recorrido, api):
    resultado = recorrido("validaciones")
    datos = resultado["datos"]
    usuario = datos["usuario"]

    publicaciones = api.get(f"/api/users/{usuario['username']}/posts")

    assert publicaciones.status_code == 200, publicaciones.text
    assert len(publicaciones.json()) == 1

    post_id = publicaciones.json()[0]["id"]
    publicacion = api.get(f"/api/posts/{post_id}").json()

    assert publicacion["title"] == datos["titulo"]
    assert publicacion["description"] == datos["descripcion"]

def test_este_recorrido_no_toca_el_perfil_ni_interactua(recorrido, api):
    resultado = recorrido("validaciones")
    usuario = resultado["datos"]["usuario"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": usuario["username"], "password": usuario["password"]},
    )
    api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    perfil = api.get("/api/auth/me").json()
    assert perfil["birthdate"] is None
    assert perfil["bio"] is None
    assert perfil["tipo"] == []

    publicaciones = api.get(f"/api/users/{usuario['username']}/posts").json()
    assert publicaciones[0]["likes_count"] == 0
    assert publicaciones[0]["comments_count"] == 0