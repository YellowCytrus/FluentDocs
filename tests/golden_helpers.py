"""Сборка эталонных Typst-источников для golden-снимков G0/G1b.

Два профиля: дефолтный (все стили с дефолтами ORM) и профиль с локальными
text_override на нескольких элементах. Pandoc вызывается без фильтров,
как в продакшене.
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
    TextOverrideStyle,
)
from app.registry import options_payload
from app.utils.typst_config import build_fd_config
from app.utils.typst_source import build_typst_source, fd_library_source

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_BODY_MARKER = "\n// --- document body ---\n"
DOCS_DIR = FIXTURES_DIR / "docs"
GOLDEN_DIR = FIXTURES_DIR / "golden"
TEXT_OVERRIDE_GOLDEN_DIR = GOLDEN_DIR / "text_override"

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


def text_override_profile(name: str = "golden-text-override") -> Profile:
    """Второй снимок: локальные переопределения текста на нескольких элементах."""
    profile = default_profile(name)
    profile.par_style.text_override_style = _with_defaults(
        TextOverrideStyle,
        font="DejaVu Sans",
        font_size=13.0,
        weight="bold",
        style="italic",
        fill="#7a1f1f",
        lang="ru",
        region="RU",
        tracking=0.2,
        word_spacing=95.0,
        hyphenate=False,
        ligatures=False,
        number_type="lining",
        number_width="tabular",
    )
    profile.heading_level_styles[0].text_override_style = _with_defaults(
        TextOverrideStyle,
        font_size=16.0,
        weight="bold",
    )
    profile.bullet_list_style.text_override_style = _with_defaults(
        TextOverrideStyle,
        font="DejaVu Sans",
        font_size=11.5,
    )
    profile.table_style.text_override_style = _with_defaults(
        TextOverrideStyle,
        font_size=10.0,
        style="italic",
        fill="#003366",
    )
    profile.figure_style.text_override_style = _with_defaults(
        TextOverrideStyle,
        font="DejaVu Serif",
        font_size=11.0,
        weight="semibold",
    )
    profile.footnote_style.text_override_style = _with_defaults(
        TextOverrideStyle,
        font_size=9.0,
        lang="ru",
        hyphenate=True,
    )
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
    """Полный Typst-источник: fd-префикс профиля + тело из Pandoc."""
    body = markdown_to_typst(markdown)
    return build_typst_source(profile or default_profile(), body)


def build_golden_source(markdown: str, profile: Profile | None = None) -> str:
    """Снимок без библиотеки fd: литерал конфига + тело документа.

    Правка ``fd.typ`` не должна менять golden: библиотека проверяется
    рендер-тестами, а снимок фиксирует только значения профиля и вывод Pandoc.
    """
    body = markdown_to_typst(markdown)
    values, _source = options_payload(profile or default_profile())
    return f"#let fd-config = {build_fd_config(values)}\n{GOLDEN_BODY_MARKER}{body}"


def golden_to_full_source(golden_text: str) -> str:
    """Собирает исполняемый исходник из снимка, подставляя текущую fd."""
    config_part, body = golden_text.split(GOLDEN_BODY_MARKER, 1)
    return f"{fd_library_source()}\n{config_part}\n#show: fd.apply.with(fd-config)\n{body}"


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_OVERRIDE_GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for doc in sorted(DOCS_DIR.glob("*.md")):
        markdown = doc.read_text(encoding="utf-8")
        default_source = build_golden_source(markdown, default_profile())
        (GOLDEN_DIR / f"{doc.stem}.typ").write_text(default_source, encoding="utf-8")
        print(f"wrote {GOLDEN_DIR / f'{doc.stem}.typ'}")
        override_source = build_golden_source(markdown, text_override_profile())
        (TEXT_OVERRIDE_GOLDEN_DIR / f"{doc.stem}.typ").write_text(override_source, encoding="utf-8")
        print(f"wrote {TEXT_OVERRIDE_GOLDEN_DIR / f'{doc.stem}.typ'}")


if __name__ == "__main__":
    main()
