import { createRouter, createWebHistory } from 'vue-router'
import ContentTypesView from '../views/ContentTypesView.vue'
import ContentView from '../views/ContentView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/content' },
    { path: '/content', component: ContentView },
    { path: '/content-types', component: ContentTypesView },
  ],
})

export default router
