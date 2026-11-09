from __future__ import annotations
from datetime import date
from typing import Any

import flet as ft

from pruebas.piloto import Piloto, descendientes

CLAVE = "Secreta123"

def personaje(base: str, nombre_visible: str, sufijo: str = "") -> dict[str, str]:
    usuario = f"{base}{sufijo}"
    return {
        "email": f"{usuario}@ubiobio.cl",
        "name": nombre_visible,
        "username": usuario,
        "password": CLAVE,
    }

def _sigue_en(piloto: Piloto, ruta: str, que_se_esperaba: str) -> None:
    if piloto.ruta != ruta:
        raise AssertionError(
            f"[{piloto.nombre}] {que_se_esperaba}, pero la app avanzo de "
            f"{ruta} a {piloto.ruta}."
        )

def _error_del_campo(piloto: Piloto, etiqueta: str) -> str:
    return piloto.campo(etiqueta).error or ""

def _exigir_error_en(piloto: Piloto, etiqueta: str, texto: str) -> None:
    mensaje = _error_del_campo(piloto, etiqueta)

    if texto.lower() not in mensaje.lower():
        errores = {
            (c.label or c.hint_text or "?"): c.error
            for c in piloto.campos()
            if c.error
        }
        raise AssertionError(
            f"[{piloto.nombre}] Esperaba el error '{texto}' bajo el campo "
            f"'{etiqueta}'.\nLos campos marcados en rojo son: {errores or 'ninguno'}"
        )

async def _registrarse(piloto: Piloto, datos: dict[str, str]) -> None:
    await piloto.ir("/register")
    piloto.exigir_texto("Bienvenido")

    await piloto.escribir("Mail", datos["email"])
    await piloto.escribir("Nombre completo", datos["name"])
    await piloto.escribir("Nombre de usuario", datos["username"])
    await piloto.escribir("Contraseña", datos["password"])
    await piloto.escribir("Confirmar Contraseña", datos["password"])

    await piloto.tocar("Iniciar Sesion")

    if piloto.ruta != "/onboarding/birthdate":
        raise AssertionError(
            f"[{piloto.nombre}] El registro no avanzo. Sigue en {piloto.ruta}.\n"
            f"Avisos en pantalla: {piloto.avisos()}"
        )

async def _iniciar_sesion(piloto: Piloto, datos: dict[str, str]) -> None:
    await piloto.ir("/login")

    await piloto.escribir("Nombre de Usuario o Mail", datos["username"])
    await piloto.escribir("Contraseña", datos["password"])

    await piloto.tocar("Iniciar Sesion")

    if piloto.ruta != "/profile":
        raise AssertionError(
            f"[{piloto.nombre}] El login no avanzo. Sigue en {piloto.ruta}.\n"
            f"Avisos en pantalla: {piloto.avisos()}"
        )

async def _cerrar_sesion(piloto: Piloto) -> None:
    await piloto.ir("/settings/account")
    await piloto.tocar("Cerrar sesión")
    await piloto.tocar_en_dialogo("Cerrar sesión")

    if piloto.state.is_authenticated:
        raise AssertionError(
            f"[{piloto.nombre}] La sesion no se cerro: el estado sigue con "
            f"{(piloto.state.user or {}).get('username')} dentro."
        )

def _color_del_corazon(piloto: Piloto) -> str | None:
    for nodo in descendientes(piloto.vista):
        if isinstance(nodo, ft.IconButton) and nodo.tooltip == "Me gusta":
            return nodo.icon_color
    return None

def _contadores(piloto: Piloto) -> list[str]:
    return [t.strip() for t in piloto.textos() if t.strip().isdigit()]

async def recorrido_onboarding(piloto: Piloto, sufijo: str = "") -> dict[str, Any]:
    datos = personaje("ana", "Ana Pintora", sufijo)

    BIO = "Pinto al oleo paisajes del sur de Chile"
    DIA, MES, ANIO = "03", "05", "2000"
    ESPECIALIDADES = ["Pintor", "Ilustrador"]

    async with piloto.paso("Crear la cuenta"):
        await _registrarse(piloto, datos)

    async with piloto.paso("La fecha de nacimiento rechaza lo imposible"):
        piloto.exigir_texto("Ingresa tu fecha de nacimiento")
        piloto.limpiar_avisos()

        await piloto.escribir("DD", "31")
        await piloto.escribir("MM", "02")
        await piloto.escribir("AAAA", "2000")
        await piloto.tocar("Listo")

        if not piloto.hubo_aviso("Esa fecha no existe"):
            raise AssertionError(
                f"El 31 de febrero deberia rechazarse. Avisos: {piloto.avisos()}"
            )
        _sigue_en(piloto, "/onboarding/birthdate", "La fecha 31/02 es invalida")

        piloto.limpiar_avisos()
        hoy = date.today()

        await piloto.escribir("DD", "01")
        await piloto.escribir("MM", "01")
        await piloto.escribir("AAAA", str(hoy.year - 10))
        await piloto.tocar("Listo")

        if not piloto.hubo_aviso("al menos 13"):
            raise AssertionError(
                f"Un chico de 10 anios deberia rechazarse. Avisos: {piloto.avisos()}"
            )
        _sigue_en(piloto, "/onboarding/birthdate", "Un menor de 13 no puede pasar")

    async with piloto.paso("Escribir una fecha valida"):
        piloto.limpiar_avisos()

        await piloto.escribir("DD", DIA)
        await piloto.escribir("MM", MES)
        await piloto.escribir("AAAA", ANIO)

        await piloto.tocar("Listo")

        if piloto.ruta != "/onboarding/tags":
            raise AssertionError(
                f"Esperaba pasar a las especialidades y estoy en {piloto.ruta}. "
                f"Avisos: {piloto.avisos()}"
            )

        guardada = (piloto.state.user or {}).get("birthdate")
        esperada = f"{ANIO}-{MES}-{DIA}"
        if guardada != esperada:
            raise AssertionError(
                f"La fecha se guardo como {guardada!r} y esperaba {esperada!r}"
            )

    async with piloto.paso("Elegir las especialidades"):
        piloto.exigir_texto("En que tipo de artes te especializas")

        for nombre in ESPECIALIDADES:
            await piloto.tocar(f"#{nombre}")

        await piloto.tocar("Listo")

        if piloto.ruta != "/onboarding/avatar":
            raise AssertionError(
                f"Esperaba pasar a la foto de perfil y estoy en {piloto.ruta}. "
                f"Avisos: {piloto.avisos()}"
            )

        elegidas = sorted(t["name"] for t in (piloto.state.user or {}).get("tipo") or [])
        if elegidas != sorted(ESPECIALIDADES):
            raise AssertionError(
                f"Las especialidades guardadas son {elegidas} y esperaba "
                f"{sorted(ESPECIALIDADES)}"
            )

    async with piloto.paso("Omitir la foto de perfil"):
        piloto.exigir_texto("Escoge tu foto de perfil")

        await piloto.tocar("Omitir")

        if piloto.ruta != "/profile":
            raise AssertionError(
                f"Esperaba llegar al perfil y estoy en {piloto.ruta}"
            )

    async with piloto.paso("Ver el perfil ya armado"):
        piloto.exigir_texto(datos["name"])
        piloto.exigir_texto(f"@{datos['username']}")

        for nombre in ESPECIALIDADES:
            piloto.exigir_texto(f"#{nombre}")

        piloto.exigir_texto("Agrega una presentacion")

    async with piloto.paso("Escribir la presentacion"):
        await piloto.tocar("Editar presentación")

        await piloto.escribir("Presentacion", BIO)
        await piloto.tocar_en_dialogo("Guardar")

        if not piloto.hubo_aviso("actualizada"):
            raise AssertionError(
                f"Esperaba el aviso de que se guardo. Avisos: {piloto.avisos()}"
            )

        piloto.exigir_texto(BIO)

    async with piloto.paso("Cerrar sesion"):
        await _cerrar_sesion(piloto)

        if piloto.ruta != "/login":
            raise AssertionError(
                f"Al cerrar sesion esperaba volver al login y estoy en {piloto.ruta}"
            )

    async with piloto.paso("Volver a entrar y comprobar que todo siguio ahi"):
        await _iniciar_sesion(piloto, datos)

        piloto.exigir_texto(BIO)

        for nombre in ESPECIALIDADES:
            piloto.exigir_texto(f"#{nombre}")

        usuario = piloto.state.user or {}
        if usuario.get("birthdate") != f"{ANIO}-{MES}-{DIA}":
            raise AssertionError(
                f"Al volver a entrar, la fecha es {usuario.get('birthdate')!r}"
            )

    return {
        "usuario": datos,
        "bio": BIO,
        "especialidades": ESPECIALIDADES,
        "nacimiento": f"{ANIO}-{MES}-{DIA}",
    }

async def recorrido_social(piloto: Piloto, sufijo: str = "") -> dict[str, Any]:
    ana = personaje("ana", "Ana Pintora", sufijo)
    beto = personaje("beto", "Beto Musico", sufijo)

    TITULO = "Atardecer en el Bio Bio"
    DESCRIPCION = "Un oleo que pinte mirando el rio desde el puente"
    COMENTARIO = "Que buen uso del color, Ana!"

    async with piloto.paso("Ana crea su cuenta"):
        await _registrarse(piloto, ana)

        await piloto.ir("/profile")

    async with piloto.paso("Ana publica su obra"):
        await piloto.tocar("Crear una publicacion")

        if piloto.ruta != "/post/new":
            raise AssertionError(f"Esperaba el editor y estoy en {piloto.ruta}")

        piloto.limpiar_avisos()

        await piloto.escribir("Titulo", TITULO)
        await piloto.escribir("Descripcion", "corta")
        await piloto.tocar("Publicar")

        if not piloto.hubo_aviso("al menos 10 caracteres"):
            raise AssertionError(
                f"Una descripcion de 5 letras deberia rechazarse. "
                f"Avisos: {piloto.avisos()}"
            )
        _sigue_en(piloto, "/post/new", "Una publicacion vacia no se puede publicar")

        piloto.limpiar_avisos()

        await piloto.escribir("Descripcion", DESCRIPCION)

        await piloto.tocar("Publicar")

        if not piloto.hubo_aviso("Publicacion creada"):
            raise AssertionError(
                f"Esperaba el aviso de publicacion creada. Avisos: {piloto.avisos()}"
            )

        if piloto.ruta != "/profile":
            raise AssertionError(
                f"Despues de publicar esperaba el perfil y estoy en {piloto.ruta}"
            )

        piloto.exigir_texto(DESCRIPCION)

    async with piloto.paso("Ana cierra sesion y entra Beto"):
        await _cerrar_sesion(piloto)
        piloto.limpiar_avisos()
        await _registrarse(piloto, beto)

    async with piloto.paso("Beto busca a Ana"):
        await piloto.ir("/search")

        await piloto.escribir_unico(ana["username"])
        await piloto.tocar("Buscar")

        piloto.exigir_texto(ana["username"])

    async with piloto.paso("Beto entra al perfil de Ana"):
        await piloto.tocar(ana["username"])

        if piloto.ruta != f"/user/{ana['username']}":
            raise AssertionError(
                f"Esperaba el perfil publico de Ana y estoy en {piloto.ruta}"
            )

        piloto.exigir_texto(ana["name"])
        piloto.exigir_texto(DESCRIPCION)

    async with piloto.paso("Beto abre la publicacion"):
        await piloto.tocar(DESCRIPCION)

        if not piloto.ruta.startswith("/post/"):
            raise AssertionError(
                f"Esperaba abrir la publicacion y estoy en {piloto.ruta}"
            )

        post_id = int(piloto.ruta.strip("/").split("/")[1])

        piloto.exigir_texto(TITULO)

        if piloto.hay_texto("Configuracion de la publicacion"):
            raise AssertionError(
                "Beto no es el autor y le aparece el boton de configuracion"
            )

    async with piloto.paso("Beto da me gusta"):
        antes = _color_del_corazon(piloto)

        await piloto.tocar("Me gusta")

        despues = _color_del_corazon(piloto)

        if antes == despues:
            raise AssertionError(
                f"El corazon no cambio de color: seguia en {despues!r}"
            )

        from style.theme import Colors

        if despues != Colors.BRAND_RED:
            raise AssertionError(
                f"Esperaba el corazon en {Colors.BRAND_RED} y quedo en {despues!r}"
            )

        if "1" not in _contadores(piloto):
            raise AssertionError(
                f"Esperaba el contador en 1 y los numeros en pantalla son "
                f"{_contadores(piloto)}"
            )

    async with piloto.paso("Beto comenta"):
        await piloto.tocar("Comentarios")

        if not piloto.ruta.endswith("/comments"):
            raise AssertionError(
                f"Esperaba la ventana de comentarios y estoy en {piloto.ruta}"
            )

        piloto.exigir_texto("Todavia no hay comentarios")

        await piloto.tocar("Enviar")

        piloto.exigir_texto("Todavia no hay comentarios")

        await piloto.escribir("Escribe un comentario", COMENTARIO)
        await piloto.tocar("Enviar")

        piloto.exigir_texto(COMENTARIO)

        campo = piloto.campo("Escribe un comentario")
        if (campo.value or "").strip():
            raise AssertionError(
                f"El campo no se limpio: quedo con {campo.value!r}"
            )

    async with piloto.paso("Beto cierra sesion y vuelve Ana"):
        await _cerrar_sesion(piloto)
        piloto.limpiar_avisos()
        await _iniciar_sesion(piloto, ana)

    async with piloto.paso("Ana ve el me gusta y el comentario"):
        await piloto.ir(f"/post/{post_id}")

        if _contadores(piloto).count("1") < 2:
            raise AssertionError(
                f"Esperaba los dos contadores en 1 y veo {_contadores(piloto)}"
            )

        from style.theme import Colors

        corazon = _color_del_corazon(piloto)
        if corazon == Colors.BRAND_RED:
            raise AssertionError(
                "El corazon de Ana esta rojo, pero el me gusta lo dio Beto. "
                "liked_by_me se esta calculando mal."
            )

        if not piloto.hay_texto("Configuracion de la publicacion"):
            raise AssertionError(
                "Ana es la autora y no le aparece el boton de configuracion"
            )

    async with piloto.paso("Ana borra el comentario de Beto"):
        await piloto.tocar("Comentarios")

        piloto.exigir_texto(COMENTARIO)
        piloto.exigir_texto(beto["username"])

        if not piloto.hay_texto("Eliminar"):
            raise AssertionError(
                "Ana es la dueña de la publicacion y no puede borrar el "
                "comentario de Beto"
            )

        await piloto.tocar("Eliminar")

        if piloto.hay_texto(COMENTARIO):
            raise AssertionError("El comentario sigue en pantalla despues de borrarlo")

        piloto.exigir_texto("Todavia no hay comentarios")

    return {
        "ana": ana,
        "beto": beto,
        "post_id": post_id,
        "titulo": TITULO,
        "descripcion": DESCRIPCION,
        "comentario": COMENTARIO,
    }

async def recorrido_validaciones(piloto: Piloto, sufijo: str = "") -> dict[str, Any]:
    datos = personaje("rai", "Raimundo Koch", sufijo)

    TITULO = "Mi primera obra"
    DESCRIPCION = "Un retrato a lapiz que hice el fin de semana"

    async def llenar_registro(**cambios: str) -> None:
        valores = {
            "Mail": datos["email"],
            "Nombre completo": datos["name"],
            "Nombre de usuario": datos["username"],
            "Contraseña": datos["password"],
            "Confirmar Contraseña": datos["password"],
        }
        valores.update(cambios)

        for etiqueta, valor in valores.items():
            await piloto.escribir(etiqueta, valor)

    async with piloto.paso("El formulario rechaza un correo mal escrito"):
        await piloto.ir("/register")
        piloto.exigir_texto("Bienvenido")

        await llenar_registro(Mail="rai-arroba-ubiobio.cl")
        await piloto.tocar("Iniciar Sesion")

        _exigir_error_en(piloto, "Mail", "no parece valido")
        _sigue_en(piloto, "/register", "Un correo sin arroba es invalido")

    async with piloto.paso("Rechaza una contrasena de menos de 6 caracteres"):
        await llenar_registro(**{"Contraseña": "abc", "Confirmar Contraseña": "abc"})
        await piloto.tocar("Iniciar Sesion")

        _exigir_error_en(piloto, "Contraseña", "Minimo 6")
        _sigue_en(piloto, "/register", "Una contrasena de 3 letras es muy corta")

    async with piloto.paso("Rechaza dos contrasenas que no coinciden"):
        await llenar_registro(**{"Confirmar Contraseña": "OtraClave456"})
        await piloto.tocar("Iniciar Sesion")

        _exigir_error_en(piloto, "Confirmar Contraseña", "no coinciden")
        _sigue_en(piloto, "/register", "Las dos contrasenas tienen que ser iguales")

    async with piloto.paso("Rechaza un nombre de usuario de menos de 3 caracteres"):
        await llenar_registro(**{"Nombre de usuario": "ra"})
        await piloto.tocar("Iniciar Sesion")

        _exigir_error_en(piloto, "Nombre de usuario", "Minimo 3")
        _sigue_en(piloto, "/register", "Un @ de 2 letras es muy corto")

    async with piloto.paso("Con todo correcto, la cuenta se crea"):
        await llenar_registro()
        await piloto.tocar("Iniciar Sesion")

        if piloto.ruta != "/onboarding/birthdate":
            raise AssertionError(
                f"El registro valido no avanzo. Sigue en {piloto.ruta}.\n"
                f"Avisos: {piloto.avisos()}"
            )

    async with piloto.paso("Cerrar sesion"):
        await piloto.ir("/profile")
        await _cerrar_sesion(piloto)

    async with piloto.paso("El login rechaza una contrasena incorrecta"):
        piloto.limpiar_avisos()

        await piloto.ir("/login")
        await piloto.escribir("Nombre de Usuario o Mail", datos["username"])
        await piloto.escribir("Contraseña", "ClaveEquivocada999")
        await piloto.tocar("Iniciar Sesion")

        if not piloto.hubo_aviso("incorrectos"):
            raise AssertionError(
                f"Esperaba el aviso de credenciales incorrectas. "
                f"Avisos: {piloto.avisos()}"
            )
        _sigue_en(piloto, "/login", "Con la contrasena mala no se entra")

    async with piloto.paso("El login rechaza un usuario que no existe"):
        piloto.limpiar_avisos()

        await piloto.escribir("Nombre de Usuario o Mail", "nadie" + sufijo)
        await piloto.escribir("Contraseña", datos["password"])
        await piloto.tocar("Iniciar Sesion")

        if not piloto.hubo_aviso("incorrectos"):
            raise AssertionError(
                f"Esperaba el mismo aviso que con la contrasena mala. "
                f"Avisos: {piloto.avisos()}"
            )
        _sigue_en(piloto, "/login", "Un usuario inexistente no entra")

    async with piloto.paso("Con las credenciales correctas, entra"):
        piloto.limpiar_avisos()
        await _iniciar_sesion(piloto, datos)

        piloto.exigir_texto(f"@{datos['username']}")

    async with piloto.paso("Crear la primera publicacion"):
        await piloto.tocar("Crear una publicacion")

        await piloto.escribir("Titulo", TITULO)
        await piloto.escribir("Descripcion", DESCRIPCION)
        await piloto.tocar("Publicar")

        if not piloto.hubo_aviso("Publicacion creada"):
            raise AssertionError(
                f"Esperaba el aviso de publicacion creada. Avisos: {piloto.avisos()}"
            )

        piloto.exigir_texto(DESCRIPCION)

    async with piloto.paso("No se puede registrar el mismo correo dos veces"):
        piloto.limpiar_avisos()
        await _cerrar_sesion(piloto)
        piloto.limpiar_avisos()

        await piloto.ir("/register")

        await llenar_registro(**{"Nombre de usuario": "otro" + (sufijo or "nombre")})
        await piloto.tocar("Iniciar Sesion")

        _exigir_error_en(piloto, "Mail", "ya esta registrado")
        _sigue_en(piloto, "/register", "Ese correo ya tiene cuenta")

    return {
        "usuario": datos,
        "titulo": TITULO,
        "descripcion": DESCRIPCION,
    }

RECORRIDOS = {
    "onboarding": {
        "titulo": "Onboarding del perfil",
        "resumen": (
            "Registro, fecha de nacimiento, especialidades, foto, presentacion, "
            "y volver a entrar para comprobar que nada se perdio."
        ),
        "funcion": recorrido_onboarding,
    },
    "social": {
        "titulo": "Recorrido social",
        "resumen": (
            "Ana publica, Beto la encuentra, le da me gusta y comenta; "
            "Ana vuelve y borra el comentario."
        ),
        "funcion": recorrido_social,
    },
    "validaciones": {
        "titulo": "Registro, validaciones y primera publicacion",
        "resumen": (
            "Pelea con el formulario: correo mal escrito, contrasena corta, "
            "contrasenas distintas, login fallido y correo repetido. Y al "
            "final, todo bien."
        ),
        "funcion": recorrido_validaciones,
    },
}
