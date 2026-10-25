"""Единая сборка Typst-источника.

Преамбула профиля — это библиотека ``fd``, литерал конфига и вызов
``fd.apply``. PDF, export-typ и превью используют один и тот же префикс;
тело документа приходит из Pandoc без фильтров.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from app.registry import options_payload
from app.utils.typst_config import build_fd_config

if TYPE_CHECKING:
    from app.models.sqlalchemy.profile import Profile

FD_LIBRARY_PATH = Path(__file__).resolve().parent.parent / "typst" / "fd.typ"


@lru_cache(maxsize=1)
def fd_library_source() -> str:
    """Читает библиотеку fd.typ; она вставляется в каждый полный исходник."""
    return FD_LIBRARY_PATH.read_text(encoding="utf-8").rstrip() + "\n"


def build_typst_preamble(profile: Profile) -> str:
    """Строит общий префикс: fd + конфиг профиля + применение конфига."""
    values, _source = options_payload(profile)
    config = build_fd_config(values)
    return (
        "// FluentDocs: библиотека оформления fd\n"
        f"{fd_library_source()}\n"
        f"#let fd-config = {config}\n\n"
        "#show: fd.apply.with(fd-config)\n"
    )


def build_typst_source(
    profile: Profile,
    typst_body: str,
    *,
    title_source: str | None = None,
    title_before_prefix: bool = False,
) -> str:
    """Полный исходник: префикс профиля, необязательный титульник, тело."""
    preamble = build_typst_preamble(profile)
    if title_source is None:
        return "\n".join([preamble, typst_body])
    if title_before_prefix:
        return "\n".join([title_source, preamble, typst_body])
    return "\n".join([preamble, title_source, typst_body])


__all__ = ["FD_LIBRARY_PATH", "build_typst_preamble", "build_typst_source", "fd_library_source"]
