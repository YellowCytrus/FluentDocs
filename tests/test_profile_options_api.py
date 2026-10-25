"""API значений реестра: запись в JSONB и старые таблицы, двойное чтение."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app.registry import SCHEMA_VERSION


async def _create_profile(client) -> int:
    name = f"Options {uuid.uuid4().hex[:8]}"
    response = await client.post("/profiles", json={"name": name})
    assert response.status_code == 200
    return response.json()["id"]


async def test_options_api_roundtrip(client):
    profile_id = await _create_profile(client)

    initial = await client.get(f"/profiles/{profile_id}/options")
    assert initial.status_code == 200
    assert initial.json()["source"] == "legacy"
    assert initial.json()["schema_version"] == SCHEMA_VERSION
    assert initial.json()["values"]["page"]["paper"] == "a4"

    updated = await client.put(
        f"/profiles/{profile_id}/options",
        json={
            "schema_version": SCHEMA_VERSION,
            "values": {
                "page": {"margin_left": 30.0, "numbering": "1"},
                "document": {"font_size": 14.0, "font": "Libertinus Serif"},
                "par": {"text_override": {"font_size": 13.0}},
                "heading_levels": {"1": {"break_before": True}},
            },
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["source"] == "jsonb"
    assert body["values"]["page"]["margin_left"] == 30.0
    assert body["values"]["page"]["paper"] == "a4"
    assert body["values"]["document"]["font_size"] == 14.0
    assert body["values"]["heading_levels"]["1"]["break_before"] is True

    page = await client.get(f"/profiles/{profile_id}/page")
    assert page.status_code == 200
    assert page.json()["margin_left"] == 30.0
    assert page.json()["numbering"] == "1"

    document = await client.get(f"/profiles/{profile_id}/document")
    assert document.json()["font"] == "Libertinus Serif"

    par = await client.get(f"/profiles/{profile_id}/par")
    assert par.json()["text_override"]["font_size"] == 13.0

    heading = await client.get(f"/profiles/{profile_id}/heading/1")
    assert heading.json()["break_before"] is True


async def test_options_legacy_double_read(client, test_session_factory):
    profile_id = await _create_profile(client)
    values = {
        "page": {"margin_left": 32.0},
        "par": {"spacing": 6.0, "text_override": {"font": "Libre Baskerville"}},
    }
    put = await client.put(
        f"/profiles/{profile_id}/options",
        json={"schema_version": SCHEMA_VERSION, "values": values},
    )
    assert put.status_code == 200

    # Имитируем профиль, созданный до появления JSONB: колонка пуста.
    async with test_session_factory() as session:
        await session.execute(
            text("UPDATE profiles SET options = '{}'::jsonb WHERE id = :profile_id"),
            {"profile_id": profile_id},
        )
        await session.commit()

    legacy = await client.get(f"/profiles/{profile_id}/options")
    assert legacy.status_code == 200
    assert legacy.json()["source"] == "legacy"
    assert legacy.json()["values"]["page"]["margin_left"] == 32.0
    assert legacy.json()["values"]["par"]["spacing"] == 6.0
    assert legacy.json()["values"]["par"]["text_override"]["font"] == "Libre Baskerville"


async def test_options_legacy_write_updates_jsonb(client):
    profile_id = await _create_profile(client)
    await client.get(f"/profiles/{profile_id}/page")

    patched = await client.patch(
        f"/profiles/{profile_id}/page",
        json={"margin_left": 21.0},
    )
    assert patched.status_code == 200

    await client.get(f"/profiles/{profile_id}/heading/1")
    heading_patched = await client.patch(
        f"/profiles/{profile_id}/heading/1",
        json={"break_before": True},
    )
    assert heading_patched.status_code == 200

    options = await client.get(f"/profiles/{profile_id}/options")
    assert options.status_code == 200
    assert options.json()["source"] == "jsonb"
    assert options.json()["values"]["page"]["margin_left"] == 21.0
    assert options.json()["values"]["heading_levels"]["1"]["break_before"] is True


async def test_options_api_rejects_bad_input(client):
    profile_id = await _create_profile(client)

    bad_version = await client.put(
        f"/profiles/{profile_id}/options",
        json={"schema_version": 999, "values": {}},
    )
    assert bad_version.status_code == 400

    unknown = await client.put(
        f"/profiles/{profile_id}/options",
        json={"schema_version": SCHEMA_VERSION, "values": {"page": {"unknown": 1}}},
    )
    assert unknown.status_code == 400

    bad_range = await client.put(
        f"/profiles/{profile_id}/options",
        json={"schema_version": SCHEMA_VERSION, "values": {"page": {"margin_left": -5}}},
    )
    assert bad_range.status_code == 400
