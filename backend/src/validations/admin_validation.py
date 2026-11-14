from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from entities.report import MAX_MOTIVO, TIPO_PUBLICACION, TIPO_USUARIO
from services.admin_service import MAX_DIAS_SANCION, MIN_DIAS_SANCION

class SancionRequest(BaseModel):
    dias: int = Field(ge=MIN_DIAS_SANCION, le=MAX_DIAS_SANCION)

    motivo: str | None = Field(default=None, max_length=MAX_MOTIVO)

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        texto = value.strip()
        return texto or None

class SancionResponse(BaseModel):
    username: str
    banned_until: datetime | None = None
    banned_reason: str | None = None
    dias_restantes: int = 0

    model_config = ConfigDict(from_attributes=True)

class ReportRequest(BaseModel):
    motivo: str | None = Field(default=None, max_length=MAX_MOTIVO)

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        texto = value.strip()
        return texto or None

class ReportResponse(BaseModel):
    id: int
    kind: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EstadoDeReporte(BaseModel):
    ya_reportado: bool = False

TIPOS = (TIPO_PUBLICACION, TIPO_USUARIO)
