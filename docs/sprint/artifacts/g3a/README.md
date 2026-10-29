# Артефакты G2d/G3a

- `g2d-measurements.json` — зазоры PDF для четырёх политик столкновения,
  измерены `pdfplumber` на паре «таблица → заголовок»; шаг строки 22.296 pt.
- `pdf-compare.json`, `pdf-compare.md` — отчёт `scripts/pdf_compare.py`:
  `collision/output.pdf` (default → `keep_both`) различается, `s12.pdf`
  (Typst CLI vs `typst.ts`) совпадает.

Команды воспроизведения:

```bash
POSTGRES_HOST=127.0.0.1 ... uv run pytest tests/test_around.py -m integration -q
uv run python scripts/pdf_compare.py before/ after/ \
  --json docs/sprint/artifacts/g3a/pdf-compare.json \
  --md docs/sprint/artifacts/g3a/pdf-compare.md
```

Сами PDF не коммитятся; они генерируются тестами и `scripts/pdf_compare.py`.
