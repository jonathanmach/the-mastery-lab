<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getPatientSummary, getPatientTimeline, getPatientResources } from '../api'
import type { PatientSummary, PatientTimeline } from '../api/types'

const props = defineProps<{ id: string }>()
const router = useRouter()

const summary = ref<PatientSummary | null>(null)
const timeline = ref<PatientTimeline | null>(null)
const rawResources = ref<Record<string, unknown[]> | null>(null)

const activeTab = ref<'summary' | 'timeline' | 'raw'>('summary')
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const [s, t] = await Promise.all([
      getPatientSummary(props.id),
      getPatientTimeline(props.id),
    ])
    summary.value = s
    timeline.value = t
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load patient'
  } finally {
    loading.value = false
  }
})

async function loadRaw() {
  if (rawResources.value) return
  rawResources.value = await getPatientResources(props.id)
}

function onTabChange(tab: 'summary' | 'timeline' | 'raw') {
  activeTab.value = tab
  if (tab === 'raw') loadRaw()
}

const conditionDisplay = (cond: Record<string, unknown>) => {
  const code = cond.code as Record<string, unknown> | undefined
  const codings = (code?.coding as Array<Record<string, string>>) || []
  return codings[0]?.display || (code?.text as string) || 'Unknown condition'
}

const medDisplay = (med: Record<string, unknown>) => {
  const mc = med.medicationCodeableConcept as Record<string, unknown> | undefined
  const codings = (mc?.coding as Array<Record<string, string>>) || []
  return codings[0]?.display || (mc?.text as string) || 'Unknown medication'
}

const EVENT_COLORS: Record<string, string> = {
  Encounter: '#0d6efd',
  Condition: '#dc3545',
  Observation: '#198754',
  MedicationRequest: '#fd7e14',
}
</script>

<template>
  <div class="detail-page">
    <div class="back-link">
      <a href="#" @click.prevent="router.back()">← Back to patients</a>
    </div>

    <div v-if="loading" class="loading-state"><span class="spinner" /> Loading patient…</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else-if="summary">
      <!-- Demographics header -->
      <div class="card demographics">
        <div class="demo-main">
          <h1 class="patient-name">{{ summary.name }}</h1>
          <span class="badge" :class="summary.validation_status">{{ summary.validation_status }}</span>
        </div>
        <div class="demo-meta">
          <span v-if="summary.gender"><strong>Gender:</strong> {{ summary.gender }}</span>
          <span v-if="summary.birth_date"><strong>DOB:</strong> {{ summary.birth_date }}</span>
          <span v-if="summary.age_band"><strong>Age band:</strong> {{ summary.age_band }}</span>
          <span v-if="summary.address"><strong>Address:</strong> {{ summary.address }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: activeTab === 'summary' }" @click="onTabChange('summary')">Summary</button>
        <button :class="{ active: activeTab === 'timeline' }" @click="onTabChange('timeline')">Timeline</button>
        <button :class="{ active: activeTab === 'raw' }" @click="onTabChange('raw')">Raw FHIR</button>
      </div>

      <!-- Summary tab -->
      <div v-if="activeTab === 'summary'" class="tab-content">
        <div class="two-col">
          <!-- Conditions -->
          <div class="card">
            <h3>Conditions ({{ summary.conditions.length }})</h3>
            <table v-if="summary.conditions.length">
              <thead><tr><th>Condition</th><th>Date</th></tr></thead>
              <tbody>
                <tr v-for="(c, i) in summary.conditions" :key="i">
                  <td>{{ conditionDisplay(c as Record<string, unknown>) }}</td>
                  <td>{{ (c as Record<string, unknown>).recordedDate || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-msg">No conditions recorded.</p>
          </div>

          <!-- Medications -->
          <div class="card">
            <h3>Medications ({{ summary.medications.length }})</h3>
            <table v-if="summary.medications.length">
              <thead><tr><th>Medication</th><th>Status</th><th>Date</th></tr></thead>
              <tbody>
                <tr v-for="(m, i) in summary.medications" :key="i">
                  <td>{{ medDisplay(m as Record<string, unknown>) }}</td>
                  <td>
                    <span :class="['tag', (m as Record<string, unknown>).status === 'active' ? 'active-tag' : '']">
                      {{ (m as Record<string, unknown>).status }}
                    </span>
                  </td>
                  <td>{{ (m as Record<string, unknown>).authoredOn || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-msg">No medications recorded.</p>
          </div>
        </div>

        <!-- Observations -->
        <div class="card" v-if="summary.latest_observations.length">
          <h3>Latest Observations</h3>
          <table>
            <thead><tr><th>Observation</th><th>Value</th><th>Date</th></tr></thead>
            <tbody>
              <tr v-for="obs in summary.latest_observations" :key="obs.code">
                <td>{{ obs.display }}</td>
                <td>
                  <template v-if="obs.value && typeof obs.value === 'object' && 'value' in (obs.value as object)">
                    {{ (obs.value as Record<string, unknown>).value }}
                    {{ (obs.value as Record<string, unknown>).unit }}
                  </template>
                  <template v-else>{{ obs.value ?? '—' }}</template>
                </td>
                <td>{{ obs.date?.slice(0, 10) || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Timeline tab -->
      <div v-if="activeTab === 'timeline'" class="tab-content">
        <div class="timeline" v-if="timeline && timeline.events.length">
          <div v-for="(ev, i) in timeline.events" :key="i" class="timeline-item">
            <div
              class="tl-dot"
              :style="{ background: EVENT_COLORS[ev.event_type] || '#adb5bd' }"
            />
            <div class="tl-body">
              <span class="tl-date">{{ ev.date?.slice(0, 10) || 'Unknown date' }}</span>
              <span class="tl-type" :style="{ color: EVENT_COLORS[ev.event_type] }">{{ ev.event_type }}</span>
              <span class="tl-desc">{{ ev.description }}</span>
            </div>
          </div>
        </div>
        <p v-else class="empty-msg">No timeline events.</p>
      </div>

      <!-- Raw FHIR tab -->
      <div v-if="activeTab === 'raw'" class="tab-content">
        <div v-if="!rawResources" class="loading-state"><span class="spinner" /></div>
        <template v-else>
          <div v-for="(resources, rt) in rawResources" :key="rt" class="raw-section">
            <h4>{{ rt }} ({{ resources.length }})</h4>
            <pre class="raw-json">{{ JSON.stringify(resources, null, 2) }}</pre>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-page { max-width: 960px; margin: 0 auto; padding: 24px; }
.back-link { margin-bottom: 16px; font-size: 13px; }
.loading-state, .error-state { display: flex; align-items: center; gap: 10px; padding: 40px; color: var(--c-muted); justify-content: center; }
.error-state { color: var(--c-danger); }

.demographics { margin-bottom: 20px; }
.demo-main { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.patient-name { margin: 0; font-size: 22px; font-weight: 700; }
.demo-meta { display: flex; gap: 16px; font-size: 13px; flex-wrap: wrap; }

.tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid var(--c-border); }
.tabs button {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--c-muted);
  margin-bottom: -2px;
}
.tabs button:hover { color: var(--c-text); background: none; }
.tabs button.active { color: var(--c-primary); border-bottom-color: var(--c-primary); }

.tab-content { display: flex; flex-direction: column; gap: 16px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card h3 { margin: 0 0 12px; font-size: 15px; }
.empty-msg { color: var(--c-muted); font-size: 13px; }
.active-tag { background: #d1e7dd; color: #0a3622; }

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; position: relative; }
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 26px;
  bottom: -10px;
  width: 2px;
  background: var(--c-border);
}
.tl-dot { width: 16px; height: 16px; border-radius: 50%; flex-shrink: 0; margin-top: 2px; }
.tl-body { display: flex; gap: 10px; flex-wrap: wrap; align-items: baseline; font-size: 13px; }
.tl-date { color: var(--c-muted); font-variant-numeric: tabular-nums; min-width: 90px; }
.tl-type { font-weight: 600; font-size: 12px; }
.tl-desc { color: var(--c-text); }

/* Raw FHIR */
.raw-section { margin-bottom: 16px; }
.raw-section h4 { margin: 0 0 8px; font-size: 14px; }
.raw-json {
  background: #f1f3f5;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 12px;
  font-size: 12px;
  overflow: auto;
  max-height: 400px;
  white-space: pre-wrap;
  word-break: break-all;
}

@media (max-width: 640px) { .two-col { grid-template-columns: 1fr; } }
</style>
