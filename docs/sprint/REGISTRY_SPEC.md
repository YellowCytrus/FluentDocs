# REGISTRY_SPEC — реестр опций оформления (G1a)

## Назначение

Реестр — единственный список допустимых опций профиля. Он описывает тип,
единицы, диапазон, значение по умолчанию, UI-подпись, источник и тесты для
каждой опции. Код реестра: `app/registry/options.py`; хранение и сериализация:
`app/registry/storage.py`.

Версия схемы: `SCHEMA_VERSION = 1` (`app/registry/options.py`).
Число опций: **402** — 181 обычная и 221 поле `text_override`.

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
| `page` — страница | 15 | 0 | 15 |
| `document` — глобальный текст | 16 | 0 | 16 |
| `par` — абзац | 4 | 13 | 17 |
| `heading` — заголовки и уровни 1–6 | 27 | 78 | 105 |
| `bullet_list` — маркированный список | 9 | 13 | 22 |
| `numbered_list` — нумерованный список | 13 | 13 | 26 |
| `terms` — список определений | 8 | 13 | 21 |
| `table` — таблица | 6 | 13 | 19 |
| `figure` — рисунок | 9 | 13 | 22 |
| `equation` — формула | 3 | 13 | 16 |
| `quote` — цитата | 5 | 13 | 18 |
| `footnote` — сноска | 6 | 13 | 19 |
| `raw` — код | 5 | 13 | 18 |
| `outline` — оглавление | 3 | 13 | 16 |
| `around` — окружение элемента | 45 | 0 | 45 |
| `structural` — структурные элементы | 1 | 0 | 1 |
| `appendix` — приложения | 6 | 0 | 6 |
| **Итого** | **181** | **221** | **402** |

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
      "before_collisions": [{"previous": "any", "policy": "keep_both"}]
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
- `outline.indent_mode` — `step` / `per_level`; `outline.indent_mm` — шаг в мм
  для `step`, `outline.indent_per_level` — список `{mm}` по уровням для
  `per_level`. Заполнитель (`fill`) не настраивается: всегда штатный Typst.
  Индекс уровня в Typst 0-based: `indent = level * step`, для `per_level` —
  `levels.at(level)`. Старые `auto`/`none`/`custom` при чтении старой таблицы
  переводятся в `step`, колонка `outline_styles.indent` не читается.
- `around.<target>.before/after` — список объектов-вставок. Обязательное поле
  `type` (`blank`, `text`, `line`, `pagebreak`); набор остальных полей зависит
  от типа. Неизвестный `type`, лишний ключ, отсутствующий обязательный ключ,
  неверный тип и выход за `min`/`max` отвергаются с `400`.
- `document.line_spacing` — объект `{"mode": "multiplier"|"mm", "value": number}`.
  `mm` — ведущий интервал Typst в миллиметрах; `multiplier` — множитель
  естественной высоты строки выбранного шрифта (1.5 = полуторный). Старое
  число в JSONB и старая колонка читаются как `{"mode": "mm", ...}`.
- `line_spacing` внутри `around.blank` — такой же объект. Единица `blank` —
  полный шаг строки: `fd.line-step(config)` = leading + высота строки шрифта.
  Для `multiplier` шаг равен `value * line_height_em * document.font_size`;
  множитель самой пустой строки задаёт долю шага документа. Для `mm` шаг равен
  `value мм + (line_height_em - default_leading_em) * document.font_size`.
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
`before_collisions: []`. Пустые списки не создают вставок и не меняют вывод.
Политика по умолчанию и fallback — `keep_both`. В конфиге Typst всегда
присутствует блок `around` (новый блок в golden-снимках), но `fd` возвращает
элемент без изменений, если вставок нет.

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
`around.<target>.after`, `around.<target>.before_collisions` (45 опций).

`before_collisions` — список объектов `{previous, policy}`. `previous` — вид
предыдущего элемента (`any`, `par`, `heading_1`…`heading_6`, `bullet_list`,
`numbered_list`, `table`, `figure`, `equation`, `quote`, `raw`, `terms`).
Правила проверяются по порядку, первое подходящее выигрывает; если ни одно не
подошло — `keep_both`. Политика действует, только когда обе стороны непусты:

| Политика | Что остаётся |
|---|---|
| `keep_previous` | `after` предыдущего, `before` текущего отбрасывается |
| `keep_current` | `before` текущего, `after` предыдущего отбрасывается |
| `keep_both` | обе вставки, сначала предыдущая, затем текущая |
| `drop_both` | ни одной |

Старое поле `collapse` удалено; `max|sum` при чтении JSONB мигрируют в
`before_collisions: [{previous: "any", policy: "keep_both"}]`. `blank` — жёсткий
`v(count × step)`, поэтому `keep_both` складывает вставки. На верху страницы
`blank` не создаёт зазор (проверка `here().position().y`), явный `pagebreak`
сохраняется. Штатные интервалы `spacing_before/after` (G2c) независимы от
вставок: `around` больше не заменяет их.

Реализация — один проход по верхнеуровневым элементам тела (`body-units` в
`fd.typ`): вид элемента определяется по функции/полям, предыдущий известен из
соседнего элемента. Таблицы Pandoc приходят как `figure(kind: table)`, поэтому
вид — `table`; остальные фигуры — `figure`. Заголовки в этом же проходе
пересобираются один раз (см. G3a), поэтому `#outline()` не видит дублей.

Измерения PDF (`tests/test_around.py`, `pdfplumber`, документ таблица →
заголовок, `document.line_spacing = 5.08 мм`, кегль 12 pt, шаг 22.30 pt):

| Сценарий | Зазор, pt |
|---|---:|
| без `around` | 19.52 |
| вставка только с одной стороны | 41.81 |
| `keep_previous` | 41.81 |
| `keep_current` | 41.81 |
| `keep_both` (default) | 64.11 |
| `drop_both` | 19.52 |
| верх страницы: `blank(5 × 10 мм)` | как без `around` |

## G2c: принятые дефолтные интервалы

Новые дефолты интервалов приняты владельцем 29.10.2026. PDF по умолчанию
может отличаться от `4e6a8c0`; baseline — текущие значения, возврат не нужен.
`tests/fixtures/baseline/g2c_geometry.json` фиксирует измеренную геометрию для
всех 28 интервалов, включая `raw`, `quote`, `terms`.
`tests/test_g2c_spacing.py::test_default_geometry_baseline` сравнивает PDF с
baseline с допуском 0.5 pt.

## Паритет и скорость G1c

`tests/test_preview_parity.py` собирает один Markdown + профиль двумя путями
(серверный `build_typst_source` и превью `preamble + "\n" + body`), компилирует
PDF через Typst CLI и Node + `typst.ts`, затем сравнивает источник, число
страниц, текст страниц и имена шрифтов. Скрипты:
`frontend/scripts/typst-parity.mjs`, `frontend/scripts/typst-render.mjs`,
`frontend/scripts/typst-preview-bench.mjs`.

Замер перерисовки: документ 152 страницы, `typst.ts` компилирует правку за
135 мс (порог S8 — 2 с). Конфигурация машины и числа — в `PROGRESS.md`.

На G2b паритет повторён для профиля `document.font = "PT Astra Serif"` и
`line_spacing = {mode: "multiplier", value: 1.5}` на тех же 8 документах:
совпали источник, страницы, текст и имена шрифтов. `typst.ts` и сервер
загружают один каталог `assets/fonts/`; CDN из паритета исключён.

## G2b: межстрочный интервал, шрифты и вынесенные константы

- `document.line_spacing` — объект `{mode, value}`. Режим `mm` сохраняет
  прежнее поведение. Режим `multiplier` считает ведущий интервал по формуле
  `fd.line-pitch`: `(m * natural - (natural - default_leading)) * 1em`.
- `document.line_height_em` — ручной коэффициент естественной высоты строки
  для шрифта, которого нет в таблице. Для известных шрифтов таблица
  `FONT_LINE_HEIGHT_COEFFICIENTS` важнее ручного значения: Libertinus Serif
  1.308, PT Astra Serif 1.312 (замер S9). Автозамер при загрузке нового шрифта
  не делается — открытый вопрос в `BLOCKERS.md`.
- `document.default_leading_em = 0.65` — техническое значение Typst, вынесено
  из `fd.typ` в данные реестра.
- В опции вынесены: `heading.unnumbered_indent` (было `-0.3em`),
  `bullet_list.tight_spacing` / `loose_spacing`,
  `numbered_list.tight_spacing` / `loose_spacing`,
  `terms.tight_spacing` / `loose_spacing` (было `0.5em` / `1em`).
  Дефолты равны прежним константам, поэтому тела golden-снимков не меняются.
- Шрифты: `assets/fonts/` содержит PT Astra Serif (4 TTF + OFL) и набор
  typst-assets v0.13.1 (Libertinus, New Computer Modern, DejaVu Sans Mono).
  Сервер получает `--font-path assets/fonts`, `typst.ts` —
  `TypstSnippet.preloadFonts` из тех же файлов. SHA-256 — в отчёте G2b.
- Старые абсолютные значения интервала мигрируют в `{mode: "mm", value}`.
  JSONB хранит абстрактный множитель, старая колонка `document_styles.line_spacing`
  получает эквивалент в мм; при пересборке JSONB множитель сохраняется, пока
  колонка не изменена вручную.

## G2c: штатные интервалы элементов

Скрытые интервалы блоков Typst вынесены в 28 опций реестра (по две на элемент):
`heading.h1..h6.spacing_before/after`, `figure`, `table`, `equation`, `quote`,
`raw`, `terms`, `bullet_list`, `numbered_list`. Тип — `number`, единица `em`
от кегля документа; диапазон 0–20, шаг 0.01. Значения по умолчанию приняты
владельцем 29.10.2026; PDF по умолчанию может отличаться от `4e6a8c0`, baseline
фиксируется в `tests/fixtures/baseline/g2c_geometry.json`.

| Элемент | before | after | Источник |
|---|---:|---:|---|
| `heading.h1` | 1.8 | 0.75 | СТУ 7.4.1; Typst heading |
| `heading.h2..h6` | 1.44 | 0.75 | СТУ 7.4.1; Typst heading |
| `figure` | 1.2 | 1.2 | СТУ 7.8; BlockElem |
| `table` | 1.2 | 1.2 | СТУ 7.7; BlockElem |
| `equation` | 1.2 | 1.2 | СТУ 7.6; BlockElem |
| `quote` | 2.4 | 1.8 | СТУ 7.3; Typst quote |
| `raw` | 1.2 | 1.2 | СТУ 7.3; BlockElem |
| `terms` | 1.2 | 1.2 | СТУ 7.4; BlockElem |
| `bullet_list` | 1.2 | 1.2 | СТУ 7.4; BlockElem |
| `numbered_list` | 1.2 | 1.2 | СТУ 7.4; BlockElem |

В `fd` интервал считается как `value * document.font_size` (pt), а не как
`value * 1em` внутри заголовка: иначе `em` зависел бы от кегля заголовка.
Тесты: `test_element_spacing_options` (дефолты, конфиг, JSONB) и
`test_element_spacing_render` (28 параметров, измеренный сдвиг START→END равен изменению в em × кегль ± 0,5 pt).

## G2c: оставшиеся правила класса A сложности 1–2

Добавлены опции без старых колонок (только JSONB):

| Правило | Опции | Тесты | Статус |
|---|---|---|---|
| `page.margins.landscape` | `page.margin_landscape_top/bottom/left/right` | `test_page_landscape_*` | реализовано; ориентация — только весь документ |
| `page.numbering` | `page.numbering_skip_first`, `page.numbering_start` | `test_page_numbering_*` | реализовано; шаблон и позиция были раньше |
| `formula.body_indent` | `equation.body_indent` | `test_equation_body_indent_*` | реализовано |
| `reference.footnote` | `footnote.separator_length`, `footnote.separator_stroke` | `test_footnote_separator_*` | реализовано; маркер и зазоры были раньше |
| `heading.spacing_before/after` | 12 опций `heading.h1..h6.spacing_*` | `test_element_spacing_*` | реализовано |
| `figure/table/formula.spacing_*` | 6 опций | `test_element_spacing_*` | реализовано |

Остальные правила класса A/1–2 уже покрыты существующими опциями
(`page.margins.portrait`, `text.*`, `heading.h1..h6`, `heading.no_hyphenation`
через `text_override.hyphenate`, `list.item` через `indent`/`body_indent`,
`figure.image`, `figure.placement_after_reference`, `table.cell_padding`,
`table.font.size` через `text_override`).

Отложено до G3/G4/G6 и не входит в G2c:

- `referat.keywords_uppercase` — структурная сущность (G3);
- `toc.indent_levels` — оглавление (G4);
- `list.nested_numeric` — формат нумерации по уровням (G3);
- `figure.caption`, `table.caption` — подписи (G3);
- `table.body` — шапка таблицы в генераторе (G4);
- `coursework.*`, `graduation_qualification_work.*` — значения seed-профиля (G6);
- `bibliography.entry` — сопоставитель структурных сущностей (G3a).


## G3a: структурные сущности, приложения и оглавление

`structural.entities` — список объектов, порядок задаёт приоритет. Опция
перенесена во вкладку «Заголовки», подвкладка «Шаблонные заголовки»; в `ui`
стоит `beta: true`. Схема (AGENTS 5.2):

```
{
  id, label,
  match: { target: "heading", level: "any"|"1".."6",
           mode: "equals"|"contains"|"regex", value, case_insensitive },
  numbering: { kind: "section"|"appendix",
               mode: "none"|"continue"|"own",
               template, start, sub_template, group },
  apply: { break_before, align, case, bold, outlined,
           around: { before, after, before_collisions }, text_override }
}
```

`numbering` — top-level, режим задаётся явно; автоматического переключения по
наличию шаблона нет. `none` — заголовок и его подразделы без номера, общий
счётчик не меняется; `continue` — общий номер и влияние на следующие
заголовки; `own` — отдельный счётчик, не влияющий на общий. Для `own`:
`template` — Typst-шаблон номера (`"1"`, `"(1)"`, `"I"`, `"A"`); если в
шаблоне есть `{letter}`, он заменяется буквой из `appendix.alphabet` по
значению счётчика; `start` — начальное значение, `sub_template` — шаблон
подзаголовков с `{prefix}` (номер семейства) и `{n}` (относительный номер:
`1` для 2-го уровня, `1.1` для 3-го), `group` — общий счётчик для нескольких
правил (пусто = `id`).

`kind` — явный пресет: `section` (обычное правило) или `appendix`
(приложение). Приложение больше не определяется эвристикой по `{letter}`:
правило `own` с шаблоном `({letter})` и `kind = "section"` даёт `(А) Раздел`,
а не формат приложения. В UI `kind` — выбираемый пресет «Приложение (пресет)».

Миграция: старое `apply.numbering: bool` → `none`/`continue`; старое
`apply.appendix: true` → `kind = "appendix"`, `mode = "own"`,
`template = "{letter}"`, `group = "appendix"`. Старое правило с точно
`template = "{letter}"` и `group = "appendix"` также получает
`kind = "appendix"`; остальные — `kind = "section"`. `apply.appendix` и
`apply.numbering` в новой схеме отсутствуют. Валидация: уникальные `id`,
непустой `match.value`.

Приложение — пресет `kind = "appendix"` (внутри `mode = "own"`). Буква
присваивается автоматически и не зависит от глобального `heading.numbering`,
в том числе `"none"`. `appendix.template` — полная строка заголовка;
`{service}`, `{letter}` и `{title}` подставляются в любом порядке, `{title}`
может быть пустым. `numbering.start` сдвигает букву (1 = А), `sub_template`
задаёт подзаголовки (`А.1`, `А.1.1` по умолчанию). Индекс буквы защищён
`max(1, index)`, поэтому до первого шага не выводится «Я». Счётчики
рисунков/формул сбрасываются на приложении.

Оглавление: у заголовка ровно один авторитетный элемент. Заголовки
пересобираются проходом по телу до показа, а не вторым `heading` внутри
`show`; поэтому `outlined=false` убирает запись, `numbering=none` даёт ровно
одну запись без номера, а номер в теле сохраняется при `outlined=false`.
`case`/`bold`/`text_override` применяются к телу заголовка и попадают в запись.
Свой номер (`own`) и полная строка приложения выводятся в теле заголовка при
`numbering: none`; `counter(heading)` не меняется. Поэтому оглавление
получает тот же текст, что тело, а общий счётчик `continue` не сбивается.

`outline.indent_mode`: `step` (отступ = `level * indent_mm`, level 0-based в
Typst) или `per_level` (`indent_per_level[level]`). Пустой `indent_per_level`
даёт fallback `0mm`, компиляция не падает. `fill` не настраивается.

Опции приложений:

| Опция | Дефолт | Смысл |
|---|---|---|
| `appendix.template` | `{service} {letter}. {title}` | одна строка заголовка |
| `appendix.service_case` | `upper` | регистр слова «Приложение» |
| `appendix.title_case` | `none` | регистр названия |
| `appendix.bold` | `false` | полужирный заголовок |
| `appendix.alphabet` | `ru_sfu` | 25 букв без Ё, З, Й, О, Ч, Ь, Ы, Ъ |
| `appendix.overflow` | `double` | после Я — АА, АБ… |

`appendix.overflow` содержит только `double`; `stop` и `latin` удалены из
реестра, UI и кода. `heading.keep_with_next` (дефолт `true`) — `sticky: true`
у блока заголовка. `match.target` — только `heading`; `paragraph` не
реализуется (отложен с «где…»).

Тесты: `tests/test_g3a_structural.py` (схема, миграция, свои счётчики,
приложения при `heading.numbering=none`, `outlined`/`numbering` в `#outline()`,
`step`/`per_level`, сопоставление, `align`, `around`).
