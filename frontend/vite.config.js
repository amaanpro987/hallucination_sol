import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/sources": "http://localhost:8000",
      "/verify": "http://localhost:8000",
      "/runs": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
      "/evaluation": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
