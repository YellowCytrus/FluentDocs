"""G3a: структурные сущности, приложения, привязка заголовка и источники."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, RegistryError, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values, validate_value
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
    "apply": {
        "numbering": False,
        "break_before": False,
        "align": "auto",
        "case": "none",
        "bold": False,
        "outlined": True,
        "appendix": True,
        "around": {"before": [], "after": [], "collapse": "max"},
        "text_override": None,
    },
}


def _entity(
    value: str,
    *,
    level: str = "any",
    mode: str = "equals",
    numbering: bool = True,
    appendix: bool = False,
    break_before: bool = False,
    case: str = "none",
    bold: bool = False,
    outlined: bool = True,
    align: str = "auto",
    text_override: dict | None = None,
    target: str = "heading",
) -> dict:
    return {
        "id": value.lower(),
        "label": value,
        "match": {
            "target": target,
            "level": level,
            "mode": mode,
            "value": value,
            "case_insensitive": True,
        },
        "apply": {
            "numbering": numbering,
            "break_before": break_before,
            "align": align,
            "case": case,
            "bold": bold,
            "outlined": outlined,
            "appendix": appendix,
            "around": {"before": [], "after": [], "collapse": "max"},
            "text_override": text_override,
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


def _render(markdown: str, profile, tmp_path: Path, name: str) -> Path:
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


def _lines(pdf_path: Path) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        return [line["text"] for page in pdf.pages for line in page.extract_text_lines()]


def test_structural_entities_schema() -> None:
    option = OPTIONS_BY_ID["structural.entities"]
    assert option.type == "list"
    assert option.default == []
    assert option.legacy is False
    assert option.ui.get("beta") is True
    keys = {field.path[-1] for field in option.item_fields}
    assert keys == {"id", "label", "match", "apply"}
    match = next(field for field in option.item_fields if field.path[-1] == "match")
    apply = next(field for field in option.item_fields if field.path[-1] == "apply")
    assert {field.path[-1] for field in match.fields} == {
        "target",
        "level",
        "mode",
        "value",
        "case_insensitive",
    }
    assert {field.path[-1] for field in apply.fields} >= {
        "numbering",
        "break_before",
        "align",
        "case",
        "bold",
        "outlined",
        "appendix",
        "around",
        "text_override",
    }

    values = default_values()
    values["structural"]["entities"] = [APPENDIX_ENTITY, _entity("Введение", numbering=False)]
    normalized = normalize_values(values)
    assert len(normalized["structural"]["entities"]) == 2  # type: ignore[arg-type]
    config = config_tree(normalized)
    first = config["structural"]["entities"][0]  # type: ignore[index]
    assert first["match"]["mode"] == "contains"  # type: ignore[index]
    assert first["apply"]["appendix"] is True  # type: ignore[index]
    assert first["apply"]["around"]["collapse"] == "max"  # type: ignore[index]

    # Обязательный текст сопоставления и неизвестные поля отвергаются.
    broken = {**APPENDIX_ENTITY, "match": {**APPENDIX_ENTITY["match"], "value": None}}
    with pytest.raises(RegistryError):
        validate_value(option, [broken])
    unknown = {**APPENDIX_ENTITY, "extra": 1}
    with pytest.raises(RegistryError):
        validate_value(option, [unknown])


def test_appendix_options() -> None:
    expected = {
        "appendix.template": "{service} {letter}. {title}",
        "appendix.service_case": "upper",
        "appendix.title_case": "none",
        "appendix.bold": False,
        "appendix.alphabet": "ru_sfu",
        "appendix.overflow": "double",
        "heading.keep_with_next": True,
    }
    for option_id, default in expected.items():
        option = OPTIONS_BY_ID[option_id]
        assert option.default == default
        assert option.legacy is False
        assert option.test_ids
        if option.group == "appendix":
            assert option.ui.get("beta") is True
    assert "double" in OPTIONS_BY_ID["appendix.overflow"].enum
    labels = dict(OPTIONS_BY_ID["appendix.overflow"].enum_labels)
    assert "не реализовано" in labels["stop"]
    assert "не реализовано" in labels["latin"]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_unnumbered_keeps_counter(tmp_path: Path) -> None:
    markdown = (
        "# Введение\n\nТекст введения.\n\n"
        "# Первый раздел\n\nТекст раздела.\n\n"
        "# Заключение\n\nКонец.\n"
    )
    profile = _profile(
        [_entity("Введение", numbering=False), _entity("Заключение", numbering=False)]
    )
    path = _render(markdown, profile, tmp_path, "unnumbered")
    lines = _lines(path)
    assert "Введение" in lines
    assert "Заключение" in lines
    assert any(line.startswith("1 Первый раздел") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_break_before(tmp_path: Path) -> None:
    markdown = "# Введение\n\nТекст.\n\n# Приложение\n\nТекст приложения.\n"
    profile = _profile([_entity("Приложение", break_before=True)])
    path = _render(markdown, profile, tmp_path, "break")
    with pdfplumber.open(path) as pdf:
        assert len(pdf.pages) >= 2
        second_page = pdf.pages[1].extract_text_lines()
    assert second_page
    assert "Приложение" in second_page[0]["text"]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_case_render(tmp_path: Path) -> None:
    markdown = "# Введение\n\nТекст.\n"
    profile = _profile([_entity("Введение", numbering=False, case="upper", bold=True)])
    path = _render(markdown, profile, tmp_path, "case")
    lines = _lines(path)
    assert "ВВЕДЕНИЕ" in lines
    with pdfplumber.open(path) as pdf:
        chars = pdf.pages[0].chars
    heading_chars = [char for char in chars if char["text"] in "ВВЕДЕНИЕ"]
    assert heading_chars
    assert any("Bold" in char["fontname"] for char in heading_chars)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_text_override_render(tmp_path: Path) -> None:
    markdown = "# Введение\n\nТекст.\n"
    override = {
        "font": "Libertinus Serif",
        "font_size": 21.0,
        "weight": "regular",
        "style": "normal",
        "fill": "black",
        "lang": "en",
        "region": None,
        "tracking": 0.0,
        "word_spacing": 100.0,
        "hyphenate": None,
        "ligatures": True,
        "number_type": "auto",
        "number_width": "auto",
    }
    profile = _profile([_entity("Введение", numbering=False, text_override=override)])
    path = _render(markdown, profile, tmp_path, "override")
    with pdfplumber.open(path) as pdf:
        sizes = {round(char["size"], 1) for char in pdf.pages[0].chars if char["text"] == "В"}
    assert 21.0 in sizes


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_outlined_false_keeps_counter(tmp_path: Path) -> None:
    markdown = "# Один\n\nТекст.\n\n# Два\n\nТекст.\n"
    profile = _profile([_entity("Один", outlined=False)])
    lines = _lines(_render(markdown, profile, tmp_path, "outline"))
    assert any(line.startswith("2 Два") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_heading_one_line(tmp_path: Path) -> None:
    markdown = "# Приложение Название приложения\n\nТекст.\n"
    profile = _profile([APPENDIX_ENTITY])
    path = _render(markdown, profile, tmp_path, "appendix")
    lines = _lines(path)
    assert "ПРИЛОЖЕНИЕ А. Название приложения" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_case_render(tmp_path: Path) -> None:
    markdown = "# Приложение Название приложения\n\nТекст.\n"
    profile = _profile(
        [APPENDIX_ENTITY],
        appendix={"service_case": "upper", "title_case": "upper"},
    )
    lines = _lines(_render(markdown, profile, tmp_path, "appendix-case"))
    assert "ПРИЛОЖЕНИЕ А. НАЗВАНИЕ ПРИЛОЖЕНИЯ" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_bold_render(tmp_path: Path) -> None:
    markdown = "# Приложение Название\n\nТекст.\n"
    profile = _profile([APPENDIX_ENTITY], appendix={"bold": True})
    path = _render(markdown, profile, tmp_path, "appendix-bold")
    with pdfplumber.open(path) as pdf:
        heading_chars = [char for char in pdf.pages[0].chars if char["text"] in "ПРИЛОЖЕНИЕ"]
    assert heading_chars
    assert any("Bold" in char["fontname"] for char in heading_chars)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_letter_sequence(tmp_path: Path) -> None:
    markdown = "\n\n".join(f"# Приложение Приложение {index}\n\nТекст." for index in range(1, 27))
    lines = _lines(_render(markdown, _profile([APPENDIX_ENTITY]), tmp_path, "letters"))
    headings = [line for line in lines if line.startswith("ПРИЛОЖЕНИЕ ")]
    assert len(headings) == 26
    assert headings[0].startswith("ПРИЛОЖЕНИЕ А.")
    assert headings[24].startswith("ПРИЛОЖЕНИЕ Я.")
    assert headings[25].startswith("ПРИЛОЖЕНИЕ АА.")


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_numbering_subheadings(tmp_path: Path) -> None:
    markdown = "# Приложение Название\n\n## Состав\n\nТекст.\n\n### Детали\n\nЕщё текст.\n"
    lines = _lines(_render(markdown, _profile([APPENDIX_ENTITY]), tmp_path, "subheadings"))
    assert any(line.startswith("А.1 Состав") for line in lines)
    assert any(line.startswith("А.1.1 Детали") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_bibliography_heading_entity(tmp_path: Path) -> None:
    markdown = (
        "# Первый раздел\n\nТекст.\n\n"
        "# Список использованных источников\n\n"
        "1. Источник один.\n2. Источник два.\n"
    )
    profile = _profile(
        [_entity("Список использованных источников", numbering=False, break_before=True)]
    )
    path = _render(markdown, profile, tmp_path, "bibliography")
    lines = _lines(path)
    assert "Список использованных источников" in lines
    with pdfplumber.open(path) as pdf:
        last_page = pdf.pages[-1].extract_text_lines()
    assert "Список использованных источников" in last_page[0]["text"]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_heading_keep_with_next_render(tmp_path: Path) -> None:
    def document(count: int) -> str:
        filler = "\n\n".join("Абзац проверки переноса заголовка." for _ in range(count))
        return filler + "\n\n# КОНТРОЛЬНЫЙ ЗАГОЛОВОК\n\nТекст после заголовка.\n"

    def first_page_last_line(keep: bool, count: int, name: str) -> str:
        profile = _profile(heading={"keep_with_next": keep})
        with pdfplumber.open(_render(document(count), profile, tmp_path, name)) as pdf:
            lines = pdf.pages[0].extract_text_lines()
        return lines[-1]["text"] if lines else ""

    # Ищем абзац, при котором заголовок попадает в самый низ страницы.
    boundary = None
    for count in range(20, 45):
        if first_page_last_line(False, count, f"off-{count}").endswith("КОНТРОЛЬНЫЙ ЗАГОЛОВОК"):
            boundary = count
            break
    assert boundary is not None
    assert not first_page_last_line(True, boundary, "on").endswith("КОНТРОЛЬНЫЙ ЗАГОЛОВОК")
