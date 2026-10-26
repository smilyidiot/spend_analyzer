import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, proxy /api to the FastAPI backend (http://localhost:8000).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
