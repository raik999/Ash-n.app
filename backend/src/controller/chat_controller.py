from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from entities.chat import Chat
from entities.message import Message
from entities.user import User
from services import chat_service, realtime_service
from validations.auth_validation import MessageResponse as TextoResponse
from validations.chat_validation import (
    ChatResponse,
    ChatSummaryResponse,
    MessageResponse,
    UnreadResponse,
)
from validations.user_validation import UserSummaryResponse

def _resumen(chat: Chat, ultimo: Message | None, no_leidos: int, yo: User) -> ChatSummaryResponse:
    return ChatSummaryResponse(
        id=chat.id,
        other=UserSummaryResponse.model_validate(chat.otro(yo.id)),
        last_message=ultimo.text if ultimo is not None else None,
        last_message_at=ultimo.created_at if ultimo is not None else None,
        unread=no_leidos,
    )

def _mensaje(mensaje: Message, yo: User) -> MessageResponse:
    return MessageResponse(
        id=mensaje.id,
        text=mensaje.text,
        created_at=mensaje.created_at,
        author=UserSummaryResponse.model_validate(mensaje.author),
        mine=mensaje.user_id == yo.id,
    )

def _mensaje_para(mensaje: Message, destinatario_id: int) -> dict[str, Any]:
    return {
        "id": mensaje.id,
        "text": mensaje.text,
        "created_at": mensaje.created_at.isoformat() if mensaje.created_at else None,
        "author": UserSummaryResponse.model_validate(mensaje.author).model_dump(
            mode="json"
        ),
        "mine": mensaje.user_id == destinatario_id,
        "chat_id": mensaje.chat_id,
    }

def list_chats(db: Session, user: User) -> list[ChatSummaryResponse]:
    return [
        _resumen(chat, ultimo, no_leidos, user)
        for chat, ultimo, no_leidos in chat_service.list_chats(db, user)
    ]

def create_chat(
    db: Session, user: User, username: str
) -> tuple[ChatSummaryResponse, list[tuple[int, str, Any]]]:
    chat, es_nuevo = chat_service.get_or_create_chat(db, user, username)

    respuesta = _resumen(chat, None, 0, user)

    avisos: list[tuple[int, str, Any]] = []

    if es_nuevo:
        otro = chat.otro(user.id)
        avisos.append(
            (
                otro.id,
                realtime_service.EVENTO_CHAT_NUEVO,
                {
                    "id": chat.id,
                    "other": UserSummaryResponse.model_validate(user).model_dump(
                        mode="json"
                    ),
                },
            )
        )

    return respuesta, avisos

def get_chat(db: Session, user: User, chat_id: int) -> ChatResponse:
    mensajes = chat_service.list_messages(db, user, chat_id)
    chat = chat_service.mark_read(db, user, chat_id)

    return ChatResponse(
        id=chat.id,
        other=UserSummaryResponse.model_validate(chat.otro(user.id)),
        messages=[_mensaje(m, user) for m in mensajes],
    )

def send_message(
    db: Session, user: User, chat_id: int, text: str
) -> tuple[MessageResponse, list[tuple[int, str, Any]]]:
    mensaje = chat_service.send_message(db, user, chat_id, text)

    chat = chat_service.get_chat(db, user, chat_id)
    otro_id = chat.otro_id(user.id)

    avisos = [
        (
            otro_id,
            realtime_service.EVENTO_MENSAJE,
            _mensaje_para(mensaje, otro_id),
        )
    ]

    return _mensaje(mensaje, user), avisos

def delete_chat(
    db: Session, user: User, chat_id: int
) -> tuple[TextoResponse, list[tuple[int, str, Any]]]:
    chat = chat_service.get_chat(db, user, chat_id)
    chat_service.exigir_puede_borrar(chat, user)

    participantes = chat_service.delete_chat(db, user, chat_id)

    avisos = [
        (
            participante,
            realtime_service.EVENTO_CHAT_ELIMINADO,
            {"id": chat_id},
        )
        for participante in participantes
    ]

    return TextoResponse(detail="Chat eliminado"), avisos

def mark_read(db: Session, user: User, chat_id: int) -> TextoResponse:
    chat_service.mark_read(db, user, chat_id)
    return TextoResponse(detail="Chat marcado como leido")

def unread_counts(db: Session, user: User) -> UnreadResponse:
    from services import notification_service

    return UnreadResponse(
        chats=chat_service.count_unread_chats(db, user),
        notifications=notification_service.count_unseen(db, user),
    )
