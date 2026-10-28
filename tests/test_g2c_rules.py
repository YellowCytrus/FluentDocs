"""G2c: оставшиеся правила класса A сложности 1–2."""

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

MM_TO_PT = 72 / 25.4


def _profile_with(updates: dict[str, float | bool | str]):
    values = default_values()
    for option_id, value in updates.items():
        path = OPTIONS_BY_ID[option_id].path
        current = values
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value
    profile = default_profile()
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return profile


def _render(markdown: str, profile, tmp_path: Path, name: str) -> Path:
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


def test_page_landscape_options() -> None:
    values = default_values()
    config = config_tree(values)
    for side in ("top", "bottom", "left", "right"):
        option = OPTIONS_BY_ID[f"page.margin_landscape_{side}"]
        assert option.default == 25.0
        assert option.unit == "mm"
        assert "СТУ" in option.source
        assert option.test_ids
        assert config["page"][f"margin_landscape_{side}"] == 25.0
        values["page"][f"margin_landscape_{side}"] = 10.0
    config = config_tree(normalize_values(values))
    assert config["page"]["margin_landscape_left"] == 10.0


def test_page_numbering_options() -> None:
    skip = OPTIONS_BY_ID["page.numbering_skip_first"]
    start = OPTIONS_BY_ID["page.numbering_start"]
    assert skip.default is False
    assert start.default == 1
    values = default_values()
    values["page"]["numbering"] = "1"
    values["page"]["numbering_skip_first"] = True
    values["page"]["numbering_start"] = 5
    config = config_tree(normalize_values(values))
    assert config["page"]["numbering"] == "1"
    assert config["page"]["numbering_skip_first"] is True
    assert config["page"]["numbering_start"] == 5


def test_equation_body_indent_options() -> None:
    option = OPTIONS_BY_ID["equation.body_indent"]
    assert option.default == 0.0
    assert option.unit == "mm"
    values = default_values()
    values["equation"]["body_indent"] = 20.0
    assert config_tree(normalize_values(values))["equation"]["body_indent"] == 20.0


def test_footnote_separator_options() -> None:
    length = OPTIONS_BY_ID["footnote.separator_length"]
    stroke = OPTIONS_BY_ID["footnote.separator_stroke"]
    assert length.default == 30.0
    assert stroke.default == pytest.approx(0.1764)
    values = default_values()
    values["footnote"]["separator_length"] = 60.0
    values["footnote"]["separator_stroke"] = 1.0
    config = config_tree(normalize_values(values))
    assert config["footnote"]["separator_length"] == 60.0
    assert config["footnote"]["separator_stroke"] == 1.0


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_page_landscape_render(tmp_path: Path) -> None:
    profile = _profile_with(
        {
            "page.flipped": True,
            "page.margin_landscape_left": 10.0,
            "page.margin_landscape_top": 12.0,
            "par.first_line_indent": 0.0,
        }
    )
    path = _render("Текст в альбомной ориентации.", profile, tmp_path, "landscape")
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        assert page.width > page.height
        x0 = min(char["x0"] for char in page.chars)
        top = min(char["top"] for char in page.chars)
    assert x0 == pytest.approx(10.0 * MM_TO_PT, abs=2.0)
    assert top == pytest.approx(12.0 * MM_TO_PT, abs=2.0)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_page_numbering_render(tmp_path: Path) -> None:
    profile = _profile_with(
        {
            "page.numbering": "1",
            "page.numbering_skip_first": True,
            "page.numbering_start": 5,
        }
    )
    markdown = "Начало.\n\n" + ("Текст без цифр. " * 900)
    path = _render(markdown, profile, tmp_path, "numbering")
    with pdfplumber.open(path) as pdf:
        assert len(pdf.pages) >= 2
        first = pdf.pages[0].extract_text() or ""
        second = pdf.pages[1].extract_text() or ""
    assert "5" not in first
    assert "6" in second


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_equation_body_indent_render(tmp_path: Path) -> None:
    markdown = "START\n\n$$E = mc^2$$\n\nEND\n"
    base = _render(markdown, _profile_with({}), tmp_path, "eq-base")
    wide = _render(markdown, _profile_with({"equation.body_indent": 30.0}), tmp_path, "eq-wide")

    def formula_x(path: Path) -> float:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            start = next(
                line for line in page.extract_text_lines() if line["text"].strip() == "START"
            )
            end = next(line for line in page.extract_text_lines() if line["text"].strip() == "END")
            chars = [char for char in page.chars if start["bottom"] < char["top"] < end["top"]]
        assert chars
        return min(char["x0"] for char in chars)

    assert formula_x(wide) > formula_x(base) + 10.0


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_footnote_separator_render(tmp_path: Path) -> None:
    markdown = "Текст со сноской[^1].\n\n[^1]: Текст сноски.\n"
    base = _render(markdown, _profile_with({}), tmp_path, "fn-base")
    wide = _render(
        markdown,
        _profile_with({"footnote.separator_length": 60.0, "footnote.separator_stroke": 1.0}),
        tmp_path,
        "fn-wide",
    )

    def separator(path: Path) -> tuple[float, float]:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            lines = [line for line in page.lines if line["top"] > page.height / 2]
        assert lines
        best = max(lines, key=lambda line: line["width"])
        return best["width"], best.get("linewidth", 0.0)

    base_width, base_stroke = separator(base)
    wide_width, wide_stroke = separator(wide)
    assert wide_width > base_width * 1.7
    assert wide_stroke > base_stroke
