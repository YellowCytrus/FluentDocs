from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.constants.style_defaults import BULLET_MARKERS_DEFAULT, LIST_BODY_INDENT_MM_DEFAULT

from app.models.sqlalchemy.styles.base import TextOverrideMixin, TextOverrideStyle

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile


class BulletListStyle(TextOverrideMixin, Base):
    __tablename__ = "bullet_list_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marker: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=lambda: list(BULLET_MARKERS_DEFAULT),
    )
    indent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    body_indent: Mapped[float] = mapped_column(
        Float, nullable=False, default=LIST_BODY_INDENT_MM_DEFAULT
    )
    spacing: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="bullet_list_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )


class NumberedListStyle(TextOverrideMixin, Base):
    __tablename__ = "numbered_list_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    indent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    body_indent: Mapped[float] = mapped_column(
        Float, nullable=False, default=LIST_BODY_INDENT_MM_DEFAULT
    )
    spacing: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    numbering: Mapped[str] = mapped_column(String(64), nullable=False, default="1.")
    start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    full: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reversed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    number_align: Mapped[str] = mapped_column(String(32), nullable=False, default="end+top")
    text_override_style_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("text_override_styles.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["Profile"] = relationship(back_populates="numbered_list_style")
    text_override_style: Mapped[Optional[TextOverrideStyle]] = relationship(
        foreign_keys=[text_override_style_id],
        lazy="joined",
    )
