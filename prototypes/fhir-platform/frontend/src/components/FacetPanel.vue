<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PatientFacets, SearchFilters } from '../api/types'

const props = defineProps<{
  facets: PatientFacets | null
  filters: SearchFilters
}>()

const emit = defineEmits<{
  (e: 'set-filter', key: keyof SearchFilters, value: string | boolean | number | null): void
  (e: 'clear'): void
}>()

const AGE_BAND_ORDER = ['<18', '18-34', '35-49', '50-64', '65+']

function sortedAgeBands(buckets: { key: string; count: number }[]) {
  return [...buckets].sort((a, b) => AGE_BAND_ORDER.indexOf(a.key) - AGE_BAND_ORDER.indexOf(b.key))
}

const hasActiveFilters = computed(() =>
  props.filters.gender || props.filters.condition || props.filters.medication ||
  props.filters.age_band || props.filters.recent_encounter !== null || props.filters.observation
)

const activeFilterCount = computed(() => [
  props.filters.gender, props.filters.condition, props.filters.medication,
  props.filters.age_band, props.filters.recent_encounter !== null ? 'x' : null,
  props.filters.observation,
].filter(Boolean).length)

function onSelectObservation(key: string) {
  const next = props.filters.observation === key ? null : key
  emit('set-filter', 'observation', next)
  emit('set-filter', 'obs_min', null)
  emit('set-filter', 'obs_max', null)
}

// Collapsible sections
const collapsed = ref<Record<string, boolean>>({})
function toggleSection(key: string) {
  collapsed.value[key] = !collapsed.value[key]
}
</script>

<template>
  <aside class="facet-panel">
    <div class="facet-header">
      <div class="facet-title">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <path d="M2 4h12M4 8h8M6 12h4"/>
        </svg>
        Filters
        <span v-if="activeFilterCount > 0" class="filter-count">{{ activeFilterCount }}</span>
      </div>
      <button v-if="hasActiveFilters" class="clear-btn" @click="emit('clear')">Clear</button>
    </div>

    <div v-if="!facets" class="facet-loading"><span class="spinner" /></div>

    <template v-else>
      <!-- Gender -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('gender')">
          <span>Gender</span>
          <svg class="chevron" :class="{ rotated: collapsed.gender }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.gender" class="facet-items">
          <div
            v-for="b in facets.gender"
            :key="b.key"
            class="facet-item"
            :class="{ active: filters.gender === b.key }"
            @click="emit('set-filter', 'gender', filters.gender === b.key ? null : b.key)"
          >
            <span class="fi-check"><svg v-if="filters.gender === b.key" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">{{ b.key }}</span>
            <span class="fi-count">{{ b.count }}</span>
          </div>
        </div>
      </div>

      <!-- Age band -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('age_band')">
          <span>Age band</span>
          <svg class="chevron" :class="{ rotated: collapsed.age_band }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.age_band" class="facet-items">
          <div
            v-for="b in sortedAgeBands(facets.age_band)"
            :key="b.key"
            class="facet-item"
            :class="{ active: filters.age_band === b.key }"
            @click="emit('set-filter', 'age_band', filters.age_band === b.key ? null : b.key)"
          >
            <span class="fi-check"><svg v-if="filters.age_band === b.key" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">{{ b.key }}</span>
            <span class="fi-count">{{ b.count }}</span>
          </div>
        </div>
      </div>

      <!-- Diagnosis -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('diagnosis')">
          <span>Diagnosis</span>
          <svg class="chevron" :class="{ rotated: collapsed.diagnosis }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.diagnosis" class="facet-items">
          <div
            v-for="b in facets.diagnosis.slice(0, 8)"
            :key="b.key"
            class="facet-item"
            :class="{ active: filters.condition === b.key }"
            @click="emit('set-filter', 'condition', filters.condition === b.key ? null : b.key)"
            :title="b.display ?? b.key"
          >
            <span class="fi-check"><svg v-if="filters.condition === b.key" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">{{ b.display ?? b.key }}</span>
            <span class="fi-count">{{ b.count }}</span>
          </div>
        </div>
      </div>

      <!-- Medication -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('medication')">
          <span>Medication</span>
          <svg class="chevron" :class="{ rotated: collapsed.medication }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.medication" class="facet-items">
          <div
            v-for="b in facets.medication.slice(0, 8)"
            :key="b.key"
            class="facet-item"
            :class="{ active: filters.medication === b.key }"
            @click="emit('set-filter', 'medication', filters.medication === b.key ? null : b.key)"
            :title="b.display ?? b.key"
          >
            <span class="fi-check"><svg v-if="filters.medication === b.key" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">{{ b.display ?? b.key }}</span>
            <span class="fi-count">{{ b.count }}</span>
          </div>
        </div>
      </div>

      <!-- Observations -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('observation')">
          <span>Observations</span>
          <svg class="chevron" :class="{ rotated: collapsed.observation }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.observation" class="facet-items">
          <div
            v-for="b in facets.observation.slice(0, 10)"
            :key="b.key"
            class="facet-item"
            :class="{ active: filters.observation === b.key }"
            @click="onSelectObservation(b.key)"
            :title="b.display ?? b.key"
          >
            <span class="fi-check"><svg v-if="filters.observation === b.key" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">{{ b.display ?? b.key }}</span>
            <span class="fi-count">{{ b.count }}</span>
          </div>
          <div v-if="filters.observation" class="obs-range">
            <span class="obs-range-label">Range</span>
            <div class="obs-range-inputs">
              <input
                type="number"
                placeholder="Min"
                :value="filters.obs_min ?? ''"
                @change="emit('set-filter', 'obs_min', ($event.target as HTMLInputElement).value === '' ? null : Number(($event.target as HTMLInputElement).value))"
              />
              <span class="obs-range-sep">–</span>
              <input
                type="number"
                placeholder="Max"
                :value="filters.obs_max ?? ''"
                @change="emit('set-filter', 'obs_max', ($event.target as HTMLInputElement).value === '' ? null : Number(($event.target as HTMLInputElement).value))"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent encounter -->
      <div class="facet-group">
        <button class="section-toggle" @click="toggleSection('recent')">
          <span>Recent encounter</span>
          <svg class="chevron" :class="{ rotated: collapsed.recent }" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6l4 4 4-4"/></svg>
        </button>
        <div v-show="!collapsed.recent" class="facet-items">
          <div
            class="facet-item"
            :class="{ active: filters.recent_encounter === true }"
            @click="emit('set-filter', 'recent_encounter', filters.recent_encounter === true ? null : true)"
          >
            <span class="fi-check"><svg v-if="filters.recent_encounter === true" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">Has recent visit</span>
          </div>
          <div
            class="facet-item"
            :class="{ active: filters.recent_encounter === false }"
            @click="emit('set-filter', 'recent_encounter', filters.recent_encounter === false ? null : false)"
          >
            <span class="fi-check"><svg v-if="filters.recent_encounter === false" viewBox="0 0 12 12" fill="currentColor"><path d="M2 6l3 3 5-5"/></svg></span>
            <span class="fi-key">No recent visit</span>
          </div>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.facet-panel {
  width: 224px;
  flex-shrink: 0;
}

.facet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 0 2px;
}
.facet-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--c-text-secondary);
}
.facet-title svg { width: 14px; height: 14px; }
.filter-count {
  background: var(--c-primary);
  color: #fff;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  padding: 0 5px;
  min-width: 16px;
  text-align: center;
}
.clear-btn {
  background: none;
  border: none;
  color: var(--c-danger);
  font-size: 12px;
  font-weight: 500;
  padding: 2px 4px;
}
.clear-btn:hover { background: var(--c-danger-light); color: var(--c-danger); }

.facet-loading { padding: 20px; text-align: center; }

.facet-group {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  margin-bottom: 8px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.section-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-secondary);
  background: none;
  border: none;
  border-radius: 0;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.section-toggle:hover { background: var(--c-tag-bg); color: var(--c-text); }

.chevron { width: 14px; height: 14px; transition: transform 0.15s; }
.chevron.rotated { transform: rotate(-90deg); }

.facet-items { padding: 4px 0 6px; border-top: 1px solid var(--c-border); }

.facet-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.1s;
}
.facet-item:hover { background: var(--c-tag-bg); }
.facet-item.active { background: var(--c-primary-light); color: var(--c-primary); }

.fi-check {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--c-primary);
}
.fi-check svg { width: 12px; height: 12px; stroke: currentColor; stroke-width: 2; fill: none; }

.fi-key { flex: 1; font-size: 12px; }
.fi-key.code { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 11px; color: var(--c-text-secondary); }
.facet-item.active .fi-key.code { color: var(--c-primary); }

.fi-count {
  font-size: 11px;
  color: var(--c-muted);
  background: var(--c-tag-bg);
  border-radius: 3px;
  padding: 0 5px;
  min-width: 22px;
  text-align: center;
}
.facet-item.active .fi-count { background: #bfdbfe; color: #1d4ed8; }

.obs-range {
  padding: 8px 12px 10px;
  border-top: 1px solid var(--c-border);
  background: var(--c-tag-bg);
}
.obs-range-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--c-muted);
  margin-bottom: 6px;
}
.obs-range-inputs {
  display: flex;
  align-items: center;
  gap: 6px;
}
.obs-range-inputs input {
  flex: 1;
  min-width: 0;
  padding: 4px 6px;
  font-size: 12px;
  border: 1px solid var(--c-border);
  border-radius: 4px;
  background: var(--c-surface);
  color: var(--c-text);
}
.obs-range-inputs input:focus { outline: none; border-color: var(--c-primary); }
.obs-range-sep { font-size: 12px; color: var(--c-muted); flex-shrink: 0; }
</style>
