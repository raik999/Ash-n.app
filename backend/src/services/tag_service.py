from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from entities.tag import Tag
from middleware.error_middleware import ConflictError, NotFoundError


def list_tags(db: Session) -> list[Tag]:
    statement = select(Tag).order_by(Tag.name)
    return list(db.execute(statement).scalars().all())


def get_tag_by_id(db: Session, tag_id: int) -> Tag:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise NotFoundError(f"No existe la especialidad con id {tag_id}")
    return tag


def create_tag(db: Session, name: str, color: str) -> Tag:
    name = name.strip().lstrip("#")

    existing = db.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"La especialidad '{name}' ya existe", field="name")

    tag = Tag(name=name, color=color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
