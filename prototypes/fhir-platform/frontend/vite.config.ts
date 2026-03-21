import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/patients': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
