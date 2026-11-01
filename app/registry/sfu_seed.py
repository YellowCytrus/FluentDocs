"""Seed-профиль «СТУ СФУ»: только значения реестра и ссылки на источник.

Профиль — данные, а не код (AGENTS 6, G6): каждое отличие от дефолтов реестра
описано парой «значение + пункт СТУ / id правила из референса». Генератор
оформления о СФУ ничего не знает.
"""

from __future__ import annotations

from typing import cast

from app.registry.options import OPTIONS_BY_ID, JsonValue
from app.registry.storage import default_values

SFU_PROFILE_NAME = "СТУ СФУ"

# Значения, отличающиеся от дефолтов реестра. Ключ — id опции.
# Формат: id -> (значение, источник).
SFU_OVERRIDES: dict[str, tuple[JsonValue, str]] = {
    # --- страница (СТУ 7.1.2, 7.2) ---
    "page.paper": ("a4", "СТУ 7.1.2; common.page.margins.portrait"),
    "page.margin_top": (20.0, "СТУ 7.1.2; common.page.margins.portrait"),
    "page.margin_bottom": (20.0, "СТУ 7.1.2; common.page.margins.portrait"),
    "page.margin_left": (30.0, "СТУ 7.1.2; common.page.margins.portrait"),
    "page.margin_right": (10.0, "СТУ 7.1.2; common.page.margins.portrait"),
    "page.margin_landscape_top": (30.0, "СТУ 7.1.2; common.page.margins.landscape"),
    "page.margin_landscape_bottom": (10.0, "СТУ 7.1.2; common.page.margins.landscape"),
    "page.margin_landscape_left": (20.0, "СТУ 7.1.2; common.page.margins.landscape"),
    "page.margin_landscape_right": (20.0, "СТУ 7.1.2; common.page.margins.landscape"),
    "page.numbering": ("1", "СТУ 7.2; common.page.numbering"),
    "page.number_align": ("center+bottom", "СТУ 7.2; common.page.numbering"),
    "page.numbering_skip_first": (True, "СТУ 7.2; common.page.numbering"),
    "page.numbering_start": (1, "СТУ 7.2; common.page.numbering"),
    # --- основной текст (СТУ 7.3, common.text) ---
    "document.font": ("Times New Roman", "СТУ 7.3; common.text.font.name"),
    "document.font_size": (14.0, "СТУ 7.3; common.text.font.size"),
    "document.line_spacing": (
        {"mode": "multiplier", "value": 1.5},
        "СТУ 7.3; common.text.line_spacing; AGENTS 5.4",
    ),
    "document.justify": (True, "СТУ 7.3; common.text.alignment"),
    "document.lang": ("ru", "СТУ 7.3; common.text.font.name"),
    "document.hyphenate": ("false", "СТУ 7.3; common.text.hyphenation"),
    "par.first_line_indent": (12.5, "СТУ 7.3; common.text.indent.first_line"),
    "par.spacing": (0.0, "СТУ 7.3; common.text"),
    "par.linebreaks": ("auto", "СТУ 7.3; common.text"),
    # --- заголовки (СТУ 7.4, common.heading.h1-h6) ---
    "heading.numbering": (
        "1.1.1.1.1.1",
        "СТУ 7.4; common.heading.h1-h6",
    ),
    "heading.h1.break_before": (True, "СТУ 7.4; common.heading.h1"),
    "heading.h2.break_before": (False, "СТУ 7.4; common.heading.h2"),
    "heading.h3.break_before": (False, "СТУ 7.4; common.heading.h3"),
    "heading.h4.break_before": (False, "СТУ 7.4; common.heading.h4"),
    "heading.h5.break_before": (False, "СТУ 7.4; common.heading.h5"),
    "heading.h6.break_before": (False, "СТУ 7.4; common.heading.h6"),
    "heading.keep_with_next": (True, "СТУ 7.4; common.heading.h1"),
    # --- списки (СТУ 7.4, common.list) ---
    "bullet_list.marker": (["- ", "- ", "- "], "СТУ 7.4; common.list.bullet"),
    "bullet_list.body_indent": (12.5, "СТУ 7.4; common.list.indent"),
    "numbered_list.numbering": ("1)", "СТУ 7.4; common.list.numbered"),
    "numbered_list.body_indent": (12.5, "СТУ 7.4; common.list.indent"),
    "numbered_list.alphabet": ("ru_sfu", "СТУ 7.4; common.list.lettered"),
    "numbered_list.level_formats": (
        [{"format": "1)"}, {"format": "а)"}, {"format": "1)"}],
        "СТУ 7.4; common.list.numbered; common.list.lettered",
    ),
    # --- рисунки (СТУ 7.8, common.figure) ---
    "figure.width": (165.0, "СТУ 7.8.1; common.figure.image"),
    "figure.fit": ("contain", "СТУ 7.8.1; common.figure.image"),
    "figure.caption_template": (
        "Рисунок {h1}.{n} — {content}",
        "СТУ 7.8.2; common.figure.section_numbering",
    ),
    "figure.caption_position": ("below", "СТУ 7.8.2; common.figure.caption"),
    "figure.caption_align": ("center", "СТУ 7.8.2; common.figure.caption"),
    "figure.caption_separator": (" — ", "СТУ 7.8.2; common.figure.caption"),
    # --- таблицы (СТУ 7.7, common.table) ---
    "table.stroke": (0.1764, "СТУ 7.7.2; common.table.grid"),
    "table.inset": (2.1167, "СТУ 7.7.3; common.table.cell"),
    "table.header_double_line": (True, "СТУ 7.7.2; common.table.header_line"),
    "table.header_double_stroke": (0.2646, "СТУ 7.7.2; common.table.header_line"),
    "table.repeat_header": (True, "СТУ 7.7.2; common.table.header_repeat"),
    "table.italic_letters": (True, "СТУ 7.7.3; common.table.cell"),
    "table.caption_template": (
        "Таблица {h1}.{n} — {content}",
        "СТУ 7.7.3; common.table.section_numbering",
    ),
    "table.caption_position": ("above", "СТУ 7.7.3; common.table.caption"),
    "table.caption_align": ("left", "СТУ 7.7.3; common.table.caption"),
    "table.caption_separator": (" — ", "СТУ 7.7.3; common.table.caption"),
    # --- формулы (СТУ 7.6, common.formula) ---
    "equation.numbering_enabled": (True, "СТУ 7.6; common.formula.section_numbering"),
    "equation.numbering_template": ("({h1}.{n})", "СТУ 7.6; common.formula.section_numbering"),
    "equation.align": ("left", "СТУ 7.6.1; common.formula.body"),
    "equation.body_indent": (12.5, "СТУ 7.6.1; common.formula.body_indent"),
    # --- сноски (СТУ 7.9, common.footnote) ---
    "footnote.marker_format": ("1", "СТУ 7.9; common.footnote"),
    "footnote.separator_length": (30.0, "СТУ 7.9; common.footnote"),
    # --- оглавление (СТУ 6.4, common.toc) ---
    "outline.depth": (4, "СТУ 6.4; common.toc.depth"),
    "outline.indent_mode": ("per_level", "СТУ 6.4; common.toc.indent"),
    "outline.indent_per_level": (
        [{"mm": 0.0}, {"mm": 5.0}, {"mm": 10.0}, {"mm": 15.0}],
        "СТУ 6.4; common.toc.indent",
    ),
    "outline.entry_case": ("none", "СТУ 6.4; common.toc.entries"),
    "outline.omit_when_pages_lte": (24, "СТУ 6.4; common.toc"),
    "outline.appendix_grouping": (True, "СТУ 6.4; common.toc.appendix"),
    "outline.appendix_min_group": (3, "СТУ 6.4; common.toc.appendix"),
    # --- приложения (СТУ 7.5.5, common.appendix) ---
    "appendix.template": ("{service} {letter}. {title}", "СТУ 7.5.5; common.appendix"),
    "appendix.service_case": ("upper", "СТУ 7.5.5; common.appendix"),
    "appendix.title_case": ("none", "СТУ 7.5.5; common.appendix"),
    "appendix.bold": (True, "СТУ 7.5.5; common.appendix"),
    "appendix.alphabet": ("ru_sfu", "СТУ 7.5.5; common.appendix"),
    "appendix.overflow": ("double", "СТУ 7.5.5; common.appendix"),
}

# Шрифт и язык текста по элементам: дефолты реестра — Merriweather/en.
_TEXT_SIZES: dict[str, float] = {
    "par": 14.0,
    "bullet_list": 14.0,
    "numbered_list": 14.0,
    "terms": 14.0,
    "figure": 14.0,
    "equation": 14.0,
    "quote": 14.0,
    "outline": 14.0,
    "table": 12.0,
    "footnote": 12.0,
    "raw": 12.0,
}
_TEXT_SOURCE = "СТУ 7.3; common.text.font.name"

_STRUCTURAL_HEADINGS = (
    "СОДЕРЖАНИЕ",
    "ВВЕДЕНИЕ",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК СОКРАЩЕНИЙ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
)


def _blank_after() -> dict[str, JsonValue]:
    """Одна пустая строка после структурного заголовка (СТУ 7.5)."""
    return {
        "before": [],
        "after": [
            {
                "type": "blank",
                "count": 1,
                "line_spacing": {"mode": "multiplier", "value": 1.0},
            }
        ],
        "before_collisions": [],
    }


def _structural_entity(value: str, *, appendix: bool = False) -> dict[str, JsonValue]:
    """Правило структурного заголовка (AGENTS 5.2, OWNER_DECISIONS 3)."""
    numbering: dict[str, JsonValue] = (
        {
            "kind": "appendix",
            "mode": "own",
            "template": "{letter}",
            "start": 1,
            "sub_template": "{prefix}.{n}",
            "group": "appendix",
        }
        if appendix
        else {
            "kind": "section",
            "mode": "none",
            "template": "1",
            "start": 1,
            "sub_template": "{prefix}.{n}",
            "group": "",
        }
    )
    return {
        "id": "appendix" if appendix else value.lower().replace(" ", "_"),
        "label": value.title(),
        "match": {
            "target": "heading",
            "level": "1",
            # Приложение пишется как «Приложение Название»: буква добавляется
            # шаблоном appendix.template (OWNER_DECISIONS 4).
            "mode": "starts_with" if appendix else "equals",
            "value": "ПРИЛОЖЕНИЕ" if appendix else value,
            "case_insensitive": True,
        },
        "numbering": numbering,
        "apply": {
            "break_before": True,
            "align": "center",
            "case": "upper",
            "bold": True,
            "outlined": True,
            "around": _blank_after(),
            "text_override": {
                "font": "Times New Roman",
                "font_size": 14.0,
                "weight": "regular",
                "style": "normal",
                "fill": "black",
                "lang": "ru",
                "region": None,
                "tracking": 0.0,
                "word_spacing": 100.0,
                "hyphenate": None,
                "ligatures": True,
                "number_type": "auto",
                "number_width": "auto",
            },
        },
    }


def _text_override_values() -> dict[str, tuple[JsonValue, str]]:
    overrides: dict[str, tuple[JsonValue, str]] = {}
    for element, size in _TEXT_SIZES.items():
        overrides[f"{element}.text_override.font"] = ("Times New Roman", _TEXT_SOURCE)
        overrides[f"{element}.text_override.font_size"] = (size, _TEXT_SOURCE)
        overrides[f"{element}.text_override.lang"] = ("ru", _TEXT_SOURCE)
    # Подписи рисунков и таблиц: TNR 14 pt (common.figure.caption/table.caption).
    for element, source in (
        ("figure", "СТУ 7.8.2; common.figure.caption"),
        ("table", "СТУ 7.7.3; common.table.caption"),
        ("equation", "СТУ 7.6.1; common.formula.body"),
    ):
        overrides[f"{element}.caption_text_override"] = (
            {"font": "Times New Roman", "font_size": 14.0, "lang": "ru"},
            source,
        )
    return overrides


def _structural_values() -> dict[str, JsonValue]:
    entities: list[JsonValue] = [
        cast(JsonValue, _structural_entity(value)) for value in _STRUCTURAL_HEADINGS
    ]
    entities.append(cast(JsonValue, _structural_entity("ПРИЛОЖЕНИЕ", appendix=True)))
    return {"structural.entities": entities}


def sfu_overrides() -> dict[str, tuple[JsonValue, str]]:
    """Все отличия профиля СФУ от дефолтов реестра с источниками."""
    merged = dict(SFU_OVERRIDES)
    merged.update(_text_override_values())
    for option_id, value in _structural_values().items():
        merged[option_id] = (value, "СТУ 7.5; common.structural")
    return merged


def build_sfu_values() -> dict[str, JsonValue]:
    """Полный набор значений профиля: дефолты реестра + seed СФУ."""
    values = default_values()
    for option_id, (value, _source) in sfu_overrides().items():
        option = OPTIONS_BY_ID[option_id]
        target: dict[str, JsonValue] = values
        for part in option.path[:-1]:
            child = target.get(part)
            if child is None:
                child = {}
                target[part] = child
            target = cast(dict[str, JsonValue], child)
        target[option.path[-1]] = value
    return values


def profile_metadata() -> dict[str, JsonValue]:
    """Данные для JSON-снимка seed-профиля."""
    overrides = sfu_overrides()
    return {
        "name": SFU_PROFILE_NAME,
        "values": build_sfu_values(),
        "sources": {option_id: source for option_id, (_value, source) in overrides.items()},
    }


__all__ = [
    "SFU_OVERRIDES",
    "SFU_PROFILE_NAME",
    "build_sfu_values",
    "profile_metadata",
    "sfu_overrides",
]
