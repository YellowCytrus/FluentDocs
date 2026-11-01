"""Создание seed-профиля «СТУ СФУ» из значений реестра (G6).

По умолчанию пишет JSON-снимок `docs/sprint/sfu_profile.json`.
С флагом `--db` создаёт профиль в базе (если профиля с таким именем нет).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.sfu_seed import SFU_PROFILE_NAME, build_sfu_values, sfu_overrides

DEFAULT_OUTPUT = Path("docs/sprint/sfu_profile.json")


def _validate() -> dict[str, object]:
    """Проверяет, что все seed-значения адресуют существующие опции."""
    unknown = [option_id for option_id in sfu_overrides() if option_id not in OPTIONS_BY_ID]
    if unknown:
        raise SystemExit(f"неизвестные опции в seed: {', '.join(unknown)}")
    return normalize_values(build_sfu_values())


def _write_snapshot(output: Path, sources: dict[str, str]) -> None:
    payload = {
        "name": SFU_PROFILE_NAME,
        "schema_version": SCHEMA_VERSION,
        "values": _validate(),
        "sources": sources,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


async def _create_profile() -> None:
    from sqlalchemy import select

    from app.database import async_session_factory, engine
    from app.models.sqlalchemy.profile import Profile

    values = _validate()
    async with async_session_factory() as session:
        existing = await session.scalar(select(Profile).where(Profile.name == SFU_PROFILE_NAME))
        if existing is not None:
            print(f"профиль «{SFU_PROFILE_NAME}» уже существует (id={existing.id})")
            return
        profile = Profile(
            name=SFU_PROFILE_NAME,
            options=values,
            options_schema_version=SCHEMA_VERSION,
        )
        session.add(profile)
        await session.commit()
        print(f"создан профиль «{SFU_PROFILE_NAME}» (id={profile.id})")
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--db", action="store_true", help="создать профиль в базе")
    args = parser.parse_args()

    sources = {option_id: source for option_id, (_value, source) in sfu_overrides().items()}
    _write_snapshot(args.output, sources)
    print(f"записан снимок {args.output} ({len(sources)} значений с источником)")
    if args.db:
        asyncio.run(_create_profile())


if __name__ == "__main__":
    main()
