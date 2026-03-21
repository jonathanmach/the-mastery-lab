<script setup lang="ts">
import { onMounted } from 'vue'
import { usePatientSearchStore } from '../stores/patientSearch'
import FacetPanel from '../components/FacetPanel.vue'
import PatientCard from '../components/PatientCard.vue'
import type { SearchFilters } from '../api/types'

const store = usePatientSearchStore()

onMounted(() => store.fetchResults())

function onSetFilter(key: keyof SearchFilters, value: string | boolean | null) {
  store.setFilter(key, value as never)
}
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
      <div class="search-bar">
        <input
          type="search"
          placeholder="Search patients by name…"
          :value="store.filters.q"
          @input="store.setFilter('q', ($event.target as HTMLInputElement).value)"
        />
      </div>

      <!-- Status -->
      <div class="results-status">
        <span v-if="store.loading"><span class="spinner" /></span>
        <span v-else-if="store.error" class="error">{{ store.error }}</span>
        <span v-else>{{ store.total }} patient{{ store.total !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Results -->
      <div class="results-grid">
        <PatientCard v-for="p in store.results" :key="p.patient_id" :patient="p" />
        <div v-if="!store.loading && store.results.length === 0" class="empty">
          No patients found. Have you run the ingestion script?
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="store.total > 20" class="pagination">
        <button :disabled="store.filters.page <= 1" @click="store.prevPage">← Prev</button>
        <span>Page {{ store.filters.page }}</span>
        <button :disabled="store.filters.page * 20 >= store.total" @click="store.nextPage">Next →</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-page { display: flex; gap: 24px; padding: 24px; max-width: 1200px; margin: 0 auto; }
.results-area { flex: 1; min-width: 0; }
.search-bar { margin-bottom: 16px; }
.results-status { font-size: 13px; color: var(--c-muted); margin-bottom: 12px; min-height: 20px; display: flex; align-items: center; gap: 8px; }
.error { color: var(--c-danger); }
.results-grid { display: flex; flex-direction: column; gap: 10px; }
.empty { text-align: center; padding: 40px; color: var(--c-muted); }
.pagination { display: flex; align-items: center; gap: 12px; margin-top: 20px; font-size: 13px; }
</style>
