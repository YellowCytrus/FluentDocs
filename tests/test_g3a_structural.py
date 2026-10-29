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


def _entity(
    value: str,
    *,
    level: str = "any",
    match_mode: str = "equals",
    mode: str = "continue",
    kind: str = "section",
    group: str = "",
    template: str = "1",
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
            "mode": match_mode,
            "value": value,
            "case_insensitive": True,
        },
        "numbering": {
            "kind": kind,
            "mode": mode,
            "template": template,
            "start": 1,
            "sub_template": "{prefix}.{n}",
            "group": group,
        },
        "apply": {
            "break_before": break_before,
            "align": align,
            "case": case,
            "bold": bold,
            "outlined": outlined,
            "around": {"before": [], "after": [], "before_collisions": []},
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


def _compile(markdown: str, profile, tmp_path: Path, name: str) -> tuple[Path, str]:
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
    return site / "output.pdf", result.stderr


def _render(markdown: str, profile, tmp_path: Path, name: str) -> Path:
    path, _stderr = _compile(markdown, profile, tmp_path, name)
    return path


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
    assert keys == {"id", "label", "match", "numbering", "apply"}
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
        "break_before",
        "align",
        "case",
        "bold",
        "outlined",
        "around",
        "text_override",
    }
    numbering = next(field for field in option.item_fields if field.path[-1] == "numbering")
    assert {field.path[-1] for field in numbering.fields} == {
        "kind",
        "mode",
        "template",
        "start",
        "sub_template",
        "group",
    }
    kind = next(field for field in numbering.fields if field.path[-1] == "kind")
    assert kind.default == "section"
    assert {value for value, _ in kind.enum_labels} == {"section", "appendix"}
    mode = next(field for field in numbering.fields if field.path[-1] == "mode")
    assert {value for value, _ in mode.enum_labels} == {"none", "continue", "own"}

    values = default_values()
    values["structural"]["entities"] = [APPENDIX_ENTITY, _entity("Введение", mode="none")]
    normalized = normalize_values(values)
    assert len(normalized["structural"]["entities"]) == 2  # type: ignore[arg-type]
    config = config_tree(normalized)
    first = config["structural"]["entities"][0]  # type: ignore[index]
    assert first["match"]["mode"] == "contains"  # type: ignore[index]
    assert first["numbering"]["kind"] == "appendix"  # type: ignore[index]
    assert first["numbering"]["mode"] == "own"  # type: ignore[index]
    assert first["apply"]["around"]["before_collisions"] == []  # type: ignore[index]

    # Обязательный текст сопоставления и неизвестные поля отвергаются.
    broken = {**APPENDIX_ENTITY, "match": {**APPENDIX_ENTITY["match"], "value": None}}
    with pytest.raises(RegistryError):
        validate_value(option, [broken])
    unknown = {**APPENDIX_ENTITY, "extra": 1}
    with pytest.raises(RegistryError):
        validate_value(option, [unknown])
    duplicate = {**APPENDIX_ENTITY, "match": {**APPENDIX_ENTITY["match"], "value": "Другое"}}
    with pytest.raises(RegistryError):
        validate_value(option, [APPENDIX_ENTITY, duplicate])
    empty = {**APPENDIX_ENTITY, "id": "empty", "match": {**APPENDIX_ENTITY["match"], "value": " "}}
    with pytest.raises(RegistryError):
        validate_value(option, [empty])


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
    assert OPTIONS_BY_ID["appendix.overflow"].enum == ("double",)


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
    profile = _profile([_entity("Введение", mode="none"), _entity("Заключение", mode="none")])
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
    profile = _profile([_entity("Введение", mode="none", case="upper", bold=True)])
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
    profile = _profile([_entity("Введение", mode="none", text_override=override)])
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
    path, stderr = _compile(markdown, _profile([APPENDIX_ENTITY]), tmp_path, "subheadings")
    lines = _lines(path)
    assert any(line.startswith("А.1 Состав") for line in lines)
    assert any(line.startswith("А.1.1 Детали") for line in lines)
    assert "did not converge" not in stderr


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
        [_entity("Список использованных источников", mode="none", break_before=True)]
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


def _outline_markdown(body: str) -> str:
    return "```{=typst}\n#outline()\n```\n\n" + body


def _outline_text(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[0].extract_text() or ""


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_numbering_own(tmp_path: Path) -> None:
    profile = _profile([_entity("Раздел", mode="own", template="I")])
    text = _outline_text(
        _render(
            _outline_markdown("# Раздел\n\nТекст.\n\n# Другой\n\nТекст.\n"),
            profile,
            tmp_path,
            "own",
        )
    )
    # Ровно две записи: оглавление и тело, без дублей.
    assert text.count("I Раздел") == 2
    assert text.count("1 Другой") == 2


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_numbering_own_group(tmp_path: Path) -> None:
    profile = _profile(
        [
            _entity("Первый", mode="own", template="I", group="shared"),
            _entity("Второй", mode="own", template="I", group="shared"),
        ]
    )
    lines = _lines(
        _render("# Первый\n\nТекст.\n\n# Второй\n\nТекст.\n", profile, tmp_path, "group")
    )
    assert "I Первый" in lines
    assert "II Второй" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_outline_numbering_none(tmp_path: Path) -> None:
    profile = _profile([_entity("Введение", mode="none")])
    text = _outline_text(
        _render(
            _outline_markdown("# Введение\n\nТекст.\n\n# Раздел\n\nТекст.\n"),
            profile,
            tmp_path,
            "outline-none",
        )
    )
    assert text.count("Введение") == 2
    assert "1 Введение" not in text
    assert text.count("1 Раздел") == 2


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_outline_outlined_false(tmp_path: Path) -> None:
    profile = _profile([_entity("Введение", outlined=False)])
    text = _outline_text(
        _render(
            _outline_markdown("# Введение\n\nТекст.\n\n# Раздел\n\nТекст.\n"),
            profile,
            tmp_path,
            "outlined-false",
        )
    )
    assert text.count("Введение") == 1
    assert "1 Введение" in text
    assert text.count("Раздел") == 2


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_numbering_true_and_global_none(tmp_path: Path) -> None:
    profile = _profile(
        [APPENDIX_ENTITY],
        heading={"numbering": "none"},
    )
    markdown = (
        "# Приложение Первое\n\n## Состав\n\nТекст.\n\n"
        "# Приложение Второе\n\n## Состав два\n\nТекст.\n"
    )
    lines = _lines(_render(markdown, profile, tmp_path, "appendix-none"))
    assert "ПРИЛОЖЕНИЕ А. Первое" in lines
    assert "ПРИЛОЖЕНИЕ Б. Второе" in lines
    assert any(line.startswith("А.1 Состав") for line in lines)
    assert any(line.startswith("Б.1 Состав два") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_custom_template_and_empty_title(tmp_path: Path) -> None:
    profile = _profile(
        [APPENDIX_ENTITY],
        appendix={"template": "Приложение {letter}. {title}"},
    )
    lines = _lines(
        _render(
            "# Приложение\n\nТекст.\n\n# Приложение   Название\n\nТекст.\n",
            profile,
            tmp_path,
            "appendix-custom",
        )
    )
    assert any(line.startswith("Приложение А.") for line in lines)
    assert any("Название" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_match_modes_level_and_priority(tmp_path: Path) -> None:
    entities = [
        _entity("Особый", match_mode="equals", mode="none"),
        _entity("содержит", match_mode="contains", mode="none"),
        _entity(r"^Рег.*$", match_mode="regex", mode="none"),
        _entity("Уровень два", level="2", mode="none"),
        _entity("Первый приоритет", mode="none"),
        _entity("Первый приоритет", mode="continue"),
    ]
    entities[5]["id"] = "priority-2"
    markdown = (
        "# Особый\n\nТекст.\n\n"
        "# Есть содержит внутри\n\nТекст.\n\n"
        "# Регулярное\n\nТекст.\n\n"
        "# Уровень два\n\nТекст.\n\n"
        "# Первый приоритет\n\nТекст.\n"
    )
    lines = _lines(_render(markdown, _profile(entities), tmp_path, "match"))
    assert "Особый" in lines
    assert "Есть содержит внутри" in lines
    assert "Регулярное" in lines
    assert "1 Уровень два" in lines
    assert "Первый приоритет" in lines
    assert "1 Первый приоритет" not in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_align_and_around(tmp_path: Path) -> None:
    entity = _entity("Введение", mode="none", align="center")
    entity["apply"]["around"] = {
        "before": [
            {
                "type": "text",
                "content": "ДО ЗАГОЛОВКА",
                "text_override": None,
                "align": "left",
            }
        ],
        "after": [],
        "before_collisions": [],
    }
    path = _render("# Введение\n\nТекст.\n", _profile([entity]), tmp_path, "align")
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        heading = [line for line in page.extract_text_lines() if "Введение" in line["text"]][0]
        page_width = page.width
    assert "ДО ЗАГОЛОВКА" in _outline_text(path)
    center = (heading["x0"] + heading["x1"]) / 2
    assert abs(center - page_width / 2) < 60


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_outline_indent_render(tmp_path: Path) -> None:
    markdown = _outline_markdown("# Один\n\nТекст.\n\n## Два\n\nТекст.\n\n### Три\n\nТекст.\n")
    profile = _profile(
        outline={"indent_mode": "step", "indent_mm": 5.0},
    )
    step_path = _render(markdown, profile, tmp_path, "indent-step")
    with pdfplumber.open(step_path) as pdf:
        lines = pdf.pages[0].extract_text_lines()
    positions = {}
    for line in lines:
        for title in ("Один", "Два", "Три"):
            if title in line["text"] and "...." in line["text"]:
                positions[title] = line["x0"]
    assert positions["Два"] - positions["Один"] > 10
    assert positions["Три"] - positions["Два"] > 10

    profile = _profile(
        outline={
            "indent_mode": "per_level",
            "indent_per_level": [
                {"mm": 0.0},
                {"mm": 10.0},
                {"mm": 30.0},
                {"mm": 0.0},
                {"mm": 0.0},
                {"mm": 0.0},
            ],
        },
    )
    per_path = _render(markdown, profile, tmp_path, "indent-per-level")
    with pdfplumber.open(per_path) as pdf:
        lines = pdf.pages[0].extract_text_lines()
    positions = {}
    for line in lines:
        for title in ("Один", "Два", "Три"):
            if title in line["text"] and "...." in line["text"]:
                positions[title] = line["x0"]
    assert positions["Два"] - positions["Один"] > 25
    assert positions["Три"] - positions["Один"] > 75


def test_structural_entity_migration() -> None:
    """Старые apply.numbering/appendix переносятся в numbering.mode."""
    old = {
        "id": "old",
        "label": "Старое",
        "match": {
            "target": "heading",
            "level": "any",
            "mode": "equals",
            "value": "Введение",
            "case_insensitive": True,
        },
        "apply": {
            "numbering": False,
            "appendix": False,
            "break_before": False,
            "align": "auto",
            "case": "none",
            "bold": False,
            "outlined": True,
            "around": {"before": [], "after": [], "collapse": "max"},
            "text_override": None,
        },
    }
    values = normalize_values({"structural": {"entities": [old]}})
    entity = values["structural"]["entities"][0]  # type: ignore[index]
    assert entity["numbering"]["mode"] == "none"  # type: ignore[index]
    assert "numbering" not in entity["apply"]  # type: ignore[operator]
    assert "appendix" not in entity["apply"]  # type: ignore[operator]
    assert entity["apply"]["around"]["before_collisions"] == [  # type: ignore[index]
        {"previous": "any", "policy": "keep_both"}
    ]

    appendix = {**old, "id": "old-appendix"}
    appendix["apply"] = {**old["apply"], "numbering": True, "appendix": True}
    values = normalize_values({"structural": {"entities": [appendix]}})
    entity = values["structural"]["entities"][0]  # type: ignore[index]
    assert entity["numbering"]["kind"] == "appendix"  # type: ignore[index]
    assert entity["numbering"]["mode"] == "own"  # type: ignore[index]
    assert entity["numbering"]["template"] == "{letter}"  # type: ignore[index]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_unnumbered_subheading_has_no_zero_prefix(tmp_path: Path) -> None:
    markdown = "# Введение\n\n## Подраздел\n\nТекст.\n\n# Раздел\n\nТекст раздела.\n"
    profile = _profile([_entity("Введение", mode="none")])
    text = _outline_text(_render(_outline_markdown(markdown), profile, tmp_path, "none-subheading"))
    assert "0.1" not in text
    assert text.count("Подраздел") == 2
    assert "1 Раздел" in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_template_title_in_any_position(tmp_path: Path) -> None:
    profile = _profile(
        [APPENDIX_ENTITY],
        appendix={"template": "{title} — {letter} {service}"},
    )
    lines = _lines(
        _render("# Приложение Название\n\nТекст.\n", profile, tmp_path, "appendix-title-first")
    )
    assert "Название — А ПРИЛОЖЕНИЕ" in lines
    assert not any(line.startswith("ПРИЛОЖЕНИЕ") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_own_letter_template_is_not_appendix(tmp_path: Path) -> None:
    profile = _profile([_entity("Раздел", mode="own", kind="section", template="({letter})")])
    lines = _lines(_render("# Раздел\n\nТекст.\n", profile, tmp_path, "own-letter"))
    assert "(А) Раздел" in lines
    assert not any(line.startswith("ПРИЛОЖЕНИЕ") for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_appendix_start_and_sub_template(tmp_path: Path) -> None:
    entity = {
        **APPENDIX_ENTITY,
        "numbering": {
            **APPENDIX_ENTITY["numbering"],
            "start": 5,
            "sub_template": "{prefix}-{n}",
        },
    }
    markdown = "# Приложение Название\n\n## Состав\n\nТекст.\n\n### Детали\n\nЕщё текст.\n"
    lines = _lines(_render(markdown, _profile([entity]), tmp_path, "appendix-start"))
    assert "ПРИЛОЖЕНИЕ Д. Название" in lines
    assert "Д-1 Состав" in lines
    assert "Д-1.1 Детали" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_outline_empty_per_level_does_not_crash(tmp_path: Path) -> None:
    profile = _profile(
        outline={"indent_mode": "per_level", "indent_per_level": []},
    )
    text = _outline_text(
        _render(
            _outline_markdown("# Один\n\nТекст.\n\n## Два\n\nТекст.\n"),
            profile,
            tmp_path,
            "outline-empty",
        )
    )
    assert "Один" in text
    assert "Два" in text


def test_own_letter_template_migrates_to_section() -> None:
    values = normalize_values(
        {"structural": {"entities": [_entity("Раздел", mode="own", template="({letter})")]}}
    )
    entity = values["structural"]["entities"][0]  # type: ignore[index]
    assert entity["numbering"]["kind"] == "section"  # type: ignore[index]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_structural_own_subheadings_use_sub_template(tmp_path: Path) -> None:
    markdown = "# Раздел\n\n## Подраздел\n\n### Детали\n\nТекст.\n"
    profile = _profile([_entity("Раздел", mode="own", template="I")])
    lines = _lines(_render(markdown, profile, tmp_path, "own-subheadings"))
    assert "I.1 Подраздел" in lines
    assert "I.1.1 Детали" in lines
    assert not any("0.1" in line for line in lines)
