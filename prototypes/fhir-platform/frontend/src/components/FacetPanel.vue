<script setup lang="ts">
import type { PatientFacets } from '../api/types'
import type { SearchFilters } from '../api/types'

const props = defineProps<{
  facets: PatientFacets | null
  filters: SearchFilters
}>()

const emit = defineEmits<{
  (e: 'set-filter', key: keyof SearchFilters, value: string | boolean | null): void
  (e: 'clear'): void
}>()

const AGE_BAND_ORDER = ['<18', '18-34', '35-49', '50-64', '65+']

function sortedAgeBands(buckets: { key: string; count: number }[]) {
  return [...buckets].sort((a, b) => AGE_BAND_ORDER.indexOf(a.key) - AGE_BAND_ORDER.indexOf(b.key))
}

const hasActiveFilters = computed(() =>
  props.filters.gender || props.filters.condition || props.filters.medication ||
  props.filters.age_band || props.filters.recent_encounter !== null
)
</script>

<script lang="ts">
import { computed } from 'vue'
export default {}
</script>

<template>
  <aside class="facet-panel">
    <div class="facet-header">
      <span>Filters</span>
      <button v-if="hasActiveFilters" class="clear-btn" @click="emit('clear')">Clear all</button>
    </div>

    <div v-if="!facets" class="facet-loading"><span class="spinner" /></div>

    <template v-else>
      <!-- Gender -->
      <div class="facet-group">
        <div class="facet-label">Gender</div>
        <div
          v-for="b in facets.gender"
          :key="b.key"
          class="facet-item"
          :class="{ active: filters.gender === b.key }"
          @click="emit('set-filter', 'gender', filters.gender === b.key ? null : b.key)"
        >
          <span class="fi-key">{{ b.key }}</span>
          <span class="fi-count">{{ b.count }}</span>
        </div>
      </div>

      <!-- Age band -->
      <div class="facet-group">
        <div class="facet-label">Age band</div>
        <div
          v-for="b in sortedAgeBands(facets.age_band)"
          :key="b.key"
          class="facet-item"
          :class="{ active: filters.age_band === b.key }"
          @click="emit('set-filter', 'age_band', filters.age_band === b.key ? null : b.key)"
        >
          <span class="fi-key">{{ b.key }}</span>
          <span class="fi-count">{{ b.count }}</span>
        </div>
      </div>

      <!-- Diagnosis -->
      <div class="facet-group">
        <div class="facet-label">Diagnosis</div>
        <div
          v-for="b in facets.diagnosis.slice(0, 8)"
          :key="b.key"
          class="facet-item"
          :class="{ active: filters.condition === b.key }"
          @click="emit('set-filter', 'condition', filters.condition === b.key ? null : b.key)"
        >
          <span class="fi-key code">{{ b.key }}</span>
          <span class="fi-count">{{ b.count }}</span>
        </div>
      </div>

      <!-- Medication -->
      <div class="facet-group">
        <div class="facet-label">Medication</div>
        <div
          v-for="b in facets.medication.slice(0, 8)"
          :key="b.key"
          class="facet-item"
          :class="{ active: filters.medication === b.key }"
          @click="emit('set-filter', 'medication', filters.medication === b.key ? null : b.key)"
        >
          <span class="fi-key code">{{ b.key }}</span>
          <span class="fi-count">{{ b.count }}</span>
        </div>
      </div>

      <!-- Recent encounter -->
      <div class="facet-group">
        <div class="facet-label">Recent encounter</div>
        <div
          class="facet-item"
          :class="{ active: filters.recent_encounter === true }"
          @click="emit('set-filter', 'recent_encounter', filters.recent_encounter === true ? null : true)"
        >
          <span class="fi-key">Yes</span>
        </div>
        <div
          class="facet-item"
          :class="{ active: filters.recent_encounter === false }"
          @click="emit('set-filter', 'recent_encounter', filters.recent_encounter === false ? null : false)"
        >
          <span class="fi-key">No</span>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.facet-panel {
  width: 220px;
  flex-shrink: 0;
  padding: 16px 0;
}
.facet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--c-muted);
  margin-bottom: 12px;
  padding: 0 4px;
}
.clear-btn { background: none; border: none; color: var(--c-primary); font-size: 12px; padding: 0; }
.clear-btn:hover { text-decoration: underline; background: none; }
.facet-loading { padding: 20px; text-align: center; }
.facet-group { margin-bottom: 20px; }
.facet-label { font-weight: 600; font-size: 12px; color: var(--c-muted); margin-bottom: 6px; padding: 0 4px; }
.facet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.facet-item:hover { background: var(--c-tag-bg); }
.facet-item.active { background: #cfe2ff; color: #084298; font-weight: 600; }
.fi-count { color: var(--c-muted); font-size: 12px; }
.fi-key.code { font-family: monospace; font-size: 12px; }
</style>
