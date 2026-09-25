/**
 * productos.test.tsx — la tabla de Productos (P4/T3, reemplaza tablero.test.tsx).
 *
 * Lo que se verifica: que cada fila diga, tal cual llega de la API, la fase, el paso vigente,
 * el estado, el bloqueante con su dueño y quién sigue; que el buscador filtre por texto; que
 * ordenar por columna cambie el orden de las filas; que cada fila enlace a su ficha; y que el
 * botón "Nuevo producto" y el glosario del paso ("nodo") sigan presentes — igual que antes con
 * el grid de tarjetas de Tablero, solo que ahora en una fila por producto.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
  createMemoryHistory,
} from "@tanstack/react-router";
import { beforeEach, expect, test, vi } from "vitest";
import { Productos } from "../pantallas/Productos";

const OVULOS = {
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

const TINNIDROP = {
  ...OVULOS,
  producto_key: "TINNIDROP",
  nombre_display: "Tinnidrop Importado Original",
  fase: "F2",
  nodo_actual: "F2.etapa-11",
  estado_flujo: "BLOQUEADO",
  bloqueantes: 1,
  siguiente_ejecutor: "subagente `etapa-11`",
};

const FLUJO_OVULOS = {
  producto_key: "OVULOS_PURITY",
  nombre: "Óvulos Purity Hernatura",
  fase: "F1",
  nodo_actual: "F1.paquete",
  estado: "LISTO_PARA_EJECUTAR",
  ejecutor: "skill `fase-1-angulos`",
  bloqueantes: [] as unknown[],
  falta_para_cumplir: [],
  entradas: [],
  nodos: [],
  avisos: [],
  ordenes: [],
};

const FLUJO_TINNIDROP = {
  ...FLUJO_OVULOS,
  producto_key: "TINNIDROP",
  nombre: "Tinnidrop Importado Original",
  fase: "F2",
  nodo_actual: "F2.etapa-11",
  estado: "BLOQUEADO",
  ejecutor: "subagente `etapa-11`",
  bloqueantes: [
    {
      dato: "carpeta de media del producto",
      ok: false,
      observado: "no existe Ads/MEDIA_TINNIDROP",
      dueno: "operador · Ads/MEDIA_[PRODUCTO]/",
      regla: "invariante 8",
    },
  ],
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
    createRoute({ getParentRoute: () => raiz, path: "/productos", component: Productos }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/nuevo", component: () => null }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: ["/productos"] }),
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
    "/api/productos": [OVULOS, TINNIDROP],
    "/api/productos/OVULOS_PURITY": FLUJO_OVULOS,
    "/api/productos/TINNIDROP": FLUJO_TINNIDROP,
    "/api/decisiones": { generado: "2026-09-17", rezago_dias: 2, datos_hasta: "2026-09-15", resumen_acciones: {}, productos: [] },
  });
});

test("cada fila muestra la fase, el paso, el estado y quién sigue tal cual llegan", async () => {
  montar();
  expect(await screen.findByRole("heading", { name: "Portafolio" })).toBeInTheDocument();
  expect(await screen.findByText("Óvulos Purity Hernatura")).toBeInTheDocument();
  // La fase se ve corta en la tabla (código), con la frase completa como tooltip.
  const filaOvulos = screen.getByText("Óvulos Purity Hernatura").closest("tr")!;
  expect(within(filaOvulos).getByText("F1")).toHaveAttribute(
    "title",
    expect.stringContaining("FASE 1 · ángulos"),
  );
  expect(within(filaOvulos).getByText("F1.paquete")).toBeInTheDocument();
  expect(within(filaOvulos).getByText("listo para ejecutar")).toBeInTheDocument();
  expect(within(filaOvulos).getByText("lo hace Claude")).toBeInTheDocument();
  expect(within(filaOvulos).getByText("skill `fase-1-angulos`")).toBeInTheDocument();
});

test("un bloqueante se muestra con el dueño del dato que falta", async () => {
  montar();
  const filaTinnidrop = (await screen.findByText("Tinnidrop Importado Original")).closest("tr")!;
  // La celda "Esto lo frena" depende de su propia consulta por producto (`/api/productos/{clave}`):
  // arranca en "…" y resuelve después, por eso `findByText` (con reintentos) y no `getByText`.
  expect(await within(filaTinnidrop).findByText(/carpeta de media del producto/)).toBeInTheDocument();
  expect(within(filaTinnidrop).getByText(/lo produce operador/)).toBeInTheDocument();
  expect(within(filaTinnidrop).getByText("bloqueado")).toBeInTheDocument();
});

test("sin bloqueantes, la fila dice que nada lo frena", async () => {
  montar();
  const filaOvulos = (await screen.findByText("Óvulos Purity Hernatura")).closest("tr")!;
  expect(await within(filaOvulos).findByText("Nada lo frena")).toBeInTheDocument();
});

test("avisa la edad de la data del sistema en el header", async () => {
  montar();
  expect(await screen.findByText(/data de hace 2 días/)).toBeInTheDocument();
});

test("avisa el rezago DE ESE producto cuando su propio motor lo trae en más de 2 días", async () => {
  servir({
    "/api/productos": [OVULOS, TINNIDROP],
    "/api/productos/OVULOS_PURITY": { ...FLUJO_OVULOS, motor: { rezago_dias: 5, datos_hasta: "2026-09-12" } },
    "/api/productos/TINNIDROP": FLUJO_TINNIDROP,
    "/api/decisiones": { generado: "2026-09-17", rezago_dias: 0, resumen_acciones: {}, productos: [] },
  });
  montar();
  const filaOvulos = (await screen.findByText("Óvulos Purity Hernatura")).closest("tr")!;
  expect(await within(filaOvulos).findByText("rezago")).toHaveAttribute(
    "title",
    expect.stringContaining("5 días"),
  );
});

test("el buscador filtra por producto, fase o estado", async () => {
  montar();
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  const buscador = screen.getByPlaceholderText(/Buscar por producto/);
  fireEvent.change(buscador, { target: { value: "OVULOS" } });
  expect(screen.getByText("Óvulos Purity Hernatura")).toBeInTheDocument();
  expect(screen.queryByText("Tinnidrop Importado Original")).not.toBeInTheDocument();
});

test("el buscador sin coincidencias muestra el estado vacío, sin inventar filas", async () => {
  montar();
  await screen.findByText("Óvulos Purity Hernatura");
  const buscador = screen.getByPlaceholderText(/Buscar por producto/);
  fireEvent.change(buscador, { target: { value: "no-existe-este-producto" } });
  expect(screen.getByText("Ningún producto coincide con la búsqueda.")).toBeInTheDocument();
});

test("el botón «Nuevo producto» enlaza a /nuevo", async () => {
  montar();
  const boton = await screen.findByRole("link", { name: "Nuevo producto" });
  expect(boton).toHaveAttribute("href", "/nuevo");
});

test("cada producto enlaza a su ficha", async () => {
  montar();
  const enlace = await screen.findByRole("link", { name: /Óvulos Purity Hernatura/ });
  expect(enlace).toHaveAttribute("href", "/producto/OVULOS_PURITY");
});

test("el glosario explica «paso del flujo» al hacer clic en la (i)", async () => {
  montar();
  await screen.findByText("Óvulos Purity Hernatura");
  fireEvent.click(screen.getByRole("button", { name: "Qué es paso del flujo" }));
  expect(screen.getByRole("tooltip")).toHaveTextContent("grafo declarado");
});

test("ordenar por Fase cambia el orden de las filas", async () => {
  // TINNIDROP (F2) llega primero de la API: si ordenar no hiciera nada, seguiría primero.
  servir({
    "/api/productos": [TINNIDROP, OVULOS],
    "/api/productos/OVULOS_PURITY": FLUJO_OVULOS,
    "/api/productos/TINNIDROP": FLUJO_TINNIDROP,
    "/api/decisiones": { generado: "2026-09-17", rezago_dias: 2, datos_hasta: "2026-09-15", resumen_acciones: {}, productos: [] },
  });
  montar();
  await screen.findByText("Óvulos Purity Hernatura");
  const primeraFilaDeDatos = () => screen.getAllByRole("row")[1].textContent ?? "";
  expect(primeraFilaDeDatos()).toContain("TINNIDROP");

  const encabezadoFase = screen.getByRole("columnheader", { name: /Fase/ });
  fireEvent.click(within(encabezadoFase).getByRole("button"));

  // F1 ordena antes que F2 (ascendente): OVULOS_PURITY pasa a ser la primera fila.
  expect(primeraFilaDeDatos()).toContain("OVULOS_PURITY");
});
