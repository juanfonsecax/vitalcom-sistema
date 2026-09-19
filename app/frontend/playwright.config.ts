import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

/**
 * La prueba de punta a punta corre contra el backend sirviendo el frontend COMPILADO,
 * que es como lo va a ver el operador con iniciar.bat, y sobre la carpeta REAL del sistema
 * (VITALCOM_BASE). En un worktree el estado sale falso: faltan las Ads/MEDIA_*.
 */
const BASE = process.env.VITALCOM_BASE || resolve(import.meta.dirname, "../..");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://127.0.0.1:8100" },
  webServer: {
    command: "uv run uvicorn vitalcom_app.main:app --host 127.0.0.1 --port 8100",
    cwd: "../backend",
    url: "http://127.0.0.1:8100/api/sistema",
    reuseExistingServer: false,
    // La base de datos de la app (DBOS) va a una carpeta temporal: la prueba no toca los datos del operador.
    env: { ...(BASE ? { VITALCOM_BASE: BASE } : {}), VITALCOM_DATOS: join(tmpdir(), "vitalcom-e2e-datos") },
    timeout: 120_000,
  },
});
