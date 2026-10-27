from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from entities.post import MAX_TAGS_PER_POST
from entities.post_comment import MAX_COMMENT_LENGTH
from validations.user_validation import TagResponse, UserSummaryResponse

class PostFileResponse(BaseModel):
    id: int
    kind: str
    url: str
    position: int

    model_config = ConfigDict(from_attributes=True)

class PostResponse(BaseModel):
    id: int
    title: str | None = None
    description: str | None = None
    created_at: datetime | None = None

    author: UserSummaryResponse

    files: list[PostFileResponse] = Field(default_factory=list)
    tags: list[TagResponse] = Field(default_factory=list)

    likes_count: int = 0
    comments_count: int = 0

    liked_by_me: bool = False

    can_edit: bool = False

    model_config = ConfigDict(from_attributes=True)

class PostSummaryResponse(BaseModel):
    id: int
    title: str | None = None
    description: str | None = None
    preview: PostFileResponse | None = None
    files_count: int = 0
    likes_count: int = 0
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime | None = None
    author: UserSummaryResponse

    can_delete: bool = False

    model_config = ConfigDict(from_attributes=True)

class LikeResponse(BaseModel):
    likes_count: int
    liked_by_me: bool

class CreatePostRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    description: str | None = None
    tag_ids: list[int] | None = None

    @field_validator("title", "description")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        unique = list(dict.fromkeys(value))
        if len(unique) > MAX_TAGS_PER_POST:
            raise ValueError(f"Puedes elegir como maximo {MAX_TAGS_PER_POST} especialidades")
        return unique

class UpdatePostRequest(CreatePostRequest):
    pass

class CreateCommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_COMMENT_LENGTH)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El comentario no puede estar vacio")
        return value
