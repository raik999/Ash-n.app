from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin
from entities.tag import user_tags

if TYPE_CHECKING:
    from entities.tag import Tag


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(80), nullable=False)

    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )

    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)

    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tags: Mapped[list[Tag]] = relationship(
        secondary=user_tags,
        back_populates="users",
        lazy="selectin",
        order_by="Tag.id",
    )

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User #{self.id} @{self.username}>"
