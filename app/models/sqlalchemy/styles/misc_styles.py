from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.constants.style_defaults import TERMS_HANGING_INDENT_MM_DEFAULT

from app.models.sqlalchemy.styles.base import TextOverrideMixin, TextOverrideStyle

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile


class RawStyle(TextOverrideMixin, Base):
    __tablename__ = "raw_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tab_size: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    align: Mapped[str] = mapped_column(String(32), nullable=False, default="start")
    theme: Mapped[str] = mapped_column(String(64), nullable=False, default="auto")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="raw_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class TermsStyle(TextOverrideMixin, Base):
    __tablename__ = "terms_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    indent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hanging_indent: Mapped[float] = mapped_column(
        Float, nullable=False, default=TERMS_HANGING_INDENT_MM_DEFAULT
    )
    spacing: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="terms_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class OutlineStyle(TextOverrideMixin, Base):
    __tablename__ = "outline_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    # Старая строковая колонка: не удаляется, но реестром не используется.
    indent: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    indent_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="step")
    indent_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="outline_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class EquationStyle(TextOverrideMixin, Base):
    __tablename__ = "equation_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="equation_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )
