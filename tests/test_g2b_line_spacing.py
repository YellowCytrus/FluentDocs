"""G2b: межстрочный интервал, шрифт PT Astra Serif и вынесенные константы."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from statistics import median

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, RegistryError, normalize_values
from app.registry.options import (
    DEFAULT_LEADING_EM,
    OPTIONS_BY_ID,
    line_height_coefficient,
)
from app.registry.storage import (
    _document_line_spacing_mm,
    default_values,
    validate_value,
)
from app.utils.typst_config import build_fd_config, config_tree
from app.utils.typst_literals import typst_font
from golden_helpers import build_source, default_profile

LONG_TEXT = "Это достаточно длинный абзац для измерения расстояния между строками. " * 60
TABLE_DOC = "# Заголовок\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n# Следующий\n"
REAL_BLANK_DOC = TABLE_DOC.replace("\n\n# Следующий", "\n\n\u00a0\n\n# Следующий")


def test_document_line_spacing_options() -> None:
    option = OPTIONS_BY_ID["document.line_spacing"]
    assert option.type == "object"
    assert option.default == {"mode": "mm", "value": 5.08}
    assert {field.path[-1] for field in option.fields} == {"mode", "value"}

    # Старые абсолютные значения читаются как миллиметры.
    assert validate_value(option, 5.08) == {"mode": "mm", "value": 5.08}
    assert validate_value(option, {"mode": "multiplier", "value": 1.5}) == {
        "mode": "multiplier",
        "value": 1.5,
    }
    with pytest.raises(RegistryError):
        validate_value(option, {"mode": "multiplier", "value": 3.5})
    with pytest.raises(RegistryError):
        validate_value(option, {"mode": "mm", "value": 1.0})

    values = default_values()
    config = config_tree(values)
    assert config["document"]["line_spacing"] == {"mode": "mm", "value": 5.08}
    assert config["document"]["line_height_em"] == pytest.approx(1.308)
    assert config["document"]["default_leading_em"] == DEFAULT_LEADING_EM

    # Для известного шрифта коэффициент берётся из таблицы, ручное значение — fallback.
    values["document"]["font"] = "PT Astra Serif"
    values["document"]["line_height_em"] = 1.9
    assert config_tree(values)["document"]["line_height_em"] == pytest.approx(1.312)
    values["document"]["font"] = "Unknown Font"
    assert config_tree(values)["document"]["line_height_em"] == pytest.approx(1.9)

    values = default_values()
    values["document"]["line_spacing"] = {"mode": "multiplier", "value": 1.5}
    values["document"]["font"] = "PT Astra Serif"
    source = build_fd_config(values)
    assert "line_spacing: (" in source
    assert 'mode: "multiplier"' in source
    assert "value: 1.5" in source
    assert "line_height_em: 1.312" in source
    assert _document_line_spacing_mm(values) == pytest.approx(5.529, abs=0.01)


def test_list_spacing_options() -> None:
    expected = {
        "bullet_list": (0.5, 1.0),
        "numbered_list": (0.5, 1.0),
        "terms": (0.5, 1.0),
    }
    for element, (tight, loose) in expected.items():
        values = default_values()
        assert values[element]["tight_spacing"] == tight
        assert values[element]["loose_spacing"] == loose
        values[element]["tight_spacing"] = 0.25
        values[element]["loose_spacing"] = 1.25
        config = config_tree(normalize_values(values))[element]
        assert config["tight_spacing"] == 0.25
        assert config["loose_spacing"] == 1.25


def test_heading_unnumbered_indent_option() -> None:
    values = default_values()
    assert values["heading"]["unnumbered_indent"] == -0.3
    values["heading"]["unnumbered_indent"] = -0.6
    source = build_fd_config(normalize_values(values))
    assert "unnumbered_indent: -0.6" in source


def test_line_height_coefficient_table() -> None:
    assert line_height_coefficient("Libertinus Serif", 9.0) == pytest.approx(1.308)
    assert line_height_coefficient("PT Astra Serif", 9.0) == pytest.approx(1.312)
    assert line_height_coefficient("Unknown Font", 1.42) == pytest.approx(1.42)

    # Ключ таблицы — реально используемый шрифт после алиасов, а не имя профиля.
    assert typst_font("Times New Roman") == "Libertinus Serif"
    assert line_height_coefficient("Times New Roman", 9.0) == pytest.approx(1.308)

    values = default_values()
    values["document"]["font"] = "Times New Roman"
    values["document"]["line_height_em"] = 9.0
    assert config_tree(values)["document"]["line_height_em"] == pytest.approx(1.308)


async def test_line_spacing_multiplier_roundtrip_and_legacy_mm(client) -> None:
    import uuid

    create = await client.post("/profiles", json={"name": f"G2b {uuid.uuid4().hex[:8]}"})
    profile_id = create.json()["id"]
    spacing = {"mode": "multiplier", "value": 1.5}
    put = await client.put(
        f"/profiles/{profile_id}/options",
        json={
            "schema_version": SCHEMA_VERSION,
            "values": {
                "document": {
                    "font": "PT Astra Serif",
                    "line_spacing": spacing,
                    "line_height_em": 1.312,
                }
            },
        },
    )
    assert put.status_code == 200, put.text
    got = await client.get(f"/profiles/{profile_id}/options")
    assert got.json()["values"]["document"]["line_spacing"] == spacing

    # Старый API отдаёт эквивалент в мм, но JSONB сохраняет абстрактный множитель.
    legacy = await client.get(f"/profiles/{profile_id}/document")
    assert legacy.status_code == 200
    assert legacy.json()["line_spacing"] == pytest.approx(5.529, abs=0.01)
    patched_page = await client.patch(f"/profiles/{profile_id}/page", json={"margin_left": 21.0})
    assert patched_page.status_code == 200
    got = await client.get(f"/profiles/{profile_id}/options")
    assert got.json()["values"]["document"]["line_spacing"] == spacing

    # Явная запись в старую колонку переводит профиль в режим мм.
    patched = await client.patch(f"/profiles/{profile_id}/document", json={"line_spacing": 7.0})
    assert patched.status_code == 200, patched.text
    got = await client.get(f"/profiles/{profile_id}/options")
    assert got.json()["values"]["document"]["line_spacing"] == {"mode": "mm", "value": 7.0}


def _render(markdown: str, profile, tmp_path: Path, name: str) -> Path:
    source = build_source(markdown, profile)
    site = tmp_path / name
    site.mkdir(parents=True, exist_ok=True)
    (site / "input.typ").write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=site,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return site / "output.pdf"


def _profile(font: str, line_spacing: dict, manual: float = 1.308):
    profile = default_profile()
    values = default_values()
    values["document"]["font"] = font
    values["document"]["line_spacing"] = line_spacing
    values["document"]["line_height_em"] = manual
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return profile


def _line_pitch(pdf_path: Path) -> float:
    with pdfplumber.open(pdf_path) as pdf:
        lines = pdf.pages[0].extract_text_lines()
    tops = [line["top"] for line in lines]
    diffs = [tops[index + 1] - tops[index] for index in range(len(tops) - 1)]
    assert diffs
    return median(diffs)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("font", ["Libertinus Serif", "PT Astra Serif"])
def test_line_spacing_multiplier_render(font: str, tmp_path: Path) -> None:
    normal = _profile(font, {"mode": "multiplier", "value": 1.0})
    wide = _profile(font, {"mode": "multiplier", "value": 1.5})
    normal_pitch = _line_pitch(_render(LONG_TEXT, normal, tmp_path, "normal"))
    wide_pitch = _line_pitch(_render(LONG_TEXT, wide, tmp_path, "wide"))
    assert wide_pitch / normal_pitch == pytest.approx(1.5, abs=0.02)

    # При множителе 1,0 шаг равен H * кегль для фактически используемого шрифта.
    expected = line_height_coefficient(font, 1.308) * 12.0
    assert normal_pitch == pytest.approx(expected, abs=0.3)
    assert wide_pitch == pytest.approx(expected * 1.5, abs=0.45)


def _table_heading_gap(pdf_path: Path) -> float:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        table_bottom = max(line["bottom"] for line in page.lines if line["top"] > 80)
        heading_top = min(
            char["top"]
            for char in page.chars
            if char["text"] == "С" and char["x0"] < 100 and char["top"] > table_bottom - 5
        )
        return heading_top - table_bottom


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("font", ["Libertinus Serif", "PT Astra Serif"])
@pytest.mark.parametrize("multiplier", [1.0, 1.5])
def test_blank_unit_matches_real_blank_line(font: str, multiplier: float, tmp_path: Path) -> None:
    real = _profile(font, {"mode": "multiplier", "value": multiplier})
    real_gap = _table_heading_gap(_render(REAL_BLANK_DOC, real, tmp_path, "real"))

    values = default_values()
    values["document"]["font"] = font
    values["document"]["line_spacing"] = {"mode": "multiplier", "value": multiplier}
    blank = {
        "type": "blank",
        "count": 1,
        "line_spacing": {"mode": "multiplier", "value": 1.0},
    }
    values["around"]["table"]["after"] = [blank]
    values["around"]["heading_1"]["before"] = [blank]
    around = default_profile()
    around.options = normalize_values(values)
    around.options_schema_version = SCHEMA_VERSION
    around_gap = _table_heading_gap(_render(TABLE_DOC, around, tmp_path, "around"))
    assert real_gap == pytest.approx(around_gap, abs=0.5)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_line_spacing_mm_render_keeps_absolute_value(tmp_path: Path) -> None:
    millimetres = _profile("Libertinus Serif", {"mode": "mm", "value": 5.08})
    wide_mm = _profile("Libertinus Serif", {"mode": "mm", "value": 8.0})
    small = _line_pitch(_render(LONG_TEXT, millimetres, tmp_path, "mm"))
    large = _line_pitch(_render(LONG_TEXT, wide_mm, tmp_path, "mm-large"))
    assert large - small == pytest.approx((8.0 - 5.08) * 72 / 25.4, abs=0.5)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_pt_astra_font_is_embedded(tmp_path: Path) -> None:
    profile = _profile("PT Astra Serif", {"mode": "multiplier", "value": 1.5})
    pdf_path = _render("# Проверка\n\nТекст шрифтом PT Astra Serif.", profile, tmp_path, "font")
    with pdfplumber.open(pdf_path) as pdf:
        names = {char["fontname"] for char in pdf.pages[0].chars}
    assert any("PTAstraSerif" in name for name in names), names
