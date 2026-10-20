from __future__ import annotations
from sqlalchemy.orm import Session
from entities.user import User
from services import search_service
from validations.auth_validation import MessageResponse
from validations.search_validation import AddSearchRequest, SearchHistoryEntry
from validations.user_validation import UserSummaryResponse


def search_users(db: Session, query: str, limit: int = 20) -> list[UserSummaryResponse]:
    users = search_service.search_users(db, query, limit)
    return [UserSummaryResponse.model_validate(user) for user in users]


def list_my_searches(db: Session, current_user: User) -> list[SearchHistoryEntry]:
    entries = search_service.list_history(db, current_user.id)
    return [SearchHistoryEntry.model_validate(entry) for entry in entries]


def add_my_search(
    db: Session, current_user: User, payload: AddSearchRequest
) -> list[SearchHistoryEntry]:
    entries = search_service.add_history(
        db,
        user_id=current_user.id,
        kind=payload.kind,
        value=payload.value,
    )
    return [SearchHistoryEntry.model_validate(entry) for entry in entries]


def clear_my_searches(db: Session, current_user: User) -> MessageResponse:
    deleted = search_service.clear_history(db, current_user.id)
    return MessageResponse(detail=f"Se eliminaron {deleted} busquedas")
