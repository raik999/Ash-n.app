from __future__ import annotations

import asyncio
import logging

from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("ashun")

EVENTO_MENSAJE = "mensaje"
EVENTO_CHAT_NUEVO = "chat_nuevo"
EVENTO_CHAT_ELIMINADO = "chat_eliminado"
EVENTO_NOTIFICACION = "notificacion"

class GestorDeConexiones:
    def __init__(self) -> None:
        self._conexiones: dict[int, set[WebSocket]] = {}

        self._candado = asyncio.Lock()

    async def conectar(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()

        async with self._candado:
            self._conexiones.setdefault(user_id, set()).add(websocket)

        logger.info(
            "WebSocket conectado: usuario %s (%d conexiones suyas)",
            user_id,
            len(self._conexiones.get(user_id, ())),
        )

    async def desconectar(self, user_id: int, websocket: WebSocket) -> None:
        async with self._candado:
            sockets = self._conexiones.get(user_id)
            if sockets is None:
                return

            sockets.discard(websocket)
            if not sockets:
                self._conexiones.pop(user_id, None)

        logger.info("WebSocket desconectado: usuario %s", user_id)

    def esta_conectado(self, user_id: int) -> bool:
        return bool(self._conexiones.get(user_id))

    async def enviar_a(self, user_id: int, tipo: str, datos: Any) -> None:
        async with self._candado:
            sockets = set(self._conexiones.get(user_id, ()))

        if not sockets:
            return

        sobre = {"tipo": tipo, "datos": datos}
        caidas: list[WebSocket] = []

        for socket in sockets:
            try:
                await socket.send_json(sobre)
            except Exception:
                caidas.append(socket)

        for socket in caidas:
            await self.desconectar(user_id, socket)

    async def enviar_a_varios(
        self, user_ids: list[int], tipo: str, datos: Any
    ) -> None:
        for user_id in user_ids:
            await self.enviar_a(user_id, tipo, datos)

gestor = GestorDeConexiones()
