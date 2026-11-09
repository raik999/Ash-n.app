from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from entities.chat import MAX_MESSAGE_LENGTH
from validations.user_validation import UserSummaryResponse

class MessageResponse(BaseModel):
    id: int
    text: str
    created_at: datetime | None = None

    author: UserSummaryResponse

    mine: bool = False

    model_config = ConfigDict(from_attributes=True)

class ChatSummaryResponse(BaseModel):
    id: int

    other: UserSummaryResponse

    last_message: str | None = None
    last_message_at: datetime | None = None

    unread: int = 0

    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    id: int
    other: UserSummaryResponse
    messages: list[MessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class NotificationResponse(BaseModel):
    id: str

    kind: str

    user: UserSummaryResponse

    post_id: int
    post_preview: str | None = None

    created_at: datetime | None = None

    is_new: bool = False

class NotificationsResponse(BaseModel):
    items: list[NotificationResponse] = Field(default_factory=list)
    unseen: int = 0

class UnreadResponse(BaseModel):
    chats: int = 0
    notifications: int = 0

class CreateChatRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)

    @field_validator("username")
    @classmethod
    def normalizar(cls, value: str) -> str:
        return value.strip().lower()

class CreateMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)

    @field_validator("text")
    @classmethod
    def limpiar(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El mensaje no puede estar vacio")
        return value
