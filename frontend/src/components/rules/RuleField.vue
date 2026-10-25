<script setup lang="ts">
import { computed, ref } from 'vue';
import type { JsonValue, RegistryOption } from '../../types/registry';
import type { Context, Unit } from '../../utils/unitConversion';
import { fromMm, toMm } from '../../utils/unitConversion';
import UnitInput from '../styles/UnitInput.vue';

const props = defineProps<{
  option: RegistryOption;
  modelValue: JsonValue | undefined;
  context?: Context;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: JsonValue];
}>();

const LENGTH_UNITS = new Set(['mm', 'cm', 'in', 'pt', 'em']);
const sourceUnit = computed<Unit | null>(() => {
  if (!props.option.unit) return null;
  return LENGTH_UNITS.has(props.option.unit) ? (props.option.unit as Unit) : null;
});
const allowedUnits = computed<Unit[]>(() => {
  const units = props.option.allowed_units.filter((unit): unit is Unit =>
    LENGTH_UNITS.has(unit),
  );
  return units.length ? units : ['mm', 'cm', 'in', 'pt'];
});
const displayUnit = ref<Unit | null>(null);
const activeUnit = computed<Unit>(
  () => displayUnit.value ?? allowedUnits.value[0] ?? 'mm',
);

const numericValue = computed(() => {
  const value = Number(props.modelValue);
  return Number.isFinite(value) ? value : 0;
});

const valueMm = computed(() => {
  if (!sourceUnit.value) return numericValue.value;
  try {
    return toMm(numericValue.value, sourceUnit.value, props.context);
  } catch {
    return 0;
  }
});

function convertBound(value: number | null): number | undefined {
  if (value == null || !sourceUnit.value) return value ?? undefined;
  try {
    return toMm(value, sourceUnit.value, props.context);
  } catch {
    return undefined;
  }
}

const minMm = computed(() => convertBound(props.option.min));
const maxMm = computed(() => convertBound(props.option.max));
const stepMm = computed(() => convertBound(props.option.step));

function commitMm(valueMmNext: number) {
  if (!sourceUnit.value) {
    emit('update:modelValue', valueMmNext);
    return;
  }
  try {
    emit('update:modelValue', fromMm(valueMmNext, sourceUnit.value, props.context));
  } catch {
    // Без контекста em значение не пересчитать: оставляем прежним.
  }
}

function emitNumeric(raw: string) {
  const value = Number(raw);
  if (!Number.isFinite(value)) return;
  emit('update:modelValue', props.option.type === 'integer' ? Math.round(value) : value);
}

function emitString(raw: string) {
  emit('update:modelValue', raw === '' && props.option.nullable ? null : raw);
}

const markers = computed<string[]>(() => {
  const value = props.modelValue;
  if (Array.isArray(value)) return value as string[];
  const fallback = Array.isArray(props.option.default) ? (props.option.default as string[]) : [];
  return [...fallback, '', '', ''].slice(0, 3);
});

function updateMarker(index: number, value: string) {
  const next = [...markers.value];
  next[index] = value;
  emit('update:modelValue', next);
}
</script>

<template>
  <div class="rule-field">
    <label class="rule-label" :title="option.rationale">
      {{ option.ui.label }}
      <span v-if="option.unit && !sourceUnit" class="rule-unit-hint">{{ option.unit }}</span>
    </label>

    <UnitInput
      v-if="(option.type === 'number' || option.type === 'integer') && sourceUnit"
      :value-mm="valueMm"
      :unit="activeUnit"
      :allowed-units="allowedUnits"
      :min-mm="minMm"
      :max-mm="maxMm"
      :step-mm="stepMm"
      :context="context"
      @preview="commitMm"
      @commit="commitMm"
      @unit-change="displayUnit = $event"
    />

    <div v-else-if="option.type === 'number' || option.type === 'integer'" class="rule-number">
      <input
        type="range"
        :min="option.min ?? 0"
        :max="option.max ?? 100"
        :step="option.step ?? 1"
        :value="numericValue"
        class="rule-slider"
        @input="emitNumeric(($event.target as HTMLInputElement).value)"
      />
      <input
        type="number"
        :min="option.min ?? undefined"
        :max="option.max ?? undefined"
        :step="option.step ?? 1"
        :value="numericValue"
        class="rule-input"
        @input="emitNumeric(($event.target as HTMLInputElement).value)"
      />
    </div>

    <div v-else-if="option.type === 'boolean'" class="rule-toggle-wrap">
      <button
        type="button"
        class="rule-toggle"
        :class="{ active: !!modelValue }"
        @click="emit('update:modelValue', !modelValue)"
      >
        <span class="rule-thumb" />
      </button>
      <span class="rule-toggle-label">{{ modelValue ? 'Да' : 'Нет' }}</span>
    </div>

    <input
      v-else-if="option.type === 'string'"
      type="text"
      :value="modelValue ?? ''"
      class="rule-input rule-text"
      @input="emitString(($event.target as HTMLInputElement).value)"
    />

    <select
      v-else-if="option.type === 'select'"
      class="rule-input rule-select"
      :value="modelValue ?? ''"
      @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="item in option.ui.options ?? []" :key="item.value" :value="item.value">
        {{ item.label }}
      </option>
    </select>

    <div v-else-if="option.type === 'markers'" class="rule-markers">
      <input
        v-for="(_, index) in 3"
        :key="index"
        type="text"
        :value="markers[index]"
        class="rule-input"
        :placeholder="`Уровень ${index + 1}`"
        @input="updateMarker(index, ($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<style scoped>
.rule-field {
  display: grid;
  grid-template-columns: minmax(180px, 260px) 1fr;
  gap: 0.75rem;
  align-items: start;
  padding: 0.45rem 0;
  border-bottom: 1px solid #27272a;
}

.rule-label {
  color: #d4d4d8;
  font-size: 0.82rem;
  padding-top: 0.3rem;
}

.rule-unit-hint {
  color: #71717a;
  margin-left: 0.25rem;
}

.rule-number,
.rule-toggle-wrap,
.rule-markers {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rule-slider {
  flex: 1;
  accent-color: #3b82f6;
}

.rule-input {
  background: #3f3f46;
  border: 1px solid #52525b;
  border-radius: 0.375rem;
  color: #fafafa;
  padding: 0.3rem 0.5rem;
  font-size: 0.82rem;
}

.rule-text,
.rule-select {
  max-width: 420px;
  width: 100%;
}

.rule-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.rule-toggle {
  position: relative;
  width: 2.5rem;
  height: 1.375rem;
  background: #3f3f46;
  border: 1px solid #52525b;
  border-radius: 9999px;
  cursor: pointer;
  padding: 0;
}

.rule-toggle.active {
  background: #3b82f6;
  border-color: #3b82f6;
}

.rule-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 1rem;
  height: 1rem;
  background: #fafafa;
  border-radius: 9999px;
  transition: transform 0.2s;
}

.rule-toggle.active .rule-thumb {
  transform: translateX(1.1rem);
}

.rule-toggle-label {
  font-size: 0.8rem;
  color: #a1a1aa;
}

.rule-markers {
  flex-direction: column;
  align-items: stretch;
  max-width: 420px;
}
</style>
