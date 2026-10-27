from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.post_file import PostFile
    from entities.tag import Tag
    from entities.user import User

MAX_FILES_PER_POST = 10

MIN_DESCRIPTION_LENGTH = 10

MAX_TAGS_PER_POST = 10

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column(
        "post_id",
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    author: Mapped[User] = relationship("User", lazy="joined")

    files: Mapped[list[PostFile]] = relationship(
        "PostFile",
        back_populates="post",
        lazy="selectin",
        order_by="PostFile.position",
        cascade="all, delete-orphan",
    )

    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary=post_tags,
        lazy="selectin",
        order_by="Tag.id",
    )

    __table_args__ = (
        Index("ix_posts_user_recent", "user_id", "published", id.desc()),
    )

    def __repr__(self) -> str:
        return f"<Post #{self.id} de user={self.user_id}>"
