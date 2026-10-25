import { createRouter, createWebHistory } from 'vue-router';
import Editor from '../views/Editor.vue';
import Styles from '../views/Styles.vue';
import Rules from '../views/Rules.vue';
import PageEditor from '../views/PageEditor.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'editor',
      component: Editor,
    },
    {
      path: '/styles',
      name: 'styles',
      component: Styles,
    },
    {
      path: '/rules',
      name: 'rules',
      component: Rules,
    },
    {
      path: '/pages',
      name: 'pages',
      component: PageEditor,
    },
    {
      path: '/pages/:id',
      name: 'pages-edit',
      component: PageEditor,
    },
  ],
});

export default router;
