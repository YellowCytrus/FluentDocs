"""Heading level API: мёртвые поля убраны из ответов и входа."""

from __future__ import annotations

import uuid


async def _profile(client) -> int:
    response = await client.post("/profiles", json={"name": f"Head {uuid.uuid4().hex[:8]}"})
    assert response.status_code == 200
    return response.json()["id"]


async def test_heading_level_response_has_no_dead_fields(client):
    profile_id = await _profile(client)
    response = await client.get(f"/profiles/{profile_id}/heading/1")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"level", "break_before", "numbering_enabled", "text_override"}


async def test_heading_level_rejects_dead_fields(client):
    profile_id = await _profile(client)
    for field, value in (
        ("outlined", False),
        ("bookmarked", "true"),
        ("offset", 2),
    ):
        response = await client.patch(
            f"/profiles/{profile_id}/heading/1",
            json={field: value},
        )
        assert response.status_code == 422, (field, response.text)
