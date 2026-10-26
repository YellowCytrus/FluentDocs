# REGISTRY_SPEC — реестр опций оформления (G1a)

## Назначение

Реестр — единственный список допустимых опций профиля. Он описывает тип,
единицы, диапазон, значение по умолчанию, UI-подпись, источник и тесты для
каждой опции. Код реестра: `app/registry/options.py`; хранение и сериализация:
`app/registry/storage.py`.

Версия схемы: `SCHEMA_VERSION = 1` (`app/registry/options.py`).
Число опций: **349** — 128 обычных и 221 поле `text_override`.

## Запись реестра

Каждая опция — `Option` (`dataclass`, frozen) со следующими полями:

| Поле | Смысл |
|---|---|
| `id` | Уникальный id вида `group.element.option`, латиница, snake_case |
| `group` | Группа опций (см. ниже) |
| `applies_to` | Элементы, к которым применяется опция (`heading_1`, `par`, …) |
| `type` | `number`, `integer`, `boolean`, `string`, `select`, `markers`, `list`, `object` |
| `unit` | Каноническая единица значения (`mm`, `pt`, `%`, …) |
| `allowed_units` | Допустимые единицы для UI-пересчёта |
| `min`, `max`, `step` | Границы и шаг для чисел |
| `enum` | Допустимые значения для `select` |
| `default` | Значение по умолчанию; для `text_override` — значение при включении переопределения |
| `nullable` | Допустим ли `null` |
| `depends_on` | Зависимости от других опций (сейчас пусто) |
| `ui` | `control`, `label`, `tab`, `order`, `options`, `section` — данные для универсального рендерера |
| `required` | Обязательное поле вложенной схемы (`list`/`object`) |
| `enum_labels` | Подписи значений `select` для вложенных полей |
| `fields` | Вложенная схема `object` |
| `item_fields` | Схема элемента `list` |
| `item_variants` | Допустимые наборы полей по `type` элемента списка |
| `rationale` | Зачем опция существует (1–2 предложения) |
| `source` | Пункт СТУ и/или id правила плана v2 |
| `test_ids` | Имена тестов, покрывающих опцию |
| `path` | Путь значения во вложенном JSONB |

`path` и `id` не совпадают у вложенных групп: id — стабильное имя для API/UI,
path — адрес значения в JSONB. Например, `heading.h1.break_before` имеет path
`("heading_levels", "1", "break_before")`.

Опции G1a помечены `legacy=True`: их конкретные `rationale`/`source`/`test_ids`
дописываются до G6. Новые опции G1c (`outline.indent_mode`, `outline.indent_mm`)
и G2a (все `around.*`) имеют `legacy=False`, конкретные `rationale`/`source`
и собственные тесты. Реестровый тест запрещает шаблонные rationale/source для
`legacy=False` и общий набор `TEST_IDS`.

## Группы опций

| Группа (`group`) | Обычные | `text_override` | Всего |
|---|---:|---:|---:|
| `page` — страница | 9 | 0 | 9 |
| `document` — глобальный текст | 15 | 0 | 15 |
| `par` — абзац | 4 | 13 | 17 |
| `heading` — заголовки и уровни 1–6 | 13 | 78 | 91 |
| `bullet_list` — маркированный список | 5 | 13 | 18 |
| `numbered_list` — нумерованный список | 9 | 13 | 22 |
| `terms` — список определений | 4 | 13 | 17 |
| `table` — таблица | 4 | 13 | 17 |
| `figure` — рисунок | 7 | 13 | 20 |
| `equation` — формула | 0 | 13 | 13 |
| `quote` — цитата | 3 | 13 | 16 |
| `footnote` — сноска | 4 | 13 | 17 |
| `raw` — код | 3 | 13 | 16 |
| `outline` — оглавление | 3 | 13 | 16 |
| `around` — окружение элемента | 45 | 0 | 45 |
| **Итого** | **128** | **221** | **349** |

`text_override` — не отдельная опция-переключатель. Наличие объекта
`"text_override": {...}` включает переопределение текста для элемента; `null`
выключает. Поля объекта — отдельные опции с id
`<element>.text_override.<field>`.

## Формат значений JSONB

Значения профиля хранятся в `profiles.options` (`JSONB`) и имеют вложенную форму:

```json
{
  "page": {"paper": "a4", "margin_left": 30.0},
  "document": {"font_size": 14.0},
  "par": {
    "spacing": 4.2333333333,
    "text_override": null
  },
  "heading": {"numbering": "1.1.1"},
  "heading_levels": {
    "1": {"break_before": false, "numbering_enabled": true, "text_override": null}
  },
  "bullet_list": {"marker": ["- ", "‣", "–"], "text_override": null},
  "figure": {"width": 4.2333333333, "text_override": null},
  "equation": {"text_override": null},
  "around": {
    "table": {
      "before": [],
      "after": [
        {"type": "blank", "count": 1, "line_spacing": {"mode": "multiplier", "value": 1.0}}
      ],
      "collapse": "max"
    }
  }
}
```

Правила:

- Длины хранятся в мм; `unit`/`allowed_units` описывают допустимые единицы UI.
- `document.hyphenate` и `text_override.hyphenate`: `null` = авто, `"true"` /
  `"false"` = явное значение. При записи в старые таблицы они превращаются в
  `null` / `True` / `False`.
- `text_override` для элемента либо `null`, либо объект со всеми 13 полями.
  Неполный объект при `PUT` дополняется дефолтами.
- `outline.indent_mode` — `auto` / `none` / `custom`, `outline.indent_mm` — мм.
  В режиме `auto` `indent` в `#set outline(...)` не передаётся, `none` даёт
  `0mm`, `custom` — `indent_mm`. Произвольные строки в этих полях отвергаются.
  Старая колонка `outline_styles.indent` и старый JSONB-ключ `outline.indent`
  миграцией `b1c2d3e4f5a6` переводятся в `indent_mode`/`indent_mm`; колонка
  остаётся в БД, но генератором не читается.
- `around.<target>.before/after` — список объектов-вставок. Обязательное поле
  `type` (`blank`, `text`, `line`, `pagebreak`); набор остальных полей зависит
  от типа. Неизвестный `type`, лишний ключ, отсутствующий обязательный ключ,
  неверный тип и выход за `min`/`max` отвергаются с `400`.
- `line_spacing` — вложенный объект `{"mode": "multiplier"|"mm", "value": number}`;
  в режиме `multiplier` значение умножается на `document.line_spacing`.
- `around` не имеет старых колонок. Он живёт только в JSONB и сохраняется при
  пересборке JSONB после записи в старые element-таблицы
  (`serialize_profile` переносит существующий блок `around`).
- `PUT /profiles/{id}/options` принимает неполный объект: отсутствующие поля
  дополняются дефолтами реестра. Неизвестные ключи, неверные типы и выход за
  `min`/`max` отвергаются с `400`.

## Дефолты

Дефолты реестра равны текущим дефолтам ORM-моделей (`column.default`), потому
что именно ORM-строка создаётся при первом обращении к стилю. Для
`document.font` и `text_override.font` ORM использует `Merriweather`; Pydantic
по умолчанию содержит `libertinus serif`, но это значение не попадает в БД без
явной записи. Реестр следует ORM; расхождение зафиксировано здесь.

Для `text_override` дефолты полей равны дефолтам `TextOverrideStyle`; сам
объект по умолчанию отсутствует (`null`).

`around` по умолчанию пуст для всех 15 целей: `before: []`, `after: []`,
`collapse: "max"`. Пустые списки не создают вставок и не меняют вывод. В
конфиге Typst всегда присутствует блок `around` (новый блок в golden-снимках),
но `fd` возвращает элемент без изменений, если вставок нет.

## Покрытие старых опций

Реестр покрывает все не-технические колонки ORM и поля
`frontend/src/config/styleFields.ts`.

Не включены:

| Опция | Причина |
|---|---|
| `heading_level_styles.outlined` | Мёртвое поле; в реестр не внесено, удалено из API/UI на G1c, колонка БД остаётся |
| `heading_level_styles.bookmarked` | То же |
| `heading_level_styles.offset` | То же |
| `outline_styles.indent` | Старая строка-выражение; заменена `outline.indent_mode`/`indent_mm`, колонка БД остаётся |
| `id`, `profile_id`, `text_override_style_id`, `level` | Технические ключи, не опции оформления |
| `text_override` как единое поле | Заменено набором опций полей; включение — наличие объекта |

`figure.outlined` **включён**: генератор использует его для списка фигур.

## API

`GET /registry/options` возвращает схему для универсального UI:

```json
{
  "schema_version": 1,
  "groups": [{"id": "page", "label": "Страница"}],
  "options": [
    {
      "id": "page.margin_left",
      "type": "number",
      "unit": "mm",
      "min": 0,
      "max": 100,
      "default": 25.0,
      "path": ["page", "margin_left"],
      "ui": {"control": "number", "label": "Поле слева", "tab": "Страница", "order": 2}
    }
  ]
}
```

`GET /profiles/{profile_id}/options` →

```json
{
  "schema_version": 1,
  "source": "jsonb",
  "values": { ... }
}
```

- Если `profiles.options` непуст, значения читаются из JSONB (`source=jsonb`).
- Если JSONB пуст (`{}`), значения собираются из старых таблиц (`source=legacy`).
- Если версия схемы не совпадает с `SCHEMA_VERSION` — `409`.

`PUT /profiles/{profile_id}/options` принимает
`{"schema_version": 1, "values": {...}}` и:

1. проверяет версию схемы (`400` при несовпадении);
2. нормализует и валидирует значения;
3. записывает значения в старые таблицы (все стили и `text_override`);
4. сохраняет те же значения в `profiles.options` и
   `profiles.options_schema_version`.

Старые element-API (`POST/PATCH/PUT /profiles/{id}/<element>`) после записи
пересобирают JSONB из старых таблиц, поэтому JSONB не устаревает. GET, который
создаёт отсутствующую строку стиля, делает то же после создания. Это и есть
«запись в оба места» на время переходного периода.

## Миграция значений между версиями схемы

1. Любое несовместимое изменение формы значений увеличивает
   `SCHEMA_VERSION` и добавляет Alembic-миграцию/функцию переноса.
2. Добавление новой опции с дефолтом совместимо: старый JSONB при чтении
   дополняется дефолтом через `normalize_values`.
3. Удаление/переименование опции требует явного переноса старых значений в
   миграции; молчаливое отбрасывание запрещено. Пример G1c:
   `b1c2d3e4f5a6` переносит `outline.indent` в `indent_mode`/`indent_mm`
   и в старых колонках, и в `profiles.options`.
4. После миграции `profiles.options_schema_version` обновляется, а JSONB
   пересобирается из старых таблиц. Старые таблицы остаются для совместимости,
   но с G1b генератор читает JSONB; пустой JSONB — fallback на старые таблицы.
5. Пока поддерживается только версия 1. Чтение JSONB с другой версией даёт
   `409`, запись — `400`.

## Рантайм G1b (обновлено в G1c)

Полный Typst-исходник собирает одна функция
`app.utils.typst_source.build_typst_source`:

1. библиотека `fd` (`app/typst/fd.typ`) вставляется в начало исходника;
2. затем `#let fd-config = (...)` — Typst-литерал, собранный из JSONB
   (`options_payload` → `build_fd_config`);
3. затем `#show: fd.apply.with(fd-config)`;
4. затем титульник (если есть) и тело из Pandoc.

SFU-титульник идёт до `fd-config`/`fd.apply`, чтобы правила профиля (например,
`show table.cell`) не влияли на его таблицы. Обычный титульник идёт после
`fd.apply`, как и тело.

Превью в `Editor.vue` использует `preamble + "\n" + typstBody`, где
`GET /profiles/{id}/preamble` возвращает шаги 1–3. PDF и `export-typ` вызывают
ту же `build_typst_source`, поэтому их исходники совпадают; это проверяется
тестом `test_pdf_and_export_use_identical_source`.

## UI G1c

Страница `/rules` (`frontend/src/views/Rules.vue`) строится одним рендерером
`RuleField.vue` по схеме `/registry/options`; отдельного Vue-кода под правила
нет. Поддерживаемые контролы: number/integer (ползунок + число + единицы),
boolean (переключатель), string, select (выпадающий список), markers (3 поля),
list (карточки элементов с добавлением, удалением и перестановкой ↑/↓),
object (вложенные поля; nullable-объект включается кнопкой «Задать значения»).
Значения читаются и пишутся через `GET`/`PUT /profiles/{id}/options`.
Секции `text_override` включаются переключателем и заполняются дефолтами
реестра. Старая страница `/styles` не удалена.

## Golden G1c

Снимки `tests/fixtures/golden/**/*.typ` больше не содержат библиотеку `fd`.
Формат снимка:

```text
#let fd-config = (...)
// --- document body ---
<body from Pandoc>
```

`build_golden_source` пишет только конфиг и тело; `golden_to_full_source`
подставляет текущую `fd` перед компиляцией. Поэтому правка `fd.typ` не меняет
снимки, а сама библиотека проверяется рендер-тестами и golden-компиляцией.

G2a добавила в конфиг только блок `around` (77 строк на снимок). Тела
документов и остальные опции не менялись; сравнение старых и новых PDF
(16 файлов, `pdfplumber`: страницы, координаты, кегль, шрифты, текст) — полное
совпадение.

## G2a: типы `list`/`object` и окружение `around`

Вложенные схемы хранятся в самой `Option`:

- `fields` — поля `object`;
- `item_fields` — поля элемента `list`;
- `item_variants` — какие поля допустимы для каждого значения `type`;
- `required`, `enum_labels` — обязательность и подписи enum-значений.

Валидация рекурсивная: для `object` неизвестные ключи отвергаются, отсутствующие
необязательные поля дополняются дефолтами; для `list` каждый элемент должен
быть объектом с допустимым `type`, лишние для этого типа ключи — `400`.
UI-рендерер `RuleField.vue` обрабатывает `list` и `object` рекурсивно; отдельного
Vue-кода под конкретное правило нет.

Окружение доступно для 15 целей: `heading_1`…`heading_6`, `par`,
`bullet_list`, `numbered_list`, `table`, `figure`, `equation`, `quote`, `raw`,
`terms`. Для каждой цели три опции: `around.<target>.before`,
`around.<target>.after`, `around.<target>.collapse` (45 опций).

Семантика `collapse`:

| Значение | Пустая строка | Складывание |
|---|---|---|
| `max` | `v(..., weak: true)` | Typst схлопывает соседние слабые отступы до максимума; сверху страницы отступ исчезает |
| `sum` | жёсткий `v(...)` | Соседние вставки и штатные отступы элемента суммируются |
| `none` | не вставляется | Пустые строки игнорируются; текст/линия/разрыв страницы продолжают работать |

Вставка `blank` с `count: 0` — no-op: `fd` не оборачивает элемент, вывод
совпадает с профилем без `around`. `text` вставляет абзац с выравниванием и
необязательным `text_override`; `line` рисует линию заданной длины и толщины;
`pagebreak` вставляет `pagebreak(weak: ...)`.

Таблицы Pandoc приходят как `figure(kind: table)`, поэтому `around.table`
применяется на уровне этой фигуры (иначе `pagebreak` попадал бы внутрь
контейнера таблицы). `around.figure` применяется к остальным фигурам.

Измерения PDF (`tests/test_around_render.py`, `pdfplumber`, документ
таблица → заголовок, `document.line_spacing = 5.08 мм`):

| Сценарий | Ожидание | Измерено |
|---|---|---|
| без `around` | штатный зазор | 19.52 pt |
| `max`, по одной пустой строке с двух сторон | ≈ одна строка (14.4 pt) | 12.32 pt |
| `sum`, по одной строке с двух сторон | штатный + 2 × 14.4 pt | 48.32 pt |
| `none` | штатный зазор | 19.52 pt |
| `count: 0` | штатный зазор | 19.52 pt |
| верх страницы, `max`, 5 строк по 10 мм | отступ исчезает | 69.04 pt = без `around` |
| верх страницы, `sum`, те же 5 строк | жёсткий сдвиг | 210.77 pt |

Разница `max` с 14.4 pt объясняется тем, что слабый отступ схлопывается со
штатным отступом заголовка, а не складывается с ним.

## Паритет и скорость G1c

`tests/test_preview_parity.py` собирает один Markdown + профиль двумя путями
(серверный `build_typst_source` и превью `preamble + "\n" + body`), компилирует
PDF через Typst CLI и Node + `typst.ts`, затем сравнивает источник, число
страниц, текст страниц и имена шрифтов. Скрипты:
`frontend/scripts/typst-parity.mjs`, `frontend/scripts/typst-render.mjs`,
`frontend/scripts/typst-preview-bench.mjs`.

Замер перерисовки: документ 152 страницы, `typst.ts` компилирует правку за
135 мс (порог S8 — 2 с). Конфигурация машины и числа — в `PROGRESS.md`.
