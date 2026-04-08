<script setup>
import { computed } from 'vue'
import { formatLargeNumber, formatDuration } from '../utils/format.js'

const props = defineProps({
  keyspaceBigInt: BigInt,
  charsetSize: Number,
  tokenLength: Number,
  additionalEntropy: Number,
  numberOfSecrets: Number,
  totalAttemptsPerDay: Number,
  daysToCrack: Number,
  yearsToCrack: Number,
  securityTier: String,
  cosmicContext: String,
})

const tierConfig = {
  green: {
    border:    'border-green-500',
    bg:        'bg-green-900/20',
    text:      'text-green-400',
    glow:      'shadow-green-900/40',
    label:     'SECURE',
    dot:       'bg-green-500',
  },
  amber: {
    border:    'border-amber-500',
    bg:        'bg-amber-900/20',
    text:      'text-amber-400',
    glow:      'shadow-amber-900/40',
    label:     'AT RISK',
    dot:       'bg-amber-500',
  },
  red: {
    border:    'border-red-500',
    bg:        'bg-red-900/20',
    text:      'text-red-400',
    glow:      'shadow-red-900/40',
    label:     'VULNERABLE',
    dot:       'bg-red-500',
  },
}

const tier = computed(() => tierConfig[props.securityTier] ?? tierConfig.red)

// Build a readable formula string
const formula = computed(() => {
  const ks = formatLargeNumber(props.keyspaceBigInt)
  const rate = formatLargeNumber(props.totalAttemptsPerDay)
  const d = formatLargeNumber(props.daysToCrack)
  const dur = formatDuration(props.daysToCrack)
  const expectedGuesses = formatLargeNumber(
    (Number(props.keyspaceBigInt) + 1) / (props.numberOfSecrets + 1)
  )
  return {
    ks,
    rate,
    expectedGuesses,
    result: `${d} days`,
    pretty: dur,
  }
})

const keyspaceExpr = computed(() => {
  const cs = props.charsetSize
  const len = props.tokenLength
  const ae = props.additionalEntropy
  let expr = `${cs}^${len}`
  if (ae > 1) expr += ` × ${formatLargeNumber(ae)}`
  return expr
})

</script>

<template>
  <div :class="[
    'border-2 rounded-xl p-6 space-y-5 shadow-lg transition-all duration-300',
    tier.border, tier.bg, tier.glow
  ]">

    <!-- Header row -->
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">
        Time to Crack (average case)
      </h2>
      <div class="flex items-center gap-2">
        <div :class="['w-2.5 h-2.5 rounded-full animate-pulse', tier.dot]" />
        <span :class="['text-xs font-bold tracking-widest', tier.text]">
          {{ tier.label }}
        </span>
      </div>
    </div>

    <!-- Main duration -->
    <div :class="['text-4xl font-bold font-mono', tier.text]">
      {{ formatDuration(daysToCrack) }}
    </div>

    <!-- Formula -->
    <div class="font-mono text-xs text-gray-400 bg-gray-950/60 rounded-lg px-4 py-3 leading-relaxed space-y-1">
      <div>
        <span class="text-gray-500">keyspace  =</span>
        <span class="text-gray-200 ml-1">{{ keyspaceExpr }}</span>
        <span class="text-gray-500 ml-1">= {{ formula.ks }}</span>
      </div>
      <div>
        <span class="text-gray-500">E[guesses] =</span>
        <span class="text-gray-200 ml-1">(K + 1) / (M + 1)</span>
        <span class="text-gray-500 ml-1">= {{ formula.ks }} / {{ numberOfSecrets + 1 }}</span>
        <span class="text-gray-500 ml-1">= </span>
        <span class="text-gray-200">{{ formula.expectedGuesses }}</span>
      </div>
      <div>
        <span class="text-gray-500">time      =</span>
        <span class="text-gray-200 ml-1">{{ formula.expectedGuesses }}</span>
        <span class="text-gray-500 ml-1">÷</span>
        <span class="text-gray-200 ml-1">{{ formula.rate }}/day</span>
        <span class="text-gray-500 ml-1">≈</span>
        <span :class="['ml-1 font-semibold', tier.text]">{{ formula.result }}</span>
      </div>
    </div>

    <!-- Cosmic context -->
    <p class="text-sm text-gray-500 italic">
      {{ cosmicContext }}
    </p>

  </div>
</template>
