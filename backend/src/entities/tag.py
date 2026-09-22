from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.user import User


user_tags = Table(
    "user_tags",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)

    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#7C7C7C")

    users: Mapped[list[User]] = relationship(
        secondary=user_tags,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag #{self.id} {self.name}>"
