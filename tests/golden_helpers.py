"""Сборка эталонного Typst-источника для golden-снимков G0.

Профиль — все стили с дефолтами ORM (как после создания профиля через API),
без text_override. Панок вызывается без фильтров, как в продакшене.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TypeVar

from app.models.sqlalchemy.profile import Profile
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
from app.utils.typst_preamble import build_typst_preamble

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DOCS_DIR = FIXTURES_DIR / "docs"
GOLDEN_DIR = FIXTURES_DIR / "golden"

StyleT = TypeVar("StyleT")


def _with_defaults(model: type[StyleT], **overrides: object) -> StyleT:
    """Создаёт ORM-объект с дефолтами колонок (без записи в БД)."""
    obj = model(**overrides)
    for column in model.__table__.columns:
        if column.name in {"id", "profile_id", "text_override_style_id"}:
            continue
        if getattr(obj, column.name, None) is not None:
            continue
        default = column.default
        if default is None:
            continue
        value = default.arg(None) if callable(default.arg) else default.arg
        setattr(obj, column.name, value)
    return obj


def default_profile(name: str = "golden-default") -> Profile:
    """Профиль со всеми стилями и дефолтными значениями моделей."""
    profile = Profile(name=name)
    profile.page_style = _with_defaults(PageStyle)
    profile.document_style = _with_defaults(DocumentStyle)
    profile.par_style = _with_defaults(ParStyle)
    profile.bullet_list_style = _with_defaults(BulletListStyle)
    profile.numbered_list_style = _with_defaults(NumberedListStyle)
    profile.table_style = _with_defaults(TableStyle)
    profile.figure_style = _with_defaults(FigureStyle)
    profile.footnote_style = _with_defaults(FootnoteStyle)
    profile.quote_style = _with_defaults(QuoteStyle)
    profile.raw_style = _with_defaults(RawStyle)
    profile.terms_style = _with_defaults(TermsStyle)
    profile.outline_style = _with_defaults(OutlineStyle)
    profile.heading_style = _with_defaults(HeadingStyle)
    profile.equation_style = _with_defaults(EquationStyle)
    profile.heading_level_styles = [
        _with_defaults(HeadingLevelStyle, level=level) for level in range(1, 7)
    ]
    return profile


def markdown_to_typst(markdown: str) -> str:
    """Pandoc CLI: markdown+raw_attribute -> typst (без фильтров)."""
    result = subprocess.run(
        ["pandoc", "--from=markdown+raw_attribute", "--to=typst", "--output=-"],
        input=markdown.encode("utf-8"),
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout.decode("utf-8")


def build_source(markdown: str, profile: Profile | None = None) -> str:
    """Полный Typst-источник: преамбула профиля + тело из Pandoc."""
    preamble = build_typst_preamble(profile or default_profile())
    body = markdown_to_typst(markdown)
    return preamble + "\n" + body


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for doc in sorted(DOCS_DIR.glob("*.md")):
        source = build_source(doc.read_text(encoding="utf-8"))
        target = GOLDEN_DIR / f"{doc.stem}.typ"
        target.write_text(source, encoding="utf-8")
        print(f"wrote {target}")


if __name__ == "__main__":
    main()
