<script setup>
import { ref } from 'vue'

defineProps({ text: String })

const visible = ref(false)
</script>

<template>
  <span class="relative inline-flex items-center">
    <button
      @mouseenter="visible = true"
      @mouseleave="visible = false"
      @focus="visible = true"
      @blur="visible = false"
      class="w-3.5 h-3.5 rounded-full bg-gray-700 text-gray-400 text-[9px] font-bold
             flex items-center justify-center hover:bg-gray-600 hover:text-white
             transition-colors focus:outline-none focus:ring-1 focus:ring-indigo-500"
      aria-label="More information"
      type="button"
    >?</button>

    <Transition
      enter-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="absolute left-5 top-1/2 -translate-y-1/2 z-50
               w-64 bg-gray-800 border border-gray-600 rounded-lg
               px-3 py-2.5 text-xs text-gray-300 leading-relaxed shadow-xl"
      >
        {{ text }}
        <!-- Arrow -->
        <span class="absolute right-full top-1/2 -translate-y-1/2
                     border-4 border-transparent border-r-gray-600" />
      </div>
    </Transition>
  </span>
</template>
