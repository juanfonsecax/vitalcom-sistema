import { expect, test } from "@playwright/test";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

/** La carpeta sobre la que corre el servidor de esta prueba (ver playwright.config.ts). */
const BASE = process.env.VITALCOM_BASE || resolve(import.meta.dirname, "../../..");

test("Ajustes muestra las tres secciones: Cuentas, FanPages y Sistema", async ({ page }) => {
  await page.goto("/ajustes");

  // CardTitle (shadcn) renderiza un <div>, no un <h*> (misma nota que dejó T4 en resultados.spec.ts).
  await expect(page.getByText("Cuentas publicitarias", { exact: true })).toBeVisible();
  await expect(page.getByText("FanPages", { exact: true })).toBeVisible();
  await expect(page.getByText("Sistema", { exact: true })).toBeVisible();

  // Con _DIM_FANPAGES.csv se listan sus páginas; sin él, el estado vacío, nunca un error.
  const ruta = `${BASE}/PRODUCTOS/_DIM_FANPAGES.csv`;
  if (existsSync(ruta)) {
    const [cabecera, primera] = readFileSync(ruta, "utf8").trim().split(/\r?\n/);
    const nombre = primera.split(",")[cabecera.split(",").indexOf("pagina_nombre")];
    // La tabla y las tarjetas de celular se renderizan las dos; solo una está visible.
    await expect(page.getByText(nombre, { exact: true }).filter({ visible: true }).first()).toBeVisible();
  } else {
    await expect(
      page.getByText("Todavía no hay FanPages declaradas en _DIM_FANPAGES.csv."),
    ).toBeVisible();
  }

  // Los enlaces de siempre siguen accesibles desde acá. «Trabajos» existe dos veces desde
  // que subió al menú lateral (barra + grid de Sistema): el de acá es el del contenido.
  await expect(page.getByRole("link", { name: "Órdenes de hoy" })).toBeVisible();
  await expect(page.getByRole("main").getByRole("link", { name: "Trabajos" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Salud del sistema" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Guía", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Nuevo producto" })).toBeVisible();

  // La carpeta sobre la que corre la app (GET /api/sistema).
  await expect(page.getByText(/^Corriendo sobre: /)).toBeVisible();
});
