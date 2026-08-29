import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiTarget =
  process.env.VITE_API_URL ||
  'http://a6126bb5e30104b1689ab6e198168212-1203948690.ap-southeast-2.elb.amazonaws.com'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1': {
        target: apiTarget.replace(/\/api\/v1\/?$/, ''),
        changeOrigin: true,
      },
    },
  },
})
