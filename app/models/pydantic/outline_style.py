from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.pydantic.text_override import TextOverrideStyles, TextOverrideStylesUpdate

IndentMode = Literal["auto", "none", "custom"]


class OutlineStyles(BaseModel):
    """Стили оглавления Typst: #set outline(...)."""

    model_config = ConfigDict(extra="forbid")

    depth: Optional[int] = Field(None, ge=1, description="Глубина (null = все уровни)")
    indent_mode: IndentMode = Field("auto", description="Режим отступа: auto/none/custom")
    indent_mm: float = Field(0.0, ge=0, le=100, description="Отступ вложенности, мм")
    text_override: Optional[TextOverrideStyles] = None


class OutlineStylesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depth: Optional[int] = Field(None, ge=1)
    indent_mode: Optional[IndentMode] = None
    indent_mm: Optional[float] = Field(None, ge=0, le=100)
    text_override: Optional[TextOverrideStylesUpdate | dict] = None
