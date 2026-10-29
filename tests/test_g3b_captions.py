"""G3b: подписи и нумерация рисунков и таблиц."""

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
from golden_helpers import DOCS_DIR, build_source, default_profile

APPENDIX_ENTITY = {
    "id": "appendix",
    "label": "Приложение",
    "match": {
        "target": "heading",
        "level": "1",
        "mode": "contains",
        "value": "Приложение",
        "case_insensitive": True,
    },
    "numbering": {
        "kind": "appendix",
        "mode": "own",
        "template": "{letter}",
        "start": 1,
        "sub_template": "{prefix}.{n}",
        "group": "appendix",
    },
    "apply": {
        "break_before": False,
        "align": "auto",
        "case": "none",
        "bold": False,
        "outlined": True,
        "around": {"before": [], "after": [], "before_collisions": []},
        "text_override": None,
    },
}


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
    if (DOCS_DIR / "sample.png").exists():
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


def _lines(pdf_path: Path) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        return [line["text"] for page in pdf.pages for line in page.extract_text_lines()]


def _line_top(pdf_path: Path, needle: str) -> float:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines():
                if needle in line["text"]:
                    return float(line["top"])
    raise AssertionError(f"строка не найдена: {needle}")


def test_caption_options_schema() -> None:
    expected = {
        "figure.caption_template": None,
        "figure.caption_position": "below",
        "figure.caption_align": "center",
        "figure.caption_separator": " — ",
        "table.caption_template": None,
        "table.caption_position": "above",
        "table.caption_align": "left",
        "table.caption_separator": " — ",
    }
    for option_id, default in expected.items():
        option = OPTIONS_BY_ID[option_id]
        assert option.default == default
        assert option.legacy is False
        assert option.test_ids
        assert "СТУ" in option.source
        assert "значение хранится в профиле" not in option.rationale

    figure_around = OPTIONS_BY_ID["figure.caption_around"]
    assert figure_around.type == "object"
    assert figure_around.default == {"before": [], "after": []}
    assert {field.path[-1] for field in figure_around.fields} == {"before", "after"}
    assert OPTIONS_BY_ID["figure.caption_text_override"].nullable is True
    assert {field.path[-1] for field in OPTIONS_BY_ID["figure.caption_text_override"].fields} >= {
        "font",
        "font_size",
        "weight",
        "style",
    }

    values = default_values()
    values["figure"]["caption_template"] = "Рисунок {h1}.{n} — {content}"
    values["table"]["caption_template"] = "Таблица {h1}.{n} — {content}"
    values["figure"]["caption_text_override"] = {"font_size": 8.0}
    normalized = normalize_values(values)
    tree = config_tree(normalized)
    assert tree["figure"]["caption_template"] == "Рисунок {h1}.{n} — {content}"
    assert tree["table"]["caption_template"] == "Таблица {h1}.{n} — {content}"
    assert tree["figure"]["caption_text_override"]["font_size"] == 8.0
    assert tree["figure"]["caption_around"] == {"before": [], "after": []}


def test_caption_generation_typst() -> None:
    profile = _profile(
        figure={
            "caption_template": "Рисунок {h1}.{n} — {content}",
            "caption_position": "below",
            "caption_align": "center",
            "caption_separator": " — ",
        },
        table={
            "caption_template": "Таблица {h1}.{n} — {content}",
            "caption_position": "above",
            "caption_align": "left",
            "caption_separator": " — ",
        },
    )
    source = build_source("Текст.\n", profile)
    assert 'caption_template: "Рисунок {h1}.{n} — {content}"' in source
    assert 'caption_template: "Таблица {h1}.{n} — {content}"' in source
    assert 'caption_position: "above"' in source
    assert 'caption_position: "below"' in source
    assert 'caption_align: "left"' in source
    assert 'caption_align: "center"' in source


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_figure_caption_render(tmp_path: Path) -> None:
    profile = _profile(
        figure={
            "caption_template": "Рисунок {h1}.{n} — {content}",
            "caption_position": "below",
            "caption_align": "center",
            "caption_separator": " — ",
        }
    )
    markdown = (
        "# Первая глава\n\n"
        "![Первый](sample.png){#fig:first}\n\n"
        "# Вторая глава\n\n"
        "![Второй](sample.png){#fig:second}\n"
    )
    lines = _lines(_compile(markdown, profile, tmp_path, "figure-caption"))
    assert "Рисунок 1.1 — Первый" in lines
    assert "Рисунок 2.1 — Второй" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_table_caption_render(tmp_path: Path) -> None:
    profile = _profile(
        table={
            "caption_template": "Таблица {h1}.{n} — {content}",
            "caption_position": "above",
            "caption_align": "left",
            "caption_separator": " — ",
        }
    )
    markdown = "# Глава\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n: Подпись таблицы\n"
    path = _compile(markdown, profile, tmp_path, "table-caption")
    lines = _lines(path)
    assert "Таблица 1.1 — Подпись таблицы" in lines
    assert _line_top(path, "Таблица 1.1") < _line_top(path, "A B")


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_caption_counters_separate_render(tmp_path: Path) -> None:
    profile = _profile(
        figure={"caption_template": "Рисунок {h1}.{n} — {content}"},
        table={"caption_template": "Таблица {h1}.{n} — {content}"},
    )
    markdown = (
        "# Глава\n\n"
        "![Рисунок](sample.png){#fig:one}\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        ": Таблица\n"
    )
    lines = _lines(_compile(markdown, profile, tmp_path, "caption-counters"))
    assert "Рисунок 1.1 — Рисунок" in lines
    assert "Таблица 1.1 — Таблица" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_caption_appendix_letter_render(tmp_path: Path) -> None:
    profile = _profile(
        structural={"entities": [APPENDIX_ENTITY]},
        figure={"caption_template": "Рисунок {h1}.{n} — {content}"},
        table={"caption_template": "Таблица {h1}.{n} — {content}"},
    )
    markdown = (
        "# Глава\n\n"
        "![Первый](sample.png){#fig:first}\n\n"
        "# Приложение Название\n\n"
        "![Второй](sample.png){#fig:second}\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        ": Таблица в приложении\n"
    )
    lines = _lines(_compile(markdown, profile, tmp_path, "caption-appendix"))
    assert "Рисунок 1.1 — Первый" in lines
    assert "Рисунок А.1 — Второй" in lines
    assert "Таблица А.1 — Таблица в приложении" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_table_caption_without_template_has_no_english(tmp_path: Path) -> None:
    profile = _profile()
    markdown = "| A | B |\n|---|---|\n| 1 | 2 |\n\n: Подпись таблицы\n"
    lines = _lines(_compile(markdown, profile, tmp_path, "table-no-template"))
    text = "\n".join(lines)
    assert "Подпись таблицы" in text
    assert "Table" not in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_figure_caption_around_render(tmp_path: Path) -> None:
    profile = _profile(
        figure={
            "caption_template": "Рисунок {h1}.{n} — {content}",
            "caption_around": {
                "before": [
                    {
                        "type": "text",
                        "content": "ДО",
                        "text_override": None,
                        "align": "left",
                    }
                ],
                "after": [
                    {
                        "type": "text",
                        "content": "ПОСЛЕ",
                        "text_override": None,
                        "align": "left",
                    }
                ],
            },
        }
    )
    lines = _lines(
        _compile(
            "# Глава\n\n![Первый](sample.png){#fig:a}\n",
            profile,
            tmp_path,
            "figure-caption-around",
        )
    )
    assert "ДО" in lines
    assert "ПОСЛЕ" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_figure_caption_text_override_render(tmp_path: Path) -> None:
    profile = _profile(
        figure={
            "caption_template": "Рисунок {h1}.{n} — {content}",
            "caption_text_override": {"font_size": 8.0},
        }
    )
    path = _compile(
        "# Глава\n\n![Первый](sample.png){#fig:a}\n",
        profile,
        tmp_path,
        "figure-caption-override",
    )
    with pdfplumber.open(path) as pdf:
        caption_sizes = [
            char["size"] for char in pdf.pages[0].chars if char["text"] == "Р" and char["size"] < 10
        ]
    assert caption_sizes
    assert all(abs(size - 8.0) < 0.2 for size in caption_sizes)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_table_caption_around_render(tmp_path: Path) -> None:
    profile = _profile(
        table={
            "caption_template": "Таблица {h1}.{n} — {content}",
            "caption_around": {
                "before": [
                    {
                        "type": "text",
                        "content": "ДО",
                        "text_override": None,
                        "align": "left",
                    }
                ],
                "after": [],
            },
        }
    )
    lines = _lines(
        _compile(
            "| A | B |\n|---|---|\n| 1 | 2 |\n\n: Таблица\n",
            profile,
            tmp_path,
            "table-caption-around",
        )
    )
    assert "ДО" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_table_caption_text_override_render(tmp_path: Path) -> None:
    profile = _profile(
        table={
            "caption_template": "Таблица {h1}.{n} — {content}",
            "caption_text_override": {"font_size": 8.0},
        }
    )
    path = _compile(
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n: Таблица\n",
        profile,
        tmp_path,
        "table-caption-override",
    )
    with pdfplumber.open(path) as pdf:
        caption_sizes = [
            char["size"] for char in pdf.pages[0].chars if char["text"] == "Т" and char["size"] < 10
        ]
    assert caption_sizes
    assert all(abs(size - 8.0) < 0.2 for size in caption_sizes)
