"""Integration test: real Pandoc + Typst — full Markdown → PDF cycle."""

import shutil
import uuid

import pytest

pandoc_available = shutil.which("pandoc") is not None
typst_available = shutil.which("typst") is not None


@pytest.mark.integration
@pytest.mark.skipif(
    not (pandoc_available and typst_available),
    reason="pandoc and typst must be in PATH",
)
async def test_generate_pdf_full_cycle_with_real_binaries(client):
    """POST generate-pdf with real pandoc+typst; verify PDF output."""
    create = await client.post("/profiles", json={"name": f"Integration {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    markdown = b"# Hello\n\nWorld"
    files = {"file": ("test.md", markdown, "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert resp.content.startswith(b"%PDF-")
    assert len(resp.content) > 100
