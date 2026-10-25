# PROGRESS — спринт `sprint`

Ветка: `sprint` (от `dev`). Тег `pre-sprint` создан на коммите `7aa92f9`
(HEAD совпадал с `dev` перед началом G0).

## Ворота

| Ворота | Статус | Отчёт |
|---|---|---|
| G0 — страховка и прототипы | выполнен, ждёт приёмки владельца | отчёт отправлен |
| G1 — реестр и рантайм | не начат | — |
| G2 — дешёвые параметры и окружения | не начат | — |
| G3 — нумерация, подписи, сущности | не начат | — |
| G4 — таблицы и оглавление | не начат | — |
| G5 — расширения Markdown, формулы, ссылки | не начат | — |
| G6 — профиль СТУ СФУ и самопроверка | не начат | — |

## G0 — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| Тег `pre-sprint` | ✔ | git-тег |
| CI зелёный | ⚠ не подтверждён локально (нет Postgres) | `BLOCKERS.md` B-04 |
| `PROGRESS.md` создан | ✔ | этот файл |
| Эталонные документы (9 шт.) | ✔ | `tests/fixtures/docs/` |
| Golden-снимки текущего Typst-вывода | ✔ (8 снимков, все компилируются) | `tests/fixtures/golden/` |
| Генератор снимков и тест | ✔ | `tests/golden_helpers.py`, `tests/test_typst_golden.py` |
| S1 схлопывание отступов | ✔ | `spikes/S1-weak-spacing.typ`, `SPIKES.md` |
| S2 метки продолжения таблицы | ✔ | `spikes/S2-table-continuation.typ` |
| S3 двойная линия под шапкой | ✔ | `spikes/S3-table-double-line.typ` |
| S4 перенос формулы | ⚠ fallback (ручной разрыв) | `spikes/S4-formula-break.typ`, B-01 |
| S5 что даёт Pandoc | ⚠ механизм работает, версии не совпадают | `spikes/S5-*`, B-02 |
| S6 пропуск оглавления | ✔ | `spikes/S6-toc-skip.typ` |
| S7 кириллическая нумерация | ✔ | `spikes/S7-cyrillic-numbering.typ` |
| S8 скорость компиляции | ✔ CLI-прокси 0.25 с; браузер не измерен | `spikes/S8-preview-speed.typ` |
| S9 калибровка интервала | ✔ | `spikes/S9-line-pitch.typ` |
| S10 ненумерованный заголовок | ✔ с ограничением | `spikes/S10-unnumbered-heading.typ`, B-05 |
| S11 нумерация приложений | ✔ | `spikes/S11-appendix-numbering.typ` |
| `SPIKES.md` | ✔ | `docs/sprint/SPIKES.md` |
| `BLOCKERS.md` | ✔ | `docs/sprint/BLOCKERS.md` |

## Эталонные документы

`tests/fixtures/docs/`:

- `simple.md` — простой текст;
- `headings.md` — заголовки 1–4;
- `lists.md` — маркированный и нумерованный списки трёх уровней;
- `figure.md` — рисунок с подписью и меткой, ссылка на рисунок;
- `table.md` — таблица с подписью и меткой, ссылка на таблицу;
- `formula.md` — формула (метка формулы Pandoc не поддерживает, см. S5);
- `footnote.md` — сноска;
- `appendix.md` — приложение;
- `sample.png` — изображение для рисунка.

Для каждого документа снят полный Typst-источник (преамбула профиля с дефолтами
ORM + тело Pandoc) в `tests/fixtures/golden/<stem>.typ`. Профиль снимка:
все стили с дефолтными значениями моделей, без `text_override`, заголовки 1–6.

## Проверки

| Команда | Результат |
|---|---|
| `typst compile` для 8 golden-снимков | 8/8 OK |
| `typst compile` для 12 `.typ` прототипов | 12/12 OK |
| `uv run pytest tests/ -m "not integration"` | 51 skipped (нет Postgres) |
| `uv run pytest tests/ -m integration` | 8 skipped (нет Postgres) |
| `cd frontend && npm test` | 5 passed |
| `cd frontend && npm run build` | OK (15.13 s) |
| `uvx ruff check tests/golden_helpers.py tests/test_typst_golden.py` | All checks passed |
| `uvx ruff format --check ...` | 2 files already formatted |

PDF-измерения прототипов: pdfplumber 0.11.10, запускался через
`uv run --with pdfplumber`. В dev-зависимости пока не добавлен; добавить на G1
вместе с тестами рендера.

## Открытые решения владельца

1. B-01: принять fallback S4 (ручной разрыв формулы).
2. B-02: как выравнивать Pandoc 3.11 (сервер) и 3.9 (`pandoc-wasm`).
3. B-03: подтвердить фактическую раскладку документов в `docs/sprint/`.
