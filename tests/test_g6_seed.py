"""G6: seed-профиль «СТУ СФУ» — данные реестра с источниками."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.sfu_seed import (
    SFU_PROFILE_NAME,
    build_sfu_values,
    profile_metadata,
    sfu_overrides,
)
from app.utils.typst_config import config_tree

SNAPSHOT = Path(__file__).resolve().parent.parent / "docs" / "sprint" / "sfu_profile.json"


def test_sfu_seed_sources_and_ids() -> None:
    """Каждое значение адресует существующую опцию и имеет пункт СТУ."""
    overrides = sfu_overrides()
    assert overrides, "seed не должен быть пустым"
    for option_id, (_value, source) in overrides.items():
        assert option_id in OPTIONS_BY_ID, option_id
        assert "СТУ" in source, (option_id, source)


def test_sfu_seed_values_validate() -> None:
    """Полный набор значений проходит валидацию реестра."""
    values = normalize_values(build_sfu_values())
    assert values["page"]["margin_top"] == 20.0
    assert values["page"]["margin_left"] == 30.0
    assert values["document"]["line_spacing"] == {"mode": "multiplier", "value": 1.5}
    assert values["document"]["font"] == "Times New Roman"
    assert values["table"]["caption_template"] == "Таблица {h1}.{n} — {content}"
    assert values["figure"]["caption_template"] == "Рисунок {h1}.{n} — {content}"


def test_sfu_seed_matches_snapshot() -> None:
    """JSON-снимок совпадает с кодом seed: правка без перегенерации запрещена."""
    assert SNAPSHOT.exists(), f"нет снимка {SNAPSHOT}"
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["schema_version"] == SCHEMA_VERSION
    assert snapshot["name"] == SFU_PROFILE_NAME
    assert snapshot["values"] == normalize_values(build_sfu_values())
    assert snapshot["sources"] == profile_metadata()["sources"]


def test_sfu_seed_structural_entities() -> None:
    """Структурные разделы СТУ: без номера, по центру, ПРОПИСНЫМИ, с разрывом."""
    values = normalize_values(build_sfu_values())
    entities = values["structural"]["entities"]
    assert [entity["id"] for entity in entities] == [
        "содержание",
        "введение",
        "заключение",
        "список_сокращений",
        "список_использованных_источников",
        "appendix",
    ]
    for entity in entities:
        assert entity["match"]["target"] == "heading"
        assert entity["match"]["level"] == "1"
        assert entity["apply"]["break_before"] is True
        assert entity["apply"]["align"] == "center"
        assert entity["apply"]["case"] == "upper"
        assert entity["apply"]["bold"] is True
        assert entity["apply"]["around"]["after"][0]["type"] == "blank"
    for entity in entities[:-1]:
        assert entity["numbering"]["mode"] == "none"
    appendix = entities[-1]
    assert appendix["numbering"]["kind"] == "appendix"
    assert appendix["numbering"]["mode"] == "own"
    assert appendix["numbering"]["template"] == "{letter}"


def test_sfu_seed_config_tree() -> None:
    """Значения seed доходят до Typst-конфига без специального кода."""
    tree = config_tree(normalize_values(build_sfu_values()))
    assert tree["page"]["margin_top"] == 20.0
    assert tree["page"]["margin_left"] == 30.0
    assert tree["page"]["numbering"] == "1"
    assert tree["page"]["numbering_skip_first"] is True
    assert tree["document"]["font"] == "Times New Roman"
    assert tree["document"]["font_size"] == 14.0
    assert tree["document"]["line_spacing"] == {"mode": "multiplier", "value": 1.5}
    assert tree["table"]["header_double_line"] is True
    assert tree["figure"]["caption_align"] == "center"
    assert tree["equation"]["numbering_enabled"] is True
    assert tree["appendix"]["bold"] is True
    assert tree["outline"]["depth"] == 4


def test_sfu_seed_does_not_hardcode_document_text() -> None:
    """В seed нет пользовательского текста документа, только правила."""
    values = normalize_values(build_sfu_values())
    assert not any(
        option_id.startswith(("document.title", "title.")) for option_id in sfu_overrides()
    )
    assert values["structural"]["entities"]


@pytest.mark.parametrize(
    ("option_id", "expected"),
    [
        ("page.margin_left", 30.0),
        ("document.font_size", 14.0),
        ("table.stroke", 0.1764),
        ("figure.width", 165.0),
        ("outline.omit_when_pages_lte", 24),
        ("appendix.overflow", "double"),
    ],
)
def test_sfu_seed_landmark_values(option_id: str, expected: object) -> None:
    """Опорные значения СТУ зафиксированы явно."""
    values = normalize_values(build_sfu_values())
    option = OPTIONS_BY_ID[option_id]
    current: object = values
    for part in option.path:
        current = current[part]  # type: ignore[index]
    assert current == expected
