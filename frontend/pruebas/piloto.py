from __future__ import annotations

import asyncio
import dataclasses
import unicodedata

from typing import Any, Callable, Iterator

import flet as ft

CAMPOS_INTERNOS = {"_values", "_dirty", "_internals", "_c", "_i", "page", "parent"}

def descendientes(control: Any) -> Iterator[ft.Control]:
    vistos: set[int] = set()

    def recorrer(nodo: Any) -> Iterator[ft.Control]:
        if nodo is None:
            return

        if isinstance(nodo, (list, tuple)):
            for hijo in nodo:
                yield from recorrer(hijo)
            return

        if isinstance(nodo, dict):
            for hijo in nodo.values():
                yield from recorrer(hijo)
            return

        if not isinstance(nodo, ft.Control):
            return

        if id(nodo) in vistos:
            return
        vistos.add(id(nodo))

        yield nodo

        if not dataclasses.is_dataclass(nodo):
            return

        for campo in dataclasses.fields(nodo):
            if campo.name in CAMPOS_INTERNOS:
                continue
            try:
                valor = getattr(nodo, campo.name)
            except Exception:
                continue
            yield from recorrer(valor)

    yield from recorrer(control)

def _normalizar(texto: str | None) -> str:
    if not texto:
        return ""
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.lower().split())

ATRIBUTOS_DE_TEXTO = ("content", "label", "hint_text", "tooltip", "error", "helper", "text")

def textos_de(control: Any) -> list[str]:
    encontrados: list[str] = []

    for nodo in descendientes(control):
        if isinstance(nodo, ft.Text) and nodo.value:
            encontrados.append(str(nodo.value))

        for atributo in ATRIBUTOS_DE_TEXTO:
            valor = getattr(nodo, atributo, None)
            if isinstance(valor, str) and valor:
                encontrados.append(valor)

    return encontrados

class PrefsFalsas:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.datos: dict[str, Any] = {}

    async def get(self, clave: str, default: Any = None) -> Any:
        return self.datos.get(clave, default)

    async def set(self, clave: str, valor: Any) -> bool:
        self.datos[clave] = valor
        return True

    async def remove(self, clave: str) -> bool:
        self.datos.pop(clave, None)
        return True

    async def clear(self) -> bool:
        self.datos.clear()
        return True

    async def contains_key(self, clave: str) -> bool:
        return clave in self.datos

class SelectorFalso:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.respuesta: list[Any] = []

    async def pick_files(self, *args: Any, **kwargs: Any) -> list[Any]:
        return self.respuesta

class VentanaFalsa:
    width: int = 414
    height: int = 896
    min_width: int = 360
    min_height: int = 640

class PaginaFalsa:
    def __init__(self) -> None:
        self.route: str = "/"
        self.views: list[ft.View] = []
        self.window = VentanaFalsa()

        self.title: str | None = None
        self.theme: Any = None
        self.theme_mode: Any = None
        self.bgcolor: Any = None
        self.padding: Any = 0
        self.fonts: dict[str, str] = {}

        self.on_route_change: Callable | None = None
        self.on_view_pop: Callable | None = None

    def update(self) -> None:
        pass

    def show_dialog(self, dialogo: Any) -> None:
        pass

    def pop_dialog(self, *args: Any) -> None:
        pass

    def run_task(self, funcion: Callable, *args: Any) -> Any:
        return asyncio.ensure_future(funcion(*args))

    async def push_route(self, ruta: str) -> None:
        self.route = ruta
        if self.on_route_change is not None:
            await self.on_route_change(None)

_update_original = ft.Control.update

def _update_tolerante(self: ft.Control, *args: Any, **kwargs: Any) -> None:
    try:
        _update_original(self, *args, **kwargs)
    except (RuntimeError, AssertionError):
        pass

_DIALOGOS: dict[int, list[Any]] = {}
_RUTAS: dict[int, list[str]] = {}

def _escuchar(page: Any) -> None:
    _DIALOGOS.setdefault(id(page), [])
    _RUTAS.setdefault(id(page), [])

    clase = type(page)
    if getattr(clase, "_ashun_escuchada", False):
        return

    show_original = getattr(clase, "show_dialog", None)
    pop_original = getattr(clase, "pop_dialog", None)
    push_original = getattr(clase, "push_route", None)

    if show_original is not None:
        def show_dialog(self: Any, dialogo: Any, *args: Any, **kwargs: Any) -> Any:
            _DIALOGOS.setdefault(id(self), []).append(dialogo)
            return show_original(self, dialogo, *args, **kwargs)

        clase.show_dialog = show_dialog

    if pop_original is not None:
        def pop_dialog(self: Any, *args: Any, **kwargs: Any) -> Any:
            lista = _DIALOGOS.get(id(self))
            if lista:
                lista.pop()
            return pop_original(self, *args, **kwargs)

        clase.pop_dialog = pop_dialog

    if push_original is not None:
        async def push_route(self: Any, ruta: str, *args: Any, **kwargs: Any) -> Any:
            _RUTAS.setdefault(id(self), []).append(ruta)
            return await push_original(self, ruta, *args, **kwargs)

        clase.push_route = push_route

    clase._ashun_escuchada = True

@dataclasses.dataclass
class Paso:
    numero: int
    nombre: str
    estado: str = "pendiente"
    detalle: str = ""

class ErrorDePiloto(AssertionError):
    pass

class Piloto:
    def __init__(
        self,
        page: Any,
        state: Any = None,
        *,
        nombre: str = "piloto",
        pausa: float = 0.0,
        al_paso: Callable[[Paso], Any] | None = None,
    ) -> None:
        self.page = page
        self.nombre = nombre
        self.pausa = pausa
        self.al_paso = al_paso
        self.pasos: list[Paso] = []
        self.token: str | None = None

        if state is None:
            from context.app_state import AppState

            state = AppState(page)

        self.state = state

        _escuchar(page)

    @property
    def rutas(self) -> list[str]:
        return _RUTAS.get(id(self.page), [])

    async def iniciar(self) -> None:
        await self.state.start()

    def instalar_enrutador(self, route_change: Callable) -> None:
        self.page.on_route_change = route_change

    def recordar_token(self) -> None:
        from services.api_client import api

        self.token = api.token

    def activar(self) -> None:
        from services.api_client import api

        api.set_token(self.token)

    @property
    def vista(self) -> ft.View:
        if not self.page.views:
            raise ErrorDePiloto(
                f"[{self.nombre}] No hay ninguna pantalla abierta. "
                "¿Se llamo a ir() alguna vez?"
            )
        return self.page.views[-1]

    @property
    def ruta(self) -> str:
        return self.page.route

    async def ir(self, ruta: str) -> None:
        self.activar()
        await self.page.push_route(ruta)
        await self.esperar()

    async def esperar(self, veces: float = 1.0) -> None:
        if self.pausa > 0:
            await asyncio.sleep(self.pausa * veces)

    def campos(self) -> list[ft.TextField]:
        del_dialogo: list[ft.TextField] = []

        dialogos = self.dialogos_abiertos()
        if dialogos:
            del_dialogo = [
                c for c in descendientes(dialogos[-1]) if isinstance(c, ft.TextField)
            ]

        de_la_vista = [c for c in descendientes(self.vista) if isinstance(c, ft.TextField)]

        return del_dialogo + de_la_vista

    def campo(self, etiqueta: str) -> ft.TextField:
        buscado = _normalizar(etiqueta)

        for campo in self.campos():
            for atributo in ("label", "hint_text", "helper"):
                valor = getattr(campo, atributo, None)
                if valor and buscado in _normalizar(str(valor)):
                    return campo

        disponibles = [
            (c.label or c.hint_text or "(sin etiqueta)") for c in self.campos()
        ]
        raise ErrorDePiloto(
            f"[{self.nombre}] No encontre el campo '{etiqueta}' en {self.ruta}.\n"
            f"Los campos que hay son: {disponibles}"
        )

    def unico_campo(self) -> ft.TextField:
        encontrados = self.campos()

        if len(encontrados) == 1:
            return encontrados[0]

        if not encontrados:
            raise ErrorDePiloto(
                f"[{self.nombre}] No hay ningun campo de texto en {self.ruta}."
            )

        etiquetas = [(c.label or c.hint_text or "(sin etiqueta)") for c in encontrados]
        raise ErrorDePiloto(
            f"[{self.nombre}] Pedi 'el unico campo' de {self.ruta} pero hay "
            f"{len(encontrados)}: {etiquetas}. Usa campo('etiqueta') en su lugar."
        )

    async def escribir_unico(self, texto: str) -> None:
        campo = self.unico_campo()

        if self.pausa > 0:
            campo.value = ""
            for letra in str(texto):
                campo.value = (campo.value or "") + letra
                self._repintar(campo)
                await asyncio.sleep(min(0.04, self.pausa / 8))
        else:
            campo.value = texto

        self._repintar(campo)
        await self.esperar(0.4)

    def tocables(self) -> list[ft.Control]:
        resultado = []
        for nodo in descendientes(self.vista):
            if isinstance(nodo, ft.TextField):
                continue
            if getattr(nodo, "on_click", None) is not None:
                resultado.append(nodo)
        return resultado

    def boton(self, texto: str) -> ft.Control:
        buscado = _normalizar(texto)

        candidatos = self.tocables()

        for nodo in candidatos:
            tooltip = getattr(nodo, "tooltip", None)
            if isinstance(tooltip, str) and buscado == _normalizar(tooltip):
                return nodo

        coincidencias = [
            nodo
            for nodo in candidatos
            if any(buscado in _normalizar(t) for t in textos_de(nodo))
        ]

        if coincidencias:
            coincidencias.sort(key=lambda n: len(list(descendientes(n))))
            return coincidencias[0]

        visibles = sorted({_normalizar(t) for t in textos_de(self.vista) if t})
        raise ErrorDePiloto(
            f"[{self.nombre}] No encontre nada tocable con el texto '{texto}' "
            f"en {self.ruta}.\nLo que se ve en pantalla es: {visibles}"
        )

    def textos(self) -> list[str]:
        return textos_de(self.vista)

    def hay_texto(self, texto: str) -> bool:
        buscado = _normalizar(texto)
        return any(buscado in _normalizar(t) for t in self.textos())

    def exigir_texto(self, texto: str) -> None:
        if not self.hay_texto(texto):
            visibles = sorted({_normalizar(t) for t in self.textos() if t})
            raise ErrorDePiloto(
                f"[{self.nombre}] Esperaba leer '{texto}' en {self.ruta} y no esta.\n"
                f"Lo que se ve es: {visibles}"
            )

    def avisos(self) -> list[str]:
        mensajes: list[str] = []
        for dialogo in self.dialogos_abiertos():
            for texto in textos_de(dialogo):
                mensajes.append(texto)
        return mensajes

    def hubo_aviso(self, texto: str) -> bool:
        buscado = _normalizar(texto)
        return any(buscado in _normalizar(a) for a in self.avisos())

    def dialogos_abiertos(self) -> list[Any]:
        return _DIALOGOS.get(id(self.page), [])

    def limpiar_avisos(self) -> None:
        self.dialogos_abiertos().clear()

    async def escribir(self, etiqueta: str, texto: str) -> None:
        campo = self.campo(etiqueta)

        if self.pausa > 0:
            campo.value = ""
            for letra in str(texto):
                campo.value = (campo.value or "") + letra
                self._repintar(campo)
                await asyncio.sleep(min(0.04, self.pausa / 8))
        else:
            campo.value = texto

        self._repintar(campo)
        await self.esperar(0.4)

    async def tocar(self, texto: str) -> None:
        self.activar()
        control = self.boton(texto)
        await self._disparar(control.on_click, control)
        self.recordar_token()
        await self.esperar()

    async def tocar_en_dialogo(self, texto: str) -> None:
        self.activar()

        abiertos = self.dialogos_abiertos()

        if not abiertos:
            raise ErrorDePiloto(
                f"[{self.nombre}] Esperaba un dialogo abierto para tocar "
                f"'{texto}' y no hay ninguno."
            )

        dialogo = abiertos[-1]
        buscado = _normalizar(texto)

        for nodo in descendientes(dialogo):
            if getattr(nodo, "on_click", None) is None:
                continue
            if any(buscado in _normalizar(t) for t in textos_de(nodo)):
                await self._disparar(nodo.on_click, nodo)
                self.recordar_token()
                await self.esperar()
                return

        raise ErrorDePiloto(
            f"[{self.nombre}] En el dialogo no hay ningun boton '{texto}'. "
            f"Hay: {sorted(set(textos_de(dialogo)))}"
        )

    async def _disparar(self, handler: Callable, control: ft.Control) -> None:
        import inspect

        try:
            cantidad = len(inspect.signature(handler).parameters)
        except (TypeError, ValueError):
            cantidad = 1

        evento = ft.ControlEvent(name="click", data="", control=control)

        if cantidad == 0:
            resultado = handler()
        else:
            resultado = handler(evento)

        if inspect.isawaitable(resultado):
            await resultado

    def _repintar(self, *controles: ft.Control) -> None:
        for control in controles:
            try:
                control.update()
            except (RuntimeError, AssertionError):
                pass
        try:
            self.page.update()
        except Exception:
            pass

    def paso(self, nombre: str) -> "_PasoEnCurso":
        paso = Paso(numero=len(self.pasos) + 1, nombre=nombre)
        self.pasos.append(paso)
        return _PasoEnCurso(self, paso)

    async def _avisar_paso(self, paso: Paso) -> None:
        if self.al_paso is None:
            return
        resultado = self.al_paso(paso)
        if hasattr(resultado, "__await__"):
            await resultado

    def informe(self) -> str:
        simbolos = {"ok": "[ok]   ", "fallo": "[FALLO]", "pendiente": "[  -  ]"}
        lineas = []
        for paso in self.pasos:
            linea = f"  {simbolos.get(paso.estado, '')} {paso.numero}. {paso.nombre}"
            if paso.detalle:
                linea += f"\n          {paso.detalle}"
            lineas.append(linea)
        return "\n".join(lineas)

class _PasoEnCurso:
    def __init__(self, piloto: Piloto, paso: Paso) -> None:
        self.piloto = piloto
        self.paso = paso

    async def __aenter__(self) -> Paso:
        await self.piloto._avisar_paso(self.paso)
        return self.paso

    async def __aexit__(self, tipo, error, traza) -> bool:
        if error is None:
            self.paso.estado = "ok"
        else:
            self.paso.estado = "fallo"
            self.paso.detalle = f"{type(error).__name__}: {error}"

        await self.piloto._avisar_paso(self.paso)

        return False

async def piloto_sin_pantalla(
    nombre: str = "usuario",
    *,
    pausa: float = 0.0,
) -> Piloto:
    ft.Control.update = _update_tolerante

    ft.SharedPreferences = PrefsFalsas

    ft.FilePicker = SelectorFalso

    from context.app_state import AppState

    page = PaginaFalsa()
    state = AppState(page)

    piloto = Piloto(page, state, nombre=nombre, pausa=pausa)
    await piloto.iniciar()

    piloto.instalar_enrutador(enrutador_de_app(page, state))

    return piloto

def enrutador_de_app(page: Any, state: Any) -> Callable:
    import traceback

    from pages import (
        account_page,
        avatar_page,
        birthdate_page,
        comments_page,
        login_page,
        post_editor_page,
        post_page,
        post_settings_page,
        profile_page,
        public_profile_page,
        register_page,
        search_page,
        settings_page,
        tags_page,
    )

    async def route_change(evento: Any) -> None:
        ruta = page.route

        rutas = {
            "/login": lambda: login_page.view(page, state),
            "/register": lambda: register_page.view(page, state),
            "/onboarding/birthdate": lambda: birthdate_page.view(page, state),
            "/onboarding/tags": lambda: tags_page.view(page, state, "/onboarding/avatar"),
            "/onboarding/avatar": lambda: avatar_page.view(page, state, "/profile"),
            "/profile/tags": lambda: tags_page.view(page, state, "/profile"),
            "/profile/avatar": lambda: avatar_page.view(page, state, "/profile"),
            "/profile": lambda: profile_page.view(page, state),
            "/settings": lambda: settings_page.view(page, state),
            "/settings/account": lambda: account_page.view(page, state),
            "/settings/account/avatar": lambda: avatar_page.view(
                page, state, "/settings/account"
            ),
            "/search": lambda: search_page.view(page, state),
            "/post/new": lambda: post_editor_page.view(page, state),
        }

        publicas = {"/login", "/register"}
        es_publica = (
            ruta in publicas
            or ruta.startswith("/user/")
            or (ruta.startswith("/post/") and ruta != "/post/new")
        )
        if not es_publica and not state.is_authenticated:
            await page.push_route("/login")
            return

        if ruta.startswith("/post/") and ruta != "/post/new":
            partes = ruta.strip("/").split("/")
            if len(partes) >= 2 and partes[1].isdigit():
                post_id = int(partes[1])
                seccion = partes[2] if len(partes) > 2 else ""

                if seccion == "comments":
                    vista = await comments_page.view(page, state, post_id)
                elif seccion == "settings":
                    vista = await post_settings_page.view(page, state, post_id)
                elif seccion == "edit":
                    vista = await post_editor_page.view(page, state, post_id)
                else:
                    vista = await post_page.view(page, state, post_id)

                page.views.clear()
                page.views.append(vista)
                page.update()
                return

        if ruta.startswith("/user/"):
            username = ruta.removeprefix("/user/")
            if username:
                vista = await public_profile_page.view(page, state, username)
                page.views.clear()
                page.views.append(vista)
                page.update()
                return

        constructor = rutas.get(ruta)
        if constructor is None:
            await page.push_route("/login")
            return

        vista = await constructor()

        page.views.clear()
        page.views.append(vista)
        page.update()

    return route_change
