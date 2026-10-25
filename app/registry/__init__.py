"""Публичный API реестра опций."""

from app.registry.options import (
    GROUP_LABELS,
    OPTIONS,
    OPTIONS_BY_ID,
    OPTIONS_BY_PATH,
    SCHEMA_VERSION,
    Option,
    JsonValue,
)
from app.registry.storage import (
    RegistryError,
    RegistryVersionError,
    apply_values_to_legacy,
    default_values,
    normalize_values,
    options_payload,
    serialize_profile,
    sync_options_jsonb,
    validate_value,
)

__all__ = [
    "GROUP_LABELS",
    "JsonValue",
    "OPTIONS",
    "OPTIONS_BY_ID",
    "OPTIONS_BY_PATH",
    "Option",
    "RegistryError",
    "RegistryVersionError",
    "SCHEMA_VERSION",
    "apply_values_to_legacy",
    "default_values",
    "normalize_values",
    "options_payload",
    "serialize_profile",
    "sync_options_jsonb",
    "validate_value",
]
