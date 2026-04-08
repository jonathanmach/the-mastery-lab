<script setup>
import { onMounted, ref } from 'vue'
import { useEntropy } from './composables/useEntropy.js'
import CharsetConfig   from './components/CharsetConfig.vue'
import RateLimitConfig from './components/RateLimitConfig.vue'
import AttackerProfile from './components/AttackerProfile.vue'
import EntropyBits     from './components/EntropyBits.vue'
import EntropyDisplay  from './components/EntropyDisplay.vue'

const {
  charsetId, tokenLength, additionalEntropy, numberOfSecrets,
  rateLimitingEnabled, rawAttemptsPerDay,
  perIpPerDay, perUserPerDay, perDevicePerDay,
  parallelIps, attackerProfileId,
  CHARSETS, ATTACKER_PROFILES,
  charsetSize, keyspaceBigInt, entropyBits,
  effectivePerIpLimit, totalAttemptsPerDay,
  daysToCrack, yearsToCrack,
  securityTier, meetsNist, cosmicContext,
  setAttackerProfile, toQueryParams, fromQueryParams,
} = useEntropy()

onMounted(() => {
  if (window.location.search) fromQueryParams(window.location.search)
})

const copied = ref(false)
function copyShareableLink() {
  const url = `${window.location.origin}${window.location.pathname}?${toQueryParams()}`
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100 py-10 px-4">
    <div class="max-w-4xl mx-auto space-y-6">

      <!-- Header -->
      <header class="text-center space-y-2 pb-2">
        <h1 class="text-3xl font-bold text-white tracking-tight">
          Token / Password Security Impact
        </h1>
        <p class="text-gray-500 text-sm max-w-xl mx-auto">
          Estimate how long a rate-limited brute-force attack would take against
          your token or password scheme. All math runs client-side.
        </p>
      </header>

      <!-- Inputs -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CharsetConfig
          v-model:charsetId="charsetId"
          v-model:tokenLength="tokenLength"
          v-model:additionalEntropy="additionalEntropy"
          v-model:numberOfSecrets="numberOfSecrets"
          :charsets="CHARSETS"
        />
        <RateLimitConfig
          v-model:rateLimitingEnabled="rateLimitingEnabled"
          v-model:rawAttemptsPerDay="rawAttemptsPerDay"
          v-model:perIpPerDay="perIpPerDay"
          v-model:perUserPerDay="perUserPerDay"
          v-model:perDevicePerDay="perDevicePerDay"
          v-model:parallelIps="parallelIps"
          :effectivePerIpLimit="effectivePerIpLimit"
          :totalAttemptsPerDay="totalAttemptsPerDay"
        />
      </div>

      <!-- Attacker presets -->
      <AttackerProfile
        :profiles="ATTACKER_PROFILES"
        :activeProfileId="attackerProfileId"
        @select="setAttackerProfile"
      />

      <!-- Entropy bar -->
      <EntropyBits
        :entropyBits="entropyBits"
        :meetsNist="meetsNist"
      />

      <!-- Main result -->
      <EntropyDisplay
        :keyspaceBigInt="keyspaceBigInt"
        :charsetSize="charsetSize"
        :tokenLength="tokenLength"
        :additionalEntropy="additionalEntropy"
        :numberOfSecrets="numberOfSecrets"
        :totalAttemptsPerDay="totalAttemptsPerDay"
        :daysToCrack="daysToCrack"
        :yearsToCrack="yearsToCrack"
        :securityTier="securityTier"
        :cosmicContext="cosmicContext"
      />

      <!-- Share -->
      <div class="flex justify-center pb-6">
        <button
          @click="copyShareableLink"
          class="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700
                 text-white font-medium text-sm transition-colors"
        >
          {{ copied ? '✓ Link copied!' : 'Copy Shareable Link' }}
        </button>
      </div>

    </div>
  </div>
</template>
