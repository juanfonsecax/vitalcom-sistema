/**
 * fase2.test.tsx — Pruebas unitarias de la pantalla Fase2 (Hito 6).
 *
 * Verifica:
 * 1. Muestra el ángulo ganador y los carriles secundarios escalonados.
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

const FASE2_MOCK = {
  producto_key: "TINNIDROP",
  fase: "FASE 2",
  nodo_actual: "F2.etapa-11",
  angulo_ganador: "ACCESIBILIDAD_MEDICO",
  conceptos_generados: 10,
  carriles_secundarios: [
    {
      angulo_key: "NOCHES_SIN_DORMIR",
      estado_motor: "GANADOR_SECUNDARIO",
      orden: "RENOVAR",
      fecha_estimada: "Esperar ~3 días tras arranque de ACCESIBILIDAD_MEDICO",
      accion: "En cola para nuevo ad set en FASE 2",
    },
  ],
  conceptos: [
    {
      creativo_id: "TINNIDROP_F2_C01",
      canonico_id: "C01",
      blueprint_id: "BP-01",
      blueprint_nombre: "Before / After Split",
      rol_embudo: "TOFU",
      dispositivo: "Comparativa visual directa",
      prompt: "Fotografía publicitaria hiperrealista dividida al medio...",
      archivo: "TINNIDROP_F2_C01.png",
      archivo_existe: true,
      estado: "GENERADO",
    },
    {
      creativo_id: "TINNIDROP_F2_C02",
      canonico_id: "C02",
      blueprint_id: "BP-04",
      blueprint_nombre: "Social Proof Wall",
      rol_embudo: "BOFU",
      dispositivo: "Capturas de chats de clientes satisfechos",
      prompt: "Collage limpio con 3 testimonios...",
      archivo: "TINNIDROP_F2_C02.png",
      archivo_existe: false,
      estado: "PENDIENTE_GENERAR",
    },
  ],
  fatiga: {
    ordenes_activas: ["RENOVAR"],
    angulos_probados: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
    mensaje: "El motor emitió ordenes de fatiga creativa (RENOVAR).",
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

test("renderiza el ángulo ganador, carril secundario y la galería de conceptos", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/FASE 2 · Testeo de Conceptos \(TINNIDROP\)/i)).toBeDefined();
  });

  expect(screen.getByText("ACCESIBILIDAD_MEDICO")).toBeDefined();
  expect(screen.getByText("F2.etapa-11")).toBeDefined();
  expect(screen.getByText("NOCHES_SIN_DORMIR")).toBeDefined();
  expect(screen.getByText(/Esperar ~3 días/i)).toBeDefined();

  // Conceptos
  expect(screen.getByText("Before / After Split")).toBeDefined();
  expect(screen.getByText("Social Proof Wall")).toBeDefined();
  expect(screen.getByText("C01")).toBeDefined();
  expect(screen.getByText("C02")).toBeDefined();
  expect(screen.getByText("✓ En disco")).toBeDefined();
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
