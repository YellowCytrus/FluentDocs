"""Литералы Typst, общие для генератора и экспорта титульной страницы."""

from __future__ import annotations

from app.utils.constants.typst_preamble_constants import FONT_ALIASES


def typst_str(value: str) -> str:
    """Форматирует строку Python как строковый литерал Typst."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def typst_font(font: str) -> str:
    """Нормализует имя шрифта для Typst (алиасы, пустое значение — дефолт)."""
    value = (font or "").strip()
    if not value:
        return "libertinus serif"
    return FONT_ALIASES.get(value.lower(), font)


def typst_bool(value: bool | None) -> str:
    """bool → true/false, None → auto."""
    if value is None:
        return "auto"
    return str(value).lower()


# Старые приватные имена используются экспортёром титульной страницы.
_typst_str = typst_str
_typst_font = typst_font
_typst_bool = typst_bool

__all__ = ["_typst_bool", "_typst_font", "_typst_str", "typst_bool", "typst_font", "typst_str"]
