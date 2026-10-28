"""G2c: штатные интервалы элементов вынесены в реестр."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values
from golden_helpers import DOCS_DIR, build_source, default_profile

SPACING_IDS = tuple(
    option.id
    for option in OPTIONS_BY_ID.values()
    if option.id.endswith(".spacing_before") or option.id.endswith(".spacing_after")
)

DEFAULTS = {
    "heading.h1.spacing_before": 1.8,
    "heading.h1.spacing_after": 0.75,
    "heading.h2.spacing_before": 1.44,
    "heading.h2.spacing_after": 0.75,
    "heading.h3.spacing_before": 1.44,
    "heading.h3.spacing_after": 0.75,
    "heading.h4.spacing_before": 1.44,
    "heading.h4.spacing_after": 0.75,
    "heading.h5.spacing_before": 1.44,
    "heading.h5.spacing_after": 0.75,
    "heading.h6.spacing_before": 1.44,
    "heading.h6.spacing_after": 0.75,
    "figure.spacing_before": 1.2,
    "figure.spacing_after": 1.2,
    "table.spacing_before": 1.2,
    "table.spacing_after": 1.2,
    "equation.spacing_before": 1.2,
    "equation.spacing_after": 1.2,
    "quote.spacing_before": 2.4,
    "quote.spacing_after": 1.8,
    "raw.spacing_before": 1.2,
    "raw.spacing_after": 1.2,
    "terms.spacing_before": 1.2,
    "terms.spacing_after": 1.2,
    "bullet_list.spacing_before": 1.2,
    "bullet_list.spacing_after": 1.2,
    "numbered_list.spacing_before": 1.2,
    "numbered_list.spacing_after": 1.2,
}


def _set_path(values: dict, path: tuple[str, ...], value: float) -> None:
    current = values
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value


def _get_path(values, path: tuple[str, ...]):
    current = values
    for key in path:
        current = current[key]
    return current


def test_element_spacing_options() -> None:
    assert set(SPACING_IDS) == set(DEFAULTS)
    values = default_values()
    for option_id in SPACING_IDS:
        option = OPTIONS_BY_ID[option_id]
        assert option.default == pytest.approx(DEFAULTS[option_id])
        assert option.unit == "em"
        assert option.legacy is False
        assert "СТУ" in option.source
        assert option.test_ids
        # Дефолт совпадает с текущим штатным интервалом Typst.
        target = (
            values["heading_levels"][option.path[1]]
            if option.path[0] == "heading_levels"
            else values[option.path[0]]
        )
        assert target[option.path[-1]] == pytest.approx(DEFAULTS[option_id])
        # Значение меняется и снова читается из JSONB-формы.
        _set_path(values, option.path, 4.0)
        assert _get_path(values, option.path) == 4.0
        assert normalize_values(values) is not None


def _profile_with(option_id: str, value: float):
    values = default_values()
    _set_path(values, OPTIONS_BY_ID[option_id].path, value)
    profile = default_profile()
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return profile


def _render(markdown: str, profile, tmp_path: Path, name: str) -> Path:
    site = tmp_path / name
    site.mkdir(parents=True, exist_ok=True)
    (site / "input.typ").write_text(build_source(markdown, profile), encoding="utf-8")
    shutil.copy(DOCS_DIR / "sample.png", site / "sample.png")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=site,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return site / "output.pdf"


def _span(pdf_path: Path) -> float:
    """Расстояние START→END по вертикали: чувствительно к интервалам элемента."""
    with pdfplumber.open(pdf_path) as pdf:
        lines = []
        for page in pdf.pages:
            lines.extend(page.extract_text_lines())
    start = next(line for line in lines if line["text"].strip() == "START")
    end = next(line for line in lines if line["text"].strip() == "END")
    return end["top"] - start["top"]


def _markdown(group: str, level: int = 1) -> str:
    if group == "heading":
        heading = "#" * level + " Заголовок"
        return f"START\n\n{heading}\n\nEND\n"
    body = {
        "figure": "![Alt](sample.png){width=5%}",
        "table": "| A | B |\n|---|---|\n| 1 | 2 |",
        "equation": "$$E = mc^2$$",
        "quote": "> Цитата для проверки отступа.",
        "raw": "```\ncode block\n```",
        "terms": "Термин\n: Определение термина.",
        "bullet_list": "- Первый пункт\n- Второй пункт",
        "numbered_list": "1. Первый пункт\n2. Второй пункт",
    }[group]
    return f"START\n\n{body}\n\nEND\n"


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("option_id", SPACING_IDS)
def test_element_spacing_render(option_id: str, tmp_path: Path) -> None:
    option = OPTIONS_BY_ID[option_id]
    group = option.path[0]
    level = int(option.path[1]) if group == "heading_levels" else 1
    markdown = _markdown("heading" if group == "heading_levels" else group, level)
    base = _span(_render(markdown, _profile_with(option_id, option.default), tmp_path, "base"))
    wide_value = min(float(option.default) + 5.0, 20.0)
    wide = _span(
        _render(
            markdown,
            _profile_with(option_id, wide_value),
            tmp_path,
            "wide",
        )
    )
    # Интервал указан в em от кегля документа: сдвиг равен изменению в pt.
    expected = (wide_value - float(option.default)) * 12.0
    assert wide - base == pytest.approx(expected, abs=0.5)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(
    ("group", "marker"),
    [("bullet_list", "- "), ("numbered_list", "1. ")],
)
def test_list_item_wrapped_line_indent(group: str, marker: str, tmp_path: Path) -> None:
    """list.item: перенесённая строка пункта управляется body_indent."""
    markdown = marker + ("Длинный пункт списка для проверки переноса строки. " * 20) + "\n"
    option_id = f"{group}.body_indent"
    base_indent = float(OPTIONS_BY_ID[option_id].default)
    delta_mm = 6.0
    base = _render(markdown, _profile_with(option_id, base_indent), tmp_path, "wrap-base")
    wide = _render(
        markdown, _profile_with(option_id, base_indent + delta_mm), tmp_path, "wrap-wide"
    )

    def wrapped_x(path: Path) -> tuple[float, float]:
        with pdfplumber.open(path) as pdf:
            lines = pdf.pages[0].extract_text_lines()
        assert len(lines) >= 2, "пункт списка не переносится"
        return lines[0]["x0"], lines[1]["x0"]

    base_first, base_wrapped = wrapped_x(base)
    wide_first, wide_wrapped = wrapped_x(wide)
    # Первая строка начинается с маркера, перенесённая — правее (висячий отступ).
    assert base_wrapped > base_first
    assert wide_first == pytest.approx(base_first, abs=0.5)
    assert wide_wrapped - base_wrapped == pytest.approx(delta_mm * 72 / 25.4, abs=0.5)
