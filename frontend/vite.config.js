import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Forward REST API calls
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // Forward WebSockets
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true, // Crucial: tells Vite to proxy websockets
      }
    }
  }
})
