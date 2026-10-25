"""Совместимый фасад сборки Typst-преамбулы.

Историческое имя оставлено для API и golden-тестов; фактическая сборка
находится в :mod:`app.utils.typst_source`.
"""

from __future__ import annotations

from app.utils.typst_literals import _typst_bool, _typst_font, _typst_str
from app.utils.typst_source import build_typst_preamble, build_typst_source

__all__ = [
    "_typst_bool",
    "_typst_font",
    "_typst_str",
    "build_typst_preamble",
    "build_typst_source",
]
