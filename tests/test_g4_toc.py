"""G4: регистр, отточие, пропуск и группировка приложений в оглавлении."""

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


def _profile(entities: list[dict] | None = None, **changes: object):
    values = default_values()
    if entities is not None:
        values["structural"]["entities"] = entities
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


def _outline_markdown(body: str) -> str:
    return "```{=typst}\n#outline()\n#pagebreak()\n```\n\n" + body


def _first_page_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return pdf.pages[0].extract_text() or ""


def test_g4_toc_options_schema() -> None:
    expected = {
        "outline.entry_case": "none",
        "outline.omit_when_pages_lte": 0,
        "outline.appendix_grouping": True,
        "outline.appendix_min_group": 3,
        "outline.appendix_group_template": "Приложения {first}–{last}",
    }
    for option_id, default in expected.items():
        option = OPTIONS_BY_ID[option_id]
        assert option.default == default, option_id
        assert option.legacy is False
        assert option.test_ids
        assert "СТУ" in option.source
        assert "значение хранится в профиле" not in option.rationale

    assert OPTIONS_BY_ID["outline.entry_case"].enum == (
        "none",
        "upper",
        "lower",
        "first_upper",
    )

    values = default_values()
    values["outline"].update(
        {
            "entry_case": "first_upper",
            "omit_when_pages_lte": 24,
            "appendix_grouping": True,
            "appendix_min_group": 2,
            "appendix_group_template": "Приложения {first} — {last}",
        }
    )
    normalized = normalize_values(values)
    tree = config_tree(normalized)
    assert tree["outline"]["entry_case"] == "first_upper"
    assert tree["outline"]["omit_when_pages_lte"] == 24
    assert tree["outline"]["appendix_grouping"] is True
    assert tree["outline"]["appendix_min_group"] == 2
    assert tree["outline"]["appendix_group_template"] == "Приложения {first} — {last}"


def test_g4_toc_generation_typst() -> None:
    profile = _profile(
        outline={
            "entry_case": "lower",
            "omit_when_pages_lte": 24,
            "appendix_grouping": True,
            "appendix_min_group": 4,
        }
    )
    source = build_source("Текст.\n", profile)
    assert 'entry_case: "lower"' in source
    assert "omit_when_pages_lte: 24" in source
    assert "appendix_grouping: true" in source
    assert "appendix_min_group: 4" in source


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(
    ("entry_case", "expected", "absent"),
    [
        ("none", "ВВЕДЕНИЕ", "Введение"),
        ("first_upper", "Введение", "ВВЕДЕНИЕ"),
        ("lower", "введение", "ВВЕДЕНИЕ"),
        ("upper", "ВВЕДЕНИЕ", "Введение"),
    ],
)
def test_g4_toc_entry_case_render(
    tmp_path: Path, entry_case: str, expected: str, absent: str
) -> None:
    markdown = _outline_markdown("# ВВЕДЕНИЕ\n\nТекст.\n")
    path = _compile(
        markdown,
        _profile(outline={"entry_case": entry_case}),
        tmp_path,
        f"case-{entry_case}",
    )
    text = _first_page_text(path)
    assert expected in text
    assert absent not in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_fill_render(tmp_path: Path) -> None:
    path = _compile(
        _outline_markdown("# Раздел\n\nТекст.\n"),
        _profile(),
        tmp_path,
        "fill",
    )
    text = _first_page_text(path)
    assert "...." in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(("threshold", "visible"), [(3, False), (2, True)])
def test_g4_toc_skip_render(tmp_path: Path, threshold: int, visible: bool) -> None:
    markdown = (
        "```{=typst}\n#outline()\n#pagebreak()\n```\n\n"
        "# Раздел\n\n```{=typst}\n#pagebreak()\n```\n\nТекст.\n"
    )
    path = _compile(
        markdown,
        _profile(outline={"omit_when_pages_lte": threshold}),
        tmp_path,
        f"skip-{threshold}",
    )
    with pdfplumber.open(path) as pdf:
        pages = len(pdf.pages)
        text = pdf.pages[0].extract_text() or ""
    assert pages >= 3
    assert ("...." in text) is visible


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(("grouping", "expected"), [(True, 1), (False, 3)])
def test_g4_toc_appendix_grouping_render(tmp_path: Path, grouping: bool, expected: int) -> None:
    body = (
        "# Приложение А\n\n## Состав\n\nТекст.\n\n"
        "```{=typst}\n#pagebreak()\n```\n\n"
        "# Приложение Б\n\nТекст.\n\n"
        "```{=typst}\n#pagebreak()\n```\n\n"
        "# Приложение В\n\nТекст.\n"
    )
    path = _compile(
        _outline_markdown(body),
        _profile(
            [APPENDIX_ENTITY],
            outline={
                "appendix_grouping": grouping,
                "appendix_min_group": 3,
            },
        ),
        tmp_path,
        f"appendix-group-{grouping}",
    )
    text = _first_page_text(path)
    if grouping:
        assert "Приложения А–В" in text
        assert "2–4" in text
        assert text.count("ПРИЛОЖЕНИЕ") == 0
        assert "А.1" not in text
        assert "Состав" not in text
    else:
        assert text.count("ПРИЛОЖЕНИЕ") == expected
        assert "Приложения А–В" not in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_appendix_grouping_default_on_render(tmp_path: Path) -> None:
    body = "# Приложение А\n\nТекст.\n\n# Приложение Б\n\nТекст.\n\n# Приложение В\n\nТекст.\n"
    path = _compile(
        _outline_markdown(body),
        _profile([APPENDIX_ENTITY]),
        tmp_path,
        "appendix-group-default",
    )
    text = _first_page_text(path)
    assert "Приложения А–В" in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_appendix_grouping_bold_render(tmp_path: Path) -> None:
    body = "# Приложение А\n\nТекст.\n\n# Приложение Б\n\nТекст.\n\n# Приложение В\n\nТекст.\n"
    path = _compile(
        _outline_markdown(body),
        _profile(
            [APPENDIX_ENTITY],
            appendix={"bold": True},
            outline={"appendix_grouping": True, "appendix_min_group": 3},
        ),
        tmp_path,
        "appendix-group-bold",
    )
    text = _first_page_text(path)
    assert "Приложения А–В" in text
    assert text.count("ПРИЛОЖЕНИЕ") == 0


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_roman_page_numbers_render(tmp_path: Path) -> None:
    markdown = _outline_markdown("# Введение\n\nТекст.\n")
    path = _compile(
        markdown,
        _profile(
            page={"numbering": "I"},
            outline={"entry_case": "upper"},
        ),
        tmp_path,
        "roman-pages",
    )
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        line = next(line for line in page.extract_text_lines() if "ВВЕДЕНИЕ" in line["text"])
    assert "II" in line["text"]
    assert " 2" not in line["text"]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("heading", ["**ВВЕДЕНИЕ**", "*ВВЕДЕНИЕ*"])
def test_g4_toc_entry_case_formatted_render(tmp_path: Path, heading: str) -> None:
    markdown = _outline_markdown(f"# {heading}\n\nТекст.\n")
    path = _compile(
        markdown,
        _profile(outline={"entry_case": "first_upper"}),
        tmp_path,
        f"case-formatted-{len(heading)}",
    )
    text = _first_page_text(path)
    assert "Введение" in text
    assert "ВВЕДЕНИЕ" not in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_appendix_grouping_custom_template_render(tmp_path: Path) -> None:
    body = "# Приложение А\n\nТекст.\n\n# Приложение Б\n\nТекст.\n\n# Приложение В\n\nТекст.\n"
    path = _compile(
        _outline_markdown(body),
        _profile(
            [APPENDIX_ENTITY],
            appendix={"template": "Дополнение {letter}. {title}"},
            outline={"appendix_grouping": True, "appendix_min_group": 3},
        ),
        tmp_path,
        "appendix-group-custom-template",
    )
    text = _first_page_text(path)
    assert "Приложения А–В" in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_appendix_grouping_roman_pages_render(tmp_path: Path) -> None:
    body = (
        "# Приложение А\n\nТекст.\n\n"
        "```{=typst}\n#pagebreak()\n```\n\n"
        "# Приложение Б\n\nТекст.\n\n"
        "```{=typst}\n#pagebreak()\n```\n\n"
        "# Приложение В\n\nТекст.\n"
    )
    path = _compile(
        _outline_markdown(body),
        _profile(
            [APPENDIX_ENTITY],
            page={"numbering": "I"},
            outline={"appendix_grouping": True, "appendix_min_group": 3},
        ),
        tmp_path,
        "appendix-group-roman",
    )
    text = _first_page_text(path)
    assert "Приложения А–В" in text
    assert "II–IV" in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g4_toc_appendix_group_minimum_render(tmp_path: Path) -> None:
    body = "# Приложение А\n\nТекст.\n\n# Приложение Б\n\nТекст.\n"
    path = _compile(
        _outline_markdown(body),
        _profile(
            [APPENDIX_ENTITY],
            outline={"appendix_grouping": True, "appendix_min_group": 3},
        ),
        tmp_path,
        "appendix-group-min",
    )
    text = _first_page_text(path)
    assert "Приложения А–Б" not in text
    assert text.count("ПРИЛОЖЕНИЕ") == 2
