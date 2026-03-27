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

// Avatar
const AVATAR_COLORS = [
  ['#dbeafe', '#1d4ed8'], ['#dcfce7', '#15803d'], ['#fce7f3', '#9d174d'],
  ['#fef3c7', '#92400e'], ['#ede9fe', '#6d28d9'], ['#ffedd5', '#c2410c'],
]
const avatarStyle = computed(() => {
  if (!summary.value) return {}
  let hash = 0
  for (const ch of summary.value.name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffff
  const [bg, fg] = AVATAR_COLORS[hash % AVATAR_COLORS.length]
  return { background: bg, color: fg }
})
const initials = computed(() => {
  if (!summary.value) return ''
  const parts = summary.value.name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return parts[0].slice(0, 2).toUpperCase()
})

// Helpers
const conditionDisplay = (cond: Record<string, unknown>) => {
  const code = cond.code as Record<string, unknown> | undefined
  const codings = (code?.coding as Array<Record<string, string>>) || []
  return codings[0]?.display || (code?.text as string) || 'Unknown'
}
const medDisplay = (med: Record<string, unknown>) => {
  const mc = med.medicationCodeableConcept as Record<string, unknown> | undefined
  const codings = (mc?.coding as Array<Record<string, string>>) || []
  return codings[0]?.display || (mc?.text as string) || 'Unknown'
}
const obsValueDisplay = (obs: { value: unknown; code: string }) => {
  if (!obs.value) return '—'
  if (typeof obs.value === 'object' && obs.value !== null && 'value' in obs.value) {
    const v = obs.value as Record<string, unknown>
    return `${v.value} ${v.unit ?? ''}`.trim()
  }
  return String(obs.value)
}

const EVENT_COLORS: Record<string, string> = {
  Encounter:         '#2563eb',
  Condition:         '#dc2626',
  Observation:       '#16a34a',
  MedicationRequest: '#d97706',
}
const EVENT_BG: Record<string, string> = {
  Encounter:         '#eff6ff',
  Condition:         '#fee2e2',
  Observation:       '#dcfce7',
  MedicationRequest: '#fef3c7',
}

// Detail panel
const selectedItem = ref<Record<string, unknown> | null>(null)
const selectedType = ref<'condition' | 'medication' | 'observation' | 'encounter' | null>(null)

function openPanel(item: unknown, type: 'condition' | 'medication' | 'observation') {
  selectedItem.value = item as Record<string, unknown>
  selectedType.value = type
}

function openPanelFromTimeline(ev: { event_type: string; resource_id: string | null }) {
  if (!summary.value || !ev.resource_id) return
  if (ev.event_type === 'Condition') {
    const item = (summary.value.conditions as any[]).find((c: any) => c.id === ev.resource_id)
    if (item) openPanel(item, 'condition')
  } else if (ev.event_type === 'MedicationRequest') {
    const item = (summary.value.medications as any[]).find((m: any) => m.id === ev.resource_id)
    if (item) openPanel(item, 'medication')
  } else if (ev.event_type === 'Observation') {
    const item = (summary.value.latest_observations as any[]).find((o: any) => o.id === ev.resource_id)
    if (item) openPanel(item, 'observation')
  } else if (ev.event_type === 'Encounter') {
    const item = (summary.value.encounters as any[]).find((e: any) => e.id === ev.resource_id)
    if (item) openPanel(item, 'encounter')
  }
}
function closePanel() {
  selectedItem.value = null
  selectedType.value = null
}

function conditionDetail(c: Record<string, unknown>) {
  const cs = c as any
  return {
    clinicalStatus:      cs.clinicalStatus?.coding?.[0]?.code,
    verificationStatus:  cs.verificationStatus?.coding?.[0]?.code,
    category:            cs.category?.[0]?.coding?.[0]?.display ?? cs.category?.[0]?.coding?.[0]?.code,
    severity:            cs.severity?.coding?.[0]?.display,
    onset:               cs.onsetDateTime?.slice(0, 10),
    abatement:           cs.abatementDateTime?.slice(0, 10),
    recorded:            cs.recordedDate?.slice(0, 10),
    snomedCode:          cs.code?.coding?.[0]?.code,
    notes:               (cs.note as any[])?.map((n: any) => n.text).filter(Boolean) ?? [],
  }
}

function medDetail(m: Record<string, unknown>) {
  const ms = m as any
  const dosage = ms.dosageInstruction?.[0]
  const doseQty = dosage?.doseAndRate?.[0]?.doseQuantity
  const dispense = ms.dispenseRequest
  return {
    status:       ms.status,
    intent:       ms.intent,
    authored:     ms.authoredOn?.slice(0, 10),
    dosageText:   dosage?.text,
    route:        dosage?.route?.coding?.[0]?.display,
    dose:         doseQty ? `${doseQty.value} ${doseQty.unit}` : null,
    timing:       dosage?.timing?.code?.text,
    reasonCode:   ms.reasonCode?.[0]?.coding?.[0]?.display ?? ms.reasonCode?.[0]?.text,
    rxNormCode:   ms.medicationCodeableConcept?.coding?.[0]?.code,
    requester:    ms.requester?.display,
    quantity:     dispense?.quantity ? `${dispense.quantity.value} ${dispense.quantity.unit}` : null,
    refills:      dispense?.numberOfRepeatsAllowed,
    notes:        (ms.note as any[])?.map((n: any) => n.text).filter(Boolean) ?? [],
  }
}

const ENC_CLASS_LABELS: Record<string, string> = {
  AMB: 'Ambulatory', IMP: 'Inpatient', EMER: 'Emergency',
  HH: 'Home Health', VR: 'Virtual', OBSENC: 'Observation',
}

function encDetail(e: Record<string, unknown>) {
  const es = e as any
  const classCode = es.class?.code
  return {
    status:       es.status,
    class:        ENC_CLASS_LABELS[classCode] ?? classCode,
    type:         es.type?.[0]?.coding?.[0]?.display ?? es.type?.[0]?.text,
    reason:       es.reasonCode?.[0]?.coding?.[0]?.display ?? es.reasonCode?.[0]?.text,
    start:        es.period?.start?.slice(0, 10),
    end:          es.period?.end?.slice(0, 10),
    participants: (es.participant as any[])?.map((p: any) =>
      p.individual?.display ?? p.individual?.reference
    ).filter(Boolean) ?? [],
    diagnoses:    (es.diagnosis as any[])?.map((d: any) =>
      d.condition?.display ?? d.condition?.reference
    ).filter(Boolean) ?? [],
    location:     es.location?.[0]?.location?.display,
    serviceProvider: es.serviceProvider?.display,
    discharge:    es.hospitalization?.dischargeDisposition?.coding?.[0]?.display,
  }
}

function obsDetail(o: Record<string, unknown>) {
  const os = o as any
  const ref = os.referenceRange?.[0]
  const refText = ref?.text ?? (ref?.low || ref?.high
    ? `${ref?.low?.value ?? '?'} – ${ref?.high?.value ?? '?'} ${ref?.low?.unit ?? ref?.high?.unit ?? ''}`.trim()
    : null)
  return {
    status:         os.status,
    category:       os.category,
    interpretation: os.interpretation,
    referenceRange: refText,
    unit:           os.value?.unit,
    components:     (os.components as any[])?.map((c: any) => ({
      display: c.code?.coding?.[0]?.display ?? c.code?.text,
      value:   c.valueQuantity ? `${c.valueQuantity.value} ${c.valueQuantity.unit}` : '—',
    })),
    notes:          (os.note as string[]) ?? [],
  }
}

// Group timeline events by year
const timelineByYear = computed(() => {
  if (!timeline.value) return []
  const groups: Array<{ year: string; events: typeof timeline.value.events }> = []
  for (const ev of timeline.value.events) {
    const year = ev.date?.slice(0, 4) ?? 'Unknown'
    const last = groups[groups.length - 1]
    if (last?.year === year) last.events.push(ev)
    else groups.push({ year, events: [ev] })
  }
  return groups
})
</script>

<template>
  <div class="detail-page">
    <div class="back-link" @click.prevent="router.back()">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 4L6 8l4 4"/></svg>
      Back to patients
    </div>

    <div v-if="loading" class="loading-state"><span class="spinner" /> Loading patient record…</div>
    <div v-else-if="error" class="error-state">
      <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm0 4a1 1 0 011 1v4a1 1 0 11-2 0V7a1 1 0 011-1zm0 8a1 1 0 110-2 1 1 0 010 2z"/></svg>
      {{ error }}
    </div>

    <template v-else-if="summary">
      <!-- Demographics header -->
      <div class="demographics card">
        <div class="demo-left">
          <div class="avatar-lg" :style="avatarStyle">{{ initials }}</div>
          <div class="demo-info">
            <h1 class="patient-name">{{ summary.name }}</h1>
            <div class="demo-pills">
              <span v-if="summary.gender" class="demo-pill">
                <svg viewBox="0 0 14 14" fill="currentColor"><circle cx="7" cy="7" r="5" fill-opacity=".15"/></svg>
                {{ summary.gender }}
              </span>
              <span v-if="summary.birth_date" class="demo-pill">
                <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2.5" width="10" height="9" rx="1.5"/><path d="M4.5 1v2M9.5 1v2M2 6h10" stroke-linecap="round"/></svg>
                {{ summary.birth_date }}
              </span>
              <span v-if="summary.age_band" class="demo-pill highlight">{{ summary.age_band }}</span>
              <span v-if="summary.address" class="demo-pill">
                <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M7 1C4.79 1 3 2.79 3 5c0 3 4 8 4 8s4-5 4-8c0-2.21-1.79-4-4-4z" stroke-linecap="round"/></svg>
                {{ summary.address }}
              </span>
            </div>
          </div>
        </div>
        <div class="demo-right">
          <span class="badge" :class="summary.validation_status">{{ summary.validation_status }}</span>
          <div class="demo-stats">
            <div class="stat-item">
              <span class="stat-num">{{ summary.conditions.length }}</span>
              <span class="stat-label">Conditions</span>
            </div>
            <div class="stat-divider"/>
            <div class="stat-item">
              <span class="stat-num">{{ summary.medications.length }}</span>
              <span class="stat-label">Medications</span>
            </div>
            <div class="stat-divider"/>
            <div class="stat-item">
              <span class="stat-num">{{ summary.latest_observations.length }}</span>
              <span class="stat-label">Observations</span>
            </div>
            <div class="stat-divider"/>
            <div class="stat-item">
              <span class="stat-num">{{ summary.encounters.length }}</span>
              <span class="stat-label">Encounters</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: activeTab === 'summary' }" @click="onTabChange('summary')">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="12" height="12" rx="2"/><path d="M5 6h6M5 9h4" stroke-linecap="round"/></svg>
          Summary
        </button>
        <button :class="{ active: activeTab === 'timeline' }" @click="onTabChange('timeline')">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 2" stroke-linecap="round"/></svg>
          Timeline
          <span v-if="timeline" class="tab-count">{{ timeline.events.length }}</span>
        </button>
        <button :class="{ active: activeTab === 'raw' }" @click="onTabChange('raw')">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 4l4 4-4 4M9 12h4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Raw FHIR
        </button>
      </div>

      <!-- Summary tab -->
      <div v-if="activeTab === 'summary'" class="tab-content">
        <div class="two-col">
          <!-- Conditions -->
          <div class="card">
            <div class="card-heading">
              <h3>Conditions</h3>
              <span class="heading-count">{{ summary.conditions.length }}</span>
            </div>
            <table v-if="summary.conditions.length">
              <thead><tr><th>Condition</th><th>Status</th><th>Recorded</th></tr></thead>
              <tbody>
                <tr v-for="(c, i) in summary.conditions" :key="i" class="clickable-row" @click="openPanel(c, 'condition')">
                  <td>{{ conditionDisplay(c as Record<string, unknown>) }}</td>
                  <td>
                    <span v-if="(c as any).clinicalStatus?.coding?.[0]?.code" class="status-pill" :class="(c as any).clinicalStatus.coding[0].code === 'active' ? 'active' : 'inactive'">
                      {{ (c as any).clinicalStatus.coding[0].code }}
                    </span>
                    <span v-else class="status-pill inactive">—</span>
                  </td>
                  <td class="date-cell">{{ (c as Record<string, unknown>).recordedDate?.toString().slice(0, 10) || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-msg">No conditions recorded.</p>
          </div>

          <!-- Medications -->
          <div class="card">
            <div class="card-heading">
              <h3>Medications</h3>
              <span class="heading-count">{{ summary.medications.length }}</span>
            </div>
            <table v-if="summary.medications.length">
              <thead><tr><th>Medication</th><th>Status</th><th>Date</th></tr></thead>
              <tbody>
                <tr v-for="(m, i) in summary.medications" :key="i" class="clickable-row" @click="openPanel(m, 'medication')">
                  <td>{{ medDisplay(m as Record<string, unknown>) }}</td>
                  <td>
                    <span class="status-pill" :class="(m as Record<string,unknown>).status === 'active' ? 'active' : 'inactive'">
                      {{ (m as Record<string, unknown>).status }}
                    </span>
                  </td>
                  <td class="date-cell">{{ (m as Record<string, unknown>).authoredOn?.toString().slice(0, 10) || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-msg">No medications recorded.</p>
          </div>
        </div>

        <!-- Encounters -->
        <div class="card">
          <div class="card-heading">
            <h3>Encounters</h3>
            <span class="heading-count">{{ summary.encounters.length }}</span>
          </div>
          <table v-if="summary.encounters.length">
            <thead><tr><th>Type / Reason</th><th>Class</th><th>Date</th></tr></thead>
            <tbody>
              <tr v-for="(e, i) in summary.encounters" :key="i" class="clickable-row" @click="openPanel(e, 'encounter')">
                <td>{{ (e as any).type?.[0]?.coding?.[0]?.display ?? (e as any).type?.[0]?.text ?? (e as any).reasonCode?.[0]?.coding?.[0]?.display ?? 'Encounter' }}</td>
                <td>{{ ENC_CLASS_LABELS[(e as any).class?.code] ?? (e as any).class?.code ?? '—' }}</td>
                <td class="date-cell">{{ (e as any).period?.start?.slice(0, 10) ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-msg">No encounters recorded.</p>
        </div>

        <!-- Observations -->
        <div class="card" v-if="summary.latest_observations.length">
          <div class="card-heading">
            <h3>Latest Observations</h3>
            <span class="heading-count">{{ summary.latest_observations.length }}</span>
          </div>
          <div class="obs-grid">
            <div v-for="obs in summary.latest_observations" :key="obs.code" class="obs-card clickable-card" @click="openPanel(obs, 'observation' as any)">
              <div class="obs-label">{{ obs.display }}</div>
              <div class="obs-value">{{ obsValueDisplay(obs) }}</div>
              <div class="obs-footer">
                <span class="obs-date">{{ obs.date?.slice(0, 10) || '—' }}</span>
                <span v-if="obs.category" class="obs-category-pill">{{ obs.category }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline tab -->
      <div v-if="activeTab === 'timeline'" class="tab-content">
        <div v-if="timeline && timelineByYear.length" class="timeline-wrap card">
          <div v-for="group in timelineByYear" :key="group.year" class="tl-year-group">
            <div class="tl-year-label">{{ group.year }}</div>
            <div v-for="(ev, i) in group.events" :key="i" class="timeline-item tl-clickable" @click="openPanelFromTimeline(ev)">
              <div class="tl-dot" :style="{ background: EVENT_COLORS[ev.event_type] || '#94a3b8' }" />
              <div class="tl-body">
                <span class="tl-type-badge" :style="{ background: EVENT_BG[ev.event_type] || '#f1f5f9', color: EVENT_COLORS[ev.event_type] || '#64748b' }">
                  {{ ev.event_type }}
                </span>
                <span class="tl-date">{{ ev.date?.slice(0, 10) }}</span>
                <span class="tl-desc">{{ ev.description }}</span>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="empty-msg card">No timeline events found.</p>
      </div>

      <!-- Raw FHIR tab -->
      <div v-if="activeTab === 'raw'" class="tab-content">
        <div v-if="!rawResources" class="loading-state"><span class="spinner" /> Fetching raw resources…</div>
        <template v-else>
          <div v-for="(resources, rt) in rawResources" :key="rt" class="raw-section card">
            <div class="card-heading">
              <h4>{{ rt }}</h4>
              <span class="heading-count">{{ resources.length }}</span>
            </div>
            <pre class="raw-json">{{ JSON.stringify(resources, null, 2) }}</pre>
          </div>
        </template>
      </div>
    </template>

    <!-- Detail slide-out panel -->
    <Teleport to="body">
      <Transition name="panel">
        <div v-if="selectedItem" class="panel-overlay" @click.self="closePanel">
          <div class="detail-panel">
            <div class="panel-header">
              <h2 class="panel-title">
                {{
                selectedType === 'condition'  ? conditionDisplay(selectedItem) :
                selectedType === 'medication' ? medDisplay(selectedItem) :
                selectedType === 'encounter'  ? (encDetail(selectedItem).type ?? encDetail(selectedItem).reason ?? 'Encounter') :
                (selectedItem as any).display
              }}
              </h2>
              <button class="panel-close" @click="closePanel">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
              </button>
            </div>

            <!-- Condition detail -->
            <template v-if="selectedType === 'condition' && selectedItem">
              <div class="panel-body">
                <div v-for="([label, value]) in ([
                  ['Clinical Status',     conditionDetail(selectedItem).clinicalStatus],
                  ['Verification',        conditionDetail(selectedItem).verificationStatus],
                  ['Category',            conditionDetail(selectedItem).category],
                  ['Severity',            conditionDetail(selectedItem).severity],
                  ['Onset',               conditionDetail(selectedItem).onset],
                  ['Abatement',           conditionDetail(selectedItem).abatement],
                  ['Recorded',            conditionDetail(selectedItem).recorded],
                  ['SNOMED Code',         conditionDetail(selectedItem).snomedCode],
                ] as [string, string | undefined][])" :key="label" class="detail-row">
                  <span class="detail-label">{{ label }}</span>
                  <span class="detail-value" :class="{ empty: !value }">{{ value || '—' }}</span>
                </div>
                <div v-if="conditionDetail(selectedItem).notes.length" class="detail-notes">
                  <span class="detail-label">Notes</span>
                  <p v-for="(note, i) in conditionDetail(selectedItem).notes" :key="i" class="note-text">{{ note }}</p>
                </div>
              </div>
            </template>

            <!-- Medication detail -->
            <template v-else-if="selectedType === 'medication' && selectedItem">
              <div class="panel-body">
                <div v-for="([label, value]) in ([
                  ['Status',          medDetail(selectedItem).status],
                  ['Intent',          medDetail(selectedItem).intent],
                  ['Authored',        medDetail(selectedItem).authored],
                  ['Dosage',          medDetail(selectedItem).dosageText],
                  ['Route',           medDetail(selectedItem).route],
                  ['Dose',            medDetail(selectedItem).dose],
                  ['Timing',          medDetail(selectedItem).timing],
                  ['Reason',          medDetail(selectedItem).reasonCode],
                  ['Prescribed by',   medDetail(selectedItem).requester],
                  ['Quantity',        medDetail(selectedItem).quantity],
                  ['Refills',         medDetail(selectedItem).refills?.toString()],
                  ['RxNorm Code',     medDetail(selectedItem).rxNormCode],
                ] as [string, string | undefined][])" :key="label" class="detail-row">
                  <span class="detail-label">{{ label }}</span>
                  <span class="detail-value" :class="{ empty: !value }">{{ value || '—' }}</span>
                </div>
                <div v-if="medDetail(selectedItem).notes.length" class="detail-notes">
                  <span class="detail-label">Notes</span>
                  <p v-for="(note, i) in medDetail(selectedItem).notes" :key="i" class="note-text">{{ note }}</p>
                </div>
              </div>
            </template>

            <!-- Observation detail -->
            <template v-else-if="selectedType === 'observation' && selectedItem">
              <div class="panel-body">
                <div v-for="([label, value]) in ([
                  ['LOINC Code',      (selectedItem as any).code],
                  ['Status',          obsDetail(selectedItem).status],
                  ['Category',        obsDetail(selectedItem).category],
                  ['Date',            (selectedItem as any).date?.slice(0, 10)],
                  ['Interpretation',  obsDetail(selectedItem).interpretation],
                  ['Reference Range', obsDetail(selectedItem).referenceRange],
                ] as [string, string | undefined][])" :key="label" class="detail-row">
                  <span class="detail-label">{{ label }}</span>
                  <span class="detail-value" :class="{ empty: !value }">{{ value || '—' }}</span>
                </div>
                <template v-if="obsDetail(selectedItem).components?.length">
                  <div class="detail-section-label">Components</div>
                  <div v-for="(comp, i) in obsDetail(selectedItem).components" :key="i" class="detail-row">
                    <span class="detail-label">{{ comp.display }}</span>
                    <span class="detail-value">{{ comp.value }}</span>
                  </div>
                </template>
                <div v-if="obsDetail(selectedItem).notes.length" class="detail-notes">
                  <span class="detail-label">Notes</span>
                  <p v-for="(note, i) in obsDetail(selectedItem).notes" :key="i" class="note-text">{{ note }}</p>
                </div>
              </div>
            </template>

            <!-- Encounter detail -->
            <template v-else-if="selectedType === 'encounter' && selectedItem">
              <div class="panel-body">
                <div v-for="([label, value]) in ([
                  ['Status',           encDetail(selectedItem).status],
                  ['Class',            encDetail(selectedItem).class],
                  ['Type',             encDetail(selectedItem).type],
                  ['Reason',           encDetail(selectedItem).reason],
                  ['Start',            encDetail(selectedItem).start],
                  ['End',              encDetail(selectedItem).end],
                  ['Location',         encDetail(selectedItem).location],
                  ['Service Provider', encDetail(selectedItem).serviceProvider],
                  ['Discharge',        encDetail(selectedItem).discharge],
                ] as [string, string | undefined][])" :key="label" class="detail-row">
                  <span class="detail-label">{{ label }}</span>
                  <span class="detail-value" :class="{ empty: !value }">{{ value || '—' }}</span>
                </div>
                <template v-if="encDetail(selectedItem).participants.length">
                  <div class="detail-section-label">Participants</div>
                  <div v-for="(p, i) in encDetail(selectedItem).participants" :key="i" class="detail-row">
                    <span class="detail-value">{{ p }}</span>
                  </div>
                </template>
                <template v-if="encDetail(selectedItem).diagnoses.length">
                  <div class="detail-section-label">Diagnoses</div>
                  <div v-for="(d, i) in encDetail(selectedItem).diagnoses" :key="i" class="detail-row">
                    <span class="detail-value">{{ d }}</span>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.detail-page { max-width: 1000px; margin: 0 auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-secondary);
  cursor: pointer;
  width: fit-content;
  padding: 4px 0;
}
.back-link:hover { color: var(--c-primary); }
.back-link svg { width: 14px; height: 14px; }

.loading-state, .error-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 60px;
  color: var(--c-muted);
  justify-content: center;
  font-size: 14px;
}
.error-state { color: var(--c-danger); }
.error-state svg { width: 18px; height: 18px; flex-shrink: 0; }

/* Demographics */
.demographics { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; flex-wrap: wrap; }
.demo-left { display: flex; align-items: flex-start; gap: 16px; }
.avatar-lg {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 20px;
  flex-shrink: 0;
}
.demo-info { display: flex; flex-direction: column; gap: 8px; }
.patient-name { margin: 0; font-size: 22px; font-weight: 700; line-height: 1.2; letter-spacing: -0.3px; }
.demo-pills { display: flex; flex-wrap: wrap; gap: 6px; }
.demo-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--c-tag-bg);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 3px 9px;
  font-size: 12px;
  color: var(--c-text-secondary);
}
.demo-pill svg { width: 12px; height: 12px; }
.demo-pill.highlight { background: var(--c-primary-light); color: var(--c-primary); border-color: #bfdbfe; font-weight: 600; }

.demo-right { display: flex; flex-direction: column; align-items: flex-end; gap: 14px; }
.demo-stats { display: flex; align-items: center; gap: 20px; background: var(--c-tag-bg); border-radius: 10px; padding: 10px 20px; border: 1px solid var(--c-border); }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.stat-num { font-size: 20px; font-weight: 700; color: var(--c-text); line-height: 1; }
.stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--c-muted); }
.stat-divider { width: 1px; height: 28px; background: var(--c-border); }

/* Tabs */
.tabs {
  display: flex;
  gap: 2px;
  border-bottom: 2px solid var(--c-border);
}
.tabs button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-muted);
  margin-bottom: -2px;
  transition: color 0.15s;
}
.tabs button svg { width: 14px; height: 14px; }
.tabs button:hover { color: var(--c-text); background: none; }
.tabs button.active { color: var(--c-primary); border-bottom-color: var(--c-primary); }
.tab-count {
  background: var(--c-tag-bg);
  border-radius: 999px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-muted);
}
.tabs button.active .tab-count { background: var(--c-primary-light); color: var(--c-primary); }

.tab-content { display: flex; flex-direction: column; gap: 16px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.card-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.card-heading h3, .card-heading h4 { margin: 0; font-size: 14px; font-weight: 700; }
.heading-count {
  background: var(--c-tag-bg);
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-muted);
}

.date-cell { color: var(--c-muted); font-size: 12px; white-space: nowrap; }

.status-pill {
  display: inline-block;
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 11px;
  font-weight: 600;
}
.status-pill.active { background: var(--c-success-light); color: #15803d; }
.status-pill.inactive { background: var(--c-tag-bg); color: var(--c-muted); }

.empty-msg { color: var(--c-muted); font-size: 13px; margin: 0; }

/* Observations grid */
.obs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}
.obs-card {
  background: var(--c-tag-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.obs-label { font-size: 11px; color: var(--c-muted); text-transform: uppercase; letter-spacing: 0.3px; line-height: 1.3; }
.obs-value { font-size: 18px; font-weight: 700; color: var(--c-text); line-height: 1.2; }
.obs-footer { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-top: 2px; }
.obs-date { font-size: 11px; color: var(--c-muted); }
.obs-category-pill {
  font-size: 10px;
  font-weight: 500;
  color: var(--c-accent);
  background: color-mix(in srgb, var(--c-accent) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--c-accent) 25%, transparent);
  border-radius: 99px;
  padding: 1px 7px;
  white-space: nowrap;
  text-transform: lowercase;
}

/* Timeline */
.timeline-wrap { padding: 20px; }
.tl-year-group { margin-bottom: 20px; }
.tl-year-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--c-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--c-border);
}
.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 6px 0;
  position: relative;
}
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 20px;
  bottom: -6px;
  width: 2px;
  background: var(--c-border);
}
.tl-dot {
  width: 14px; height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
  box-shadow: 0 0 0 3px var(--c-surface);
}
.tl-body {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13px;
  flex: 1;
}
.tl-type-badge {
  display: inline-block;
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.tl-date { color: var(--c-muted); font-size: 12px; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tl-clickable { cursor: pointer; border-radius: 6px; padding-left: 4px; padding-right: 4px; margin-left: -4px; transition: background 0.1s; }
.tl-clickable:hover { background: var(--c-tag-bg); }
.tl-desc { color: var(--c-text-secondary); flex: 1; }

/* Raw FHIR */
.raw-section { gap: 0; }
.raw-json {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: var(--radius-sm);
  padding: 14px;
  font-size: 11px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  overflow: auto;
  max-height: 400px;
  white-space: pre;
  margin: 0;
  line-height: 1.6;
}

/* Clickable rows / cards */
.clickable-row { cursor: pointer; transition: background 0.1s; }
.clickable-row:hover { background: var(--c-tag-bg); }
.clickable-card { cursor: pointer; transition: box-shadow 0.15s, border-color 0.15s; }
.clickable-card:hover { border-color: var(--c-primary); box-shadow: 0 0 0 2px var(--c-primary-light); }

.detail-section-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--c-muted);
  padding: 14px 0 4px;
}

/* Slide-out panel */
.panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}
.detail-panel {
  width: 380px;
  max-width: 92vw;
  height: 100%;
  background: var(--c-surface);
  border-left: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--c-border);
}
.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--c-text);
}
.panel-close {
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 4px;
  color: var(--c-muted);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel-close:hover { background: var(--c-tag-bg); color: var(--c-text); }
.panel-close svg { width: 14px; height: 14px; }

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--c-border);
  font-size: 13px;
}
.detail-row:last-child { border-bottom: none; }
.detail-label {
  color: var(--c-muted);
  font-size: 12px;
  flex-shrink: 0;
  min-width: 100px;
}
.detail-value { color: var(--c-text); text-align: right; }
.detail-value.empty { color: var(--c-muted); }
.detail-notes {
  padding: 12px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.note-text {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-secondary);
  line-height: 1.5;
  background: var(--c-tag-bg);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}

/* Panel transition */
.panel-enter-active, .panel-leave-active { transition: opacity 0.2s; }
.panel-enter-active .detail-panel, .panel-leave-active .detail-panel { transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.panel-enter-from, .panel-leave-to { opacity: 0; }
.panel-enter-from .detail-panel, .panel-leave-to .detail-panel { transform: translateX(100%); }

@media (max-width: 640px) {
  .two-col { grid-template-columns: 1fr; }
  .demographics { flex-direction: column; }
  .demo-right { align-items: flex-start; }
}
</style>
