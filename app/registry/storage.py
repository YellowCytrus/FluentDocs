"""Хранение и сериализация значений реестра опций.

JSONB-значения профиля имеют вложенную форму::

    {
      "page": {"paper": "a4", ...},
      "heading_levels": {"1": {"break_before": false, ...}, ...},
      "par": {"spacing": 4.23, "text_override": null | {...}},
      ...
    }

Здесь же — двойное чтение (JSONB → старые таблицы) и запись в оба места.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.registry.options import (
    AROUND_TARGETS,
    DEFAULT_LEADING_EM,
    ELEMENT_PATHS,
    HEADING_LEVELS,
    OPTIONS,
    OPTIONS_BY_PATH,
    SCHEMA_VERSION,
    TEXT_OVERRIDE_ELEMENTS,
    TEXT_OVERRIDE_FIELDS,
    JsonValue,
    Option,
    line_height_coefficient,
)
from app.repositories.profile_repository import ProfileRepository
from app.repositories.style_repository import StyleRepository

_MISSING = object()


class RegistryError(ValueError):
    """Некорректное значение или неизвестная опция."""


class RegistryVersionError(RegistryError):
    """Версия схемы JSONB не поддерживается."""


# element -> (orm model, relationship name on Profile)
ELEMENT_MODELS: dict[str, tuple[type[object], str]] = {
    "page": (PageStyle, "page_style"),
    "document": (DocumentStyle, "document_style"),
    "par": (ParStyle, "par_style"),
    "heading": (HeadingStyle, "heading_style"),
    "bullet_list": (BulletListStyle, "bullet_list_style"),
    "numbered_list": (NumberedListStyle, "numbered_list_style"),
    "terms": (TermsStyle, "terms_style"),
    "table": (TableStyle, "table_style"),
    "figure": (FigureStyle, "figure_style"),
    "equation": (EquationStyle, "equation_style"),
    "quote": (QuoteStyle, "quote_style"),
    "footnote": (FootnoteStyle, "footnote_style"),
    "raw": (RawStyle, "raw_style"),
    "outline": (OutlineStyle, "outline_style"),
}

TO_ELEMENT_PREFIXES: tuple[tuple[str, ...], ...] = tuple(
    prefix for _, _, _, prefix in TEXT_OVERRIDE_ELEMENTS
)
TO_FIELD_NAMES: tuple[str, ...] = tuple(field[0] for field in TEXT_OVERRIDE_FIELDS)


def _get_path(values: Mapping[str, JsonValue], path: tuple[str, ...]) -> JsonValue:
    current: JsonValue = cast(JsonValue, values)
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return cast(JsonValue, _MISSING)
        current = current[key]
    return current


def _set_path(values: dict[str, JsonValue], path: tuple[str, ...], value: JsonValue) -> None:
    current: dict[str, JsonValue] = values
    for key in path[:-1]:
        nested = current.get(key)
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested
    current[path[-1]] = value


def default_values() -> dict[str, JsonValue]:
    """Полный набор значений по умолчанию для всех опций реестра."""
    values: dict[str, JsonValue] = {element: {} for element in ELEMENT_PATHS}
    values["heading_levels"] = {str(level): {} for level in HEADING_LEVELS}
    values["around"] = {}
    for option in OPTIONS:
        if "text_override" in option.path:
            continue
        _set_path(values, option.path, copy.deepcopy(option.default))
    for prefix in TO_ELEMENT_PREFIXES:
        _set_path(values, (*prefix, "text_override"), None)
    return values


def _schema_key(field: Option) -> str:
    """Ключ вложенного поля: последний сегмент его path."""
    return field.path[-1]


def validate_value(option: Option, value: JsonValue) -> JsonValue:
    """Проверяет одно значение по описанию опции и возвращает каноническую форму."""
    # Старые профили хранили интервал одним числом миллиметров.
    if option.id == "document.line_spacing" and isinstance(value, (int, float)):
        if isinstance(value, bool):
            raise RegistryError(f"Опция {option.id}: ожидается число")
        value = {"mode": "mm", "value": float(value)}
    if value is None:
        if option.nullable or option.default is None:
            return None
        raise RegistryError(f"Опция {option.id} не допускает null")

    if option.type in {"number", "integer"}:
        if isinstance(value, bool):
            raise RegistryError(f"Опция {option.id}: ожидается число")
        if option.type == "integer":
            if not isinstance(value, int):
                raise RegistryError(f"Опция {option.id}: ожидается целое число")
        elif not isinstance(value, (int, float)):
            raise RegistryError(f"Опция {option.id}: ожидается число")
        if option.min is not None and value < option.min:
            raise RegistryError(f"Опция {option.id}: меньше минимума {option.min}")
        if option.max is not None and value > option.max:
            raise RegistryError(f"Опция {option.id}: больше максимума {option.max}")
        return value

    if option.type == "boolean":
        if not isinstance(value, bool):
            raise RegistryError(f"Опция {option.id}: ожидается boolean")
        return value

    if option.type == "string":
        if not isinstance(value, str):
            raise RegistryError(f"Опция {option.id}: ожидается строка")
        return value

    if option.type == "markers":
        if (
            not isinstance(value, list)
            or not 1 <= len(value) <= 3
            or not all(isinstance(item, str) for item in value)
        ):
            raise RegistryError(f"Опция {option.id}: ожидается список из 1–3 строк")
        return list(value)

    if option.type == "object":
        if not isinstance(value, Mapping):
            raise RegistryError(f"Опция {option.id}: ожидается объект")
        if not option.fields:
            raise RegistryError(f"Опция {option.id}: пустая схема объекта")
        known = {_schema_key(field) for field in option.fields}
        unknown = set(value) - known
        if unknown:
            raise RegistryError(f"Опция {option.id}: неизвестные поля {sorted(unknown)}")
        normalized: dict[str, JsonValue] = {}
        for field in option.fields:
            if _schema_key(field) in value:
                normalized[_schema_key(field)] = validate_value(
                    field, cast(JsonValue, value[_schema_key(field)])
                )
            elif field.required:
                raise RegistryError(f"Опция {option.id}: обязательно поле {_schema_key(field)}")
            else:
                normalized[_schema_key(field)] = copy.deepcopy(field.default)
        if option.id == "document.line_spacing":
            mode = normalized["mode"]
            spacing = normalized["value"]
            if mode == "multiplier" and not 0.5 <= float(spacing) <= 3.0:
                raise RegistryError(
                    "document.line_spacing: множитель должен быть в диапазоне 0.5–3.0"
                )
            if mode == "mm" and not 2.116 <= float(spacing) <= 12.7:
                raise RegistryError(
                    "document.line_spacing: миллиметры должны быть в диапазоне 2.116–12.7"
                )
        return normalized

    if option.type == "list":
        if not isinstance(value, list):
            raise RegistryError(f"Опция {option.id}: ожидается список")
        if not option.item_fields:
            raise RegistryError(f"Опция {option.id}: пустая схема элемента списка")
        normalized_items: list[JsonValue] = []
        variants = dict(option.item_variants)
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                raise RegistryError(f"Опция {option.id}[{index}]: ожидается объект")
            if variants:
                variant = item.get("type")
                if not isinstance(variant, str) or variant not in variants:
                    raise RegistryError(
                        f"Опция {option.id}[{index}]: недопустимый type {variant!r}"
                    )
                allowed = {"type", *variants[variant]}
                unknown = set(item) - allowed
                if unknown:
                    raise RegistryError(
                        f"Опция {option.id}[{index}]: неизвестные поля {sorted(unknown)}"
                    )
            else:
                variant = None
                allowed = {_schema_key(field) for field in option.item_fields}
                unknown = set(item) - allowed
                if unknown:
                    raise RegistryError(
                        f"Опция {option.id}[{index}]: неизвестные поля {sorted(unknown)}"
                    )
            normalized_item: dict[str, JsonValue] = {}
            if variant is not None:
                normalized_item["type"] = variant
            for field in option.item_fields:
                if variant is not None and _schema_key(field) not in allowed:
                    continue
                if _schema_key(field) in item:
                    normalized_item[_schema_key(field)] = validate_value(
                        field, cast(JsonValue, item[_schema_key(field)])
                    )
                elif field.required:
                    raise RegistryError(
                        f"Опция {option.id}[{index}]: обязательно поле {_schema_key(field)}"
                    )
                else:
                    normalized_item[_schema_key(field)] = copy.deepcopy(field.default)
            normalized_items.append(normalized_item)
        return normalized_items

    if option.type == "select":
        # Переносы в старых таблицах хранятся как bool | null.
        if option.path[-1] == "hyphenate":
            if isinstance(value, bool):
                return "true" if value else "false"
            if value == "auto":
                return None
            if value in {"true", "false"}:
                return value
            raise RegistryError(f"Опция {option.id}: недопустимое значение {value!r}")
        if not isinstance(value, str) or value not in option.enum:
            raise RegistryError(f"Опция {option.id}: недопустимое значение {value!r}")
        return value

    raise RegistryError(f"Опция {option.id}: неизвестный тип {option.type}")


def _normalize_text_override(
    prefix: tuple[str, ...],
    raw: JsonValue,
    values: dict[str, JsonValue],
) -> None:
    if raw is None:
        _set_path(values, (*prefix, "text_override"), None)
        return
    if not isinstance(raw, Mapping):
        raise RegistryError("text_override должен быть объектом или null")

    normalized: dict[str, JsonValue] = {}
    for field in TO_FIELD_NAMES:
        option = OPTIONS_BY_PATH[(*prefix, "text_override", field)]
        normalized[field] = copy.deepcopy(option.default)
    for key, value in raw.items():
        option = OPTIONS_BY_PATH.get((*prefix, "text_override", key))
        if option is None:
            raise RegistryError(f"Неизвестная опция text_override: {'.'.join(prefix)}.{key}")
        normalized[key] = validate_value(option, value)
    _set_path(values, (*prefix, "text_override"), normalized)


def _normalize_element(
    element: str, raw: Mapping[str, JsonValue], values: dict[str, JsonValue]
) -> None:
    for key, value in raw.items():
        if key == "text_override":
            _normalize_text_override((element,), value, values)
            continue
        option = OPTIONS_BY_PATH.get((element, key))
        if option is None:
            raise RegistryError(f"Неизвестная опция: {element}.{key}")
        _set_path(values, option.path, validate_value(option, value))


def normalize_values(raw: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Дополняет неполный набор значений дефолтами и проверяет его."""
    if not isinstance(raw, Mapping):
        raise RegistryError("Значения опций должны быть объектом")

    values = default_values()
    for element, element_values in raw.items():
        if element == "heading_levels":
            if not isinstance(element_values, Mapping):
                raise RegistryError("heading_levels должен быть объектом")
            for level_key, level_values in element_values.items():
                if level_key not in {str(level) for level in HEADING_LEVELS}:
                    raise RegistryError(f"Неизвестный уровень заголовка: {level_key}")
                if not isinstance(level_values, Mapping):
                    raise RegistryError(f"heading_levels.{level_key} должен быть объектом")
                for key, value in level_values.items():
                    if key == "text_override":
                        _normalize_text_override(("heading_levels", level_key), value, values)
                        continue
                    option = OPTIONS_BY_PATH.get(("heading_levels", level_key, key))
                    if option is None:
                        raise RegistryError(f"Неизвестная опция: heading_levels.{level_key}.{key}")
                    _set_path(values, option.path, validate_value(option, value))
            continue

        if element == "around":
            if not isinstance(element_values, Mapping):
                raise RegistryError("around должен быть объектом")
            for target, target_values in element_values.items():
                if target not in AROUND_TARGETS:
                    raise RegistryError(f"Неизвестный элемент окружения: {target}")
                if not isinstance(target_values, Mapping):
                    raise RegistryError(f"around.{target} должен быть объектом")
                # Миграция старого режима none: вставок нет, остаётся max.
                if target_values.get("collapse") == "none":
                    target_values = {"before": [], "after": [], "collapse": "max"}
                for key, value in target_values.items():
                    option = OPTIONS_BY_PATH.get(("around", target, key))
                    if option is None:
                        raise RegistryError(f"Неизвестная опция: around.{target}.{key}")
                    _set_path(values, option.path, validate_value(option, value))
            continue

        if element not in ELEMENT_PATHS:
            raise RegistryError(f"Неизвестный элемент: {element}")
        if not isinstance(element_values, Mapping):
            raise RegistryError(f"{element} должен быть объектом")
        _normalize_element(element, element_values, values)

    return values


def _to_registry_value(option: Option, value: object) -> JsonValue:
    if value is None:
        return None
    if option.path[-1] == "hyphenate" and isinstance(value, bool):
        return "true" if value else "false"
    if option.type == "markers":
        return list(cast(list[str], value))
    if option.id == "document.line_spacing" and isinstance(value, (int, float)):
        return {"mode": "mm", "value": float(value)}
    return cast(JsonValue, value)


def _document_line_spacing_mm(
    values: Mapping[str, JsonValue], spacing: object | None = None
) -> float:
    """Переводит абстрактный интервал в мм для старой колонки."""
    document = values.get("document")
    if not isinstance(document, Mapping):
        raise RegistryError("Нет значений document для межстрочного интервала")
    if spacing is None:
        spacing = document.get("line_spacing")
    if not isinstance(spacing, Mapping) or "mode" not in spacing or "value" not in spacing:
        raise RegistryError("document.line_spacing должен быть объектом {mode, value}")
    value = float(spacing["value"])
    if spacing["mode"] == "mm":
        return value
    font_size = float(document.get("font_size", 12.0))
    font = str(document.get("font", ""))
    manual = float(document.get("line_height_em", 1.308))
    natural = line_height_coefficient(font, manual)
    leading_em = value * natural - (natural - DEFAULT_LEADING_EM)
    return leading_em * font_size * 25.4 / 72


def _to_legacy_value(option: Option, value: JsonValue) -> object:
    if option.path[-1] == "hyphenate":
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if value == "true":
            return True
        if value == "false":
            return False
    return value


def _serialize_text_override(row: object) -> JsonValue:
    text_override = getattr(row, "text_override_style", None)
    if text_override is None:
        return None
    result: dict[str, JsonValue] = {}
    for field_name, _, _, _, _, _ in TEXT_OVERRIDE_FIELDS:
        option = OPTIONS_BY_PATH[("par", "text_override", field_name)]
        result[field_name] = _to_registry_value(option, getattr(text_override, field_name))
    return result


def serialize_profile(profile: Profile) -> dict[str, JsonValue]:
    """Строит полный набор значений из старых таблиц стилей."""
    values = default_values()

    for element, (_, relation_name) in ELEMENT_MODELS.items():
        row = getattr(profile, relation_name, None)
        if row is None:
            continue
        for option in OPTIONS:
            if option.path[0] != element or "text_override" in option.path:
                continue
            if not hasattr(row, option.path[-1]):
                continue
            _set_path(
                values,
                option.path,
                _to_registry_value(option, getattr(row, option.path[-1], None)),
            )
        if hasattr(row, "text_override_style"):
            values[element]["text_override"] = _serialize_text_override(row)

    rows_by_level = {row.level: row for row in getattr(profile, "heading_level_styles", [])}
    for level in HEADING_LEVELS:
        row = rows_by_level.get(level)
        if row is None:
            continue
        for option in OPTIONS:
            if option.path[:2] != ("heading_levels", str(level)):
                continue
            if "text_override" in option.path:
                continue
            if not hasattr(row, option.path[-1]):
                continue
            _set_path(
                values,
                option.path,
                _to_registry_value(option, getattr(row, option.path[-1], None)),
            )
        values["heading_levels"][str(level)]["text_override"] = _serialize_text_override(row)

    # around и новые опции без старых колонок сохраняем из JSONB при пересборке.
    raw_options = profile.options
    if isinstance(raw_options, Mapping):
        around = raw_options.get("around")
        if isinstance(around, Mapping):
            values["around"] = copy.deepcopy(around)
        for option in OPTIONS:
            if option.path[0] == "around" or "text_override" in option.path:
                continue
            if option.path[0] == "heading_levels":
                relation_name = "heading_level_styles"
                level_row = next(
                    (
                        row
                        for row in getattr(profile, relation_name, [])
                        if str(row.level) == option.path[1]
                    ),
                    None,
                )
                legacy_row: object | None = level_row
            else:
                model = ELEMENT_MODELS.get(option.path[0])
                legacy_row = getattr(profile, model[1], None) if model else None
            if legacy_row is None or hasattr(legacy_row, option.path[-1]):
                continue
            raw_value = _get_path(raw_options, option.path)
            if raw_value is not _MISSING:
                _set_path(values, option.path, copy.deepcopy(raw_value))

        # Множитель интервала хранится абстрактно; старая колонка получает мм.
        raw_spacing = _get_path(raw_options, ("document", "line_spacing"))
        document_row = getattr(profile, "document_style", None)
        if (
            isinstance(raw_spacing, Mapping)
            and raw_spacing.get("mode") == "multiplier"
            and document_row is not None
            and hasattr(document_row, "line_spacing")
        ):
            expected = _document_line_spacing_mm(values, raw_spacing)
            actual = float(getattr(document_row, "line_spacing"))
            if abs(actual - expected) < 0.01:
                values["document"]["line_spacing"] = copy.deepcopy(raw_spacing)

    return values


async def _apply_text_override(
    session: AsyncSession, row: object, value: dict[str, object] | None
) -> None:
    """Создаёт/обновляет/удаляет TextOverrideStyle для строки стиля элемента."""
    style_id = getattr(row, "text_override_style_id", None)
    if value is None:
        if style_id is not None:
            existing = await session.get(TextOverrideStyle, style_id)
            if existing is not None:
                await session.delete(existing)
            row.text_override_style_id = None  # type: ignore[attr-defined]
        return

    if style_id is not None:
        to_row = await session.get(TextOverrideStyle, style_id)
        if to_row is None:
            to_row = TextOverrideStyle()
            session.add(to_row)
            await session.flush()
            row.text_override_style_id = to_row.id  # type: ignore[attr-defined]
    else:
        to_row = TextOverrideStyle()
        session.add(to_row)
        await session.flush()
        row.text_override_style_id = to_row.id  # type: ignore[attr-defined]

    for key, field_value in value.items():
        if hasattr(to_row, key):
            setattr(to_row, key, field_value)


def _legacy_text_override(prefix: tuple[str, ...], value: JsonValue) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise RegistryError("text_override должен быть объектом или null")
    result: dict[str, object] = {}
    for field_name in TO_FIELD_NAMES:
        option = OPTIONS_BY_PATH[(*prefix, "text_override", field_name)]
        result[field_name] = _to_legacy_value(option, cast(JsonValue, value[field_name]))
    return result


async def apply_values_to_legacy(
    session: AsyncSession, profile_id: int, values: Mapping[str, JsonValue]
) -> None:
    """Записывает значения реестра в старые таблицы стилей."""
    for element, (model, _) in ELEMENT_MODELS.items():
        row = await StyleRepository(session, model).get_or_create(profile_id)
        for option in OPTIONS:
            if option.path[0] != element or "text_override" in option.path:
                continue
            if not hasattr(row, option.path[-1]):
                continue
            if option.id == "document.line_spacing":
                continue
            setattr(row, option.path[-1], _to_legacy_value(option, _get_path(values, option.path)))
        if element == "document" and hasattr(row, "line_spacing"):
            setattr(row, "line_spacing", _document_line_spacing_mm(values))
        if hasattr(row, "text_override_style_id"):
            element_values = values.get(element)
            if isinstance(element_values, Mapping):
                to_value = _legacy_text_override((element,), element_values.get("text_override"))
                await _apply_text_override(session, row, to_value)

    result = await session.execute(
        select(HeadingLevelStyle).where(HeadingLevelStyle.profile_id == profile_id)
    )
    rows_by_level = {row.level: row for row in result.scalars().all()}
    heading_values = values.get("heading_levels")
    for level in HEADING_LEVELS:
        row = rows_by_level.get(level)
        if row is None:
            row = HeadingLevelStyle(profile_id=profile_id, level=level)
            session.add(row)
            await session.flush()
            rows_by_level[level] = row
        if not isinstance(heading_values, Mapping):
            continue
        level_values = heading_values.get(str(level))
        if not isinstance(level_values, Mapping):
            continue
        for option in OPTIONS:
            if option.path[:2] != ("heading_levels", str(level)):
                continue
            if "text_override" in option.path:
                continue
            if not hasattr(row, option.path[-1]):
                continue
            setattr(
                row,
                option.path[-1],
                _to_legacy_value(option, _get_path(level_values, option.path[2:])),
            )
        to_value = _legacy_text_override(
            ("heading_levels", str(level)), level_values.get("text_override")
        )
        await _apply_text_override(session, row, to_value)

    await session.flush()


async def sync_options_jsonb(session: AsyncSession, profile_id: int) -> None:
    """Пересобирает JSONB из старых таблиц после записи через element API."""
    profile = await ProfileRepository(session).get_by_id_with_styles(profile_id)
    if profile is None:
        return
    profile.options = serialize_profile(profile)
    profile.options_schema_version = SCHEMA_VERSION
    await session.flush()


def options_payload(profile: Profile) -> tuple[dict[str, JsonValue], str]:
    """Читает JSONB, а при пустом JSONB — старые таблицы. Возвращает (values, source)."""
    raw_options = profile.options
    if raw_options:
        if profile.options_schema_version != SCHEMA_VERSION:
            raise RegistryVersionError(
                f"Версия схемы опций {profile.options_schema_version} "
                f"не поддерживается (ожидается {SCHEMA_VERSION})"
            )
        return normalize_values(raw_options), "jsonb"
    return serialize_profile(profile), "legacy"


__all__ = [
    "ELEMENT_MODELS",
    "RegistryError",
    "RegistryVersionError",
    "apply_values_to_legacy",
    "default_values",
    "normalize_values",
    "options_payload",
    "serialize_profile",
    "sync_options_jsonb",
    "validate_value",
]
