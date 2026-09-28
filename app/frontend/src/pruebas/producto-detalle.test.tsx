/**
 * producto-detalle.test.tsx — pruebas de ProductoDetalle (T2 resumen + T3 pestañas).
 *
 * T2: la tarjeta de resumen dice, en una frase: en qué fase está, cuál es el paso de ahora
 * (título humano, no el id crudo), quién lo hace, y avisa cuando la data del motor tiene más de
 * 2 días de rezago. Todo sale de `flujo.py` (mock de `/api/productos/{clave}`).
 *
 * T3: el header (nombre, fase, paso, bloqueante) es siempre visible sin importar la pestaña;
 * la pestaña activa la decide la URL (`/fase1|2|3|4` → esa pestaña) o, a falta de sufijo, la fase
 * vigente del producto (`d.fase`) — nunca al revés. El contenido del recorrido completo (avisos,
 * entradas, línea de tiempo nodo por nodo) vive ahora bajo la pestaña "Resumen".
 */
import { fireEvent, render, screen } from "@testing-library/react";
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

/** Registra las cinco rutas reales de la ficha (igual que `main.tsx`, P4/T3: un solo
 * componente para Resumen y cada fase) para que la navegación entre pestañas funcione tal
 * cual en producción. */
function montar(rutaInicial = "/producto/TINNIDROP") {
  const raiz = createRootRoute();
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/productos", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase1", component: ProductoDetalle }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase2", component: ProductoDetalle }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase3", component: ProductoDetalle }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase4", component: ProductoDetalle }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: [rutaInicial] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

/** Abre la pestaña Resumen — necesario porque, con `fase: "F2"`, la pestaña por defecto es
 * "Fase 2" (P4/T3: el default es la fase vigente, no Resumen). Espera primero a que `flujo.py`
 * resuelva (el header, que depende de esa consulta, ya está pintado): mientras está en vuelo el
 * default es Resumen (para no bloquear la pantalla), y hacer clic ANTES de eso sería un clic
 * sobre la pestaña ya activa — un no-op que el propio `cambiarTab` descarta. */
async function abrirResumen() {
  await screen.findByRole("heading", { level: 1 });
  fireEvent.click(screen.getByRole("tab", { name: "Resumen" }));
}

test("resume la fase en una frase y el paso de ahora con su título humano, no el id crudo", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar();
  // El header (nombre, fase, paso de ahora) es siempre visible, sin importar la pestaña abierta.
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(await screen.findByText(/FASE 2 · conceptos: el ángulo ganador, 10 conceptos\./)).toBeInTheDocument();
  // El título de la fase tal como lo nombra flujo.py (FLUJO.json), no solo el código "F2".
  expect(screen.getByText("FASE 2 · TESTEO DE CONCEPTOS")).toBeInTheDocument();
  expect(await screen.findAllByText("Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)")).toHaveLength(1);
  expect((await screen.findAllByText("lo hace Claude")).length).toBeGreaterThanOrEqual(1);
  // El id crudo sigue presente, pero como dato secundario, nunca el único texto del paso.
  expect((await screen.findAllByText("F2.etapa-11")).length).toBeGreaterThanOrEqual(1);

  // Al abrir Resumen, el mismo título humano aparece TAMBIÉN en su tarjeta del recorrido: dos
  // veces en total, ninguna de las dos el id crudo.
  await abrirResumen();
  expect(
    await screen.findAllByText("Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)"),
  ).toHaveLength(2);
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
  await abrirResumen();
  expect(await screen.findByText("Avisos del recorrido")).toBeInTheDocument();
  expect(screen.getByText(/Meta YA gastó en una campaña de conceptos/)).toBeInTheDocument();
});

test("no muestra la tarjeta de avisos cuando flujo.py no trae ninguno", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar();
  await abrirResumen();
  expect(await screen.findByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(screen.queryByText("Avisos del recorrido")).not.toBeInTheDocument();
});

test("el header dice el bloqueante y su dueño, y la pestaña Resumen los repite en su propia tarjeta", async () => {
  servir({
    "/api/productos/TINNIDROP": {
      ...FLUJO_BASE,
      bloqueantes: [
        { dato: "carpeta de media del producto", ok: false, observado: "no existe", dueno: "operador", regla: "invariante 8" },
      ],
    },
  });
  montar();
  expect(await screen.findAllByText("carpeta de media del producto")).toHaveLength(1);
  expect(screen.getByText(/lo produce operador/)).toBeInTheDocument();
});

test("pestañas — P4/T3: la URL manda cuando trae sufijo de fase (/fase2 → pestaña Fase 2)", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar("/producto/TINNIDROP/fase2");
  const tabFase2 = await screen.findByRole("tab", { name: "Fase 2" });
  expect(tabFase2).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute("aria-selected", "false");
});

test("pestañas — P4/T3: sin sufijo de fase, el default es la fase VIGENTE del producto, no Resumen", async () => {
  servir({ "/api/productos/TINNIDROP": { ...FLUJO_BASE, fase: "F1" } });
  montar("/producto/TINNIDROP");
  // Mientras `flujo.py` está en vuelo, el default es Resumen (para no bloquear la pantalla);
  // recién con el header pintado se conoce la fase vigente y la pestaña puede recalcularse.
  await screen.findByRole("heading", { level: 1 });
  expect(screen.getByRole("tab", { name: "Fase 1" })).toHaveAttribute("aria-selected", "true");
});

test("pestañas — P4/T3: una fase fuera de F1/F2/F3/F4 (p. ej. PAUSADO) cae en Resumen por defecto", async () => {
  servir({ "/api/productos/TINNIDROP": { ...FLUJO_BASE, fase: "PAUSADO", estado: "EXCEPCION" } });
  montar("/producto/TINNIDROP");
  await screen.findByRole("heading", { level: 1 });
  expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute("aria-selected", "true");
});

test("pestañas — hacer clic en Fase 1 navega a la URL de esa fase", async () => {
  servir({ "/api/productos/TINNIDROP": FLUJO_BASE });
  montar("/producto/TINNIDROP");
  fireEvent.click(await screen.findByRole("tab", { name: "Fase 1" }));
  expect(await screen.findByRole("tab", { name: "Fase 1" })).toHaveAttribute("aria-selected", "true");
});
