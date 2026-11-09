from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from config.database import SessionLocal, get_db
from controller import chat_controller
from entities.user import User
from middleware.auth_middleware import get_current_user
from services import realtime_service, user_service
from services.realtime_service import gestor
from services.security_service import decode_access_token
from validations.auth_validation import MessageResponse
from validations.chat_validation import (
    ChatResponse,
    ChatSummaryResponse,
    CreateChatRequest,
    CreateMessageRequest,
    MessageResponse as MensajeResponse,
    UnreadResponse,
)

router = APIRouter(prefix="/api/chats", tags=["Chat"])

@router.get("", response_model=list[ChatSummaryResponse], summary="Mis chats")
def list_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSummaryResponse]:
    return chat_controller.list_chats(db, current_user)

@router.get(
    "/unread",
    response_model=UnreadResponse,
    summary="Cuantos chats y notificaciones sin ver",
)
def unread_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadResponse:
    return chat_controller.unread_counts(db, current_user)

@router.post(
    "",
    response_model=ChatSummaryResponse,
    status_code=201,
    summary="Abrir un chat con alguien",
)
async def create_chat(
    payload: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSummaryResponse:
    respuesta, avisos = await run_in_threadpool(
        chat_controller.create_chat, db, current_user, payload.username
    )

    for a_quien, tipo, datos in avisos:
        await gestor.enviar_a(a_quien, tipo, datos)

    return respuesta

@router.get("/{chat_id}", response_model=ChatResponse, summary="Abrir un chat")
def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    return chat_controller.get_chat(db, current_user, chat_id)

@router.post(
    "/{chat_id}/messages",
    response_model=MensajeResponse,
    status_code=201,
    summary="Enviar un mensaje",
)
async def send_message(
    chat_id: int,
    payload: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MensajeResponse:
    respuesta, avisos = await run_in_threadpool(
        chat_controller.send_message, db, current_user, chat_id, payload.text
    )

    for a_quien, tipo, datos in avisos:
        await gestor.enviar_a(a_quien, tipo, datos)

    return respuesta

@router.post(
    "/{chat_id}/read",
    response_model=MessageResponse,
    summary="Marcar el chat como leido",
)
def mark_read(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return chat_controller.mark_read(db, current_user, chat_id)

@router.delete(
    "/{chat_id}",
    response_model=MessageResponse,
    summary="Eliminar el chat (para los dos)",
)
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    respuesta, avisos = await run_in_threadpool(
        chat_controller.delete_chat, db, current_user, chat_id
    )

    for a_quien, tipo, datos in avisos:
        await gestor.enviar_a(a_quien, tipo, datos)

    return respuesta

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, token: str = "") -> None:
    if not token:
        await websocket.close(code=1008, reason="Falta el token")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=1008, reason="Token invalido")
        return

    db = SessionLocal()
    try:
        usuario = user_service.get_user_by_id(db, user_id)
    finally:
        db.close()

    if usuario is None:
        await websocket.close(code=1008, reason="El usuario ya no existe")
        return

    await gestor.conectar(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await gestor.desconectar(user_id, websocket)
