from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from config.database import get_db
from controller import post_controller
from entities.user import User
from middleware.auth_middleware import get_current_user, get_current_user_optional
from validations.auth_validation import MessageResponse
from validations.post_validation import (
    CommentResponse,
    CreateCommentRequest,
    CreatePostRequest,
    LikeResponse,
    PostFileResponse,
    PostResponse,
    UpdatePostRequest,
)

router = APIRouter(prefix="/api/posts", tags=["Publicaciones"])

@router.post("", response_model=PostResponse, status_code=201, summary="Crear un borrador")
def create_post(
    payload: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    return post_controller.create_post(db, current_user, payload)

@router.post(
    "/{post_id}/publish",
    response_model=PostResponse,
    summary="Publicar (hacerla visible)",
)
def publish_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    return post_controller.publish_post(db, current_user, post_id)

@router.post(
    "/{post_id}/files",
    response_model=PostFileResponse,
    status_code=201,
    summary="Subir un archivo a la publicacion",
)
async def add_file(
    post_id: int,
    file: UploadFile = File(..., description="Imagen, video o audio"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostFileResponse:
    content = await file.read()
    return post_controller.add_file(db, current_user, post_id, content)

@router.delete(
    "/{post_id}/files/{file_id}",
    response_model=MessageResponse,
    summary="Quitar un archivo de la publicacion",
)
def remove_file(
    post_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return post_controller.remove_file(db, current_user, post_id, file_id)

@router.post("/{post_id}/like", response_model=LikeResponse, summary="Dar like")
def add_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LikeResponse:
    return post_controller.add_like(db, current_user, post_id)

@router.delete("/{post_id}/like", response_model=LikeResponse, summary="Quitar mi like")
def remove_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LikeResponse:
    return post_controller.remove_like(db, current_user, post_id)

@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse],
    summary="Ver los comentarios",
)
def list_comments(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    return post_controller.list_comments(db, post_id, viewer)

@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=201,
    summary="Comentar",
)
def add_comment(
    post_id: int,
    payload: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    return post_controller.add_comment(db, current_user, post_id, payload)

@router.delete(
    "/{post_id}/comments/{comment_id}",
    response_model=MessageResponse,
    summary="Eliminar un comentario",
)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return post_controller.delete_comment(db, current_user, post_id, comment_id)

@router.patch("/{post_id}", response_model=PostResponse, summary="Editar la publicacion")
def update_post(
    post_id: int,
    payload: UpdatePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    return post_controller.update_post(db, current_user, post_id, payload)

@router.delete(
    "/{post_id}", response_model=MessageResponse, summary="Eliminar la publicacion"
)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    return post_controller.delete_post(db, current_user, post_id)

@router.get("/{post_id}", response_model=PostResponse, summary="Ver una publicacion")
def get_post(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PostResponse:
    return post_controller.get_post(db, post_id, viewer)
