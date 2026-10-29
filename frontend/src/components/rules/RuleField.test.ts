import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import type { JsonValue, RegistryOption } from '../../types/registry';
import RuleField from './RuleField.vue';

function field(
  id: string,
  key: string,
  type: RegistryOption['type'],
  overrides: Partial<RegistryOption> = {},
): RegistryOption {
  return {
    id,
    group: 'around',
    group_label: 'Окружение',
    applies_to: ['around'],
    type,
    default: type === 'string' ? '' : 0,
    path: [key],
    ui: {
      control: type,
      label: key,
      tab: 'Окружение',
      order: 0,
      options:
        type === 'select'
          ? [
              { value: 'blank', label: 'Пустая строка' },
              { value: 'text', label: 'Текст' },
            ]
          : undefined,
    },
    rationale: '',
    source: '',
    unit: null,
    allowed_units: [],
    min: null,
    max: null,
    step: null,
    enum: [],
    depends_on: [],
    nullable: false,
    ...overrides,
  };
}

function listOption(): RegistryOption {
  return field('around.table.after', 'after', 'list', {
    default: [],
    item_fields: [
      field('around.item.type', 'type', 'select', { default: 'blank', required: true }),
      field('around.item.count', 'count', 'integer', { default: 1 }),
      field('around.item.content', 'content', 'string', { default: '', required: true }),
    ],
    item_variants: [
      ['blank', ['count']],
      ['text', ['content']],
    ],
  });
}

describe('RuleField list renderer', () => {
  it('renders variant fields and adds/removes/reorders items', async () => {
    const wrapper = mount(RuleField, {
      props: {
        option: listOption(),
        modelValue: [
          { type: 'blank', count: 1 },
          { type: 'text', content: 'A' },
        ] as JsonValue[],
      },
    });

    expect(wrapper.findAll('.rule-list-item')).toHaveLength(2);
    expect(wrapper.text()).toContain('Элемент 1');
    expect(wrapper.text()).toContain('Элемент 2');

    await wrapper.findAll('.rule-add')[0]!.trigger('click');
    const addedEvents = wrapper.emitted('update:modelValue') as unknown[][] | undefined;
    const added = addedEvents?.[addedEvents.length - 1]?.[0] as JsonValue[];
    expect(added).toHaveLength(3);
    expect(added[2]).toEqual({ type: 'blank', count: 1 });

    const buttons = wrapper.findAll('.rule-list-actions')[0]!.findAll('button');
    const remove = buttons[buttons.length - 1]!;
    await remove.trigger('click');
    const removedEvents = wrapper.emitted('update:modelValue') as unknown[][] | undefined;
    const removed = removedEvents?.[removedEvents.length - 1]?.[0] as JsonValue[];
    expect(removed).toHaveLength(1);
    expect(removed[0]).toEqual({ type: 'text', content: 'A' });

    const down = wrapper.findAll('.rule-list-actions')[0]!.findAll('button')[1]!;
    await down.trigger('click');
    const movedEvents = wrapper.emitted('update:modelValue') as unknown[][] | undefined;
    const moved = movedEvents?.[movedEvents.length - 1]?.[0] as JsonValue[];
    expect(moved[0]).toEqual({ type: 'text', content: 'A' });
  });

  it('switches item fields when the variant changes', async () => {
    const wrapper = mount(RuleField, {
      props: {
        option: listOption(),
        modelValue: [{ type: 'blank', count: 1 }] as JsonValue[],
      },
    });
    const select = wrapper.find('select');
    expect(select.exists()).toBe(true);
    await select.setValue('text');
    const changedEvents = wrapper.emitted('update:modelValue') as unknown[][] | undefined;
    const changed = changedEvents?.[changedEvents.length - 1]?.[0] as JsonValue[];
    expect(changed[0]).toEqual({ type: 'text', content: '' });
  });

  it('hides nested fields whose enabled_when does not match the object', () => {
    const kind = field('structural.entity.numbering.kind', 'kind', 'select', {
      default: 'section',
      ui: {
        control: 'select',
        label: 'kind',
        tab: 'Заголовки',
        order: 0,
        options: [
          { value: 'section', label: 'Обычный' },
          { value: 'appendix', label: 'Приложение' },
        ],
      },
    });
    const mode = field('structural.entity.numbering.mode', 'mode', 'select', {
      default: 'continue',
      enabled_when: { key: 'kind', values: ['section'] },
      ui: {
        control: 'select',
        label: 'mode',
        tab: 'Заголовки',
        order: 1,
        options: [{ value: 'continue', label: 'Продолжать' }],
      },
    });
    const numbering = field('structural.entity.numbering', 'numbering', 'object', {
      default: { kind: 'section', mode: 'continue' },
      fields: [kind, mode],
    });

    const appendixWrapper = mount(RuleField, {
      props: { option: numbering, modelValue: { kind: 'appendix', mode: 'continue' } },
    });
    expect(appendixWrapper.text()).toContain('kind');
    expect(appendixWrapper.text()).not.toContain('mode');

    const sectionWrapper = mount(RuleField, {
      props: { option: numbering, modelValue: { kind: 'section', mode: 'continue' } },
    });
    expect(sectionWrapper.text()).toContain('mode');
  });

  it('renders nested object fields and nullable object toggles', async () => {
    const nested = field('around.item.line_spacing', 'line_spacing', 'object', {
      default: { mode: 'multiplier', value: 1 },
      fields: [
        field('around.item.line_spacing.mode', 'mode', 'select', {
          default: 'multiplier',
          ui: {
            control: 'select',
            label: 'Режим',
            tab: 'Окружение',
            order: 0,
            options: [{ value: 'multiplier', label: 'Множитель' }],
          },
        }),
      ],
    });
    const wrapper = mount(RuleField, {
      props: {
        option: field('around.table.after', 'after', 'list', {
          default: [],
          item_fields: [nested],
          item_variants: [['blank', ['line_spacing']]],
        }),
        modelValue: [{ type: 'blank', line_spacing: { mode: 'multiplier', value: 1 } }],
      },
    });
    expect(wrapper.find('select').exists()).toBe(true);

    const nullable = field('around.item.text_override', 'text_override', 'object', {
      default: null,
      nullable: true,
      fields: [field('around.item.text_override.font', 'font', 'string', { default: 'A' })],
    });
    const objectWrapper = mount(RuleField, {
      props: { option: nullable, modelValue: null },
    });
    await objectWrapper.find('.rule-add').trigger('click');
    expect(objectWrapper.emitted('update:modelValue')?.[0]?.[0]).toEqual({
      font: 'A',
    });
  });
});

describe('RuleField beta marker', () => {
  it('shows a beta badge from ui.beta', () => {
    const option = field('structural.entities', 'entities', 'list', {
      default: [],
      ui: {
        control: 'list',
        label: 'Структурные элементы',
        tab: 'Структурные элементы',
        order: 0,
        beta: true,
      },
    });
    const wrapper = mount(RuleField, { props: { option, modelValue: [] } });
    expect(wrapper.find('.rule-beta').exists()).toBe(true);
    expect(wrapper.find('.rule-beta').text()).toBe('beta');
  });
});
