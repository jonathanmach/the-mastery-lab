<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart,
  BarElement, LineElement, PointElement, ArcElement,
  CategoryScale, LinearScale, Tooltip, Legend,
} from 'chart.js'
import { Bar, Line, Pie } from 'vue-chartjs'
import type { ChartSpec } from '../api/types'

Chart.register(BarElement, LineElement, PointElement, ArcElement, CategoryScale, LinearScale, Tooltip, Legend)

const PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1', '#14b8a6', '#fb923c',
]

const props = defineProps<{
  spec: ChartSpec
  results: Record<string, unknown>[]
}>()

const rows = computed(() =>
  props.spec.type === 'pie' ? props.results.slice(0, 50) : props.results
)

const chartData = computed(() => ({
  labels: rows.value.map(r => String(r[props.spec.label_column] ?? '')),
  datasets: [{
    label: props.spec.value_column,
    data: rows.value.map(r => Number(r[props.spec.value_column] ?? 0)),
    backgroundColor: PALETTE,
    borderColor: props.spec.type === 'line' ? PALETTE[0] : PALETTE,
    borderWidth: props.spec.type === 'line' ? 2 : 1,
    fill: false,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  plugins: {
    legend: { display: props.spec.type === 'pie' },
    tooltip: { enabled: true },
  },
  scales: props.spec.type !== 'pie'
    ? { x: { ticks: { maxRotation: 45 } }, y: { beginAtZero: true } }
    : {},
}))
</script>

<template>
  <div class="chart-wrap">
    <div v-if="!results.length" class="chart-empty">No data to display</div>
    <template v-else>
      <div v-if="spec.type === 'pie' && results.length > 50" class="chart-cap-warning">
        Showing first 50 slices of {{ results.length }}
      </div>
      <div class="chart-canvas-wrap">
        <Bar v-if="spec.type === 'bar'" :data="chartData" :options="chartOptions" />
        <Line v-else-if="spec.type === 'line'" :data="chartData" :options="chartOptions" />
        <Pie v-else :data="chartData" :options="chartOptions" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.chart-wrap {
  margin-top: 4px;
}
.chart-canvas-wrap {
  height: 280px;
  position: relative;
}
.chart-empty {
  font-size: 13px;
  color: #94a3b8;
  font-style: italic;
  padding: 8px 0;
}
.chart-cap-warning {
  font-size: 11px;
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 4px;
  padding: 3px 8px;
  margin-bottom: 8px;
  width: fit-content;
}
</style>
