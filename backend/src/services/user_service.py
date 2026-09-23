from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from entities.tag import Tag
from entities.user import User, UserRole
from middleware.error_middleware import ConflictError, NotFoundError
from services.security_service import hash_password, verify_password
from validations.auth_validation import RegisterRequest
from validations.user_validation import UpdateProfileRequest


def get_user_by_id(db: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.execute(statement).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.execute(statement).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username.lower())
    return db.execute(statement).scalar_one_or_none()


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    identifier = identifier.strip().lower()
    statement = select(User).where(
        (User.email == identifier) | (User.username == identifier)
    )
    return db.execute(statement).scalar_one_or_none()


def create_user(db: Session, data: RegisterRequest) -> User:
    email = data.email.lower()
    username = data.username.lower()

    if get_user_by_email(db, email) is not None:
        raise ConflictError("Ese correo ya esta registrado", field="email")

    if get_user_by_username(db, username) is not None:
        raise ConflictError("Ese nombre de usuario ya esta ocupado", field="username")

    user = User(
        name=data.name.strip(),
        username=username,
        email=email,
        password_hash=hash_password(data.password),
        role=UserRole.USER,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_profile(db: Session, user: User, data: UpdateProfileRequest) -> User:
    provided = data.model_dump(exclude_unset=True)

    if "name" in provided and provided["name"] is not None:
        user.name = provided["name"].strip()

    if "username" in provided and provided["username"] is not None:
        new_username = provided["username"]

        if new_username != user.username:
            taken_by = get_user_by_username(db, new_username)
            if taken_by is not None:
                raise ConflictError(
                    "Ese nombre de usuario ya esta ocupado", field="username"
                )
            user.username = new_username

    if "bio" in provided:
        user.bio = provided["bio"]

    if "birthdate" in provided:
        user.birthdate = provided["birthdate"]

    if "tag_ids" in provided and provided["tag_ids"] is not None:
        user.tags = _resolve_tags(db, provided["tag_ids"])

    db.commit()
    db.refresh(user)
    return user


def _resolve_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []

    statement = select(Tag).where(Tag.id.in_(tag_ids))
    found = db.execute(statement).scalars().all()

    if len(found) != len(tag_ids):
        found_ids = {tag.id for tag in found}
        missing = [tid for tid in tag_ids if tid not in found_ids]
        raise NotFoundError(f"Estas especialidades no existen: {missing}", field="tag_ids")

    by_id = {tag.id: tag for tag in found}
    return [by_id[tid] for tid in tag_ids]


def set_avatar(db: Session, user: User, avatar_url: str) -> User:
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current: str, new: str) -> User:
    if not verify_password(current, user.password_hash):
        raise ConflictError("La contrasena actual no es correcta", field="current_password")

    user.password_hash = hash_password(new)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, identifier: str, password: str) -> User:
    user = get_user_by_identifier(db, identifier)

    if user is None:
        verify_password(password, "$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV0123")
        raise _invalid_credentials()

    if not verify_password(password, user.password_hash):
        raise _invalid_credentials()

    return user


def _invalid_credentials():
    from middleware.error_middleware import UnauthorizedError

    return UnauthorizedError("Usuario o contrasena incorrectos")
