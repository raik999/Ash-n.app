from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from entities.user import UserRole
from validations.auth_validation import USERNAME_PATTERN


class TagResponse(BaseModel):
    id: int
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: UserRole
    birthdate: date | None = None
    bio: str | None = None
    avatar_url: str | None = None
    tags: list[TagResponse] = Field(default_factory=list, alias="tipo")
    created_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    username: str | None = Field(default=None, min_length=3, max_length=30)
    bio: str | None = Field(default=None, max_length=500)
    birthdate: date | None = None
    tag_ids: list[int] | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                "El nombre de usuario solo puede tener letras, numeros, punto "
                "y guion bajo, y debe medir entre 3 y 30 caracteres"
            )
        return value

    @field_validator("bio")
    @classmethod
    def clean_bio(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("birthdate")
    @classmethod
    def validate_birthdate(cls, value: date | None) -> date | None:
        if value is None:
            return None
        today = date.today()
        if value > today:
            raise ValueError("La fecha de nacimiento no puede estar en el futuro")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise ValueError("Debes tener al menos 13 anios para usar Ashun")
        if age > 120:
            raise ValueError("Revisa la fecha de nacimiento, no parece valida")
        return value

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        unique = list(dict.fromkeys(value))
        if len(unique) > 10:
            raise ValueError("Puedes seleccionar como maximo 10 especialidades")
        return unique


class AvatarResponse(BaseModel):
    avatar_url: str
