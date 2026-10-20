from __future__ import annotations
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from entities.base import Base, TimestampMixin

MAX_HISTORY = 12
KIND_QUERY = "query"
KIND_USER = "user"


class SearchHistory(Base, TimestampMixin):
    __tablename__ = "search_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[str] = mapped_column(String(60), nullable=False)
    __table_args__ = (
        Index("ix_search_history_user_recent", "user_id", id.desc()),
    )

    def __repr__(self) -> str:
        return f"<SearchHistory #{self.id} user={self.user_id} {self.kind}:{self.value}>"
