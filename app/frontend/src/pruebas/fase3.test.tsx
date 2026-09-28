/**
 * fase3.test.tsx — Pruebas unitarias de la pantalla Fase3 (FASE 3, optimización del flujo
 * LucidBot; B3 de las cuatro fases).
 *
 * Verifica:
 * 1. Semáforo del gate de entrada (concepto 2de2) cumplido o pendiente.
 * 2. Sin CAMBIO_BOT todavía: lo dice y muestra cómo registrarlo.
 * 3. Con CAMBIO_BOT pero cierre bajo el piso: el gate F4 sigue sin desbloquear.
 * 4. Con CAMBIO_BOT y cierre sobre el piso: el gate F4 desbloquea FASE 4.
 */
import { render, screen, waitFor } from "@testing-library/react";
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

function simularFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const ruta = new URL(url, "http://localhost").pathname + new URL(url, "http://localhost").search;
      const cuerpo = respuestas[`GET ${ruta}`] ?? respuestas[`GET ${ruta.split("?")[0]}`];
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

const BASE = {
  producto_key: "TINNIDROP",
  fase: "F3",
  nodo_actual: "F3.medir_cierre",
  entrada: {
    ok: true,
    observado: "Concepto C01 validado en 2 de 2 tandas.",
    regla: "Regla de replicación: un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido.",
  },
  nodo_reescribir: {
    id: "F3.reescribir",
    titulo: "Reescribir",
    ejecutor: "etapa-5",
    ejecutor_tipo: "subagente",
    como: "",
    estado: "CUMPLIDO",
    cumplido: true,
    ciclo: false,
    secuencia: [],
    produce: [],
  },
  nodo_medir_cierre: {
    id: "F3.medir_cierre",
    titulo: "Medir cierre",
    ejecutor: "script",
    ejecutor_tipo: "script",
    como: "",
    estado: "PENDIENTE",
    cumplido: false,
    ciclo: false,
    secuencia: [],
    produce: [],
  },
  eventos_cambio_bot: [] as { evento: string; fecha: string; motivo: string }[],
  gate_f4: null as Record<string, unknown> | null,
  entrada_f4: { ok: false, observado: "sin CAMBIO_BOT todavía", regla: "" },
};

beforeEach(() => {
  respuestas = {
    "GET /api/acciones": [],
  };
  simularFetch();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("sin CAMBIO_BOT: dice que falta registrarlo y no desbloquea FASE 4", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = {
    ...BASE,
    gate_f4: {
      fecha_cambio_bot: null, mensajes: null, ventas: null, cierre_pct: null,
      min_mensajes: 30, min_cierre_pct: 10, cierre_meta_min_pct: 15, cierre_meta_max_pct: 20,
      ok: false,
      explicacion: "sin CAMBIO_BOT (ni EXCEPCION_CAMBIO_BOT) posterior al concepto ganador todavía",
    },
  };
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/FASE 3 · Flujo LucidBot \(TINNIDROP\)/i)).toBeDefined();
  });

  expect(screen.getByText("✓ GATE CUMPLIDO")).toBeDefined();
  expect(screen.getByText("Ninguno todavía")).toBeDefined();
  expect(screen.getByText("⚠ SE QUEDA EN FASE 3")).toBeDefined();
});

test("CAMBIO_BOT registrado pero cierre bajo el piso: sigue en FASE 3", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = {
    ...BASE,
    eventos_cambio_bot: [{ evento: "CAMBIO_BOT", fecha: "2026-09-20", motivo: "reescritura etapa-5" }],
    gate_f4: {
      fecha_cambio_bot: "2026-09-20", mensajes: 40, ventas: 2, cierre_pct: 5.0,
      min_mensajes: 30, min_cierre_pct: 10, cierre_meta_min_pct: 15, cierre_meta_max_pct: 20,
      ok: false,
      explicacion: "desde CAMBIO_BOT 2026-09-20: 40 mensaje(s) (≥30) · cierre 5.0% (≥10%)",
    },
  };
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("1 registrado(s)")).toBeDefined();
  });

  expect(screen.getByText("⚠ SE QUEDA EN FASE 3")).toBeDefined();
  expect(screen.getByText(/desde CAMBIO_BOT 2026-09-20/i)).toBeDefined();
});

test("CAMBIO_BOT registrado y cierre sobre el piso: desbloquea FASE 4", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase3"] = {
    ...BASE,
    fase: "F4",
    eventos_cambio_bot: [{ evento: "CAMBIO_BOT", fecha: "2026-09-15", motivo: "reescritura etapa-5" }],
    gate_f4: {
      fecha_cambio_bot: "2026-09-15", mensajes: 40, ventas: 6, cierre_pct: 15.0,
      min_mensajes: 30, min_cierre_pct: 10, cierre_meta_min_pct: 15, cierre_meta_max_pct: 20,
      ok: true,
      explicacion: "desde CAMBIO_BOT 2026-09-15: 40 mensaje(s) (≥30) · cierre 15.0% (≥10%)",
    },
    entrada_f4: { ok: true, observado: "todo cumplido", regla: "" },
  };
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("✓ DESBLOQUEA FASE 4")).toBeDefined();
  });
});
