# PROGRESS — спринт `sprint`

Ветка: `sprint` (от `dev`). Тег `pre-sprint` создан на коммите `7aa92f9`
(HEAD совпадал с `dev` перед началом G0).

## Ворота

| Ворота | Статус | Отчёт |
|---|---|---|
| G0 — страховка и прототипы | выполнен, принят владельцем | отчёт отправлен |
| G1a — реестр и хранение | выполнен, принят владельцем | отчёт отправлен |
| G1b — рантайм `fd` и единая сборка | выполнен, ждёт приёмки владельца | отчёт отправлен |
| G1c — UI и паритет | не начат | — |
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

## G0-fix — чек-лист

Коммиты: `dd4b272` (conftest), `a8d1cbd` (версии), `62f1539` (golden, S5b,
решения блокеров).

| Пункт | Статус | Где |
|---|---|---|
| Pandoc 3.9 в Dockerfile | ✔ (`ARG PANDOC_VERSION=3.9`) | `Dockerfile` |
| Тест падает, если `pandoc --version` не 3.9 | ✔ | `tests/test_versions.py` |
| CI устанавливает Pandoc 3.9 | ✔ | `.github/workflows/ci.yml` |
| conftest не пропускает весь набор без Postgres | ✔ | `tests/conftest.py` |
| Golden-тест выполняется без Postgres | ✔ 8 passed | `tests/test_typst_golden.py` |
| Golden-снимки пересозданы на Pandoc 3.9 | ✔ изменён только `figure.typ` (`alt` удалён) | `tests/fixtures/golden/` |
| S5b: подпись формулы через `: Подпись` | ✔ | `spikes/S5b-*`, `SPIKES.md` |
| `VERSIONS.md` + тест версий | ✔ | `docs/sprint/VERSIONS.md`, `tests/test_versions.py` |
| B-01…B-05 отмечены решёнными | ✔ | `BLOCKERS.md` |
| S9: коэффициент — свойство шрифта, в G2 из реестра | ✔ дописано | `SPIKES.md` |

## G1a — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| Реестр опций Python-модулем | ✔ 303 опции | `app/registry/options.py` |
| Поля записи по AGENTS §4 | ✔ | `Option`, `REGISTRY_SPEC.md` |
| Дефолты равны ORM-дефолтам | ✔ тест | `tests/test_registry.py` |
| Мёртвые поля не внесены | ✔ `outlined`, `bookmarked`, `offset` | `REGISTRY_SPEC.md` |
| Версия схемы | ✔ `SCHEMA_VERSION = 1` | `app/registry/options.py` |
| JSONB-хранилище | ✔ `profiles.options`, `options_schema_version` | `app/models/sqlalchemy/profile.py` |
| Alembic-миграция | ✔ `a9b8c7d6e5f4` | `alembic/versions/add_profile_options_jsonb.py` |
| API чтения/записи | ✔ GET/PUT `/profiles/{id}/options` | `app/api/profiles.py` |
| Двойное чтение JSONB → старые таблицы | ✔ тест | `tests/test_profile_options_api.py` |
| Запись в оба места | ✔ options API + sync после element API | `app/registry/storage.py`, `app/api/elements/` |
| Реестровый тест | ✔ | `tests/test_registry.py` |
| Тесты хранения/API | ✔ 4 теста | `tests/test_profile_options_api.py` |
| `REGISTRY_SPEC.md` | ✔ | `docs/sprint/REGISTRY_SPEC.md` |
| Существующие тесты зелёные | ✔ 78 + 9 | см. проверки ниже |

## G1a — проверки

| Команда | Результат |
|---|---|
| `uv run pytest tests/ -m "not integration"` (Postgres 16.2, `pgserver`) | 78 passed, 9 deselected |
| `uv run pytest tests/ -m integration` (Postgres 16.2, `pgserver`) | 9 passed, 78 deselected |
| `uv run pytest tests/test_registry.py tests/test_profile_options_api.py` | 22 passed |
| `cd frontend && npm test -- --run` | 5 passed |
| `cd frontend && npm run build` | OK |
| `uv run --with ruff ruff check app tests alembic` | All checks passed |

Четыре старых теста `tests/test_element_styles_api.py` ожидали старые
неметрические дефолты (0.5, 1.2, 1.0) и падали на канонических мм-значениях.
Ожидания заменены на константы `app/models/constants/style_defaults.py`; это не
ослабление, а приведение к действующему контракту мм.

## G1b — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| Библиотека `fd` | ✔ 502 строки, 15 766 байт | `app/typst/fd.typ` |
| Конфиг профиля — Typst-литерал | ✔ `fd-config` | `app/utils/typst_config.py` |
| Одна сборка полного источника | ✔ PDF, export-typ, превью | `app/utils/typst_source.py`, `app/api/generate.py` |
| PDF и export-typ получают один источник | ✔ тест | `tests/test_generate_pdf_api.py::test_pdf_and_export_use_identical_source` |
| Все элементы переведены на реестр/`fd` | ✔ 15 элементов, `heading_levels` | `fd-config`, `fd.apply` |
| Дефолтный вывод совпадает со старыми golden | ✔ тела снимков байт в байт, PDF-символы совпадают | `tests/fixtures/golden/`, отчёт G1b |
| Второй golden-профиль с `text_override` | ✔ 8 снимков | `tests/fixtures/golden/text_override/` |
| Рендер `text_override` в PDF | ✔ 6 integration-тестов | `tests/test_typst_render_override.py` |
| Инвариант после записей в старые таблицы | ✔ все пути ниже | `tests/test_options_invariant.py` |
| Буквальные мм в четырёх тестах | ✔ | `tests/test_element_styles_api.py` |
| `pdfplumber` для тестов рендера | ✔ dev-группа | `pyproject.toml`, `uv.lock` |
| Тесты версий не ослаблены | ✔ | `tests/test_versions.py` |

### Пути записи в старые таблицы

| Путь | Синхронизация `profiles.options` | Тест |
|---|---|---|
| `POST /profiles/{id}/{element}` | после `persist`/text override | `test_invariant_after_element_post_patch_put` |
| `PATCH /profiles/{id}/{element}` | после `persist` | тот же |
| `PUT /profiles/{id}/{element}` | после `persist` | тот же |
| `GET /profiles/{id}/{element}` при создании строки | после `get_or_create` | `test_invariant_after_get_creates_legacy_rows` |
| `PATCH /profiles/{id}/heading/{level}` | после `persist` | `test_invariant_after_heading_level_patch_put` |
| `PUT /profiles/{id}/heading/{level}` | после `persist` | тот же |
| `GET /profiles/{id}/heading/{level}` при создании строки | после `_get_or_create_level` | `test_invariant_after_get_creates_legacy_rows` |
| `PUT /profiles/{id}/options` | пишет JSONB и старые таблицы | `test_invariant_after_options_put` |
| `POST /profiles`, `DELETE /profiles/{id}` | строк стилей не создаёт; удаление каскадное | `test_profile_create_delete_do_not_write_legacy_tables` |

Копирования/дублирования профиля в API нет. `PATCH /profiles/{id}` меняет
только имя и стилей не касается.

### Golden-изменения G1b

- 8 дефолтных снимков: изменился только общий префикс (`fd` + конфиг),
  тело документа байт в байт совпадает со старым снимком. Тело проверено
  сравнением с выводом Pandoc; PDF старых и новых снимков совпадают по
  страницам, координатам, кеглю и именам шрифтов (`pdfplumber`, 8/8).
- 8 новых снимков `tests/fixtures/golden/text_override/`.
- Размер префикса: было 21 строка / 1 090 байт, стало 659 строк /
  18 688 байт. Полный `simple.typ`: 670 строк / 19 323 байта.
- Исправлен счётчик подписи рисунка: старый шаблон без `{N}` не компилировался,
  а с `{N}` первый рисунок получал 0/2. Теперь счётчики сбрасываются в 0,
  `{N}` показывает текущий номер + 1. На дефолтные снимки не влияет.

### Проверки G1b

| Команда | Результат |
|---|---|
| `uv run pytest tests/ -m "not integration"` (Postgres 16.2, `pgserver`) | 93 passed, 39 deselected |
| `uv run pytest tests/ -m integration` (Postgres 16.2, `pgserver`) | 39 passed, 93 deselected |
| `uv run pytest tests/test_typst_golden.py -m integration` | 32 passed |
| `uv run pytest tests/test_typst_render_override.py -m integration` | 6 passed |
| `cd frontend && npm test` | 5 passed |
| `cd frontend && npm run build` | OK (15.16 s) |
| `uvx ruff check app tests` | All checks passed |
| `uvx ruff format --check` для файлов G1b | 16 files already formatted |

Вне G1b в репозитории остаются старые файлы, которые `ruff format` предлагает
переформатировать; массовый рефакторинг не выполнялся.

## Проверки G0 (исторические)

| Команда | Результат |
|---|---|
| `typst compile` для 8 golden-снимков G0 | 8/8 OK |
| `typst compile` для 13 `.typ` прототипов | 13/13 OK |
| `uv run pytest tests/ -m "not integration"` (без Postgres в окружении G0) | 5 passed, 51 skipped, 9 deselected |
| `uv run pytest tests/ -m integration` (без Postgres в окружении G0) | 8 passed, 1 skipped, 56 deselected |
| `cd frontend && npm test` | 5 passed |
| `cd frontend && npm run build` | OK (15.13 s) |

Пропуск DB-тестов в G0 был следствием отсутствия Postgres; на G1a/G1b Postgres
16.2 (`pgserver`) запущен, глобальных пропусков нет, актуальные цифры — в
разделах G1a/G1b.

PDF-измерения прототипов: pdfplumber 0.11.10. На G1b зависимость добавлена в
dev-группу `pyproject.toml`, тесты рендера используют её без `uv run --with`.

## Открытые решения владельца

B-01…B-05 отмечены решёнными в `BLOCKERS.md`. GitHub CI в этом окружении не
прогонялся; workflow дополнен установкой Pandoc 3.9.
