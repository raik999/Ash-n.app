from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from controller import notification_controller
from entities.user import User
from middleware.auth_middleware import get_current_user
from validations.auth_validation import MessageResponse
from validations.chat_validation import NotificationsResponse

router = APIRouter(prefix="/api/notifications", tags=["Notificaciones"])

@router.get(
    "",
    response_model=NotificationsResponse,
    summary="Reacciones a mis publicaciones",
)
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationsResponse:
    return notification_controller.list_notifications(db, current_user)

@router.post(
    "/seen",
    response_model=MessageResponse,
    summary="Marcar las notificaciones como vistas",
)
def mark_seen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return notification_controller.mark_seen(db, current_user)
