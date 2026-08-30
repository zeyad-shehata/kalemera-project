import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: path.resolve(fileURLToPath(new URL('.', import.meta.url)), '../dist'),
    emptyOutDir: true,
  },
  server: {
    host: true,
    port: 5173,
  },
  resolve: {
    alias: {
      '@': path.resolve(fileURLToPath(new URL('.', import.meta.url)), './src'),
    },
  },
})

