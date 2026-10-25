"""Схема реестра опций для универсального UI."""

from dataclasses import asdict

from fastapi import APIRouter

from app.registry import GROUP_LABELS, OPTIONS, SCHEMA_VERSION

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/options")
def get_registry_options() -> dict[str, object]:
    """Описание всех опций: тип, границы, enum, подпись и порядок в UI."""
    groups = [{"id": group, "label": label} for group, label in GROUP_LABELS.items()]
    options = []
    for option in OPTIONS:
        payload = asdict(option)
        payload["group_label"] = GROUP_LABELS.get(option.group, option.group)
        options.append(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "groups": groups,
        "options": options,
    }
