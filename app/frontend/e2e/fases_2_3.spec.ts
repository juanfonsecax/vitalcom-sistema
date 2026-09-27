import { expect, test } from "@playwright/test";

test("la pantalla de FASE 2 para TINNIDROP muestra el ángulo ganador, carril secundario y conceptos sin ejecutar mutaciones", async ({ page }) => {
  let llamadasPost = 0;
  page.on("request", (req) => {
    if (req.method() === "POST") {
      llamadasPost++;
    }
  });

  await page.goto("/producto/TINNIDROP/fase2");

  // 1. Cabecera principal de FASE 2. El primer golpe del endpoint contra el servidor recién
  //    levantado puede tardar más que los 5s default (flujo documentado en playwright.config);
  //    se le da aire a la espera, no se debilita lo que se afirma.
  await expect(page.getByRole("heading", { name: /FASE 2 · Testeo de Conceptos \(TINNIDROP\)/i })).toBeVisible({ timeout: 15_000 });

  // 2. Ángulo ganador y nodo actual del motor
  await expect(page.getByText("Ángulo Ganador Coronado por Ventas")).toBeVisible();

  // 3. Carriles secundarios escalonados: dependen de la data viva, así que la prueba lee lo mismo
  //    que la pantalla (GET fase2) en vez de fijar qué ángulo va de secundario.
  const detalle = await (await page.request.get("/api/productos/TINNIDROP/fase2")).json();
  await expect(page.getByRole("heading", { name: detalle.angulo_ganador, exact: true })).toBeVisible();
  const carriles = detalle.carriles_secundarios as { angulo_key: string }[];
  if (carriles.length > 0) {
    await expect(page.getByText(/Carriles Escalonados/i)).toBeVisible();
    await expect(page.getByText(carriles[0].angulo_key, { exact: true }).first()).toBeVisible();
  } else {
    await expect(page.getByText(/Carriles Escalonados/i)).toHaveCount(0);
  }

  // 4. Módulo de fatiga y botón de reingreso
  await expect(page.getByText(/Ciclo de Fatiga & Renovación/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /Nuevos ángulos para este producto/i })).toBeVisible();

  // 5. Galería de conceptos
  await expect(page.getByRole("heading", { name: /Galería de Conceptos/i })).toBeVisible();

  // 6. Ninguna mutación automática disparada
  expect(llamadasPost).toBe(0);
});

test("la pantalla de FASE 3 para TINNIDROP muestra el semáforo del gate 2de2 y estructura CBO", async ({ page }) => {
  let llamadasPost = 0;
  page.on("request", (req) => {
    if (req.method() === "POST") {
      llamadasPost++;
    }
  });

  await page.goto("/producto/TINNIDROP/fase3");

  // 1. Cabecera principal de FASE 3
  await expect(page.getByRole("heading", { name: /FASE 3 · Escalado CBO \(TINNIDROP\)/i })).toBeVisible();

  // 2. Semáforo del Gate 2de2
  await expect(page.getByText(/Gate de Entrada a FASE 3/i)).toBeVisible();
  await expect(page.getByText(/Concepto Ganador Replicado en 2 de 2/i)).toBeVisible();

  // 3. Estructura CBO 1-1-7
  await expect(page.getByText(/Estructura de Campaña 1-1-7 CBO/i)).toBeVisible();

  // 4. Expansión Horizontal
  await expect(page.getByText(/Expansión Horizontal/i)).toBeVisible();

  // 5. Enlace a FASE 2
  const linkFase2 = page.getByRole("link", { name: /Ver FASE 2/i });
  await expect(linkFase2).toBeVisible();

  // 6. Sin mutaciones automáticas
  expect(llamadasPost).toBe(0);
});
