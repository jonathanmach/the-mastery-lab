<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { getBlogPost, type ContentEntry } from '../api/cms'

const route = useRoute()
const post = ref<ContentEntry | null>(null)
const error = ref('')

onMounted(async () => {
  try {
    post.value = await getBlogPost(route.params.id as string)
  } catch (e) {
    error.value = String(e)
  }
})

const bodyHtml = computed(() => {
  const body = post.value?.data?.body
  if (!body) return ''
  return marked.parse(String(body)) as string
})

function str(v: unknown): string {
  return v != null ? String(v) : ''
}
</script>

<template>
  <div>
    <RouterLink to="/blog-posts" class="back">&larr; Blog Posts</RouterLink>

    <p v-if="error" style="color:#c00; margin-top:16px;">{{ error }}</p>

    <article v-else-if="post" class="post">
      <img
        v-if="post.data.cover_image"
        :src="str(post.data.cover_image)"
        :alt="str(post.data.title)"
        class="cover"
      />

      <div class="tags" v-if="post.data.tags && (post.data.tags as string[]).length">
        <span
          v-for="tag in (post.data.tags as string[])"
          :key="tag"
          class="tag"
        >{{ tag }}</span>
      </div>

      <h1>{{ str(post.data.title) }}</h1>

      <p class="meta">
        <span v-if="post.data.author">By {{ str(post.data.author) }}</span>
        <span v-if="post.data.author && post.data.published_at"> · </span>
        <span v-if="post.data.published_at">{{ str(post.data.published_at) }}</span>
      </p>

      <div class="body" v-html="bodyHtml" />
    </article>

    <p v-else style="color:#888; margin-top:16px;">Loading…</p>
  </div>
</template>

<style scoped>
.back {
  display: inline-block;
  color: #2563eb;
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 24px;
}

.back:hover { text-decoration: underline; }

.post { max-width: 720px; }

.cover {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 20px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.tag {
  font-size: 11px;
  background: #f0f4ff;
  color: #2563eb;
  border-radius: 4px;
  padding: 2px 8px;
}

h1 { margin: 0 0 8px; font-size: 32px; line-height: 1.2; }

.meta { color: #888; font-size: 14px; margin: 0 0 32px; }

.body {
  font-size: 17px;
  line-height: 1.7;
  color: #333;
}

.body :deep(h2),
.body :deep(h3) { margin-top: 2em; }

.body :deep(p) { margin: 0 0 1em; }

.body :deep(img) { border-radius: 6px; }

.body :deep(code) {
  background: #f4f4f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.body :deep(pre) {
  background: #f4f4f4;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}
</style>
