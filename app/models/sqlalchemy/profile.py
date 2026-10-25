from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.sqlalchemy.styles import (
        BulletListStyle,
        DocumentStyle,
        EquationStyle,
        FigureStyle,
        FootnoteStyle,
        HeadingLevelStyle,
        HeadingStyle,
        NumberedListStyle,
        OutlineStyle,
        PageStyle,
        ParStyle,
        QuoteStyle,
        RawStyle,
        TableStyle,
        TermsStyle,
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    options_schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    options: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    bullet_list_style: Mapped[BulletListStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    document_style: Mapped[DocumentStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    figure_style: Mapped[FigureStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    footnote_style: Mapped[FootnoteStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    heading_style: Mapped[HeadingStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    heading_level_styles: Mapped[list[HeadingLevelStyle]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    equation_style: Mapped[EquationStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    numbered_list_style: Mapped[NumberedListStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    outline_style: Mapped[OutlineStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    page_style: Mapped[PageStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    par_style: Mapped[ParStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    quote_style: Mapped[QuoteStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    raw_style: Mapped[RawStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    table_style: Mapped[TableStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    terms_style: Mapped[TermsStyle | None] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
