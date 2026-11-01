<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useProfilesStore } from '../stores/profiles';
import { useEditorStore } from '../stores/editor';
import { API_BASE } from '../config';
import type {
  DocumentStyles,
  DocumentStylesUpdate,
  HeadingStyles,
  TableStyles,
} from '../types/api';

const profilesStore = useProfilesStore();
const editorStore = useEditorStore();

const expandedSection = ref<string | null>('profiles');
const newProfileName = ref('');
const creatingProfile = ref(false);
const createProfileError = ref('');

const currentProfileId = computed(() => profilesStore.currentId);

async function fetchElement<T>(path: string): Promise<T | null> {
  if (!currentProfileId.value) return null;
  const res = await fetch(`${API_BASE}/profiles/${currentProfileId.value}/${path}`);
  if (!res.ok) return null;
  return res.json();
}

const docStyles = ref<DocumentStyles | null>(null);
const headingStyles = ref<HeadingStyles | null>(null);
const tableStyles = ref<TableStyles | null>(null);

watch(
  currentProfileId,
  async (id) => {
    if (!id) return;
    const [doc, head, tbl] = await Promise.all([
      fetchElement<DocumentStyles>('document'),
      fetchElement<HeadingStyles>('heading'),
      fetchElement<TableStyles>('table'),
    ]);
    docStyles.value = doc ?? ({ font_size: 12, line_spacing: 5.08 } as DocumentStyles);
    headingStyles.value = head ?? ({ numbering: '1.1.1' } as HeadingStyles);
    tableStyles.value = tbl ?? ({ stroke: 0.1763888889, align: 'auto', inset: 1.7638888889, fill: 'none', text_override: null } as TableStyles);
  },
  { immediate: true }
);


async function updateDocument(up: DocumentStylesUpdate) {
  if (!currentProfileId.value || !docStyles.value) return;
  const body = { ...docStyles.value, ...up };
  await fetch(`${API_BASE}/profiles/${currentProfileId.value}/document`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  docStyles.value = body;
  profilesStore.invalidateCache(currentProfileId.value);
  await profilesStore.loadProfileStyles(currentProfileId.value);
}

async function updateHeading(up: { numbering?: string }) {
  if (!currentProfileId.value || !headingStyles.value) return;
  const body = { ...headingStyles.value, ...up };
  await fetch(`${API_BASE}/profiles/${currentProfileId.value}/heading`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  headingStyles.value = body;
  profilesStore.invalidateCache(currentProfileId.value);
  await profilesStore.loadProfileStyles(currentProfileId.value);
}

async function updateTable(up: { stroke?: number }) {
  if (!currentProfileId.value || !tableStyles.value) return;
  const body = { ...tableStyles.value, ...up };
  await fetch(`${API_BASE}/profiles/${currentProfileId.value}/table`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  tableStyles.value = body;
  profilesStore.invalidateCache(currentProfileId.value);
  await profilesStore.loadProfileStyles(currentProfileId.value);
}

async function createProfile() {
  const name = newProfileName.value.trim();
  if (!name) return;
  creatingProfile.value = true;
  createProfileError.value = '';
  try {
    const p = await profilesStore.createProfile(name);
    profilesStore.setCurrent(p.id);
    newProfileName.value = '';
  } catch (error) {
    createProfileError.value =
      error instanceof Error ? error.message : 'Не удалось создать профиль';
  } finally {
    creatingProfile.value = false;
  }
}

function toggleSection(s: string) {
  expandedSection.value = expandedSection.value === s ? null : s;
}
</script>

<template>
  <div
    class="right-panel w-[60px] hover:w-[250px] flex flex-col bg-zinc-800 border-l border-zinc-700 transition-all duration-200 ease-out overflow-hidden"
  >
    <div class="p-4 space-y-4 min-w-[250px]">
      <section>
        <button
          type="button"
          class="w-full text-left font-medium flex items-center justify-between py-2"
          @click="toggleSection('profiles')"
        >
          Профили
          <span class="transform transition-transform" :class="expandedSection === 'profiles' ? 'rotate-180' : ''">
            ▼
          </span>
        </button>
        <div v-show="expandedSection === 'profiles'" class="space-y-2 pl-2">
          <select
            :value="profilesStore.currentId"
            class="w-full rounded bg-zinc-700 px-2 py-1 text-sm"
            @change="profilesStore.setCurrent(+(($event.target as HTMLSelectElement).value))"
          >
            <option v-for="p in profilesStore.list" :key="p.id" :value="p.id">
              {{ p.name }}
            </option>
          </select>
          <div class="flex gap-1">
            <input
              v-model="newProfileName"
              type="text"
              placeholder="Имя"
              class="flex-1 rounded bg-zinc-700 px-2 py-1 text-sm"
              @keyup.enter="createProfile"
            />
            <button
              type="button"
              class="px-2 py-1 rounded bg-zinc-600 hover:bg-zinc-500 text-sm disabled:opacity-50"
              :disabled="creatingProfile || !newProfileName.trim()"
              @click="createProfile"
            >
              +
            </button>
          </div>
          <p v-if="createProfileError" class="text-xs text-red-400">
            {{ createProfileError }}
          </p>
        </div>
      </section>

      <section>
        <button
          type="button"
          class="w-full text-left font-medium flex items-center justify-between py-2"
          @click="toggleSection('elements')"
        >
          Элементы
          <span class="transform transition-transform" :class="expandedSection === 'elements' ? 'rotate-180' : ''">
            ▼
          </span>
        </button>
        <div v-show="expandedSection === 'elements'" class="space-y-4 pl-2">
          <div v-if="docStyles" class="space-y-2">
            <div class="text-sm font-medium">Документ</div>
            <div>
              <label class="text-xs text-zinc-400">Шрифт (pt)</label>
              <input
                type="number"
                :value="docStyles.font_size"
                min="6"
                max="72"
                step="1"
                class="w-full rounded bg-zinc-700 px-2 py-1 text-sm"
                @input="updateDocument({ font_size: +(($event.target as HTMLInputElement).value) })"
              />
            </div>
            <div>
              <label class="text-xs text-zinc-400">Интервал (em)</label>
              <input
                type="number"
                :value="docStyles.line_spacing"
                min="0.5"
                max="3"
                step="0.1"
                class="w-full rounded bg-zinc-700 px-2 py-1 text-sm"
                @input="updateDocument({ line_spacing: +(($event.target as HTMLInputElement).value) })"
              />
            </div>
          </div>
          <div v-if="headingStyles" class="space-y-2">
            <div class="text-sm font-medium">Заголовок</div>
            <input
              type="text"
              :value="headingStyles.numbering"
              placeholder="1.1.1 или none"
              class="w-full rounded bg-zinc-700 px-2 py-1 text-sm"
              @input="updateHeading({ numbering: ($event.target as HTMLInputElement).value })"
            />
          </div>
          <div v-if="tableStyles" class="space-y-2">
            <div class="text-sm font-medium">Таблица</div>
            <input
              type="number"
              :value="tableStyles.stroke"
              step="0.01"
              class="w-full rounded bg-zinc-700 px-2 py-1 text-sm"
              @input="updateTable({ stroke: +(($event.target as HTMLInputElement).value) })"
            />
          </div>
          <div class="space-y-2">
            <div class="text-sm font-medium">Debounce (мс)</div>
            <input
              type="range"
              :value="editorStore.debounceMs"
              min="100"
              max="1000"
              step="50"
              class="w-full"
              @input="editorStore.setDebounceMs(+(($event.target as HTMLInputElement).value))"
            />
            <span class="text-xs text-zinc-400">{{ editorStore.debounceMs }} ms</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
