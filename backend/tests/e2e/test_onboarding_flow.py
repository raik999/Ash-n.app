def test_el_onboarding_completo_funciona(recorrido):
    resultado = recorrido("onboarding")

    assert resultado["ok"] is True

    pasos = [paso["nombre"] for paso in resultado["pasos"]]
    assert pasos == [
        "Crear la cuenta",
        "Escribir la fecha de nacimiento",
        "Elegir las especialidades",
        "Omitir la foto de perfil",
        "Ver el perfil ya armado",
        "Escribir la presentacion",
        "Cerrar sesion",
        "Volver a entrar y comprobar que todo siguio ahi",
    ]

    assert all(paso["estado"] == "ok" for paso in resultado["pasos"])

def test_el_recorrido_pasa_por_todas_las_pantallas_del_alta(recorrido):
    resultado = recorrido("onboarding")

    rutas = resultado["rutas"]

    esperadas = [
        "/register",
        "/onboarding/birthdate",
        "/onboarding/tags",
        "/onboarding/avatar",
        "/profile",
    ]

    posiciones = [rutas.index(ruta) for ruta in esperadas]
    assert posiciones == sorted(posiciones), (
        f"Las pantallas del alta no se visitaron en orden.\n"
        f"Esperaba {esperadas}\nFui por {rutas}"
    )

def test_los_datos_del_onboarding_quedaron_guardados(recorrido, api):
    resultado = recorrido("onboarding")
    datos = resultado["datos"]

    usuario = datos["usuario"]

    login = api.post(
        "/api/auth/login",
        json={"identifier": usuario["username"], "password": usuario["password"]},
    )
    assert login.status_code == 200, login.text

    api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    yo = api.get("/api/auth/me")
    assert yo.status_code == 200, yo.text
    perfil = yo.json()

    assert perfil["birthdate"] == datos["nacimiento"]
    assert perfil["bio"] == datos["bio"]

    especialidades = sorted(tag["name"] for tag in perfil["tipo"])
    assert especialidades == sorted(datos["especialidades"])

    assert perfil["avatar_url"] is None

def test_el_onboarding_no_crea_publicaciones(recorrido, api):
    resultado = recorrido("onboarding")
    usuario = resultado["datos"]["usuario"]

    publicaciones = api.get(f"/api/users/{usuario['username']}/posts")

    assert publicaciones.status_code == 200, publicaciones.text
    assert publicaciones.json() == []
