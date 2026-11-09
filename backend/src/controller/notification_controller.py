from __future__ import annotations

from sqlalchemy.orm import Session

from entities.user import User
from services import notification_service
from validations.auth_validation import MessageResponse as TextoResponse
from validations.chat_validation import NotificationResponse, NotificationsResponse
from validations.user_validation import UserSummaryResponse

def list_notifications(db: Session, user: User) -> NotificationsResponse:
    elementos, nuevas = notification_service.list_notifications(db, user)

    return NotificationsResponse(
        items=[
            NotificationResponse(
                id=item["id"],
                kind=item["kind"],
                user=UserSummaryResponse.model_validate(item["user"]),
                post_id=item["post_id"],
                post_preview=item["post_preview"],
                created_at=item["created_at"],
                is_new=item["is_new"],
            )
            for item in elementos
        ],
        unseen=nuevas,
    )

def mark_seen(db: Session, user: User) -> TextoResponse:
    notification_service.mark_seen(db, user)
    return TextoResponse(detail="Notificaciones marcadas como vistas")
