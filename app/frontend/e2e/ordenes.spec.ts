import { expect, test } from "@playwright/test";

test("la pantalla de órdenes abre, muestra las órdenes de hoy y sus detalles", async ({ page }) => {
  await page.goto("/ordenes");
  await expect(page.getByRole("heading", { name: "Órdenes de hoy" })).toBeVisible();

  // Debe haber acciones recomendadas listadas
  await expect(page.getByText(/Acciones recomendadas/i)).toBeVisible();

  // La aprobación vive solo en Trabajos: no hay botones Aprobar/Rechazar muertos en esta pantalla.
  await expect(page.getByRole("button", { name: "Aprobar" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Rechazar" })).toHaveCount(0);
});
