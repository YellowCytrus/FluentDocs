"""G3b: форматы нумерованных списков по уровням и перенос строки."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values
from app.utils.typst_config import config_tree
from golden_helpers import build_source, default_profile


def _profile(**changes: object):
    values = default_values()
    for section, section_values in changes.items():
        target = values[section]
        assert isinstance(target, dict)
        target.update(section_values)  # type: ignore[arg-type]
    profile = default_profile()
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return profile


def _compile(markdown: str, profile, tmp_path: Path, name: str) -> Path:
    site = tmp_path / name
    site.mkdir(parents=True, exist_ok=True)
    (site / "input.typ").write_text(build_source(markdown, profile), encoding="utf-8")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=site,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return site / "output.pdf"


def _lines(pdf_path: Path) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        return [line["text"] for page in pdf.pages for line in page.extract_text_lines()]


def test_numbered_list_options_schema() -> None:
    formats = OPTIONS_BY_ID["numbered_list.level_formats"]
    assert formats.type == "list"
    assert formats.default == []
    assert formats.legacy is False
    assert {field.path[-1] for field in formats.item_fields} == {"format"}
    assert "СТУ" in formats.source
    assert "значение хранится в профиле" not in formats.rationale

    alphabet = OPTIONS_BY_ID["numbered_list.alphabet"]
    assert alphabet.type == "select"
    assert alphabet.default == "ru_sfu"
    assert alphabet.enum == ("ru_sfu", "latin")

    wrap = OPTIONS_BY_ID["numbered_list.wrap_mode"]
    assert wrap.default == "left_margin"
    assert set(wrap.enum) == {"left_margin", "body_text"}

    values = default_values()
    values["numbered_list"]["level_formats"] = [
        {"format": "1."},
        {"format": "{letter})"},
        {"format": "1)"},
    ]
    normalized = normalize_values(values)
    tree = config_tree(normalized)
    assert tree["numbered_list"]["level_formats"] == [
        {"format": "1."},
        {"format": "{letter})"},
        {"format": "1)"},
    ]
    assert tree["numbered_list"]["alphabet"] == "ru_sfu"
    assert tree["numbered_list"]["wrap_mode"] == "left_margin"


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_level_formats_render(tmp_path: Path) -> None:
    profile = _profile(
        numbered_list={
            "level_formats": [
                {"format": "1."},
                {"format": "{letter})"},
                {"format": "1)"},
            ],
            "alphabet": "ru_sfu",
        }
    )
    markdown = "1. Первый\n    1. Вложенный\n        1. Глубокий\n2. Второй\n"
    lines = _lines(_compile(markdown, profile, tmp_path, "list-levels"))
    assert "1. Первый" in lines
    assert "а) Вложенный" in lines
    assert "1) Глубокий" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_alphabet_latin_render(tmp_path: Path) -> None:
    profile = _profile(
        numbered_list={
            "level_formats": [{"format": "{letter})"}],
            "alphabet": "latin",
        }
    )
    lines = _lines(
        _compile(
            "1. Первый\n2. Второй\n",
            profile,
            tmp_path,
            "list-latin",
        )
    )
    assert "a) Первый" in lines
    assert "b) Второй" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_level_format_repeat_render(tmp_path: Path) -> None:
    profile = _profile(
        numbered_list={
            "level_formats": [{"format": "1."}, {"format": "{letter})"}],
            "alphabet": "ru_sfu",
        }
    )
    lines = _lines(
        _compile(
            "1. Первый\n    1. Вложенный\n        1. Глубокий\n",
            profile,
            tmp_path,
            "list-level-repeat",
        )
    )
    assert "1. Первый" in lines
    assert "а) Вложенный" in lines
    assert "а) Глубокий" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_full_render(tmp_path: Path) -> None:
    profile = _profile(
        numbered_list={
            "level_formats": [{"format": "1."}, {"format": "{letter})"}],
            "alphabet": "ru_sfu",
            "full": True,
        }
    )
    lines = _lines(
        _compile(
            "1. Первый\n    1. Вложенный\n        1. Глубокий\n",
            profile,
            tmp_path,
            "list-full",
        )
    )
    assert "1. Первый" in lines
    assert "1. а) Вложенный" in lines
    assert "1.1. а) Глубокий" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_wrap_mode_render(tmp_path: Path) -> None:
    long_text = (
        "Длинный текст пункта списка, который должен переноситься на следующую "
        "строку несколько раз, чтобы проверить выравнивание продолжения. " * 2
    )
    markdown = f"1. {long_text}\n"

    left_path = _compile(
        markdown,
        _profile(numbered_list={"wrap_mode": "left_margin"}),
        tmp_path,
        "list-left",
    )
    body_path = _compile(
        markdown,
        _profile(numbered_list={"wrap_mode": "body_text"}),
        tmp_path,
        "list-body",
    )
    with pdfplumber.open(left_path) as pdf:
        left_lines = pdf.pages[0].extract_text_lines()
        left_words = pdf.pages[0].extract_words()
    with pdfplumber.open(body_path) as pdf:
        body_lines = pdf.pages[0].extract_text_lines()
        body_words = pdf.pages[0].extract_words()

    assert len(left_lines) >= 2
    assert len(body_lines) >= 2
    margin_pt = default_values()["page"]["margin_left"] * 72 / 25.4
    first_text_x = left_words[1]["x0"]
    assert abs(left_lines[1]["x0"] - margin_pt) < 0.8
    assert abs(body_lines[1]["x0"] - first_text_x) < 0.8
    assert left_lines[1]["x0"] < body_lines[1]["x0"] - 5.0
    assert first_text_x > margin_pt + 5.0
    assert body_words[1]["x0"] > margin_pt + 5.0


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("wrap_mode", ["left_margin", "body_text"])
def test_numbered_list_nested_indent_render(tmp_path: Path, wrap_mode: str) -> None:
    profile = _profile(numbered_list={"wrap_mode": wrap_mode})
    markdown = "1. Первый\n    1. Вложенный\n        1. Глубокий\n2. Второй\n"
    path = _compile(markdown, profile, tmp_path, f"nested-{wrap_mode}")
    with pdfplumber.open(path) as pdf:
        words = pdf.pages[0].extract_words()
    markers = [word for word in words if word["text"] == "1."]
    texts = [word for word in words if word["text"] in {"Первый", "Вложенный", "Глубокий"}]
    assert len(markers) >= 3
    assert len(texts) >= 3
    marker_x = [float(word["x0"]) for word in markers[:3]]
    text_x = [float(word["x0"]) for word in texts[:3]]
    marker_steps = [marker_x[1] - marker_x[0], marker_x[2] - marker_x[1]]
    text_steps = [text_x[1] - text_x[0], text_x[2] - text_x[1]]
    assert all(step > 5.0 for step in marker_steps)
    assert abs(marker_steps[0] - marker_steps[1]) < 0.8
    assert abs(text_steps[0] - text_steps[1]) < 0.8
    assert all(abs(text_steps[index] - marker_steps[index]) < 0.8 for index in range(2))


def _list_tops(pdf_path: Path) -> list[float]:
    with pdfplumber.open(pdf_path) as pdf:
        lines = pdf.pages[0].extract_text_lines()
    return [float(line["top"]) for line in lines if line["text"][:2] in {"1.", "2.", "3."}]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(
    ("changes", "expected_gap"),
    [
        ({}, 22.3),
        ({"tight": False}, 22.3),
        ({"spacing": "tight"}, 13.9),
        ({"spacing": "loose"}, 19.9),
    ],
    ids=["auto-tight", "auto-not-tight", "tight", "loose"],
)
def test_numbered_list_spacing_render(
    tmp_path: Path, changes: dict[str, object], expected_gap: float
) -> None:
    profile = _profile(numbered_list=changes)
    path = _compile(
        "1. Первый пункт\n2. Второй пункт\n3. Третий пункт\n",
        profile,
        tmp_path,
        f"spacing-{'-'.join(str(value) for value in changes.values()) or 'default'}",
    )
    tops = _list_tops(path)
    assert len(tops) == 3
    gaps = [tops[1] - tops[0], tops[2] - tops[1]]
    assert all(abs(gap - expected_gap) < 0.5 for gap in gaps)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_tight_loose_spacing_values_render(tmp_path: Path) -> None:
    markdown = "1. Первый пункт\n2. Второй пункт\n3. Третий пункт\n"

    def gap(name: str, changes: dict[str, object]) -> float:
        path = _compile(markdown, _profile(numbered_list=changes), tmp_path, name)
        tops = _list_tops(path)
        return tops[1] - tops[0]

    tight_base = gap("tight-base", {"spacing": "tight", "tight_spacing": 0.5})
    tight_wide = gap("tight-wide", {"spacing": "tight", "tight_spacing": 2.0})
    loose_base = gap("loose-base", {"spacing": "loose", "loose_spacing": 1.0})
    loose_wide = gap("loose-wide", {"spacing": "loose", "loose_spacing": 2.0})
    assert tight_wide - tight_base == pytest.approx(1.5 * 12.0, abs=0.5)
    assert loose_wide - loose_base == pytest.approx(1.0 * 12.0, abs=0.5)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_numbered_list_number_align_bottom_render(tmp_path: Path) -> None:
    long_text = (
        "Длинный текст пункта списка, который должен переноситься на следующую "
        "строку несколько раз, чтобы проверить выравнивание маркера внизу. "
    ) * 2
    markdown = f"1. {long_text}\n"

    top_path = _compile(
        markdown,
        _profile(),
        tmp_path,
        "number-align-top",
    )
    bottom_path = _compile(
        markdown,
        _profile(numbered_list={"number_align": "end+bottom"}),
        tmp_path,
        "number-align-bottom",
    )

    def marker_top(path: Path) -> float:
        with pdfplumber.open(path) as pdf:
            chars = pdf.pages[0].chars
        tops = [float(char["top"]) for char in chars if char["text"] == "1"]
        assert tops
        return min(tops)

    with pdfplumber.open(top_path) as pdf:
        top_lines = pdf.pages[0].extract_text_lines()
    with pdfplumber.open(bottom_path) as pdf:
        bottom_lines = pdf.pages[0].extract_text_lines()
    first_top = float(top_lines[0]["top"])
    last_top = float(bottom_lines[-1]["top"])
    assert abs(marker_top(top_path) - first_top) < 0.8
    assert marker_top(bottom_path) > first_top + 20.0
    assert abs(marker_top(bottom_path) - last_top) < 1.0
