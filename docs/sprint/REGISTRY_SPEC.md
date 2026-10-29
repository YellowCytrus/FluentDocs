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

На G4 реализованы `toc.indent_levels` (отступы оглавления) и `table.body`
в объёме повтора шапки и кегля через `table.text_override.font_size`.

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
шаблоне есть `{letter}`, он заменяется номером/буквой из `appendix.alphabet`
(для `arabic` — числом) по значению счётчика; `start` — начальное значение,
`sub_template` — шаблон подзаголовков с `{prefix}` (номер семейства) и `{n}` (относительный номер:
`1` для 2-го уровня, `1.1` для 3-го), `group` — общий счётчик для нескольких
правил (пусто = `id`).

`kind` — явный пресет: `section` (обычное правило) или `appendix`
(приложение). Приложение больше не определяется эвристикой по `{letter}`:
правило `own` с шаблоном `({letter})` и `kind = "section"` даёт `(А) Раздел`,
а не формат приложения. В UI `kind` — выбираемый пресет «Приложение (пресет)».
При `kind = "appendix"` поля `numbering.mode`, `numbering.template` и
`numbering.group` не применяются и скрываются универсальным рендерером по
`enabled_when: {key: "kind", values: ["section"]}`; `start` и `sub_template`
остаются рабочими.

Миграция: старое `apply.numbering: bool` → `none`/`continue`; старое
`apply.appendix: true` → `kind = "appendix"`, `mode = "own"`,
`template = "{letter}"`, `group = "appendix"`. Старое правило с точно
`template = "{letter}"` и `group = "appendix"` также получает
`kind = "appendix"`; остальные — `kind = "section"`. `apply.appendix` и
`apply.numbering` в новой схеме отсутствуют. Валидация: уникальные `id`,
непустой `match.value`.

Приложение — пресет `kind = "appendix"` (внутри `mode = "own"`). Номер
присваивается автоматически и не зависит от глобального `heading.numbering`,
в том числе `"none"`. `appendix.alphabet = "arabic"` — это 1-based десятичное
число (`1`, `2`, …, `999`), а не 0-based цифры; `ru_sfu` и `latin` — буквы.
`appendix.template` — полная строка заголовка; `{service}`, `{letter}` и
`{title}` подставляются в любом порядке, `{title}` может быть пустым.
`numbering.start` сдвигает номер/букву (1 = А или 1), `sub_template` задаёт
подзаголовки (`А.1`, `А.1.1` по умолчанию). Индекс буквы защищён `max(1,
index)`, поэтому до первого шага не выводится «Я». После исчерпания
двухбуквенных сочетаний (`ЯЯ` для `ru_sfu`) те же буквы продолжаются в
тройном сочетании (`ААА`, `ААБ…`), поэтому `start` до 999 и длинные серии
приложений не выходят за границы массива и не роняют Typst; это продолжение
режима `double`, зафиксированное в `AGENTS.md` 5.3 и `OWNER_DECISIONS.md`.
`apply.case` сущности применяется ко всей строке её заголовка после
`appendix.service_case`/`title_case`; для подзаголовка приложения применяется
`apply.case`/`apply.bold` текущего правила подзаголовка, а `appendix.bold`
действует глобально. Для `own` подзаголовок без своего правила наследует
номер родителя; если правило подзаголовка есть (`mode="continue"`), его
`apply.case`/`apply.bold` применяются к тексту. Счётчики рисунков/формул
сбрасываются на приложении.

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
| `appendix.alphabet` | `ru_sfu` | 25 букв без Ё, З, Й, О, Ч, Ь, Ы, Ъ; `latin` — A–Z; `arabic` — число 1, 2, … |
| `appendix.overflow` | `double` | после Я — АА, АБ…; после ЯЯ — ААА… |

`appendix.overflow` содержит только `double`; `stop` и `latin` удалены из
реестра, UI и кода. `heading.keep_with_next` (дефолт `true`) — `sticky: true`
у блока заголовка. `match.target` — только `heading`; `paragraph` не
реализуется (отложен с «где…»).

Тесты: `tests/test_g3a_structural.py` (схема, миграция, свои счётчики,
приложения при `heading.numbering=none`, `outlined`/`numbering` в `#outline()`,
`step`/`per_level`, сопоставление, `align`, `around`).

## G3b: подписи и нумерация рисунков и таблиц, нумерованные списки

### Подписи

Рисунок и таблица используют одну схему из шести опций; отдельные шаблоны,
счётчики и показ подписи фильтруются по виду фигуры
(`figure.where(kind: image)` / `figure.where(kind: table)`).

| Опция | Тип | Дефолт | Смысл |
|---|---|---|---|
| `figure.caption_template` | string/null | `null` | Шаблон подписи рисунка |
| `figure.caption_position` | select | `below` | `above` / `below` |
| `figure.caption_align` | select | `center` | `left` / `center` / `right` |
| `figure.caption_separator` | string | `" — "` | Разделитель перед текстом, если в шаблоне нет `{content}` |
| `figure.caption_text_override` | object/null | `null` | Шрифт, кегль, начертание только подписи |
| `figure.caption_around` | object | `{before: [], after: []}` | Вставки до/после текста подписи |
| `table.caption_template` | string/null | `null` | Шаблон подписи таблицы |
| `table.caption_position` | select | `above` | `above` / `below` |
| `table.caption_align` | select | `left` | `left` / `center` / `right` |
| `table.caption_separator` | string | `" — "` | Разделитель перед текстом, если в шаблоне нет `{content}` |
| `table.caption_text_override` | object/null | `null` | Шрифт, кегль, начертание только подписи |
| `table.caption_around` | object | `{before: [], after: []}` | Вставки до/после текста подписи |

Шаблон понимает `{h1}`…`{h6}`, `{n}` и `{content}`. `{n}` — номер внутри
раздела; `{h1}` — номер раздела, а внутри приложения — буква приложения
(`Рисунок А.1`). Счётчики раздельные: `figure-h1..h6`/`figure-n` и
`table-h1..h6`/`table-n`; на заголовке уровня 1 сбрасываются `n` и более
глубокие уровни, при начале приложения — все счётчики обоих видов. Поэтому
рисунок и таблица в одной главе независимо получают `.1`, а после перехода
к следующей главе или приложению нумерация начинается заново.

Если `table.caption_template = null`, подпись таблицы выводится только своим
текстом: английское `Table 1` в подписи не появляется. Нативная нумерация
таблицы (`numbering: "1"`) при этом сохраняется, чтобы компилировались ссылки
`@tbl`; она не попадает в подпись. Если `figure.caption_template = null`,
рисунок сохраняет прежнее поведение Typst (`Figure 1: …`), но
`caption_align`, `caption_around` и `caption_text_override` применяются к
нативной подписи: она оборачивается в `block(width: 100%, align(...))`, поэтому
выравнивание меняет x0 подписи, а не только содержимое.

`caption_align` действует одинаково для рисунка и таблицы, с шаблоном и без
него: выравнивание задаётся внешним блоком шириной 100 %, а не `align` вокруг
содержимого естественной ширины. Тесты `test_figure_caption_align_render` и
`test_table_caption_align_render` проверяют x0 для `left`/`center`/`right` в
обоих режимах шаблона.

`caption_around` применяется внутри подписи: вставки `before` идут перед
текстом, `after` — после; столкновения для подписи не настраиваются (это не
элемент верхнего уровня тела). Пустой `caption_around` не меняет вывод.
Типы `blank`, `text`, `line`, `pagebreak` проверяются тестами
`test_*_caption_around_render`, в том числе при `caption_template = null`.
Поскольку Typst запрещает `pagebreak` внутри контейнера figure, разрывы из
`caption_around` выносятся непосредственно перед/после figure; остальные
вставки остаются внутри подписи.
`caption_text_override` задаёт те же поля, что обычный `text_override`.

### Нумерованные списки

| Опция | Тип | Дефолт | Смысл |
|---|---|---|---|
| `numbered_list.level_formats` | list объектов `{format}` | `[]` | Формат маркера по уровням; пусто — общий `numbered_list.numbering` |
| `numbered_list.alphabet` | select | `ru_sfu` | Алфавит для `{letter}`: русский по СТУ (25 букв) или латинский |
| `numbered_list.wrap_mode` | select | `left_margin` | `left_margin` / `body_text` |

`level_formats` — порядок уровней. В строке формата поддерживаются `{n}`
(номер текущего уровня), `{letter}` (буква из `alphabet`) и обычный шаблон
Typst (`1)`, `1.`). Если элементов меньше глубины списка, повторяется
последний формат; более глубокий уровень проверяется тестом
`test_numbered_list_level_format_repeat_render`. Пустой список сохраняет
прежний `numbered_list.numbering`. `numbered_list.full` добавляет номера
предков в начало; тест — `test_numbered_list_full_render`. Алфавит `ru_sfu` —
строчные буквы без Ё, З, Й, О, Ч, Ь, Ы, Ъ; `latin` — `a`…`z`; после последней
буквы используется удвоение, без падения компиляции. Латинский алфавит
проверяется тестом `test_numbered_list_alphabet_latin_render`.

Нумерованный список рисуется собственным `show enum` (`fd.list-render`), а не
штатным `enum`: маркер ставится через `place`, тело абзаца получает
`par(first-line-indent: marker_width + body_indent, all: true)`. Поэтому
`wrap_mode = left_margin` действительно начинает перенесённые строки верхнего
уровня у левого поля страницы. `body_indent` — расстояние между маркером и
текстом первой строки. `body_text` оставляет продолжение на уровне текста
первой строки (висячий отступ). Точное совпадение x0 продолжения с левым полем
проверяет `test_numbered_list_wrap_mode_render` (допуск 0,8 pt).

Вложенные списки используют `fd.list-body-offset-state`: в `left_margin`
следующий уровень начинается от текста родителя (`marker_width + body_indent`),
в `body_text` — от уже сдвинутого тела родителя. Тест
`test_numbered_list_nested_indent_render` проверяет оба режима по x0 маркеров и
текста на трёх уровнях.

Все четыре значения `numbered_list.number_align` (`start`/`end` +
`top`/`bottom`) работают. Вертикальная часть передаётся в `place`,
горизонтальная — в `align` колонки маркера. При `bottom` +
`wrap_mode = left_margin` маркер сдвигается в поле страницы на
`marker_width + body_indent`, чтобы не накладываться на последнюю строку,
которая начинается у левого поля; текст продолжения не сдвигается. Тест
`test_numbered_list_number_align_render` проверяет все четыре значения, тест
`test_numbered_list_number_align_bottom_left_margin_no_overlap_render` —
отсутствие пересечения для `end+bottom` и `start+bottom`.

Интервалы: `spacing = auto` даёт `line-pitch` независимо от `tight`;
`spacing = tight` — ровно `tight_spacing`; `spacing = loose` — ровно
`loose_spacing`. Тесты `test_numbered_list_spacing_render` и
`test_numbered_list_tight_loose_spacing_values_render` проверяют PDF-координаты
и изменение обоих значений. Опции `numbered_list.left_margin_offset` больше
нет; B-10a–B-10d закрыты.

### Значения для seed G6 (профили не создаются)

Для будущих профилей курсовых и ВКР в seed G6 используются только значения:

| Опция | Курсовая / ВКР |
|---|---|
| `figure.caption_template` | `Рисунок {h1}.{n} — {content}` |
| `figure.caption_position` | `below` |
| `figure.caption_align` | `center` |
| `table.caption_template` | `Таблица {h1}.{n} — {content}` |
| `table.caption_position` | `above` |
| `table.caption_align` | `left` |
| `numbered_list.level_formats` | `[{format: "1."}, {format: "а)"}]` |

Профили «Курсовая» и «ВКР» в G3b не создаются и не копируются.

## G4: таблицы и оглавление

### Таблицы

| Опция | Тип | Дефолт | Смысл |
|---|---|---|---|
| `table.border_top` | boolean | `true` | Верхняя внешняя граница |
| `table.border_bottom` | boolean | `true` | Нижняя внешняя граница |
| `table.border_left` | boolean | `true` | Левая внешняя граница |
| `table.border_right` | boolean | `true` | Правая внешняя граница |
| `table.border_inside_horizontal` | boolean | `true` | Горизонтальные линии между строками |
| `table.border_inside_vertical` | boolean | `true` | Вертикальные линии между столбцами |
| `table.header_double_line` | boolean | `false` | Двойная линия под шапкой |
| `table.header_double_stroke` | number, mm | `0.2645833333` | Толщина линий двойной шапки (0,75 pt) |
| `table.header_double_gap` | number, mm | `0.5` | Зазор между линиями двойной шапки |
| `table.repeat_header` | boolean | `true` | Повторять шапку на страницах продолжения |
| `table.italic_letters` | boolean | `false` | Курсив для ячейки ровно из одной латинской/греческой буквы |
| `table.continuation_label` | boolean | `false` | Метки «Продолжение/Окончание таблицы N» |
| `table.continuation_template` | string | `"Продолжение таблицы {n}"` | Текст метки на средней странице |
| `table.final_template` | string | `"Окончание таблицы {n}"` | Текст метки на последней странице |

Толщина обычной сетки остаётся в `table.stroke`, отступы ячеек — в
`table.inset`, кегль ячеек — в `table.text_override.font_size`.
`fd.table-stroke` строит функцию `stroke` по координатам ячейки, поэтому
внешние и внутренние линии включаются независимо. `show table` пересобирает
таблицу с этой функцией; при двойной шапке в `table.header` добавляются две
линии и зазор, а служебные строки учитываются в индексах `stroke`. Явные
`table.hline` из Pandoc скрываются только когда сетка рисуется целиком
(двойная шапка или выключенные внутренние горизонтали).

`repeat_header = false` пересобирает `table.header(repeat: false)`. Таблица
внутри `figure` делается разрывной через
`show figure.where(kind: table): set block(breakable: true)`; без этого
длинная таблица не переходит на следующую страницу.

Метки продолжения: вокруг figure таблицы ставятся `metadata(number)` с
метками `<fd-table-start>`/`<fd-table-end>`, диапазон читается в
`page.header` через `query`. Номер берётся из счётчиков подписи таблицы
(`{h1}.{n}`, `{h1}.{h2}.{n}` или `{n}`) и подставляется в шаблон `{n}`.
Тесты: `test_g4_table_borders_render`,
`test_g4_table_double_header_render`, `test_g4_table_repeat_header_render`,
`test_g4_table_inset_and_font_render`,
`test_g4_table_italic_letters_render`,
`test_g4_table_continuation_label_render`.

### Оглавление

| Опция | Тип | Дефолт | Смысл |
|---|---|---|---|
| `outline.entry_case` | select | `none` | Регистр записей: `none` / `upper` / `lower` / `first_upper` |
| `outline.omit_when_pages_lte` | integer | `0` | Не выводить оглавление при числе страниц ≤ N; 0 — выключено |
| `outline.appendix_grouping` | boolean | `true` | Сворачивать подряд идущие приложения в одну запись |
| `outline.appendix_min_group` | integer | `3` | Минимум приложений для групповой записи |
| `outline.appendix_group_template` | string | `"Приложения {first}–{last}"` | Шаблон групповой записи |

Глубина, `step`/`per_level` и отступы по уровням остаются из G3a
(`outline.depth`, `outline.indent_mode`, `outline.indent_mm`,
`outline.indent_per_level`) и в G4 не переделывались.

`fd.outline-entry` заменяет запись `outline.entry` только при выбранном
регистре или группировке. `first_upper` рекурсивно обрабатывает текстовые узлы
и сохраняет `strong`/`emph`; `content-text` извлекает текст из форматированных
заголовков. Номер страницы записи форматируется тем же `page.numbering`
(`outline-page` → `page-number`), поэтому при `page.numbering = "I"` запись
показывает `II`, а не `2`; total передаётся только для шаблона с `/`.
Запись заголовка всегда строится своя, в том числе при `entry_case = none`:
стандартная запись Typst не учитывает `numbering_start`/`numbering_skip_first`.
`page-number` принимает total необязательным rest-аргументом, потому что
стандартная запись Typst вызывает функцию номера страницы только с текущим
номером.
Группировка использует `metadata` в заголовке приложения
(`fd-appendix-kind`, `fd-appendix-letter`) и подзаголовка, а не текст
«Приложение…». Поэтому она работает при `appendix.bold = true` и при
пользовательском `appendix.template`; отдельные записи и подзаголовки
скрываются, первая запись выводится как `Приложения А–В` с диапазоном
страниц в формате `page.numbering`. Заполнитель — фиксированные точки
(`repeat[.]`); по OWNER_DECISIONS 9 он не настраивается. Пропуск оглавления
проверяет `counter(page).final().first()`.

Тесты: `test_g4_toc_entry_case_render`,
`test_g4_toc_entry_case_formatted_render`, `test_g4_toc_fill_render`,
`test_g4_toc_skip_render`, `test_g4_toc_appendix_grouping_render`,
`test_g4_toc_appendix_grouping_default_on_render`,
`test_g4_toc_appendix_grouping_bold_render`,
`test_g4_toc_appendix_grouping_custom_template_render`,
`test_g4_toc_appendix_grouping_roman_pages_render`,
`test_g4_toc_roman_page_numbers_render`,
`test_g4_toc_numbering_start_and_skip_render`,
`test_g4_toc_grouping_numbering_start_and_skip_render`,
`test_g4_toc_appendix_group_minimum_render`.

## G5: формулы и подпись формулы

### Опции формулы

| Опция | Тип | Дефолт | Смысл |
|---|---|---|---|
| `equation.align` | select | `auto` | `auto` сохраняет центрирование Typst; `left`/`center`/`right` задают выравнивание формулы |
| `equation.numbering_enabled` | boolean | `false` | Включает автоматическую нумерацию формул |
| `equation.numbering_template` | string | `"({n})"` | Шаблон номера: `{n}`, `{h1}`…`{h6}` |
| `equation.caption_template` | string/null | `null` | Шаблон подписи формулы: `{n}`, `{h1}`…`{h6}`, `{content}` |
| `equation.caption_position` | select | `below` | `above` / `below` |
| `equation.caption_align` | select | `center` | `left` / `center` / `right` |
| `equation.caption_separator` | string | `" — "` | Разделитель перед текстом, если в шаблоне нет `{content}` |
| `equation.caption_text_override` | object/null | `null` | Шрифт, кегль и начертание только подписи |
| `equation.caption_around` | object | `{before: [], after: []}` | Вставки до/после подписи |

`equation.body_indent`, `equation.spacing_before/after` и
`equation.text_override` остаются прежними. Нумерация по умолчанию выключена,
чтобы существующие документы не менялись; для профиля СТУ G6 включает её и
задаёт шаблон `({h1}.{n})`.

### Подпись и нумерация

Pandoc 3.9 превращает `$$…$$` + строку `: Текст` в `terms.item`, где `term` —
`math.equation`. `fd` перехватывает только такие `terms.item`; обычные
definition lists возвращаются без изменений. Терм рендерится как встроенная
формула (`block: false`), чтобы блок-формула не получила второй номер.

Формула с подписью нумеруется отдельным счётчиком `formula-n`, главы —
`formula-h1…h6`. Номер выводится справа (grid `1fr + auto`), подпись — по
`caption_position`/`caption_align`; `caption_around` и `caption_text_override`
работают так же, как у таблиц и рисунков. Шаблон номера и шаблон подписи
понимают `{n}`, `{h1}`…`{h6}`, подпись — ещё `{content}`; в подписи `{n}` —
уже готовый номер по `numbering_template`, включая скобки и раздел. Сброс формул по
главам выполняется, когда шаблон номера содержит `{hN}`; в приложении
используется буква приложения, например `(А.1)`.

Формула без подписи — обычный block `math.equation`; при включённой нумерации
номер выводится справа, при выключенной вывод остаётся прежним. Формулы в
`terms.item` не проходят через block-обработчик, поэтому двойной нумерации нет.

### «где…»

`structural.entities` расширены целью `paragraph` и режимом `starts_with`.
Правило применяется к абзацу по началу текста, без нового синтаксиса Markdown:
align, case, bold, text_override и around; отступ первой строки у такого
абзаца сбрасывается в 0. Тест —
`test_g5_formula_explanation_paragraph_render`.

### Тесты и отложенное

Тесты: `tests/test_g5_formulas.py` — схема, генерация, подпись, обычные
definition lists, нумерация global/section/appendix/disabled, номер справа,
выравнивание, позиция/выравнивание/разделитель/стиль/окружение подписи,
объяснение «где…».

`formula.line_continuation` отложен: автоматический перенос по знаку операции
не реализован, остаётся ручной разрыв `\`; `fd.eq-break` не добавлялся.
`formula.cross_reference` отложен: ссылки/метки формул требуют нового
синтаксиса Markdown.
