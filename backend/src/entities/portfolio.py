from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.post import Post
    from entities.user import User

MAX_TITULO = 60
MAX_DESCRIPCION = 300

COLORES = (
    "#2E9E27",
    "#F0743C",
    "#BE2EDD",
    "#4D7CFE",
    "#F03C3C",
    "#17B8C4",
    "#E8A317",
    "#E0457B",
)

COLOR_POR_DEFECTO = COLORES[3]

portfolio_posts = Table(
    "portfolio_posts",
    Base.metadata,
    Column(
        "portfolio_id",
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "post_id",
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_portfolio_posts_post", "post_id"),
)

class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(MAX_TITULO), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    color: Mapped[str] = mapped_column(
        String(9), nullable=False, default=COLOR_POR_DEFECTO,
        server_default=COLOR_POR_DEFECTO,
    )

    is_private: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    owner: Mapped[User] = relationship(lazy="joined")

    posts: Mapped[list[Post]] = relationship(
        secondary=portfolio_posts,
        lazy="selectin",
        order_by="Post.id.desc()",
    )

    def __repr__(self) -> str:
        return f"<Portfolio #{self.id} '{self.title}' de user#{self.user_id}>"
