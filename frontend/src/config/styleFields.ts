import type { ElementType } from '../types/api';
import type { Unit } from '../utils/unitConversion';

export interface FieldDef {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'string' | 'select' | 'markers';
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  options?: { value: string; label: string }[];
  placeholder?: string;
  hint?: string;
  allowedUnits?: Unit[];
}

export const UNIT_EXCLUDED_KEYS = new Set(['font_size', 'tracking', 'word_spacing']);
const ABSOLUTE_SOURCE_UNITS = new Set(['mm', 'cm', 'pt', 'em']);
const PERCENT_UNIT = '%';
export const DEFAULT_ALLOWED_UNITS: Unit[] = ['mm', 'cm', 'in', 'em'];

export function isMmConvertibleField(field: FieldDef): boolean {
  if (field.type !== 'number') return false;
  if (UNIT_EXCLUDED_KEYS.has(field.key)) return false;
  if (field.unit === PERCENT_UNIT) return false;
  return typeof field.unit === 'string' && ABSOLUTE_SOURCE_UNITS.has(field.unit);
}

export function getAllowedUnits(field: FieldDef): Unit[] {
  return field.allowedUnits?.length ? field.allowedUnits : DEFAULT_ALLOWED_UNITS;
}

export interface TabLeaf {
  kind: 'leaf';
  label: string;
  elementKey: ElementType;
  fields: FieldDef[];
  /** If true, show "Задать свой стиль для текста" toggle with text override fields */
  hasTextOverride?: boolean;
}

export interface TabGroup {
  kind: 'group';
  label: string;
  children: TabNode[];
}

export type TabNode = TabLeaf | TabGroup;

/** Default text style for title page elements (text, variable). */
export const TITLE_TEXT_DEFAULTS: Record<string, unknown> = {
  font: 'Libertinus Serif',
  font_size: 12,
  weight: 'regular',
  style: 'normal',
  fill: 'black',
  tracking: 0,
  word_spacing: 100,
  lang: 'ru',
  ligatures: true,
  number_type: 'auto',
  number_width: 'auto',
  hyphenate: 'auto',
  align: 'left',
};

/** Alignment options for variable elements in title page. */
export const VARIABLE_ALIGN_OPTIONS: { value: string; label: string }[] = [
  { value: 'left', label: 'По левому краю' },
  { value: 'center', label: 'По центру' },
  { value: 'right', label: 'По правому краю' },
  { value: 'justify', label: 'По ширине' },
];

/** Fields for "Задать свой стиль для текста" - same as document text (without line_spacing) */
export const TEXT_OVERRIDE_FIELDS: FieldDef[] = [
  { key: 'font', label: 'Шрифт', type: 'string' },
  { key: 'font_size', label: 'Размер шрифта', type: 'number', min: 6, max: 72, step: 0.5, unit: 'pt' },
  {
    key: 'weight',
    label: 'Насыщенность',
    type: 'select',
    options: [
      { value: 'thin', label: 'Thin' },
      { value: 'extralight', label: 'Extra Light' },
      { value: 'light', label: 'Light' },
      { value: 'regular', label: 'Regular' },
      { value: 'medium', label: 'Medium' },
      { value: 'semibold', label: 'Semibold' },
      { value: 'bold', label: 'Bold' },
      { value: 'extrabold', label: 'Extra Bold' },
      { value: 'black', label: 'Black' },
    ],
  },
  {
    key: 'style',
    label: 'Начертание',
    type: 'select',
    options: [
      { value: 'normal', label: 'Обычный' },
      { value: 'italic', label: 'Курсив' },
      { value: 'oblique', label: 'Наклонный' },
    ],
  },
  { key: 'fill', label: 'Цвет текста', type: 'string' },
  { key: 'tracking', label: 'Межбуквенный интервал', type: 'number', min: -5, max: 20, step: 0.1, unit: 'pt' },
  { key: 'word_spacing', label: 'Межсловный интервал', type: 'number', min: 0, max: 500, step: 5, unit: '%' },
  { key: 'lang', label: 'Язык', type: 'select', options: [
    { value: 'ru', label: 'Русский' },
    { value: 'en', label: 'English' },
    { value: 'de', label: 'Deutsch' },
    { value: 'fr', label: 'Français' },
    { value: 'es', label: 'Español' },
    { value: 'zh', label: '中文' },
    { value: 'ja', label: '日本語' },
  ] },
  { key: 'ligatures', label: 'Лигатуры', type: 'boolean' },
  { key: 'number_type', label: 'Тип цифр', type: 'select', options: [
    { value: 'auto', label: 'Авто' },
    { value: 'lining', label: 'Маюскульные' },
    { value: 'old-style', label: 'Минускульные' },
  ] },
  { key: 'number_width', label: 'Ширина цифр', type: 'select', options: [
    { value: 'auto', label: 'Авто' },
    { value: 'proportional', label: 'Пропорциональные' },
    { value: 'tabular', label: 'Табличные' },
  ] },
  { key: 'region', label: 'Регион', type: 'string' },
  {
    key: 'hyphenate',
    label: 'Переносы',
    type: 'select',
    options: [
      { value: 'auto', label: 'Авто' },
      { value: 'true', label: 'Да' },
      { value: 'false', label: 'Нет' },
    ],
  },
];

export const STYLE_TAB_TREE: TabNode[] = [
  // ── Страница ──
  {
    kind: 'leaf',
    label: 'Страница',
    elementKey: 'page',
    fields: [
      {
        key: 'paper',
        label: 'Формат бумаги',
        type: 'select',
        options: [
          { value: 'a4', label: 'A4' },
          { value: 'a3', label: 'A3' },
          { value: 'a5', label: 'A5' },
          { value: 'us-letter', label: 'US Letter' },
          { value: 'us-legal', label: 'US Legal' },
          { value: 'us-tabloid', label: 'US Tabloid' },
          { value: 'presentation-16-9', label: '16:9' },
          { value: 'presentation-4-3', label: '4:3' },
        ],
      },
      {
        key: 'flipped',
        label: 'Альбомная ориентация',
        type: 'boolean',
      },
      {
        key: 'margin_top',
        label: 'Поле сверху',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'cm',
      },
      {
        key: 'margin_bottom',
        label: 'Поле снизу',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'cm',
      },
      {
        key: 'margin_left',
        label: 'Поле слева',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'cm',
      },
      {
        key: 'margin_right',
        label: 'Поле справа',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'cm',
      },
      {
        key: 'columns',
        label: 'Колонки',
        type: 'number',
        min: 1,
        max: 10,
        step: 1,
      },
      {
        key: 'numbering',
        label: 'Нумерация страниц',
        type: 'select',
        options: [
          { value: 'none', label: 'Нет' },
          { value: '1', label: '1, 2, 3...' },
          { value: '- 1 -', label: '- 1 -' },
          { value: 'I', label: 'I, II, III...' },
          { value: '1 / 1', label: '1 / N' },
        ],
      },
      {
        key: 'number_align',
        label: 'Позиция номера',
        type: 'select',
        options: [
          { value: 'center+bottom', label: 'Низ по центру' },
          { value: 'right+bottom', label: 'Низ справа' },
          { value: 'left+bottom', label: 'Низ слева' },
          { value: 'center+top', label: 'Верх по центру' },
          { value: 'right+top', label: 'Верх справа' },
        ],
      },
    ],
  },

  // ── Текст (глобальные настройки) ──
  {
    kind: 'leaf',
    label: 'Текст',
    elementKey: 'document',
    fields: [
          {
            key: 'font',
            label: 'Шрифт',
            type: 'string',
          },
          {
            key: 'font_size',
            label: 'Размер шрифта',
            type: 'number',
            min: 6,
            max: 72,
            step: 0.5,
            unit: 'pt',
          },
          {
            key: 'weight',
            label: 'Насыщенность',
            type: 'select',
            options: [
              { value: 'thin', label: 'Thin' },
              { value: 'extralight', label: 'Extra Light' },
              { value: 'light', label: 'Light' },
              { value: 'regular', label: 'Regular' },
              { value: 'medium', label: 'Medium' },
              { value: 'semibold', label: 'Semibold' },
              { value: 'bold', label: 'Bold' },
              { value: 'extrabold', label: 'Extra Bold' },
              { value: 'black', label: 'Black' },
            ],
          },
          {
            key: 'style',
            label: 'Начертание',
            type: 'select',
            options: [
              { value: 'normal', label: 'Обычный' },
              { value: 'italic', label: 'Курсив' },
              { value: 'oblique', label: 'Наклонный' },
            ],
          },
          {
            key: 'fill',
            label: 'Цвет текста',
            type: 'string',
          },
          {
            key: 'line_spacing',
            label: 'Межстрочный интервал',
            type: 'number',
            min: 0.5,
            max: 3,
            step: 0.05,
            unit: 'em',
          },
          {
            key: 'tracking',
            label: 'Межбуквенный интервал',
            type: 'number',
            min: -5,
            max: 20,
            step: 0.1,
            unit: 'pt',
          },
          {
            key: 'word_spacing',
            label: 'Межсловный интервал',
            type: 'number',
            min: 0,
            max: 500,
            step: 5,
            unit: '%',
          },
          {
            key: 'lang',
            label: 'Язык',
            type: 'select',
            options: [
              { value: 'ru', label: 'Русский' },
              { value: 'en', label: 'English' },
              { value: 'de', label: 'Deutsch' },
              { value: 'fr', label: 'Français' },
              { value: 'es', label: 'Español' },
              { value: 'zh', label: '中文' },
              { value: 'ja', label: '日本語' },
            ],
          },
          {
            key: 'ligatures',
            label: 'Лигатуры',
            type: 'boolean',
          },
          {
            key: 'number_type',
            label: 'Тип цифр',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'lining', label: 'Маюскульные' },
              { value: 'old-style', label: 'Минускульные' },
            ],
          },
          {
            key: 'number_width',
            label: 'Ширина цифр',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'proportional', label: 'Пропорциональные' },
              { value: 'tabular', label: 'Табличные' },
            ],
          },
          {
            key: 'justify',
            label: 'По ширине',
            type: 'boolean',
          },
        ],
  },

  // ── Абзац ──
  {
    kind: 'leaf',
    label: 'Абзац',
    elementKey: 'par',
    hasTextOverride: true,
    fields: [
          {
            key: 'spacing',
            label: 'Интервал между абзацами',
            type: 'number',
            min: 0,
            max: 5,
            step: 0.1,
            unit: 'em',
          },
          {
            key: 'first_line_indent',
            label: 'Отступ первой строки',
            type: 'number',
            min: 0,
            max: 5,
            step: 0.1,
            unit: 'em',
          },
      {
        key: 'hanging_indent',
        label: 'Висячий отступ',
        type: 'number',
        min: 0,
        max: 5,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'linebreaks',
            label: 'Разбиение строк',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'simple', label: 'Простой' },
              { value: 'optimized', label: 'Оптимизированный' },
            ],
          },
        ],
  },

  // ── Заголовки ──
  {
    kind: 'group',
    label: 'Заголовки',
    children: [
      {
        kind: 'leaf',
        label: 'Общее',
        elementKey: 'heading',
        fields: [
          {
            key: 'numbering',
            label: 'Нумерация',
            type: 'string',
          },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 1',
        elementKey: 'heading_1',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 2',
        elementKey: 'heading_2',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 3',
        elementKey: 'heading_3',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 4',
        elementKey: 'heading_4',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 5',
        elementKey: 'heading_5',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
      {
        kind: 'leaf',
        label: 'Заголовок 6',
        elementKey: 'heading_6',
        hasTextOverride: true,
        fields: [
          { key: 'break_before', label: 'С новой страницы', type: 'boolean' },
          { key: 'numbering_enabled', label: 'Нумерация', type: 'boolean' },
        ],
      },
    ],
  },

  // ── Списки ──
  {
    kind: 'group',
    label: 'Списки',
    children: [
      {
        kind: 'leaf',
        label: 'Маркированный',
        elementKey: 'bullet_list',
        hasTextOverride: true,
        fields: [
          {
            key: 'tight',
            label: 'Компактный',
            type: 'boolean',
          },
          {
            key: 'marker',
            label: 'Маркеры уровней',
            type: 'markers',
          },
          {
            key: 'indent',
            label: 'Отступ',
            type: 'number',
            min: 0,
            max: 10,
            step: 0.5,
            unit: 'pt',
          },
          {
            key: 'body_indent',
            label: 'Отступ тела',
            type: 'number',
            min: 0,
            max: 5,
            step: 0.1,
            unit: 'em',
          },
          {
            key: 'spacing',
            label: 'Межстрочный интервал',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'tight', label: 'Компактный' },
              { value: 'loose', label: 'Свободный' },
            ],
          },
        ],
      },
      {
        kind: 'leaf',
        label: 'Нумерованный',
        elementKey: 'numbered_list',
        hasTextOverride: true,
        fields: [
          {
            key: 'tight',
            label: 'Компактный',
            type: 'boolean',
          },
          {
            key: 'numbering',
            label: 'Формат нумерации',
            type: 'string',
          },
          {
            key: 'indent',
            label: 'Отступ',
            type: 'number',
            min: 0,
            max: 10,
            step: 0.5,
            unit: 'pt',
          },
          {
            key: 'body_indent',
            label: 'Отступ тела',
            type: 'number',
            min: 0,
            max: 5,
            step: 0.1,
            unit: 'em',
          },
          {
            key: 'spacing',
            label: 'Межстрочный интервал',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'tight', label: 'Компактный' },
              { value: 'loose', label: 'Свободный' },
            ],
          },
          {
            key: 'full',
            label: 'Полная нумерация',
            type: 'boolean',
          },
          {
            key: 'reversed',
            label: 'Обратный порядок',
            type: 'boolean',
          },
          {
            key: 'number_align',
            label: 'Выравнивание номера',
            type: 'select',
            options: [
              { value: 'end+top', label: 'Конец + верх' },
              { value: 'start+top', label: 'Начало + верх' },
              { value: 'end+bottom', label: 'Конец + низ' },
              { value: 'start+bottom', label: 'Начало + низ' },
            ],
          },
        ],
      },
      {
        kind: 'leaf',
        label: 'Определения',
        elementKey: 'terms',
        hasTextOverride: true,
        fields: [
          {
            key: 'tight',
            label: 'Компактный',
            type: 'boolean',
          },
          {
            key: 'indent',
            label: 'Отступ',
            type: 'number',
            min: 0,
            max: 10,
            step: 0.5,
            unit: 'pt',
          },
          {
            key: 'hanging_indent',
            label: 'Висячий отступ',
            type: 'number',
            min: 0,
            max: 5,
            step: 0.1,
            unit: 'em',
          },
          {
            key: 'spacing',
            label: 'Интервал',
            type: 'select',
            options: [
              { value: 'auto', label: 'Авто' },
              { value: 'tight', label: 'Компактный' },
              { value: 'loose', label: 'Свободный' },
            ],
          },
        ],
      },
    ],
  },

  // ── Таблица ──
  {
    kind: 'leaf',
    label: 'Таблица',
    elementKey: 'table',
    hasTextOverride: true,
    fields: [
      {
        key: 'stroke',
        label: 'Толщина линий',
        type: 'number',
        min: 0,
        max: 20,
        step: 0.01,
        unit: 'mm',
        allowedUnits: ['mm', 'cm', 'in', 'pt'],
      },
      {
        key: 'align',
        label: 'Выравнивание',
        type: 'select',
        options: [
          { value: 'auto', label: 'Авто' },
          { value: 'left', label: 'Слева' },
          { value: 'center', label: 'По центру' },
          { value: 'right', label: 'Справа' },
        ],
      },
      {
        key: 'inset',
        label: 'Отступ ячеек',
        type: 'number',
        min: 0,
        max: 100,
        step: 0.05,
        unit: 'mm',
        allowedUnits: ['mm', 'cm', 'in', 'pt'],
      },
      {
        key: 'fill',
        label: 'Заливка',
        type: 'string',
      },
    ],
  },

  // ── Изображение ──
  {
    kind: 'leaf',
    label: 'Изображение',
    elementKey: 'figure',
    hasTextOverride: true,
    fields: [
      {
        key: 'width',
        label: 'Ширина',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'height',
        label: 'Высота',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'fit',
        label: 'Подгонка',
        type: 'select',
        options: [
          { value: 'cover', label: 'Покрытие' },
          { value: 'contain', label: 'Вписать' },
          { value: 'stretch', label: 'Растянуть' },
        ],
      },
      {
        key: 'placement',
        label: 'Размещение',
        type: 'select',
        options: [
          { value: 'none', label: 'В потоке' },
          { value: 'auto', label: 'Авто' },
          { value: 'top', label: 'Вверху' },
          { value: 'bottom', label: 'Внизу' },
        ],
      },
      {
        key: 'gap',
        label: 'Зазор до подписи',
        type: 'number',
        min: 0,
        max: 5,
        step: 0.05,
        unit: 'em',
      },
      {
        key: 'outlined',
        label: 'В списке фигур',
        type: 'boolean',
      },
      {
        key: 'caption_template',
        label: 'Шаблон для подписи',
        type: 'string',
        placeholder: 'Рисунок {h1}.{N} --- {content}',
        hint: 'В шаблоне можно использовать: {h1}–{h6} — номер заголовка уровня 1–6, {N} — номер рисунка, {content} — текст подписи.',
      },
    ],
  },

  // ── Формула ──
  {
    kind: 'leaf',
    label: 'Формула',
    elementKey: 'equation',
    hasTextOverride: true,
    fields: [],
  },

  // ── Цитата ──
  {
    kind: 'leaf',
    label: 'Цитата',
    elementKey: 'quote',
    hasTextOverride: true,
    fields: [
      {
        key: 'indent',
        label: 'Отступ',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'block',
        label: 'Блочная цитата',
        type: 'boolean',
      },
      {
        key: 'quotes',
        label: 'Кавычки',
        type: 'select',
        options: [
          { value: 'auto', label: 'Авто' },
          { value: 'true', label: 'Да' },
          { value: 'false', label: 'Нет' },
        ],
      },
    ],
  },

  // ── Сноска ──
  {
    kind: 'leaf',
    label: 'Сноска',
    elementKey: 'footnote',
    hasTextOverride: true,
    fields: [
      {
        key: 'marker_format',
        label: 'Формат маркера',
        type: 'select',
        options: [
          { value: '1', label: '1, 2, 3...' },
          { value: 'a', label: 'a, b, c...' },
          { value: 'A', label: 'A, B, C...' },
          { value: 'i', label: 'i, ii, iii...' },
          { value: 'I', label: 'I, II, III...' },
          { value: '*', label: '*, **, ***...' },
        ],
      },
      {
        key: 'clearance',
        label: 'Расстояние до сносок',
        type: 'number',
        min: 0,
        max: 5,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'gap',
        label: 'Расстояние между записями',
        type: 'number',
        min: 0,
        max: 5,
        step: 0.1,
        unit: 'em',
      },
      {
        key: 'indent',
        label: 'Отступ записи',
        type: 'number',
        min: 0,
        max: 5,
        step: 0.1,
        unit: 'em',
      },
    ],
  },

  // ── Код ──
  {
    kind: 'leaf',
    label: 'Код',
    elementKey: 'raw',
    hasTextOverride: true,
    fields: [
      {
        key: 'tab_size',
        label: 'Размер табуляции',
        type: 'number',
        min: 1,
        max: 16,
        step: 1,
      },
      {
        key: 'align',
        label: 'Выравнивание',
        type: 'select',
        options: [
          { value: 'start', label: 'По началу' },
          { value: 'center', label: 'По центру' },
          { value: 'end', label: 'По концу' },
        ],
      },
      {
        key: 'theme',
        label: 'Тема подсветки',
        type: 'select',
        options: [
          { value: 'auto', label: 'Авто' },
          { value: 'none', label: 'Без подсветки' },
        ],
      },
    ],
  },

  // ── Оглавление ──
  {
    kind: 'leaf',
    label: 'Оглавление',
    elementKey: 'outline',
    hasTextOverride: true,
    fields: [
      {
        key: 'depth',
        label: 'Глубина',
        type: 'number',
        min: 1,
        max: 10,
        step: 1,
      },
      {
        key: 'indent_mode',
        label: 'Режим отступа вложенности',
        type: 'select',
        options: [
          { value: 'auto', label: 'Авто' },
          { value: 'none', label: 'Без отступа' },
          { value: 'custom', label: 'Свой отступ' },
        ],
      },
      {
        key: 'indent_mm',
        label: 'Свой отступ вложенности',
        type: 'number',
        min: 0,
        max: 100,
        step: 0.1,
        unit: 'mm',
      },
    ],
  },
];

/** Collect all ElementType keys used in the tree (for bulk-loading). */
export function collectElementKeys(nodes: TabNode[]): ElementType[] {
  const keys: ElementType[] = [];
  for (const node of nodes) {
    if (node.kind === 'leaf') {
      keys.push(node.elementKey);
    } else {
      keys.push(...collectElementKeys(node.children));
    }
  }
  return keys;
}
