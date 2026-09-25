import { expect, test } from "@playwright/test";

/**
 * resultados.spec.ts — humo de `/resultados` (T4b) contra el backend y el sistema reales.
 *
 * Nadie subió todavía un export de Dropi a este checkout, así que la pantalla tiene que caer
 * en el estado vacío (nunca en el error genérico) y ofrecer la carga — eso es lo que se
 * verifica acá. El P&L con datos reales lo cubren los tests unitarios (`resultados.test.tsx`)
 * y de backend (`test_resultados_api.py`), que sí controlan el export de entrada.
 */
test("/resultados renderiza sus secciones: encabezado, estado vacío y carga de export", async ({ page }) => {
  await page.goto("/resultados");
  await expect(page.getByRole("heading", { name: "Resultados", exact: true })).toBeVisible();

  // Sin ningún _PL_*.json en PRODUCTOS/_AUDITORIAS/, la pantalla explica por qué (nunca un
  // "No pude leer el sistema" genérico: un 404 acá es un estado normal, no una falla).
  await expect(page.getByText(/todavía no hay ningún export de dropi cargado/i)).toBeVisible();
  await expect(page.getByText(/no pude leer el sistema/i)).toHaveCount(0);

  // La sección de carga siempre está, con o sin datos previos (su título no es un <h*>: es un
  // CardTitle, sin rol "heading" en el árbol de accesibilidad).
  await expect(page.getByText("Cargar export de Dropi")).toBeVisible();
  await expect(page.getByLabel(/export de órdenes de dropi/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /calcular el p&l/i })).toBeDisabled();
});
