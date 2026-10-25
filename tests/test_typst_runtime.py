"""Единая сборка Typst: fd, литерал конфига и паритет превью/сервера."""

from __future__ import annotations

from typing import cast

import pytest

from app.registry import SCHEMA_VERSION, RegistryVersionError, normalize_values
from app.registry.options import JsonValue
from app.utils.typst_source import (
    FD_LIBRARY_PATH,
    build_typst_preamble,
    build_typst_source,
    fd_library_source,
)
from golden_helpers import default_profile, text_override_profile


def test_fd_library_is_embedded_once():
    assert FD_LIBRARY_PATH.is_file()
    source = build_typst_preamble(default_profile())
    assert source.count("#let fd = {") == 1
    assert "#let fd-config = (" in source
    assert "#show: fd.apply.with(fd-config)" in source
    assert "text-override-body" in fd_library_source()


def test_config_literal_contains_all_elements_and_defaults():
    source = build_typst_preamble(default_profile())
    for element in (
        "page:",
        "document:",
        "par:",
        "heading:",
        "heading_levels:",
        "bullet_list:",
        "numbered_list:",
        "terms:",
        "table:",
        "figure:",
        "equation:",
        "quote:",
        "footnote:",
        "raw:",
        "outline:",
    ):
        assert f"  {element}" in source
    assert 'paper: "a4"' in source
    assert "margin_top: 25.0" in source
    assert 'numbering: "1.1.1"' in source


def test_config_uses_jsonb_values_before_legacy_rows():
    profile = default_profile()
    profile.options = normalize_values({"page": {"margin_left": 31.5}})
    profile.options_schema_version = SCHEMA_VERSION
    source = build_typst_preamble(profile)
    assert "margin_left: 31.5" in source
    # Старая таблица остаётся с дефолтом, JSONB выигрывает.
    assert "margin_left: 25.0" not in source


def test_hyphenate_true_false_auto_is_typst_value():
    for raw, expected in (
        (True, "hyphenate: true"),
        (False, "hyphenate: false"),
        (None, "hyphenate: auto"),
    ):
        profile = default_profile()
        profile.document_style.hyphenate = raw
        assert expected in build_typst_preamble(profile)


def test_text_override_profile_serializes_override_fields():
    source = build_typst_preamble(text_override_profile())
    assert 'font: "DejaVu Sans"' in source
    assert "font_size: 13.0" in source
    assert 'fill: "#7a1f1f"' in source
    assert "show par: it => text-override-body" in source
    assert "show figure: it => text-override-body" in source


def test_source_matches_preview_concatenation():
    """Editor.vue: preamble + '\\n' + Pandoc body; сервер строит ровно это."""
    profile = default_profile()
    body = "= Заголовок\n\nТекст.\n"
    preamble = build_typst_preamble(profile)
    assert build_typst_source(profile, body) == preamble + "\n" + body


def test_source_title_order_default_and_sfu():
    profile = default_profile()
    preamble = build_typst_preamble(profile)
    title = "#pagebreak()\nTITLE"
    assert build_typst_source(profile, "BODY", title_source=title) == (
        preamble + "\n" + title + "\nBODY"
    )
    assert (
        build_typst_source(profile, "BODY", title_source=title, title_before_prefix=True)
        == title + "\n" + preamble + "\nBODY"
    )


def test_config_escaping_and_region_none():
    profile = default_profile()
    profile.document_style.font = 'A"B\\C'
    source = build_typst_preamble(profile)
    assert 'font: "A\\"B\\\\C"' in source
    assert "region: none" in source


def test_options_schema_version_error_is_reported():
    profile = default_profile()
    profile.options = cast(dict[str, JsonValue], {"page": {"paper": "a4"}})
    profile.options_schema_version = 999
    with pytest.raises(RegistryVersionError):
        build_typst_preamble(profile)
