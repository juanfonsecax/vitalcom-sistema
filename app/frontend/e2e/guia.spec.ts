import { expect, test } from "@playwright/test";

test("la guía de uso abre desde Ajustes y muestra sus 3 secciones", async ({ page }) => {
  await page.goto("/ajustes");
  // Clic en el enlace Guía de Ajustes (la barra lateral solo tiene Hoy/Productos/Resultados/Ajustes)
  await page.getByRole("link", { name: "Guía", exact: true }).click();
  await expect(page).toHaveURL(/\/guia/);

  // Título y secciones clave
  await expect(page.getByRole("heading", { name: "Guía de Uso del Sistema" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "¿Qué hace cada pantalla y botón?" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "¿Qué significa cada estado?" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "¿Qué hacer si algo falla o se detiene?" })).toBeVisible();

  // Vocabulario y estados
  await expect(page.getByText("Portafolio (Inicio)")).toBeVisible();
  await expect(page.getByText("SEGUIR MIDIENDO")).toBeVisible();
  await expect(page.getByText("VITALCOM_RESPALDOS")).toBeVisible();
});
