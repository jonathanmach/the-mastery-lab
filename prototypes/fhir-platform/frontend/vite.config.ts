import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/patients': {
        target: 'http://api-server:8000',
        bypass(req) {
          // Let browser page navigations fall through to Vite's SPA handler
          if (req.headers.accept?.includes('text/html')) return req.url
        },
      },
      '/health': 'http://api-server:8000',
      '/omop': {
        target: 'http://api-server:8000',
        bypass(req) {
          if (req.headers.accept?.includes('text/html')) return req.url
        },
      },
    },
  },
})
