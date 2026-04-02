<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { RouterView, RouterLink } from 'vue-router'

const isDark = ref(false)

// Initialise from localStorage, fall back to system preference
const stored = localStorage.getItem('theme')
if (stored === 'dark') isDark.value = true
else if (stored === 'light') isDark.value = false
else isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches

watchEffect(() => {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
})
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect width="14" height="14" rx="3" fill="white" fill-opacity=".2"/>
            <path d="M3 4h8M3 7h8M3 10h5" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="logo-name">Pydantic CMS</span>
      </div>

      <nav class="sidebar-nav">
        <p class="nav-group-label">Navigation</p>
        <RouterLink to="/content" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
          </svg>
          Content
        </RouterLink>
        <RouterLink to="/content-types" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z"/>
          </svg>
          Content Types
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-footer-dot"></div>
        <span>Admin</span>
        <button class="theme-toggle" :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'" @click="isDark = !isDark">
          <!-- Sun -->
          <svg v-if="isDark" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
          </svg>
          <!-- Moon -->
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --primary-light: #eef2ff;
  --primary-text: #4338ca;
  --danger: #dc2626;
  --danger-hover: #b91c1c;
  --danger-light: #fef2f2;
  --danger-hover-bg: #fee2e2;
  --danger-border: #fecaca;
  --danger-border-hover: #fca5a5;
  --danger-text: #dc2626;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-raised: #f8fafc;
  --surface-subtle: #f1f5f9;
  --border: #e2e8f0;
  --border-hover: #cbd5e1;
  --text: #0f172a;
  --text-secondary: #475569;
  --text-tertiary: #94a3b8;
  --code-color: #3730a3;
  --sidebar-w: 224px;
  --radius: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / .05);
  --shadow: 0 1px 3px 0 rgb(0 0 0 / .08), 0 1px 2px -1px rgb(0 0 0 / .06);
}

[data-theme="dark"] {
  --primary-light: rgb(79 70 229 / .18);
  --primary-text: #818cf8;
  --danger-light: rgb(220 38 38 / .15);
  --danger-hover-bg: rgb(220 38 38 / .22);
  --danger-border: rgb(220 38 38 / .35);
  --danger-border-hover: rgb(220 38 38 / .5);
  --danger-text: #f87171;
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-raised: #1e293b;
  --surface-subtle: #334155;
  --border: #334155;
  --border-hover: #475569;
  --text: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --code-color: #a5b4fc;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / .25);
  --shadow: 0 1px 3px 0 rgb(0 0 0 / .3), 0 1px 2px -1px rgb(0 0 0 / .25);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; }
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Layout ────────────────────────────────────────────── */
.layout { display: flex; min-height: 100vh; }

/* ── Sidebar ───────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 16px 14px;
  border-bottom: 1px solid var(--border);
}
.logo-mark {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgb(79 70 229 / .35);
}
.logo-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.nav-group-label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  padding: 6px 8px 6px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: background .12s, color .12s;
}
.nav-item:hover { background: var(--surface-subtle); color: var(--text); }
.nav-item.router-link-active {
  background: var(--primary-light);
  color: var(--primary-text);
}
.nav-icon { width: 15px; height: 15px; flex-shrink: 0; }

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
}
.sidebar-footer-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
}
.sidebar-footer span { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }

/* ── Main content ──────────────────────────────────────── */
.main-content { flex: 1; overflow: auto; min-width: 0; }

/* ── Page primitives (shared by all views) ─────────────── */
.page-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 18px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 10;
}
.page-header h1 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}
.page-header-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 1px;
}
.page-body { padding: 24px 32px; }

/* ── Table ─────────────────────────────────────────────── */
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
table { width: 100%; border-collapse: collapse; }
th {
  text-align: left;
  padding: 9px 16px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--border);
}
td {
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-secondary);
}
tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--surface-raised); }

/* ── Empty state ───────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 52px 20px;
}
.empty-state-icon {
  margin: 0 auto 14px;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--surface-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}
.empty-state h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; }
.empty-state p { font-size: 13px; color: var(--text-tertiary); }

/* ── Buttons ───────────────────────────────────────────── */
button {
  cursor: pointer;
  border: none;
  font-family: inherit;
  transition: all .12s;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
}
.btn-sm { padding: 5px 9px; font-size: 12px; }
.btn-primary {
  background: var(--primary);
  color: white;
  box-shadow: 0 1px 2px rgb(79 70 229 / .2);
}
.btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
.btn-primary:disabled { opacity: .45; cursor: not-allowed; }
.btn-secondary {
  background: var(--surface);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-secondary:hover { background: var(--surface-raised); color: var(--text); border-color: var(--border-hover); }
.btn-danger {
  background: var(--danger-light);
  color: var(--danger-text);
  border: 1px solid var(--danger-border);
}
.btn-danger:hover { background: var(--danger-hover-bg); border-color: var(--danger-border-hover); }

/* ── Form card ─────────────────────────────────────────── */
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  margin-top: 20px;
}
.form-card-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-raised);
  display: flex;
  align-items: center;
  gap: 10px;
}
.form-card-header h2 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.form-card-body { padding: 20px; }

/* ── Form controls ─────────────────────────────────────── */
.form-group { margin-bottom: 14px; }
.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 5px;
  letter-spacing: .01em;
}
input[type=text],
input[type=number],
input[type=date],
input[type=datetime-local],
select,
textarea {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 13px;
  font-family: inherit;
  color: var(--text);
  background: var(--surface);
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
input:focus, select:focus, textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgb(79 70 229 / .1);
}
input:disabled {
  background: var(--surface-raised);
  color: var(--text-tertiary);
  cursor: not-allowed;
}
textarea { resize: vertical; min-height: 80px; }

/* ── Misc ──────────────────────────────────────────────── */
.error-alert {
  background: var(--danger-light);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius);
  padding: 9px 13px;
  font-size: 13px;
  color: var(--danger-text);
  margin-bottom: 16px;
}
.tag {
  display: inline-flex;
  align-items: center;
  background: var(--primary-light);
  color: var(--primary-text);
  border-radius: 20px;
  padding: 1px 8px;
  font-size: 11px;
  font-weight: 500;
  margin-right: 3px;
}
.badge {
  display: inline-flex;
  align-items: center;
  background: var(--surface-subtle);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 600;
}
code {
  font-family: 'SF Mono', 'Cascadia Code', 'Monaco', monospace;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 11.5px;
  color: var(--code-color);
}
.actions { display: flex; gap: 6px; align-items: center; }
.divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

/* ── Theme toggle ───────────────────────────────────────── */
.sidebar-footer { justify-content: space-between; }
.theme-toggle {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: transparent;
  color: var(--text-tertiary);
  border: 1px solid transparent;
  flex-shrink: 0;
  transition: background .12s, color .12s, border-color .12s;
}
.theme-toggle:hover {
  background: var(--surface-subtle);
  color: var(--text-secondary);
  border-color: var(--border);
}
</style>
