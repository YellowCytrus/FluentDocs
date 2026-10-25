"""Рендер второго golden-профиля: text_override реально меняет PDF."""

from __future__ import annotations

import shutil
import subprocess

import pdfplumber
import pytest

from golden_helpers import DOCS_DIR, build_source, text_override_profile

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        shutil.which("pandoc") is None or shutil.which("typst") is None,
        reason="pandoc and typst must be in PATH",
    ),
]


def _render(doc_name: str, tmp_path):
    source = build_source(
        (DOCS_DIR / doc_name).read_text(encoding="utf-8"), text_override_profile()
    )
    (tmp_path / "input.typ").write_text(source, encoding="utf-8")
    sample = DOCS_DIR / "sample.png"
    if sample.exists():
        shutil.copy(sample, tmp_path / "sample.png")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return pdfplumber.open(tmp_path / "output.pdf")


def _chars(pdf):
    return [char for page in pdf.pages for char in page.chars]


def test_par_and_heading_text_override_in_pdf(tmp_path):
    with _render("simple.md", tmp_path) as pdf:
        chars = _chars(pdf)
    heading = [c for c in chars if c["top"] < 80 and c["text"].isalpha()]
    assert heading
    assert all(abs(c["size"] - 16.0) < 0.1 for c in heading)
    body = [c for c in chars if c["top"] > 80 and c["text"].isalpha()]
    assert body
    assert any(abs(c["size"] - 13.0) < 0.1 for c in body)
    assert any("DejaVuSans-BoldOblique" in c["fontname"] for c in body)
    assert any(c.get("non_stroking_color") == (0.47843137, 0.12156863, 0.12156863) for c in body)


def test_table_text_override_in_pdf(tmp_path):
    with _render("table.md", tmp_path) as pdf:
        chars = _chars(pdf)
    assert any(abs(c["size"] - 10.0) < 0.1 for c in chars)
    assert any(c.get("non_stroking_color") == (0.0, 0.2, 0.4) for c in chars)


def test_footnote_text_override_in_pdf(tmp_path):
    with _render("footnote.md", tmp_path) as pdf:
        chars = _chars(pdf)
    assert any(abs(c["size"] - 9.0) < 0.1 for c in chars)


def test_nondefault_page_heading_and_caption_render(tmp_path):
    profile = text_override_profile()
    profile.figure_style.caption_template = "Рисунок {h1}.{N}. {content}"
    profile.page_style.margin_left = 30.0
    profile.page_style.numbering = "1"
    profile.heading_level_styles[1].numbering_enabled = False
    profile.heading_level_styles[1].break_before = True
    markdown = "# Раздел\n\nТекст.\n\n![Alt](sample.png)\n\n## Подраздел\n\nТекст после разрыва.\n"
    source = build_source(markdown, profile)
    (tmp_path / "input.typ").write_text(source, encoding="utf-8")
    shutil.copy(DOCS_DIR / "sample.png", tmp_path / "sample.png")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    with pdfplumber.open(tmp_path / "output.pdf") as pdf:
        assert len(pdf.pages) == 2
        first_text = pdf.pages[0].extract_text() or ""
        assert "Рисунок 1.1." in first_text
        assert "Подраздел" in (pdf.pages[1].extract_text() or "")
        assert "1.1 Подраздел" not in (pdf.pages[1].extract_text() or "")
        assert min(char["x0"] for char in pdf.pages[0].chars) >= 84.5


def test_list_text_override_in_pdf(tmp_path):
    with _render("lists.md", tmp_path) as pdf:
        chars = _chars(pdf)
    assert any(abs(c["size"] - 11.5) < 0.1 for c in chars)
    assert any("DejaVuSans" in c["fontname"] for c in chars)


def test_figure_text_override_in_pdf(tmp_path):
    with _render("figure.md", tmp_path) as pdf:
        chars = _chars(pdf)
    assert any(abs(c["size"] - 11.0) < 0.1 for c in chars)
    assert any("DejaVuSerif-Bold" in c["fontname"] for c in chars)
