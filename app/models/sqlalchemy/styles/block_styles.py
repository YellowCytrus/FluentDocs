from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from app.models.constants.style_defaults import (
    DOCUMENT_LINE_SPACING_MM_DEFAULT,
    PAR_SPACING_MM_DEFAULT,
    QUOTE_INDENT_MM_DEFAULT,
)
from app.models.sqlalchemy.styles.base import DEFAULT_FONT, TextOverrideMixin, TextOverrideStyle

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile


class DocumentStyle(Base):
    __tablename__ = "document_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    font_size: Mapped[float] = mapped_column(Float, nullable=False, default=12.0)
    line_spacing: Mapped[float] = mapped_column(
        Float, nullable=False, default=DOCUMENT_LINE_SPACING_MM_DEFAULT
    )
    font: Mapped[str] = mapped_column(String(255), nullable=False, default=DEFAULT_FONT)
    weight: Mapped[str] = mapped_column(String(32), nullable=False, default="regular")
    style: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    fill: Mapped[str] = mapped_column(String(64), nullable=False, default="black")
    lang: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    region: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, default=None)
    tracking: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    word_spacing: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    hyphenate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=None)
    ligatures: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    number_type: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    number_width: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    justify: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped["Profile"] = relationship(back_populates="document_style")


class ParStyle(TextOverrideMixin, Base):
    __tablename__ = "par_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    spacing: Mapped[float] = mapped_column(Float, nullable=False, default=PAR_SPACING_MM_DEFAULT)
    first_line_indent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hanging_indent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    linebreaks: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="par_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class QuoteStyle(TextOverrideMixin, Base):
    __tablename__ = "quote_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    indent: Mapped[float] = mapped_column(Float, nullable=False, default=QUOTE_INDENT_MM_DEFAULT)
    block: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quotes: Mapped[str] = mapped_column(String(16), nullable=False, default="auto")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="quote_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )
