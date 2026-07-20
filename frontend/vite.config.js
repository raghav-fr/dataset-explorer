import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /api requests to the local FastAPI backend during development.
    // On Vercel, both app and API share the same origin so no proxy is needed.
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  // Expose env variables prefixed with VITE_ to the browser bundle.
  // VITE_API_BASE_URL is used in production when the API lives on a different domain.
  define: {
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL || ""),
  },
});
