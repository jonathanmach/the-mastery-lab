<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBlogPosts, type ContentEntry } from '../api/cms'

const posts = ref<ContentEntry[]>([])
const error = ref('')

onMounted(async () => {
  try {
    posts.value = await getBlogPosts()
  } catch (e) {
    error.value = String(e)
  }
})

function str(v: unknown): string {
  return v != null ? String(v) : ''
}
</script>

<template>
  <div>
    <h1>Blog Posts</h1>

    <p v-if="error" style="color:#c00;">{{ error }}</p>

    <p v-else-if="!posts.length" style="color:#888;">
      No blog posts yet. Create some in the admin.
    </p>

    <div v-else class="grid">
      <RouterLink
        v-for="post in posts"
        :key="post.id"
        :to="`/blog-posts/${post.id}`"
        class="card"
      >
        <img
          v-if="post.data.cover_image"
          :src="str(post.data.cover_image)"
          :alt="str(post.data.title)"
          class="card-cover"
        />
        <div class="card-cover card-cover--placeholder" v-else />

        <div class="card-body">
          <h2 class="card-title">{{ str(post.data.title) }}</h2>
          <p class="card-meta">
            <span v-if="post.data.author">{{ str(post.data.author) }}</span>
            <span v-if="post.data.author && post.data.published_at"> · </span>
            <span v-if="post.data.published_at">{{ str(post.data.published_at) }}</span>
          </p>
          <div v-if="post.data.tags && (post.data.tags as string[]).length" class="card-tags">
            <span
              v-for="tag in (post.data.tags as string[])"
              :key="tag"
              class="tag"
            >{{ tag }}</span>
          </div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
h1 { margin-bottom: 24px; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.15s;
}

.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }

.card-cover {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.card-cover--placeholder {
  background: #f0f0f0;
}

.card-body { padding: 16px; }

.card-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 6px;
  line-height: 1.3;
}

.card-meta {
  font-size: 13px;
  color: #888;
  margin: 0 0 10px;
}

.card-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.tag {
  font-size: 11px;
  background: #f0f4ff;
  color: #2563eb;
  border-radius: 4px;
  padding: 2px 8px;
}
</style>
