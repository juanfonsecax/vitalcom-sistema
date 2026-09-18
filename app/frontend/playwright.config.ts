import { defineConfig } from "@playwright/test";

/**
 * La prueba de punta a punta corre contra el backend sirviendo el frontend COMPILADO,
 * que es como lo va a ver el operador con iniciar.bat, y sobre la carpeta REAL del sistema
 * (VITALCOM_BASE). En un worktree el estado sale falso: faltan las Ads/MEDIA_*.
 */
const BASE = process.env.VITALCOM_BASE;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://127.0.0.1:8100" },
  webServer: {
    command: "uv run uvicorn vitalcom_app.main:app --host 127.0.0.1 --port 8100",
    cwd: "../backend",
    url: "http://127.0.0.1:8100/api/sistema",
    reuseExistingServer: false,
    env: BASE ? { VITALCOM_BASE: BASE } : {},
    timeout: 120_000,
  },
});
