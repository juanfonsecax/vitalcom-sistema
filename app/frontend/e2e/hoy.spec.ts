import { expect, test } from "@playwright/test";

test("«/» muestra Hoy: banner de datos, órdenes del motor y qué sigue por producto", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Hoy", exact: true })).toBeVisible();

  // Sección 1: siempre hay o el aviso de rezago o la línea discreta de "Datos hasta" — nunca
  // las dos a la vez, y nunca ninguna (el banner es SIEMPRE una de las dos, según
  // `_DECISIONES.json`). El texto exacto de "Datos hasta …" también aparece DENTRO del banner
  // de alerta cuando hay rezago, así que se distingue por el título del `Alert`, no por esa frase.
  const banner = page.getByRole("alert").filter({ hasText: /órdenes de hoy están calculadas sobre datos viejos/i });
  const lineaFresca = page.getByText(/^Datos hasta \d{4}-\d{2}-\d{2}\.$/);
  await expect(banner.or(lineaFresca).first()).toBeVisible();

  // Sección 2: las órdenes del motor, o el estado vacío si no hay ninguna accionable hoy.
  await expect(page.getByRole("heading", { name: "Órdenes de hoy" })).toBeVisible();
  const sinOrdenes = page.getByText(/No hay órdenes que pidan una acción hoy/);
  const tarjetaDeOrden = page.getByRole("button", { name: "Aprobar" }).first();
  await expect(sinOrdenes.or(tarjetaDeOrden)).toBeVisible();

  // Sección 3: al menos un producto real, cada uno como enlace a su detalle.
  await expect(page.getByRole("heading", { name: "Qué sigue en cada producto" })).toBeVisible();
  const enlacesDeProducto = page.locator('a[href^="/producto/"]');
  await expect(enlacesDeProducto.first()).toBeVisible();
  expect(await enlacesDeProducto.count()).toBeGreaterThanOrEqual(4);
});
