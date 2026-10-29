"""G4: границы таблиц, шапка, курсив букв и метки продолжения."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values
from app.utils.typst_config import config_tree
from golden_helpers import build_source, default_profile


def _profile(**changes: object):
    values = default_values()
    for section, section_values in changes.items():
        target = values[section]
        assert isinstance(target, dict)
        target.update(section_values)  # type: ignore[arg-type]
    profile = default_profile()
    profile.options = normalize_values(values)
    profile.options_schema_version = SCHEMA_VERSION
    return profile


def _compile(markdown: str, profile, tmp_path: Path, name: str) -> Path:
    site = tmp_path / name
    site.mkdir(parents=True, exist_ok=True)
    (site / "input.typ").write_text(build_source(markdown, profile), encoding="utf-8")
    result = subprocess.run(
        ["typst", "compile", "input.typ", "output.pdf"],
        cwd=site,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return site / "output.pdf"


def _table_lines(path: Path) -> tuple[list[float], list[float]]:
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        vertical = sorted(
            {
                round(float(line["x0"]), 1)
                for line in page.lines
                if abs(float(line["x0"]) - float(line["x1"])) < 0.1
            }
        )
        horizontal = sorted(
            {
                round(float(line["top"]), 1)
                for line in page.lines
                if abs(float(line["top"]) - float(line["bottom"])) < 0.1
            }
        )
    return vertical, horizontal


def _page_texts(path: Path) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def test_g4_table_options_schema() -> None:
    expected = {
        "table.border_top": True,
        "table.border_bottom": True,
        "table.border_left": True,
        "table.border_right": True,
        "table.border_inside_horizontal": True,
        "table.border_inside_vertical": True,
        "table.header_double_line": False,
        "table.header_double_gap": 0.5,
        "table.repeat_header": True,
        "table.italic_letters": False,
        "table.continuation_label": False,
        "table.continuation_template": "Продолжение таблицы {n}",
        "table.final_template": "Окончание таблицы {n}",
    }
    for option_id, default in expected.items():
        option = OPTIONS_BY_ID[option_id]
        assert option.default == default, option_id
        assert option.legacy is False
        assert option.test_ids
        assert "СТУ" in option.source
        assert "значение хранится в профиле" not in option.rationale

    assert OPTIONS_BY_ID["table.header_double_stroke"].unit == "mm"
    assert OPTIONS_BY_ID["table.header_double_gap"].unit == "mm"

    values = default_values()
    values["table"].update(
        {
            "border_left": False,
            "border_inside_horizontal": False,
            "header_double_line": True,
            "header_double_gap": 1.2,
            "repeat_header": False,
            "italic_letters": True,
            "continuation_label": True,
            "continuation_template": "Продолжение {n}",
            "final_template": "Окончание {n}",
        }
    )
    normalized = normalize_values(values)
    tree = config_tree(normalized)
    assert tree["table"]["border_left"] is False
    assert tree["table"]["border_inside_horizontal"] is False
    assert tree["table"]["header_double_line"] is True
    assert tree["table"]["header_double_gap"] == 1.2
    assert tree["table"]["repeat_header"] is False
    assert tree["table"]["italic_letters"] is True
    assert tree["table"]["continuation_label"] is True
    assert tree["table"]["continuation_template"] == "Продолжение {n}"
    assert tree["table"]["final_template"] == "Окончание {n}"


def test_g4_table_generation_typst() -> None:
    profile = _profile(
        table={
            "border_top": False,
            "border_bottom": False,
            "border_inside_vertical": False,
            "header_double_line": True,
            "repeat_header": False,
            "italic_letters": True,
            "continuation_label": True,
        }
    )
    source = build_source("Текст.\n", profile)
    assert "border_top: false" in source
    assert "border_bottom: false" in source
    assert "border_inside_vertical: false" in source
    assert "header_double_line: true" in source
    assert "repeat_header: false" in source
    assert "italic_letters: true" in source
    assert "continuation_label: true" in source


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_table_borders_render(tmp_path: Path) -> None:
    markdown = "# Глава\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\n: Подпись\n"
    default_path = _compile(markdown, _profile(), tmp_path, "borders-default")
    default_v, default_h = _table_lines(default_path)
    assert len(default_v) >= 3
    assert len(default_h) >= 4

    cases = [
        ("left", {"border_left": False}, "v", "min"),
        ("right", {"border_right": False}, "v", "max"),
        ("top", {"border_top": False}, "h", "min"),
        ("bottom", {"border_bottom": False}, "h", "max"),
        ("inside_vertical", {"border_inside_vertical": False}, "v", "inside"),
        ("inside_horizontal", {"border_inside_horizontal": False}, "h", "inside"),
    ]
    for name, changes, axis, kind in cases:
        path = _compile(
            markdown,
            _profile(table=changes),
            tmp_path,
            f"borders-{name}",
        )
        vertical, horizontal = _table_lines(path)
        values = vertical if axis == "v" else horizontal
        reference = default_v if axis == "v" else default_h
        if kind == "min":
            assert min(values) > min(reference) + 1, name
        elif kind == "max":
            assert max(values) < max(reference) - 1, name
        else:
            assert len(values) < len(reference), name
            if name == "inside_horizontal":
                assert len(values) == 2


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_table_double_header_render(tmp_path: Path) -> None:
    markdown = "# Глава\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\n: Подпись\n"
    path = _compile(
        markdown,
        _profile(
            table={
                "header_double_line": True,
                "header_double_gap": 0.5,
                "header_double_stroke": 0.2645833333,
            }
        ),
        tmp_path,
        "double-header",
    )
    _vertical, horizontal = _table_lines(path)
    assert len(horizontal) >= 5
    gaps = [horizontal[index + 1] - horizontal[index] for index in range(len(horizontal) - 1)]
    assert any(0.9 < gap < 2.0 for gap in gaps), gaps
    with pdfplumber.open(path) as pdf:
        lines = pdf.pages[0].lines
    assert any(
        abs(float(line["linewidth"]) - 0.75) < 0.15
        for line in lines
        if abs(float(line["top"]) - float(line["bottom"])) < 0.1
    )


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("repeat_header", [True, False])
def test_g4_table_repeat_header_render(tmp_path: Path, repeat_header: bool) -> None:
    rows = "\n".join(f"| Строка {index} | {index} |" for index in range(1, 121))
    markdown = f"| Заголовок1 | Заголовок2 |\n|---|---|\n{rows}\n"
    path = _compile(
        markdown,
        _profile(table={"repeat_header": repeat_header}),
        tmp_path,
        f"repeat-{repeat_header}",
    )
    pages = _page_texts(path)
    assert len(pages) >= 2
    assert "Заголовок1" in pages[0]
    assert ("Заголовок1" in pages[1]) is repeat_header


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("italic", [True, False])
def test_g4_table_italic_letters_render(tmp_path: Path, italic: bool) -> None:
    markdown = "| Лат | Греч | Слово | Кир |\n|---|---|---|---|\n| x | α | AB | б |\n"
    path = _compile(
        markdown,
        _profile(table={"italic_letters": italic}),
        tmp_path,
        f"italic-{italic}",
    )
    with pdfplumber.open(path) as pdf:
        chars = pdf.pages[0].chars

    def font(text: str) -> str:
        return next(str(char["fontname"]) for char in chars if char["text"] == text)

    assert ("Italic" in font("x")) is italic
    assert ("Italic" in font("α")) is italic
    assert "Italic" not in font("A")
    assert "Italic" not in font("б")


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_table_continuation_label_render(tmp_path: Path) -> None:
    rows = "\n".join(f"| Строка {index} | {index} |" for index in range(1, 181))
    markdown = f"| Показатель | Значение |\n|---|---|\n{rows}\n\n: Длинная таблица\n"
    path = _compile(
        markdown,
        _profile(
            table={
                "caption_template": "Таблица {n} — {content}",
                "caption_position": "above",
                "continuation_label": True,
            }
        ),
        tmp_path,
        "continuation",
    )
    pages = _page_texts(path)
    assert len(pages) >= 2
    assert "Продолжение таблицы 1" not in pages[0]
    assert "Окончание таблицы 1" not in pages[0]
    assert any(
        "Продолжение таблицы 1" in text or "Окончание таблицы 1" in text for text in pages[1:]
    )
    assert "Окончание таблицы 1" in pages[-1]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_table_inset_and_font_render(tmp_path: Path) -> None:
    markdown = "# Глава\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n: Подпись\n"
    default_path = _compile(
        markdown,
        _profile(),
        tmp_path,
        "inset-default",
    )
    wide_path = _compile(
        markdown,
        _profile(
            table={
                "inset": 5.0,
                "text_override": {"font_size": 8.0},
            }
        ),
        tmp_path,
        "inset-wide",
    )

    def cell_position(path: Path) -> tuple[float, object]:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            table_left = min(
                float(line["x0"])
                for line in page.lines
                if abs(float(line["x0"]) - float(line["x1"])) < 0.1
            )
            line = next(line for line in page.extract_text_lines() if line["text"].startswith("A "))
            return float(line["x0"]) - table_left, line

    default_offset, _default_line = cell_position(default_path)
    wide_offset, wide_line = cell_position(wide_path)
    assert wide_offset > default_offset + 5.0
    assert all(abs(float(char["size"]) - 8.0) < 0.2 for char in wide_line["chars"])
