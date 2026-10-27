from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from entities.base import Base, TimestampMixin

if TYPE_CHECKING:
    from entities.post import Post

KIND_IMAGE = "image"
KIND_VIDEO = "video"
KIND_AUDIO = "audio"

ALL_KINDS = (KIND_IMAGE, KIND_VIDEO, KIND_AUDIO)

class PostFile(Base, TimestampMixin):
    __tablename__ = "post_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    kind: Mapped[str] = mapped_column(String(10), nullable=False)

    url: Mapped[str] = mapped_column(String(255), nullable=False)

    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    post: Mapped[Post] = relationship("Post", back_populates="files")

    __table_args__ = (
        Index("ix_post_files_post_position", "post_id", "position"),
    )

    def __repr__(self) -> str:
        return f"<PostFile #{self.id} post={self.post_id} {self.kind}>"
