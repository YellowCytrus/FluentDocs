"""Сериализация значений реестра в Typst-литерал fd-config.

Литерал — обычный словарь Typst. Вся логика применения значений находится
в библиотеке ``app/typst/fd.typ``; Python только раскладывает значения по
полям конфига.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from app.registry.options import JsonValue
from app.utils.typst_literals import typst_str


@dataclass(frozen=True)
class _Raw:
    """Готовое к вставке выражение Typst (auto, true/false)."""

    text: str


def _element(values: Mapping[str, JsonValue], name: str) -> Mapping[str, JsonValue]:
    raw = values.get(name)
    if not isinstance(raw, Mapping):
        raise ValueError(f"В значениях реестра отсутствует элемент {name!r}")
    return raw


def _value(element: Mapping[str, JsonValue], key: str) -> JsonValue:
    if key not in element:
        raise ValueError(f"В значениях реестра отсутствует поле {key!r}")
    return element[key]


def _hyphenate(value: JsonValue) -> _Raw:
    """Строковое кодирование registry → значение Typst hyphenate."""
    if value is None:
        return _Raw("auto")
    if value is True or value == "true":
        return _Raw("true")
    if value is False or value == "false":
        return _Raw("false")
    raise ValueError(f"Недопустимое значение hyphenate: {value!r}")


def _text_override(raw: JsonValue) -> dict[str, JsonValue] | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("text_override должен быть объектом или null")
    result: dict[str, JsonValue] = {}
    for key, value in raw.items():
        result[key] = _hyphenate(value) if key == "hyphenate" else value
    return result


def _element_tree(element: Mapping[str, JsonValue], keys: tuple[str, ...]) -> dict[str, JsonValue]:
    tree: dict[str, JsonValue] = {}
    for key in keys:
        raw = _value(element, key)
        tree[key] = _text_override(raw) if key == "text_override" else raw
    if "hyphenate" in tree:
        tree["hyphenate"] = _hyphenate(tree["hyphenate"])
    return tree


def _heading_levels(values: Mapping[str, JsonValue]) -> list[JsonValue]:
    raw_levels = values.get("heading_levels")
    if not isinstance(raw_levels, Mapping):
        raise ValueError("В значениях реестра отсутствует heading_levels")
    levels: list[JsonValue] = []
    for level in range(1, 7):
        raw = raw_levels.get(str(level))
        if not isinstance(raw, Mapping):
            raise ValueError(f"В значениях реестра отсутствует уровень {level}")
        record: dict[str, JsonValue] = {
            "level": level,
            "break_before": _value(raw, "break_before"),
            "numbering_enabled": _value(raw, "numbering_enabled"),
            "text_override": _text_override(_value(raw, "text_override")),
        }
        levels.append(record)
    return levels


def config_tree(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Строит дерево конфига из полного набора значений реестра."""
    return {
        "page": _element_tree(
            _element(values, "page"),
            (
                "paper",
                "flipped",
                "margin_top",
                "margin_bottom",
                "margin_left",
                "margin_right",
                "columns",
                "numbering",
                "number_align",
            ),
        ),
        "document": _element_tree(
            _element(values, "document"),
            (
                "font_size",
                "line_spacing",
                "font",
                "weight",
                "style",
                "fill",
                "lang",
                "region",
                "tracking",
                "word_spacing",
                "hyphenate",
                "ligatures",
                "number_type",
                "number_width",
                "justify",
            ),
        ),
        "par": _element_tree(
            _element(values, "par"),
            (
                "spacing",
                "first_line_indent",
                "hanging_indent",
                "linebreaks",
                "text_override",
            ),
        ),
        "heading": _element_tree(_element(values, "heading"), ("numbering",)),
        "heading_levels": _heading_levels(values),
        "bullet_list": _element_tree(
            _element(values, "bullet_list"),
            ("tight", "marker", "indent", "body_indent", "spacing", "text_override"),
        ),
        "numbered_list": _element_tree(
            _element(values, "numbered_list"),
            (
                "tight",
                "indent",
                "body_indent",
                "spacing",
                "numbering",
                "start",
                "full",
                "reversed",
                "number_align",
                "text_override",
            ),
        ),
        "terms": _element_tree(
            _element(values, "terms"),
            ("tight", "indent", "hanging_indent", "spacing", "text_override"),
        ),
        "table": _element_tree(
            _element(values, "table"),
            ("stroke", "align", "inset", "fill", "text_override"),
        ),
        "figure": _element_tree(
            _element(values, "figure"),
            (
                "width",
                "height",
                "placement",
                "gap",
                "outlined",
                "fit",
                "caption_template",
                "text_override",
            ),
        ),
        "equation": _element_tree(_element(values, "equation"), ("text_override",)),
        "quote": _element_tree(
            _element(values, "quote"),
            ("indent", "block", "quotes", "text_override"),
        ),
        "footnote": _element_tree(
            _element(values, "footnote"),
            ("marker_format", "clearance", "gap", "indent", "text_override"),
        ),
        "raw": _element_tree(
            _element(values, "raw"),
            ("tab_size", "align", "theme", "text_override"),
        ),
        "outline": _element_tree(
            _element(values, "outline"),
            ("depth", "indent", "text_override"),
        ),
    }


def _render(value: JsonValue, indent: int) -> str:
    pad = "  " * indent
    if isinstance(value, _Raw):
        return value.text
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return typst_str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return "()"
        lines = ["("]
        for item in value:
            lines.append(f"{pad}  {_render(item, indent + 1)},")
        lines.append(f"{pad})")
        return "\n".join(lines)
    if isinstance(value, Mapping):
        if not value:
            return "()"
        lines = ["("]
        for key, item in value.items():
            lines.append(f"{pad}  {key}: {_render(item, indent + 1)},")
        lines.append(f"{pad})")
        return "\n".join(lines)
    raise TypeError(f"Неподдерживаемое значение конфига: {type(value)!r}")


def build_fd_config(values: Mapping[str, JsonValue]) -> str:
    """Возвращает Typst-литерал словаря конфига профиля."""
    return _render(cast(JsonValue, config_tree(values)), 0)


__all__ = ["build_fd_config", "config_tree"]
