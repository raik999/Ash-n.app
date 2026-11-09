from __future__ import annotations

import asyncio
import json

from typing import Any, Callable

import websockets

from config import api_base_url

EVENTO_MENSAJE = "mensaje"
EVENTO_CHAT_NUEVO = "chat_nuevo"
EVENTO_CHAT_ELIMINADO = "chat_eliminado"
EVENTO_NOTIFICACION = "notificacion"

CLAVE_GLOBAL = "global"

def _url_del_socket(token: str) -> str:
    base = api_base_url()

    if base.startswith("https://"):
        base = "wss://" + base[len("https://"):]
    elif base.startswith("http://"):
        base = "ws://" + base[len("http://"):]

    return f"{base}/api/chats/ws?token={token}"

class ConexionEnVivo:
    def __init__(self) -> None:
        self._token: str | None = None
        self._tarea: asyncio.Task | None = None
        self._conectado = False

        self._oyentes: dict[str, Callable[[str, Any], Any]] = {}

    def arrancar(self, token: str) -> None:
        self.detener()

        self._token = token
        self._tarea = asyncio.ensure_future(self._bucle())

    def detener(self) -> None:
        if self._tarea is not None:
            self._tarea.cancel()
            self._tarea = None

        self._token = None
        self._conectado = False

    @property
    def conectado(self) -> bool:
        return self._conectado

    def suscribir(self, clave: str, oyente: Callable[[str, Any], Any]) -> None:
        self._oyentes[clave] = oyente

    def desuscribir(self, clave: str) -> None:
        self._oyentes.pop(clave, None)

    def limpiar_pantalla(self) -> None:
        self._oyentes = {
            clave: oyente
            for clave, oyente in self._oyentes.items()
            if clave == CLAVE_GLOBAL
        }

    async def _repartir(self, tipo: str, datos: Any) -> None:
        for oyente in list(self._oyentes.values()):
            try:
                resultado = oyente(tipo, datos)
                if hasattr(resultado, "__await__"):
                    await resultado
            except Exception:
                pass

    async def _bucle(self) -> None:
        espera = 1.0

        while self._token:
            try:
                async with websockets.connect(_url_del_socket(self._token)) as socket:
                    self._conectado = True
                    espera = 1.0

                    async for crudo in socket:
                        try:
                            sobre = json.loads(crudo)
                        except (ValueError, TypeError):
                            continue

                        await self._repartir(
                            sobre.get("tipo", ""), sobre.get("datos")
                        )

            except asyncio.CancelledError:
                raise
            except Exception:
                pass

            self._conectado = False

            if not self._token:
                return

            await asyncio.sleep(espera)
            espera = min(espera * 2, 30.0)
