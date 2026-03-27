<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const route = useRoute()
const isDetail = computed(() => route.name === 'patient-detail' || !!route.params.id)
</script>

<template>
  <div id="layout">
    <header>
      <div class="header-inner">
        <RouterLink to="/patients" class="brand">
          <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" stroke-opacity="0.4"/>
            <path d="M12 7v5l3 3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 12H7M12 9V7M15 12h2M12 15v2" stroke-linecap="round"/>
          </svg>
          <span class="brand-name">FHIR Platform</span>
          <span class="brand-tag">R4</span>
        </RouterLink>

        <nav class="main-nav">
          <RouterLink to="/patients" class="nav-link" :class="{ active: route.path.startsWith('/patients') }">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
            </svg>
            Patients
          </RouterLink>
          <RouterLink to="/omop" class="nav-link" :class="{ active: route.path === '/omop' }">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            OMOP Chat
          </RouterLink>
        </nav>

        <nav v-if="isDetail" class="breadcrumb">
          <RouterLink to="/patients" class="bc-link">Patients</RouterLink>
          <span class="bc-sep">›</span>
          <span class="bc-current">Patient Detail</span>
        </nav>
      </div>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#layout { display: flex; flex-direction: column; min-height: 100vh; }

header {
  background: #1e293b;
  color: #f8fafc;
  height: 52px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.header-inner {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f8fafc;
  text-decoration: none;
  flex-shrink: 0;
}
.brand:hover { text-decoration: none; opacity: 0.9; }
.brand-icon { width: 22px; height: 22px; color: #60a5fa; }
.brand-name { font-weight: 700; font-size: 15px; letter-spacing: -0.2px; }
.brand-tag {
  background: rgba(96, 165, 250, 0.2);
  color: #93c5fd;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 2px;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  text-decoration: none;
  transition: color 0.15s, background 0.15s;
}
.nav-link svg { width: 15px; height: 15px; }
.nav-link:hover { color: #f8fafc; background: rgba(255,255,255,0.07); text-decoration: none; }
.nav-link.active { color: #f8fafc; background: rgba(255,255,255,0.1); }

.breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-left: auto; }
.bc-link { color: #94a3b8; }
.bc-link:hover { color: #f8fafc; text-decoration: none; }
.bc-sep { color: #475569; }
.bc-current { color: #cbd5e1; }

main { flex: 1; }
</style>
