from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from entities.chat import Chat
from entities.message import Message
from entities.user import User
from middleware.error_middleware import ForbiddenError, NotFoundError, ValidationError
from services import user_service

def get_chat_or_404(db: Session, chat_id: int) -> Chat:
    chat = db.get(Chat, chat_id)
    if chat is None:
        raise NotFoundError("Ese chat no existe")
    return chat

def _exigir_participante(chat: Chat, user: User) -> Chat:
    if not chat.participa(user.id):
        raise NotFoundError("Ese chat no existe")
    return chat

def find_chat(db: Session, un_usuario: int, otro_usuario: int) -> Chat | None:
    a, b = Chat.ordenar(un_usuario, otro_usuario)

    return db.scalar(select(Chat).where(Chat.user_a_id == a, Chat.user_b_id == b))

def get_or_create_chat(db: Session, user: User, username: str) -> tuple[Chat, bool]:
    otro = user_service.get_user_by_username(db, username)

    if otro is None:
        raise NotFoundError("Ese usuario no existe")

    if otro.id == user.id:
        raise ValidationError("No puedes abrir un chat contigo mismo")

    existente = find_chat(db, user.id, otro.id)
    if existente is not None:
        return existente, False

    a, b = Chat.ordenar(user.id, otro.id)
    chat = Chat(user_a_id=a, user_b_id=b)
    db.add(chat)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        ya_existe = find_chat(db, user.id, otro.id)
        if ya_existe is None:
            raise
        return ya_existe, False

    db.refresh(chat)
    return chat, True

def list_chats(db: Session, user: User) -> list[tuple[Chat, Message | None, int]]:
    chats = list(
        db.scalars(
            select(Chat).where(
                (Chat.user_a_id == user.id) | (Chat.user_b_id == user.id)
            )
        ).all()
    )

    if not chats:
        return []

    ids = [chat.id for chat in chats]

    ultimos_ids = db.scalars(
        select(func.max(Message.id))
        .where(Message.chat_id.in_(ids))
        .group_by(Message.chat_id)
    ).all()

    ultimos: dict[int, Message] = {}
    if ultimos_ids:
        for mensaje in db.scalars(
            select(Message).where(Message.id.in_(list(ultimos_ids)))
        ).all():
            ultimos[mensaje.chat_id] = mensaje

    sin_leer: dict[int, int] = {}
    for chat in chats:
        marca = chat.leido_de(user.id)

        condiciones = [Message.chat_id == chat.id, Message.user_id != user.id]
        if marca is not None:
            condiciones.append(Message.created_at > marca)

        sin_leer[chat.id] = (
            db.scalar(select(func.count()).select_from(Message).where(*condiciones)) or 0
        )

    def cuando(chat: Chat) -> datetime:
        ultimo = ultimos.get(chat.id)
        if ultimo is not None and ultimo.created_at is not None:
            return ultimo.created_at
        return chat.created_at

    chats.sort(key=cuando, reverse=True)

    return [(chat, ultimos.get(chat.id), sin_leer.get(chat.id, 0)) for chat in chats]

def count_unread_chats(db: Session, user: User) -> int:
    return sum(1 for _, _, no_leidos in list_chats(db, user) if no_leidos > 0)

MAX_MENSAJES = 200

def get_chat(db: Session, user: User, chat_id: int) -> Chat:
    return _exigir_participante(get_chat_or_404(db, chat_id), user)

def list_messages(db: Session, user: User, chat_id: int) -> list[Message]:
    chat = get_chat(db, user, chat_id)

    recientes = list(
        db.scalars(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(Message.id.desc())
            .limit(MAX_MENSAJES)
        ).all()
    )

    recientes.reverse()
    return recientes

def mark_read(db: Session, user: User, chat_id: int) -> Chat:
    chat = get_chat(db, user, chat_id)

    chat.marcar_leido(user.id, datetime.now(timezone.utc))
    db.commit()
    db.refresh(chat)

    return chat

def send_message(db: Session, user: User, chat_id: int, text: str) -> Message:
    chat = get_chat(db, user, chat_id)

    mensaje = Message(chat_id=chat.id, user_id=user.id, text=text)
    db.add(mensaje)

    chat.marcar_leido(user.id, datetime.now(timezone.utc))

    db.commit()
    db.refresh(mensaje)

    return mensaje

def delete_chat(db: Session, user: User, chat_id: int) -> list[int]:
    chat = get_chat(db, user, chat_id)

    participantes = [chat.user_a_id, chat.user_b_id]

    db.delete(chat)
    db.commit()

    return participantes

def exigir_puede_borrar(chat: Chat, user: User) -> None:
    if not chat.participa(user.id):
        raise ForbiddenError("No puedes eliminar un chat del que no participas")
