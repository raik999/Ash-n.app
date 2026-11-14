from __future__ import annotations

import enum
import math

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Date, DateTime, Enum, Integer, String, Text
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

    notifications_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    banned_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    banned_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

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

    @property
    def esta_sancionado(self) -> bool:
        if self.banned_until is None:
            return False

        hasta = self.banned_until
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)

        return hasta > datetime.now(timezone.utc)

    @property
    def dias_de_sancion_restantes(self) -> int:
        if not self.esta_sancionado:
            return 0

        hasta = self.banned_until
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)

        faltan = hasta - datetime.now(timezone.utc)
        return max(1, math.ceil(faltan.total_seconds() / 86400))

    @property
    def mensaje_de_sancion(self) -> str | None:
        if not self.esta_sancionado:
            return None

        dias = self.dias_de_sancion_restantes
        plural = "dia" if dias == 1 else "dias"

        texto = f"Tu cuenta esta suspendida. Faltan {dias} {plural}."
        if self.banned_reason:
            texto += f" Motivo: {self.banned_reason}"

        return texto

    def __repr__(self) -> str:
        return f"<User #{self.id} @{self.username}>"
