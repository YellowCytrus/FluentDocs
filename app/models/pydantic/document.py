from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.constants.style_defaults import DOCUMENT_LINE_SPACING_MM_DEFAULT


class DocumentStyles(BaseModel):
    """Стили документа Typst: #set text(...) + #set par(leading: ...)."""

    font_size: float = Field(12.0, ge=6.0, le=72.0, description="Размер шрифта в pt")
    line_spacing: float = Field(
        DOCUMENT_LINE_SPACING_MM_DEFAULT,
        ge=2.1166666667,
        le=12.7,
        description="Межстрочный интервал в mm",
    )
    font: str = Field("libertinus serif", max_length=255, description="Семейство шрифта")
    weight: Literal[
        "thin",
        "extralight",
        "light",
        "regular",
        "medium",
        "semibold",
        "bold",
        "extrabold",
        "black",
    ] = "regular"
    style: Literal["normal", "italic", "oblique"] = "normal"
    fill: str = Field("black", max_length=64, description="Цвет текста")
    lang: str = Field("en", max_length=16, description="ISO 639 код языка")
    region: Optional[str] = Field(None, max_length=16, description="ISO 3166-1 alpha-2 регион")
    tracking: float = Field(0.0, description="Межбуквенный интервал в pt")
    word_spacing: float = Field(100.0, ge=0.0, le=500.0, description="Межсловный интервал в %")
    hyphenate: Optional[bool] = Field(None, description="Перенос слов (null = auto)")
    ligatures: bool = Field(True, description="Лигатуры")
    number_type: Literal["auto", "lining", "old-style"] = "auto"
    number_width: Literal["auto", "proportional", "tabular"] = "auto"
    justify: bool = Field(False, description="Выравнивание по ширине (глобально для абзацев)")


class DocumentStylesUpdate(BaseModel):
    font_size: Optional[float] = Field(None, ge=6.0, le=72.0)
    line_spacing: Optional[float] = Field(None, ge=2.1166666667, le=12.7)
    font: Optional[str] = Field(None, max_length=255)
    weight: Optional[
        Literal[
            "thin",
            "extralight",
            "light",
            "regular",
            "medium",
            "semibold",
            "bold",
            "extrabold",
            "black",
        ]
    ] = None
    style: Optional[Literal["normal", "italic", "oblique"]] = None
    fill: Optional[str] = Field(None, max_length=64)
    lang: Optional[str] = Field(None, max_length=16)
    region: Optional[str] = Field(None, max_length=16)
    tracking: Optional[float] = None
    word_spacing: Optional[float] = Field(None, ge=0.0, le=500.0)
    hyphenate: Optional[bool] = None
    ligatures: Optional[bool] = None
    number_type: Optional[Literal["auto", "lining", "old-style"]] = None
    number_width: Optional[Literal["auto", "proportional", "tabular"]] = None
    justify: Optional[bool] = None
