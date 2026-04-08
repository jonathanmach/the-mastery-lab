<script setup>
import { formatLargeNumber } from '../utils/format.js'
import InfoTooltip from './InfoTooltip.vue'


const props = defineProps({
  rateLimitingEnabled: Boolean,
  rawAttemptsPerDay: Number,
  perIpPerDay: Number,
  perUserPerDay: Number,
  perDevicePerDay: Number,
  parallelIps: Number,
  effectivePerIpLimit: Number,
  totalAttemptsPerDay: Number,
})


const emit = defineEmits([
  'update:rateLimitingEnabled',
  'update:rawAttemptsPerDay',
  'update:perIpPerDay',
  'update:perUserPerDay',
  'update:perDevicePerDay',
  'update:parallelIps',
])

const limits = [
  {
    label: 'Per IP / day',
    prop: 'perIpPerDay',
    event: 'update:perIpPerDay',
    tip: 'Max attempts allowed from a single IP address per day. A common default is 5–10. Attackers can bypass this by rotating IPs — see "Parallel IPs" below.',
  },
  {
    label: 'Per user / day (not modelled — bypassable by registering multiple accounts)',
    prop: 'perUserPerDay',
    event: 'update:perUserPerDay',
    tip: 'Max attempts allowed against a single user account per day, regardless of how many IPs are used. This is the most important limit — it caps total exposure per account even against distributed attacks.',
    disabled: true,
  },
  {
    label: 'Per device / fingerprint / day',
    prop: 'perDevicePerDay',
    event: 'update:perDevicePerDay',
    tip: 'Max attempts per browser fingerprint or device ID per day. Less reliable than IP or user limits since fingerprints can be spoofed, but adds another layer against unsophisticated attackers.',
  },
]

const parallelIpsTip = `The number of distinct IP addresses the attacker controls simultaneously.

Since rate limiting is per-IP, an attacker with N IPs can make N × (per-IP limit) attempts per day while each individual IP stays under the limit.

• Script Kiddie: ~10 IPs (a single botnet node or VPN rotation)
• Organised Crime: ~1,000 IPs (a small botnet or cloud burst)
• Nation-State: ~1,000,000 IPs (large-scale infrastructure)

The effective attack rate is bounded by whichever is lower: IP throughput or the aggregate per-user ceiling across all targeted accounts.`

const rawTip = `Total guesses per day the attacker can make with no throttling.

Useful reference points:
• 1,000,000,000 (1B/day) ≈ 11,574/sec — fast unthrottled web endpoint
• 86,400,000,000 (86.4B/day) ≈ 1,000,000/sec — local hash cracking (e.g. MD5 on a GPU)
• 8,640,000,000,000 (8.6T/day) ≈ 100,000,000/sec — bcrypt is ~1,000× slower; use a lower number for well-hashed passwords`
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">

    <!-- Header + toggle -->
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">
        Rate Limiting Configuration
      </h2>
      <button
        @click="emit('update:rateLimitingEnabled', !rateLimitingEnabled)"
        :class="[
          'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent',
          'transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900',
          rateLimitingEnabled ? 'bg-indigo-600' : 'bg-gray-700'
        ]"
        role="switch"
        :aria-checked="rateLimitingEnabled"
        type="button"
      >
        <span
          :class="[
            'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200',
            rateLimitingEnabled ? 'translate-x-4' : 'translate-x-0'
          ]"
        />
      </button>
    </div>

    <!-- Disabled state: raw rate input -->
    <template v-if="!rateLimitingEnabled">
      <div class="rounded-lg border border-amber-800/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-300">
        Rate limiting is <strong>off</strong>. The attacker can guess at the raw rate below — no per-IP, per-user, or per-device throttling applies.
      </div>
      <div class="space-y-1.5">
        <label class="flex items-center gap-1.5 text-xs text-gray-400">
          Raw attempts / day
          <InfoTooltip :text="rawTip" />
        </label>
        <input
          type="number"
          min="1" step="1"
          :value="rawAttemptsPerDay"
          @input="emit('update:rawAttemptsPerDay', Math.max(1, Number($event.target.value)))"
          class="w-full bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 text-sm
                 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </template>

    <!-- Enabled state: normal rate limit inputs -->
    <template v-else>
      <!-- Three rate limit inputs -->
      <div class="space-y-3">
        <div v-for="limit in limits" :key="limit.prop" class="space-y-1">
          <label class="flex items-center gap-1.5 text-xs text-gray-400">
            {{ limit.label }}
            <InfoTooltip :text="limit.tip" />
          </label>
          <input
            type="number"
            min="0" step="1"
            :value="props[limit.prop]"
            :disabled="limit.disabled"
            @input="emit(limit.event, Math.max(0, Number($event.target.value)))"
            :class="[
              'w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500',
              limit.disabled
                ? 'bg-gray-800/40 border-gray-700/50 text-gray-600 cursor-not-allowed'
                : 'bg-gray-800 border-gray-700 text-white'
            ]"
          />
        </div>
      </div>

      <!-- Parallel IPs -->
      <div class="space-y-1.5">
        <label class="flex items-center gap-1.5 text-xs text-gray-400">
          Parallel IPs / Attackers
          <InfoTooltip :text="parallelIpsTip" />
        </label>
        <input
          type="number"
          min="1" step="1"
          :value="parallelIps"
          @input="emit('update:parallelIps', Math.max(1, Number($event.target.value)))"
          class="w-full bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 text-sm
                 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </template>

    <!-- Total attack rate — always visible -->
    <div class="border-t border-gray-800 pt-3 text-sm">
      <span class="text-gray-400">Total attack rate: </span>
      <span class="text-white font-mono font-medium">
        {{ formatLargeNumber(totalAttemptsPerDay) }} attempts/day
      </span>
    </div>
  </div>
</template>
