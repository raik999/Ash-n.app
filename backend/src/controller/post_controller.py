from __future__ import annotations
from sqlalchemy.orm import Session
from entities.post import Post
from entities.user import User
from middleware.error_middleware import NotFoundError
from services import post_service, user_service
from validations.auth_validation import MessageResponse
from validations.post_validation import (
    CommentResponse,
    CreateCommentRequest,
    CreatePostRequest,
    LikeResponse,
    PostFileResponse,
    PostResponse,
    PostSummaryResponse,
    UpdatePostRequest,
)
from validations.user_validation import TagResponse, UserSummaryResponse

def _to_response(
    post: Post, likes: int, comments: int, liked: bool, viewer: User | None
) -> PostResponse:
    return PostResponse(
        id=post.id,
        title=post.title,
        description=post.description,
        created_at=post.created_at,
        author=UserSummaryResponse.model_validate(post.author),
        files=[PostFileResponse.model_validate(f) for f in post.files],
        tags=[TagResponse.model_validate(t) for t in post.tags],
        likes_count=likes,
        comments_count=comments,
        liked_by_me=liked,
        can_edit=viewer is not None and viewer.id == post.user_id,
    )

def _to_summary(post: Post, likes: int, comments: int) -> PostSummaryResponse:
    return PostSummaryResponse(
        id=post.id,
        title=post.title,
        description=post.description,
        preview=PostFileResponse.model_validate(post.files[0]) if post.files else None,
        files_count=len(post.files),
        likes_count=likes,
        comments_count=comments,
    )

def _single(db: Session, post: Post, viewer: User | None) -> PostResponse:
    conteos = post_service.counts_for(db, [post.id])
    likes, comments = conteos.get(post.id, (0, 0))
    liked = post_service.has_like(db, post.id, viewer.id if viewer else None)
    return _to_response(post, likes, comments, liked, viewer)

def create_post(db: Session, user: User, payload: CreatePostRequest) -> PostResponse:
    post = post_service.create_post(
        db, user, payload.title, payload.description, payload.tag_ids
    )
    return _single(db, post, user)

def update_post(
    db: Session, user: User, post_id: int, payload: UpdatePostRequest
) -> PostResponse:
    post = post_service.update_post(
        db,
        user,
        post_id,
        payload.title,
        payload.description,
        payload.tag_ids,
        touched=payload.model_fields_set,
    )
    return _single(db, post, user)

def publish_post(db: Session, user: User, post_id: int) -> PostResponse:
    post = post_service.publish_post(db, user, post_id)
    return _single(db, post, user)

def delete_post(db: Session, user: User, post_id: int) -> MessageResponse:
    post_service.delete_post(db, user, post_id)
    return MessageResponse(detail="Publicacion eliminada")

def get_post(db: Session, post_id: int, viewer: User | None) -> PostResponse:
    post = post_service.get_post(db, post_id, viewer)
    return _single(db, post, viewer)

def list_user_posts(
    db: Session, username: str, viewer: User | None
) -> list[PostSummaryResponse]:
    author = user_service.get_user_by_username(db, username)
    if author is None:
        raise NotFoundError(f"No existe el usuario @{username}")

    posts = post_service.list_user_posts(db, author, viewer)

    conteos = post_service.counts_for(db, [p.id for p in posts])

    return [
        _to_summary(p, *conteos.get(p.id, (0, 0)))
        for p in posts
    ]

def add_file(db: Session, user: User, post_id: int, content: bytes) -> PostFileResponse:
    archivo = post_service.add_file(db, user, post_id, content)
    return PostFileResponse.model_validate(archivo)

def remove_file(db: Session, user: User, post_id: int, file_id: int) -> MessageResponse:
    post_service.remove_file(db, user, post_id, file_id)
    return MessageResponse(detail="Archivo eliminado")

def add_like(db: Session, user: User, post_id: int) -> LikeResponse:
    total = post_service.add_like(db, user, post_id)
    return LikeResponse(likes_count=total, liked_by_me=True)

def remove_like(db: Session, user: User, post_id: int) -> LikeResponse:
    total = post_service.remove_like(db, user, post_id)
    return LikeResponse(likes_count=total, liked_by_me=False)

def list_comments(
    db: Session, post_id: int, viewer: User | None
) -> list[CommentResponse]:
    post = post_service.get_post(db, post_id, viewer)
    comentarios = post_service.list_comments(db, post_id, viewer)

    return [
        CommentResponse(
            id=c.id,
            text=c.text,
            created_at=c.created_at,
            author=UserSummaryResponse.model_validate(c.author),
            can_delete=post_service.can_delete_comment(c, post, viewer),
        )
        for c in comentarios
    ]

def add_comment(
    db: Session, user: User, post_id: int, payload: CreateCommentRequest
) -> CommentResponse:
    comentario = post_service.add_comment(db, user, post_id, payload.text)
    post = post_service.get_post(db, post_id, user)

    return CommentResponse(
        id=comentario.id,
        text=comentario.text,
        created_at=comentario.created_at,
        author=UserSummaryResponse.model_validate(comentario.author),
        can_delete=True,
    )

def delete_comment(
    db: Session, user: User, post_id: int, comment_id: int
) -> MessageResponse:
    post_service.delete_comment(db, user, post_id, comment_id)
    return MessageResponse(detail="Comentario eliminado")
