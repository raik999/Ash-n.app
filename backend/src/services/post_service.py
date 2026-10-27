from __future__ import annotations
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from entities.post import MAX_FILES_PER_POST, MIN_DESCRIPTION_LENGTH, Post
from entities.post_comment import PostComment
from entities.post_file import PostFile
from entities.post_like import PostLike
from entities.tag import Tag
from entities.user import User
from middleware.error_middleware import (
    AppError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from services import storage_service

def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise NotFoundError("Esa publicacion no existe")
    return post

def _require_author(post: Post, user: User) -> None:
    if post.user_id != user.id:
        raise ForbiddenError("Solo el autor puede modificar esta publicacion")

def _resolve_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all())
    if len(tags) != len(set(tag_ids)):
        encontrados = {t.id for t in tags}
        faltan = [i for i in tag_ids if i not in encontrados]
        raise NotFoundError(f"No existe la especialidad con id {faltan[0]}")
    return tags

def counts_for(db: Session, post_ids: list[int]) -> dict[int, tuple[int, int]]:
    if not post_ids:
        return {}

    likes = dict(
        db.execute(
            select(PostLike.post_id, func.count())
            .where(PostLike.post_id.in_(post_ids))
            .group_by(PostLike.post_id)
        ).all()
    )
    comentarios = dict(
        db.execute(
            select(PostComment.post_id, func.count())
            .where(PostComment.post_id.in_(post_ids))
            .group_by(PostComment.post_id)
        ).all()
    )
    return {pid: (likes.get(pid, 0), comentarios.get(pid, 0)) for pid in post_ids}

def liked_by(db: Session, post_ids: list[int], user_id: int | None) -> set[int]:
    if not post_ids or user_id is None:
        return set()
    filas = db.scalars(
        select(PostLike.post_id).where(
            PostLike.post_id.in_(post_ids), PostLike.user_id == user_id
        )
    ).all()
    return set(filas)

def create_post(
    db: Session,
    user: User,
    title: str | None,
    description: str | None,
    tag_ids: list[int] | None,
) -> Post:
    post = Post(user_id=user.id, title=title, description=description)
    if tag_ids:
        post.tags = _resolve_tags(db, tag_ids)

    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def update_post(
    db: Session,
    user: User,
    post_id: int,
    title: str | None,
    description: str | None,
    tag_ids: list[int] | None,
    touched: set[str],
) -> Post:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)

    if "title" in touched:
        post.title = title
    if "description" in touched:
        post.description = description
    if "tag_ids" in touched:
        post.tags = _resolve_tags(db, tag_ids or [])

    if post.published:
        _assert_has_content(post)

    db.commit()
    db.refresh(post)
    return post

def delete_post(db: Session, user: User, post_id: int) -> None:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)

    for archivo in post.files:
        storage_service.delete_post_file(archivo.url)

    db.delete(post)
    db.commit()

def _assert_has_content(post: Post) -> None:
    if post.files:
        return

    descripcion = (post.description or "").strip()
    if len(descripcion) >= MIN_DESCRIPTION_LENGTH:
        return

    raise ValidationError(
        f"Una publicacion sin archivos necesita una descripcion de al menos "
        f"{MIN_DESCRIPTION_LENGTH} caracteres",
        field="description",
    )

def publish_post(db: Session, user: User, post_id: int) -> Post:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)

    _assert_has_content(post)

    post.published = True
    db.commit()
    db.refresh(post)
    return post

def add_file(db: Session, user: User, post_id: int, content: bytes) -> PostFile:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)

    if len(post.files) >= MAX_FILES_PER_POST:
        raise ValidationError(
            f"Una publicacion puede tener como maximo {MAX_FILES_PER_POST} archivos",
            field="file",
        )

    url, kind = storage_service.save_post_file(post_id, content)

    archivo = PostFile(post_id=post.id, kind=kind, url=url, position=len(post.files))
    db.add(archivo)
    db.commit()
    db.refresh(archivo)
    return archivo

def remove_file(db: Session, user: User, post_id: int, file_id: int) -> None:
    post = _get_post_or_404(db, post_id)
    _require_author(post, user)

    archivo = db.get(PostFile, file_id)
    if archivo is None or archivo.post_id != post.id:
        raise NotFoundError("Ese archivo no existe en esta publicacion")

    storage_service.delete_post_file(archivo.url)
    db.delete(archivo)
    db.flush()

    restantes = db.scalars(
        select(PostFile).where(PostFile.post_id == post.id).order_by(PostFile.position)
    ).all()
    for indice, item in enumerate(restantes):
        item.position = indice

    db.commit()

def get_post(db: Session, post_id: int, viewer: User | None) -> Post:
    post = _get_post_or_404(db, post_id)

    if not post.published and (viewer is None or viewer.id != post.user_id):
        raise NotFoundError("Esa publicacion no existe")

    return post

def list_user_posts(db: Session, author: User, viewer: User | None) -> list[Post]:
    statement = select(Post).where(Post.user_id == author.id)

    if viewer is None or viewer.id != author.id:
        statement = statement.where(Post.published.is_(True))

    statement = statement.order_by(Post.id.desc())
    return list(db.scalars(statement).all())

def add_like(db: Session, user: User, post_id: int) -> int:
    post = get_post(db, post_id, user)

    db.add(PostLike(post_id=post.id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    return count_likes(db, post.id)

def remove_like(db: Session, user: User, post_id: int) -> int:
    post = get_post(db, post_id, user)

    db.execute(
        delete(PostLike).where(
            PostLike.post_id == post.id, PostLike.user_id == user.id
        )
    )
    db.commit()
    return count_likes(db, post.id)

def count_likes(db: Session, post_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
    ) or 0

def has_like(db: Session, post_id: int, user_id: int | None) -> bool:
    if user_id is None:
        return False
    return db.get(PostLike, (post_id, user_id)) is not None

def list_comments(db: Session, post_id: int, viewer: User | None) -> list[PostComment]:
    get_post(db, post_id, viewer)

    return list(
        db.scalars(
            select(PostComment)
            .where(PostComment.post_id == post_id)
            .order_by(PostComment.id)
        ).all()
    )

def add_comment(db: Session, user: User, post_id: int, text: str) -> PostComment:
    post = get_post(db, post_id, user)

    comentario = PostComment(post_id=post.id, user_id=user.id, text=text)
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario

def can_delete_comment(comment: PostComment, post: Post, user: User | None) -> bool:
    if user is None:
        return False
    return comment.user_id == user.id or post.user_id == user.id

def delete_comment(db: Session, user: User, post_id: int, comment_id: int) -> None:
    post = get_post(db, post_id, user)

    comentario = db.get(PostComment, comment_id)
    if comentario is None or comentario.post_id != post.id:
        raise NotFoundError("Ese comentario no existe en esta publicacion")

    if not can_delete_comment(comentario, post, user):
        raise ForbiddenError("No puedes eliminar este comentario")

    db.delete(comentario)
    db.commit()
