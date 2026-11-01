"""G6: самопроверка профиля «СТУ СФУ» по CONFORMANCE.md.

Эталонный документ со всеми элементами + seed-профиль → PDF.
Проверяются измеримые правила класса A; остальные отмечены в CONFORMANCE.md.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.models.sqlalchemy.profile import Profile
from app.registry import SCHEMA_VERSION, normalize_values
from app.registry.sfu_seed import SFU_PROFILE_NAME, build_sfu_values
from golden_helpers import DOCS_DIR, build_source

PT_PER_MM = 72 / 25.4
DOCS = Path(__file__).resolve().parent.parent / "docs" / "sprint"
PLAN = DOCS / "FluentDocs_SFU_rules_plan_v2.md"
CONFORMANCE = DOCS / "CONFORMANCE.md"

DOC = """# ВВЕДЕНИЕ

Вводный абзац с текстом для проверки оформления основного текста.
Второе предложение для измерения межстрочного интервала в абзаце.

# Раздел первый

## Подраздел

Основной абзац раздела с достаточно длинным текстом, чтобы он занял целую строку и позволил измерить поля страницы.

- Первый пункт списка
- Второй пункт списка

1. Первый нумерованный пункт
2. Второй нумерованный пункт

| Параметр | Значение |
|---|---|
| А | 1 |
| Б | 2 |

: Подпись таблицы

![Подпись рисунка](sample.png){#fig:a}

$$E = mc^2$$

Текст со сноской.[^1]

[^1]: Текст сноски.

# ЗАКЛЮЧЕНИЕ

Заключительный текст.

# Приложение Результаты

## Обозначение

Текст приложения.
"""


def sfu_profile(**changes: object) -> Profile:
    """Профиль СТУ СФУ; changes — точечные правки для контрольных замеров."""
    values = normalize_values(build_sfu_values())
    for section, section_values in changes.items():
        target = values[section]
        assert isinstance(target, dict)
        target.update(section_values)  # type: ignore[arg-type]
    return Profile(
        name=SFU_PROFILE_NAME,
        options=values,
        options_schema_version=SCHEMA_VERSION,
    )


def compile_doc(markdown: str, profile: Profile, tmp_path: Path, name: str) -> Path:
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


def find_line(pdf: pdfplumber.PDF, needle: str) -> tuple[int, dict]:
    for index, page in enumerate(pdf.pages, start=1):
        for line in page.extract_text_lines():
            if needle in line["text"]:
                return index, line
    raise AssertionError(f"строка не найдена: {needle}")


def line_sizes(line: dict) -> set[float]:
    return {round(float(char["size"]), 1) for char in line["chars"]}


def line_fonts(line: dict) -> set[str]:
    return {str(char["fontname"]) for char in line["chars"]}


def line_center(line: dict) -> float:
    return (float(line["x0"]) + float(line["x1"])) / 2


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        shutil.which("pandoc") is None or shutil.which("typst") is None,
        reason="pandoc and typst must be in PATH",
    ),
]


def test_sfu_conformance_render(tmp_path: Path) -> None:
    path = compile_doc(DOC, sfu_profile(), tmp_path, "sfu-conformance")
    values = normalize_values(build_sfu_values())
    margin_left = values["page"]["margin_left"] * PT_PER_MM
    margin_right = values["page"]["margin_right"] * PT_PER_MM
    margin_top = values["page"]["margin_top"] * PT_PER_MM

    with pdfplumber.open(path) as pdf:
        page_width = pdf.pages[0].width
        page_height = pdf.pages[0].height
        body_page = pdf.pages[1]

        # Поля и основной текст: 30/10/20 мм (СТУ 7.1.2).
        assert page_width == pytest.approx(595.28, abs=0.5)
        assert page_height == pytest.approx(841.89, abs=0.5)
        body_lines = [
            line
            for line in body_page.extract_text_lines()
            if line["text"] not in {"1 Раздел первый", "1.1 Подраздел", "2"}
        ]
        assert body_lines
        assert min(float(line["x0"]) for line in body_lines) == pytest.approx(margin_left, abs=2.0)
        assert max(float(line["x1"]) for line in body_lines) <= (page_width - margin_right + 2.0)
        top_line = min(body_page.extract_text_lines(), key=lambda line: line["top"])
        assert float(top_line["top"]) == pytest.approx(margin_top, abs=3.0)

        # Шрифт и кегль: Times New Roman (алиас Libertinus Serif), 14 pt.
        _, paragraph = find_line(pdf, "Основной абзац раздела")
        assert line_sizes(paragraph) == {14.0}
        assert any("LibertinusSerif" in font for font in line_fonts(paragraph))
        assert values["document"]["font"] == "Times New Roman"

        # Красная строка 1,25 см (СТУ 7.3).
        _, first_paragraph_line = find_line(pdf, "Вводный абзац")
        assert float(first_paragraph_line["x0"]) == pytest.approx(
            margin_left + 12.5 * PT_PER_MM, abs=2.0
        )

        # Нумерация страниц: первая без номера, со второй — внизу по центру.
        first_page_text = pdf.pages[0].extract_text()
        assert "\n1\n" not in first_page_text
        for index in range(1, len(pdf.pages)):
            page = pdf.pages[index]
            number_lines = [
                line for line in page.extract_text_lines() if line["text"].strip() == str(index + 1)
            ]
            assert number_lines, f"нет номера страницы {index + 1}"
            number = number_lines[0]
            assert line_center(number) == pytest.approx(
                (margin_left + page_width - margin_right) / 2, abs=6.0
            )
            assert float(number["top"]) > page_height - 60

        # Заголовки разделов: нумерация 1, 1.1; структурный — без номера.
        _, h1 = find_line(pdf, "1 Раздел первый")
        _, h2 = find_line(pdf, "1.1 Подраздел")
        assert h1["text"].startswith("1 ")
        assert h2["text"].startswith("1.1 ")
        _, introduction = find_line(pdf, "ВВЕДЕНИЕ")
        assert introduction["text"] == "ВВЕДЕНИЕ"
        assert line_center(introduction) == pytest.approx(
            (margin_left + page_width - margin_right) / 2, abs=6.0
        )
        assert any("Bold" in font for font in line_fonts(introduction))

        # Подпись таблицы: над таблицей, по левой границе, 14 pt (СТУ 7.7.3).
        _, table_caption = find_line(pdf, "Таблица 1.1 — Подпись таблицы")
        assert float(table_caption["x0"]) == pytest.approx(margin_left, abs=2.0)
        assert line_sizes(table_caption) == {14.0}
        table_page = pdf.pages[1]
        assert len(table_page.lines) >= 4, "у таблицы нет сетки"
        _, header_cell = find_line(pdf, "Параметр")
        assert float(table_caption["top"]) < float(header_cell["top"])
        assert line_sizes(header_cell) == {12.0}

        # Подпись рисунка: под рисунком, по центру, 14 pt (СТУ 7.8.2).
        figure_page_index, figure_caption = find_line(pdf, "Рисунок 1.1 — Подпись рисунка")
        figure_page = pdf.pages[figure_page_index - 1]
        assert line_sizes(figure_caption) == {14.0}
        assert figure_page.images, "рисунок не найден"
        image = figure_page.images[0]
        assert float(image["x1"]) - float(image["x0"]) == pytest.approx(165.0 * PT_PER_MM, abs=2.0)
        assert float(figure_caption["top"]) > float(image["bottom"]) - 6
        assert line_center(figure_caption) == pytest.approx(
            (margin_left + page_width - margin_right) / 2, abs=6.0
        )

        # Формула: отступ 1,25 см от левого поля, номер справа (СТУ 7.6.1).
        formula_page_index, formula = find_line(pdf, "(1.1)")
        formula_page = pdf.pages[formula_page_index - 1]
        number_chars = [char for char in formula_page.chars if 500 < float(char["x0"]) < page_width]
        assert number_chars
        assert max(float(char["x1"]) for char in number_chars) == pytest.approx(
            page_width - margin_right, abs=3.0
        )
        equation_chars = [
            char
            for char in formula_page.chars
            if abs(float(char["top"]) - float(formula["top"])) < 6 and float(char["x0"]) < 500
        ]
        assert min(float(char["x0"]) for char in equation_chars) == pytest.approx(
            margin_left + 12.5 * PT_PER_MM, abs=3.0
        )

        # Сноска: 12 pt (СТУ 7.9).
        _, footnote = find_line(pdf, "Текст сноски.")
        assert line_sizes(footnote) == {12.0}

        # Приложение: новая страница, ПРОПИСНЫЕ, по центру, подзаголовок «А.1» (СТУ 7.5.5).
        appendix_index, appendix = find_line(pdf, "ПРИЛОЖЕНИЕ А. РЕЗУЛЬТАТЫ")
        assert appendix_index == len(pdf.pages)
        assert line_center(appendix) == pytest.approx(
            (margin_left + page_width - margin_right) / 2, abs=6.0
        )
        assert any("Bold" in font for font in line_fonts(appendix))
        _, subheading = find_line(pdf, "А.1 Обозначение")
        assert subheading["text"].startswith("А.1 ")


def test_sfu_line_spacing_multiplier_render(tmp_path: Path) -> None:
    """1,5 даёт шаг строк в 1,5 раза больше, чем 1,0 (AGENTS 5.4)."""
    single = compile_doc(
        DOC,
        sfu_profile(document={"line_spacing": {"mode": "multiplier", "value": 1.0}}),
        tmp_path,
        "sfu-spacing-1",
    )

    def step(path: Path) -> float:
        with pdfplumber.open(path) as pdf:
            _, first = find_line(pdf, "Вводный абзац")
            _, second = find_line(pdf, "Второе предложение")
        return float(second["top"]) - float(first["top"])

    one_and_half = compile_doc(DOC, sfu_profile(), tmp_path, "sfu-spacing-15")
    ratio = step(one_and_half) / step(single)
    assert ratio == pytest.approx(1.5, abs=0.12)


def test_structural_heading_does_not_offset_caption_counters(tmp_path: Path) -> None:
    """«Введение» без номера не сдвигает главы подписей: 1.1, а не 2.1."""
    markdown = (
        "# ВВЕДЕНИЕ\n\nТекст.\n\n"
        "# Раздел\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n: Подпись таблицы\n\n"
        "![Подпись рисунка](sample.png){#fig:a}\n"
    )
    path = compile_doc(markdown, sfu_profile(), tmp_path, "structural-counters")
    with pdfplumber.open(path) as pdf:
        text = "\n".join(line["text"] for page in pdf.pages for line in page.extract_text_lines())
    assert "Таблица 1.1 — Подпись таблицы" in text
    assert "Рисунок 1.1 — Подпись рисунка" in text
    assert "2.1" not in text


def _class_a_rule_ids() -> list[str]:
    rules: list[str] = []
    for line in PLAN.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cols = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cols) >= 6 and cols[2] == "A":
            rules.append(cols[0].strip("`"))
    return rules


def _conformance_rows() -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in CONFORMANCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cols = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cols) >= 4:
            rows[cols[0].strip("`")] = (cols[2], cols[3])
    return rows


def test_conformance_covers_all_class_a_rules() -> None:
    """CONFORMANCE.md: каждое правило класса A имеет тест или явную пометку."""
    rules = _class_a_rule_ids()
    assert len(rules) == 78
    rows = _conformance_rows()
    assert not [rule for rule in rules if rule not in rows], "правило класса A без строки"
    allowed = ("не измеряется", "отложено", "вне спринта", "не реализовано", "значения есть")
    for rule in rules:
        test, status = rows[rule]
        assert status, rule
        if test == "—":
            assert status.startswith(allowed), (rule, status)
        else:
            assert "`test_" in test, (rule, test)
