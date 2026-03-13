import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/public': 'http://localhost:8004',
      '/media': 'http://localhost:8004',
    },
  },
})
