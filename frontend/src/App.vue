<script setup lang="ts">
import { RouterView, RouterLink, useRoute } from 'vue-router';
import { computed } from 'vue';

const route = useRoute();
const isEditor = computed(() => route.name === 'editor');
const isStyles = computed(() => route.name === 'styles');
const isRules = computed(() => route.name === 'rules');
const isPages = computed(() => route.name === 'pages' || route.name === 'pages-edit');
</script>

<template>
  <div class="app-shell">
    <nav class="app-nav">
      <RouterLink to="/" class="nav-link" :class="{ active: isEditor }">
        Редактор
      </RouterLink>
      <RouterLink to="/styles" class="nav-link" :class="{ active: isStyles }">
        Стили
      </RouterLink>
      <RouterLink to="/rules" class="nav-link" :class="{ active: isRules }">
        Правила
      </RouterLink>
      <RouterLink to="/pages" class="nav-link" :class="{ active: isPages }">
        Титульники
      </RouterLink>
    </nav>
    <div class="app-content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.app-nav {
  display: flex;
  gap: 0.25rem;
  padding: 0 1rem;
  background: #18181b;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.nav-link {
  padding: 0.625rem 1rem;
  color: #a1a1aa;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}

.nav-link:hover {
  color: #fafafa;
}

.nav-link.active {
  color: #fafafa;
  border-bottom-color: #3b82f6;
}

.app-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
