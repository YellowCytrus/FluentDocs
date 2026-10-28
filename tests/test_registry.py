"""Контракт реестра опций: полнота, уникальность, дефолты и покрытие ORM."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.models.sqlalchemy.styles import HeadingLevelStyle, TextOverrideStyle
from app.registry.options import (
    ELEMENT_PATHS,
    GROUP_LABELS,
    OPTIONS,
    OPTIONS_BY_ID,
    OPTIONS_BY_PATH,
    TEST_IDS,
    TEXT_OVERRIDE_ELEMENTS,
    TEXT_OVERRIDE_FIELDS,
)
from app.registry.storage import ELEMENT_MODELS, default_values, serialize_profile, validate_value
from tests.golden_helpers import default_profile

TESTS_DIR = Path(__file__).resolve().parent


def _test_function_names() -> set[str]:
    names: set[str] = set()
    for path in TESTS_DIR.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


def test_registry_option_contract() -> None:
    """У каждой опции есть все поля, id уникальны, default валиден, тесты существуют."""
    assert OPTIONS, "реестр не должен быть пустым"
    assert len(OPTIONS_BY_ID) == len(OPTIONS)
    assert len(OPTIONS_BY_PATH) == len(OPTIONS)

    known_tests = _test_function_names()
    for option in OPTIONS:
        assert option.id
        assert option.group in GROUP_LABELS
        assert option.applies_to
        assert option.path
        assert option.rationale.strip()
        assert option.source.strip()
        assert option.test_ids
        assert set(option.test_ids) <= known_tests, set(option.test_ids) - known_tests
        if not option.legacy:
            assert option.test_ids != tuple(TEST_IDS)
            assert all(name.startswith("test_") for name in option.test_ids)
            assert "значение хранится в профиле" not in option.rationale
            assert "без переопределения действует" not in option.rationale
            assert "СТУ" in option.source or "reference:" in option.source
        assert option.ui.get("control")
        assert option.ui.get("label")
        assert option.ui.get("tab")

        value = validate_value(option, option.default)
        assert value == option.default

        if option.type in {"number", "integer"}:
            assert option.unit in option.allowed_units or option.unit is None
            if option.min is not None and option.max is not None:
                assert option.min <= option.max
        if option.type == "select":
            assert option.enum
            if option.default is not None:
                assert option.default in option.enum
        if option.type == "markers":
            assert isinstance(option.default, list)
            assert 1 <= len(option.default) <= 3


def test_registry_defaults_match_models() -> None:
    """Дефолты реестра совпадают с дефолтами ORM, включая text_override."""
    assert serialize_profile(default_profile()) == default_values()

    for field_name, _, _, _, _, _ in TEXT_OVERRIDE_FIELDS:
        option = OPTIONS_BY_PATH[("par", "text_override", field_name)]
        column = TextOverrideStyle.__table__.columns[field_name]
        default = column.default.arg if column.default is not None else None
        if callable(default):
            default = default(None)
        assert option.default == default, field_name


@pytest.mark.parametrize("element", ELEMENT_PATHS)
def test_registry_covers_orm_fields(element: str) -> None:
    """Каждая колонка стилей (кроме мёртвых) представлена опцией реестра."""
    if element not in ELEMENT_MODELS:
        # structural/appendix живут только в JSONB, старых таблиц у них нет.
        assert any(option.path[0] == element for option in OPTIONS)
        return
    model, _ = ELEMENT_MODELS[element]
    ignored = {"id", "profile_id", "text_override_style_id", "level"}
    # Старая строковая колонка отступа оглавления заменена структурными опциями.
    if element == "outline":
        ignored.add("indent")
    for column in model.__table__.columns:
        if column.name in ignored:
            continue
        assert (element, column.name) in OPTIONS_BY_PATH, f"{element}.{column.name}"


def test_registry_covers_heading_levels_and_text_overrides() -> None:
    """Уровни 1–6 и все поля text_override покрыты опциями."""
    ignored = {
        "id",
        "profile_id",
        "text_override_style_id",
        "level",
        "outlined",
        "bookmarked",
        "offset",
    }
    for level in range(1, 7):
        for column in HeadingLevelStyle.__table__.columns:
            if column.name in ignored:
                continue
            assert ("heading_levels", str(level), column.name) in OPTIONS_BY_PATH

    for _, _, _, prefix in TEXT_OVERRIDE_ELEMENTS:
        for field_name, _, _, _, _, _ in TEXT_OVERRIDE_FIELDS:
            assert (*prefix, "text_override", field_name) in OPTIONS_BY_PATH


def test_registry_normalize_and_validate() -> None:
    """Неполные значения дополняются дефолтами, неизвестные и неверные — отвергаются."""
    values = default_values()
    values["page"]["margin_left"] = 30
    values["par"]["text_override"] = {"font_size": 14}
    from app.registry import normalize_values

    normalized = normalize_values(
        {"page": {"margin_left": 30}, "par": {"text_override": {"font_size": 14}}}
    )
    assert normalized["page"]["margin_left"] == 30
    assert normalized["par"]["text_override"]["font_size"] == 14
    assert normalized["par"]["text_override"]["font"] == "Merriweather"
    assert normalized["page"]["paper"] == "a4"

    with pytest.raises(ValueError):
        normalize_values({"unknown": {}})
    with pytest.raises(ValueError):
        normalize_values({"page": {"unknown": 1}})
    with pytest.raises(ValueError):
        normalize_values({"page": {"margin_left": -1}})
