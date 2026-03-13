<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="layout">
    <aside class="sidenav">
      <div class="sidenav-logo">CMS</div>
      <nav>
        <RouterLink to="/content">Content</RouterLink>
        <RouterLink to="/content-types">Content Types</RouterLink>
      </nav>
    </aside>
    <main class="page">
      <RouterView />
    </main>
  </div>
</template>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; font-size: 14px; color: #111; background: #f8f8f8; }

.layout { display: flex; min-height: 100vh; }

.sidenav {
  width: 200px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidenav-logo {
  padding: 20px 20px 16px;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255,255,255,.1);
}
.sidenav nav {
  display: flex;
  flex-direction: column;
  padding: 12px 0;
}
.sidenav nav a {
  color: rgba(255,255,255,.7);
  text-decoration: none;
  padding: 10px 20px;
  border-left: 3px solid transparent;
  transition: background .15s;
}
.sidenav nav a:hover { background: rgba(255,255,255,.07); color: #fff; }
.sidenav nav a.router-link-active { color: #fff; border-left-color: #a0c4ff; background: rgba(255,255,255,.1); }

.page { flex: 1; padding: 28px 32px; overflow: auto; }

h1 { margin-bottom: 16px; font-size: 1.4rem; }
h2 { margin-bottom: 12px; font-size: 1.1rem; }

table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #e5e5e5; }
th { background: #f0f0f0; font-weight: 600; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafafa; }

button { cursor: pointer; padding: 6px 12px; border: none; border-radius: 4px; font-size: 13px; }
.btn-primary { background: #1a1a2e; color: #fff; }
.btn-primary:hover { background: #2d2d5e; }
.btn-danger { background: #e05260; color: #fff; }
.btn-danger:hover { background: #c0394a; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover { background: #cccccc; }
.btn-sm { padding: 4px 8px; font-size: 12px; }

.actions { display: flex; gap: 6px; }
.panel { background: #fff; border-radius: 6px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.1); margin-top: 20px; }

label { display: block; margin-bottom: 4px; font-weight: 600; font-size: 13px; }
input[type=text], input[type=number], input[type=date], input[type=datetime-local], select, textarea {
  width: 100%; padding: 7px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; margin-bottom: 12px;
}
textarea { resize: vertical; min-height: 80px; }

.error { color: #c0394a; font-size: 13px; margin-bottom: 12px; }
.tag { display: inline-block; background: #e8f0fe; color: #1a3a8a; border-radius: 3px; padding: 2px 6px; font-size: 11px; margin-right: 4px; }
.badge { display: inline-block; background: #f0f0f0; color: #555; border-radius: 3px; padding: 2px 7px; font-size: 11px; font-weight: 600; }
</style>
