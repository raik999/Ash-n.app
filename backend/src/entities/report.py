from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.post import Post
    from entities.user import User

TIPO_PUBLICACION = "post"
TIPO_USUARIO = "user"

MAX_MOTIVO = 300

class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    kind: Mapped[str] = mapped_column(String(10), nullable=False)

    post_id: Mapped[int | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)

    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id], lazy="joined")
    target_user: Mapped[User | None] = relationship(
        foreign_keys=[target_user_id], lazy="joined"
    )
    post: Mapped[Post | None] = relationship(lazy="joined")

    __table_args__ = (
        CheckConstraint(
            "(post_id IS NOT NULL AND target_user_id IS NULL)"
            " OR (post_id IS NULL AND target_user_id IS NOT NULL)",
            name="ck_reports_un_objetivo",
        ),
        Index(
            "uq_reports_publicacion",
            "reporter_id",
            "post_id",
            unique=True,
            postgresql_where=text("post_id IS NOT NULL"),
        ),
        Index(
            "uq_reports_usuario",
            "reporter_id",
            "target_user_id",
            unique=True,
            postgresql_where=text("target_user_id IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        objetivo = f"post#{self.post_id}" if self.post_id else f"user#{self.target_user_id}"
        return f"<Report #{self.id} de user#{self.reporter_id} sobre {objetivo}>"
