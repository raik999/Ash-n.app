from __future__ import annotations
from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from entities.base import Base, TimestampMixin

class PostLike(Base, TimestampMixin):
    __tablename__ = "post_likes"

    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        Index("ix_post_likes_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<PostLike post={self.post_id} user={self.user_id}>"
