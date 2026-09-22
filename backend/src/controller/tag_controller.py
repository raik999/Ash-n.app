from __future__ import annotations
from sqlalchemy.orm import Session
from services import tag_service
from validations.user_validation import TagResponse


def list_tags(db: Session) -> list[TagResponse]:
    tags = tag_service.list_tags(db)
    return [TagResponse.model_validate(tag) for tag in tags]


def create_tag(db: Session, name: str, color: str) -> TagResponse:
    tag = tag_service.create_tag(db, name=name, color=color)
    return TagResponse.model_validate(tag)
