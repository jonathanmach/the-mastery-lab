<script setup>
import { formatLargeNumber } from '../utils/format.js'

const props = defineProps({
  profiles: Array,
  activeProfileId: String,
})

const emit = defineEmits(['select'])

const profileStyles = {
  script_kiddie:   { active: 'bg-sky-700 border-sky-600 text-white',       inactive: 'border-sky-800 text-sky-400 hover:border-sky-600' },
  organized_crime: { active: 'bg-amber-700 border-amber-600 text-white',   inactive: 'border-amber-800 text-amber-400 hover:border-amber-600' },
  nation_state:    { active: 'bg-red-700 border-red-600 text-white',       inactive: 'border-red-800 text-red-400 hover:border-red-600' },
}
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
    <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">
      Attacker Profile Presets
    </h2>
    <div class="flex flex-wrap gap-3">
      <button
        v-for="profile in profiles"
        :key="profile.id"
        @click="emit('select', profile.id)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-medium border transition-all',
          activeProfileId === profile.id
            ? profileStyles[profile.id].active
            : profileStyles[profile.id].inactive
        ]"
      >
        {{ profile.label }}
        <span class="opacity-70 font-normal ml-1">
          ({{ formatLargeNumber(profile.parallelIps) }} IPs)
        </span>
      </button>
    </div>
    <p class="text-xs text-gray-600">
      Presets set the number of parallel IPs. You can override this in the rate limit panel.
    </p>
  </div>
</template>
