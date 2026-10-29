"""Реестр опций оформления (G1a).

Каждая опция описывает одно значение профиля: тип, единицы, диапазон, дефолт,
UI-подпись, обоснование, источник и тесты. Опции с path, содержащим
``text_override``, задают необязательный текстовый стиль элемента.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Literal

from app.utils.typst_literals import typst_font

SCHEMA_VERSION = 1

OptionType = Literal[
    "number", "integer", "boolean", "string", "select", "markers", "list", "object"
]
type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]

TEST_IDS = (
    "test_registry_option_contract",
    "test_registry_defaults_match_models",
    "test_registry_covers_orm_fields",
    "test_options_api_roundtrip",
    "test_options_legacy_double_read",
    "test_options_legacy_write_updates_jsonb",
)

# Коэффициент естественной высоты строки (в em) по данным S9. Это данные
# реестра, а не константа fd.typ; для шрифта вне таблицы берётся ручное значение
# опции document.line_height_em.
FONT_LINE_HEIGHT_COEFFICIENTS: dict[str, float] = {
    "libertinus serif": 1.308,
    "pt astra serif": 1.312,
}

# Стандартный leading Typst, нужный для пересчёта множителя в leading.
DEFAULT_LEADING_EM = 0.65


def line_height_coefficient(font: str, manual: float) -> float:
    """Возвращает коэффициент строки: для реально используемого шрифта или ручной."""
    # typst_font раскрывает алиасы (Times New Roman → Libertinus Serif).
    key = typst_font(font).strip().lower()
    return FONT_LINE_HEIGHT_COEFFICIENTS.get(key, manual)


@dataclass(frozen=True)
class Option:
    id: str
    group: str
    applies_to: tuple[str, ...]
    type: OptionType
    default: JsonValue
    path: tuple[str, ...]
    ui: dict[str, JsonValue]
    rationale: str
    source: str
    test_ids: tuple[str, ...] = TEST_IDS
    unit: str | None = None
    allowed_units: tuple[str, ...] = ()
    min: float | None = None
    max: float | None = None
    step: float | None = None
    enum: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    enabled_when: dict[str, JsonValue] | None = None
    nullable: bool = False
    legacy: bool = True
    required: bool = False
    enum_labels: tuple[tuple[str, str], ...] = ()
    fields: tuple[Option, ...] = ()
    item_fields: tuple[Option, ...] = ()
    item_variants: tuple[tuple[str, tuple[str, ...]], ...] = ()


GROUP_LABELS: dict[str, str] = {
    "page": "Страница",
    "document": "Текст",
    "par": "Абзац",
    "heading": "Заголовки",
    "bullet_list": "Маркированный список",
    "numbered_list": "Нумерованный список",
    "terms": "Определения",
    "table": "Таблица",
    "figure": "Изображение",
    "equation": "Формула",
    "quote": "Цитата",
    "footnote": "Сноска",
    "raw": "Код",
    "outline": "Оглавление",
    "around": "Окружение",
    "structural": "Структурные элементы",
    "appendix": "Приложения",
}

SOURCE = {
    "page": "СТУ 7.1.2, 7.2; plan_v2 page.*",
    "document": "СТУ 7.1.1, 7.3; plan_v2 text.*",
    "par": "СТУ 7.3; plan_v2 text.indent.first_line",
    "heading": "СТУ 7.4, 7.5.3; plan_v2 heading.h1–h6",
    "bullet_list": "СТУ 7.4; plan_v2 list.*",
    "numbered_list": "СТУ 7.4; plan_v2 list.*",
    "terms": "plan_v2 §5; элемент terms",
    "table": "СТУ 7.7; plan_v2 table.*",
    "figure": "СТУ 7.8; plan_v2 figure.*",
    "equation": "СТУ 7.6; plan_v2 formula.*",
    "quote": "plan_v2 §5; элемент quote",
    "footnote": "СТУ 7.9; plan_v2 reference.footnote",
    "raw": "plan_v2 §5; элемент raw",
    "outline": "СТУ 6.4; plan_v2 toc.*",
    "around": "СТУ 7.4–7.8; plan_v2 around.*",
    "structural": "СТУ 7.4, 7.5; plan_v2 structural entities; AGENTS 5.2",
    "appendix": "СТУ 7.5.5; plan_v2 appendix; AGENTS 5.2",
}

LENGTH_UNITS = ("mm", "cm", "in", "pt", "em")
MM_UNITS = ("mm", "cm", "in", "pt")
PT_UNITS = ("pt", "em")
PERCENT_UNITS = ("%",)
EM_UNITS = ("em",)

SELECT_LABELS: dict[str, list[tuple[str, str]]] = {
    "weight": [
        ("thin", "Тонкий"),
        ("extralight", "Сверхлёгкий"),
        ("light", "Лёгкий"),
        ("regular", "Обычный"),
        ("medium", "Средний"),
        ("semibold", "Полужирный"),
        ("bold", "Жирный"),
        ("extrabold", "Сверхжирный"),
        ("black", "Чёрный"),
    ],
    "text_style": [("normal", "Обычный"), ("italic", "Курсив"), ("oblique", "Наклонный")],
    "number_type": [("auto", "Авто"), ("lining", "Маюскульные"), ("old-style", "Минускульные")],
    "number_width": [
        ("auto", "Авто"),
        ("proportional", "Пропорциональные"),
        ("tabular", "Табличные"),
    ],
    "spacing": [("auto", "Авто"), ("tight", "Компактный"), ("loose", "Свободный")],
    "outline_indent_mode": [
        ("step", "Шаг на уровень"),
        ("per_level", "Свой отступ на каждый уровень"),
    ],
    "align": [("auto", "Авто"), ("left", "Слева"), ("center", "По центру"), ("right", "Справа")],
    "quotes": [("auto", "Авто"), ("true", "Да"), ("false", "Нет")],
    "hyphenate": [("auto", "Авто"), ("true", "Да"), ("false", "Нет")],
    "page_numbering": [
        ("none", "Нет"),
        ("1", "1, 2, 3…"),
        ("- 1 -", "- 1 -"),
        ("I", "I, II, III…"),
        ("1 / 1", "1 / N"),
    ],
    "number_align_page": [
        ("center+bottom", "Низ по центру"),
        ("right+bottom", "Низ справа"),
        ("left+bottom", "Низ слева"),
        ("center+top", "Верх по центру"),
        ("right+top", "Верх справа"),
    ],
    "number_align_list": [
        ("end+top", "Конец + верх"),
        ("start+top", "Начало + верх"),
        ("end+bottom", "Конец + низ"),
        ("start+bottom", "Начало + низ"),
    ],
    "paper": [
        ("a4", "A4"),
        ("a3", "A3"),
        ("a5", "A5"),
        ("us-letter", "US Letter"),
        ("us-legal", "US Legal"),
        ("us-tabloid", "US Tabloid"),
        ("presentation-16-9", "16:9"),
        ("presentation-4-3", "4:3"),
    ],
    "lang": [
        ("ru", "Русский"),
        ("en", "English"),
        ("de", "Deutsch"),
        ("fr", "Français"),
        ("es", "Español"),
        ("zh", "中文"),
        ("ja", "日本語"),
    ],
    "marker_format": [
        ("1", "1, 2, 3…"),
        ("a", "a, b, c…"),
        ("A", "A, B, C…"),
        ("i", "i, ii, iii…"),
        ("I", "I, II, III…"),
        ("*", "*, **, ***…"),
    ],
    "fit": [("cover", "Покрытие"), ("contain", "Вписать"), ("stretch", "Растянуть")],
    "placement": [
        ("none", "В потоке"),
        ("auto", "Авто"),
        ("top", "Вверху"),
        ("bottom", "Внизу"),
    ],
    "raw_align": [("start", "По началу"), ("center", "По центру"), ("end", "По концу")],
    "theme": [("auto", "Авто"), ("none", "Без подсветки")],
    "linebreaks": [
        ("auto", "Авто"),
        ("simple", "Простой"),
        ("optimized", "Оптимизированный"),
    ],
}

ELEMENT_LABELS: dict[str, str] = {
    "page": "страницы",
    "document": "текста",
    "par": "абзаца",
    "heading": "заголовков",
    "heading_1": "заголовка 1",
    "heading_2": "заголовка 2",
    "heading_3": "заголовка 3",
    "heading_4": "заголовка 4",
    "heading_5": "заголовка 5",
    "heading_6": "заголовка 6",
    "bullet_list": "маркированного списка",
    "numbered_list": "нумерованного списка",
    "terms": "списка определений",
    "table": "таблицы",
    "figure": "изображения",
    "equation": "формулы",
    "quote": "цитаты",
    "footnote": "сноски",
    "raw": "блока кода",
    "outline": "оглавления",
}

HEADING_LEVELS = tuple(range(1, 7))

AROUND_TARGETS: tuple[str, ...] = (
    "heading_1",
    "heading_2",
    "heading_3",
    "heading_4",
    "heading_5",
    "heading_6",
    "par",
    "bullet_list",
    "numbered_list",
    "table",
    "figure",
    "equation",
    "quote",
    "raw",
    "terms",
)

AROUND_TARGET_META: dict[str, tuple[str, str, str]] = {
    "heading_1": ("заголовка 1", "СТУ 7.4.1", "heading.h1"),
    "heading_2": ("заголовка 2", "СТУ 7.4.2", "heading.h2"),
    "heading_3": ("заголовка 3", "СТУ 7.4.3", "heading.h3"),
    "heading_4": ("заголовка 4", "СТУ 7.4.4", "heading.h4"),
    "heading_5": ("заголовка 5", "СТУ 7.4.5", "heading.h5"),
    "heading_6": ("заголовка 6", "СТУ 7.4.6", "heading.h6"),
    "par": ("абзаца", "СТУ 7.3", "text.par"),
    "bullet_list": ("маркированного списка", "СТУ 7.4", "list.bullet"),
    "numbered_list": ("нумерованного списка", "СТУ 7.4", "list.enum"),
    "table": ("таблицы", "СТУ 7.7", "table"),
    "figure": ("рисунка", "СТУ 7.8", "figure"),
    "equation": ("формулы", "СТУ 7.6", "formula"),
    "quote": ("цитаты", "plan_v2 §5", "quote"),
    "raw": ("блока кода", "plan_v2 §5", "raw"),
    "terms": ("списка определений", "plan_v2 §5", "terms"),
}

COLLISION_POLICY_LABELS: tuple[tuple[str, str], ...] = (
    ("keep_previous", "Оставить вставку предыдущего элемента"),
    ("keep_current", "Оставить свою вставку"),
    ("keep_both", "Оставить обе"),
    ("drop_both", "Убрать обе"),
)

COLLISION_PREVIOUS_LABELS: tuple[tuple[str, str], ...] = (
    ("any", "Любой элемент"),
    ("par", "Абзац"),
    ("heading_1", "Заголовок 1"),
    ("heading_2", "Заголовок 2"),
    ("heading_3", "Заголовок 3"),
    ("heading_4", "Заголовок 4"),
    ("heading_5", "Заголовок 5"),
    ("heading_6", "Заголовок 6"),
    ("bullet_list", "Маркированный список"),
    ("numbered_list", "Нумерованный список"),
    ("table", "Таблица"),
    ("figure", "Рисунок"),
    ("equation", "Формула"),
    ("quote", "Цитата"),
    ("raw", "Код"),
    ("terms", "Список определений"),
)

AROUND_ITEM_LABELS: tuple[tuple[str, str], ...] = (
    ("blank", "Пустая строка"),
    ("text", "Текст"),
    ("line", "Линия"),
    ("pagebreak", "Разрыв страницы"),
)
TEXT_OVERRIDE_ELEMENTS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("par", "par", ("par",), ("par",)),
    *(
        (f"h{level}", "heading", ("heading_{0}".format(level),), ("heading_levels", str(level)))
        for level in HEADING_LEVELS
    ),
    ("bullet_list", "bullet_list", ("bullet_list",), ("bullet_list",)),
    ("numbered_list", "numbered_list", ("numbered_list",), ("numbered_list",)),
    ("terms", "terms", ("terms",), ("terms",)),
    ("table", "table", ("table",), ("table",)),
    ("figure", "figure", ("figure",), ("figure",)),
    ("equation", "equation", ("equation",), ("equation",)),
    ("quote", "quote", ("quote",), ("quote",)),
    ("footnote", "footnote", ("footnote",), ("footnote",)),
    ("raw", "raw", ("raw",), ("raw",)),
    ("outline", "outline", ("outline",), ("outline",)),
)

TEXT_OVERRIDE_FIELDS: tuple[tuple[str, OptionType, JsonValue, str, str, tuple[str, ...]], ...] = (
    ("font", "string", "Merriweather", "Шрифт", "", ()),
    ("font_size", "number", 12.0, "Размер шрифта", "pt", PT_UNITS),
    ("weight", "select", "regular", "Насыщенность", "", ()),
    ("style", "select", "normal", "Начертание", "", ()),
    ("fill", "string", "black", "Цвет текста", "", ()),
    ("lang", "select", "en", "Язык", "", ()),
    ("region", "string", None, "Регион", "", ()),
    ("tracking", "number", 0.0, "Межбуквенный интервал", "pt", PT_UNITS),
    ("word_spacing", "number", 100.0, "Межсловный интервал", "%", PERCENT_UNITS),
    ("hyphenate", "select", None, "Переносы", "", ()),
    ("ligatures", "boolean", True, "Лигатуры", "", ()),
    ("number_type", "select", "auto", "Тип цифр", "", ()),
    ("number_width", "select", "auto", "Ширина цифр", "", ()),
)


def _ui(
    label: str,
    group: str,
    control: str,
    order: int,
    enum: tuple[str, ...] = (),
    enum_labels: tuple[tuple[str, str], ...] = (),
    section: str | None = None,
    help_text: str | None = None,
    beta: bool = False,
) -> dict:
    ui: dict[str, JsonValue] = {
        "control": control,
        "label": label,
        "tab": GROUP_LABELS.get(group, group),
        "order": order,
    }
    if beta:
        ui["beta"] = True
    if section:
        ui["section"] = section
    if help_text:
        ui["help"] = help_text
    if enum:
        labels = dict(enum_labels)
        if not labels:
            for values in SELECT_LABELS.values():
                if tuple(value for value, _ in values) == enum:
                    labels = dict(values)
                    break
        ui["options"] = [{"value": value, "label": labels.get(value, value)} for value in enum]
    return ui


def _rationale(label: str, applies_to: str, text_override: bool = False) -> str:
    if text_override:
        return (
            f"Переопределяет «{label}» только для элемента «{ELEMENT_LABELS[applies_to]}»; "
            "без переопределения действует общий стиль текста."
        )
    return (
        f"Настраивает «{label}» для {ELEMENT_LABELS[applies_to]}; "
        "значение хранится в профиле, а не в коде генератора."
    )


def _option(
    id: str,
    group: str,
    applies_to: tuple[str, ...],
    type: OptionType,
    default: JsonValue,
    path: tuple[str, ...],
    label: str,
    *,
    order: int,
    unit: str | None = None,
    allowed_units: tuple[str, ...] = (),
    min: float | None = None,
    max: float | None = None,
    step: float | None = None,
    enum: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    enabled_when: dict[str, JsonValue] | None = None,
    nullable: bool = False,
    rationale: str | None = None,
    source: str | None = None,
    test_ids: tuple[str, ...] | None = None,
    legacy: bool = True,
    required: bool = False,
    enum_labels: tuple[tuple[str, str], ...] = (),
    fields: tuple[Option, ...] = (),
    item_fields: tuple[Option, ...] = (),
    item_variants: tuple[tuple[str, tuple[str, ...]], ...] = (),
    ui_section: str | None = None,
    ui_help: str | None = None,
    beta: bool = False,
) -> Option:
    control = {
        "number": "number",
        "integer": "number",
        "boolean": "toggle",
        "string": "text",
        "select": "select",
        "markers": "markers",
        "list": "list",
        "object": "object",
    }[type]
    return Option(
        id=id,
        group=group,
        applies_to=applies_to,
        type=type,
        default=default,
        path=path,
        ui=_ui(label, group, control, order, enum, enum_labels, ui_section, ui_help, beta),
        rationale=rationale or _rationale(label, applies_to[0]),
        source=source or SOURCE[group],
        unit=unit,
        allowed_units=allowed_units,
        min=min,
        max=max,
        step=step,
        enum=enum,
        depends_on=depends_on,
        enabled_when=enabled_when,
        nullable=nullable,
        test_ids=test_ids or TEST_IDS,
        legacy=legacy,
        required=required,
        enum_labels=enum_labels,
        fields=fields,
        item_fields=item_fields,
        item_variants=item_variants,
    )


def _nested_option(
    key: str,
    type_: OptionType,
    default: JsonValue,
    label: str,
    *,
    order: int,
    unit: str | None = None,
    allowed_units: tuple[str, ...] = (),
    min: float | None = None,
    max: float | None = None,
    step: float | None = None,
    enum: tuple[str, ...] = (),
    enum_labels: tuple[tuple[str, str], ...] = (),
    enabled_when: dict[str, JsonValue] | None = None,
    nullable: bool = False,
    required: bool = False,
    fields: tuple[Option, ...] = (),
    item_fields: tuple[Option, ...] = (),
    item_variants: tuple[tuple[str, tuple[str, ...]], ...] = (),
    id_prefix: str = "around.item",
    group: str = "around",
    applies_to: tuple[str, ...] = ("around",),
    rationale: str | None = None,
    source: str = "plan_v2 around.item; AGENTS 5.1",
    test_ids: tuple[str, ...] = ("test_around_item_schema_contract",),
    ui_help: str | None = None,
) -> Option:
    """Поле вложенной схемы (list/object); не входит в плоский OPTIONS."""
    return _option(
        f"{id_prefix}.{key}",
        group,
        applies_to,
        type_,
        default,
        (key,),
        label,
        order=order,
        unit=unit,
        allowed_units=allowed_units,
        min=min,
        max=max,
        step=step,
        enum=enum,
        enum_labels=enum_labels,
        enabled_when=enabled_when,
        nullable=nullable,
        required=required,
        fields=fields,
        item_fields=item_fields,
        item_variants=item_variants,
        rationale=rationale or f"Поле «{label}» вложенной схемы; задаёт значение без правки кода.",
        source=source,
        test_ids=test_ids,
        legacy=False,
        ui_help=ui_help,
    )


def _around_item_fields() -> tuple[Option, ...]:
    text_override_fields: list[Option] = []
    for order, (field_key, type_, default, label, unit, allowed_units) in enumerate(
        TEXT_OVERRIDE_FIELDS
    ):
        enum: tuple[str, ...] = ()
        if field_key == "weight":
            enum = tuple(v for v, _ in SELECT_LABELS["weight"])
        elif field_key == "style":
            enum = tuple(v for v, _ in SELECT_LABELS["text_style"])
        elif field_key == "lang":
            enum = tuple(v for v, _ in SELECT_LABELS["lang"])
        elif field_key == "hyphenate":
            enum = tuple(v for v, _ in SELECT_LABELS["hyphenate"])
        elif field_key == "number_type":
            enum = tuple(v for v, _ in SELECT_LABELS["number_type"])
        elif field_key == "number_width":
            enum = tuple(v for v, _ in SELECT_LABELS["number_width"])
        text_override_fields.append(
            _nested_option(
                field_key,
                type_,
                copy.deepcopy(default),
                label,
                order=order,
                unit=unit or None,
                allowed_units=allowed_units,
                min=6
                if field_key == "font_size"
                else (-5 if field_key == "tracking" else 0)
                if type_ == "number"
                else None,
                max=72
                if field_key == "font_size"
                else (
                    20
                    if field_key == "tracking"
                    else (500 if field_key == "word_spacing" else None)
                ),
                step=0.5 if field_key == "font_size" else (0.1 if field_key == "tracking" else 5),
                enum=enum,
                nullable=default is None,
            )
        )

    line_spacing = _nested_option(
        "line_spacing",
        "object",
        {"mode": "multiplier", "value": 1.0},
        "Высота пустой строки",
        order=2,
        fields=(
            _nested_option(
                "mode",
                "select",
                "multiplier",
                "Режим",
                order=0,
                enum=("multiplier", "mm"),
                enum_labels=(("multiplier", "Множитель"), ("mm", "Миллиметры")),
            ),
            _nested_option(
                "value",
                "number",
                1.0,
                "Значение",
                order=1,
                min=0,
                max=1000,
                step=0.1,
            ),
        ),
    )
    return (
        _nested_option(
            "type",
            "select",
            "blank",
            "Тип вставки",
            order=0,
            enum=tuple(value for value, _ in AROUND_ITEM_LABELS),
            enum_labels=AROUND_ITEM_LABELS,
            required=True,
        ),
        _nested_option(
            "count",
            "integer",
            1,
            "Количество строк",
            order=1,
            min=0,
            max=1000,
            step=1,
        ),
        line_spacing,
        _nested_option(
            "content",
            "string",
            "",
            "Текст",
            order=3,
            required=True,
        ),
        _nested_option(
            "text_override",
            "object",
            None,
            "Свой стиль текста",
            order=4,
            nullable=True,
            fields=tuple(text_override_fields),
        ),
        _nested_option(
            "align",
            "select",
            "left",
            "Выравнивание",
            order=5,
            enum=("left", "center", "right"),
            enum_labels=(("left", "Слева"), ("center", "По центру"), ("right", "Справа")),
        ),
        _nested_option(
            "length",
            "number",
            100.0,
            "Длина линии",
            order=6,
            unit="%",
            allowed_units=PERCENT_UNITS,
            min=0,
            max=100,
            step=1,
        ),
        _nested_option(
            "stroke_mm",
            "number",
            0.5,
            "Толщина линии",
            order=7,
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=20,
            step=0.05,
        ),
        _nested_option(
            "weak",
            "boolean",
            True,
            "Слабый разрыв",
            order=8,
        ),
    )


def _around_options() -> list[Option]:
    opts: list[Option] = []
    fields = _around_item_fields()
    variants = (
        ("blank", ("count", "line_spacing")),
        ("text", ("content", "text_override", "align")),
        ("line", ("length", "stroke_mm")),
        ("pagebreak", ("weak",)),
    )
    for target in AROUND_TARGETS:
        target_label, stu, rule = AROUND_TARGET_META[target]
        section = (
            f"Заголовок {target.split('_')[-1]}"
            if target.startswith("heading_")
            else GROUP_LABELS[target]
        )
        for side, side_label in (("before", "до"), ("after", "после")):
            opts.append(
                _option(
                    f"around.{target}.{side}",
                    "around",
                    (target,),
                    "list",
                    [],
                    ("around", target, side),
                    f"Вставки {side_label} {target_label}",
                    order=len(opts),
                    item_fields=fields,
                    item_variants=variants,
                    rationale=(
                        f"Задаёт вставки {side_label} {target_label}: пустые строки, текст, "
                        "линию или разрыв страницы. Позволяет воспроизвести практику СТУ "
                        "без правки генератора; пустой список ничего не меняет."
                    ),
                    source=f"{stu}; plan_v2 {rule}; reference: around.{target}.{side}",
                    test_ids=(f"test_around_{target}_options",),
                    legacy=False,
                    ui_section=section,
                )
            )
        opts.append(
            _collision_option(
                f"around.{target}.before_collisions",
                target,
                f"Столкновение вставок перед {target_label}",
                len(opts),
                f"{stu}; plan_v2 {rule}",
                ui_section=section,
            )
        )
    return opts


def _collision_fields() -> tuple[Option, ...]:
    """Поля правила столкновения вставок: вид предыдущего элемента и политика."""
    return (
        _nested_option(
            "previous",
            "select",
            "any",
            "Предыдущий элемент",
            order=0,
            enum=tuple(value for value, _ in COLLISION_PREVIOUS_LABELS),
            enum_labels=COLLISION_PREVIOUS_LABELS,
        ),
        _nested_option(
            "policy",
            "select",
            "keep_both",
            "Политика",
            order=1,
            enum=tuple(value for value, _ in COLLISION_POLICY_LABELS),
            enum_labels=COLLISION_POLICY_LABELS,
        ),
    )


def _collision_option(
    option_id: str,
    target: str,
    label: str,
    order: int,
    source: str,
    ui_section: str | None = None,
) -> Option:
    """Опция before_collisions: первое подходящее правило, иначе keep_both."""
    return _option(
        option_id,
        "around",
        (target,),
        "list",
        [],
        ("around", target, "before_collisions"),
        label,
        order=order,
        item_fields=_collision_fields(),
        rationale=(
            "Задаёт, что делать, когда после предыдущего элемента и перед текущим "
            "одновременно есть вставки: оставить предыдущую, свою, обе или убрать обе. "
            "Пустой список означает «оставить обе»."
        ),
        source=f"{source}; СТУ 7.5.4; AGENTS 5.1; OWNER_DECISIONS 1",
        test_ids=(f"test_around_{target}_options",),
        legacy=False,
        ui_section=ui_section,
        ui_help="Правила проверяются по порядку; первое подходящее по виду предыдущего элемента.",
    )


def _structural_options() -> list[Option]:
    """Структурные сущности (AGENTS 5.2) и оформление приложений."""
    around_fields = _around_item_fields()
    around_variants = (
        ("blank", ("count", "line_spacing")),
        ("text", ("content", "text_override", "align")),
        ("line", ("length", "stroke_mm")),
        ("pagebreak", ("weak",)),
    )
    text_override_field = next(
        field for field in around_fields if field.path[-1] == "text_override"
    )

    def schema_field(
        key: str,
        type_: OptionType,
        default: JsonValue,
        label: str,
        order: int,
        **kwargs: object,
    ) -> Option:
        return _nested_option(
            key,
            type_,
            default,
            label,
            order=order,
            id_prefix="structural.entity",
            group="structural",
            applies_to=("structural",),
            source="AGENTS 5.2; plan_v2 structural entities",
            test_ids=("test_structural_entities_schema",),
            **kwargs,  # type: ignore[arg-type]
        )

    match_fields = (
        schema_field(
            "target",
            "select",
            "heading",
            "Что сопоставлять",
            0,
            enum=("heading",),
            enum_labels=(("heading", "Заголовок"),),
        ),
        schema_field(
            "level",
            "select",
            "any",
            "Уровень заголовка",
            1,
            enum=("any", "1", "2", "3", "4", "5", "6"),
            enum_labels=(
                ("any", "Любой"),
                ("1", "1"),
                ("2", "2"),
                ("3", "3"),
                ("4", "4"),
                ("5", "5"),
                ("6", "6"),
            ),
        ),
        schema_field(
            "mode",
            "select",
            "equals",
            "Способ сравнения",
            2,
            enum=("equals", "contains", "regex"),
            enum_labels=(
                ("equals", "Совпадает"),
                ("contains", "Содержит"),
                ("regex", "Регулярное выражение"),
            ),
        ),
        schema_field("value", "string", "", "Текст для сопоставления", 3, required=True),
        schema_field("case_insensitive", "boolean", True, "Без учёта регистра", 4),
    )
    around_fields_nested = (
        schema_field(
            "before",
            "list",
            [],
            "Вставки до",
            0,
            item_fields=around_fields,
            item_variants=around_variants,
        ),
        schema_field(
            "after",
            "list",
            [],
            "Вставки после",
            1,
            item_fields=around_fields,
            item_variants=around_variants,
        ),
        schema_field(
            "before_collisions",
            "list",
            [],
            "Столкновения вставок",
            2,
            item_fields=_collision_fields(),
        ),
    )
    numbering_fields = (
        schema_field(
            "kind",
            "select",
            "section",
            "Вид правила",
            0,
            enum=("section", "appendix"),
            enum_labels=(
                ("section", "Обычный заголовок"),
                ("appendix", "Приложение (пресет)"),
            ),
        ),
        schema_field(
            "mode",
            "select",
            "continue",
            "Режим нумерации",
            1,
            enum=("none", "continue", "own"),
            enum_labels=(
                ("none", "Без номера"),
                ("continue", "Продолжать общий счётчик"),
                ("own", "Свой счётчик"),
            ),
            enabled_when={"key": "kind", "values": ["section"]},
        ),
        schema_field(
            "template",
            "string",
            "1",
            "Шаблон номера",
            2,
            enabled_when={"key": "kind", "values": ["section"]},
        ),
        schema_field("start", "integer", 1, "Начальный номер", 3, min=1, max=999),
        schema_field(
            "sub_template",
            "string",
            "{prefix}.{n}",
            "Шаблон подзаголовков",
            4,
        ),
        schema_field(
            "group",
            "string",
            "",
            "Общий счётчик (group)",
            5,
            enabled_when={"key": "kind", "values": ["section"]},
        ),
    )
    apply_fields = (
        schema_field("break_before", "boolean", False, "С новой страницы", 1),
        schema_field(
            "align",
            "select",
            "auto",
            "Выравнивание",
            2,
            enum=("auto", "left", "center", "right"),
            enum_labels=(
                ("auto", "Как у заголовка"),
                ("left", "Слева"),
                ("center", "По центру"),
                ("right", "Справа"),
            ),
        ),
        schema_field(
            "case",
            "select",
            "none",
            "Регистр текста",
            3,
            enum=("none", "upper", "lower", "first_upper"),
            enum_labels=(
                ("none", "Не менять"),
                ("upper", "ПРОПИСНЫЕ"),
                ("lower", "строчные"),
                ("first_upper", "С заглавной"),
            ),
            ui_help=(
                "Для приложения применяется после appendix.service_case/title_case "
                "ко всей строке заголовка."
            ),
        ),
        schema_field(
            "bold",
            "boolean",
            False,
            "Полужирный",
            4,
            ui_help="Для приложения действует вместе с appendix.bold (достаточно одного).",
        ),
        schema_field("outlined", "boolean", True, "В оглавлении", 5),
        schema_field(
            "around",
            "object",
            {"before": [], "after": [], "before_collisions": []},
            "Окружение сущности",
            6,
            fields=around_fields_nested,
        ),
        schema_field(
            "text_override",
            "object",
            None,
            "Свой стиль текста",
            7,
            nullable=True,
            fields=text_override_field.fields,
        ),
    )
    entity_fields = (
        schema_field("id", "string", "", "Идентификатор", 0, required=True),
        schema_field("label", "string", "", "Название сущности", 1),
        schema_field("match", "object", {}, "Сопоставление", 2, fields=match_fields),
        schema_field(
            "numbering",
            "object",
            {
                "kind": "section",
                "mode": "continue",
                "template": "1",
                "start": 1,
                "sub_template": "{prefix}.{n}",
                "group": "",
            },
            "Нумерация",
            3,
            fields=numbering_fields,
        ),
        schema_field("apply", "object", {}, "Оформление", 4, fields=apply_fields),
    )
    entities = _option(
        "structural.entities",
        "heading",
        ("structural",),
        "list",
        [],
        ("structural", "entities"),
        "Шаблонные заголовки",
        order=95,
        item_fields=entity_fields,
        rationale=(
            "Список правил «заголовок содержит текст X → оформить так». "
            "Позволяет убрать номер у введения и заключения, задать свой счётчик "
            "приложения, разрыв страницы и регистр без отдельного кода под каждый элемент."
        ),
        source="СТУ 7.4, 7.5; plan_v2 structural entities; AGENTS 5.2",
        test_ids=(
            "test_structural_entities_schema",
            "test_structural_unnumbered_keeps_counter",
            "test_structural_break_before",
            "test_structural_case_render",
            "test_structural_numbering_own",
            "test_structural_numbering_own_group",
            "test_structural_outline_numbering_none",
            "test_structural_outline_outlined_false",
            "test_structural_unnumbered_subheading_has_no_zero_prefix",
            "test_own_letter_template_is_not_appendix",
            "test_appendix_start_and_sub_template",
            "test_appendix_large_start_does_not_overflow",
            "test_appendix_entity_case_and_bold_apply",
            "test_subheading_entity_case_and_bold_apply",
            "test_appendix_numbering_subheadings",
            "test_structural_own_subheadings_use_sub_template",
        ),
        legacy=False,
        beta=True,
        ui_section="Шаблонные заголовки",
    )

    appendix_options = [
        _option(
            "appendix.template",
            "appendix",
            ("appendix",),
            "string",
            "{service} {letter}. {title}",
            ("appendix", "template"),
            "Шаблон заголовка приложения",
            order=0,
            beta=True,
            rationale=(
                "Задаёт вид строки приложения: служебное слово, буква и название "
                "в одной строке; меняется без правки генератора."
            ),
            source="СТУ 7.5.5; plan_v2 appendix.template; AGENTS 5.3",
            test_ids=(
                "test_appendix_options",
                "test_appendix_heading_one_line",
                "test_appendix_custom_template_and_empty_title",
                "test_appendix_template_title_in_any_position",
            ),
            legacy=False,
        ),
        _option(
            "appendix.service_case",
            "appendix",
            ("appendix",),
            "select",
            "upper",
            ("appendix", "service_case"),
            "Регистр служебного слова",
            order=1,
            beta=True,
            enum=("none", "upper", "lower"),
            enum_labels=(("none", "Не менять"), ("upper", "ПРОПИСНЫЕ"), ("lower", "строчные")),
            rationale=(
                "Управляет регистром слова «Приложение» в заголовке; "
                "СТУ печатает служебное слово прописными."
            ),
            source="СТУ 7.5.5; plan_v2 appendix.service_case",
            test_ids=("test_appendix_options", "test_appendix_case_render"),
            legacy=False,
        ),
        _option(
            "appendix.title_case",
            "appendix",
            ("appendix",),
            "select",
            "none",
            ("appendix", "title_case"),
            "Регистр названия",
            order=2,
            beta=True,
            enum=("none", "upper", "lower", "first_upper"),
            enum_labels=(
                ("none", "Не менять"),
                ("upper", "ПРОПИСНЫЕ"),
                ("lower", "строчные"),
                ("first_upper", "С заглавной"),
            ),
            rationale=(
                "Управляет регистром названия приложения, не меняя авторский текст в Markdown."
            ),
            source="СТУ 7.5.5; plan_v2 appendix.title_case",
            test_ids=("test_appendix_options", "test_appendix_case_render"),
            legacy=False,
        ),
        _option(
            "appendix.bold",
            "appendix",
            ("appendix",),
            "boolean",
            False,
            ("appendix", "bold"),
            "Полужирный заголовок",
            order=3,
            beta=True,
            rationale=(
                "Включает полужирное начертание всего заголовка приложения; "
                "в СТУ заголовок приложения выделяется."
            ),
            source="СТУ 7.5.5; plan_v2 appendix.bold",
            test_ids=("test_appendix_options", "test_appendix_bold_render"),
            legacy=False,
        ),
        _option(
            "appendix.alphabet",
            "appendix",
            ("appendix",),
            "select",
            "ru_sfu",
            ("appendix", "alphabet"),
            "Алфавит нумерации приложений",
            order=4,
            beta=True,
            enum=("ru_sfu", "latin", "arabic"),
            enum_labels=(
                ("ru_sfu", "Русский по СТУ (25 букв)"),
                ("latin", "Латинский"),
                ("arabic", "Цифры (1, 2, 3…)"),
            ),
            rationale=(
                "Задаёт нумерацию приложений: ru_sfu — 25 букв без Ё, З, Й, О, "
                "Ч, Ь, Ы, Ъ; latin — A–Z; arabic — 1-based десятичное число "
                "(1, 2, …, 999), а не 0-based цифры."
            ),
            source="СТУ 7.5.5; plan_v2 alphabet ru_sfu",
            test_ids=(
                "test_appendix_options",
                "test_appendix_letter_sequence",
                "test_appendix_arabic_alphabet_is_decimal",
                "test_appendix_latin_letter_sequence",
            ),
            legacy=False,
        ),
        _option(
            "appendix.overflow",
            "appendix",
            ("appendix",),
            "select",
            "double",
            ("appendix", "overflow"),
            "Когда буквы кончились",
            order=5,
            beta=True,
            enum=("double",),
            enum_labels=(("double", "Удваивать (АА, АБ…)"),),
            rationale=(
                "Определяет поведение после 25-й буквы: буквы удваиваются "
                "(АА, АБ…), а после исчерпания удвоения продолжаются в тройном "
                "сочетании, чтобы диапазон start до 999 не ронял компиляцию."
            ),
            source="СТУ 7.5.5; OWNER_DECISIONS 4; plan_v2 alphabet_overflow",
            test_ids=(
                "test_appendix_options",
                "test_appendix_letter_sequence",
                "test_appendix_large_start_does_not_overflow",
            ),
            legacy=False,
        ),
        _option(
            "heading.keep_with_next",
            "heading",
            ("heading",),
            "boolean",
            True,
            ("heading", "keep_with_next"),
            "Не отрывать заголовок от текста",
            order=90,
            rationale=(
                "Заголовок не остаётся один внизу страницы: следующий абзац "
                "переносится вместе с ним. По умолчанию включено."
            ),
            source="СТУ 7.4.6; OWNER_DECISIONS 14",
            test_ids=("test_heading_keep_with_next_render",),
            legacy=False,
        ),
    ]
    return [entities, *appendix_options]


def _spacing_options() -> list[Option]:
    """Штатные интервалы элементов: значения Typst, вынесенные в реестр."""
    opts: list[Option] = []
    o = len

    def add(
        option_id: str,
        group: str,
        target: str,
        path: tuple[str, ...],
        default: float,
        label: str,
        source: str,
        rationale: str,
    ) -> None:
        opts.append(
            _option(
                option_id,
                group,
                (target,),
                "number",
                default,
                path,
                label,
                order=o(opts),
                unit="em",
                allowed_units=EM_UNITS,
                min=0.0,
                max=20.0,
                step=0.01,
                rationale=rationale,
                source=source,
                test_ids=("test_element_spacing_options", "test_element_spacing_render"),
                legacy=False,
            )
        )

    for level in HEADING_LEVELS:
        before = 1.8 if level == 1 else 1.44
        for key, label in (("before", "Отступ до"), ("after", "Отступ после")):
            default = before if key == "before" else 0.75
            add(
                f"heading.h{level}.spacing_{key}",
                "heading",
                f"heading_{level}",
                ("heading_levels", str(level), f"spacing_{key}"),
                default,
                f"{label} заголовка {level}",
                "СТУ 7.4.1; plan_v2 heading.spacing_before",
                (
                    f"Задаёт {label.lower()} заголовка уровня {level}; "
                    "без опции действовал бы скрытый интервал блока Typst."
                ),
            )

    simple = (
        ("figure", "figure", "figure.spacing_before", 1.2, 1.2, "СТУ 7.8"),
        ("table", "table", "table.spacing_before", 1.2, 1.2, "СТУ 7.7"),
        ("equation", "equation", "formula.spacing_before", 1.2, 1.2, "СТУ 7.6"),
        ("quote", "quote", "plan_v2 §5", 2.4, 1.8, "СТУ 7.3"),
        ("raw", "raw", "plan_v2 §5", 1.2, 1.2, "СТУ 7.3"),
        ("terms", "terms", "plan_v2 §5", 1.2, 1.2, "СТУ 7.4"),
        ("bullet_list", "bullet_list", "list", 1.2, 1.2, "СТУ 7.4"),
        ("numbered_list", "numbered_list", "list", 1.2, 1.2, "СТУ 7.4"),
    )
    labels = {
        "figure": "рисунка",
        "table": "таблицы",
        "equation": "формулы",
        "quote": "цитаты",
        "raw": "блока кода",
        "terms": "списка определений",
        "bullet_list": "маркированного списка",
        "numbered_list": "нумерованного списка",
    }
    for group, target, rule, before, after, stu in simple:
        for key, label, default in (
            ("before", "Отступ до", before),
            ("after", "Отступ после", after),
        ):
            add(
                f"{group}.spacing_{key}",
                group,
                target,
                (group, f"spacing_{key}"),
                default,
                f"{label} {labels[group]}",
                f"{stu}; plan_v2 {rule}",
                (
                    f"Задаёт {label.lower()} {labels[group]}; "
                    "без опции действовал бы скрытый интервал блока Typst."
                ),
            )
    return opts


def _caption_options(
    kind: str,
    *,
    default_position: str,
    default_align: str,
    source: str,
    start_order: int,
) -> list[Option]:
    """Опции подписи рисунка или таблицы по одной схеме (AGENTS 5.3)."""
    around_fields = _around_item_fields()
    around_variants = (
        ("blank", ("count", "line_spacing")),
        ("text", ("content", "text_override", "align")),
        ("line", ("length", "stroke_mm")),
        ("pagebreak", ("weak",)),
    )
    text_override_field = next(
        field for field in around_fields if field.path[-1] == "text_override"
    )
    around_object = _option(
        f"{kind}.caption_around",
        kind,
        (kind,),
        "object",
        {"before": [], "after": []},
        (kind, "caption_around"),
        "Окружение подписи",
        order=start_order + 4,
        fields=(
            _nested_option(
                "before",
                "list",
                [],
                "Вставки до подписи",
                order=0,
                id_prefix=f"{kind}.caption",
                group=kind,
                applies_to=(kind,),
                item_fields=around_fields,
                item_variants=around_variants,
                source=source,
                test_ids=(f"test_{kind}_caption_around_render",),
            ),
            _nested_option(
                "after",
                "list",
                [],
                "Вставки после подписи",
                order=1,
                id_prefix=f"{kind}.caption",
                group=kind,
                applies_to=(kind,),
                item_fields=around_fields,
                item_variants=around_variants,
                source=source,
                test_ids=(f"test_{kind}_caption_around_render",),
            ),
        ),
        rationale=(
            "Задаёт вставки до и после текста подписи: пустые строки, текст, "
            "линию или разрыв страницы; пустой список ничего не меняет."
        ),
        source=source,
        test_ids=(f"test_{kind}_caption_around_render",),
        legacy=False,
    )
    text_override_object = _option(
        f"{kind}.caption_text_override",
        kind,
        (kind,),
        "object",
        None,
        (kind, "caption_text_override"),
        "Стиль текста подписи",
        order=start_order + 5,
        nullable=True,
        fields=text_override_field.fields,
        rationale=(
            "Переопределяет шрифт, кегль, начертание и другие свойства только "
            "для текста подписи, не затрагивая сам рисунок или таблицу."
        ),
        source=source,
        test_ids=(f"test_{kind}_caption_text_override_render",),
        legacy=False,
    )
    return [
        _option(
            f"{kind}.caption_template",
            kind,
            (kind,),
            "string",
            None,
            (kind, "caption_template"),
            "Шаблон подписи",
            order=start_order,
            nullable=True,
            rationale=(
                f"Задаёт шаблон подписи {'рисунка' if kind == 'figure' else 'таблицы'}: "
                "{h1}…{h6} — номер раздела или буква приложения, {n} — номер "
                "внутри раздела, {content} — текст подписи. Пустой шаблон "
                "оставляет подпись без автоматического номера."
            ),
            source=source,
            test_ids=(
                f"test_{kind}_caption_render",
                "test_caption_options_schema",
                "test_caption_generation_typst",
            ),
            legacy=False,
        ),
        _option(
            f"{kind}.caption_position",
            kind,
            (kind,),
            "select",
            default_position,
            (kind, "caption_position"),
            "Положение подписи",
            order=start_order + 1,
            enum=("above", "below"),
            enum_labels=(("above", "Над элементом"), ("below", "Под элементом")),
            rationale=(
                f"Определяет, где стоит подпись {'рисунка' if kind == 'figure' else 'таблицы'}: "
                "СТУ требует подпись таблицы над таблицей, подпись рисунка — под рисунком."
            ),
            source=source,
            test_ids=(f"test_{kind}_caption_position_render",),
            legacy=False,
        ),
        _option(
            f"{kind}.caption_align",
            kind,
            (kind,),
            "select",
            default_align,
            (kind, "caption_align"),
            "Выравнивание подписи",
            order=start_order + 2,
            enum=("left", "center", "right"),
            enum_labels=(("left", "Слева"), ("center", "По центру"), ("right", "Справа")),
            rationale=(
                f"Задаёт выравнивание подписи {'рисунка' if kind == 'figure' else 'таблицы'} "
                "без изменения выравнивания самого элемента."
            ),
            source=source,
            test_ids=(f"test_{kind}_caption_align_render",),
            legacy=False,
        ),
        _option(
            f"{kind}.caption_separator",
            kind,
            (kind,),
            "string",
            " — ",
            (kind, "caption_separator"),
            "Разделитель подписи",
            order=start_order + 3,
            rationale=(
                "Вставляется между номером и текстом подписи, если в шаблоне нет "
                "{content}; СТУ использует тире с пробелами."
            ),
            source=source,
            test_ids=(f"test_{kind}_caption_separator_render",),
            legacy=False,
        ),
        around_object,
        text_override_object,
    ]


def _base_options() -> list[Option]:
    opts: list[Option] = []
    o = len
    # Страница
    opts += [
        _option(
            "page.paper",
            "page",
            ("page",),
            "select",
            "a4",
            ("page", "paper"),
            "Формат бумаги",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["paper"]),
        ),
        _option(
            "page.flipped",
            "page",
            ("page",),
            "boolean",
            False,
            ("page", "flipped"),
            "Альбомная ориентация",
            order=o(opts),
        ),
        _option(
            "page.margin_top",
            "page",
            ("page",),
            "number",
            25.0,
            ("page", "margin_top"),
            "Поле сверху",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "page.margin_bottom",
            "page",
            ("page",),
            "number",
            25.0,
            ("page", "margin_bottom"),
            "Поле снизу",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "page.margin_left",
            "page",
            ("page",),
            "number",
            25.0,
            ("page", "margin_left"),
            "Поле слева",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "page.margin_right",
            "page",
            ("page",),
            "number",
            25.0,
            ("page", "margin_right"),
            "Поле справа",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        *(
            _option(
                f"page.margin_landscape_{side}",
                "page",
                ("page",),
                "number",
                25.0,
                ("page", f"margin_landscape_{side}"),
                f"Поле {label} в альбомной ориентации",
                order=o(opts),
                unit="mm",
                allowed_units=MM_UNITS,
                min=0,
                max=100,
                step=0.1,
                rationale=(
                    f"Задаёт поле {label} для альбомной ориентации отдельно от "
                    "книжной; смена ориентации в середине документа не делается."
                ),
                source="СТУ 7.1.2; plan_v2 page.margins.landscape",
                test_ids=("test_page_landscape_options", "test_page_landscape_render"),
                legacy=False,
            )
            for side, label in (
                ("top", "сверху"),
                ("bottom", "снизу"),
                ("left", "слева"),
                ("right", "справа"),
            )
        ),
        _option(
            "page.columns",
            "page",
            ("page",),
            "integer",
            1,
            ("page", "columns"),
            "Колонки",
            order=o(opts),
            min=1,
            max=10,
            step=1,
        ),
        _option(
            "page.numbering",
            "page",
            ("page",),
            "select",
            "none",
            ("page", "numbering"),
            "Нумерация страниц",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["page_numbering"]),
        ),
        _option(
            "page.number_align",
            "page",
            ("page",),
            "select",
            "center+bottom",
            ("page", "number_align"),
            "Позиция номера",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["number_align_page"]),
        ),
        _option(
            "page.numbering_skip_first",
            "page",
            ("page",),
            "boolean",
            False,
            ("page", "numbering_skip_first"),
            "Без номера на первой странице",
            order=o(opts),
            rationale=(
                "Скрывает номер на первой странице, сохраняя её в счёте; "
                "без опции номер печатается на всех страницах."
            ),
            source="СТУ 7.2; plan_v2 page.numbering",
            test_ids=("test_page_numbering_options", "test_page_numbering_render"),
            legacy=False,
        ),
        _option(
            "page.numbering_start",
            "page",
            ("page",),
            "integer",
            1,
            ("page", "numbering_start"),
            "Начальный номер",
            order=o(opts),
            min=1,
            max=999,
            step=1,
            rationale=(
                "Сдвигает отображаемый номер первой страницы; счёт страниц при этом не меняется."
            ),
            source="СТУ 7.2; plan_v2 page.numbering",
            test_ids=("test_page_numbering_options", "test_page_numbering_render"),
            legacy=False,
        ),
    ]
    # Документ
    opts += [
        _option(
            "document.font_size",
            "document",
            ("document",),
            "number",
            12.0,
            ("document", "font_size"),
            "Размер шрифта",
            order=o(opts),
            unit="pt",
            allowed_units=PT_UNITS,
            min=6,
            max=72,
            step=0.5,
        ),
        _option(
            "document.line_spacing",
            "document",
            ("document",),
            "object",
            {"mode": "mm", "value": 5.08},
            ("document", "line_spacing"),
            "Межстрочный интервал",
            order=o(opts),
            fields=(
                _option(
                    "document.line_spacing.mode",
                    "document",
                    ("document",),
                    "select",
                    "mm",
                    ("mode",),
                    "Режим интервала",
                    order=0,
                    enum=("mm", "multiplier"),
                    enum_labels=(("mm", "Миллиметры"), ("multiplier", "Множитель")),
                    rationale=(
                        "Выбирает, задан интервал в миллиметрах или множителем "
                        "естественной высоты строки выбранного шрифта."
                    ),
                    source="СТУ 7.3; AGENTS 5.4; S9",
                    test_ids=("test_document_line_spacing_options",),
                    legacy=False,
                ),
                _option(
                    "document.line_spacing.value",
                    "document",
                    ("document",),
                    "number",
                    5.08,
                    ("value",),
                    "Значение интервала",
                    order=1,
                    min=0.5,
                    max=12.7,
                    step=0.01,
                    rationale=(
                        "Задаёт межстрочный интервал: миллиметры или множитель "
                        "естественной высоты строки (1,5 = полуторный)."
                    ),
                    source="СТУ 7.3; AGENTS 5.4; S9",
                    test_ids=("test_document_line_spacing_options",),
                    legacy=False,
                ),
            ),
            rationale=(
                "Задаёт межстрочный интервал как длину в мм или как множитель "
                "естественной высоты строки; старые значения читаются как мм."
            ),
            source="СТУ 7.3; AGENTS 5.4; S9",
            test_ids=("test_document_line_spacing_options",),
            legacy=False,
        ),
        _option(
            "document.line_height_em",
            "document",
            ("document",),
            "number",
            1.308,
            ("document", "line_height_em"),
            "Коэффициент высоты строки",
            order=o(opts),
            min=0.5,
            max=3.0,
            step=0.001,
            rationale=(
                "Ручной коэффициент естественной высоты строки для шрифта, "
                "которого нет в таблице S9; для известных шрифтов берётся таблица."
            ),
            source="СТУ 7.3; S9; AGENTS 5.4",
            test_ids=("test_document_line_spacing_options",),
            legacy=False,
        ),
        _option(
            "document.font",
            "document",
            ("document",),
            "string",
            "Merriweather",
            ("document", "font"),
            "Шрифт",
            order=o(opts),
        ),
        _option(
            "document.weight",
            "document",
            ("document",),
            "select",
            "regular",
            ("document", "weight"),
            "Насыщенность",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["weight"]),
        ),
        _option(
            "document.style",
            "document",
            ("document",),
            "select",
            "normal",
            ("document", "style"),
            "Начертание",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["text_style"]),
        ),
        _option(
            "document.fill",
            "document",
            ("document",),
            "string",
            "black",
            ("document", "fill"),
            "Цвет текста",
            order=o(opts),
        ),
        _option(
            "document.lang",
            "document",
            ("document",),
            "select",
            "en",
            ("document", "lang"),
            "Язык",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["lang"]),
        ),
        _option(
            "document.region",
            "document",
            ("document",),
            "string",
            None,
            ("document", "region"),
            "Регион",
            order=o(opts),
            nullable=True,
        ),
        _option(
            "document.tracking",
            "document",
            ("document",),
            "number",
            0.0,
            ("document", "tracking"),
            "Межбуквенный интервал",
            order=o(opts),
            unit="pt",
            allowed_units=PT_UNITS,
            min=-5,
            max=20,
            step=0.1,
        ),
        _option(
            "document.word_spacing",
            "document",
            ("document",),
            "number",
            100.0,
            ("document", "word_spacing"),
            "Межсловный интервал",
            order=o(opts),
            unit="%",
            allowed_units=PERCENT_UNITS,
            min=0,
            max=500,
            step=5,
        ),
        _option(
            "document.hyphenate",
            "document",
            ("document",),
            "select",
            None,
            ("document", "hyphenate"),
            "Переносы",
            order=o(opts),
            nullable=True,
            enum=tuple(v for v, _ in SELECT_LABELS["hyphenate"]),
        ),
        _option(
            "document.ligatures",
            "document",
            ("document",),
            "boolean",
            True,
            ("document", "ligatures"),
            "Лигатуры",
            order=o(opts),
        ),
        _option(
            "document.number_type",
            "document",
            ("document",),
            "select",
            "auto",
            ("document", "number_type"),
            "Тип цифр",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["number_type"]),
        ),
        _option(
            "document.number_width",
            "document",
            ("document",),
            "select",
            "auto",
            ("document", "number_width"),
            "Ширина цифр",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["number_width"]),
        ),
        _option(
            "document.justify",
            "document",
            ("document",),
            "boolean",
            False,
            ("document", "justify"),
            "По ширине",
            order=o(opts),
        ),
    ]
    # Абзац
    opts += [
        _option(
            "par.spacing",
            "par",
            ("par",),
            "number",
            4.2333333333,
            ("par", "spacing"),
            "Интервал между абзацами",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "par.first_line_indent",
            "par",
            ("par",),
            "number",
            0.0,
            ("par", "first_line_indent"),
            "Отступ первой строки",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "par.hanging_indent",
            "par",
            ("par",),
            "number",
            0.0,
            ("par", "hanging_indent"),
            "Висячий отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "par.linebreaks",
            "par",
            ("par",),
            "select",
            "auto",
            ("par", "linebreaks"),
            "Разбиение строк",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["linebreaks"]),
        ),
    ]
    # Заголовки
    opts.append(
        _option(
            "heading.numbering",
            "heading",
            ("heading",),
            "string",
            "1.1.1",
            ("heading", "numbering"),
            "Нумерация",
            order=o(opts),
        )
    )
    opts.append(
        _option(
            "heading.unnumbered_indent",
            "heading",
            ("heading",),
            "number",
            -0.3,
            ("heading", "unnumbered_indent"),
            "Компенсация отступа ненумерованного заголовка",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=-2.0,
            max=0.0,
            step=0.01,
            rationale=(
                "Сдвигает ненумерованный заголовок так, чтобы его текст совпал "
                "с началом нумерованного; значение em зависит от кегля."
            ),
            source="S10; СТУ 7.4.1",
            test_ids=("test_heading_unnumbered_indent_option",),
            legacy=False,
        )
    )
    for level in HEADING_LEVELS:
        opts += [
            _option(
                f"heading.h{level}.break_before",
                "heading",
                (f"heading_{level}",),
                "boolean",
                False,
                ("heading_levels", str(level), "break_before"),
                "С новой страницы",
                order=o(opts),
            ),
            _option(
                f"heading.h{level}.numbering_enabled",
                "heading",
                (f"heading_{level}",),
                "boolean",
                True,
                ("heading_levels", str(level), "numbering_enabled"),
                "Нумерация",
                order=o(opts),
            ),
        ]
    # Списки
    opts += [
        _option(
            "bullet_list.tight",
            "bullet_list",
            ("bullet_list",),
            "boolean",
            True,
            ("bullet_list", "tight"),
            "Компактный",
            order=o(opts),
        ),
        _option(
            "bullet_list.marker",
            "bullet_list",
            ("bullet_list",),
            "markers",
            ["- ", "‣", "–"],
            ("bullet_list", "marker"),
            "Маркеры уровней",
            order=o(opts),
        ),
        _option(
            "bullet_list.indent",
            "bullet_list",
            ("bullet_list",),
            "number",
            0.0,
            ("bullet_list", "indent"),
            "Отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "bullet_list.body_indent",
            "bullet_list",
            ("bullet_list",),
            "number",
            2.1166666667,
            ("bullet_list", "body_indent"),
            "Отступ тела",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "bullet_list.spacing",
            "bullet_list",
            ("bullet_list",),
            "select",
            "auto",
            ("bullet_list", "spacing"),
            "Межстрочный интервал",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["spacing"]),
        ),
        _option(
            "bullet_list.tight_spacing",
            "bullet_list",
            ("bullet_list",),
            "number",
            0.5,
            ("bullet_list", "tight_spacing"),
            "Интервал компактного списка",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между пунктами компактного маркированного "
                "списка; ранее 0.5em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=("test_list_spacing_options",),
            legacy=False,
        ),
        _option(
            "bullet_list.loose_spacing",
            "bullet_list",
            ("bullet_list",),
            "number",
            1.0,
            ("bullet_list", "loose_spacing"),
            "Интервал некомпактного списка",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между пунктами некомпактного маркированного "
                "списка; ранее 1em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=("test_list_spacing_options",),
            legacy=False,
        ),
        _option(
            "numbered_list.tight",
            "numbered_list",
            ("numbered_list",),
            "boolean",
            True,
            ("numbered_list", "tight"),
            "Компактный",
            order=o(opts),
            test_ids=("test_numbered_list_spacing_render",),
        ),
        _option(
            "numbered_list.indent",
            "numbered_list",
            ("numbered_list",),
            "number",
            0.0,
            ("numbered_list", "indent"),
            "Отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "numbered_list.body_indent",
            "numbered_list",
            ("numbered_list",),
            "number",
            2.1166666667,
            ("numbered_list", "body_indent"),
            "Отступ тела",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "numbered_list.spacing",
            "numbered_list",
            ("numbered_list",),
            "select",
            "auto",
            ("numbered_list", "spacing"),
            "Межстрочный интервал",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["spacing"]),
            test_ids=("test_numbered_list_spacing_render",),
        ),
        _option(
            "numbered_list.tight_spacing",
            "numbered_list",
            ("numbered_list",),
            "number",
            0.5,
            ("numbered_list", "tight_spacing"),
            "Интервал компактного списка",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между пунктами компактного нумерованного "
                "списка; ранее 0.5em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=(
                "test_list_spacing_options",
                "test_numbered_list_tight_loose_spacing_values_render",
            ),
            legacy=False,
        ),
        _option(
            "numbered_list.loose_spacing",
            "numbered_list",
            ("numbered_list",),
            "number",
            1.0,
            ("numbered_list", "loose_spacing"),
            "Интервал некомпактного списка",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между пунктами некомпактного нумерованного "
                "списка; ранее 1em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=(
                "test_list_spacing_options",
                "test_numbered_list_tight_loose_spacing_values_render",
            ),
            legacy=False,
        ),
        _option(
            "numbered_list.numbering",
            "numbered_list",
            ("numbered_list",),
            "string",
            "1.",
            ("numbered_list", "numbering"),
            "Формат нумерации",
            order=o(opts),
        ),
        _option(
            "numbered_list.level_formats",
            "numbered_list",
            ("numbered_list",),
            "list",
            [],
            ("numbered_list", "level_formats"),
            "Форматы по уровням",
            order=o(opts),
            item_fields=(
                _nested_option(
                    "format",
                    "string",
                    "{n}.",
                    "Формат уровня",
                    order=0,
                    id_prefix="numbered_list.level_format",
                    group="numbered_list",
                    applies_to=("numbered_list",),
                    source="СТУ 7.4.3; plan_v2 list.nested_numeric, list.lettered",
                    test_ids=("test_numbered_list_level_formats_render",),
                    ui_help=(
                        "{n} — номер, {letter} — буква выбранного алфавита; "
                        "можно использовать обычный шаблон Typst, например 1)."
                    ),
                ),
            ),
            rationale=(
                "Задаёт формат маркера отдельно для каждого уровня вложенности: "
                "например, 1. на первом уровне и {letter}) на втором. Пустой "
                "список сохраняет общий numbered_list.numbering."
            ),
            source="СТУ 7.4.3; plan_v2 list.nested_numeric, list.lettered; AGENTS 5.3",
            test_ids=(
                "test_numbered_list_options_schema",
                "test_numbered_list_level_formats_render",
                "test_numbered_list_level_format_repeat_render",
                "test_numbered_list_full_render",
            ),
            legacy=False,
            ui_help="Порядок элементов — уровни вложенности; для более глубоких уровней повторяется последний формат.",
        ),
        _option(
            "numbered_list.alphabet",
            "numbered_list",
            ("numbered_list",),
            "select",
            "ru_sfu",
            ("numbered_list", "alphabet"),
            "Алфавит букв",
            order=o(opts),
            enum=("ru_sfu", "latin"),
            enum_labels=(("ru_sfu", "Русский по СТУ (25 букв)"), ("latin", "Латинский")),
            rationale=(
                "Определяет буквы для плейсхолдера {letter} в форматах уровней: "
                "ru_sfu исключает Ё, З, Й, О, Ч, Ь, Ы, Ъ."
            ),
            source="СТУ 7.4.3; plan_v2 list.lettered; SPIKE S7",
            test_ids=(
                "test_numbered_list_level_formats_render",
                "test_numbered_list_alphabet_latin_render",
            ),
            legacy=False,
        ),
        _option(
            "numbered_list.wrap_mode",
            "numbered_list",
            ("numbered_list",),
            "select",
            "left_margin",
            ("numbered_list", "wrap_mode"),
            "Перенос строки пункта",
            order=o(opts),
            enum=("left_margin", "body_text"),
            enum_labels=(
                ("left_margin", "К левому полю"),
                ("body_text", "По тексту первой строки"),
            ),
            rationale=(
                "Выбирает, как выравнивать продолжение пункта списка: к левому "
                "краю списка или по тексту первой строки (висячий отступ)."
            ),
            source="СТУ 7.4.3; plan_v2 list.item; OWNER_DECISIONS 3",
            test_ids=("test_numbered_list_wrap_mode_render",),
            legacy=False,
        ),
        _option(
            "numbered_list.start",
            "numbered_list",
            ("numbered_list",),
            "integer",
            None,
            ("numbered_list", "start"),
            "Начальный номер",
            order=o(opts),
            min=0,
            step=1,
            nullable=True,
        ),
        _option(
            "numbered_list.full",
            "numbered_list",
            ("numbered_list",),
            "boolean",
            False,
            ("numbered_list", "full"),
            "Полная нумерация",
            order=o(opts),
        ),
        _option(
            "numbered_list.reversed",
            "numbered_list",
            ("numbered_list",),
            "boolean",
            False,
            ("numbered_list", "reversed"),
            "Обратный порядок",
            order=o(opts),
        ),
        _option(
            "numbered_list.number_align",
            "numbered_list",
            ("numbered_list",),
            "select",
            "end+top",
            ("numbered_list", "number_align"),
            "Выравнивание номера",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["number_align_list"]),
            test_ids=(
                "test_numbered_list_number_align_render",
                "test_numbered_list_number_align_bottom_left_margin_no_overlap_render",
            ),
        ),
        _option(
            "terms.tight",
            "terms",
            ("terms",),
            "boolean",
            True,
            ("terms", "tight"),
            "Компактный",
            order=o(opts),
        ),
        _option(
            "terms.indent",
            "terms",
            ("terms",),
            "number",
            0.0,
            ("terms", "indent"),
            "Отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "terms.hanging_indent",
            "terms",
            ("terms",),
            "number",
            8.4666666667,
            ("terms", "hanging_indent"),
            "Висячий отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "terms.spacing",
            "terms",
            ("terms",),
            "select",
            "auto",
            ("terms", "spacing"),
            "Интервал",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["spacing"]),
        ),
        _option(
            "terms.tight_spacing",
            "terms",
            ("terms",),
            "number",
            0.5,
            ("terms", "tight_spacing"),
            "Интервал компактного списка определений",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между терминами компактного списка "
                "определений; ранее 0.5em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=("test_list_spacing_options",),
            legacy=False,
        ),
        _option(
            "terms.loose_spacing",
            "terms",
            ("terms",),
            "number",
            1.0,
            ("terms", "loose_spacing"),
            "Интервал некомпактного списка определений",
            order=o(opts),
            unit="em",
            allowed_units=EM_UNITS,
            min=0.0,
            max=5.0,
            step=0.01,
            rationale=(
                "Задаёт расстояние между терминами некомпактного списка "
                "определений; ранее 1em было зашито в fd.typ."
            ),
            source="AGENTS G2b; S1; СТУ 7.4",
            test_ids=("test_list_spacing_options",),
            legacy=False,
        ),
    ]
    # Таблица, изображение, цитата, сноска, код, оглавление
    opts += [
        _option(
            "table.stroke",
            "table",
            ("table",),
            "number",
            0.1763888889,
            ("table", "stroke"),
            "Толщина линий",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=20,
            step=0.01,
        ),
        _option(
            "table.align",
            "table",
            ("table",),
            "select",
            "auto",
            ("table", "align"),
            "Выравнивание",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["align"]),
        ),
        _option(
            "table.inset",
            "table",
            ("table",),
            "number",
            1.7638888889,
            ("table", "inset"),
            "Отступ ячеек",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.05,
        ),
        _option(
            "table.fill",
            "table",
            ("table",),
            "string",
            "none",
            ("table", "fill"),
            "Заливка",
            order=o(opts),
        ),
        *_caption_options(
            "table",
            default_position="above",
            default_align="left",
            source="СТУ 7.7.3, 7.7.5; plan_v2 table.caption; AGENTS 5.3",
            start_order=o(opts),
        ),
        _option(
            "figure.width",
            "figure",
            ("figure",),
            "number",
            4.2333333333,
            ("figure", "width"),
            "Ширина",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=1000,
            step=0.1,
        ),
        _option(
            "figure.height",
            "figure",
            ("figure",),
            "number",
            0.0,
            ("figure", "height"),
            "Высота",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=1000,
            step=0.1,
        ),
        _option(
            "figure.placement",
            "figure",
            ("figure",),
            "select",
            "none",
            ("figure", "placement"),
            "Размещение",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["placement"]),
        ),
        _option(
            "figure.gap",
            "figure",
            ("figure",),
            "number",
            2.7516666667,
            ("figure", "gap"),
            "Зазор до подписи",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.05,
        ),
        _option(
            "figure.outlined",
            "figure",
            ("figure",),
            "boolean",
            True,
            ("figure", "outlined"),
            "В списке фигур",
            order=o(opts),
        ),
        _option(
            "figure.fit",
            "figure",
            ("figure",),
            "select",
            "cover",
            ("figure", "fit"),
            "Подгонка",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["fit"]),
        ),
        *_caption_options(
            "figure",
            default_position="below",
            default_align="center",
            source="СТУ 7.8.2, 7.8.3; plan_v2 figure.caption; AGENTS 5.3",
            start_order=o(opts),
        ),
        _option(
            "equation.body_indent",
            "equation",
            ("equation",),
            "number",
            0.0,
            ("equation", "body_indent"),
            "Отступ формулы",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
            rationale=(
                "Сдвигает блочную формулу вправо от левого поля; без опции "
                "действует центрирование Typst."
            ),
            source="СТУ 7.6.1; plan_v2 formula.body_indent",
            test_ids=("test_equation_body_indent_options", "test_equation_body_indent_render"),
            legacy=False,
        ),
        _option(
            "quote.indent",
            "quote",
            ("quote",),
            "number",
            6.35,
            ("quote", "indent"),
            "Отступ",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "quote.block",
            "quote",
            ("quote",),
            "boolean",
            True,
            ("quote", "block"),
            "Блочная цитата",
            order=o(opts),
        ),
        _option(
            "quote.quotes",
            "quote",
            ("quote",),
            "select",
            "auto",
            ("quote", "quotes"),
            "Кавычки",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["quotes"]),
        ),
        _option(
            "footnote.marker_format",
            "footnote",
            ("footnote",),
            "select",
            "1",
            ("footnote", "marker_format"),
            "Формат маркера",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["marker_format"]),
        ),
        _option(
            "footnote.clearance",
            "footnote",
            ("footnote",),
            "number",
            4.2333333333,
            ("footnote", "clearance"),
            "Расстояние до сносок",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "footnote.gap",
            "footnote",
            ("footnote",),
            "number",
            2.1166666667,
            ("footnote", "gap"),
            "Расстояние между записями",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "footnote.indent",
            "footnote",
            ("footnote",),
            "number",
            4.2333333333,
            ("footnote", "indent"),
            "Отступ записи",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
        ),
        _option(
            "footnote.separator_length",
            "footnote",
            ("footnote",),
            "number",
            30.0,
            ("footnote", "separator_length"),
            "Длина разделительной линии",
            order=o(opts),
            unit="%",
            allowed_units=PERCENT_UNITS,
            min=0,
            max=100,
            step=1,
            rationale=("Задаёт длину линии над сносками; без опции Typst рисует линию 30% ширины."),
            source="СТУ 7.9; plan_v2 reference.footnote",
            test_ids=("test_footnote_separator_options", "test_footnote_separator_render"),
            legacy=False,
        ),
        _option(
            "footnote.separator_stroke",
            "footnote",
            ("footnote",),
            "number",
            0.1764,
            ("footnote", "separator_stroke"),
            "Толщина разделительной линии",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=5,
            step=0.01,
            rationale=(
                "Задаёт толщину линии над сносками; значение по умолчанию равно 0,5 pt Typst."
            ),
            source="СТУ 7.9; plan_v2 reference.footnote",
            test_ids=("test_footnote_separator_options", "test_footnote_separator_render"),
            legacy=False,
        ),
        _option(
            "raw.tab_size",
            "raw",
            ("raw",),
            "integer",
            2,
            ("raw", "tab_size"),
            "Размер табуляции",
            order=o(opts),
            min=1,
            max=16,
            step=1,
        ),
        _option(
            "raw.align",
            "raw",
            ("raw",),
            "select",
            "start",
            ("raw", "align"),
            "Выравнивание",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["raw_align"]),
        ),
        _option(
            "raw.theme",
            "raw",
            ("raw",),
            "select",
            "auto",
            ("raw", "theme"),
            "Тема подсветки",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["theme"]),
        ),
        _option(
            "outline.depth",
            "outline",
            ("outline",),
            "integer",
            None,
            ("outline", "depth"),
            "Глубина",
            order=o(opts),
            min=1,
            max=10,
            step=1,
            nullable=True,
        ),
        _option(
            "outline.indent_mode",
            "outline",
            ("outline",),
            "select",
            "step",
            ("outline", "indent_mode"),
            "Режим отступа вложенности",
            order=o(opts),
            enum=tuple(v for v, _ in SELECT_LABELS["outline_indent_mode"]),
            rationale=(
                "Выбирает, как считается отступ подзаголовков в оглавлении: "
                "единый шаг на уровень или отдельное значение для каждого уровня."
            ),
            source="СТУ 6.4; plan_v2 toc.indent; OWNER_DECISIONS 9",
            test_ids=(
                "test_outline_indent_modes_config",
                "test_outline_indent_rejects_arbitrary_strings",
                "test_outline_indent_render",
            ),
            legacy=False,
        ),
        _option(
            "outline.indent_mm",
            "outline",
            ("outline",),
            "number",
            0.0,
            ("outline", "indent_mm"),
            "Шаг отступа, мм",
            order=o(opts),
            unit="mm",
            allowed_units=MM_UNITS,
            min=0,
            max=100,
            step=0.1,
            depends_on=("outline.indent_mode",),
            rationale=(
                "Задаёт шаг отступа в миллиметрах: отступ уровня равен "
                "(уровень − 1) × значение; применяется в режиме «Шаг на уровень»."
            ),
            source="СТУ 6.4; plan_v2 toc.indent; OWNER_DECISIONS 9",
            test_ids=(
                "test_outline_indent_modes_config",
                "test_outline_indent_rejects_arbitrary_strings",
                "test_outline_indent_render",
            ),
            legacy=False,
        ),
        _option(
            "outline.indent_per_level",
            "outline",
            ("outline",),
            "list",
            [
                {"mm": 0.0},
                {"mm": 5.0},
                {"mm": 10.0},
                {"mm": 15.0},
                {"mm": 20.0},
                {"mm": 25.0},
            ],
            ("outline", "indent_per_level"),
            "Отступы по уровням, мм",
            order=o(opts),
            item_fields=(
                _nested_option(
                    "mm",
                    "number",
                    0.0,
                    "Отступ, мм",
                    order=0,
                    unit="mm",
                    allowed_units=MM_UNITS,
                    min=0,
                    max=100,
                    step=0.1,
                ),
            ),
            depends_on=("outline.indent_mode",),
            rationale=(
                "Задаёт отдельный отступ для каждого уровня оглавления; "
                "применяется в режиме «Свой отступ на каждый уровень»."
            ),
            source="СТУ 6.4; plan_v2 toc.indent; OWNER_DECISIONS 9",
            test_ids=(
                "test_outline_indent_modes_config",
                "test_outline_indent_rejects_arbitrary_strings",
                "test_outline_indent_render",
                "test_outline_empty_per_level_does_not_crash",
            ),
            legacy=False,
        ),
    ]
    opts += _spacing_options()
    return opts


def _text_override_options() -> list[Option]:
    opts: list[Option] = []
    for element_key, group, applies_to, path_prefix in TEXT_OVERRIDE_ELEMENTS:
        for order, (field_key, type_, default, label, unit, allowed_units) in enumerate(
            TEXT_OVERRIDE_FIELDS
        ):
            enum: tuple[str, ...] = ()
            if field_key == "weight":
                enum = tuple(v for v, _ in SELECT_LABELS["weight"])
            elif field_key == "style":
                enum = tuple(v for v, _ in SELECT_LABELS["text_style"])
            elif field_key == "lang":
                enum = tuple(v for v, _ in SELECT_LABELS["lang"])
            elif field_key == "hyphenate":
                enum = tuple(v for v, _ in SELECT_LABELS["hyphenate"])
            elif field_key == "number_type":
                enum = tuple(v for v, _ in SELECT_LABELS["number_type"])
            elif field_key == "number_width":
                enum = tuple(v for v, _ in SELECT_LABELS["number_width"])
            option = _option(
                f"{element_key}.text_override.{field_key}",
                group,
                applies_to,
                type_,
                copy.deepcopy(default),
                (*path_prefix, "text_override", field_key),
                label,
                order=100 + order,
                unit=unit or None,
                allowed_units=allowed_units,
                min=6
                if field_key == "font_size"
                else (-5 if field_key == "tracking" else 0)
                if type_ == "number"
                else None,
                max=72
                if field_key == "font_size"
                else (
                    20
                    if field_key == "tracking"
                    else (500 if field_key == "word_spacing" else None)
                ),
                step=0.5 if field_key == "font_size" else (0.1 if field_key == "tracking" else 5),
                enum=enum,
                nullable=default is None,
                rationale=_rationale(label, applies_to[0], text_override=True),
            )
            opts.append(option)
    return opts


OPTIONS: tuple[Option, ...] = tuple(
    _base_options() + _text_override_options() + _around_options() + _structural_options()
)
OPTIONS_BY_ID: dict[str, Option] = {option.id: option for option in OPTIONS}
OPTIONS_BY_PATH: dict[tuple[str, ...], Option] = {option.path: option for option in OPTIONS}
ELEMENT_PATHS: tuple[str, ...] = (
    "page",
    "document",
    "par",
    "heading",
    "bullet_list",
    "numbered_list",
    "terms",
    "table",
    "figure",
    "equation",
    "quote",
    "footnote",
    "raw",
    "outline",
    "structural",
    "appendix",
)
