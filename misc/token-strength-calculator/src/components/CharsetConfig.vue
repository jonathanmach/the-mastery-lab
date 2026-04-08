<script setup>
import { computed } from 'vue'

const props = defineProps({
  charsetId: String,
  tokenLength: Number,
  additionalEntropy: Number,
  numberOfSecrets: Number,
  charsets: Array,
})

const emit = defineEmits([
  'update:charsetId',
  'update:tokenLength',
  'update:additionalEntropy',
  'update:numberOfSecrets',
])

const currentCharset = computed(() =>
  props.charsets.find(c => c.id === props.charsetId)
)

const dateOptions = [
  { label: 'None',       value: 1,      display: '1' },
  { label: 'mm-yyyy',    value: 1200,   display: '1,200' },
  { label: 'dd-mm-yyyy', value: 36500,  display: '36,500' },
]
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
    <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">
      Token / Password Configuration
    </h2>

    <!-- Charset selector -->
    <div class="space-y-1.5">
      <label class="text-xs text-gray-400">Character Set</label>
      <select
        :value="charsetId"
        @change="emit('update:charsetId', $event.target.value)"
        class="w-full bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 text-sm
               focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        <option v-for="cs in charsets" :key="cs.id" :value="cs.id">
          {{ cs.label }}
        </option>
      </select>
      <p class="text-xs text-gray-500">
        Charset size: <span class="text-indigo-400 font-mono">{{ currentCharset?.size }}</span> characters
      </p>
    </div>

    <!-- Token length -->
    <div class="space-y-1.5">
      <label class="text-xs text-gray-400">Token / Password Length</label>
      <div class="flex items-center gap-3">
        <input
          type="range"
          min="1" max="128" step="1"
          :value="tokenLength"
          @input="emit('update:tokenLength', Number($event.target.value))"
          class="flex-1 accent-indigo-500"
        />
        <input
          type="number"
          min="1" max="256"
          :value="tokenLength"
          @input="emit('update:tokenLength', Math.min(256, Math.max(1, Number($event.target.value))))"
          class="w-20 bg-gray-800 border border-gray-700 text-white rounded-md px-2 py-1.5 text-sm
                 font-mono text-center focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>

    <!-- Number of valid secrets -->
    <div class="space-y-1.5">
      <label class="text-xs text-gray-400">Number of Valid Secrets (M)</label>
      <input
        type="number"
        min="1" step="1"
        :value="numberOfSecrets"
        @input="emit('update:numberOfSecrets', Math.max(1, Math.floor(Number($event.target.value))))"
        class="w-full bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 text-sm
               font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      <p class="text-xs text-gray-500 leading-relaxed">
        How many valid tokens exist simultaneously.
        More valid targets = attacker hits one sooner.
        E.g. 1 = one reset token per user · 500 = 500 active sessions.
      </p>
    </div>

    <!-- Additional entropy: date format selector -->
    <div class="space-y-1.5">
      <label class="text-xs text-gray-400">Additional Date Entropy</label>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="opt in dateOptions"
          :key="opt.value"
          @click="emit('update:additionalEntropy', opt.value)"
          :class="[
            'flex flex-col items-center gap-0.5 px-3 py-2.5 rounded-lg border text-sm transition-all',
            additionalEntropy === opt.value
              ? 'bg-indigo-700 border-indigo-500 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
          ]"
        >
          <span class="font-mono font-semibold text-xs tracking-tight">{{ opt.label }}</span>
          <span class="text-xs opacity-60">~{{ opt.display }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
