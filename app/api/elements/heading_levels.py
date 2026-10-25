"""Custom router for heading level styles (heading/1..6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.elements.text_override import apply_text_override
from app.database import get_session
from app.deps import get_profile_repository
from app.models.pydantic.heading_level import HeadingLevelStyles, HeadingLevelStylesUpdate
from app.models.sqlalchemy.styles import HeadingLevelStyle
from app.registry import sync_options_jsonb
from app.repositories.profile_repository import ProfileRepository

router = APIRouter(
    prefix="/profiles/{profile_id}/heading",
    tags=["heading_level"],
)


async def _get_or_create_level(
    session: AsyncSession, profile_id: int, level: int
) -> HeadingLevelStyle:
    result = await session.execute(
        select(HeadingLevelStyle).where(
            HeadingLevelStyle.profile_id == profile_id,
            HeadingLevelStyle.level == level,
        )
    )
    row = result.scalars().one_or_none()
    if row is not None:
        return row
    row = HeadingLevelStyle(profile_id=profile_id, level=level)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


@router.get("/{level}", response_model=HeadingLevelStyles)
async def get_heading_level(
    profile_id: int,
    level: int,
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    session: AsyncSession = Depends(get_session),
) -> HeadingLevelStyles:
    if level < 1 or level > 6:
        raise HTTPException(status_code=400, detail="Level must be 1-6")
    if await profile_repo.get_by_id(profile_id) is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    row = await _get_or_create_level(session, profile_id, level)
    return HeadingLevelStyles.model_validate(row, from_attributes=True)


@router.patch("/{level}", response_model=HeadingLevelStyles)
async def patch_heading_level(
    profile_id: int,
    level: int,
    body: HeadingLevelStylesUpdate,
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    session: AsyncSession = Depends(get_session),
) -> HeadingLevelStyles:
    if level < 1 or level > 6:
        raise HTTPException(status_code=400, detail="Level must be 1-6")
    if await profile_repo.get_by_id(profile_id) is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    row = await _get_or_create_level(session, profile_id, level)
    dump = body.model_dump(exclude_unset=True)
    had_text_override = "text_override" in dump
    text_override_val = dump.pop("text_override", None)
    for key, value in dump.items():
        if hasattr(row, key):
            setattr(row, key, value)
    if had_text_override:
        await apply_text_override(session, row, text_override_val)
    await session.flush()
    await session.refresh(row)
    await sync_options_jsonb(session, profile_id)
    return HeadingLevelStyles.model_validate(row, from_attributes=True)


@router.put("/{level}", response_model=HeadingLevelStyles)
async def put_heading_level(
    profile_id: int,
    level: int,
    body: HeadingLevelStyles,
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    session: AsyncSession = Depends(get_session),
) -> HeadingLevelStyles:
    if level < 1 or level > 6:
        raise HTTPException(status_code=400, detail="Level must be 1-6")
    if await profile_repo.get_by_id(profile_id) is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    row = await _get_or_create_level(session, profile_id, level)
    row.outlined = body.outlined
    row.bookmarked = body.bookmarked
    row.offset = body.offset
    row.break_before = body.break_before
    row.numbering_enabled = body.numbering_enabled
    to_data = body.text_override.model_dump() if body.text_override is not None else None
    await apply_text_override(session, row, to_data)
    await session.flush()
    await session.refresh(row)
    await sync_options_jsonb(session, profile_id)
    return HeadingLevelStyles.model_validate(row, from_attributes=True)
