"""Паритет превью (typst.ts) и серверного PDF (Typst CLI).

Один Markdown и один профиль собираются двумя путями:
- превью: preamble сервера + тело Pandoc, компиляция Node + typst.ts;
- сервер: build_typst_source, компиляция Typst CLI.

Сравниваются нормализованный Typst-источник, число страниц, текст страниц
и имена шрифтов в PDF. Тест не требует Postgres.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.utils.typst_source import build_typst_preamble, build_typst_source
from golden_helpers import DOCS_DIR, default_profile, markdown_to_typst

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
NODE = shutil.which("node")
TYPST = shutil.which("typst")
PANDOC = shutil.which("pandoc")
NODE_MODULES = FRONTEND / "node_modules" / "@myriaddreamin" / "typst-ts-web-compiler"

DOCS = ["simple", "headings", "lists", "figure", "table", "formula", "footnote", "appendix"]

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        NODE is None or TYPST is None or PANDOC is None or not NODE_MODULES.exists(),
        reason="для теста паритета нужны node, typst, pandoc и frontend/node_modules",
    ),
]


def _page_fonts(path: Path) -> set[str]:
    with pdfplumber.open(path) as pdf:
        return {char["fontname"] for page in pdf.pages for char in page.chars}


def _pages(path: Path) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def test_preview_and_server_match(tmp_path):
    profile = default_profile()
    preamble = build_typst_preamble(profile)

    jobs = []
    expected_sources: dict[str, str] = {}
    for stem in DOCS:
        markdown = (DOCS_DIR / f"{stem}.md").read_text(encoding="utf-8")
        body = markdown_to_typst(markdown)
        preview_source = preamble + "\n" + body
        server_source = build_typst_source(profile, body)
        assert preview_source == server_source, stem

        source_path = tmp_path / f"{stem}.typ"
        source_path.write_text(server_source, encoding="utf-8")
        if (DOCS_DIR / "sample.png").exists():
            shutil.copy(DOCS_DIR / "sample.png", tmp_path / "sample.png")
        jobs.append({"input": str(source_path), "output": str(tmp_path / f"{stem}.ts.pdf")})
        expected_sources[stem] = server_source

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(jobs), encoding="utf-8")
    subprocess.run(
        [NODE, "scripts/typst-parity.mjs", str(manifest)],
        cwd=FRONTEND,
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )

    for stem in DOCS:
        cli_pdf = tmp_path / f"{stem}.cli.pdf"
        result = subprocess.run(
            ["typst", "compile", str(tmp_path / f"{stem}.typ"), str(cli_pdf)],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stderr
        preview_pdf = tmp_path / f"{stem}.ts.pdf"
        assert _pages(cli_pdf) == _pages(preview_pdf), stem
        assert _page_fonts(cli_pdf) == _page_fonts(preview_pdf), stem
        assert expected_sources[stem]


def test_preview_redraw_under_two_seconds(tmp_path):
    """Документ 100+ страниц: перерисовка после правки ≤ 2 с (порог S8)."""
    paragraphs = []
    for index in range(1, 1201):
        if index % 50 == 1:
            paragraphs.append(f"# Раздел {index // 50 + 1}")
        paragraphs.append(
            f"Абзац {index}. " + "Текст для проверки скорости перерисовки превью. " * 5
        )
    source = build_typst_source(default_profile(), markdown_to_typst("\n\n".join(paragraphs)))
    source_path = tmp_path / "bench.typ"
    source_path.write_text(source, encoding="utf-8")

    result = subprocess.run(
        [NODE, "scripts/typst-preview-bench.mjs", str(source_path)],
        cwd=FRONTEND,
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["redraw_ms"] <= 2000, payload
