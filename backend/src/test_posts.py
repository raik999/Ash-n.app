import struct
import sys
import uuid
import zlib
import httpx

BASE_URL = "http://localhost:8000"
FAILURES = 0

def check(label, condition, detail=""):
    global FAILURES
    if condition:
        print(f"  [OK]    {label}")
    else:
        FAILURES += 1
        print(f"  [FALLO] {label}")
        if detail:
            print(f"          -> {str(detail)[:400]}")

def png_bytes():
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + chunk(b"IEND", b""))

MP4 = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 200
MP3 = b"ID3\x03\x00\x00\x00" + b"\x00" * 200

def registrar(client, prefijo):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/auth/register", json={
        "email": f"{prefijo}_{suf}@ashun.cl", "name": f"{prefijo.title()} Artista",
        "username": f"{prefijo}_{suf}", "password": "ashun1234",
        "confirm_password": "ashun1234"})
    d = r.json()
    return {"Authorization": f"Bearer {d['access_token']}"}, d["user"]["username"]

def main():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        ana, ana_user = registrar(c, "ana")
        beto, beto_user = registrar(c, "beto")
        tags = c.get("/api/tags").json()

        print("\n1. Crear el borrador")
        r = c.post("/api/posts", headers=ana, json={
            "title": "Mi acuarela", "description": "Pintada en Concepcion",
            "tag_ids": [tags[0]["id"], tags[1]["id"]]})
        check("POST /api/posts responde 201", r.status_code == 201, r.text)
        post = r.json()
        pid = post["id"]
        check("guarda titulo y descripcion", post["title"] == "Mi acuarela")
        check("guarda los 2 #", len(post["tags"]) == 2, str(post["tags"]))
        check("el autor viene con @ y nombre", post["author"]["username"] == ana_user)
        check("nace sin likes ni comentarios",
              post["likes_count"] == 0 and post["comments_count"] == 0)
        check("el autor ve can_edit=True", post["can_edit"] is True)

        print("\n2. Un borrador NO aparece en el perfil")
        check("no sale en el grid del autor", c.get(f"/api/users/{ana_user}/posts").json() == [])
        r = c.get(f"/api/posts/{pid}")
        check("y sin sesion responde 404", r.status_code == 404, r.text)
        r = c.get(f"/api/posts/{pid}", headers=ana)
        check("pero su autor si lo ve", r.status_code == 200)
        r = c.get(f"/api/posts/{pid}", headers=beto)
        check("otro usuario NO lo ve", r.status_code == 404)

        print("\n3. Subir archivos de los tres tipos")
        r = c.post(f"/api/posts/{pid}/files", headers=ana,
                   files={"file": ("foto.png", png_bytes(), "image/png")})
        check("sube una imagen", r.status_code == 201, r.text)
        check("la detecta como 'image'", r.json()["kind"] == "image", r.text)
        check("la guarda en uploads/posts/", r.json()["url"].startswith("/uploads/posts/"), r.json()["url"])
        url_imagen = r.json()["url"]
        id_imagen = r.json()["id"]

        r = c.post(f"/api/posts/{pid}/files", headers=ana,
                   files={"file": ("video.mp4", MP4, "video/mp4")})
        check("sube un video y lo detecta", r.json().get("kind") == "video", r.text)
        r = c.post(f"/api/posts/{pid}/files", headers=ana,
                   files={"file": ("cancion.mp3", MP3, "audio/mpeg")})
        check("sube una cancion y la detecta", r.json().get("kind") == "audio", r.text)
        check("las posiciones van 0,1,2", r.json()["position"] == 2, r.text)

        check("el archivo se descarga de verdad", c.get(url_imagen).status_code == 200)

        print("\n4. El backend no se fia de la extension")
        r = c.post(f"/api/posts/{pid}/files", headers=ana,
                   files={"file": ("virus.png", b"MZ\x90esto es un ejecutable", "image/png")})
        check("rechaza un archivo disfrazado de PNG", r.status_code == 422, r.text)

        print("\n5. Solo el autor toca sus archivos")
        r = c.post(f"/api/posts/{pid}/files", headers=beto,
                   files={"file": ("x.png", png_bytes(), "image/png")})
        check("otro usuario no puede subir (403)", r.status_code == 403, r.text)
        r = c.delete(f"/api/posts/{pid}/files/{id_imagen}", headers=beto)
        check("otro usuario no puede borrar (403)", r.status_code == 403, r.text)

        print("\n6. Publicar")
        r = c.post(f"/api/posts/{pid}/publish", headers=ana)
        check("POST /publish responde 200", r.status_code == 200, r.text)
        r = c.get(f"/api/users/{ana_user}/posts")
        check("ahora SI aparece en el grid", len(r.json()) == 1, r.text)
        casilla = r.json()[0]
        check("el grid trae la vista previa del primer archivo",
              casilla["preview"]["kind"] == "image", str(casilla))
        check("y cuenta los 3 archivos", casilla["files_count"] == 3, str(casilla))
        check("se ve sin iniciar sesion", c.get(f"/api/posts/{pid}").status_code == 200)

        print("\n7. La regla del contenido minimo")
        r = c.post("/api/posts", headers=ana, json={"description": "corta"})
        vacio = r.json()["id"]
        r = c.post(f"/api/posts/{vacio}/publish", headers=ana)
        check("sin archivos y con menos de 10 letras, rechaza", r.status_code == 422, r.text)
        check("y dice que el campo es 'description'",
              r.json().get("field") == "description", r.text)
        r = c.patch(f"/api/posts/{vacio}", headers=ana,
                    json={"description": "ya tiene diez letras de sobra"})
        check("con descripcion larga ya se puede publicar",
              c.post(f"/api/posts/{vacio}/publish", headers=ana).status_code == 200)

        r = c.post("/api/posts", headers=ana, json={})
        solo_foto = r.json()["id"]
        c.post(f"/api/posts/{solo_foto}/files", headers=ana,
               files={"file": ("f.png", png_bytes(), "image/png")})
        check("con un archivo y SIN descripcion tambien se publica",
              c.post(f"/api/posts/{solo_foto}/publish", headers=ana).status_code == 200)

        print("\n8. Likes")
        r = c.post(f"/api/posts/{pid}/like")
        check("dar like sin sesion responde 401", r.status_code == 401)
        r = c.post(f"/api/posts/{pid}/like", headers=beto)
        check("Beto da like", r.status_code == 200 and r.json()["likes_count"] == 1, r.text)
        check("y le vuelve liked_by_me=True", r.json()["liked_by_me"] is True)
        r = c.post(f"/api/posts/{pid}/like", headers=beto)
        check("DAR LIKE DOS VECES NO SUMA DOS", r.json()["likes_count"] == 1, r.text)
        r = c.post(f"/api/posts/{pid}/like", headers=ana)
        check("otro usuario suma su propio like", r.json()["likes_count"] == 2, r.text)
        r = c.get(f"/api/posts/{pid}", headers=beto)
        check("Beto ve su corazon rojo", r.json()["liked_by_me"] is True)
        r = c.get(f"/api/posts/{pid}")
        check("quien no inicio sesion lo ve gris", r.json()["liked_by_me"] is False)
        r = c.delete(f"/api/posts/{pid}/like", headers=beto)
        check("quitar el like lo descuenta", r.json()["likes_count"] == 1, r.text)
        check("y deja liked_by_me=False", r.json()["liked_by_me"] is False)
        r = c.delete(f"/api/posts/{pid}/like", headers=beto)
        check("quitarlo dos veces no da numeros negativos", r.json()["likes_count"] == 1, r.text)

        print("\n9. Comentarios")
        r = c.post(f"/api/posts/{pid}/comments", json={"text": "hola"})
        check("comentar sin sesion responde 401", r.status_code == 401)
        r = c.post(f"/api/posts/{pid}/comments", headers=beto,
                   json={"text": "muy buena publicacion <3"})
        check("Beto comenta", r.status_code == 201, r.text)
        com_beto = r.json()["id"]
        r = c.post(f"/api/posts/{pid}/comments", headers=ana, json={"text": "gracias!"})
        com_ana = r.json()["id"]
        r = c.get(f"/api/posts/{pid}/comments")
        check("se leen los 2 sin sesion", len(r.json()) == 2, r.text)
        check("del mas antiguo al mas nuevo",
              [x["id"] for x in r.json()] == [com_beto, com_ana], r.text)
        check("cada comentario trae a su autor",
              r.json()[0]["author"]["username"] == beto_user, r.text)
        check("sin sesion, can_delete es False en todos",
              all(x["can_delete"] is False for x in r.json()), r.text)

        r = c.post(f"/api/posts/{pid}/comments", headers=beto, json={"text": "x" * 801})
        check("rechaza mas de 800 caracteres", r.status_code == 422, r.text)
        r = c.post(f"/api/posts/{pid}/comments", headers=beto, json={"text": "   "})
        check("rechaza un comentario en blanco", r.status_code == 422, r.text)
        r = c.post(f"/api/posts/{pid}/comments", headers=beto, json={"text": "x" * 800})
        check("acepta exactamente 800", r.status_code == 201, r.text)
        com_largo = r.json()["id"]

        print("\n10. Quien puede borrar un comentario")
        r = c.get(f"/api/posts/{pid}/comments", headers=beto)
        propios = {x["id"]: x["can_delete"] for x in r.json()}
        check("Beto puede borrar los suyos", propios[com_beto] is True, str(propios))
        check("pero NO el de Ana", propios[com_ana] is False, str(propios))
        r = c.get(f"/api/posts/{pid}/comments", headers=ana)
        de_ana = {x["id"]: x["can_delete"] for x in r.json()}
        check("Ana, dueña de la publicacion, puede borrar CUALQUIERA",
              all(de_ana.values()), str(de_ana))

        r = c.delete(f"/api/posts/{pid}/comments/{com_ana}", headers=beto)
        check("Beto no puede borrar el comentario de Ana (403)", r.status_code == 403, r.text)
        r = c.delete(f"/api/posts/{pid}/comments/{com_beto}", headers=beto)
        check("Beto si borra el suyo", r.status_code == 200, r.text)
        r = c.delete(f"/api/posts/{pid}/comments/{com_largo}", headers=ana)
        check("Ana borra el comentario ajeno de su publicacion", r.status_code == 200, r.text)
        check("quedan los comentarios correctos",
              [x["id"] for x in c.get(f"/api/posts/{pid}/comments").json()] == [com_ana])

        print("\n11. Editar la publicacion")
        r = c.patch(f"/api/posts/{pid}", headers=beto, json={"title": "secuestrada"})
        check("otro usuario no puede editar (403)", r.status_code == 403, r.text)
        r = c.patch(f"/api/posts/{pid}", headers=ana, json={"title": "Acuarela nueva"})
        check("el autor edita el titulo", r.json()["title"] == "Acuarela nueva", r.text)
        check("y la descripcion no se toca al no mandarla",
              r.json()["description"] == "Pintada en Concepcion", r.text)
        r = c.patch(f"/api/posts/{pid}", headers=ana, json={"tag_ids": []})
        check("se pueden quitar todos los #", r.json()["tags"] == [], r.text)
        r = c.patch(f"/api/posts/{pid}", headers=ana, json={"tag_ids": [99999]})
        check("rechaza un # inexistente", r.status_code == 404, r.text)

        print("\n12. Quitar un archivo recoloca el orden")
        r = c.get(f"/api/posts/{pid}", headers=ana)
        archivos = r.json()["files"]
        check("hay 3 archivos en posiciones 0,1,2",
              [f["position"] for f in archivos] == [0, 1, 2], str(archivos))
        c.delete(f"/api/posts/{pid}/files/{archivos[0]['id']}", headers=ana)
        r = c.get(f"/api/posts/{pid}", headers=ana)
        check("tras borrar el primero quedan 2 sin huecos",
              [f["position"] for f in r.json()["files"]] == [0, 1], str(r.json()["files"]))
        check("el archivo borrado ya no se descarga", c.get(url_imagen).status_code == 404)

        print("\n13. El tope de 10 archivos")
        r = c.post("/api/posts", headers=ana, json={"description": "diez archivos de prueba"})
        lleno = r.json()["id"]
        for i in range(10):
            c.post(f"/api/posts/{lleno}/files", headers=ana,
                   files={"file": (f"f{i}.png", png_bytes(), "image/png")})
        r = c.post(f"/api/posts/{lleno}/files", headers=ana,
                   files={"file": ("once.png", png_bytes(), "image/png")})
        check("el archivo numero 11 se rechaza", r.status_code == 422, r.text)
        check("y quedan exactamente 10",
              len(c.get(f"/api/posts/{lleno}", headers=ana).json()["files"]) == 10)

        print("\n14. Eliminar la publicacion")
        r = c.get(f"/api/posts/{pid}", headers=ana)
        urls = [f["url"] for f in r.json()["files"]]
        r = c.delete(f"/api/posts/{pid}", headers=beto)
        check("otro usuario no puede eliminar (403)", r.status_code == 403, r.text)
        r = c.delete(f"/api/posts/{pid}", headers=ana)
        check("el autor la elimina", r.status_code == 200, r.text)
        check("deja de existir", c.get(f"/api/posts/{pid}", headers=ana).status_code == 404)
        check("sus archivos se borraron del disco",
              all(c.get(u).status_code == 404 for u in urls), str(urls))
        check("sus comentarios se fueron con ella",
              c.get(f"/api/posts/{pid}/comments", headers=ana).status_code == 404)

        print("\n15. El perfil publico y el grid")
        r = c.get(f"/api/users/{ana_user}/posts")
        check("el grid sigue respondiendo tras el borrado", r.status_code == 200)
        ids = [p["id"] for p in r.json()]
        check("ordenado de la mas nueva a la mas vieja", ids == sorted(ids, reverse=True), str(ids))
        r = c.get("/api/users/no_existe_este_usuario/posts")
        check("un perfil inexistente responde 404", r.status_code == 404, r.text)

        solo_texto = [p for p in c.get(f"/api/users/{ana_user}/posts").json()
                      if p["files_count"] == 0]
        check("una publicacion de solo texto llega con preview=None",
              solo_texto and solo_texto[0]["preview"] is None, str(solo_texto[:1]))

    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS PASARON" if FAILURES == 0 else f"{FAILURES} PRUEBA(S) FALLARON")
    print("=" * 60)
    return 0 if FAILURES == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
