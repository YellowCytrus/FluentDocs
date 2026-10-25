"""Golden-снимки полного Typst-вывода для эталонных документов (G0/G1b).

Два профиля: дефолтный и профиль с локальными переопределениями текста.
Обновление снимков — только осознанно:
    UPDATE_GOLDEN=1 uv run pytest tests/test_typst_golden.py -m integration
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from golden_helpers import (
    DOCS_DIR,
    GOLDEN_DIR,
    TEXT_OVERRIDE_GOLDEN_DIR,
    build_golden_source,
    default_profile,
    golden_to_full_source,
    text_override_profile,
)

pandoc_available = shutil.which("pandoc") is not None
typst_available = shutil.which("typst") is not None

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not pandoc_available, reason="pandoc must be in PATH"),
]

DOCS = sorted(DOCS_DIR.glob("*.md"))
PROFILES = [
    pytest.param(default_profile, GOLDEN_DIR, id="default"),
    pytest.param(text_override_profile, TEXT_OVERRIDE_GOLDEN_DIR, id="text_override"),
]


@pytest.mark.parametrize("doc", DOCS, ids=[d.stem for d in DOCS])
@pytest.mark.parametrize("profile_factory,golden_dir", PROFILES)
def test_typst_output_matches_golden(doc, profile_factory, golden_dir):
    source = build_golden_source(doc.read_text(encoding="utf-8"), profile_factory())
    golden_path = golden_dir / f"{doc.stem}.typ"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        golden_dir.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(source, encoding="utf-8")
    assert golden_path.exists(), f"нет golden-снимка {golden_path}"
    assert source == golden_path.read_text(encoding="utf-8")


def test_golden_does_not_embed_fd_library():
    """Снимок хранит конфиг и тело, а не библиотеку fd."""
    source = build_golden_source(DOCS_DIR.joinpath("simple.md").read_text(encoding="utf-8"))
    assert "#let fd = {" not in source
    assert "fd.apply" not in source
    assert "#let fd-config = (" in source


@pytest.mark.skipif(not typst_available, reason="typst must be in PATH")
@pytest.mark.parametrize("doc", DOCS, ids=[d.stem for d in DOCS])
@pytest.mark.parametrize("profile_factory,golden_dir", PROFILES)
def test_golden_source_compiles(doc, profile_factory, golden_dir, tmp_path):
    """Снимок каждого профиля компилируется тем же Typst CLI, что и PDF."""
    golden_text = (golden_dir / f"{doc.stem}.typ").read_text(encoding="utf-8")
    source = golden_to_full_source(golden_text)
    source_path = tmp_path / "input.typ"
    source_path.write_text(source, encoding="utf-8")
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
    assert (tmp_path / "output.pdf").read_bytes().startswith(b"%PDF-")
