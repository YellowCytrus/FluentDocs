"""Element styles API: bullet_list as representative — behavior tests."""

import uuid


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
    assert data["marker"] == ["*", "- ", "‣"]  # padded to 3 by style DTO
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


async def test_patch_bullet_list_returns_200_when_seeded(client):
    create = await client.post("/profiles", json={"name": f"P4 {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.patch(f"/profiles/{pid}/bullet_list", json={"tight": False})
    assert resp.status_code == 200
    assert resp.json()["tight"] is False


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
    assert data["marker"] == ["- ", "- ", "- "]
    assert data["spacing"] == "auto"
    assert data["indent"] == 0.0
    assert data["body_indent"] == 12.5


async def test_document_default_values(client):
    """Document style defaults: seeded СТУ СФУ values."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/document")
    assert resp.status_code == 200
    data = resp.json()
    assert data["font"] == "Times New Roman"
    assert data["font_size"] == 14.0
    assert data["justify"] is True


async def test_page_default_values(client):
    """Page style defaults: paper, columns, numbering."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/page")
    assert resp.status_code == 200
    data = resp.json()
    assert data["paper"] == "a4"
    assert data["columns"] == 1
    assert data["numbering"] == "1"
    assert data["flipped"] is False


async def test_figure_default_values(client):
    """Figure style defaults: seeded СТУ СФУ values."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/figure")
    assert resp.status_code == 200
    data = resp.json()
    assert data["width"] == 165.0
    assert data["placement"] == "none"
    assert data["outlined"] is True
    assert data["fit"] == "contain"


async def test_par_default_values(client):
    """Par style defaults: seeded СТУ СФУ values."""
    create = await client.post("/profiles", json={"name": f"P {uuid.uuid4().hex[:8]}"})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}/par")
    assert resp.status_code == 200
    data = resp.json()
    assert data["spacing"] == 0.0
    assert data["linebreaks"] == "auto"
