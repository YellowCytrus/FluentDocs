"""Сравнение двух наборов PDF по измеримым свойствам.

Использование::

    uv run python scripts/pdf_compare.py before/ after/ --json report.json --md report.md

Скрипт не падает на различиях: он пишет отчёт и возвращает 0, если все пары
найдены, и 2, если в каталогах разный набор файлов.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pdfplumber


def _snapshot(path: Path) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text_lines()
            pages.append(
                {
                    "width": round(page.width, 3),
                    "height": round(page.height, 3),
                    "text": page.extract_text() or "",
                    "lines": [
                        {
                            "text": line["text"].strip(),
                            "top": round(line["top"], 2),
                            "x0": round(line["x0"], 2),
                        }
                        for line in lines
                    ],
                    "font_sizes": sorted({round(char["size"], 2) for char in page.chars}),
                }
            )
    return {"pages": pages}


def _compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_pages = before["pages"]
    after_pages = after["pages"]
    changes: list[str] = []
    if len(before_pages) != len(after_pages):
        changes.append(f"страниц: {len(before_pages)} → {len(after_pages)}")
    for index, (left, right) in enumerate(zip(before_pages, after_pages), start=1):
        if left["text"] != right["text"]:
            changes.append(f"стр. {index}: текст отличается")
        if left["font_sizes"] != right["font_sizes"]:
            changes.append(f"стр. {index}: кегли {left['font_sizes']} → {right['font_sizes']}")
        if len(left["lines"]) != len(right["lines"]):
            changes.append(f"стр. {index}: строк {len(left['lines'])} → {len(right['lines'])}")
            continue
        moved = [
            (old["text"], old["top"], new["top"])
            for old, new in zip(left["lines"], right["lines"])
            if abs(old["top"] - new["top"]) > 0.5 or abs(old["x0"] - new["x0"]) > 0.5
        ]
        for text, old_top, new_top in moved:
            changes.append(f"стр. {index}: «{text[:40]}» top {old_top:.2f} → {new_top:.2f}")
    return {
        "pages_before": len(before_pages),
        "pages_after": len(after_pages),
        "different": bool(changes),
        "changes": changes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="каталог PDF «до»")
    parser.add_argument("after", type=Path, help="каталог PDF «после»")
    parser.add_argument("--json", type=Path, help="куда записать JSON-отчёт")
    parser.add_argument("--md", type=Path, help="куда записать Markdown-отчёт")
    args = parser.parse_args()

    before_files = {path.relative_to(args.before) for path in args.before.rglob("*.pdf")}
    after_files = {path.relative_to(args.after) for path in args.after.rglob("*.pdf")}
    common = sorted(before_files & after_files)
    missing = sorted(before_files ^ after_files)
    report: dict[str, Any] = {
        "before": str(args.before),
        "after": str(args.after),
        "files": {},
        "missing": [str(path) for path in missing],
    }
    for relative in common:
        left = _snapshot(args.before / relative)
        right = _snapshot(args.after / relative)
        report["files"][str(relative)] = _compare(left, right)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.md:
        lines = ["# pdf-comparison", ""]
        lines.append(f"- до: `{args.before}`")
        lines.append(f"- после: `{args.after}`")
        lines.append(f"- общих PDF: {len(common)}")
        if missing:
            lines.append(f"- нет пары: {', '.join(map(str, missing))}")
        for name, result in report["files"].items():
            status = "различия" if result["different"] else "совпадает"
            lines.append(f"## {name}: {status}")
            for change in result["changes"]:
                lines.append(f"- {change}")
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {name: result["different"] for name, result in report["files"].items()},
            ensure_ascii=False,
        )
    )
    if missing:
        print(f"нет пары: {missing}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
