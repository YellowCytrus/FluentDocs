import { describe, expect, it } from 'vitest';
import type { JsonValue, RegistryOption } from '../types/registry';
import { buildRuleTabs, getPath, setPath, textOverrideDefaults } from './registryRules';

function option(
  id: string,
  path: string[],
  tab: string,
  order: number,
  overrides: Partial<RegistryOption> = {},
): RegistryOption {
  return {
    id,
    group: path[0]!,
    group_label: 'Абзац',
    applies_to: [path[0]!],
    type: 'number',
    default: 0,
    path,
    ui: { control: 'number', label: id, tab, order },
    rationale: '',
    source: '',
    unit: 'mm',
    allowed_units: ['mm'],
    min: 0,
    max: 100,
    step: 0.1,
    enum: [],
    depends_on: [],
    nullable: false,
    ...overrides,
  };
}

describe('registry rules', () => {
  it('groups options into tabs and sections, heading levels separately', () => {
    const tabs = buildRuleTabs([
      option('page.margin_left', ['page', 'margin_left'], 'Страница', 0),
      option('outline.depth', ['outline', 'depth'], 'Оглавление', 0),
      option('heading_levels.1.break_before', ['heading_levels', '1', 'break_before'], 'Заголовки', 0),
      option('heading_levels.2.break_before', ['heading_levels', '2', 'break_before'], 'Заголовки', 0),
      option('par.text_override.font_size', ['par', 'text_override', 'font_size'], 'Абзац', 100),
    ]);

    expect(tabs.map((tab) => tab.label)).toEqual([
      'Страница',
      'Оглавление',
      'Заголовки',
      'Абзац',
    ]);
    const heading = tabs.find((tab) => tab.label === 'Заголовки');
    expect(heading?.sections.map((section) => section.label)).toEqual([
      'Заголовок 1',
      'Заголовок 2',
    ]);
    const par = tabs.find((tab) => tab.label === 'Абзац');
    expect(par?.sections[0]?.textOverridePath).toEqual(['par', 'text_override']);
  });

  it('reads and immutably writes nested values', () => {
    const values: Record<string, JsonValue> = {
      par: { spacing: 4, text_override: null },
    };
    expect(getPath(values, ['par', 'spacing'])).toBe(4);
    expect(getPath(values, ['par', 'text_override', 'font'])).toBeUndefined();

    const next = setPath(values, ['par', 'text_override', 'font'], 'DejaVu Sans');
    expect(getPath(next, ['par', 'text_override', 'font'])).toBe('DejaVu Sans');
    expect(getPath(values, ['par', 'text_override', 'font'])).toBeUndefined();

    const cleared = setPath(next, ['par', 'text_override'], null);
    expect(getPath(cleared, ['par', 'text_override'])).toBeNull();
  });

  it('builds default text override object from option defaults', () => {
    const section = buildRuleTabs([
      option('par.text_override.font_size', ['par', 'text_override', 'font_size'], 'Абзац', 100, {
        default: 12,
      }),
      option('par.text_override.font', ['par', 'text_override', 'font'], 'Абзац', 101, {
        type: 'string',
        default: 'Merriweather',
        unit: null,
      }),
    ])[0]!.sections[0]!;
    expect(textOverrideDefaults(section)).toEqual({
      font_size: 12,
      font: 'Merriweather',
    });
  });
});
