from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Correo del usuario")
    name: str = Field(..., min_length=2, max_length=80, description="Nombre completo")
    username: str = Field(..., min_length=3, max_length=30, description="Nombre de usuario")
    password: str = Field(..., min_length=6, max_length=72)
    confirm_password: str = Field(..., min_length=6, max_length=72)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                "El nombre de usuario solo puede tener letras, numeros, punto "
                "y guion bajo, y debe medir entre 3 y 30 caracteres"
            )
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacio")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contrasena es demasiado larga (maximo 72 bytes)")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Las contrasenas no coinciden")
        return self


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=160)
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class MessageResponse(BaseModel):
    detail: str
