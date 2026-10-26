from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.constants.style_defaults import FIGURE_GAP_MM_DEFAULT, FIGURE_WIDTH_MM_DEFAULT
from app.models.pydantic.text_override import TextOverrideStyles, TextOverrideStylesUpdate


class FigureStyles(BaseModel):
    """Стили изображения/фигуры Typst: #set image(...) + #set figure(...)."""

    width: float = Field(FIGURE_WIDTH_MM_DEFAULT, ge=0.0, description="Ширина в mm (0 = auto)")
    height: float = Field(0.0, ge=0.0, description="Высота в mm (0 = auto)")
    placement: Literal["none", "auto", "top", "bottom"] = Field(
        "none",
        description="Размещение фигуры на странице",
    )
    gap: float = Field(
        FIGURE_GAP_MM_DEFAULT, ge=0.0, description="Зазор между телом и подписью в mm"
    )
    outlined: bool = Field(True, description="Включать в список фигур")
    fit: Literal["cover", "contain", "stretch"] = Field(
        "cover",
        description="Способ подгонки изображения",
    )
    caption_template: Optional[str] = Field(
        None,
        max_length=256,
        description="Шаблон подписи: {h1}–{h6}, {N}, {content}",
    )
    text_override: Optional[TextOverrideStyles] = None


class FigureStylesUpdate(BaseModel):
    width: Optional[float] = Field(None, ge=0.0)
    height: Optional[float] = Field(None, ge=0.0)
    placement: Optional[Literal["none", "auto", "top", "bottom"]] = None
    gap: Optional[float] = Field(None, ge=0.0)
    outlined: Optional[bool] = None
    fit: Optional[Literal["cover", "contain", "stretch"]] = None
    caption_template: Optional[str] = Field(None, max_length=256)
    text_override: Optional[TextOverrideStylesUpdate | dict] = None
