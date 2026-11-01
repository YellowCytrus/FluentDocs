"""Profiles API: behavior tests — input X → output Y."""

import uuid


async def test_create_profile_returns_200_and_body(client):
    unique_name = f"Test Profile {uuid.uuid4().hex[:8]}"
    resp = await client.post("/profiles", json={"name": unique_name})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == unique_name
    assert "id" in data and isinstance(data["id"], int)


async def test_get_profiles_returns_list(client):
    name_a = f"A {uuid.uuid4().hex[:8]}"
    name_b = f"B {uuid.uuid4().hex[:8]}"
    await client.post("/profiles", json={"name": name_a})
    await client.post("/profiles", json={"name": name_b})
    # limit=200 чтобы новые профили (макс. id) попали в выборку
    resp = await client.get("/profiles?limit=200")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert name_a in names and name_b in names


async def test_get_profiles_pagination(client):
    resp = await client.get("/profiles?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) <= 2


async def test_get_profile_by_id_returns_200(client):
    unique_name = f"Fetch Me {uuid.uuid4().hex[:8]}"
    create = await client.post("/profiles", json={"name": unique_name})
    pid = create.json()["id"]
    resp = await client.get(f"/profiles/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == unique_name
    assert resp.json()["id"] == pid


async def test_get_profile_by_id_returns_404(client):
    resp = await client.get("/profiles/99999")
    assert resp.status_code == 404
    assert "detail" in resp.json()


async def test_patch_profile_returns_200(client):
    unique_name = f"Original {uuid.uuid4().hex[:8]}"
    updated_name = f"Updated {uuid.uuid4().hex[:8]}"
    create = await client.post("/profiles", json={"name": unique_name})
    pid = create.json()["id"]
    resp = await client.patch(f"/profiles/{pid}", json={"name": updated_name})
    assert resp.status_code == 200
    assert resp.json()["name"] == updated_name


async def test_patch_profile_returns_404(client):
    resp = await client.patch("/profiles/99999", json={"name": "X"})
    assert resp.status_code == 404


async def test_delete_profile_returns_204(client):
    unique_name = f"To Delete {uuid.uuid4().hex[:8]}"
    create = await client.post("/profiles", json={"name": unique_name})
    pid = create.json()["id"]
    resp = await client.delete(f"/profiles/{pid}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/profiles/{pid}")
    assert get_resp.status_code == 404


async def test_delete_profile_returns_404(client):
    resp = await client.delete("/profiles/99999")
    assert resp.status_code == 404


async def test_create_profile_with_existing_name_returns_409(client):
    name = f"Duplicate {uuid.uuid4().hex[:8]}"
    first = await client.post("/profiles", json={"name": name})
    assert first.status_code == 200
    second = await client.post("/profiles", json={"name": name})
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert name in detail
    assert "уже существует" in detail


async def test_rename_profile_to_existing_name_returns_409(client):
    first_name = f"First {uuid.uuid4().hex[:8]}"
    second_name = f"Second {uuid.uuid4().hex[:8]}"
    await client.post("/profiles", json={"name": first_name})
    second = await client.post("/profiles", json={"name": second_name})
    pid = second.json()["id"]
    resp = await client.patch(f"/profiles/{pid}", json={"name": first_name})
    assert resp.status_code == 409
    assert first_name in resp.json()["detail"]
