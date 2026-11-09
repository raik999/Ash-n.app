from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from entities.post import Post
from entities.post_comment import PostComment
from entities.post_like import PostLike
from entities.user import User

MAX_NOTIFICACIONES = 50

TIPO_LIKE = "like"
TIPO_COMENTARIO = "comment"

def _vista_previa(post: Post) -> str | None:
    texto = (post.description or post.title or "").strip()
    if not texto:
        return None
    return texto[:60]

def _aware(momento: datetime | None) -> datetime | None:
    if momento is None:
        return None
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento

def list_notifications(db: Session, user: User) -> tuple[list[dict[str, Any]], int]:
    mis_posts = {
        post.id: post
        for post in db.scalars(select(Post).where(Post.user_id == user.id)).all()
    }

    if not mis_posts:
        return [], 0

    ids = list(mis_posts)
    visto = _aware(user.notifications_seen_at)

    elementos: list[dict[str, Any]] = []

    for like in db.scalars(
        select(PostLike).where(
            PostLike.post_id.in_(ids), PostLike.user_id != user.id
        )
    ).all():
        autor = db.get(User, like.user_id)
        if autor is None:
            continue

        cuando = _aware(like.created_at)
        elementos.append(
            {
                "id": f"like-{like.post_id}-{like.user_id}",
                "kind": TIPO_LIKE,
                "user": autor,
                "post_id": like.post_id,
                "post_preview": _vista_previa(mis_posts[like.post_id]),
                "created_at": cuando,
                "is_new": visto is None or (cuando is not None and cuando > visto),
            }
        )

    for comentario in db.scalars(
        select(PostComment).where(
            PostComment.post_id.in_(ids), PostComment.user_id != user.id
        )
    ).all():
        autor = db.get(User, comentario.user_id)
        if autor is None:
            continue

        cuando = _aware(comentario.created_at)
        elementos.append(
            {
                "id": f"comment-{comentario.id}",
                "kind": TIPO_COMENTARIO,
                "user": autor,
                "post_id": comentario.post_id,
                "post_preview": _vista_previa(mis_posts[comentario.post_id]),
                "created_at": cuando,
                "is_new": visto is None or (cuando is not None and cuando > visto),
            }
        )

    elementos.sort(
        key=lambda item: item["created_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    nuevas = sum(1 for item in elementos if item["is_new"])

    return elementos[:MAX_NOTIFICACIONES], nuevas

def count_unseen(db: Session, user: User) -> int:
    _, nuevas = list_notifications(db, user)
    return nuevas

def mark_seen(db: Session, user: User) -> None:
    user.notifications_seen_at = datetime.now(timezone.utc)
    db.commit()
