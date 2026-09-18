import { expect, test } from "@playwright/test";

/**
 * Trabajos y acciones, de punta a punta contra el servidor real (frontend compilado).
 *
 * Solo se lee: la app arranca DBOS sobre una base de datos temporal y no se pide ninguna acción.
 * Que las acciones se ejecuten (y que Meta nunca corra sin aprobación) lo prueba el backend contra fakes.
 */
test("la pantalla Trabajos abre, dice que no hay trabajos y muestra el estado de Claude", async ({ page }) => {
  await page.goto("/trabajos");
  await expect(page.getByRole("heading", { name: "Trabajos", level: 1 })).toBeVisible();
  await expect(page.getByText("No hay trabajos todavía")).toBeVisible();
  await expect(page.getByText(/Claude: /)).toBeVisible();
  await expect(page.getByRole("link", { name: "Trabajos" })).toBeVisible();
});

test("una acción que no está declarada en el manifiesto es un 403", async ({ request }) => {
  const respuesta = await request.post("/api/acciones/nodo.no.existe", { data: { parametros: {}, confirmado: true } });
  expect(respuesta.status()).toBe(403);
  expect((await respuesta.json()).codigo).toBe("ACCION_NO_DECLARADA");
});

test("las acciones que se ofrecen son las del manifiesto y las internas no aparecen", async ({ request }) => {
  const respuesta = await request.get("/api/acciones");
  expect(respuesta.ok()).toBeTruthy();
  const acciones = (await respuesta.json()) as { id: string; habilitada: boolean; toca_meta: boolean }[];
  // Con el manifiesto v6 (carpeta real todavía sin mergear) no hay ninguna; con el v7, sí.
  expect(acciones.map((a) => a.id)).not.toContain("producto.alta");
  expect(acciones.map((a) => a.id)).not.toContain("sistema.gen_app");
  for (const accion of acciones.filter((a) => a.toca_meta)) {
    expect(accion.habilitada, `${accion.id} toca Meta y no puede estar habilitada en el Hito 3`).toBe(false);
  }
});
