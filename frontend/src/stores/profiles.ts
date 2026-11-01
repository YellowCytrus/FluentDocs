import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useLocalStorage } from '@vueuse/core';
import type { Profile } from '../types/api';
import { API_BASE } from '../config';

export const useProfilesStore = defineStore('profiles', () => {
  const list = ref<Profile[]>([]);
  const currentId = ref<number | null>(null);
  const styleCache = ref<Map<number, string>>(new Map());
  const loading = ref(false);
  const lastProfileId = useLocalStorage<number | null>('sfuLastProfileId', null);

  const current = computed(() =>
    list.value.find((p) => p.id === currentId.value) ?? null
  );

  async function fetchProfiles() {
    loading.value = true;
    try {
      const res = await fetch(`${API_BASE}/profiles`);
      if (!res.ok) throw new Error('Failed to fetch profiles');
      list.value = await res.json();
      if (list.value.length > 0 && !currentId.value) {
        // При первом открытии новых профилей по умолчанию показываем
        // профиль СТУ СФУ, если он есть (OWNER_DECISIONS 15).
        const preferred =
          list.value.find((profile) => profile.name === 'СТУ СФУ') ?? list.value[0];
        const id = lastProfileId.value ?? preferred?.id;
        if (id != null && list.value.some((p) => p.id === id)) {
          currentId.value = id;
        } else if (preferred) {
          currentId.value = preferred.id;
        }
        if (currentId.value != null) lastProfileId.value = currentId.value;
      }
    } finally {
      loading.value = false;
    }
  }

  function setCurrent(id: number) {
    currentId.value = id;
    lastProfileId.value = id;
  }

  async function loadProfileStyles(profileId: number) {
    const res = await fetch(`${API_BASE}/profiles/${profileId}/preamble`);
    const preamble = res.ok ? await res.text() : '';
    const cache = new Map(styleCache.value);
    cache.set(profileId, preamble);
    styleCache.value = cache;
    return preamble;
  }

  function getCachedPreamble(profileId: number): string | undefined {
    return styleCache.value.get(profileId);
  }

  function invalidateCache(profileId: number) {
    const cache = new Map(styleCache.value);
    cache.delete(profileId);
    styleCache.value = cache;
  }

  async function createProfile(name: string) {
    const res = await fetch(`${API_BASE}/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      const detail = await res
        .json()
        .then((body: { detail?: string }) => body.detail)
        .catch(() => undefined);
      throw new Error(detail || 'Не удалось создать профиль');
    }
    const profile = await res.json();
    list.value = [...list.value, profile];
    return profile;
  }

  return {
    list,
    currentId,
    current,
    styleCache,
    loading,
    lastProfileId,
    fetchProfiles,
    setCurrent,
    loadProfileStyles,
    getCachedPreamble,
    invalidateCache,
    createProfile,
  };
});
