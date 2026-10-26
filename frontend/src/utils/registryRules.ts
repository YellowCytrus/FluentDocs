import type { JsonValue, RegistryOption } from '../types/registry';

export interface RuleSection {
  id: string;
  label: string;
  /** Путь до объекта text_override; null для обычной секции. */
  textOverridePath: string[] | null;
  options: RegistryOption[];
}

export interface RuleTab {
  label: string;
  sections: RuleSection[];
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function getPath(root: JsonValue | undefined, path: string[]): JsonValue | undefined {
  let current: JsonValue | undefined = root;
  for (const key of path) {
    if (current == null || typeof current !== 'object' || Array.isArray(current)) return undefined;
    current = (current as Record<string, JsonValue>)[key];
  }
  return current;
}

export function setPath(
  root: Record<string, JsonValue>,
  path: string[],
  value: JsonValue,
): Record<string, JsonValue> {
  const next = clone(root);
  let current: Record<string, JsonValue> = next;
  for (const key of path.slice(0, -1)) {
    const nested = current[key];
    if (nested == null || typeof nested !== 'object' || Array.isArray(nested)) {
      current[key] = {};
    }
    current = current[key] as Record<string, JsonValue>;
  }
  const last = path[path.length - 1];
  if (!last) return next;
  current[last] = value;
  return next;
}

function baseKey(option: RegistryOption): string {
  if (option.path[0] === 'heading_levels') return `heading_levels.${option.path[1]!}`;
  if (option.path[0] === 'around') return `around.${option.path[1]!}`;
  return option.path[0]!;
}

function sectionLabel(option: RegistryOption, textOverride: boolean): string {
  if (option.path[0] === 'heading_levels') {
    const level = option.path[1]!;
    return textOverride ? `Уровень ${level}: свой стиль текста` : `Заголовок ${level}`;
  }
  if (option.path[0] === 'around') {
    const target = option.ui.section ?? option.path[1]!;
    return `Окружение: ${target}`;
  }
  return textOverride ? `${option.group_label}: свой стиль текста` : option.group_label;
}

function textOverridePath(option: RegistryOption): string[] | null {
  const index = option.path.indexOf('text_override');
  if (index < 0) return null;
  return option.path.slice(0, index + 1);
}

/** Группирует опции в вкладки по ui.tab и секции по элементу/уровню. */
export function buildRuleTabs(options: RegistryOption[]): RuleTab[] {
  const tabs = new Map<string, Map<string, RuleSection>>();
  for (const option of options) {
    const tabLabel = option.ui.tab;
    if (!tabs.has(tabLabel)) tabs.set(tabLabel, new Map());
    const sections = tabs.get(tabLabel)!;
    const toPath = textOverridePath(option);
    const key = toPath ? `${baseKey(option)}.text_override` : baseKey(option);
    if (!sections.has(key)) {
      sections.set(key, {
        id: key,
        label: sectionLabel(option, Boolean(toPath)),
        textOverridePath: toPath,
        options: [],
      });
    }
    sections.get(key)!.options.push(option);
  }

  const result: RuleTab[] = [];
  for (const [label, sections] of tabs) {
    result.push({
      label,
      sections: [...sections.values()].map((section) => ({
        ...section,
        options: [...section.options].sort((a, b) => a.ui.order - b.ui.order),
      })),
    });
  }
  return result;
}

/** Дефолтный объект text_override для секции. */
export function textOverrideDefaults(section: RuleSection): Record<string, JsonValue> {
  const result: Record<string, JsonValue> = {};
  for (const option of section.options) {
    const key = option.path[option.path.length - 1];
    if (key) result[key] = option.default;
  }
  return result;
}

/** Дефолтный объект по вложенной схеме (object). */
export function objectDefaults(fields: RegistryOption[]): Record<string, JsonValue> {
  const result: Record<string, JsonValue> = {};
  for (const field of fields) {
    result[field.path[field.path.length - 1] ?? field.id] = clone(field.default);
  }
  return result;
}

/** Вложенные поля, видимые для выбранного варианта list-элемента. */
export function listItemFields(option: RegistryOption, item: JsonValue): RegistryOption[] {
  const fields = option.item_fields ?? [];
  const variants = option.item_variants ?? [];
  if (!variants.length) return fields;
  const type =
    item != null && typeof item === 'object' && !Array.isArray(item)
      ? (item as Record<string, JsonValue>).type
      : null;
  const variant = variants.find(([value]) => value === type);
  if (!variant) return fields;
  const allowed = new Set(variant[1]);
  return fields.filter(
    (field) =>
      field.path[field.path.length - 1] === 'type' ||
      allowed.has(field.path[field.path.length - 1]!),
  );
}

/** Дефолтный элемент списка для варианта (type). */
export function listItemDefaults(option: RegistryOption, variant: string): Record<string, JsonValue> {
  const fields = option.item_fields ?? [];
  const variants = option.item_variants ?? [];
  const result: Record<string, JsonValue> = { type: variant };
  const match = variants.find(([value]) => value === variant);
  const allowed = new Set(match ? match[1] : fields.map((field) => field.path[field.path.length - 1]!));
  for (const field of fields) {
    const key = field.path[field.path.length - 1] ?? field.id;
    if (key !== 'type' && allowed.has(key)) result[key] = clone(field.default);
  }
  return result;
}

/** Дефолтный первый элемент списка: variant + поля его варианта. */
export function defaultListItem(option: RegistryOption): Record<string, JsonValue> {
  const variants = option.item_variants ?? [];
  if (!variants.length) return objectDefaults(option.item_fields ?? []);
  return listItemDefaults(option, variants[0]![0]);
}

export function addListItem(items: JsonValue[], item: JsonValue): JsonValue[] {
  return [...items, item];
}

export function removeListItem(items: JsonValue[], index: number): JsonValue[] {
  return items.filter((_, current) => current !== index);
}

export function moveListItem(items: JsonValue[], index: number, delta: -1 | 1): JsonValue[] {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  const [item] = next.splice(index, 1);
  next.splice(target, 0, item!);
  return next;
}
