/**
 * ajustes.test.tsx — pruebas de la pantalla «Ajustes» (`/ajustes`, T5).
 *
 * Verifica las tres secciones: Cuentas (filas del CSV), FanPages (filas del CSV o el estado
 * vacío cuando el archivo no existe todavía en esta carpeta) y Sistema (los enlaces de
 * siempre + la carpeta sobre la que corre la app).
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

import { Ajustes } from "../pantallas/Ajustes";

const CUENTAS = [
  { cuenta_alias: "GTR 7", cuenta_id: "act_1", moneda: "USD", mcp_habilitado: "SI", sube_media_local: "SI", estado_cuenta: "ACTIVA" },
];

const FANPAGES = [
  {
    pagina_num: "1",
    pagina_nombre: "Fitness Masculino",
    identidad: "Sebastian Mora - entrenador de elite",
    rol: "entrenador de elite",
    tono: "Motivacional, directo.",
    logica: "El hombre compra a quien admira.",
    edad_orientacion: "25+",
    page_id: "",
    productos_nicho: "Creatine Monohydrate",
  },
];

function servir(respuestas: Record<string, unknown>) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const ruta = new URL(url, "http://x").pathname;
      const cuerpo = respuestas[ruta];
      if (cuerpo === undefined) {
        return { ok: false, status: 404, json: async () => ({ detail: "no existe" }) } as Response;
      }
      return { ok: true, status: 200, json: async () => cuerpo } as Response;
    }),
  );
}

function montar() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const raiz = createRootRoute();
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/", component: Ajustes }),
    createRoute({ getParentRoute: () => raiz, path: "/ordenes", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/salud", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/guia", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/nuevo", component: () => null }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

test("muestra las cuentas del CSV", async () => {
  servir({ "/api/cuentas": CUENTAS, "/api/fanpages": [], "/api/trabajos": [], "/api/sistema": { base: "/x" } });
  montar();
  expect((await screen.findAllByText("GTR 7")).length).toBeGreaterThan(0);
  expect(screen.getAllByText("USD").length).toBeGreaterThan(0);
});

test("FanPages: estado vacío cuando el CSV no existe en esta carpeta", async () => {
  servir({ "/api/cuentas": [], "/api/fanpages": [], "/api/trabajos": [], "/api/sistema": { base: "/x" } });
  montar();
  expect(
    await screen.findByText("Todavía no hay FanPages declaradas en _DIM_FANPAGES.csv."),
  ).toBeInTheDocument();
});

test("FanPages: filas cuando el CSV sí existe", async () => {
  servir({ "/api/cuentas": [], "/api/fanpages": FANPAGES, "/api/trabajos": [], "/api/sistema": { base: "/x" } });
  montar();
  expect(await screen.findAllByText("Fitness Masculino")).not.toHaveLength(0);
  expect(screen.getAllByText("25+").length).toBeGreaterThan(0);
});

test("Sistema: enlaces de siempre y la carpeta donde corre la app", async () => {
  servir({ "/api/cuentas": [], "/api/fanpages": [], "/api/trabajos": [], "/api/sistema": { base: "/carpeta/del/sistema" } });
  montar();
  expect(await screen.findByRole("link", { name: "Órdenes de hoy" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Trabajos" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Salud del sistema" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Guía" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Nuevo producto" })).toBeInTheDocument();
  expect(await screen.findByText("Corriendo sobre: /carpeta/del/sistema")).toBeInTheDocument();
});

test("Sistema: el badge de Trabajos cuenta los pendientes", async () => {
  servir({
    "/api/cuentas": [],
    "/api/fanpages": [],
    "/api/trabajos": [{ id: "a", pendiente: { tipo: "aprobacion" } }, { id: "b", pendiente: null }],
    "/api/sistema": { base: "/x" },
  });
  montar();
  expect(await screen.findByTitle("Trabajos que esperan tu aprobación o tu respuesta")).toHaveTextContent("1");
});
