<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProfilesStore } from '../../stores/profiles';
import { API_BASE } from '../../config';

const profilesStore = useProfilesStore();
const newName = ref('');
const creating = ref(false);
const createError = ref('');
const editingId = ref<number | null>(null);
const editingName = ref('');
const confirmDeleteId = ref<number | null>(null);

onMounted(() => {
  profilesStore.fetchProfiles();
});

async function createProfile() {
  const name = newName.value.trim();
  if (!name) return;
  creating.value = true;
  createError.value = '';
  try {
    const p = await profilesStore.createProfile(name);
    profilesStore.setCurrent(p.id);
    newName.value = '';
  } catch (error) {
    createError.value = error instanceof Error ? error.message : 'Не удалось создать профиль';
  } finally {
    creating.value = false;
  }
}

function startRename(id: number, currentName: string) {
  editingId.value = id;
  editingName.value = currentName;
}

async function finishRename() {
  if (editingId.value == null) return;
  const name = editingName.value.trim();
  if (!name) {
    editingId.value = null;
    return;
  }
  try {
    await fetch(`${API_BASE}/profiles/${editingId.value}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    await profilesStore.fetchProfiles();
  } finally {
    editingId.value = null;
  }
}

function cancelRename() {
  editingId.value = null;
}

async function deleteProfile(id: number) {
  try {
    await fetch(`${API_BASE}/profiles/${id}`, { method: 'DELETE' });
    if (profilesStore.currentId === id) {
      const remaining = profilesStore.list.filter((p) => p.id !== id);
      const first = remaining[0];
      if (first) {
        profilesStore.setCurrent(first.id);
      }
    }
    await profilesStore.fetchProfiles();
  } finally {
    confirmDeleteId.value = null;
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">Профили</h2>
    </div>

    <div class="profile-list">
      <div
        v-for="p in profilesStore.list"
        :key="p.id"
        class="profile-item"
        :class="{ active: profilesStore.currentId === p.id }"
        @click="profilesStore.setCurrent(p.id)"
        @dblclick.stop="startRename(p.id, p.name)"
      >
        <template v-if="editingId === p.id">
          <input
            v-model="editingName"
            type="text"
            class="rename-input"
            @keyup.enter="finishRename"
            @keyup.escape="cancelRename"
            @blur="finishRename"
            @click.stop
            autofocus
          />
        </template>
        <template v-else>
          <span class="profile-name">{{ p.name }}</span>
          <button
            type="button"
            class="delete-btn"
            title="Удалить"
            @click.stop="confirmDeleteId = p.id"
          >
            &times;
          </button>
        </template>
      </div>

      <div v-if="profilesStore.list.length === 0 && !profilesStore.loading" class="empty-hint">
        Нет профилей
      </div>
    </div>

    <div class="create-section">
      <input
        v-model="newName"
        type="text"
        placeholder="Новый профиль..."
        class="create-input"
        @keyup.enter="createProfile"
      />
      <button
        type="button"
        class="create-btn"
        :disabled="creating || !newName.trim()"
        @click="createProfile"
      >
        +
      </button>
    </div>
    <p v-if="createError" class="create-error">{{ createError }}</p>

    <!-- Delete confirmation overlay -->
    <Teleport to="body">
      <div v-if="confirmDeleteId != null" class="modal-overlay" @click="confirmDeleteId = null">
        <div class="modal-box" @click.stop>
          <p class="modal-text">Удалить профиль?</p>
          <div class="modal-actions">
            <button type="button" class="modal-cancel" @click="confirmDeleteId = null">
              Отмена
            </button>
            <button type="button" class="modal-confirm" @click="deleteProfile(confirmDeleteId!)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  min-width: 220px;
  background: #18181b;
  border-right: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  padding: 1rem 1rem 0.5rem;
  border-bottom: 1px solid #27272a;
}

.sidebar-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #fafafa;
  margin: 0;
}

.profile-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.profile-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.625rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s;
  gap: 0.25rem;
}

.profile-item:hover {
  background: #27272a;
}

.profile-item.active {
  background: #3f3f46;
}

.profile-name {
  flex: 1;
  font-size: 0.85rem;
  color: #d4d4d8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  user-select: none;
}

.profile-item.active .profile-name {
  color: #fafafa;
}

.delete-btn {
  opacity: 0;
  background: transparent;
  border: none;
  color: #71717a;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
  transition: opacity 0.15s, color 0.15s;
}

.profile-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ef4444;
}

.rename-input {
  width: 100%;
  background: #27272a;
  border: 1px solid #3b82f6;
  border-radius: 0.25rem;
  color: #fafafa;
  padding: 0.2rem 0.4rem;
  font-size: 0.85rem;
  outline: none;
}

.empty-hint {
  text-align: center;
  color: #52525b;
  font-size: 0.8rem;
  padding: 2rem 0.5rem;
}

.create-section {
  display: flex;
  gap: 0.375rem;
  padding: 0.75rem;
  border-top: 1px solid #27272a;
}

.create-input {
  flex: 1;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 0.375rem;
  color: #fafafa;
  padding: 0.375rem 0.5rem;
  font-size: 0.8rem;
}

.create-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.create-btn {
  background: #3f3f46;
  border: 1px solid #52525b;
  border-radius: 0.375rem;
  color: #fafafa;
  padding: 0.375rem 0.625rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.15s;
}

.create-btn:hover:not(:disabled) {
  background: #52525b;
}

.create-error {
  margin: 4px 12px 0;
  font-size: 11px;
  line-height: 1.3;
  color: #f87171;
}

.create-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 0.5rem;
  padding: 1.5rem;
  min-width: 280px;
}

.modal-text {
  color: #fafafa;
  font-size: 0.9rem;
  margin: 0 0 1.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.modal-cancel {
  padding: 0.4rem 1rem;
  border-radius: 0.375rem;
  background: #3f3f46;
  border: 1px solid #52525b;
  color: #d4d4d8;
  cursor: pointer;
  font-size: 0.85rem;
}

.modal-cancel:hover {
  background: #52525b;
}

.modal-confirm {
  padding: 0.4rem 1rem;
  border-radius: 0.375rem;
  background: #ef4444;
  border: 1px solid #ef4444;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}

.modal-confirm:hover {
  background: #dc2626;
}
</style>
