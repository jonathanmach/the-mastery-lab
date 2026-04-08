<script setup>
import { computed } from 'vue'
import { formatBits } from '../utils/format.js'

const props = defineProps({
  entropyBits: Number,
  meetsNist: Boolean,
})

// Clamp to [0, 256] for bar display
const clampedBits = computed(() => Math.min(256, Math.max(0, props.entropyBits)))

// Each zone as a percentage of the 256-bit total bar
// Red: 0–56, Orange: 56–80, Amber: 80–112, Green: 112–256
const zones = [
  { label: 'Critical', color: 'bg-red-600',    from: 0,   to: 56  },
  { label: 'Weak',     color: 'bg-orange-500', from: 56,  to: 80  },
  { label: 'Fair',     color: 'bg-amber-400',  from: 80,  to: 112 },
  { label: 'Strong',   color: 'bg-green-500',  from: 112, to: 256 },
]

// The fill progress as a percentage
const fillPercent = computed(() => (clampedBits.value / 256) * 100)

// NIST marker position (112/256 = 43.75%)
const nistPercent = (112 / 256) * 100

// Tick marks at key entropy values
const ticks = [
  { bits: 40,  label: '40' },
  { bits: 56,  label: '56' },
  { bits: 80,  label: '80' },
  { bits: 112, label: '112' },
  { bits: 128, label: '128' },
  { bits: 256, label: '256' },
]

// Current fill color based on zone
const fillColor = computed(() => {
  const b = clampedBits.value
  if (b < 56)  return 'bg-red-600'
  if (b < 80)  return 'bg-orange-500'
  if (b < 112) return 'bg-amber-400'
  return 'bg-green-500'
})

const fillTextColor = computed(() => {
  const b = clampedBits.value
  if (b < 56)  return 'text-red-400'
  if (b < 80)  return 'text-orange-400'
  if (b < 112) return 'text-amber-400'
  return 'text-green-400'
})
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
    <div class="flex items-baseline justify-between">
      <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">Entropy</h2>
      <span :class="['text-2xl font-bold font-mono', fillTextColor]">
        {{ formatBits(entropyBits) }} bits
      </span>
    </div>

    <!-- Segmented bar -->
    <div class="relative">
      <!-- Zone background segments -->
      <div class="flex h-4 rounded-full overflow-hidden">
        <div v-for="zone in zones" :key="zone.label"
          :class="['opacity-20', zone.color]"
          :style="{ width: `${((zone.to - zone.from) / 256) * 100}%` }"
        />
      </div>

      <!-- Fill overlay -->
      <div class="absolute inset-0 flex h-4 rounded-full overflow-hidden">
        <div :class="['transition-all duration-300', fillColor]"
          :style="{ width: `${fillPercent}%` }"
        />
      </div>

      <!-- NIST marker line -->
      <div class="absolute top-0 bottom-0 w-0.5 bg-white/60"
        :style="{ left: `${nistPercent}%` }"
      />
    </div>

    <!-- Tick labels -->
    <div class="relative h-4 text-xs text-gray-500">
      <span v-for="tick in ticks" :key="tick.bits"
        class="absolute -translate-x-1/2"
        :style="{ left: `${(tick.bits / 256) * 100}%` }"
      >{{ tick.label }}</span>
    </div>

    <!-- NIST label + badge -->
    <div class="flex items-center justify-between pt-1">
      <span class="text-xs text-gray-500">
        NIST SP 800-63B minimum: 112 bits
      </span>
      <span :class="[
        'text-xs font-medium px-2 py-0.5 rounded-full',
        meetsNist
          ? 'bg-green-900/60 text-green-300 border border-green-700'
          : 'bg-red-900/60 text-red-300 border border-red-700'
      ]">
        {{ meetsNist ? '✓ Meets NIST' : '✗ Below NIST' }}
      </span>
    </div>
  </div>
</template>
