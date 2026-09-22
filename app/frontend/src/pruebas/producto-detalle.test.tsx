/**
 * producto-detalle.test.tsx — pruebas del resumen de ProductoDetalle (T2, vista-por-que).
 *
 * Verifica que la tarjeta de resumen diga, en una frase: en qué fase está, cuál es el paso de
 * ahora (título humano, no el id crudo), quién lo hace, y que avise cuando la data del motor
 * tiene más de 2 días de rezago. Todo sale de `flujo.py` (mock de `/api/productos/{clave}`).
 */
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { expect, test, vi } from "vitest";
import { ProductoDetalle } from "../pantallas/ProductoDetalle";

const FLUJO_BASE = {
  producto_key: "TINNIDROP",
  nombre: "Tinnidrop Importado Original",
  estado_producto: "VIVO",
  fase: "F2",
  fase_titulo: "FASE 2 · TESTEO DE CONCEPTOS",
  nodo_actual: "F2.etapa-11",
  estado: "LISTO_PARA_EJECUTAR",
  ejecutor: "subagente `etapa-11` (Task, subagent_type=etapa-11)",
  como: "Diagnostica el cierre por ángulo y entrega el brief a etapa-5.",
  evaluado_el: "2026-09-21",
  bloqueantes: [] as unknown[],
  falta_para_cumplir: [],
  entradas: [],
  nodos: [
    {
      id: "F2.etapa-11",
      titulo: "Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)",
      ejecutor: "subagente `etapa-11`",
      ejecutor_tipo: "subagente",
      como: "Diagnostica el cierre por ángulo.",
      estado: "LISTO_PARA_EJECUTAR",
      cumplido: false,
      ciclo: false,
      secuencia: [],
      produce: [],
      avisos: [],
    },
  ],
  avisos: [],
  ordenes: [],
};

function servir(respuestas: Record<string, unknown>) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const cuerpo = respuestas[new URL(url, "http://x").pathname];
      return { ok: cuerpo !== undefined, status: cuerpo === undefined ? 404 : 200, json: async () => cuerpo } as Response;
    }),
  );
}

function montar(clave = "TINNIDROP") {
  const raiz = createRootRoute();
  const ruta = createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle });
  const router = createRouter({
    routeTree: raiz.addChildren([ruta]),
    history: createMemoryHistory({ initialEntries: [`/producto/${clave}`] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

test("resume la fase en una frase y el paso de ahora con su título humano, no el id crudo", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar();
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(await screen.findByText(/FASE 2 · conceptos: el ángulo ganador, 10 conceptos\./)).toBeInTheDocument();
  // El título humano del paso aparece en el resumen de arriba Y en su tarjeta del recorrido:
  // ninguna de las dos veces es el id crudo (F2.etapa-11).
  expect(
    await screen.findAllByText("Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)"),
  ).toHaveLength(2);
  expect((await screen.findAllByText("lo hace Claude")).length).toBeGreaterThanOrEqual(1);
  // El id crudo sigue presente, pero como dato secundario, nunca el único texto del paso.
  expect((await screen.findAllByText("F2.etapa-11")).length).toBeGreaterThanOrEqual(1);
});

test("avisa cuando la data del motor tiene más de 2 días de rezago", async () => {
  servir({
    "/api/productos/TINNIDROP": { ...FLUJO_BASE, motor: { rezago_dias: 4, datos_hasta: "2026-09-17" } },
  });
  montar();
  expect(await screen.findByText(/Data con rezago:/)).toBeInTheDocument();
  expect(screen.getByText(/data de hace 4 días/)).toBeInTheDocument();
});

test("no avisa rezago cuando el motor no trae uno viejo", async () => {
  servir({ "/api/productos/TINNIDROP": { ...FLUJO_BASE, motor: { rezago_dias: 1 } } });
  montar();
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(screen.queryByText(/Data con rezago:/)).not.toBeInTheDocument();
});

test("muestra los avisos que trae flujo.py en una tarjeta cerca del resumen", async () => {
  servir({
    "/api/productos/TINNIDROP": {
      ...FLUJO_BASE,
      avisos: [
        "F2.publicar: Meta YA gastó en una campaña de conceptos de este producto — verificar contra Meta antes de crear nada — …",
      ],
    },
  });
  montar();
  expect(await screen.findByText("Avisos del recorrido")).toBeInTheDocument();
  expect(screen.getByText(/Meta YA gastó en una campaña de conceptos/)).toBeInTheDocument();
});

test("no muestra la tarjeta de avisos cuando flujo.py no trae ninguno", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar();
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(screen.queryByText("Avisos del recorrido")).not.toBeInTheDocument();
});
