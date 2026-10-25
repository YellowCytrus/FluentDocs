"""Generate PDF API: behavior tests with mocked pandoc/typst."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

# Minimal PDF bytes (valid PDF header)
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<>>\nstartxref\n20\n%%EOF"


@pytest.fixture(autouse=True)
def _mock_pandoc_typst():
    """Mock pandoc and typst so tests don't require external binaries."""
    with (
        patch("app.api.generate.markdown_to_typst", new_callable=AsyncMock) as m_pandoc,
        patch("app.api.generate.compile_typst_to_pdf", new_callable=AsyncMock) as m_typst,
    ):
        m_pandoc.return_value = "#let doc = block\nHello"
        m_typst.return_value = MINIMAL_PDF
        yield m_pandoc, m_typst


async def test_generate_pdf_returns_200_and_pdf(client):
    create = await client.post("/profiles", json={"name": f"Gen {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("doc.md", b"# Hello\n\nWorld", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert "content-disposition" in [k.lower() for k in resp.headers]
    assert resp.content.startswith(b"%PDF-")


async def test_generate_pdf_content_disposition_filename(client):
    create = await client.post("/profiles", json={"name": f"Gen2 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("mydoc.md", b"x", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 200
    disp = resp.headers.get("content-disposition", "")
    assert "mydoc.pdf" in disp or "filename=" in disp


async def test_generate_pdf_404_for_nonexistent_profile(client):
    files = {"file": ("x.md", b"# x", "text/markdown")}
    resp = await client.post("/profiles/99999/generate-pdf", files=files)
    assert resp.status_code == 404


async def test_generate_pdf_400_empty_file(client):
    create = await client.post("/profiles", json={"name": f"Gen3 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("e.md", b"   \n\n", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 400
    assert "detail" in resp.json()


async def test_generate_pdf_413_file_too_large(client):
    create = await client.post("/profiles", json={"name": f"Gen4b {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    # 10 MB limit; send 10 MB + 1 byte
    big = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.md", big, "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 413


async def test_generate_pdf_400_unsupported_extension(client):
    create = await client.post("/profiles", json={"name": f"Gen4 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("x.pdf", b"x", "application/pdf")}
    resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert resp.status_code == 400


async def test_generate_pdf_500_on_pandoc_error(client):
    with patch("app.api.generate.markdown_to_typst", new_callable=AsyncMock) as m:
        from app.utils.pandoc_converter import PandocError

        m.side_effect = PandocError("failed", stderr="err")
        create = await client.post("/profiles", json={"name": f"Gen5 {uuid.uuid4().hex[:8]}"})
        pid = create.json()["id"]
        files = {"file": ("x.md", b"x", "text/markdown")}
        resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
        assert resp.status_code == 500
        assert "detail" in resp.json()


async def test_generate_pdf_500_on_typst_error(client):
    with patch("app.api.generate.compile_typst_to_pdf", new_callable=AsyncMock) as m:
        from app.utils.typst_compiler import TypstCompileError

        m.side_effect = TypstCompileError("failed", stderr="err")
        create = await client.post("/profiles", json={"name": f"Gen6 {uuid.uuid4().hex[:8]}"})
        pid = create.json()["id"]
        files = {"file": ("x.md", b"x", "text/markdown")}
        resp = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
        assert resp.status_code == 500
        assert "detail" in resp.json()


# --- export-typ ---


async def test_export_typ_returns_200_and_typ_content(client):
    create = await client.post("/profiles", json={"name": f"ExportTyp {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("doc.md", b"# Hello\n\nWorld", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/plain")
    assert "content-disposition" in [k.lower() for k in resp.headers]
    text = resp.text
    assert "#let doc = block" in text or "Hello" in text


async def test_export_typ_content_disposition_filename(client):
    create = await client.post("/profiles", json={"name": f"ExportTyp2 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("mydoc.md", b"x", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert resp.status_code == 200
    disp = resp.headers.get("content-disposition", "")
    assert "mydoc.typ" in disp or "filename=" in disp


async def test_export_typ_404_for_nonexistent_profile(client):
    files = {"file": ("x.md", b"# x", "text/markdown")}
    resp = await client.post("/profiles/99999/export-typ", files=files)
    assert resp.status_code == 404


async def test_export_typ_400_empty_file(client):
    create = await client.post("/profiles", json={"name": f"ExportTyp3 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("e.md", b"   \n\n", "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert resp.status_code == 400
    assert "detail" in resp.json()


async def test_export_typ_413_file_too_large(client):
    create = await client.post("/profiles", json={"name": f"ExportTyp4 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    big = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.md", big, "text/markdown")}
    resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert resp.status_code == 413


async def test_export_typ_400_unsupported_extension(client):
    create = await client.post("/profiles", json={"name": f"ExportTyp5 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("x.pdf", b"x", "application/pdf")}
    resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert resp.status_code == 400


async def test_export_typ_500_on_pandoc_error(client):
    with patch("app.api.generate.markdown_to_typst", new_callable=AsyncMock) as m:
        from app.utils.pandoc_converter import PandocError

        m.side_effect = PandocError("failed", stderr="err")
        create = await client.post("/profiles", json={"name": f"ExportTyp6 {uuid.uuid4().hex[:8]}"})
        pid = create.json()["id"]
        files = {"file": ("x.md", b"x", "text/markdown")}
        resp = await client.post(f"/profiles/{pid}/export-typ", files=files)
        assert resp.status_code == 500
        assert "detail" in resp.json()


async def test_pdf_and_export_use_identical_source(client, _mock_pandoc_typst):
    """PDF-компилятор получает ровно тот же полный Typst, что и export-typ."""
    _m_pandoc, m_typst = _mock_pandoc_typst
    create = await client.post("/profiles", json={"name": f"Parity {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    files = {"file": ("doc.md", b"# Hello\n\nWorld", "text/markdown")}

    exported = await client.post(f"/profiles/{pid}/export-typ", files=files)
    assert exported.status_code == 200

    generated = await client.post(f"/profiles/{pid}/generate-pdf", files=files)
    assert generated.status_code == 200
    compiled_source = m_typst.await_args.args[0]
    assert compiled_source == exported.text
