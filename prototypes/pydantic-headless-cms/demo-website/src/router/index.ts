import { createRouter, createWebHistory } from 'vue-router'
import BlogPostsView from '../views/BlogPostsView.vue'
import BlogPostDetailView from '../views/BlogPostDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/blog-posts' },
    { path: '/blog-posts', component: BlogPostsView },
    { path: '/blog-posts/:id', component: BlogPostDetailView },
  ],
})

export default router
