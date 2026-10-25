<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue';
import ProfileSidebar from '../components/styles/ProfileSidebar.vue';
import RuleField from '../components/rules/RuleField.vue';
import { useProfilesStore } from '../stores/profiles';
import { API_BASE } from '../config';
import type {
  JsonValue,
  ProfileOptions,
  RegistryOption,
  RegistrySchema,
} from '../types/registry';
import type { RuleSection, RuleTab } from '../utils/registryRules';
import {
  buildRuleTabs,
  getPath,
  setPath,
  textOverrideDefaults,
} from '../utils/registryRules';
import { ptToMm } from '../utils/unitConversion';

const profilesStore = useProfilesStore();
const schema = shallowRef<RegistryOption[]>([]);
const values = shallowRef<Record<string, JsonValue>>({});
const schemaVersion = ref(1);
const activeTab = ref('');
const loading = ref(false);
const saveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle');

const tabs = computed<RuleTab[]>(() => buildRuleTabs(schema.value));
const activeSections = computed(
  () => tabs.value.find((tab) => tab.label === activeTab.value)?.sections ?? [],
);
const context = computed(() => {
  const document = values.value.document;
  const fontSize =
    document != null && typeof document === 'object' && !Array.isArray(document)
      ? Number(document.font_size ?? 12)
      : 12;
  return { fontSizeMm: ptToMm(fontSize) };
});

let saveTimer: ReturnType<typeof setTimeout> | null = null;
let statusTimer: ReturnType<typeof setTimeout> | null = null;

function setStatus(status: 'idle' | 'saving' | 'saved' | 'error') {
  saveStatus.value = status;
  if (statusTimer) clearTimeout(statusTimer);
  if (status === 'saved' || status === 'error') {
    statusTimer = setTimeout(() => {
      saveStatus.value = 'idle';
    }, 2000);
  }
}

async function loadRules(profileId: number) {
  loading.value = true;
  try {
    const [schemaResponse, valuesResponse] = await Promise.all([
      fetch(`${API_BASE}/registry/options`),
      fetch(`${API_BASE}/profiles/${profileId}/options`),
    ]);
    if (!schemaResponse.ok || !valuesResponse.ok) throw new Error('Не удалось загрузить правила');
    const schemaBody = (await schemaResponse.json()) as RegistrySchema;
    const valuesBody = (await valuesResponse.json()) as ProfileOptions;
    schema.value = schemaBody.options;
    values.value = valuesBody.values;
    schemaVersion.value = valuesBody.schema_version;
    if (!tabs.value.some((tab) => tab.label === activeTab.value)) {
      activeTab.value = tabs.value[0]?.label ?? '';
    }
  } catch {
    setStatus('error');
  } finally {
    loading.value = false;
  }
}

async function persist() {
  const profileId = profilesStore.currentId;
  if (profileId == null) return;
  setStatus('saving');
  try {
    const response = await fetch(`${API_BASE}/profiles/${profileId}/options`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        schema_version: schemaVersion.value,
        values: values.value,
      }),
    });
    if (!response.ok) throw new Error('save failed');
    setStatus('saved');
    profilesStore.invalidateCache(profileId);
  } catch {
    setStatus('error');
  }
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(persist, 400);
}

function onFieldChange(option: RegistryOption, value: JsonValue) {
  values.value = setPath(values.value, option.path, value);
  scheduleSave();
}

function overrideEnabled(section: RuleSection): boolean {
  if (!section.textOverridePath) return false;
  return getPath(values.value, section.textOverridePath) != null;
}

function toggleOverride(section: RuleSection) {
  if (!section.textOverridePath) return;
  const next = overrideEnabled(section) ? null : textOverrideDefaults(section);
  values.value = setPath(values.value, section.textOverridePath, next);
  scheduleSave();
}

function fieldValue(option: RegistryOption): JsonValue | undefined {
  return getPath(values.value, option.path);
}

onMounted(() => {
  void profilesStore.fetchProfiles();
});

watch(
  () => profilesStore.currentId,
  (profileId) => {
    if (saveTimer) clearTimeout(saveTimer);
    if (profileId != null) void loadRules(profileId);
  },
  { immediate: true },
);
</script>

<template>
  <div class="rules-page">
    <ProfileSidebar />

    <main class="rules-main">
      <header class="rules-header">
        <div>
          <h1 class="rules-title">Правила оформления</h1>
          <p class="rules-subtitle">
            Форма строится по реестру опций; сохранение — в JSONB профиля.
          </p>
        </div>
        <div class="rules-status">
          <span v-if="loading">Загрузка...</span>
          <span v-else-if="saveStatus === 'saving'" class="saving">Сохранение...</span>
          <span v-else-if="saveStatus === 'saved'" class="saved">Сохранено</span>
          <span v-else-if="saveStatus === 'error'" class="error">Ошибка</span>
        </div>
      </header>

      <div v-if="profilesStore.currentId == null" class="rules-empty">
        Выберите или создайте профиль
      </div>

      <template v-else>
        <nav class="rules-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.label"
            type="button"
            class="rules-tab"
            :class="{ active: activeTab === tab.label }"
            @click="activeTab = tab.label"
          >
            {{ tab.label }}
          </button>
        </nav>

        <div class="rules-content">
          <section v-for="section in activeSections" :key="section.id" class="rules-section">
            <div class="section-head">
              <h2 class="section-title">{{ section.label }}</h2>
              <button
                v-if="section.textOverridePath"
                type="button"
                class="override-toggle"
                :class="{ active: overrideEnabled(section) }"
                @click="toggleOverride(section)"
              >
                {{ overrideEnabled(section) ? 'Свой стиль включён' : 'Задать свой стиль' }}
              </button>
            </div>

            <template v-if="!section.textOverridePath || overrideEnabled(section)">
              <RuleField
                v-for="option in section.options"
                :key="option.id"
                :option="option"
                :model-value="fieldValue(option)"
                :context="context"
                @update:model-value="onFieldChange(option, $event)"
              />
            </template>
          </section>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.rules-page {
  display: flex;
  height: 100%;
  background: #09090b;
  color: #fafafa;
}

.rules-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.rules-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #27272a;
  background: #18181b;
}

.rules-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.rules-subtitle {
  margin: 0.2rem 0 0;
  color: #71717a;
  font-size: 0.78rem;
}

.rules-status {
  font-size: 0.75rem;
  white-space: nowrap;
}

.saving {
  color: #facc15;
}

.saved {
  color: #22c55e;
}

.error {
  color: #ef4444;
}

.rules-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  padding: 0.75rem 1.25rem;
  background: #27272a;
  border-bottom: 1px solid #3f3f46;
}

.rules-tab {
  padding: 0.4rem 0.9rem;
  border-radius: 9999px;
  border: 1px solid #3f3f46;
  background: transparent;
  color: #a1a1aa;
  font-size: 0.82rem;
  cursor: pointer;
}

.rules-tab.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.rules-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 1.25rem 2rem;
}

.rules-section {
  margin-top: 1rem;
  padding-bottom: 0.5rem;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.section-title {
  margin: 0;
  font-size: 0.9rem;
  color: #fafafa;
}

.override-toggle {
  border: 1px solid #3f3f46;
  background: #18181b;
  color: #a1a1aa;
  border-radius: 0.375rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.override-toggle.active {
  border-color: #3b82f6;
  color: #60a5fa;
}

.rules-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #52525b;
  font-size: 0.9rem;
}
</style>
