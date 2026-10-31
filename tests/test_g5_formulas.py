"""G5: подпись, нумерация и оформление формул."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.options import OPTIONS_BY_ID
from app.registry.storage import default_values, options_payload
from app.utils.typst_config import build_fd_config, config_tree
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


PARAGRAPH_ENTITY = {
    "id": "where",
    "label": "Пояснение где",
    "match": {
        "target": "paragraph",
        "level": "any",
        "mode": "starts_with",
        "value": "где",
        "case_insensitive": True,
    },
    "numbering": {
        "kind": "section",
        "mode": "continue",
        "template": "1",
        "start": 1,
        "sub_template": "{prefix}.{n}",
        "group": "",
    },
    "apply": {
        "break_before": False,
        "align": "left",
        "case": "none",
        "bold": False,
        "outlined": True,
        "around": {"before": [], "after": [], "before_collisions": []},
        "text_override": {"font_size": 8.0},
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


def _lines(path: Path) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [line["text"] for page in pdf.pages for line in page.extract_text_lines()]


def _line_top(path: Path, needle: str) -> float:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines():
                if needle in line["text"]:
                    return float(line["top"])
    raise AssertionError(f"строка не найдена: {needle}")


def _line_x0(path: Path, needle: str) -> float:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines():
                if needle in line["text"]:
                    return float(line["x0"])
    raise AssertionError(f"строка не найдена: {needle}")


def _line_sizes(path: Path, needle: str) -> list[float]:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines():
                if needle in line["text"]:
                    return [float(char["size"]) for char in line["chars"]]
    raise AssertionError(f"строка не найдена: {needle}")


def test_g5_formula_options_schema() -> None:
    expected = {
        "equation.align": "auto",
        "equation.numbering_enabled": False,
        "equation.numbering_template": "({n})",
        "equation.caption_template": None,
        "equation.caption_position": "below",
        "equation.caption_align": "center",
        "equation.caption_separator": " — ",
        "equation.caption_text_override": None,
    }
    for option_id, default in expected.items():
        option = OPTIONS_BY_ID[option_id]
        assert option.default == default, option_id
        assert option.legacy is False
        assert option.test_ids
        assert "СТУ" in option.source
        assert "значение хранится в профиле" not in option.rationale

    around = OPTIONS_BY_ID["equation.caption_around"]
    assert around.default == {"before": [], "after": []}
    assert {field.path[-1] for field in around.fields} == {"before", "after"}
    assert OPTIONS_BY_ID["equation.numbering_template"].type == "string"
    assert OPTIONS_BY_ID["equation.align"].enum == ("auto", "left", "center", "right")

    entity = OPTIONS_BY_ID["structural.entities"]
    match = next(field for field in entity.item_fields if field.path[-1] == "match")
    target = next(field for field in match.fields if field.path[-1] == "target")
    mode = next(field for field in match.fields if field.path[-1] == "mode")
    assert "paragraph" in target.enum
    assert "starts_with" in mode.enum

    values = default_values()
    values["equation"].update(
        {
            "align": "left",
            "numbering_enabled": True,
            "numbering_template": "({h1}.{n})",
            "caption_template": "Формула {n} — {content}",
            "caption_position": "above",
            "caption_align": "left",
            "caption_separator": ": ",
            "caption_text_override": {"font_size": 8.0},
        }
    )
    tree = config_tree(normalize_values(values))
    assert tree["equation"]["align"] == "left"
    assert tree["equation"]["numbering_enabled"] is True
    assert tree["equation"]["numbering_template"] == "({h1}.{n})"
    assert tree["equation"]["caption_template"] == "Формула {n} — {content}"
    assert tree["equation"]["caption_position"] == "above"
    assert tree["equation"]["caption_align"] == "left"
    assert tree["equation"]["caption_separator"] == ": "
    assert tree["equation"]["caption_text_override"]["font_size"] == 8.0
    assert tree["equation"]["caption_around"] == {"before": [], "after": []}


def test_g5_formula_generation_typst() -> None:
    """Конфиг-литерал собирается без Pandoc: тест не требует внешних бинарников."""
    profile = _profile(
        equation={
            "align": "left",
            "numbering_enabled": True,
            "numbering_template": "({h1}.{n})",
            "caption_template": "Формула {n} — {content}",
            "caption_position": "above",
            "caption_align": "left",
            "caption_separator": ": ",
        }
    )
    values, _source = options_payload(profile)
    source = build_fd_config(values)
    assert 'align: "left"' in source
    assert "numbering_enabled: true" in source
    assert 'numbering_template: "({h1}.{n})"' in source
    assert 'caption_template: "Формула {n} — {content}"' in source
    assert 'caption_position: "above"' in source
    assert 'caption_align: "left"' in source
    assert 'caption_separator: ": "' in source


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_render(tmp_path: Path) -> None:
    markdown = "$$E = mc^2$$\n\n: Подпись формулы\n"
    path = _compile(
        markdown,
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({n})",
                "caption_template": "Формула {n} — {content}",
                "caption_position": "below",
                "caption_align": "center",
            }
        ),
        tmp_path,
        "equation-caption",
    )
    lines = _lines(path)
    assert "Формула (1) — Подпись формулы" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_section_placeholders_render(tmp_path: Path) -> None:
    path = _compile(
        "# Глава\n\n$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({h1}.{n})",
                "caption_template": "Глава {h1}, формула {n} — {content}",
            }
        ),
        tmp_path,
        "equation-caption-section",
    )
    assert "Глава 1, формула (1.1) — Подпись" in _lines(path)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_chapter_without_number_template_render(
    tmp_path: Path,
) -> None:
    """{h1} только в шаблоне подписи: счётчик главы обязан шагать по заголовкам."""
    path = _compile(
        "# Глава\n\n$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({n})",
                "caption_template": "Глава {h1}, формула {n} — {content}",
            }
        ),
        tmp_path,
        "equation-caption-chapter-only",
    )
    lines = _lines(path)
    assert "Глава 1, формула (1) — Подпись" in lines
    assert not any("Глава 0" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_chapter_reset_render(tmp_path: Path) -> None:
    """Сброс счётчика главы для подписи работает и без {h1} в шаблоне номера."""
    markdown = (
        "# Первая\n\n$$E = mc^2$$\n\n: Подпись один\n\n"
        "# Вторая\n\n$$a^2 + b^2 = c^2$$\n\n: Подпись два\n"
    )
    path = _compile(
        markdown,
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({n})",
                "caption_template": "Глава {h1}, формула {n} — {content}",
            }
        ),
        tmp_path,
        "equation-caption-chapter-reset",
    )
    lines = _lines(path)
    assert "Глава 1, формула (1) — Подпись один" in lines
    assert "Глава 2, формула (2) — Подпись два" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_definition_list_not_broken(tmp_path: Path) -> None:
    path = _compile(
        "Термин\n\n: Определение термина\n",
        _profile(),
        tmp_path,
        "definition-list",
    )
    lines = _lines(path)
    assert "Термин" in lines
    assert "Определение термина" in lines
    assert not any("Формула" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_numbering_section_render(tmp_path: Path) -> None:
    markdown = "# Первая\n\n$$E = mc^2$$\n\n# Вторая\n\n$$a^2 + b^2 = c^2$$\n"
    path = _compile(
        markdown,
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({h1}.{n})",
            }
        ),
        tmp_path,
        "equation-section",
    )
    lines = _lines(path)
    assert any("(1.1)" in line for line in lines)
    assert any("(2.1)" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_numbering_global_render(tmp_path: Path) -> None:
    markdown = "# Первая\n\n$$E = mc^2$$\n\n# Вторая\n\n$$a^2 + b^2 = c^2$$\n"
    path = _compile(
        markdown,
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({n})",
            }
        ),
        tmp_path,
        "equation-global",
    )
    lines = _lines(path)
    assert any("(1)" in line for line in lines)
    assert any("(2)" in line for line in lines)
    assert not any("(2.1)" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_numbering_appendix_render(tmp_path: Path) -> None:
    path = _compile(
        "# Приложение А\n\n$$E = mc^2$$\n",
        _profile(
            [APPENDIX_ENTITY],
            equation={
                "numbering_enabled": True,
                "numbering_template": "({h1}.{n})",
            },
        ),
        tmp_path,
        "equation-appendix",
    )
    lines = _lines(path)
    assert any("(А.1)" in line for line in lines)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_appendix_letter_render(tmp_path: Path) -> None:
    """{h1} в подписи в режиме приложения даёт букву приложения."""
    path = _compile(
        "# Приложение А\n\n$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            [APPENDIX_ENTITY],
            equation={
                "numbering_enabled": True,
                "numbering_template": "({h1}.{n})",
                "caption_template": "Приложение {h1}, формула {n} — {content}",
            },
        ),
        tmp_path,
        "equation-caption-appendix",
    )
    assert "Приложение А, формула (А.1) — Подпись" in _lines(path)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_numbering_disabled_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n",
        _profile(),
        tmp_path,
        "equation-no-number",
    )
    text = "\n".join(_lines(path))
    assert "(1)" not in text


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_g5_equation_align_render(tmp_path: Path, align: str) -> None:
    markdown = "START\n\n$$E = mc^2$$\n\nEND\n"
    path = _compile(
        markdown,
        _profile(equation={"align": align}),
        tmp_path,
        f"equation-align-{align}",
    )

    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        start = next(line for line in page.extract_text_lines() if line["text"] == "START")
        end = next(line for line in page.extract_text_lines() if line["text"] == "END")
        chars = [
            char
            for char in page.chars
            if float(start["bottom"]) < float(char["top"]) < float(end["top"])
        ]
    assert chars
    x0 = min(float(char["x0"]) for char in chars)
    x1 = max(float(char["x1"]) for char in chars)
    if align == "left":
        assert x0 < page.width / 2
    elif align == "right":
        assert x1 > page.width / 2
    else:
        assert x0 > 100 and x1 < page.width - 100


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_number_right_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "numbering_template": "({n})",
            }
        ),
        tmp_path,
        "equation-number-right",
    )
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        number = next(word for word in page.extract_words() if word["text"] == "(1)")
    right_margin = default_values()["page"]["margin_right"] * 72 / 25.4
    assert abs(float(number["x1"]) - (page.width - right_margin)) < 2.0


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize(("position", "above"), [("above", True), ("below", False)])
def test_g5_equation_caption_position_render(tmp_path: Path, position: str, above: bool) -> None:
    path = _compile(
        "$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n} — {content}",
                "caption_position": position,
            }
        ),
        tmp_path,
        f"equation-caption-position-{position}",
    )
    caption_top = _line_top(path, "Формула (1)")
    with pdfplumber.open(path) as pdf:
        formula_top = next(
            float(line["top"]) for line in pdf.pages[0].extract_text_lines() if "=" in line["text"]
        )
    assert (caption_top < formula_top) is above


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_g5_equation_caption_align_render(tmp_path: Path, align: str) -> None:
    path = _compile(
        "$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n} — {content}",
                "caption_align": align,
            }
        ),
        tmp_path,
        f"equation-caption-align-{align}",
    )
    positions: dict[str, float] = {}
    for name in ("left", "center", "right"):
        profile = _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n} — {content}",
                "caption_align": name,
            }
        )
        if name == align:
            positions[name] = _line_x0(path, "Формула (1)")
        else:
            other = _compile(
                "$$E = mc^2$$\n\n: Подпись\n",
                profile,
                tmp_path,
                f"equation-caption-align-other-{name}",
            )
            positions[name] = _line_x0(other, "Формула (1)")
    assert positions["left"] < positions["center"] < positions["right"]


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_separator_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n}",
                "caption_separator": " — ",
            }
        ),
        tmp_path,
        "equation-caption-separator",
    )
    assert "Формула (1) — Подпись" in _lines(path)


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_text_override_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n} — {content}",
                "caption_text_override": {"font_size": 8.0},
            }
        ),
        tmp_path,
        "equation-caption-style",
    )
    assert all(abs(size - 8.0) < 0.2 for size in _line_sizes(path, "Формула (1)"))


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_equation_caption_around_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n\n: Подпись\n",
        _profile(
            equation={
                "numbering_enabled": True,
                "caption_template": "Формула {n} — {content}",
                "caption_around": {
                    "before": [
                        {
                            "type": "text",
                            "content": "ДО ФОРМУЛЫ",
                            "text_override": None,
                            "align": "left",
                        }
                    ],
                    "after": [
                        {
                            "type": "text",
                            "content": "ПОСЛЕ ФОРМУЛЫ",
                            "text_override": None,
                            "align": "left",
                        }
                    ],
                },
            }
        ),
        tmp_path,
        "equation-caption-around",
    )
    lines = _lines(path)
    assert "ДО ФОРМУЛЫ" in lines
    assert "ПОСЛЕ ФОРМУЛЫ" in lines


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("typst") is None,
    reason="pandoc and typst must be in PATH",
)
def test_g5_formula_explanation_paragraph_render(tmp_path: Path) -> None:
    path = _compile(
        "$$E = mc^2$$\n\nгде $E$ — энергия.\n",
        _profile([PARAGRAPH_ENTITY], par={"first_line_indent": 12.5}),
        tmp_path,
        "formula-explanation",
    )
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        line = next(line for line in page.extract_text_lines() if "где" in line["text"])
    margin_pt = default_values()["page"]["margin_left"] * 72 / 25.4
    assert abs(float(line["x0"]) - margin_pt) < 1.5
    assert all(abs(float(char["size"]) - 8.0) < 0.2 for char in line["chars"])
