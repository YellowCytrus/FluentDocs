"""Element styles API: bullet_list as representative — behavior tests."""

import uuid

from app.models.constants.style_defaults import (
    DOCUMENT_LINE_SPACING_MM_DEFAULT,
    FIGURE_WIDTH_MM_DEFAULT,
    LIST_BODY_INDENT_MM_DEFAULT,
    PAR_SPACING_MM_DEFAULT,
)


async def test_post_bullet_list_creates_styles(client):
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.post(
        f"/profiles/{pid}/bullet_list",
        json={"tight": False, "marker": ["*"], "spacing": "loose"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tight"] is False
    assert data["marker"] == ["*", "- ", "‣"]  # padded to 3 from default
    assert data["spacing"] == "loose"


async def test_get_bullet_list_returns_styles(client):
    create = await client.post("/profiles", json={"name": f"P2 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    await client.post(f"/profiles/{pid}/bullet_list", json={"tight": True})
    resp = await client.get(f"/profiles/{pid}/bullet_list")
    assert resp.status_code == 200
    assert resp.json()["tight"] is True


async def test_get_bullet_list_creates_defaults_if_missing(client):
    create = await client.post("/profiles", json={"name": f"P3 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/bullet_list")
    assert resp.status_code == 200
    data = resp.json()
    assert "tight" in data
    assert "marker" in data


async def test_patch_bullet_list_returns_404_when_not_set(client):
    create = await client.post("/profiles", json={"name": f"P4 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.patch(f"/profiles/{pid}/bullet_list", json={"tight": False})
    assert resp.status_code == 404


async def test_patch_bullet_list_returns_200_after_post(client):
    create = await client.post("/profiles", json={"name": f"P5 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    await client.post(f"/profiles/{pid}/bullet_list", json={})
    resp = await client.patch(f"/profiles/{pid}/bullet_list", json={"tight": False})
    assert resp.status_code == 200
    assert resp.json()["tight"] is False


async def test_element_styles_404_for_nonexistent_profile(client):
    resp = await client.get("/profiles/99999/bullet_list")
    assert resp.status_code == 404
    resp = await client.post("/profiles/99999/bullet_list", json={})
    assert resp.status_code == 404
    resp = await client.patch("/profiles/99999/bullet_list", json={"tight": True})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Default values: GET without prior POST returns ORM defaults (regression guard)
# ---------------------------------------------------------------------------


async def test_bullet_list_default_values(client):
    """First GET creates row with ORM defaults."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/bullet_list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tight"] is True
    assert data["marker"] == ["- ", "‣", "–"]
    assert data["spacing"] == "auto"
    assert data["indent"] == 0.0
    assert data["body_indent"] == LIST_BODY_INDENT_MM_DEFAULT


async def test_document_default_values(client):
    """Document style defaults: font, line_spacing, justify."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/document")
    assert resp.status_code == 200
    data = resp.json()
    assert data["font"] == "Merriweather"
    assert data["font_size"] == 12.0
    assert data["line_spacing"] == DOCUMENT_LINE_SPACING_MM_DEFAULT
    assert data["justify"] is False


async def test_page_default_values(client):
    """Page style defaults: paper, columns, numbering."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/page")
    assert resp.status_code == 200
    data = resp.json()
    assert data["paper"] == "a4"
    assert data["columns"] == 1
    assert data["numbering"] == "none"
    assert data["flipped"] is False


async def test_figure_default_values(client):
    """Figure style defaults: width, placement, outlined, fit."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/figure")
    assert resp.status_code == 200
    data = resp.json()
    assert data["width"] == FIGURE_WIDTH_MM_DEFAULT
    assert data["placement"] == "none"
    assert data["outlined"] is True
    assert data["fit"] == "cover"


async def test_par_default_values(client):
    """Par style defaults: spacing, linebreaks."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/par")
    assert resp.status_code == 200
    data = resp.json()
    assert data["spacing"] == PAR_SPACING_MM_DEFAULT
    assert data["linebreaks"] == "auto"
