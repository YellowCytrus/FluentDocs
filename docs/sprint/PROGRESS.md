# PROGRESS — спринт `sprint`

Ветка: `sprint` (от `dev`). Тег `pre-sprint` создан на коммите `7aa92f9`
(HEAD совпадал с `dev` перед началом G0).

## Ворота

| Ворота | Статус | Отчёт |
|---|---|---|
| G0 — страховка и прототипы | выполнен, принят владельцем | отчёт отправлен |
| G1a — реестр и хранение | выполнен, принят владельцем | отчёт отправлен |
| G1b — рантайм `fd` и единая сборка | выполнен, принят владельцем | отчёт отправлен |
| G1c — UI и паритет | выполнен, принят владельцем | отчёт отправлен |
| G2a — типы реестра и окружения «до/после» | выполнен, принят владельцем | этот файл |
| G2b — интервал, шрифты, зашитые значения | выполнен, принят владельцем | этот файл |
| G2c — остальные «дешёвые» правила | выполнен; G2c-fix ждёт приёмки | этот файл |
| G2d — политика столкновения вставок | выполнен, принят владельцем | этот файл |
| G3a — структурные сущности, приложения, оглавление | переделан, ждёт приёмки | этот файл |
| G3b — подписи и нумерация рисунков/таблиц | не начат | — |
| G4 — таблицы и оглавление | не начат | — |
| G5 — единицы измерения и чистка интерфейса | не начат | — |
| G6 — профиль СТУ СФУ и самопроверка | не начат | — |

## G0 — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| Тег `pre-sprint` | ✔ | git-тег |
| CI зелёный | ✔ https://github.com/YellowCytrus/FluentDocs/actions/runs/40832823434 | `BLOCKERS.md` B-04 |
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

## G1c — чек-лист

Коммиты: `e9f5aea`, `508a339`, `8ddc970`, `bc52dd3`, `8a7e534`, финальный
коммит документации.

| Пункт | Статус | Где |
|---|---|---|
| Убрать `eval` из `fd.typ` | ✔ осталось структурное `auto`/`none`/`custom` | `app/typst/fd.typ` |
| Тест: нет `eval`/`read`/`include`/`plugin` | ✔ | `tests/test_typst_runtime.py::test_fd_library_has_no_dynamic_code_execution` |
| Реестр: `outline.indent_mode` / `indent_mm` | ✔ `legacy=False`, отдельные тесты | `app/registry/options.py` |
| Миграция старого `outline.indent` | ✔ колонки + JSONB | `alembic/versions/add_outline_structured_indent.py` |
| Произвольная строка отвергается | ✔ 400 на `outline.indent`, `indent_mode`, `indent_mm` | `tests/test_profile_options_api.py` |
| Golden хранит только конфиг и тело | ✔ 16 снимков | `tests/golden_helpers.py`, `tests/fixtures/golden/` |
| Правка `fd.typ` не меняет golden | ✔ тест на отсутствие `fd` в снимке | `test_golden_does_not_embed_fd_library` |
| Универсальная страница «Правила» | ✔ одна форма на все 304 опции | `frontend/src/views/Rules.vue`, `RuleField.vue` |
| UI из реестра, без Vue-кода под правила | ✔ | `GET /registry/options` |
| Паритет превью/PDF | ✔ 8 документов | `tests/test_preview_parity.py` |
| Одинаковые шрифты | ✔ имена в PDF совпадают, файлы сверены по SHA-256 | ниже |
| Скорость перерисовки 100+ страниц | ✔ 135 мс на 152 страницах | `typst-preview-bench.mjs` |
| Мёртвые поля заголовков убраны из API/UI | ✔ `outlined`, `bookmarked`, `offset` | `tests/test_heading_level_api.py` |
| Колонки БД не удалены | ✔ | `heading_level_styles` |
| Тесты версий не пропускаются молча | ✔ `pytest.skip` с причиной | `tests/test_versions.py` |
| CI: Typst 0.14.2 + Node + `npm ci` | ✔ | `.github/workflows/ci.yml` |
| GitHub Actions зелёный | ✔ run `40273965590` (test + lint) | Actions |

### Безопасность отступа оглавления

Старое поле `outline.indent` содержало произвольную строку Typst и исполнялось
через `eval`. Замена: `outline.indent_mode` (`auto`/`none`/`custom`) и
`outline.indent_mm` (мм). В `fd.typ`:

- `auto` — `indent` не передаётся (поведение Typst по умолчанию);
- `none` — `indent: 0mm`;
- `custom` — `indent: indent_mm * 1mm`.

Строковые выражения и неизвестные ключи отвергаются реестром с `400`.
Колонка `outline_styles.indent` остаётся в БД; миграция переносит её значения
(включая старый JSONB-ключ) в новые поля. `em` при миграции пересчитан по
базовым 12 pt и это единственное приближение.

### Golden G1c

Формат снимка: `#let fd-config = (...)` + маркер `// --- document body ---` +
тело Pandoc. Библиотека `fd` в снимок не входит, поэтому её правка снимки не
меняет. Перед компиляцией `golden_to_full_source` подставляет текущую `fd` и
`#show: fd.apply.with(fd-config)`. Все 16 снимков пересозданы; изменился только
блок `outline` (`indent` → `indent_mode`/`indent_mm`), тела документов не
менялись. Размер снимка `simple.typ`: 3 512 байт (было 19 323).

### Универсальный UI

`/rules`: `ProfileSidebar` + вкладки `ui.tab` + секции по элементу/уровню
заголовка. Данные — `GET /registry/options` (схема) и
`GET/PUT /profiles/{id}/options` (значения). Контролы: number/integer
(ползунок + число + единицы), boolean, string, select, markers. Секции
`text_override` включаются переключателем и заполняются дефолтами реестра.
Вкладки: Страница 9, Текст 15, Абзац 17, Заголовки 91, Маркированный список 18,
Нумерованный список 22, Определения 17, Таблица 17, Изображение 20, Цитата 16,
Сноска 17, Код 16, Оглавление 16, Формула 13. Всего 304 опции, из них
`legacy=False` только две новые опции отступа оглавления.

### Паритет превью и PDF

`tests/test_preview_parity.py`: один Markdown + профиль, источник сервера и
превью совпадают байт в байт; PDF собираются Typst CLI и Node + `typst.ts`.
Проверены 8 документов: источник, число страниц, текст страниц и имена шрифтов.

| Документ | Страниц | Текст совпал | Шрифты совпали |
|---|---:|---|---|
| simple | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| headings | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| lists | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| figure | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| table | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| formula | 1 | ✔ | ✔ LibertinusSerif Regular/Bold + NewCMMath-Book |
| footnote | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |
| appendix | 1 | ✔ | ✔ LibertinusSerif Regular/Bold |

### Шрифты: файлы и хэши

`typst.ts` загружает текстовые ассеты `typst-assets@v0.13.1`; Typst CLI 0.14.2
встраивает те же файлы. SHA-256 файлов (скачанные ассеты; для CLI совпали
извлечённые из бинаря sfnt-блоки с учётом padding):

| Файл | SHA-256 |
|---|---|
| `LibertinusSerif-Regular.otf` | `fcf06307a77367394fcb0ccb241e59eea70dba3d732be309647611224679c733` |
| `LibertinusSerif-Bold.otf` | `0264914210ed51b3231ebc92ce529e9f2e166ba9eebf0cd4a579558690a27b64` |
| `LibertinusSerif-Italic.otf` | `9a393d63d6e05f620d3dc0190dfd35a8ede58c0808cf0fc9de7fcb9c723e4c24` |
| `LibertinusSerif-BoldItalic.otf` | `47a665259f09f554f5d133d7718cdad43ff462c6a6b2328f38023465e62d57ce` |
| `LibertinusSerif-Semibold.otf` | `a4b3f28e85881db34695c1f005e4c79233a6caf3a2bd286c9b418c025fb99308` |
| `LibertinusSerif-SemiboldItalic.otf` | `397f0d7aba35ae6a988948ae046c14c6b1e0d270fcc6e292b8bc29fd625c6101` |
| `NewCMMath-Book.otf` | `b2e655d5cae5ab9569fa6f5d94e929156fe70bd3548d916b4b23d1a1c1a55693` |
| `DejaVuSansMono.ttf` | `b4a6c3e4faab8773f4ff761d56451646409f29abedd68f05d38c2df667d3c582` |
| `DejaVuSansMono-Bold.ttf` | `bce60f1b4421acd9ea51ba6623d7024ecbe6817a953e3654df62a5e6bdf8f769` |

### Скорость превью

Конфигурация: Linux 7.2.11, Intel Core i5-1135G7, 4 ядра / 8 потоков,
7.4 GiB RAM, Node v26.12.0, Typst 0.14.2, Pandoc 3.9.

| Документ | Страниц | Холодная сборка | Перерисовка после правки |
|---|---:|---:|---:|
| 1 200 абзацев | 152 | 655 мс | **135 мс** |
| 4 000 абзацев | 507 | 1 479–1 634 мс | **394–1 123 мс** |

Порог S8 — 2 000 мс; на 507 страницах порог тоже выдержан. Тест
`test_preview_redraw_under_two_seconds` проверяет 152-страничный документ.

### Проверки G1c

| Команда | Результат |
|---|---|
| `uv run pytest tests/ -m "not integration"` (Postgres 16.2, `pgserver`) | 99 passed, 42 deselected |
| `uv run pytest tests/ -m integration` | 42 passed, 99 deselected |
| `cd frontend && npm test -- --run` | 8 passed (3 files) |
| `cd frontend && npm run build` | OK |
| `uvx ruff check app tests` | All checks passed |
| `uvx ruff format --check` для файлов G1c | 18 files already formatted |
| Alembic на чистой БД | `upgrade head` без ошибок |

Вне G1c остаются старые файлы, которые `ruff format` предлагает
переформатировать; массовый рефакторинг не выполнялся.

## G2a — чек-лист

Коммиты: см. отчёт на воротах G2a.

| Пункт | Статус | Где |
|---|---|---|
| Типы реестра `list` и `object` | ✔ рекурсивные `fields`/`item_fields`/`item_variants` | `app/registry/options.py` |
| Подписи enum для вложенных полей | ✔ `enum_labels`, `ui.options` | `app/registry/options.py` |
| Хранение в JSONB | ✔ блок `around` | `app/registry/storage.py` |
| Валидация: границы, обязательные, неизвестные ключи → 400 | ✔ рекурсивно | `validate_value`, `tests/test_around.py` |
| API чтения/записи | ✔ GET/PUT `/profiles/{id}/options` | `app/api/profiles.py` |
| Сохранение `around` при записи в старые таблицы | ✔ `serialize_profile` переносит JSONB-блок | `app/registry/storage.py` |
| 15 целей `around` | ✔ 60 опций (`before`, `after`, `before_collisions`) | `app/registry/options.py` |
| Вставки `blank`, `text`, `line`, `pagebreak` | ✔ | `app/typst/fd.typ` |
| `before_collisions`: `keep_previous` / `keep_current` / `keep_both` / `drop_both` | ✔ G2d; `collapse` удалён | `app/typst/fd.typ`, `REGISTRY_SPEC.md` |
| Пустой `around` не меняет вывод | ✔ старые и новые PDF совпали 16/16 | сравнение `pdfplumber` |
| Golden: только блок `around` | ✔ +77 строк на снимок, 0 удалений | `tests/fixtures/golden/` |
| UI-рендерер списков/объектов | ✔ добавить/удалить/↑/↓, вложенные поля | `RuleField.vue` |
| Тесты UI | ✔ 7 новых тестов (helpers + component) | `frontend/src/**` |
| Тесты генерации | ✔ 15 тестов по целям + схема | `tests/test_around.py` |
| Тесты API/валидации | ✔ unknown, required, bounds, roundtrip | `tests/test_around.py` |
| Рендер-тесты `pdfplumber` | ✔ 3 integration-теста | `tests/test_around.py` |
| `legacy=False`, конкретные rationale/source/test_ids | ✔ | реестровый тест усилен |
| G2b/G2c не начаты | ✔ | — |

### Проверки G2a

| Команда | Результат |
|---|---|
| `uv run pytest tests/ -m "not integration"` | 118 passed, 45 deselected |
| `uv run pytest tests/ -m integration` | 45 passed, 118 deselected |
| `cd frontend && npm test -- --run` | 15 passed (4 files) |
| `cd frontend && npm run build` | OK (`vue-tsc -b` + vite) |
| `uvx ruff check app/ tests/` | All checks passed |
| `uvx ruff format --check app/ tests/` | All files formatted |
| GitHub Actions `sprint` | run `40273965590`: test + lint success (до G2a) |

### Golden-изменения G2a

Все 16 снимков получили только новый блок `around` (77 строк, 0 удалений):
15 целей × `before: ()`, `after: ()`, `collapse: "max"` (на G2d заменён на
`before_collisions: ()`). Тела документов и
остальные опции не менялись. Для проверки «профиль без `around` не меняет
вывод» старые и новые PDF всех 16 документов сравнены `pdfplumber`: число
страниц, координаты, кегль, имена шрифтов и текст совпали (16/16).

### Ручная проверка скорости в браузере

Playwright + Chromium (Xvfb, headed), документ 4 000 абзацев → **115 страниц**,
профиль по умолчанию, редактор `/`:

| Сценарий | Время |
|---|---:|
| Первая загрузка и отрисовка 115 страниц | 8.0–8.6 с |
| Правка в конце документа → canvas перерисован, оверлей «Компиляция...» исчез | **8.0–8.6 с** |

Это не соответствует порогу S8 (≤ 2 с) и расходится с Node-замером 135 мс,
который мерил компиляцию, но не отрисовку 115 страниц canvas. Записано в
`BLOCKERS.md` B-07; G2a это не блокирует, но для комфортной работы редактора
нужен отдельный механизм (ленивая отрисовка/виртуализация страниц или
инкрементальная компиляция).

## G2a-fix — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| Удалить `none` из enum, UI, fd | ✔ остались `max` и `sum` | `app/registry/options.py`, `app/typst/fd.typ` |
| Миграция старых `none` | ✔ `max` + пустые `before/after` | `app/registry/storage.py` |
| `blank.count = 0` при `max` | ✔ явный `v(0)`, заменяет штатный интервал | `app/typst/fd.typ` |
| `blank.count = 0` при `sum` | ✔ ничего не добавляет | `app/typst/fd.typ` |
| Калибровка теста «таблица → заголовок» | ✔ ±0.5 pt | `tests/test_around.py` |
| Замеры | ✔ base 19.52, max 12.32, sum 48.32, count0 max −2.08, count0 sum 19.52 pt | `tests/test_around.py` |

## G2b — чек-лист

| Пункт | Статус | Где |
|---|---|---|
| `document.line_spacing = {mode, value}` | ✔ `multiplier` / `mm` | `app/registry/options.py` |
| Множитель от естественной высоты строки | ✔ `fd.line-pitch` | `app/typst/fd.typ` |
| Коэффициенты шрифтов — данные реестра | ✔ Libertinus 1.308, PT Astra 1.312 | `app/registry/options.py` |
| Неизвестный шрифт — ручной коэффициент | ✔ `document.line_height_em`; автозамер отложен (B-09) | реестр, `REGISTRY_SPEC.md` |
| Миграция старых значений в `mm` | ✔ JSONB + старые колонки | `app/registry/storage.py` |
| PT Astra Serif (OFL-1.1) в репозитории | ✔ 4 TTF + лицензия | `assets/fonts/` |
| Сервер и `typst.ts` загружают одни файлы | ✔ `--font-path assets/fonts`, `preloadFonts` | `typst_compiler.py`, `frontend/src/typstFonts.ts` |
| Паритет с PT Astra | ✔ 3 passed (2 профиля + версии) | `tests/test_preview_parity.py` |
| Вынести `-0.3em` | ✔ `heading.unnumbered_indent` | `app/registry/options.py` |
| Вынести `0.5em` / `1em` | ✔ `tight_spacing` / `loose_spacing` у трёх списков | `app/registry/options.py` |
| Вынести `0.65em` | ✔ `document.default_leading_em` | `app/registry/options.py` |
| Дефолты сохранены | ✔ тела golden не изменились | `tests/fixtures/golden/` |
| Golden: только блок конфига | ✔ новые ключи, тела байт в байт | `UPDATE_GOLDEN=1` |
| B-07 разложен по этапам | ✔ таблица ниже | этот файл |
| Тесты с реальной БД | ✔ 123 + 50 passed | ниже |

### Проверки G2b

| Команда | Результат |
|---|---|
| `uv run pytest tests/ -m "not integration"` (Postgres 16, `pgserver`) | 123 passed, 50 deselected |
| `uv run pytest tests/ -m integration` (Postgres 16, `pgserver`) | 50 passed, 123 deselected |
| `cd frontend && npm test -- --run` | 15 passed (4 files) |
| `cd frontend && npm run build` | OK (`vue-tsc -b` + vite) |
| `npx vue-tsc --noEmit` | OK |
| `uvx ruff check app/ tests/` | All checks passed |

### Golden-изменения G2b

Все 16 снимков получили только новые ключи конфига: `document.line_spacing`
стал объектом `{mode, value}`, добавлены `document.line_height_em = 1.308`,
`document.default_leading_em = 0.65`, `heading.unnumbered_indent = -0.3`,
`tight_spacing = 0.5`, `loose_spacing = 1.0` у маркированного, нумерованного
списков и списка определений. Тела документов не изменились.

### Шрифты G2b: SHA-256

| Файл | SHA-256 |
|---|---|
| `pt-astra-serif_regular.ttf` | `cdb923648978a89f3851b6f844d31c36e2f1b14b09659bd0f0c310fbf9f5102b` |
| `pt-astra-serif_italic.ttf` | `56c6fa4cac5a917c08c6957179f80e3ce277ac60e609c0c1584b7ad331d49897` |
| `pt-astra-serif_bold.ttf` | `9420cec257b3e7ab2236edf76966c20ebca1528a5d0096786cd0b1a5be6277a4` |
| `pt-astra-serif_bold-italic.ttf` | `ae5ac2d2596c92c600f52870b9eca5268b529233d701c4aeef987eeaf3e6a388` |
| `OFL.txt` | `1d361a8f8e8ce6e68457dcd93fb56e162e6baa3bbb7e7573a290d44399f6b57e` |

`Libertinus`, `New Computer Modern` и `DejaVu Sans Mono` скопированы из
`typst-assets` v0.13.1 в тот же `assets/fonts/`, чтобы исключить CDN из
паритета; SHA-256 этих файлов совпадают с таблицей G1c.

### B-07: замер по этапам

Playwright + Chromium (headless), редактор `/`, профиль по умолчанию,
900 абзацев → **114 страниц**. Три прогона, первая видимая страница —
первый тёмный `fill` в canvas превью:

| Этап | Холодный старт | Правка первой страницы |
|---|---:|---:|
| Компиляция `typst.ts` | 501–554 мс | 339–365 мс |
| Получение страниц | 31–40 мс | 37–47 мс |
| Отрисовка всех canvas | 3 448–3 853 мс | 3 388–3 549 мс |
| Текстовый слой | 17–21 мс | 78–85 мс |
| Итого `$typst.canvas` | 3 997–4 465 мс | 3 842–4 030 мс |
| **Первая видимая страница** | **2 039–2 145 мс** | **1 668–1 750 мс** |
| Пик JS heap | 117.5–123.9 МБ | 71.0–74.1 МБ |
| JS heap после отрисовки | 42.5–45.9 МБ | 43.1–54.8 МБ |

Порог S8 переопределён владельцем: для 100+ страниц проверяется время до
обновления видимой страницы. Тёплая правка укладывается (1.67–1.75 с),
холодный старт — 2.04–2.15 с. Виртуализация/ленивая отрисовка — после G2c.

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

B-01…B-06 и B-08 отмечены решёнными в `BLOCKERS.md`. B-07 замерен и отложен
по решению владельца: порог проверяется по видимой странице, полная отрисовка
всех страниц оптимизируется после G2c. B-09 — открытый вопрос автозамера
коэффициента высоты строки для нового шрифта. GitHub Actions на ветке `sprint`
прогонялся зелёным (run `40273965590`, до G2a).

## G2c — чек-лист

Коммиты: `6988bff` (единица `blank`), `ac706f4` (штатные интервалы),
`d1e4e82` (оставшиеся правила класса A).

| Пункт | Статус | Где |
|---|---|---|
| Единица `blank` = полный шаг строки | ✔ `fd.line-step`; multiplier и mm | `app/typst/fd.typ` |
| Единица `blank`: эталон — шаг строк обычного абзаца в том же PDF | ✔ ±0,5 pt; NBSP-обход удалён | `tests/test_around.py`, `tests/test_g2b_line_spacing.py` |
| Множитель 1,0 ≈ `line_height_em × кегль` | ✔ оба шрифта, допуск 0,3 pt | `test_line_spacing_multiplier_render` |
| Ключ таблицы коэффициентов после алиасов | ✔ `Times New Roman → Libertinus Serif` | `test_line_height_coefficient_table` |
| Штатные интервалы 28 опций | ✔ заголовки 1–6, рисунок, таблица, формула, цитата, код, terms, списки | `tests/test_g2c_spacing.py` |
| `page.margins.landscape` | ✔ 4 поля, только весь документ | `tests/test_g2c_rules.py` |
| `page.numbering` | ✔ пропуск первой, начальный номер | `tests/test_g2c_rules.py` |
| `formula.body_indent` | ✔ `equation.body_indent` | `tests/test_g2c_rules.py` |
| `reference.footnote` | ✔ длина и толщина разделительной линии | `tests/test_g2c_rules.py` |
| Golden | ✔ изменился только блок конфига | `tests/fixtures/golden/` |
| Реестровый контракт | ✔ 28 + 7 новых опций с конкретными source/test_ids | `tests/test_registry.py` |
| Ruff | ✔ All checks passed | `uvx ruff check` |

### G2c: измерения `blank`

Документ: таблица → заголовок, `document.line_spacing = 5.08 мм`, кегль 12 pt.
Полный шаг: `5.08 мм + (1.308 − 0.65) × 12 pt = 22.30 pt`.

| Сценарий | Ожидание | Измерено |
|---|---|---|
| без `around` | штатный зазор | 19.52 pt |
| шаг строк абзаца (эталон) | `5,08 мм + (1,308 − 0,65) × 12` | 22.30 pt |
| `blank(count=1)`, `max`, с двух сторон | `count=0` + 1 шаг | 20.21 pt (−2.08 + 22.30) |
| `blank(count=1)`, `sum`, с двух сторон | штатный + 2 шага | 64.11 pt |
| `count: 0`, `max` | геометрия + 0 | −2.08 pt |
| `count: 0`, `sum` | штатный зазор | 19.52 pt |

Множители 1,0 и 1,5 и режим мм на Libertinus Serif и PT Astra Serif:
`blank(count=1)` при `max` даёт ровно измеренный шаг строк абзаца в том же PDF
с допуском 0,5 pt (`test_blank_unit_matches_line_step`); смещение калибруется
зазором при `count=0`.
Шаг при 1,0: Libertinus 15.70 pt, PT Astra 15.74 pt (ожидание
`1.308/1.312 × 12`), допуск 0,3 pt.

### G2c: вынесенные штатные интервалы

| Элемент | before | after |
|---|---:|---:|
| `heading.h1` | 1.8 em | 0.75 em |
| `heading.h2..h6` | 1.44 em | 0.75 em |
| `figure` | 1.2 em | 1.2 em |
| `table` | 1.2 em | 1.2 em |
| `equation` | 1.2 em | 1.2 em |
| `quote` | 2.4 em | 1.8 em |
| `raw` | 1.2 em | 1.2 em |
| `terms` | 1.2 em | 1.2 em |
| `bullet_list` | 1.2 em | 1.2 em |
| `numbered_list` | 1.2 em | 1.2 em |

### G2c: правила класса A/1–2

| Правило | Опция | Тест | Статус |
|---|---|---|---|
| `page.margins.portrait` | `page.margin_*` | существующие | было |
| `page.margins.landscape` | `page.margin_landscape_*` | `test_page_landscape_*` | реализовано |
| `page.numbering` | `page.numbering`, `number_align`, `numbering_skip_first`, `numbering_start` | `test_page_numbering_*` | реализовано |
| `text.font.name/size/color/alignment` | `document.*` | существующие | было |
| `text.indent.first_line` | `par.first_line_indent` | существующие | было |
| `text.line_spacing` | `document.line_spacing` | `test_line_spacing_*` | было/G2b |
| `referat.keywords_uppercase` | — | — | отложено владельцем (реферат) |
| `toc.indent_levels` | — | — | отложено G4 |
| `heading.h1..h6` | `heading.h*` | существующие | было |
| `heading.spacing_before/after` | `heading.h*.spacing_*` | `test_element_spacing_*` | реализовано |
| `heading.no_hyphenation` | `text_override.hyphenate` | существующие | покрыто |
| `list.item` | `indent`, `body_indent` | `test_list_item_wrapped_line_indent` | реализовано/измерено |
| `list.nested_numeric` | — | — | отложено G3 |
| `figure.caption` | — | — | отложено G3 |
| `figure.spacing_before/after` | `figure.spacing_*` | `test_element_spacing_*` | реализовано |
| `figure.image` | `figure.width/height/fit` | существующие | было |
| `figure.placement_after_reference` | `figure.placement` | существующие | покрыто (авторский порядок) |
| `formula.spacing_before/after` | `equation.spacing_*` | `test_element_spacing_*` | реализовано |
| `formula.explanation` («где…») | — | — | отложено владельцем (формулы) |
| `formula.body_indent` | `equation.body_indent` | `test_equation_body_indent_*` | реализовано |
| `bibliography.entry` | `structural.entities` (заголовок списка) | `test_bibliography_heading_entity` | G3a, через сопоставитель |
| `table.caption` | — | — | отложено G3 |
| `table.spacing_before/after` | `table.spacing_*` | `test_element_spacing_*` | реализовано |
| `table.cell_padding` | `table.inset` | существующие | было |
| `table.font.size` | `table.text_override.font_size` | существующие | было |
| `table.body` | — | — | отложено G4 |
| `reference.footnote` | `footnote.*`, `separator_*` | `test_footnote_separator_*` | реализовано |
| `coursework.*_numbering`, `graduation_qualification_work.*_numbering` | — | — | seed G6 после G3 |
| `coursework.toc.form_t` | — | — | отложено G4 |

### Проверки G2c

| Команда | Результат |
|---|---|
| `POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432 POSTGRES_DB=pizdo_test uv run pytest tests/ -m "not integration"` | 128 passed, 86 deselected |
| `POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432 POSTGRES_DB=pizdo_test uv run pytest tests/ -m integration` | 86 passed, 128 deselected |
| `cd frontend && npm test -- --run` | 15 passed (4 files) |
| `cd frontend && npm run build` | OK |
| `npx vue-tsc --noEmit` | OK |
| `uvx ruff check app tests alembic` | All checks passed |
| `uvx ruff format --check` для файлов G2c | OK |

### Golden-изменения G2c

16 снимков получили только новые ключи конфига: `heading_levels[*].spacing_before/after`,
`spacing_before/after` у figure/table/equation/quote/raw/terms/списков,
`page.margin_landscape_*`, `page.numbering_skip_first/start`,
`equation.body_indent`, `footnote.separator_length/stroke`. Тела документов
не изменились. Новые дефолтные интервалы приняты владельцем 29.10.2026:
baseline — текущие значения, возврат к `4e6a8c0` не требуется.
`tests/fixtures/baseline/g2c_geometry.json` фиксирует измеренную геометрию.

### Отложено из-за синтаксиса

В G2c не реализовывались правила, требующие нового синтаксиса Markdown:
`figure.placement_after_reference` в части «после первой ссылки» (авторский
порядок), `formula.explanation` («где…») и любые fenced-div/атрибуты.
Формулы, реферат и «где…» отложены владельцем (AGENTS 2.11); fenced-div
остаются вне спринта.

## G2c-fix — чек-лист

Коммит: `f963cc4`; CI run [40646588836](https://github.com/YellowCytrus/FluentDocs/actions/runs/40646588836) — test + lint success.

| Пункт | Статус | Где |
|---|---|---|
| Убрать NBSP-обход из `fd` | ✔ show-правило удалено | `app/typst/fd.typ` |
| Эталон `blank` — шаг строк обычного абзаца в том же PDF | ✔ `max − count=0` = шаг ±0,5 pt | `tests/test_around.py`, `tests/test_g2b_line_spacing.py` |
| Режимы `mm`, множители 1,0 и 1,5 на Libertinus Serif и PT Astra Serif | ✔ 6 комбинаций | `test_blank_unit_matches_line_step` |
| PDF «до/после» 16 golden-документов (`4e6a8c0` → текущий) | ✔ расхождения ниже | `pdfplumber` |
| 28 spacing-интервалов: сдвиг = ожидаемому ±0,5 pt | ✔ 28/28 | `test_element_spacing_render` |
| `list.item`: фактический перенос строки пункта | ✔ измерен `body_indent` | `test_list_item_wrapped_line_indent` |
| `formula.explanation`, `referat.*`, `bibliography.entry` в `PROGRESS.md` | ✔ по решениям владельца | таблица G2c |
| UI-названия столкновений | ✔ четыре политики из AGENTS 5.1 | `COLLISION_POLICY_LABELS` |
| `terms.spacing_before` применяется один раз | ✔ обёртка `block` вместо `set block` | `app/typst/fd.typ` |
| `git diff fd.typ` | ✔ приложен к отчёту | — |

### G2c-fix: единица `blank`

NBSP-абзац больше не трактуется как weak-пустая строка: скрытой семантики
Markdown нет. Эталон — измеренный шаг строк обычного абзаца в том же PDF.
Зазор `blank(count=1)` при `max` равен `зазор(count=0) + шаг` с допуском 0,5 pt.

| Режим интервала | Шрифт | Шаг строк, pt | `blank.max − count=0`, pt |
|---|---|---:|---:|
| мм 5,08 | Libertinus Serif | 22,30 | 22,30 |
| мм 5,08 | PT Astra Serif | 22,30 | 22,34 |
| множитель 1,0 | Libertinus Serif | 15,70 | 15,70 |
| множитель 1,0 | PT Astra Serif | 15,70 | 15,74 |
| множитель 1,5 | Libertinus Serif | 23,54 | 23,54 |
| множитель 1,5 | PT Astra Serif | 23,57 | 23,62 |

### G2c-fix: сравнение PDF 16 golden-документов

Собраны `4e6a8c0` (worktree) и текущий `sprint`. Сравнивались число страниц,
текст, координаты (`x0`, `top`), кегль и имена шрифтов всех символов.

| Документ | Страницы | Текст | Кегль | Шрифты | Сдвиг по вертикали |
|---|---|---|---|---|---|
| simple, appendix, footnote, headings | совпали | совпал | совпал | совпали | нет |
| figure (оба профиля) | совпали | совпал | совпал | совпали | +4,8 pt после рисунка |
| formula (оба профиля) | совпали | совпал | совпал | совпали | +4,8 pt после формулы |
| table (оба профиля) | совпали | совпал | совпал | совпали | +2,4 pt у таблицы и текста |
| lists (оба профиля) | совпали | совпал | совпал | совпали | до +10,8 pt |

Причина — явные значения G2c: `figure`/`equation` 1,2 em вместо штатных
Typst 1,0 em, `table` 1,2 em, списки 1,2 em. Это не ошибка кода G2c-fix:
значения заданы в реестре; расхождение зафиксировано, решение о смене
дефолтов остаётся за владельцем. Текст, шрифты, кегль и число страниц не
изменились.

## G2d — чек-лист

Коммит: см. отчёт на воротах G3a.

| Пункт | Статус | Где |
|---|---|---|
| `around.<element>.before_collisions` — список `{previous, policy}` | ✔ 15 целей | `app/registry/options.py` |
| Политики `keep_previous`, `keep_current`, `keep_both`, `drop_both` | ✔ | `app/typst/fd.typ`, `COLLISION_POLICY_LABELS` |
| Политика по умолчанию и fallback — `keep_both` | ✔ | `test_around_render_collision_policies` |
| `collapse` удалён; `max|sum` → `keep_both` | ✔ миграция JSONB | `app/registry/storage.py`, `tests/test_around.py` |
| Проход по верхнеуровневым элементам тела | ✔ `body-units` | `app/typst/fd.typ` |
| Пустая строка на верху страницы пропадает | ✔ `here().position().y` | `test_around_render_one_side_top_and_previous_kind` |
| Вставка только с одной стороны действует | ✔ | тот же тест |
| Правило по виду предыдущего элемента | ✔ первое подходящее | тот же тест |
| UI: четыре названия из AGENTS 5.1 | ✔ без «оставить большую» | `COLLISION_POLICY_LABELS` |
| Golden: меняется только блок конфига | ✔ `before_collisions: ()` | `tests/fixtures/golden/` |
| Прототип S12: 500+ элементов, typst.ts = CLI | ✔ | `SPIKES.md` |

### G2d: измерения PDF

Пара «таблица (after = 1 строка) → заголовок (before = 1 строка)»,
`document.line_spacing = 5.08 мм`, кегль 12 pt; шаг строки 22.30 pt.

| Политика | Зазор, pt | Ожидание |
|---|---:|---|
| без вставок | 19.52 | штатный интервал |
| одна сторона | 41.81 | 19.52 + 22.30 |
| `keep_previous` | 41.81 | 19.52 + 22.30 |
| `keep_current` | 41.81 | 19.52 + 22.30 |
| `keep_both` (default) | 64.11 | 19.52 + 2 × 22.30 |
| `drop_both` | 19.52 | без вставок |

## G3a — чек-лист (переделан)

Коммит: см. отчёт на воротах G3a.

| Пункт | Статус | Где |
|---|---|---|
| Схема сущности: `match`, `numbering`, `apply` | ✔ `numbering` — top-level | `app/registry/options.py` |
| Режимы `none` / `continue` / `own` задаются явно | ✔ без авто-переключения | `app/typst/fd.typ` |
| `none`: без номера, общий счётчик не сбит | ✔ | `test_structural_outline_numbering_none` |
| `none` + `##`: подраздел без `0.1` | ✔ | `test_structural_unnumbered_subheading_has_no_zero_prefix` |
| `continue`: общий номер и влияние на следующие | ✔ | `test_structural_numbering_own` |
| `own`: отдельный счётчик, `template`, `start`, `sub_template`, `group` | ✔ | `test_structural_numbering_own`, `test_structural_numbering_own_group` |
| `own` + `{letter}` при `kind=section` — не приложение | ✔ `(А) Раздел` | `test_own_letter_template_is_not_appendix` |
| Приложение — явный пресет `numbering.kind = "appendix"` | ✔ буква не зависит от `heading.numbering` | `test_appendix_numbering_true_and_global_none` |
| Подзаголовки приложения `А.1`, `А.1.1` | ✔ | `test_appendix_numbering_true_and_global_none` |
| Защита индекса 0 (не «Я») | ✔ `calc.max(1, index)` | `app/typst/fd.typ` |
| Тело приложения — `appendix.template` с `{service}`/`{letter}`/`{title}` в любом порядке | ✔ без числового префикса | `test_appendix_template_title_in_any_position`, `test_appendix_custom_template_and_empty_title` |
| Приложение: `numbering.start` сдвигает букву, `sub_template` применяется | ✔ start=5 → Д, `Д-1`, `Д-1.1` | `test_appendix_start_and_sub_template` |
| Приложение: `start=999` и серия после `ЯЯ` не падают | ✔ `АРЮ`, `ААА`; поведение закреплено в `AGENTS.md`/`OWNER_DECISIONS.md` | `test_appendix_large_start_does_not_overflow` |
| Приложение: `apply.case`/`apply.bold` сущности работают | ✔ регистр и полужирный | `test_appendix_entity_case_and_bold_apply` |
| Приложение: `apply.case`/`apply.bold` правила подзаголовка работают | ✔ `А.1 ПОДРАЗДЕЛ` | `test_subheading_entity_case_and_bold_apply` |
| Приложение: `arabic` — 1-based число, `latin` — A–Z | ✔ 9/10/11, 999; A/Z/AA | `test_appendix_arabic_alphabet_is_decimal`, `test_appendix_latin_letter_sequence` |
| `own`: подзаголовок с правилом и `apply.case`/`bold` | ✔ `I.1 ПОДРАЗДЕЛ` | `test_subheading_entity_case_and_bold_apply` |
| Неприменимые поля приложения скрыты в UI | ✔ `numbering.mode/template/group` при `kind=appendix` | `test_structural_entities_schema`, `RuleField.test.ts` |
| Приложение: нет `layout did not converge` на `А.1.1` | ✔ stderr проверяется | `test_appendix_numbering_subheadings` |
| Один авторитетный `heading`, без второго в `show` | ✔ заголовки собираются проходом по телу | `app/typst/fd.typ` |
| `outlined=false` убирает запись из `#outline()` | ✔ ровно одна запись в теле | `test_structural_outline_outlined_false` |
| `mode="none"` — одна запись без номера | ✔ | `test_structural_outline_numbering_none` |
| `mode="continue"` + `outlined=false` сохраняет номер в теле | ✔ | `test_structural_outline_outlined_false` |
| `case` / `bold` / `text_override` в записи оглавления | ✔ через тело заголовка | `test_structural_case_render` |
| Отступы `step` и `per_level` | ✔ 0-based level Typst | `test_outline_indent_render` |
| `match.mode` equals/contains/regex, регистр, уровень, приоритет | ✔ | `test_structural_match_modes_level_and_priority` |
| `apply.align`, `apply.around` сущности | ✔ | `test_structural_align_and_around` |
| `appendix.template`, пустое/многословное название, `{title}` не в конце | ✔ | `test_appendix_custom_template_and_empty_title`, `test_appendix_template_title_in_any_position` |
| `appendix.overflow` только `double`, после `ЯЯ` — тройное продолжение | ✔ `stop`/`latin` удалены | `test_appendix_large_start_does_not_overflow` |
| Миграция `apply.numbering`/`apply.appendix` | ✔ bool → mode; appendix → `kind=appendix` + own | `test_structural_entity_migration` |
| Пустой `outline.indent_per_level` | ✔ fallback `0mm`, без падения | `test_outline_empty_per_level_does_not_crash` |
| UI: подвкладка «Шаблонные заголовки» в «Заголовках», beta | ✔ универсальный рендерер | `app/registry/options.py` |
| Прототип S13: один авторитетный заголовок | ✔ | `SPIKES.md` |
| Отдельные счётчики рисунков/таблиц | — G3b, не начато | — |
| «где…», реферат, формулы | ✔ не трогались | — |

### G3a: измерения

| Правило | Тест | Измерение |
|---|---|---|
| Свой счётчик | `test_structural_numbering_own` | «I Раздел» в теле и одна запись в оглавлении |
| Общий `group` | `test_structural_numbering_own_group` | «I Первый», «II Второй» |
| Без номера | `test_structural_outline_numbering_none` | «Введение» без номера, следующий «1 Раздел» |
| Скрытие из оглавления | `test_structural_outline_outlined_false` | записи «Введение» нет, номер «1 Введение» в теле |
| Приложение при `heading.numbering=none` | `test_appendix_numbering_true_and_global_none` | «ПРИЛОЖЕНИЕ А.», «ПРИЛОЖЕНИЕ Б.», «А.1» |
| Отступы оглавления | `test_outline_indent_render` | `step` 5 мм: +14.17 pt/уровень; `per_level` 10/30 мм |
| Сопоставление | `test_structural_match_modes_level_and_priority` | equals/contains/regex/level/порядок |

### G3a: golden

16 снимков получили только ключи конфига: `numbering` у сущностей
(`kind`/`mode`/`template`/`start`/`sub_template`/`group`), `before_collisions`,
`outline.indent_mode: "step"`, `outline.indent_per_level`. Тела документов не
изменились. В фиксе блокеров G3a golden-снимки не менялись: дефолтный профиль
не содержит структурных сущностей, поэтому `kind` в снимки не попадает.

### Проверки G2d + G3a

Окружение: CI — Postgres 16 (service), Typst 0.14.2, Pandoc 3.9; локально
Postgres не запущен, поэтому DB-тесты локально пропущены, а в CI пройдены.

| Команда | Результат |
|---|---|
| **CI, GitHub Actions** | `test`: 134 passed, 148 deselected; `integration`: 148 passed, 134 deselected; `lint`: success — <https://github.com/YellowCytrus/FluentDocs/actions/runs/40844662044> |
| Локально `pytest -m "not integration" -q -rs` (без Postgres) | 68 passed, 66 skipped, 148 deselected |
| Локально `pytest -m integration -q -rs` (без Postgres) | 147 passed, 1 skipped, 134 deselected |
| `cd frontend && npm test -- --run` | 17 passed (4 files) |
| `cd frontend && npm run build` | OK |
| `npx vue-tsc --noEmit` | exit 0 |
| `uvx ruff check app tests scripts` | All checks passed |
| `uvx ruff format --check app tests scripts` | 102 files already formatted |
| `uv run python scripts/pdf_compare.py ...` | рабочий скрипт, отчёт JSON/MD |
| `node frontend/scripts/typst-parity.mjs` на S12 | 292 мс, 36 страниц, текст совпал с CLI |
