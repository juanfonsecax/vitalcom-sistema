/** situacion.test.ts — la línea corta «fase · paso · trabado · lo hace» sale de los datos. */
import { expect, test } from "vitest";
import { lineaDeSituacion, resumenDeSituacion, responsableEnPalabras } from "../componentes/situacion";

const CLEARSTEM = {
  fase: "F2",
  faseTitulo: "FASE 2 · TESTEO DE CONCEPTOS",
  paso: "Fabricar los 10 conceptos",
  trabadoPor: "conceptos GENERADOS: 5 fila(s) · esperado ≥ 10",
  dueno: "etapa-9 (filas) + etapa-render (PNG)",
};

test("arma fase, paso, trabado y quién lo hace desde los datos", () => {
  const r = resumenDeSituacion(CLEARSTEM);
  expect(r.fase).toBe("Fase 2 · testeo de conceptos");
  expect(r.loHace).toBe("Fábrica de conceptos + Renderizador de creativos");
  expect(lineaDeSituacion(CLEARSTEM)).toBe(
    "Fase 2 · testeo de conceptos — Paso: Fabricar los 10 conceptos — Trabado: conceptos GENERADOS: 5 fila(s) · esperado ≥ 10 — Lo hace: Fábrica de conceptos + Renderizador de creativos",
  );
});

test("sin bloqueante lo dice y usa el ejecutor siguiente; sin título cae a «Fase N»", () => {
  const linea = lineaDeSituacion({ fase: "F3", ejecutor: "subagente etapa-5" });
  expect(linea).toBe("Fase 3 — Nada lo frena — Lo hace: Flujo del bot");
});

test("los scripts se dicen con un nombre corto, sin rutas ni flags", () => {
  expect(responsableEnPalabras("Ads/_TOOLS/recopilar_lucidsales.py · bajar_lucidsales.py")).toBe(
    "el sistema (recolección de LucidSales)",
  );
  expect(
    responsableEnPalabras(
      "la etapa que nombra cada bloqueante · Ads/_TOOLS/gen_publicacion.py --solo-paquete (solo los de ámbito paquete: la cuenta y la fecha los juzga F1.publicar)",
    ),
  ).toBe("el sistema (generador del paquete)");
  expect(responsableEnPalabras("`python Ads/_TOOLS/gen_decisiones.py`")).toBe("el sistema (motor de decisiones)");
  expect(responsableEnPalabras("script desconocido.py")).toBe("el sistema");
  // Si nombra una etapa, manda la etapa aunque cite un script.
  expect(responsableEnPalabras("etapa-6 · Ads/_TOOLS/gen_plan.py --validar")).toBe("Planificador de lanzamiento");
});

test("responsables sin etapa conocida", () => {
  expect(responsableEnPalabras("operador")).toBe("vos");
  expect(responsableEnPalabras("script gen_manual.py")).toBe("el sistema (generador del manual)");
  expect(responsableEnPalabras("skill `fase-1-angulos`")).toBe("Claude");
  expect(responsableEnPalabras(null)).toBe("sin ejecutor declarado");
});
