import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: /api an das lokale Backend (uvicorn auf :8000) durchreichen.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
