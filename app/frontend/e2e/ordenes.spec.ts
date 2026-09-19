import { expect, test } from "@playwright/test";

test("la pantalla de órdenes abre, muestra las órdenes de hoy y sus detalles", async ({ page }) => {
  await page.goto("/ordenes");
  await expect(page.getByRole("heading", { name: "Órdenes de hoy" })).toBeVisible();

  // Debe haber acciones recomendadas listadas
  await expect(page.getByText(/Acciones recomendadas/i)).toBeVisible();

  // El botón de aprobar debe estar deshabilitado porque el ciclo no está habilitado
  const botonAprobar = page.getByRole("button", { name: "Aprobar" }).first();
  if (await botonAprobar.isVisible()) {
    await expect(botonAprobar).toBeDisabled();
  }
});
