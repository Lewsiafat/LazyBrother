import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Override with: VITE_PORT=3000 npm run dev
    port: parseInt(process.env.VITE_PORT || '5173'),
  },
})
