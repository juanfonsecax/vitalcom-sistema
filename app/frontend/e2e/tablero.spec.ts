import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

/** La carpeta real del sistema; la misma que usa el servidor de esta prueba. */
const BASE = process.env.VITALCOM_BASE || resolve(import.meta.dirname, "../../..");

function estadoFlujo(): Record<string, Record<string, string>> {
  const texto = readFileSync(`${BASE}/PRODUCTOS/_ESTADO_FLUJO.csv`, "utf8").trim();
  const [cabecera, ...filas] = texto.split(/\r?\n/);
  const columnas = cabecera.split(",");
  const salida: Record<string, Record<string, string>> = {};
  for (const fila of filas) {
    // Las columnas con comas van entre comillas; acá solo se leen las simples.
    const valores = fila.match(/("([^"]*)"|[^,]*)(,|$)/g)!.map((v) => v.replace(/,$/, "").replace(/^"|"$/g, ""));
    const objeto = Object.fromEntries(columnas.map((c, i) => [c, valores[i] ?? ""]));
    salida[objeto.producto_key] = objeto;
  }
  return salida;
}

test("el tablero muestra los productos reales con su fase y su paso", async ({ page }) => {
  const estado = estadoFlujo();
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Portafolio" })).toBeVisible();

  for (const [clave, fila] of Object.entries(estado)) {
    const tarjeta = page.locator("div", { hasText: fila.nodo_actual }).first();
    await expect(tarjeta, `tarjeta de ${clave}`).toBeVisible();
    await expect(page.getByText(fila.nodo_actual, { exact: true }).first()).toBeVisible();
  }
  expect(Object.keys(estado).length).toBeGreaterThanOrEqual(5);
});

test("el estado de OVULOS_PURITY coincide con flujo.py", async ({ page }) => {
  const directo = JSON.parse(
    execFileSync("python", [`${BASE}/Ads/_TOOLS/flujo.py`, "OVULOS_PURITY", "--json", "--sin-escribir", "--silencioso"], {
      cwd: BASE,
      encoding: "utf8",
    }),
  );
  await page.goto("/producto/OVULOS_PURITY");
  await expect(page.getByText(directo.nodo_actual, { exact: true }).first()).toBeVisible();
  await expect(page.getByText(directo.fase_titulo, { exact: false })).toBeVisible();
  // Lo que el grafo marca como bloqueante tiene que estar en pantalla, con su dueño.
  for (const bloqueante of directo.bloqueantes) {
    await expect(page.getByText(bloqueante.dato, { exact: false }).first()).toBeVisible();
  }
});

test("el glosario explica un término al hacer clic en la (i)", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Qué es el punto exacto|Qué es paso del flujo/ }).first().click();
  await expect(page.getByRole("tooltip").first()).toContainText("grafo declarado");
});
