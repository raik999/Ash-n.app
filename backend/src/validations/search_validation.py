from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchHistoryEntry(BaseModel):
    id: int
    kind: str
    value: str
    model_config = ConfigDict(from_attributes=True)

class AddSearchRequest(BaseModel):
    kind: Literal["query", "user"]
    value: str = Field(..., min_length=1, max_length=60)

    @field_validator("value")
    @classmethod
    def clean_value(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La busqueda no puede estar vacia")
        return value
