<script setup lang="ts">
</script>

<template>
  <header>
    <nav>
      <RouterLink to="/blog-posts">Blog Posts</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  color: #1a1a1a;
  background: #f9f9f9;
}

header {
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
  padding: 0 32px;
}

nav {
  display: flex;
  gap: 24px;
  height: 56px;
  align-items: center;
}

nav a {
  text-decoration: none;
  color: #555;
  font-size: 15px;
  font-weight: 500;
}

nav a.router-link-active {
  color: #2563eb;
}

main {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 16px;
}

img { max-width: 100%; }
</style>
