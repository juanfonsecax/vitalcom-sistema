/**
 * fase3.test.tsx — Pruebas unitarias de la pantalla Fase3 (Hito 6).
 *
 * Verifica:
 * 1. Semáforo del gate 2de2 (cumplido o pendiente) con evidencia del motor.
 * 2. Visualización de la estructura 1-1-7 CBO y su desglose.
 * 3. Expansión horizontal por Post ID, multicuenta y multifanpage.
 * 4. Botón de reingreso a FASE 1 por agotamiento del escalado.
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
import { Fase3 } from "../pantallas/Fase3";

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
    path: "/producto/$clave/fase3",
    component: Fase3,
  });
  const historia = createMemoryHistory({
    initialEntries: [`/producto/${clave}/fase3`],
  });
  const router = createRouter({ routeTree: raiz.addChildren([ruta]), history: historia });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const FASE3_MOCK_PENDIENTE = {
  producto_key: "TINNIDROP",
  fase: "FASE 3",
  nodo_actual: "F2.etapa-11",
  gate_2de2: {
    ok: false,
    observado: "El producto se encuentra en FASE 2. Se requiere ganador replicado en 2 tandas.",
    regla: "Regla de replicación: un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido.",
  },
  plan_cbo: {
    estructura: "1-1-7 CBO",
    descripcion: "1 Campaña CBO, 1 Conjunto de 7 anuncios con el concepto validado en 2 de 2 × 7 hooks",
    tiene_plan: false,
    estado: "PENDIENTE",
    archivo: null,
  },
  expansion: {
    post_id: false,
    cuenta_primaria: "act_vitalcom_gt",
    cuentas_activas: ["act_vitalcom_gt"],
    page_id: "vitalcom_salud_gt",
  },
  fatiga: {
    angulos_probados: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
    puede_reingresar: true,
  },
};

const FASE3_MOCK_CUMPLIDO = {
  ...FASE3_MOCK_PENDIENTE,
  nodo_actual: "F3.cbo",
  gate_2de2: {
    ok: true,
    observado: "Concepto C01 validado en 2 de 2 tandas con ROAS superior.",
    regla: "Regla de replicación: un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido.",
  },
  plan_cbo: {
    estructura: "1-1-7 CBO",
    descripcion: "1 Campaña CBO con presupuesto optimizado",
    tiene_plan: true,
    estado: "GENERADO",
    archivo: "4_PLAN_ESCALADO.txt",
  },
  expansion: {
    post_id: true,
    cuenta_primaria: "act_vitalcom_gt",
    cuentas_activas: ["act_vitalcom_gt", "act_vitalcom_respaldo"],
    page_id: "vitalcom_salud_gt",
  },
};

beforeEach(() => {
  respuestas = {};
  llamadasFetch = [];
  simularFetch();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("muestra gate 2de2 como pendiente con su mensaje doctrinario", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = FASE3_MOCK_PENDIENTE;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/FASE 3 · Escalado CBO \(TINNIDROP\)/i)).toBeDefined();
  });

  expect(screen.getByText("⚠ GATE PENDIENTE")).toBeDefined();
  expect(
    screen.getByText(/El producto se encuentra en FASE 2. Se requiere ganador replicado en 2 tandas./i),
  ).toBeDefined();
  expect(screen.getByText("Estructura de Campaña 1-1-7 CBO")).toBeDefined();
  expect(screen.getByText("PENDIENTE")).toBeDefined();
  expect(screen.getAllByText("act_vitalcom_gt").length).toBeGreaterThan(0);
});

test("muestra gate 2de2 como cumplido y plan CBO generado", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = FASE3_MOCK_CUMPLIDO;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("✓ GATE CUMPLIDO")).toBeDefined();
  });

  expect(
    screen.getByText(/Concepto C01 validado en 2 de 2 tandas con ROAS superior./i),
  ).toBeDefined();
  expect(screen.getByText("GENERADO")).toBeDefined();
  expect(screen.getByText(/4_PLAN_ESCALADO.txt/i)).toBeDefined();
  expect(screen.getByText("Post ID Activo")).toBeDefined();
});

test("botón de reingreso a F1 desde Fase 3 abre modal y ejecuta POST", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = FASE3_MOCK_CUMPLIDO;
  respuestas["POST /api/productos/TINNIDROP/reingreso-f1"] = {
    producto_key: "TINNIDROP",
    ok: true,
    nodo_destino: "F1.etapa-0",
    angulos_excluidos: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
    motivo: "Escalado agotado / fatiga de microángulos",
  };

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Nuevos ángulos para este producto →")).toBeDefined();
  });

  fireEvent.click(screen.getByText("Nuevos ángulos para este producto →"));

  expect(screen.getByText(/Confirmar retorno a FASE 1 desde FASE 3/i)).toBeDefined();
  expect(screen.getByText(/ACCESIBILIDAD_MEDICO, NOCHES_SIN_DORMIR/i)).toBeDefined();

  fireEvent.click(screen.getByText("Confirmar retorno a F1"));

  await waitFor(() => {
    const llamada = llamadasFetch.find(
      (l) => l.url === "/api/productos/TINNIDROP/reingreso-f1" && l.metodo === "POST",
    );
    expect(llamada).toBeDefined();
    expect(llamada?.cuerpo?.motivo).toBe("Escalado agotado / fatiga de microángulos");
  });
});
