import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The API (FastAPI, port 8000 or API_PORT) is proxied under /api so the screen and the data share one origin.
const apiPort = process.env.API_PORT ?? "8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
    fs: { allow: [".."] }, // design/girlypop.css and design/sigils live one level up
  },
});
