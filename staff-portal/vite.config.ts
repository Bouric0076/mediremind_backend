import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Allow external connections
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '9bcfa7a683f9.ngrok-free.app', // Allow ngrok host
      '.ngrok-free.app', // Allow any ngrok-free.app subdomain
      '.ngrok.io', // Allow any ngrok.io subdomain for future use
    ],
  },
})
