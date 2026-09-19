import { expect, test } from "@playwright/test";

test("la pantalla de FASE 1 para OVULOS_PURITY abre, muestra las 7 pestañas y no ejecuta nada", async ({ page }) => {
  // Monitorear que ninguna llamada de mutación o ejecución se dispare
  let llamadasPost = 0;
  page.on("request", (req) => {
    if (req.method() === "POST") {
      llamadasPost++;
    }
  });

  await page.goto("/producto/OVULOS_PURITY/fase1");

  // 1. Cabecera principal
  await expect(page.getByRole("heading", { name: /FASE 1 · OVULOS_PURITY/i })).toBeVisible();

  // 2. Verificar que las 7 pestañas están presentes
  const tabAvance = page.getByRole("button", { name: "Avance" });
  const tabInvestigacion = page.getByRole("button", { name: "Investigación" });
  const tabAngulos = page.getByRole("button", { name: "Avatares y ángulos" });
  const tabAnuncios = page.getByRole("button", { name: "Anuncios" });
  const tabFlujoBot = page.getByRole("button", { name: "Flujo LucidBot" });
  const tabCampana = page.getByRole("button", { name: "Estructura de campaña" });
  const tabChecklist = page.getByRole("button", { name: /Checklist/ });

  await expect(tabAvance).toBeVisible();
  await expect(tabInvestigacion).toBeVisible();
  await expect(tabAngulos).toBeVisible();
  await expect(tabAnuncios).toBeVisible();
  await expect(tabFlujoBot).toBeVisible();
  await expect(tabCampana).toBeVisible();
  await expect(tabChecklist).toBeVisible();

  // Pestaña 1: Avance (activa por defecto)
  await expect(page.getByText(/Armado de FASE 1 · 9 pasos/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Armar FASE 1" })).toBeVisible();

  // Pestaña 2: Investigación
  await tabInvestigacion.click();
  // Debe renderizar la pestaña de investigación (con etapas o mensaje de investigación)
  await expect(page.locator("body")).toContainText(/Investigación de mercado|No hay salidas de investigación/i);

  // Pestaña 3: Avatares y ángulos
  await tabAngulos.click();
  // Doctrina del embudo obligatoria sin TOFU/MOFU/BOFU
  await expect(
    page.getByText(/Embudo: pendiente de decisión del operador \(la doctrina dice tres cosas distintas\)/i).first(),
  ).toBeVisible();
  // Verificar que NO contenga clasificaciones arbitrarias de TOFU / MOFU / BOFU
  const cuerpoTexto = await page.textContent("body");
  expect(cuerpoTexto).not.toMatch(/\bTOFU\b/);
  expect(cuerpoTexto).not.toMatch(/\bMOFU\b/);
  expect(cuerpoTexto).not.toMatch(/\bBOFU\b/);

  // Pestaña 4: Anuncios
  await tabAnuncios.click();
  await expect(page.locator("body")).toContainText(/Anuncio|No hay anuncios generados todavía/i);

  // Pestaña 5: Flujo LucidBot
  await tabFlujoBot.click();
  await expect(page.locator("body")).toContainText(/Flujo LucidBot|No hay flujo de bot generado todavía/i);

  // Pestaña 6: Estructura de campaña
  await tabCampana.click();
  await expect(page.locator("body")).toContainText(/Estructura de campaña|No hay plan de campaña generado todavía/i);

  // Pestaña 7: Checklist
  await tabChecklist.click();
  await expect(page.getByText(/Verificaciones de publicación \(Preflight\)/i)).toBeVisible();
  await expect(page.getByText(/se verifica al publicar \(contra Meta\)/i).first()).toBeVisible();

  // Comprobar que no se ejecutó ninguna acción (cero llamadas POST)
  expect(llamadasPost).toBe(0);
});
