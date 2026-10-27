from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.user import User

MAX_COMMENT_LENGTH = 800

class PostComment(Base, TimestampMixin):
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(String(MAX_COMMENT_LENGTH), nullable=False)

    author: Mapped[User] = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_post_comments_post", "post_id", "id"),
    )

    def __repr__(self) -> str:
        return f"<PostComment #{self.id} post={self.post_id} user={self.user_id}>"
