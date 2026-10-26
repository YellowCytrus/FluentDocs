from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.constants.style_defaults import (
    FIGURE_GAP_MM_DEFAULT,
    FIGURE_WIDTH_MM_DEFAULT,
    FOOTNOTE_CLEARANCE_MM_DEFAULT,
    FOOTNOTE_GAP_MM_DEFAULT,
    FOOTNOTE_INDENT_MM_DEFAULT,
    TABLE_INSET_MM_DEFAULT,
    TABLE_STROKE_MM_DEFAULT,
)

from app.models.sqlalchemy.styles.base import TextOverrideMixin, TextOverrideStyle

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile


class FigureStyle(TextOverrideMixin, Base):
    __tablename__ = "figure_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    width: Mapped[float] = mapped_column(Float, nullable=False, default=FIGURE_WIDTH_MM_DEFAULT)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    placement: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    gap: Mapped[float] = mapped_column(Float, nullable=False, default=FIGURE_GAP_MM_DEFAULT)
    outlined: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fit: Mapped[str] = mapped_column(String(32), nullable=False, default="cover")
    caption_template: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, default=None
    )
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="figure_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class FootnoteStyle(TextOverrideMixin, Base):
    __tablename__ = "footnote_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    marker_format: Mapped[str] = mapped_column(String(32), nullable=False, default="1")
    clearance: Mapped[float] = mapped_column(
        Float, nullable=False, default=FOOTNOTE_CLEARANCE_MM_DEFAULT
    )
    gap: Mapped[float] = mapped_column(Float, nullable=False, default=FOOTNOTE_GAP_MM_DEFAULT)
    indent: Mapped[float] = mapped_column(Float, nullable=False, default=FOOTNOTE_INDENT_MM_DEFAULT)
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="footnote_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class HeadingStyle(Base):
    __tablename__ = "heading_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    numbering: Mapped[str] = mapped_column(String(64), nullable=False, default="1.1.1")

    profile: Mapped["Profile"] = relationship(back_populates="heading_style")


class HeadingLevelStyle(TextOverrideMixin, Base):
    __tablename__ = "heading_level_styles"
    __table_args__ = (
        UniqueConstraint("profile_id", "level", name="uq_heading_level_profile_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–6
    outlined: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bookmarked: Mapped[str] = mapped_column(String(16), nullable=False, default="auto")
    offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    break_before: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    numbering_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="heading_level_styles")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class TableStyle(TextOverrideMixin, Base):
    __tablename__ = "table_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    stroke: Mapped[float] = mapped_column(Float, nullable=False, default=TABLE_STROKE_MM_DEFAULT)
    align: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    inset: Mapped[float] = mapped_column(Float, nullable=False, default=TABLE_INSET_MM_DEFAULT)
    fill: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="table_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )
