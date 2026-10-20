from __future__ import annotations
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from entities.search_history import MAX_HISTORY, SearchHistory
from entities.user import User


def search_users(db: Session, query: str, limit: int = 20) -> list[User]:
    query = query.strip().lower()

    if not query:
        return []

    statement = (
        select(User)
        .where(User.username.startswith(query, autoescape=True))
        .order_by(User.username)
        .limit(limit)
    )
    return list(db.execute(statement).scalars().all())


def list_history(db: Session, user_id: int) -> list[SearchHistory]:
    statement = (
        select(SearchHistory)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.id.desc())
        .limit(MAX_HISTORY)
    )
    return list(db.execute(statement).scalars().all())


def add_history(db: Session, user_id: int, kind: str, value: str) -> list[SearchHistory]:
    value = value.strip()
    if not value:
        return list_history(db, user_id)

    db.execute(
        delete(SearchHistory).where(
            SearchHistory.user_id == user_id,
            SearchHistory.kind == kind,
            SearchHistory.value == value,
        )
    )

    db.add(SearchHistory(user_id=user_id, kind=kind, value=value))

    db.flush()

    keep_ids = (
        select(SearchHistory.id)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.id.desc())
        .limit(MAX_HISTORY)
        .scalar_subquery()
    )

    db.execute(
        delete(SearchHistory).where(
            SearchHistory.user_id == user_id,
            SearchHistory.id.not_in(keep_ids),
        )
    )

    db.commit()
    return list_history(db, user_id)


def clear_history(db: Session, user_id: int) -> int:
    result = db.execute(delete(SearchHistory).where(SearchHistory.user_id == user_id))
    db.commit()
    return result.rowcount or 0