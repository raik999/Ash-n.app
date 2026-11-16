from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from entities.portfolio import (
    COLOR_POR_DEFECTO,
    COLORES,
    MAX_DESCRIPCION,
    MAX_TITULO,
)
from validations.post_validation import PostFileResponse, PostSummaryResponse

def _validar_color(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in COLORES:
        raise ValueError("Ese color no esta en la paleta")
    return value

class CreatePortfolioRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITULO)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPCION)
    color: str = COLOR_POR_DEFECTO
    is_private: bool = False

    @field_validator("title")
    @classmethod
    def limpiar_titulo(cls, value: str) -> str:
        texto = value.strip()
        if not texto:
            raise ValueError("El portafolio necesita un titulo")
        return texto

    @field_validator("description")
    @classmethod
    def limpiar_descripcion(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("color")
    @classmethod
    def color_de_la_paleta(cls, value: str) -> str:
        return _validar_color(value) or COLOR_POR_DEFECTO

class UpdatePortfolioRequest(BaseModel):
    title: str | None = Field(default=None, max_length=MAX_TITULO)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPCION)
    color: str | None = None
    is_private: bool | None = None

    @field_validator("title")
    @classmethod
    def limpiar_titulo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        texto = value.strip()
        if not texto:
            raise ValueError("El portafolio necesita un titulo")
        return texto

    @field_validator("color")
    @classmethod
    def color_de_la_paleta(cls, value: str | None) -> str | None:
        return _validar_color(value)

class SetPostsRequest(BaseModel):
    post_ids: list[int] = Field(default_factory=list)

class PortfolioSummaryResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    color: str
    is_private: bool = False

    posts_count: int = 0

    preview: PostFileResponse | None = None

    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioResponse(PortfolioSummaryResponse):
    posts: list[PostSummaryResponse] = Field(default_factory=list)

    can_edit: bool = False

class TituloRepetidoResponse(BaseModel):
    repetido: bool = False
