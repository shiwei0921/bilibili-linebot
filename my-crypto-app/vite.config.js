import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      "bilibili-linebot.onrender.com"  // <== ✅ 改成你現在 ngrok 的網址
    ],
    headers: {
      'X-Frame-Options': 'ALLOWALL',
      'Content-Security-Policy': 'frame-ancestors *'
    }
  }
})
