/**
 * El Tablero muestra lo que dice la API, sin adornarlo.
 *
 * Lo que se verifica: que la fase y el paso aparezcan tal cual llegan, que un bloqueante se
 * vea con el nombre de su dueño, y que la data vieja se avise en palabras. La API se simula:
 * lo que la API diga lo mismo que los CSV ya lo prueba el backend (`test_api_espeja_los_csv`).
 */
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
  createMemoryHistory,
} from "@tanstack/react-router";
import { beforeEach, expect, test, vi } from "vitest";
import { Tablero } from "../pantallas/Tablero";

const PRODUCTO = {
  producto_key: "OVULOS_PURITY",
  nombre_display: "Óvulos Purity Hernatura",
  estado: "NUEVO",
  cuenta_alias: "EXTERNA",
  moneda: "GTQ",
  costo_q: "7000",
  precio_base_q: "",
  cpa_base_q: "",
  cpa_be_q: "",
  campaign_id: "",
  fase_bitacora: "",
  fase: "F1",
  nodo_actual: "F1.paquete",
  estado_flujo: "LISTO_PARA_EJECUTAR",
  bloqueantes: 0,
  siguiente_ejecutor: "skill `fase-1-angulos`",
  evaluado_el: "2026-09-17",
};

const FLUJO = {
  producto_key: "OVULOS_PURITY",
  nombre: "Óvulos Purity Hernatura",
  fase: "F1",
  nodo_actual: "F1.paquete",
  estado: "LISTO_PARA_EJECUTAR",
  ejecutor: "skill `fase-1-angulos`",
  bloqueantes: [] as unknown[],
  falta_para_cumplir: [{ dato: "break-even calculado (cpa_be_q)", ok: false, observado: "vacío", dueno: "etapa-guardar-producto", regla: "invariante 2" }],
  entradas: [],
  nodos: [],
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

function montar() {
  const raiz = createRootRoute();
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/", component: Tablero }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: () => null }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  servir({
    "/api/productos": [PRODUCTO],
    "/api/productos/OVULOS_PURITY": FLUJO,
    "/api/decisiones": { generado: "2026-09-17", rezago_dias: 2, datos_hasta: "2026-09-15", resumen_acciones: {}, productos: [] },
  });
});

test("muestra la fase y el paso vigentes tal cual llegan", async () => {
  montar();
  expect(await screen.findByText("Óvulos Purity Hernatura")).toBeInTheDocument();
  expect(await screen.findByText("F1")).toBeInTheDocument();
  expect(await screen.findByText("F1.paquete")).toBeInTheDocument();
  expect(await screen.findByText("listo para ejecutar")).toBeInTheDocument();
});

test("dice quién hace el paso siguiente, sin esconder el ejecutor crudo", async () => {
  montar();
  expect(await screen.findByText("lo hace Claude")).toBeInTheDocument();
  expect(await screen.findByText("skill `fase-1-angulos`")).toBeInTheDocument();
});

test("avisa la edad de la data en palabras", async () => {
  montar();
  expect(await screen.findByText(/data de hace 2 días/)).toBeInTheDocument();
});

test("un bloqueante se muestra con el dueño del dato que falta", async () => {
  servir({
    "/api/productos": [{ ...PRODUCTO, estado_flujo: "BLOQUEADO", bloqueantes: 1 }],
    "/api/productos/OVULOS_PURITY": {
      ...FLUJO,
      estado: "BLOQUEADO",
      bloqueantes: [
        {
          dato: "carpeta de media del producto",
          ok: false,
          observado: "no existe Ads/MEDIA_OVULOSPURITY",
          dueno: "operador · Ads/MEDIA_[PRODUCTO]/",
          regla: "invariante 8",
        },
      ],
    },
    "/api/decisiones": { generado: "2026-09-17", rezago_dias: 0, resumen_acciones: {}, productos: [] },
  });
  montar();
  expect(await screen.findByText("carpeta de media del producto")).toBeInTheDocument();
  expect(
    await screen.findByText(/lo produce operador · Ads\/MEDIA_\[PRODUCTO\]\//),
  ).toBeInTheDocument();
  expect(await screen.findByText("bloqueado")).toBeInTheDocument();
});
