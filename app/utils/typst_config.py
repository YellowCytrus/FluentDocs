"""Сериализация значений реестра в Typst-литерал fd-config.

Литерал — обычный словарь Typst. Вся логика применения значений находится
в библиотеке ``app/typst/fd.typ``; Python только раскладывает значения по
полям конфига.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from app.registry.options import (
    AROUND_TARGETS,
    DEFAULT_LEADING_EM,
    JsonValue,
    line_height_coefficient,
)
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


def _around_item(raw: JsonValue) -> JsonValue:
    if not isinstance(raw, Mapping):
        raise ValueError("Элемент around должен быть объектом")
    item: dict[str, JsonValue] = {}
    for key, value in raw.items():
        item[key] = _text_override(value) if key == "text_override" else value
    return item


def _around(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    raw_around = values.get("around")
    if not isinstance(raw_around, Mapping):
        raise ValueError("В значениях реестра отсутствует around")
    tree: dict[str, JsonValue] = {}
    for target in AROUND_TARGETS:
        raw = raw_around.get(target)
        if not isinstance(raw, Mapping):
            raise ValueError(f"В значениях реестра отсутствует around.{target}")
        before = raw.get("before")
        after = raw.get("after")
        if not isinstance(before, list) or not isinstance(after, list):
            raise ValueError(f"around.{target}.before/after должны быть списками")
        tree[target] = {
            "before": [_around_item(item) for item in before],
            "after": [_around_item(item) for item in after],
            "collapse": _value(raw, "collapse"),
        }
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
            "spacing_before": _number(raw, "spacing_before"),
            "spacing_after": _number(raw, "spacing_after"),
            "text_override": _text_override(_value(raw, "text_override")),
        }
        levels.append(record)
    return levels


def _structural_entity(raw: JsonValue) -> JsonValue:
    """Одна структурная сущность: match + apply с вложенным окружением."""
    if not isinstance(raw, Mapping):
        raise ValueError("structural.entities: элемент должен быть объектом")
    match = raw.get("match")
    apply = raw.get("apply")
    if not isinstance(match, Mapping) or not isinstance(apply, Mapping):
        raise ValueError("structural.entities: нужны match и apply")
    around = apply.get("around")
    if not isinstance(around, Mapping):
        raise ValueError("structural.entities: нужен apply.around")
    before = around.get("before")
    after = around.get("after")
    if not isinstance(before, list) or not isinstance(after, list):
        raise ValueError("structural.entities: around.before/after должны быть списками")
    return {
        "id": raw.get("id", ""),
        "label": raw.get("label", ""),
        "match": {
            key: match.get(key)
            for key in (
                "target",
                "level",
                "mode",
                "value",
                "case_insensitive",
            )
        },
        "apply": {
            "numbering": apply.get("numbering"),
            "break_before": apply.get("break_before"),
            "align": apply.get("align"),
            "case": apply.get("case"),
            "bold": apply.get("bold"),
            "outlined": apply.get("outlined"),
            "appendix": apply.get("appendix"),
            "around": {
                "before": [_around_item(item) for item in before],
                "after": [_around_item(item) for item in after],
                "collapse": around.get("collapse"),
            },
            "text_override": _text_override(apply.get("text_override")),
        },
    }


def _structural(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    raw = _element(values, "structural")
    entities = raw.get("entities")
    if not isinstance(entities, list):
        raise ValueError("structural.entities должен быть списком")
    return {"entities": [_structural_entity(item) for item in entities]}


def _number(element: Mapping[str, JsonValue], key: str) -> float:
    raw = _value(element, key)
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise ValueError(f"Поле {key!r} должно быть числом")
    return float(raw)


def _document(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    raw = _element(values, "document")
    tree = _element_tree(
        raw,
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
    )
    spacing = tree["line_spacing"]
    if not isinstance(spacing, Mapping) or "mode" not in spacing or "value" not in spacing:
        raise ValueError("document.line_spacing должен быть объектом {mode, value}")
    # Для известного шрифта коэффициент берётся из таблицы S9, иначе — ручной.
    tree["line_height_em"] = line_height_coefficient(
        str(_value(raw, "font")), _number(raw, "line_height_em")
    )
    tree["default_leading_em"] = DEFAULT_LEADING_EM
    return tree


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
                "margin_landscape_top",
                "margin_landscape_bottom",
                "margin_landscape_left",
                "margin_landscape_right",
                "columns",
                "numbering",
                "numbering_skip_first",
                "numbering_start",
                "number_align",
            ),
        ),
        "document": _document(values),
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
        "heading": _element_tree(
            _element(values, "heading"),
            ("numbering", "unnumbered_indent", "keep_with_next"),
        ),
        "heading_levels": _heading_levels(values),
        "bullet_list": _element_tree(
            _element(values, "bullet_list"),
            (
                "tight",
                "marker",
                "indent",
                "body_indent",
                "spacing",
                "tight_spacing",
                "loose_spacing",
                "spacing_before",
                "spacing_after",
                "text_override",
            ),
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
                "tight_spacing",
                "loose_spacing",
                "spacing_before",
                "spacing_after",
                "text_override",
            ),
        ),
        "terms": _element_tree(
            _element(values, "terms"),
            (
                "tight",
                "indent",
                "hanging_indent",
                "spacing",
                "tight_spacing",
                "loose_spacing",
                "spacing_before",
                "spacing_after",
                "text_override",
            ),
        ),
        "table": _element_tree(
            _element(values, "table"),
            (
                "stroke",
                "align",
                "inset",
                "fill",
                "spacing_before",
                "spacing_after",
                "text_override",
            ),
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
                "spacing_before",
                "spacing_after",
                "text_override",
            ),
        ),
        "equation": _element_tree(
            _element(values, "equation"),
            ("body_indent", "spacing_before", "spacing_after", "text_override"),
        ),
        "quote": _element_tree(
            _element(values, "quote"),
            ("indent", "block", "quotes", "spacing_before", "spacing_after", "text_override"),
        ),
        "footnote": _element_tree(
            _element(values, "footnote"),
            (
                "marker_format",
                "clearance",
                "gap",
                "indent",
                "separator_length",
                "separator_stroke",
                "text_override",
            ),
        ),
        "raw": _element_tree(
            _element(values, "raw"),
            ("tab_size", "align", "theme", "spacing_before", "spacing_after", "text_override"),
        ),
        "outline": _element_tree(
            _element(values, "outline"),
            ("depth", "indent_mode", "indent_mm", "text_override"),
        ),
        "structural": _structural(values),
        "appendix": _element_tree(
            _element(values, "appendix"),
            (
                "template",
                "service_case",
                "title_case",
                "bold",
                "alphabet",
                "overflow",
            ),
        ),
        "around": _around(values),
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
