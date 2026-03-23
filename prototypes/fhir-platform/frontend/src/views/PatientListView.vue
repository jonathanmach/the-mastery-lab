<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { usePatientSearchStore } from '../stores/patientSearch'
import FacetPanel from '../components/FacetPanel.vue'
import PatientCard from '../components/PatientCard.vue'
import type { SearchFilters } from '../api/types'

const store = usePatientSearchStore()

onMounted(() => store.fetchResults())

function onSetFilter(key: keyof SearchFilters, value: string | boolean | number | null) {
  store.setFilter(key, value as never)
}

const totalPages = computed(() => Math.ceil(store.total / 20))
const pageStart = computed(() => (store.filters.page - 1) * 20 + 1)
const pageEnd = computed(() => Math.min(store.filters.page * 20, store.total))
</script>

<template>
  <div class="list-page">
    <FacetPanel
      :facets="store.facets"
      :filters="store.filters"
      @set-filter="onSetFilter"
      @clear="store.clearFilters"
    />

    <div class="results-area">
      <!-- Search bar -->
      <div class="search-wrap">
        <svg class="search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="8.5" cy="8.5" r="5.5"/>
          <path d="M13.5 13.5L18 18" stroke-linecap="round"/>
        </svg>
        <input
          type="search"
          placeholder="Search patients by name…"
          :value="store.filters.q"
          @input="store.setFilter('q', ($event.target as HTMLInputElement).value)"
        />
      </div>

      <!-- Status bar -->
      <div class="results-status">
        <span v-if="store.loading" class="status-loading">
          <span class="spinner" /> Loading patients…
        </span>
        <span v-else-if="store.error" class="status-error">
          <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 4a1 1 0 011 1v3a1 1 0 11-2 0V6a1 1 0 011-1zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
          {{ store.error }}
        </span>
        <template v-else-if="store.total > 0">
          <span class="status-count">
            Showing <strong>{{ pageStart }}–{{ pageEnd }}</strong> of <strong>{{ store.total }}</strong> patients
          </span>
        </template>
        <span v-else class="status-count">No patients found</span>
      </div>

      <!-- Results grid -->
      <div class="results-grid" :class="{ loading: store.loading }">
        <PatientCard v-for="p in store.results" :key="p.patient_id" :patient="p" />
        <div v-if="!store.loading && store.results.length === 0" class="empty">
          <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="24" cy="24" r="20"/>
            <path d="M24 16v8M24 32h.01" stroke-linecap="round"/>
          </svg>
          <p>No patients found.</p>
          <span>Try adjusting your search or filters, or run the ingestion script.</span>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="store.total > 20" class="pagination">
        <button :disabled="store.filters.page <= 1" @click="store.prevPage">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 4L6 8l4 4"/></svg>
          Prev
        </button>
        <span class="page-info">Page <strong>{{ store.filters.page }}</strong> of <strong>{{ totalPages }}</strong></span>
        <button :disabled="store.filters.page >= totalPages" @click="store.nextPage">
          Next
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-page {
  display: flex;
  gap: 20px;
  padding: 24px;
  max-width: 1280px;
  margin: 0 auto;
  align-items: flex-start;
}

.results-area { flex: 1; min-width: 0; }

.search-wrap {
  position: relative;
  margin-bottom: 14px;
}
.search-icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--c-muted);
  pointer-events: none;
}
.search-wrap input { padding-left: 36px; }

.results-status {
  font-size: 13px;
  color: var(--c-muted);
  margin-bottom: 14px;
  min-height: 22px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-loading { display: flex; align-items: center; gap: 8px; }
.status-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--c-danger);
}
.status-error svg { width: 14px; height: 14px; flex-shrink: 0; }
.status-count strong { color: var(--c-text-secondary); }

.results-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  transition: opacity 0.15s;
}
.results-grid.loading { opacity: 0.5; pointer-events: none; }

.empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 24px;
  color: var(--c-muted);
  text-align: center;
  gap: 8px;
}
.empty svg { width: 48px; height: 48px; opacity: 0.3; }
.empty p { margin: 0; font-size: 15px; font-weight: 600; color: var(--c-text-secondary); }
.empty span { font-size: 13px; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--c-border);
}
.pagination button {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
}
.pagination button svg { width: 14px; height: 14px; }
.page-info { font-size: 13px; color: var(--c-text-secondary); }
.page-info strong { color: var(--c-text); }

@media (max-width: 900px) { .results-grid { grid-template-columns: 1fr; } }
@media (max-width: 640px) { .list-page { flex-direction: column; padding: 16px; } }
</style>
