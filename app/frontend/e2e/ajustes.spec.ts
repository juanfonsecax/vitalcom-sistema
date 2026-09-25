import { expect, test } from "@playwright/test";

test("Ajustes muestra las tres secciones: Cuentas, FanPages y Sistema", async ({ page }) => {
  await page.goto("/ajustes");

  // CardTitle (shadcn) renderiza un <div>, no un <h*> (misma nota que dejó T4 en resultados.spec.ts).
  await expect(page.getByText("Cuentas publicitarias", { exact: true })).toBeVisible();
  await expect(page.getByText("FanPages", { exact: true })).toBeVisible();
  await expect(page.getByText("Sistema", { exact: true })).toBeVisible();

  // Esta carpeta (worktree) todavía no tiene _DIM_FANPAGES.csv: el estado vacío, no un error.
  await expect(
    page.getByText("Todavía no hay FanPages declaradas en _DIM_FANPAGES.csv."),
  ).toBeVisible();

  // Los enlaces de siempre siguen accesibles desde acá.
  await expect(page.getByRole("link", { name: "Órdenes de hoy" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Trabajos" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Salud del sistema" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Guía", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Nuevo producto" })).toBeVisible();

  // La carpeta sobre la que corre la app (GET /api/sistema).
  await expect(page.getByText(/^Corriendo sobre: /)).toBeVisible();
});
