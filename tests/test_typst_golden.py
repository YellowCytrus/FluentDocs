"""Golden-снимки полного Typst-вывода для эталонных документов (G0).

Обновление снимков — только осознанно:
    UPDATE_GOLDEN=1 uv run pytest tests/test_typst_golden.py -m integration
"""

from __future__ import annotations

import os
import shutil

import pytest

from golden_helpers import DOCS_DIR, GOLDEN_DIR, build_source, default_profile

pandoc_available = shutil.which("pandoc") is not None

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not pandoc_available, reason="pandoc must be in PATH"),
]

DOCS = sorted(DOCS_DIR.glob("*.md"))


@pytest.mark.parametrize("doc", DOCS, ids=[d.stem for d in DOCS])
def test_typst_output_matches_golden(doc):
    source = build_source(doc.read_text(encoding="utf-8"), default_profile())
    golden_path = GOLDEN_DIR / f"{doc.stem}.typ"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        golden_path.write_text(source, encoding="utf-8")
    assert golden_path.exists(), f"нет golden-снимка {golden_path}"
    assert source == golden_path.read_text(encoding="utf-8")
