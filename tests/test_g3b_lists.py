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
    with pdfplumber.open(body_path) as pdf:
        body_lines = pdf.pages[0].extract_text_lines()

    assert len(left_lines) >= 2
    assert len(body_lines) >= 2
    assert left_lines[1]["x0"] < body_lines[1]["x0"] - 1.0
