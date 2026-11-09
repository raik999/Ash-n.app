from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin
from entities.chat import MAX_MESSAGE_LENGTH

if TYPE_CHECKING:
    from entities.chat import Chat
    from entities.user import User

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(String(MAX_MESSAGE_LENGTH), nullable=False)

    chat: Mapped[Chat] = relationship(back_populates="messages")

    author: Mapped[User] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_messages_chat_recent", "chat_id", id.desc()),
    )

    def __repr__(self) -> str:
        return f"<Message #{self.id} chat={self.chat_id} de={self.user_id}>"
