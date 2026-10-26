from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.constants.style_defaults import PAR_SPACING_MM_DEFAULT
from app.models.pydantic.text_override import TextOverrideStyles, TextOverrideStylesUpdate


class ParStyles(BaseModel):
    """Стили абзаца Typst: #set par(...)."""

    spacing: float = Field(
        PAR_SPACING_MM_DEFAULT, ge=0.0, description="Интервал между абзацами в mm"
    )
    first_line_indent: float = Field(0.0, ge=0.0, description="Отступ первой строки в mm")
    hanging_indent: float = Field(0.0, ge=0.0, description="Висячий отступ в mm")
    linebreaks: Literal["auto", "simple", "optimized"] = "auto"
    text_override: Optional[TextOverrideStyles] = None


class ParStylesUpdate(BaseModel):
    spacing: Optional[float] = Field(None, ge=0.0)
    first_line_indent: Optional[float] = Field(None, ge=0.0)
    hanging_indent: Optional[float] = Field(None, ge=0.0)
    linebreaks: Optional[Literal["auto", "simple", "optimized"]] = None
    text_override: Optional[TextOverrideStylesUpdate | dict] = None
