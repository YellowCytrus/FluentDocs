"""Pydantic schema for per-level heading styles."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.pydantic.text_override import TextOverrideStyles, TextOverrideStylesUpdate


class HeadingLevelStyles(BaseModel):
    """Стили заголовка по уровню: break_before, numbering_enabled + text_override."""

    model_config = ConfigDict(extra="forbid")

    level: int = Field(..., ge=1, le=6)
    break_before: bool = Field(False, description="Начинать с новой страницы")
    numbering_enabled: bool = Field(
        True, description="Показывать номер заголовка (при глобальной нумерации)"
    )
    text_override: Optional[TextOverrideStyles] = None


class HeadingLevelStylesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    break_before: Optional[bool] = None
    numbering_enabled: Optional[bool] = None
    text_override: Optional[TextOverrideStylesUpdate | dict] = None  # None = clear
