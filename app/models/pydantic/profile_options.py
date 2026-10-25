"""Pydantic-схемы API значений реестра опций профиля."""

from typing import Literal

from pydantic import BaseModel, Field

from app.registry.options import JsonValue


class ProfileOptionsUpdate(BaseModel):
    """Полная замена значений опций профиля."""

    schema_version: int = Field(..., ge=1)
    values: dict[str, JsonValue]


class ProfileOptionsRead(BaseModel):
    """Значения опций и источник, из которого они прочитаны."""

    schema_version: int
    source: Literal["jsonb", "legacy"]
    values: dict[str, JsonValue]
