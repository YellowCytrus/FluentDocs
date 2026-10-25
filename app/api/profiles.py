"""
CRUD для стилевых профилей: POST/GET/PATCH/DELETE /profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import get_profile_repository
from app.models.pydantic.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.models.pydantic.profile_options import ProfileOptionsRead, ProfileOptionsUpdate
from app.models.sqlalchemy.profile import Profile
from app.registry import (
    SCHEMA_VERSION,
    RegistryError,
    RegistryVersionError,
    apply_values_to_legacy,
    normalize_values,
    options_payload,
)
from app.repositories.profile_repository import ProfileRepository

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileRead)
async def create_profile(
    body: ProfileCreate,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> Profile:
    return await repo.create(body.name)


@router.get("", response_model=list[ProfileRead])
async def list_profiles(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: ProfileRepository = Depends(get_profile_repository),
) -> list[Profile]:
    return await repo.list(limit=limit, offset=offset)


@router.get("/{profile_id}", response_model=ProfileRead)
async def get_profile(
    profile_id: int,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> Profile:
    profile = await repo.get_by_id(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: int,
    body: ProfileUpdate,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> Profile:
    profile = await repo.update(profile_id, body)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/{profile_id}/options", response_model=ProfileOptionsRead)
async def get_profile_options(
    profile_id: int,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> ProfileOptionsRead:
    profile = await repo.get_by_id_with_styles(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        values, source = options_payload(profile)
    except RegistryVersionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RegistryError as exc:
        raise HTTPException(status_code=409, detail=f"Повреждённые опции профиля: {exc}") from exc
    return ProfileOptionsRead(
        schema_version=profile.options_schema_version or SCHEMA_VERSION,
        source=source,
        values=values,
    )


@router.put("/{profile_id}/options", response_model=ProfileOptionsRead)
async def put_profile_options(
    profile_id: int,
    body: ProfileOptionsUpdate,
    repo: ProfileRepository = Depends(get_profile_repository),
    session: AsyncSession = Depends(get_session),
) -> ProfileOptionsRead:
    if body.schema_version != SCHEMA_VERSION:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Неподдерживаемая версия схемы опций {body.schema_version}; "
                f"ожидается {SCHEMA_VERSION}"
            ),
        )
    profile = await repo.get_by_id_with_styles(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        values = normalize_values(body.values)
    except RegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await apply_values_to_legacy(session, profile_id, values)
    profile.options = values
    profile.options_schema_version = SCHEMA_VERSION
    await session.flush()

    return ProfileOptionsRead(
        schema_version=SCHEMA_VERSION,
        source="jsonb",
        values=values,
    )


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: int,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> None:
    deleted = await repo.delete(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
