<script setup lang="ts">
import type { PatientHit } from '../api/types'
import { RouterLink } from 'vue-router'
import { computed } from 'vue'

const props = defineProps<{ patient: PatientHit }>()

const AVATAR_COLORS = [
  ['#dbeafe', '#1d4ed8'], ['#dcfce7', '#15803d'], ['#fce7f3', '#9d174d'],
  ['#fef3c7', '#92400e'], ['#ede9fe', '#6d28d9'], ['#ffedd5', '#c2410c'],
  ['#e0f2fe', '#0369a1'], ['#f0fdf4', '#166534'],
]

const avatarStyle = computed(() => {
  let hash = 0
  for (const ch of props.patient.name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffff
  const [bg, fg] = AVATAR_COLORS[hash % AVATAR_COLORS.length]
  return { background: bg, color: fg }
})

const initials = computed(() => {
  const parts = props.patient.name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return parts[0].slice(0, 2).toUpperCase()
})

const genderIcon = computed(() => {
  if (props.patient.gender === 'male') return '♂'
  if (props.patient.gender === 'female') return '♀'
  return null
})

const formattedDate = computed(() => {
  if (!props.patient.last_encounter_date) return null
  return props.patient.last_encounter_date.slice(0, 10)
})
</script>

<template>
  <RouterLink :to="`/patients/${patient.patient_id}`" class="patient-card">
    <div class="card-header">
      <div class="avatar" :style="avatarStyle">{{ initials }}</div>
      <div class="card-identity">
        <span class="patient-name">{{ patient.name }}</span>
        <span class="card-meta">
          <span v-if="genderIcon" class="gender-icon">{{ genderIcon }}</span>
          <span v-if="patient.gender" class="meta-text">{{ patient.gender }}</span>
          <span v-if="patient.birth_date" class="meta-sep">·</span>
          <span v-if="patient.birth_date" class="meta-text">{{ patient.birth_date }}</span>
          <span v-if="patient.age_band" class="meta-sep">·</span>
          <span v-if="patient.age_band" class="age-band">{{ patient.age_band }}</span>
        </span>
      </div>
      <span class="badge" :class="patient.validation_status">{{ patient.validation_status }}</span>
    </div>

    <div v-if="patient.conditions.length" class="card-conditions">
      <span v-for="c in patient.conditions.slice(0, 2)" :key="c" class="cond-tag">{{ c }}</span>
      <span v-if="patient.conditions.length > 2" class="cond-more">+{{ patient.conditions.length - 2 }}</span>
    </div>

    <div class="card-footer">
      <span v-if="formattedDate" class="footer-item">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="12" height="11" rx="1.5"/><path d="M5 1v3M11 1v3M2 7h12" stroke-linecap="round"/></svg>
        {{ formattedDate }}
      </span>
      <span v-if="patient.has_active_medication" class="footer-item rx-badge">
        <svg viewBox="0 0 16 16" fill="currentColor"><path d="M10 2H6a1 1 0 00-1 1v1H4a2 2 0 00-2 2v7a2 2 0 002 2h8a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 00-1-1zm-3 2h2v1H7V4zm1 4a1 1 0 110 2 1 1 0 010-2z"/></svg>
        Active Rx
      </span>
      <span v-if="patient.has_recent_encounter" class="footer-item recent-badge">Recent visit</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.patient-card {
  display: block;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  color: var(--c-text);
  text-decoration: none;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
  box-shadow: var(--shadow-sm);
}
.patient-card:hover {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  text-decoration: none;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.card-identity {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.patient-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--c-muted);
  flex-wrap: wrap;
}
.gender-icon { font-size: 13px; }
.meta-text { color: var(--c-text-secondary); }
.meta-sep { color: var(--c-muted); }
.age-band {
  background: var(--c-tag-bg);
  border-radius: 3px;
  padding: 0 5px;
  font-size: 11px;
  color: var(--c-text-secondary);
}

.card-conditions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}
.cond-tag {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--c-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.cond-more {
  background: var(--c-tag-bg);
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 11px;
  color: var(--c-muted);
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--c-border);
}
.footer-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--c-muted);
}
.footer-item svg { width: 12px; height: 12px; }
.rx-badge { color: var(--c-success); font-weight: 600; }
.recent-badge {
  margin-left: auto;
  background: var(--c-primary-light);
  color: var(--c-primary);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 600;
}
</style>
