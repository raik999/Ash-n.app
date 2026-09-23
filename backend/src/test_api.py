import sys
import uuid
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"

FAILURES = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global FAILURES
    if condition:
        print(f"  [OK]    {label}")
    else:
        FAILURES += 1
        print(f"  [FALLO] {label}")
        if detail:
            print(f"          -> {detail}")


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    email = f"test_{suffix}@ashun.cl"
    username = f"test_{suffix}"
    password = "ashun1234"

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        print("\n1. Comprobando que el servidor responda")
        try:
            response = client.get("/health")
        except httpx.ConnectError:
            print("  [FALLO] No hay nadie escuchando en " + BASE_URL)
            print("          -> Levanta el backend con: python index.py")
            return 1

        check("GET /health responde 200", response.status_code == 200, response.text)
        check(
            "La base de datos esta conectada",
            response.json().get("database") == "ok",
            response.text,
        )

        print("\n2. Listando las especialidades (#)")
        response = client.get("/api/tags")
        check("GET /api/tags responde 200", response.status_code == 200, response.text)
        tags = response.json()
        check("Hay especialidades cargadas", len(tags) > 0, f"recibidas: {len(tags)}")

        print("\n3. Registrando un usuario nuevo")
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "name": "Usuario De Prueba",
                "username": username,
                "password": password,
                "confirm_password": password,
            },
        )
        check("POST /api/auth/register responde 201", response.status_code == 201, response.text)
        if response.status_code != 201:
            return 1

        data = response.json()
        token = data["access_token"]
        check("Devuelve un token", bool(token))
        check("El rol por defecto es 'user'", data["user"]["role"] == "user", str(data["user"]))
        check("El campo 'tipo' viene vacio", data["user"]["tipo"] == [], str(data["user"]))

        auth_headers = {"Authorization": f"Bearer {token}"}

        print("\n4. Validaciones del registro")
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "name": "Otro",
                "username": f"otro_{suffix}",
                "password": password,
                "confirm_password": password,
            },
        )
        check("Rechaza un mail repetido con 409", response.status_code == 409, response.text)

        response = client.post(
            "/api/auth/register",
            json={
                "email": f"otro_{suffix}@ashun.cl",
                "name": "Otro",
                "username": f"otro_{suffix}",
                "password": password,
                "confirm_password": "distinta123",
            },
        )
        check(
            "Rechaza contrasenas que no coinciden con 422",
            response.status_code == 422,
            response.text,
        )

        print("\n5. Iniciando sesion")
        response = client.post(
            "/api/auth/login", json={"identifier": username, "password": password}
        )
        check("Login con nombre de usuario", response.status_code == 200, response.text)

        response = client.post(
            "/api/auth/login", json={"identifier": email, "password": password}
        )
        check("Login con correo", response.status_code == 200, response.text)

        response = client.post(
            "/api/auth/login", json={"identifier": username, "password": "malaclave"}
        )
        check("Rechaza la contrasena incorrecta con 401", response.status_code == 401)

        print("\n6. Endpoints protegidos")
        response = client.get("/api/auth/me")
        check("GET /api/auth/me sin token responde 401", response.status_code == 401)

        response = client.get("/api/auth/me", headers={"Authorization": "Bearer token.falso.aqui"})
        check("GET /api/auth/me con token invalido responde 401", response.status_code == 401)

        response = client.get("/api/auth/me", headers=auth_headers)
        check("GET /api/auth/me con token valido responde 200", response.status_code == 200)
        check("Devuelve el usuario correcto", response.json()["username"] == username)
        check("NUNCA devuelve la contrasena", "password_hash" not in response.json())

        print("\n7. Paso opcional: fecha de nacimiento")
        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"birthdate": "2000-05-14"}
        )
        check("Guarda la fecha de nacimiento", response.status_code == 200, response.text)
        check("La fecha quedo guardada", response.json()["birthdate"] == "2000-05-14")

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"birthdate": "2035-01-01"}
        )
        check("Rechaza una fecha futura", response.status_code == 422, response.text)

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"birthdate": "2020-01-01"}
        )
        check("Rechaza a un menor de 13 anios", response.status_code == 422, response.text)

        print("\n8. Paso opcional: especialidades (#)")
        chosen = [tags[0]["id"], tags[1]["id"]]
        response = client.patch("/api/users/me", headers=auth_headers, json={"tag_ids": chosen})
        check("Guarda las especialidades", response.status_code == 200, response.text)
        returned = [tag["id"] for tag in response.json()["tipo"]]
        check(
            "El campo 'tipo' trae los # elegidos",
            sorted(returned) == sorted(chosen),
            f"esperados {sorted(chosen)}, recibidos {returned}",
        )

        response = client.patch("/api/users/me", headers=auth_headers, json={"tag_ids": [99999]})
        check("Rechaza un # inexistente", response.status_code == 404, response.text)

        print("\n9. Editando el perfil (bio)")
        bio = "Artista independiente de Concepcion, Chile. 6 anios de trayectoria."
        response = client.patch("/api/users/me", headers=auth_headers, json={"bio": bio})
        check("Guarda el texto de presentacion", response.status_code == 200, response.text)
        check("La bio quedo guardada", response.json()["bio"] == bio)
        check(
            "Los # siguen ahi despues de editar la bio (PATCH parcial)",
            len(response.json()["tipo"]) == 2,
            str(response.json()["tipo"]),
        )

        print("\n10. Foto de perfil")
        tiny_png = bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010802000000"
            "907753de0000000c49444154789c63f8cfc0000003010100c9fe92ef00"
            "00000049454e44ae426082"
        )

        response = client.post(
            "/api/users/me/avatar",
            headers=auth_headers,
            files={"file": ("avatar.png", tiny_png, "image/png")},
        )
        check("Sube la foto de perfil", response.status_code == 200, response.text)
        avatar_url = response.json().get("avatar_url", "")
        check("Devuelve la URL de la foto", avatar_url.startswith("/uploads/"), avatar_url)

        response = client.get(avatar_url)
        check("La foto se puede descargar", response.status_code == 200)

        response = client.post(
            "/api/users/me/avatar",
            headers=auth_headers,
            files={"file": ("virus.png", b"esto no es una imagen", "image/png")},
        )
        check("Rechaza un archivo que no es imagen", response.status_code == 422, response.text)

        print("\n11. Perfil publico y permisos de admin")
        response = client.get(f"/api/users/{username}")
        check("Se puede ver un perfil publico sin token", response.status_code == 200)

        response = client.get("/api/users/no_existe_este_usuario_xyz")
        check("Un perfil inexistente responde 404", response.status_code == 404)

        response = client.post(
            "/api/tags", headers=auth_headers, json={"name": "Hacker", "color": "#000000"}
        )
        check("Un usuario normal NO puede crear # (403)", response.status_code == 403, response.text)

        print("\n12. Cambio de nombre de usuario")
        other_suffix = uuid.uuid4().hex[:8]
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"otro_{other_suffix}@ashun.cl",
                "name": "Otro Artista",
                "username": f"otro_{other_suffix}",
                "password": password,
                "confirm_password": password,
            },
        )
        taken_username = response.json()["user"]["username"]

        new_username = f"raik_{suffix}"
        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"username": new_username}
        )
        check("Cambia el nombre de usuario", response.status_code == 200, response.text)
        check("El nuevo nombre quedo guardado", response.json()["username"] == new_username)

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"username": new_username}
        )
        check("Guardar el MISMO nombre no choca consigo mismo", response.status_code == 200)

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"username": taken_username}
        )
        check("Rechaza un nombre ya ocupado con 409", response.status_code == 409, response.text)
        check(
            "Indica que el campo que fallo es 'username'",
            response.json().get("field") == "username",
            response.text,
        )

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"username": "con espacios!"}
        )
        check("Rechaza un nombre con caracteres invalidos", response.status_code == 422)

        response = client.patch("/api/users/me", headers=auth_headers, json={"username": "ab"})
        check("Rechaza un nombre demasiado corto", response.status_code == 422)

        response = client.patch(
            "/api/users/me", headers=auth_headers, json={"username": f"MAYUS_{suffix}"}
        )
        check(
            "Normaliza el nombre a minusculas",
            response.json()["username"] == f"mayus_{suffix}",
            response.text,
        )

        response = client.get("/api/auth/me", headers=auth_headers)
        check("La sesion sigue valida tras cambiar el nombre", response.status_code == 200)

    print("\n" + "=" * 60)
    if FAILURES == 0:
        print("TODAS LAS PRUEBAS PASARON")
    else:
        print(f"{FAILURES} PRUEBA(S) FALLARON")
    print("=" * 60)
    return 0 if FAILURES == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
