import { expect, test } from "@playwright/test";

test("la pantalla de FASE 2 para TINNIDROP muestra el #1 en testeo, la fila de ganadores y los conceptos sin ejecutar mutaciones", async ({ page }) => {
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

  // 2. Los ángulos dependen de la data viva: la prueba lee lo mismo que la pantalla (GET fase2)
  //    en vez de fijar cuál va de #1, cuál en fila y cuáles no funcionaron.
  const detalle = await (await page.request.get("/api/productos/TINNIDROP/fase2")).json();
  const angulos = detalle.angulos as { angulo_key: string; rol: string }[];
  const principal = angulos.find((a) => a.rol === "ganador_activo");
  if (principal) {
    await expect(page.getByText("En testeo de conceptos ahora")).toBeVisible();
    await expect(page.getByTestId("angulo-en-testeo").getByText(principal.angulo_key, { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("Todavía no hay un ángulo ganador")).toBeVisible();
  }

  // 3. Ganadores en fila y ángulos que no funcionaron, cada uno en su bloque
  const enFila = angulos.filter((a) => a.rol === "ganador_en_fila");
  if (enFila.length > 0) {
    await expect(page.getByTestId("angulos-en-fila").getByText(enFila[0].angulo_key, { exact: true })).toBeVisible();
  } else {
    await expect(page.getByTestId("angulos-en-fila")).toHaveCount(0);
  }
  const descartados = angulos.filter((a) => a.rol === "perdedor" || a.rol === "midiendo");
  if (descartados.length > 0) {
    await expect(page.getByText("Ángulos que no funcionaron")).toBeVisible();
  } else {
    await expect(page.getByTestId("angulos-no-funcionaron")).toHaveCount(0);
  }

  // 4. Módulo de fatiga y botón de reingreso
  await expect(page.getByText(/Ciclo de Fatiga & Renovación/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /Nuevos ángulos para este producto/i })).toBeVisible();

  // 5. Galería de conceptos
  await expect(page.getByRole("heading", { name: /Galería de Conceptos/i })).toBeVisible();

  // 6. Ninguna mutación automática disparada
  expect(llamadasPost).toBe(0);
});

test("la pantalla de FASE 3 para TINNIDROP muestra el gate de entrada y el gate F4 pendiente", async ({ page }) => {
  let llamadasPost = 0;
  page.on("request", (req) => {
    if (req.method() === "POST") {
      llamadasPost++;
    }
  });

  await page.goto("/producto/TINNIDROP/fase3");

  // 1. Cabecera principal de FASE 3 (flujo LucidBot)
  await expect(page.getByRole("heading", { name: /FASE 3 · Flujo LucidBot \(TINNIDROP\)/i })).toBeVisible({ timeout: 15_000 });

  // 2. Semáforo del gate de entrada (concepto 2de2) — TINNIDROP hoy está en F2, así que el gate
  //    todavía no se cumple. La prueba lee el mismo contrato que la pantalla en vez de fijar el
  //    veredicto exacto, que depende de la data viva.
  const detalle = await (await page.request.get("/api/productos/TINNIDROP/fase3")).json();
  await expect(page.getByText(/Gate de Entrada a FASE 3/i)).toBeVisible();
  await expect(page.getByText(/Concepto Ganador Replicado en 2 de 2/i)).toBeVisible();
  await expect(page.getByText(detalle.entrada.ok ? "✓ GATE CUMPLIDO" : "⚠ GATE PENDIENTE")).toBeVisible();

  // 3. Sin CAMBIO_BOT todavía para TINNIDROP: el módulo de eventos lo dice.
  expect(detalle.eventos_cambio_bot).toEqual([]);
  await expect(page.getByText("Ninguno todavía")).toBeVisible();

  // 4. Gate duro hacia FASE 4: sin data (el producto ni entró a F3), la tarjeta lo dice.
  expect(detalle.gate_f4).toBeNull();
  await expect(page.getByText(/Gate duro hacia FASE 4/i)).toBeVisible();

  // 5. Enlaces de navegación a FASE 2 y FASE 4
  await expect(page.getByRole("link", { name: /Ver FASE 2/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Ver FASE 4/i })).toBeVisible();

  // 6. Sin mutaciones automáticas
  expect(llamadasPost).toBe(0);
});

test("la pantalla de FASE 4 para TINNIDROP muestra el semáforo del gate y estructura CBO", async ({ page }) => {
  let llamadasPost = 0;
  page.on("request", (req) => {
    if (req.method() === "POST") {
      llamadasPost++;
    }
  });

  await page.goto("/producto/TINNIDROP/fase4");

  // 1. Cabecera principal de FASE 4
  await expect(page.getByRole("heading", { name: /FASE 4 · Escalado CBO \(TINNIDROP\)/i })).toBeVisible({ timeout: 15_000 });

  // 2. Semáforo del Gate 2de2+CAMBIO_BOT+cierre
  await expect(page.getByText(/Gate de Entrada a FASE 4/i)).toBeVisible();
  await expect(page.getByText(/Concepto Ganador Replicado en 2 de 2/i)).toBeVisible();

  // 3. Estructura CBO 1-1-7
  await expect(page.getByText(/Estructura de Campaña 1-1-7 CBO/i)).toBeVisible();

  // 4. Expansión Horizontal
  await expect(page.getByText(/Expansión Horizontal/i)).toBeVisible();

  // 5. Enlace a FASE 3
  const linkFase3 = page.getByRole("link", { name: /Ver FASE 3/i });
  await expect(linkFase3).toBeVisible();

  // 6. Sin mutaciones automáticas
  expect(llamadasPost).toBe(0);
});
