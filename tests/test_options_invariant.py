"""Инвариант G1b: любая запись в старые таблицы синхронизирует profiles.options."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app.api.elements.descriptors import ELEMENT_DESCRIPTORS
from app.models.pydantic.heading_level import HeadingLevelStyles
from app.models.sqlalchemy.styles import HeadingLevelStyle
from app.registry import SCHEMA_VERSION, serialize_profile
from app.registry.storage import ELEMENT_MODELS
from app.repositories.profile_repository import ProfileRepository


async def _create_profile(client) -> int:
    response = await client.post("/profiles", json={"name": f"Invariant {uuid.uuid4().hex[:8]}"})
    assert response.status_code == 200
    return response.json()["id"]


async def _stored_options(session_factory, profile_id: int) -> dict[str, object]:
    async with session_factory() as session:
        raw = await session.scalar(
            text("SELECT options FROM profiles WHERE id = :profile_id"),
            {"profile_id": profile_id},
        )
    assert isinstance(raw, dict)
    return raw


async def _assert_invariant(session_factory, profile_id: int) -> None:
    stored = await _stored_options(session_factory, profile_id)
    async with session_factory() as session:
        profile = await ProfileRepository(session).get_by_id_with_styles(profile_id)
        assert profile is not None
        expected = serialize_profile(profile)
    assert stored == expected


async def test_invariant_after_element_post_patch_put(client, test_session_factory):
    profile_id = await _create_profile(client)

    for descriptor in ELEMENT_DESCRIPTORS:
        url = f"/profiles/{profile_id}/{descriptor.path}"
        posted = await client.post(url, json={})
        assert posted.status_code == 200, (descriptor.path, posted.text)
        await _assert_invariant(test_session_factory, profile_id)

    # Переопределение текста — отдельная ветка записи, не только скалярные поля.
    par_override = await client.post(
        f"/profiles/{profile_id}/par",
        json={"text_override": {"font_size": 15.0, "font": "DejaVu Sans"}},
    )
    assert par_override.status_code == 200, par_override.text
    await _assert_invariant(test_session_factory, profile_id)

    for descriptor in ELEMENT_DESCRIPTORS:
        url = f"/profiles/{profile_id}/{descriptor.path}"
        patched = await client.patch(url, json={})
        assert patched.status_code == 200, (descriptor.path, patched.text)
        await _assert_invariant(test_session_factory, profile_id)
        body = descriptor.styles_model().model_dump(mode="json")
        put = await client.put(url, json=body)
        assert put.status_code == 200, (descriptor.path, put.text)
        await _assert_invariant(test_session_factory, profile_id)

    cleared = await client.patch(f"/profiles/{profile_id}/par", json={"text_override": None})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["text_override"] is None
    await _assert_invariant(test_session_factory, profile_id)


async def test_invariant_after_heading_level_patch_put(client, test_session_factory):
    profile_id = await _create_profile(client)

    for level in range(1, 7):
        patch_body: dict[str, object] = {
            "break_before": level % 2 == 0,
            "numbering_enabled": level != 3,
        }
        if level == 1:
            patch_body["text_override"] = {"font_size": 16.0, "weight": "bold"}
        patched = await client.patch(f"/profiles/{profile_id}/heading/{level}", json=patch_body)
        assert patched.status_code == 200, patched.text
        await _assert_invariant(test_session_factory, profile_id)

        put_body = HeadingLevelStyles(
            level=level,
            break_before=level == 2,
            numbering_enabled=level != 4,
        ).model_dump(mode="json")
        put = await client.put(f"/profiles/{profile_id}/heading/{level}", json=put_body)
        assert put.status_code == 200, put.text
        await _assert_invariant(test_session_factory, profile_id)


async def test_invariant_after_get_creates_legacy_rows(client, test_session_factory):
    profile_id = await _create_profile(client)

    for descriptor in ELEMENT_DESCRIPTORS:
        response = await client.get(f"/profiles/{profile_id}/{descriptor.path}")
        assert response.status_code == 200, (descriptor.path, response.text)
        await _assert_invariant(test_session_factory, profile_id)

    for level in range(1, 7):
        response = await client.get(f"/profiles/{profile_id}/heading/{level}")
        assert response.status_code == 200, level
        await _assert_invariant(test_session_factory, profile_id)


async def test_invariant_after_options_put(client, test_session_factory):
    profile_id = await _create_profile(client)
    response = await client.put(
        f"/profiles/{profile_id}/options",
        json={
            "schema_version": SCHEMA_VERSION,
            "values": {
                "page": {"margin_left": 29.0},
                "par": {"text_override": {"font_size": 12.5}},
            },
        },
    )
    assert response.status_code == 200, response.text
    await _assert_invariant(test_session_factory, profile_id)


async def test_profile_create_delete_do_not_write_legacy_tables(client, test_session_factory):
    profile_id = await _create_profile(client)

    async with test_session_factory() as session:
        for model, _relation in ELEMENT_MODELS.values():
            count = await session.scalar(
                text(f"SELECT count(*) FROM {model.__tablename__} WHERE profile_id = :profile_id"),
                {"profile_id": profile_id},
            )
            assert count == 0, model.__tablename__
        heading_count = await session.scalar(
            text(
                f"SELECT count(*) FROM {HeadingLevelStyle.__tablename__} "
                "WHERE profile_id = :profile_id"
            ),
            {"profile_id": profile_id},
        )
        assert heading_count == 0

    # Пустой JSONB — штатное состояние fallback на старые таблицы.
    assert await _stored_options(test_session_factory, profile_id) == {}

    deleted = await client.delete(f"/profiles/{profile_id}")
    assert deleted.status_code == 204
    missing = await client.get(f"/profiles/{profile_id}/options")
    assert missing.status_code == 404
