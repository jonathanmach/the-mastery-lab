<script setup lang="ts">
import type { PatientHit } from '../api/types'
import { RouterLink } from 'vue-router'

defineProps<{ patient: PatientHit }>()
</script>

<template>
  <RouterLink :to="`/patients/${patient.patient_id}`" class="patient-card">
    <div class="card-top">
      <span class="patient-name">{{ patient.name }}</span>
      <span class="badge" :class="patient.validation_status">{{ patient.validation_status }}</span>
    </div>
    <div class="card-meta">
      <span v-if="patient.gender">{{ patient.gender }}</span>
      <span v-if="patient.birth_date">· {{ patient.birth_date }}</span>
      <span v-if="patient.age_band" class="tag">{{ patient.age_band }}</span>
    </div>
    <div v-if="patient.conditions.length" class="card-tags">
      <span v-for="c in patient.conditions.slice(0, 3)" :key="c" class="tag">{{ c }}</span>
      <span v-if="patient.conditions.length > 3" class="tag muted">+{{ patient.conditions.length - 3 }} more</span>
    </div>
    <div class="card-footer">
      <span v-if="patient.last_encounter_date" class="meta-item">
        Last encounter: {{ patient.last_encounter_date }}
      </span>
      <span v-if="patient.has_active_medication" class="meta-item active-med">Active Rx</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.patient-card {
  display: block;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 14px 16px;
  color: var(--c-text);
  text-decoration: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.patient-card:hover {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px rgba(13,110,253,0.1);
  text-decoration: none;
}
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.patient-name { font-weight: 600; font-size: 15px; }
.card-meta { font-size: 13px; color: var(--c-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.tag.muted { color: var(--c-muted); }
.card-footer { display: flex; gap: 12px; font-size: 12px; color: var(--c-muted); }
.active-med { color: var(--c-success); font-weight: 600; }
</style>
