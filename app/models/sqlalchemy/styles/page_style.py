from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.constants.style_defaults import PAGE_MARGIN_MM_DEFAULT

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile


class PageStyle(Base):
    __tablename__ = "page_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    paper: Mapped[str] = mapped_column(String(64), nullable=False, default="a4")
    flipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    margin_top: Mapped[float] = mapped_column(Float, nullable=False, default=PAGE_MARGIN_MM_DEFAULT)
    margin_bottom: Mapped[float] = mapped_column(
        Float, nullable=False, default=PAGE_MARGIN_MM_DEFAULT
    )
    margin_left: Mapped[float] = mapped_column(
        Float, nullable=False, default=PAGE_MARGIN_MM_DEFAULT
    )
    margin_right: Mapped[float] = mapped_column(
        Float, nullable=False, default=PAGE_MARGIN_MM_DEFAULT
    )
    columns: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    numbering: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    number_align: Mapped[str] = mapped_column(String(32), nullable=False, default="center+bottom")

    profile: Mapped["Profile"] = relationship(back_populates="page_style")
