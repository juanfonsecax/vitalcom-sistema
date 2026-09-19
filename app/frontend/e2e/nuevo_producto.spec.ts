import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * El asistente de alta, de punta a punta, contra la carpeta REAL del sistema.
 *
 * Se recorre hasta la tabla de precios y se compara contra `costear.py` en vivo, pero NO se
 * confirma el alta: eso escribiría en los CSV reales. El alta con escritura se prueba sobre
 * un sistema falso en `app/backend/tests/test_alta_por_la_app.py`.
 */
const BASE = process.env.VITALCOM_BASE || resolve(import.meta.dirname, "../../..");

const DESCRIPCION =
  "Serum facial con vitamina C al 20% y ácido hialurónico, frasco de 30 ml con gotero. " +
  "Uso: 3 gotas por la noche. Registro MSPAS en trámite. Proveedor local, entrega en 48 h.";

function costear(costo: string) {
  return JSON.parse(
    execFileSync("python", [`${BASE}/Ads/_TOOLS/costear.py`, costo, "--json"], { cwd: BASE, encoding: "utf8" }),
  );
}

test("el asistente muestra la tabla de Guatemala de costear.py sin escribir nada", async ({ page }) => {
  const productosAntes = readFileSync(`${BASE}/PRODUCTOS/_DIM_PRODUCTOS.csv`, "utf8");
  const esperado = costear("41");

  await page.goto("/nuevo");
  await page.getByPlaceholder("Ej.: Serum Vitamina C").fill("Serum de Prueba E2E");
  await page.getByLabel("Foto del producto").setInputFiles({
    name: "foto.png",
    mimeType: "image/png",
    buffer: Buffer.from("89504e470d0a1a0a", "hex"),
  });
  await page.getByRole("button", { name: "Siguiente →" }).click();

  await page.getByRole("textbox").fill(DESCRIPCION);
  await page.getByRole("button", { name: "Siguiente →" }).click();

  await page.getByLabel("Costo en quetzales").fill("41");
  const escalera = page.getByTestId("escalera");
  await expect(escalera).toBeVisible({ timeout: 15_000 });

  for (const fila of esperado.escalera) {
    await expect(escalera.getByText(`Q${String(fila.precio)}`, { exact: true })).toBeVisible();
  }
  const umbrales = page.getByTestId("umbrales");
  await expect(umbrales.getByText(`Q${String(esperado.cpa_break_even)}`, { exact: true })).toBeVisible();
  await expect(umbrales.getByText(`Q${String(esperado.cpa_objetivo)}`, { exact: true })).toBeVisible();
  if (esperado.criterio_de_fila !== "exacta") {
    await expect(page.getByTestId("aviso-fila")).toContainText(`Q${String(esperado.fila_usada)}`);
  }

  // Recorrer el asistente no escribe: el CSV real sigue idéntico.
  expect(readFileSync(`${BASE}/PRODUCTOS/_DIM_PRODUCTOS.csv`, "utf8")).toBe(productosAntes);
});
