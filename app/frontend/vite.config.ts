import path from "node:path";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";

// En desarrollo, el frontend corre en 5173 y llama a la API en 8000 a través de este proxy,
// así que el código nunca escribe una URL absoluta. Compilado, lo sirve el mismo backend.
export default defineConfig({
  plugins: [react(), tailwind()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/pruebas/preparar.ts"],
    exclude: ["node_modules/**", "e2e/**"],
  },
});
