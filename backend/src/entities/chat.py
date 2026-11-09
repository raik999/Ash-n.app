from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.message import Message
    from entities.user import User

MAX_MESSAGE_LENGTH = 1000

class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_a_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_b_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    leido_a: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    leido_b: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user_a: Mapped[User] = relationship(foreign_keys=[user_a_id], lazy="joined")
    user_b: Mapped[User] = relationship(foreign_keys=[user_b_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_chats_pareja"),
        CheckConstraint("user_a_id < user_b_id", name="ck_chats_orden"),
        Index("ix_chats_user_b", "user_b_id"),
    )

    @staticmethod
    def ordenar(un_usuario: int, otro_usuario: int) -> tuple[int, int]:
        if un_usuario < otro_usuario:
            return un_usuario, otro_usuario
        return otro_usuario, un_usuario

    def participa(self, user_id: int) -> bool:
        return user_id in (self.user_a_id, self.user_b_id)

    def otro_id(self, user_id: int) -> int:
        return self.user_b_id if user_id == self.user_a_id else self.user_a_id

    def otro(self, user_id: int) -> User:
        return self.user_b if user_id == self.user_a_id else self.user_a

    def leido_de(self, user_id: int) -> datetime | None:
        return self.leido_a if user_id == self.user_a_id else self.leido_b

    def marcar_leido(self, user_id: int, cuando: datetime) -> None:
        if user_id == self.user_a_id:
            self.leido_a = cuando
        else:
            self.leido_b = cuando

    def __repr__(self) -> str:
        return f"<Chat #{self.id} {self.user_a_id}<->{self.user_b_id}>"
