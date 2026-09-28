/**
 * fase2.test.tsx — Pruebas unitarias de la pantalla Fase2 (Hito 6).
 *
 * Verifica:
 * 1. Muestra el #1 en testeo, los ganadores en fila y los ángulos que no funcionaron.
 * 2. Galería de 10 conceptos con blueprints, chips de rol y prompts.
 * 3. Botón para copiar el prompt al portapapeles.
 * 4. Modal de confirmación para reingreso a FASE 1 por fatiga y envío de la mutación.
 * 5. Banner informativo cuando ya existe un reingreso activo.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Fase2 } from "../pantallas/Fase2";

let respuestas: Record<string, unknown> = {};
let llamadasFetch: { url: string; metodo: string; cuerpo?: any }[] = [];

function simularFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, opciones?: RequestInit) => {
      const ruta = new URL(url, "http://localhost").pathname;
      const metodo = opciones?.method ?? "GET";
      let cuerpoParseado: any = undefined;
      if (opciones?.body && typeof opciones.body === "string") {
        try {
          cuerpoParseado = JSON.parse(opciones.body);
        } catch {
          cuerpoParseado = opciones.body;
        }
      }
      llamadasFetch.push({
        url: ruta,
        metodo,
        cuerpo: cuerpoParseado,
      });
      const cuerpo = respuestas[`${metodo} ${ruta}`];
      return {
        ok: cuerpo !== undefined,
        status: cuerpo === undefined ? 404 : 200,
        json: async () => cuerpo,
        statusText: cuerpo === undefined ? "Not Found" : "OK",
      } as Response;
    }),
  );
}

function renderizar(clave = "TINNIDROP") {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const raiz = createRootRoute();
  const ruta = createRoute({
    getParentRoute: () => raiz,
    path: "/producto/$clave/fase2",
    component: Fase2,
  });
  const historia = createMemoryHistory({
    initialEntries: [`/producto/${clave}/fase2`],
  });
  const router = createRouter({ routeTree: raiz.addChildren([ruta]), history: historia });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const ANGULO_BASE = {
  posicion: null,
  etiqueta: "",
  estado_angulo: "",
  dias_sin_gasto: 0,
  ultimo_dia_gasto: "2026-09-25",
  estado: null,
  accion_sugerida: null,
  ventas_acum: null,
  cpa_real_q: null,
  cierre_pct: null,
  ic: null,
  spend_acum_q: null,
};

const FASE2_MOCK = {
  producto_key: "TINNIDROP",
  fase: "FASE 2",
  nodo_actual: "F2.etapa-11",
  angulo_ganador: "ACCESIBILIDAD_MEDICO",
  conceptos_generados: 10,
  angulos: [
    {
      ...ANGULO_BASE,
      angulo_key: "ACCESIBILIDAD_MEDICO",
      rol: "ganador_activo",
      posicion: 1,
      estado: "ESCALAR",
      estado_angulo: "ESCALANDO",
      ventas_acum: 91,
      cpa_real_q: 41.5,
      cierre_pct: 18.2,
      ic: [30, 41.5, 60],
      accion_sugerida: "NO SUBIR PRESUPUESTO todavía",
    },
    {
      ...ANGULO_BASE,
      angulo_key: "NOCHES_SIN_DORMIR",
      rol: "ganador_en_fila",
      posicion: 2,
      estado: "RENOVAR",
      ventas_acum: 24,
      cpa_real_q: 77,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "DETERIORO_COGNITIVO",
      rol: "ganador_en_fila",
      posicion: 3,
      ventas_acum: 105,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "ME_DIJERON_NO_CURA",
      rol: "perdedor",
      etiqueta: "ya apagado (40 días sin gastar)",
      estado_angulo: "APAGADO_ABANDONO",
      dias_sin_gasto: 40,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "MANCHAS_OSCURAS",
      rol: "perdedor",
      etiqueta: "el motor ordena pausarlo",
      estado: "PAUSAR",
      accion_sugerida: "PAUSAR: el costo por venta supera el break-even",
    },
    {
      ...ANGULO_BASE,
      angulo_key: "VERGUENZA_PIERNAS",
      rol: "midiendo",
      etiqueta: "midiendo",
      estado: "SEGUIR_MIDIENDO",
    },
  ],
  conceptos: [
    {
      creativo_id: "TINNIDROP_F2_C01",
      angulo_key: "ACCESIBILIDAD_MEDICO",
      canonico_id: "C01",
      blueprint_id: "BP-01",
      blueprint_nombre: "Before / After Split",
      rol_embudo: "TOFU",
      dispositivo: "Comparativa visual directa",
      prompt: "Fotografía publicitaria hiperrealista dividida al medio...",
      prompt_origen: "paquete",
      referencia_url: "/api/swipe/_IMG/Camila_Recomienda/15_foto.jpg",
      comando_generar: null,
      archivo: "TINNIDROP_F2_C01.png",
      archivo_existe: true,
      estado: "GENERADO",
    },
    {
      creativo_id: "TINNIDROP_F2_C02",
      angulo_key: "ACCESIBILIDAD_MEDICO",
      canonico_id: "C02",
      blueprint_id: "BP-04",
      blueprint_nombre: "Social Proof Wall",
      rol_embudo: "BOFU",
      dispositivo: "Capturas de chats de clientes satisfechos",
      prompt: null,
      prompt_origen: "pendiente",
      referencia_url: null,
      comando_generar: "python Ads/_TOOLS/armar_prompts_fase2.py TINNIDROP ACCESIBILIDAD_MEDICO",
      archivo: "TINNIDROP_F2_C02.png",
      archivo_existe: false,
      estado: "PENDIENTE_GENERAR",
    },
  ],
  fatiga: {
    ordenes: [
      { celda: "NOCHES_SIN_DORMIR", estado: "RENOVAR", accion: "RENOVAR CREATIVO: rotá el concepto, no apagues" },
      { celda: "ACCESIBILIDAD_MEDICO", estado: "ESCALAR", accion: "NO SUBIR PRESUPUESTO todavía" },
    ],
    angulos_probados: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
  },
  reingreso_activo: null,
};

beforeEach(() => {
  respuestas = {};
  llamadasFetch = [];
  simularFetch();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("renderiza el #1 en testeo, la fila, los que no funcionaron y la galería", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/FASE 2 · Testeo de Conceptos \(TINNIDROP\)/i)).toBeDefined();
  });

  // (a) el #1, con sus cifras clave
  const hero = await screen.findByTestId("angulo-en-testeo");
  expect(hero.textContent).toContain("En testeo de conceptos ahora");
  expect(hero.textContent).toContain("ACCESIBILIDAD_MEDICO");
  expect(hero.textContent).toContain("91");
  expect(hero.textContent).toContain("Q41.5");
  expect(hero.textContent).toContain("18.2%");
  expect(screen.getByText("F2.etapa-11")).toBeDefined();

  // (b) en fila: #2 y #3, con la regla y sin fechas inventadas
  const fila = screen.getByTestId("angulos-en-fila");
  expect(fila.textContent).toContain("NOCHES_SIN_DORMIR");
  expect(fila.textContent).toContain("DETERIORO_COGNITIVO");
  expect(fila.textContent).toContain("#2 en la fila");
  expect(fila.textContent).toContain("#3 en la fila");
  expect(screen.getAllByText(/Entra a su propia Fase 2 cuando el #1 cierre la suya/i)).toHaveLength(2);
  expect(screen.queryByText(/Esperar ~3 días/i)).toBeNull();

  // Conceptos
  expect(screen.getByText("Before / After Split")).toBeDefined();
  expect(screen.getByText("Social Proof Wall")).toBeDefined();
  expect(screen.getByText("C01")).toBeDefined();
  expect(screen.getByText("C02")).toBeDefined();
  expect(screen.getByText("✓ En disco")).toBeDefined();
});

test("los ángulos que no funcionaron llevan la etiqueta que dicen los datos", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["GET /api/trabajos"] = [
    { job_id: "job-77", producto_key: "TINNIDROP", pendiente: { tipo: "aprobacion" } },
  ];
  renderizar("TINNIDROP");

  const lista = await screen.findByTestId("angulos-no-funcionaron");
  expect(lista.textContent).toContain("ME_DIJERON_NO_CURA");
  expect(lista.textContent).toContain("ya apagado (40 días sin gastar)");
  expect(lista.textContent).toContain("MANCHAS_OSCURAS");
  expect(lista.textContent).toContain("el motor ordena pausarlo");
  expect(lista.textContent).toContain("VERGUENZA_PIERNAS");
  expect(lista.textContent).toContain("midiendo");
  // la orden de pausa lleva a Trabajos, donde vive la aprobación
  await waitFor(() => {
    const enlace = screen.getByRole("link", { name: "Revisar en Trabajos" });
    expect(enlace.getAttribute("href")).toContain("/trabajos/job-77");
  });
  // el detalle técnico sigue ahí, plegado
  expect(screen.getAllByText("Ver detalle técnico").length).toBeGreaterThan(0);
});

test("la fatiga muestra la orden concreta del motor como «Qué hacer» y pliega la doctrina", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const bloque = await screen.findByTestId("ordenes-renovar");
  expect(bloque.textContent).toContain("Qué hacer");
  expect(bloque.textContent).toContain("NOCHES_SIN_DORMIR");
  expect(bloque.textContent).toContain("RENOVAR CREATIVO: rotá el concepto, no apagues");
  // solo las órdenes de renovar; la de escalar no es de este bloque
  expect(bloque.textContent).not.toContain("NO SUBIR PRESUPUESTO");
  expect(screen.getByText("¿Cómo funciona la renovación?")).toBeDefined();
});

test("la galería agrupa por ángulo y arranca en el #1", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    conceptos: [
      ...FASE2_MOCK.conceptos,
      {
        ...FASE2_MOCK.conceptos[0],
        creativo_id: "TINNIDROP_F2_N01",
        angulo_key: "NOCHES_SIN_DORMIR",
        canonico_id: "N01",
        blueprint_nombre: "Testimonio de noche",
      },
    ],
  };
  renderizar("TINNIDROP");

  const pestanas = await screen.findAllByRole("tab");
  expect(pestanas.map((t) => t.textContent)).toEqual(["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"]);
  expect(pestanas[0].getAttribute("aria-selected")).toBe("true");
  expect(screen.getByText("Before / After Split")).toBeDefined();
  expect(screen.queryByText("Testimonio de noche")).toBeNull();

  fireEvent.click(pestanas[1]);
  expect(screen.getByText("Testimonio de noche")).toBeDefined();
  expect(screen.queryByText("Before / After Split")).toBeNull();
});

test("sin ganador no inventa un #1 y lo dice", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = { ...FASE2_MOCK, angulo_ganador: "", angulos: [] };
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Todavía no hay un ángulo ganador")).toBeDefined();
  });
  expect(screen.queryByTestId("angulos-en-fila")).toBeNull();
});

test("botón de copiar prompt invoca clipboard.writeText", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  const writeTextMock = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", {
    clipboard: { writeText: writeTextMock },
  });

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getAllByText("Copiar").length).toBeGreaterThan(0);
  });

  const botones = screen.getAllByText("Copiar");
  fireEvent.click(botones[0]);

  expect(writeTextMock).toHaveBeenCalledWith(
    "Fotografía publicitaria hiperrealista dividida al medio...",
  );

  await waitFor(() => {
    expect(screen.getByText("Copiado")).toBeDefined();
  });
});

test("concepto pendiente muestra el comando de armar_prompts_fase2.py, nunca un prompt inventado", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Prompt pendiente de generar")).toBeDefined();
  });

  expect(
    screen.getByText("python Ads/_TOOLS/armar_prompts_fase2.py TINNIDROP ACCESIBILIDAD_MEDICO"),
  ).toBeDefined();
});

test("concepto con paquete muestra la imagen de referencia y el botón de copiar imagen", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByAltText("Referencia de swipe para C01")).toBeDefined();
  });

  expect(screen.getByText("Copiar imagen")).toBeDefined();
});

test("modal de reingreso por fatiga confirma y envía mutación a F1", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["POST /api/productos/TINNIDROP/reingreso-f1"] = {
    producto_key: "TINNIDROP",
    ok: true,
    nodo_destino: "F1.etapa-0",
    angulos_excluidos: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
    motivo: "Ángulo agotado / fatiga de ventas",
  };

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Nuevos ángulos para este producto →")).toBeDefined();
  });

  fireEvent.click(screen.getByText("Nuevos ángulos para este producto →"));

  // Verificar que abre el modal mostrando los ángulos excluidos
  expect(screen.getByText(/¿Confirmar retorno a FASE 1 para TINNIDROP\?/i)).toBeDefined();
  expect(screen.getByText(/ACCESIBILIDAD_MEDICO, NOCHES_SIN_DORMIR/i)).toBeDefined();

  // Confirmar
  fireEvent.click(screen.getByText("Sí, volver a F1"));

  await waitFor(() => {
    const llamada = llamadasFetch.find(
      (l) => l.url === "/api/productos/TINNIDROP/reingreso-f1" && l.metodo === "POST",
    );
    expect(llamada).toBeDefined();
    expect(llamada?.cuerpo?.motivo).toBe("Ángulo agotado / fatiga de ventas");
  });
});

test("muestra banner de reingreso activo cuando existe", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    reingreso_activo: {
      fecha: "2026-09-19 15:30:00",
      motivo: "Fatiga creativa severa",
      angulos_excluidos: ["ACCESIBILIDAD_MEDICO"],
    },
  };

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/Reingreso a FASE 1 activo desde el 2026-09-19 15:30:00/i)).toBeDefined();
  });

  expect(screen.getByText("Fatiga creativa severa")).toBeDefined();
  expect(screen.getByText("Ir a FASE 1 →")).toBeDefined();
});
