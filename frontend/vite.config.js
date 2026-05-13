import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@locales': path.resolve(__dirname, '../locales')
    }
  },
  server: {
    port: 3200,
    strictPort: true,
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:5201',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
