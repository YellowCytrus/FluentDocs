"""G2a: окружение «до/после» — схема, генерация, API и измерения PDF."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, RegistryError, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values, validate_value
from app.utils.typst_source import build_typst_preamble
from golden_helpers import build_source, default_profile

LINE_PT = 5.08 * 72 / 25.4  # document.line_spacing по умолчанию, 5.08 мм


def _source(around: dict) -> str:
    profile = default_profile()
    values = default_values()
    values["around"].update(around)
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return build_typst_preamble(profile)


def _text_item(content: str = "ДО") -> dict:
    return {"type": "text", "content": content, "text_override": None, "align": "left"}


def _blank(count: int = 1, value: float = 1.0, mode: str = "multiplier") -> dict:
    return {"type": "blank", "count": count, "line_spacing": {"mode": mode, "value": value}}


def _assert_target_options(target: str) -> None:
    source = _source(
        {
            target: {
                "before": [_text_item()],
                "after": [_blank(count=2, value=6.0, mode="mm")],
                "collapse": "sum",
            }
        }
    )
    assert f"    {target}: (" in source
    assert 'content: "ДО"' in source
    assert "count: 2" in source
    assert 'mode: "mm"' in source
    assert "value: 6.0" in source
    assert 'collapse: "sum"' in source


def test_around_heading_1_options() -> None:
    _assert_target_options("heading_1")


def test_around_heading_2_options() -> None:
    _assert_target_options("heading_2")


def test_around_heading_3_options() -> None:
    _assert_target_options("heading_3")


def test_around_heading_4_options() -> None:
    _assert_target_options("heading_4")


def test_around_heading_5_options() -> None:
    _assert_target_options("heading_5")


def test_around_heading_6_options() -> None:
    _assert_target_options("heading_6")


def test_around_par_options() -> None:
    _assert_target_options("par")


def test_around_bullet_list_options() -> None:
    _assert_target_options("bullet_list")


def test_around_numbered_list_options() -> None:
    _assert_target_options("numbered_list")


def test_around_table_options() -> None:
    _assert_target_options("table")


def test_around_figure_options() -> None:
    _assert_target_options("figure")


def test_around_equation_options() -> None:
    _assert_target_options("equation")


def test_around_quote_options() -> None:
    _assert_target_options("quote")


def test_around_raw_options() -> None:
    _assert_target_options("raw")


def test_around_terms_options() -> None:
    _assert_target_options("terms")


def test_around_item_schema_contract() -> None:
    option = OPTIONS_BY_ID["around.table.after"]
    assert option.type == "list"
    assert option.item_fields
    assert option.item_variants
    assert {value for value, _ in option.item_variants} == {
        "blank",
        "text",
        "line",
        "pagebreak",
    }
    fields = {field.path[-1]: field for field in option.item_fields}
    assert fields["type"].required is True
    assert fields["count"].default == 1
    assert fields["line_spacing"].type == "object"
    assert fields["line_spacing"].fields
    assert fields["text_override"].nullable is True
    assert fields["content"].required is True
    assert fields["length"].unit == "%"
    assert fields["stroke_mm"].unit == "mm"
    assert fields["weak"].default is True


def test_around_validation_rejects_unknown_and_required() -> None:
    with pytest.raises(RegistryError):
        normalize_values({"around": {"unknown": {"before": []}}})
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"unknown": []}}})
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"after": [{"type": "blank", "unknown": 1}]}}})
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"after": [{"count": 1}]}}})
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"after": [{"type": "text"}]}}})
    with pytest.raises(RegistryError):
        normalize_values(
            {
                "around": {
                    "table": {
                        "after": [
                            {
                                "type": "blank",
                                "line_spacing": {"mode": "mm", "absolute": 1},
                            }
                        ]
                    }
                }
            }
        )
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"after": [{"type": "line", "length": 101}]}}})
    with pytest.raises(RegistryError):
        normalize_values({"around": {"table": {"collapse": "bogus"}}})


def test_around_object_and_list_validation_are_recursive() -> None:
    option = OPTIONS_BY_ID["around.table.after"]
    value = validate_value(
        option,
        [
            {
                "type": "blank",
                "count": 0,
                "line_spacing": {"mode": "multiplier"},
            },
            {"type": "pagebreak", "weak": False},
        ],
    )
    assert value == [
        {
            "type": "blank",
            "count": 0,
            "line_spacing": {"mode": "multiplier", "value": 1.0},
        },
        {"type": "pagebreak", "weak": False},
    ]


async def _create_profile(client) -> int:
    response = await client.post("/profiles", json={"name": f"Around {uuid.uuid4().hex[:8]}"})
    assert response.status_code == 200
    return response.json()["id"]


async def test_options_around_roundtrip_and_legacy_write(client) -> None:
    profile_id = await _create_profile(client)
    around = {
        "table": {
            "before": [_text_item("ДО ТАБЛИЦЫ")],
            "after": [_blank(count=2, value=4.0, mode="mm")],
            "collapse": "sum",
        },
        "heading_1": {"before": [_blank(count=0)], "collapse": "none"},
    }
    put = await client.put(
        f"/profiles/{profile_id}/options",
        json={"schema_version": SCHEMA_VERSION, "values": {"around": around}},
    )
    assert put.status_code == 200, put.text

    got = await client.get(f"/profiles/{profile_id}/options")
    assert got.status_code == 200
    assert got.json()["values"]["around"]["table"]["collapse"] == "sum"
    assert got.json()["values"]["around"]["table"]["after"][0]["count"] == 2
    assert got.json()["values"]["around"]["heading_1"]["collapse"] == "none"

    # Запись в старую таблицу не должна затирать around, которого там нет.
    patched = await client.patch(f"/profiles/{profile_id}/page", json={"margin_left": 21.0})
    assert patched.status_code == 200
    after_patch = await client.get(f"/profiles/{profile_id}/options")
    assert after_patch.json()["values"]["around"]["table"]["before"][0]["content"] == ("ДО ТАБЛИЦЫ")

    bad = await client.put(
        f"/profiles/{profile_id}/options",
        json={
            "schema_version": SCHEMA_VERSION,
            "values": {"around": {"table": {"after": [{"type": "text"}]}}},
        },
    )
    assert bad.status_code == 400


def _render(around: dict, markdown: str, tmp_path) -> Path:
    profile = default_profile()
    values = default_values()
    values["around"].update(around)
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    source = build_source(markdown, profile)
    site = Path(tmp_path)
    site.mkdir(parents=True, exist_ok=True)
    (site / "input.typ").write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=site,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return site / "output.pdf"


def _table_heading_gap(page) -> float:
    table_bottom = max(line["bottom"] for line in page.lines if line["top"] > 80)
    heading_top = min(
        char["top"]
        for char in page.chars
        if char["text"] == "С" and char["x0"] < 100 and char["top"] > table_bottom - 5
    )
    return heading_top - table_bottom


TABLE_DOC = "# Заголовок\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n# Следующий\n"


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_around_render_spacing_max_sum_none(tmp_path) -> None:
    blank = _blank(count=1)
    base = _table_heading_gap(pdfplumber.open(_render({}, TABLE_DOC, tmp_path / "base")).pages[0])
    max_pdf = pdfplumber.open(
        _render(
            {
                "table": {"after": [blank]},
                "heading_1": {"before": [blank]},
            },
            TABLE_DOC,
            tmp_path / "max",
        )
    )
    sum_pdf = pdfplumber.open(
        _render(
            {
                "table": {"after": [blank], "collapse": "sum"},
                "heading_1": {"before": [blank], "collapse": "sum"},
            },
            TABLE_DOC,
            tmp_path / "sum",
        )
    )
    none_pdf = pdfplumber.open(
        _render(
            {
                "table": {"after": [blank], "collapse": "none"},
                "heading_1": {"before": [blank], "collapse": "none"},
            },
            TABLE_DOC,
            tmp_path / "none",
        )
    )
    with max_pdf as pdf:
        max_gap = _table_heading_gap(pdf.pages[0])
    with sum_pdf as pdf:
        sum_gap = _table_heading_gap(pdf.pages[0])
    with none_pdf as pdf:
        none_gap = _table_heading_gap(pdf.pages[0])

    # max: одна слабая пустая строка, Typst схлопывает её с отступом заголовка.
    assert abs(max_gap - LINE_PT) < 3.0
    # sum: обе пустые строки жёсткие и складываются с отступом заголовка.
    assert abs((sum_gap - base) - 2 * LINE_PT) < 1.0
    # none: пустые строки не вставляются, отступ остаётся штатным.
    assert abs(none_gap - base) < 0.5


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_around_render_count_zero_and_top_of_page(tmp_path) -> None:
    base_page = pdfplumber.open(_render({}, TABLE_DOC, tmp_path / "base")).pages[0]
    base_gap = _table_heading_gap(base_page)
    zero_pdf = pdfplumber.open(
        _render(
            {"table": {"after": [_blank(count=0)]}},
            TABLE_DOC,
            tmp_path / "zero",
        )
    )
    with zero_pdf as pdf:
        assert abs(_table_heading_gap(pdf.pages[0]) - base_gap) < 0.5

    top_doc = "# Верх\n\nТекст.\n"
    base_top = min(
        char["top"]
        for char in pdfplumber.open(_render({}, top_doc, tmp_path / "top-base")).pages[0].chars
    )
    weak_pdf = pdfplumber.open(
        _render(
            {
                "heading_1": {
                    "before": [_blank(count=5, value=10.0, mode="mm")],
                    "collapse": "max",
                }
            },
            top_doc,
            tmp_path / "top-weak",
        )
    )
    hard_pdf = pdfplumber.open(
        _render(
            {
                "heading_1": {
                    "before": [_blank(count=5, value=10.0, mode="mm")],
                    "collapse": "sum",
                }
            },
            top_doc,
            tmp_path / "top-hard",
        )
    )
    with weak_pdf as pdf:
        weak_top = min(char["top"] for char in pdf.pages[0].chars)
    with hard_pdf as pdf:
        hard_top = min(char["top"] for char in pdf.pages[0].chars)
    assert abs(weak_top - base_top) < 0.5
    assert hard_top > base_top + 50


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_around_render_text_line_and_pagebreak(tmp_path) -> None:
    text_pdf = pdfplumber.open(
        _render(
            {
                "table": {
                    "after": [
                        {
                            "type": "text",
                            "content": "ВСТАВКА",
                            "text_override": None,
                            "align": "center",
                        }
                    ]
                }
            },
            TABLE_DOC,
            tmp_path / "text",
        )
    )
    with text_pdf as pdf:
        page_text = pdf.pages[0].extract_text() or ""
        assert "ВСТАВКА" in page_text
        assert page_text.index("ВСТАВКА") < page_text.index("Следующий")

    base_lines = len(pdfplumber.open(_render({}, TABLE_DOC, tmp_path / "line-base")).pages[0].lines)
    line_pdf = pdfplumber.open(
        _render(
            {"table": {"after": [{"type": "line", "length": 100, "stroke_mm": 0.5}]}},
            TABLE_DOC,
            tmp_path / "line",
        )
    )
    with line_pdf as pdf:
        assert len(pdf.pages[0].lines) == base_lines + 1

    break_pdf = pdfplumber.open(
        _render(
            {"table": {"after": [{"type": "pagebreak", "weak": False}]}},
            TABLE_DOC,
            tmp_path / "break",
        )
    )
    with break_pdf as pdf:
        assert len(pdf.pages) == 2
        assert "Следующий" in (pdf.pages[1].extract_text() or "")
