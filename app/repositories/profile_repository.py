"""Profile repository: data access for profiles."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pydantic.profile import ProfileUpdate
from app.models.sqlalchemy.profile import Profile
from app.models.sqlalchemy.styles import (
    BulletListStyle,
    EquationStyle,
    FigureStyle,
    FootnoteStyle,
    HeadingLevelStyle,
    NumberedListStyle,
    OutlineStyle,
    ParStyle,
    QuoteStyle,
    RawStyle,
    TableStyle,
    TermsStyle,
)


class ProfileNameConflictError(Exception):
    """Имя профиля уже занято: API отвечает 409, а не 500."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, profile_id: int) -> Profile | None:
        result = await self._session.execute(select(Profile).where(Profile.id == profile_id))
        return result.scalars().one_or_none()

    async def get_by_id_with_styles(self, profile_id: int) -> Profile | None:
        """Загружает профиль с eager load всех style-связей для генерации PDF."""
        result = await self._session.execute(
            select(Profile)
            .where(Profile.id == profile_id)
            .options(
                selectinload(Profile.bullet_list_style).selectinload(
                    BulletListStyle.text_override_style
                ),
                selectinload(Profile.document_style),
                selectinload(Profile.equation_style).selectinload(
                    EquationStyle.text_override_style
                ),
                selectinload(Profile.figure_style).selectinload(FigureStyle.text_override_style),
                selectinload(Profile.footnote_style).selectinload(
                    FootnoteStyle.text_override_style
                ),
                selectinload(Profile.heading_style),
                selectinload(Profile.heading_level_styles).selectinload(
                    HeadingLevelStyle.text_override_style
                ),
                selectinload(Profile.numbered_list_style).selectinload(
                    NumberedListStyle.text_override_style
                ),
                selectinload(Profile.outline_style).selectinload(OutlineStyle.text_override_style),
                selectinload(Profile.page_style),
                selectinload(Profile.par_style).selectinload(ParStyle.text_override_style),
                selectinload(Profile.quote_style).selectinload(QuoteStyle.text_override_style),
                selectinload(Profile.raw_style).selectinload(RawStyle.text_override_style),
                selectinload(Profile.table_style).selectinload(TableStyle.text_override_style),
                selectinload(Profile.terms_style).selectinload(TermsStyle.text_override_style),
            )
        )
        return result.scalars().one_or_none()

    async def list(self, limit: int, offset: int) -> list[Profile]:
        result = await self._session.execute(
            select(Profile).order_by(Profile.id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def _ensure_name_is_free(self, name: str, profile_id: int | None = None) -> None:
        query = select(Profile.id).where(Profile.name == name)
        if profile_id is not None:
            query = query.where(Profile.id != profile_id)
        existing = await self._session.scalar(query)
        if existing is not None:
            raise ProfileNameConflictError(name)

    async def create(self, name: str) -> Profile:
        await self._ensure_name_is_free(name)
        profile = Profile(name=name)
        self._session.add(profile)
        try:
            await self._session.flush()
        except IntegrityError as exc:  # гонка двух одновременных запросов
            raise ProfileNameConflictError(name) from exc
        await self._session.refresh(profile)
        return profile

    async def update(self, profile_id: int, data: ProfileUpdate) -> Profile | None:
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None
        if data.name is not None and data.name != profile.name:
            await self._ensure_name_is_free(data.name, profile_id)
            profile.name = data.name
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ProfileNameConflictError(data.name or profile.name) from exc
        await self._session.refresh(profile)
        return profile

    async def delete(self, profile_id: int) -> bool:
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return False
        await self._session.delete(profile)
        await self._session.flush()
        return True
