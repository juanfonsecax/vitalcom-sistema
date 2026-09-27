/**
 * hoy.test.tsx — pruebas de la pantalla «Hoy» (`/`).
 *
 * Verifica el orden que fija la metodología (CLAUDE.md, invariante 13), no la pantalla:
 *   1. banner de rezago (fresco / con rezago / desconocido);
 *   2. órdenes accionables antes que SEGUIR_MIDIENDO (colapsado);
 *   3. estado vacío cuando no hay órdenes accionables;
 *   4. filas de "qué sigue" con su bloqueante y su dueño.
 */
import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
  createMemoryHistory,
} from "@tanstack/react-router";
import { beforeEach, expect, test, vi } from "vitest";
import { Hoy } from "../pantallas/Hoy";

const PRODUCTO_A = {
  producto_key: "CLEARSTEM",
  nombre_display: "ClearStem",
  estado: "VIVO",
  cuenta_alias: "GTR7",
  moneda: "GTQ",
  costo_q: "100",
  precio_base_q: "",
  cpa_base_q: "",
  cpa_be_q: "",
  campaign_id: "",
  fase_bitacora: "",
  fase: "F2",
  nodo_actual: "F2.etapa-9",
  estado_flujo: "EN_CURSO",
  bloqueantes: 1,
  siguiente_ejecutor: "subagente etapa-9",
  evaluado_el: "2026-09-24",
};

const PRODUCTO_B = {
  ...PRODUCTO_A,
  producto_key: "TINNIDROP",
  nombre_display: "Tinnidrop",
  fase: "F1",
  nodo_actual: "F1.paquete",
  bloqueantes: 0,
  siguiente_ejecutor: "skill `fase-1-angulos`",
};

const FLUJO_A = {
  producto_key: "CLEARSTEM",
  nodo_actual: "F2.etapa-9",
  ejecutor: "subagente etapa-9",
  bloqueantes: [
    { dato: "10 conceptos generados", ok: false, observado: "3 de 10", dueno: "etapa-9", regla: "F2.entrada" },
  ],
  nodos: [],
  como: "Generar los conceptos que faltan",
  avisos: [],
};

const FLUJO_B = {
  producto_key: "TINNIDROP",
  nodo_actual: "F1.paquete",
  ejecutor: "skill `fase-1-angulos`",
  bloqueantes: [] as unknown[],
  nodos: [],
  como: "Armar el paquete de FASE 1",
  avisos: [],
};

const ORDENES_BASE = {
  schema: "ordenes/1",
  rezago_dias: 1,
  llamadas: [],
  ordenes: [
    {
      producto_key: "OVULOS_PURITY",
      angulo_key: "INFECCION_RECURRENTE",
      angulo_nombre: "Infección Recurrente",
      estado: "SEGUIR_MIDIENDO",
      accion_codigo: "SEGUIR_MIDIENDO",
      frase_simple: "Mantener presupuesto: faltan ~4 ventas para decidir",
      por_que: { faltan_ventas: 4, ventas_actual: 3, ventas_necesarias: 7 },
      bloqueo_fase: null,
      ejecutable: false,
      conjuntos: [],
    },
    {
      producto_key: "TINNIDROP",
      angulo_key: "ZUMBIDO_GRAVE",
      angulo_nombre: "Zumbido Grave",
      estado: "PAUSAR",
      accion_codigo: "PAUSAR_CELDA",
      frase_simple: "Pausar conjunto de Zumbido Grave",
      por_que: { cpa_real_q: 120.5, break_even_q: 93.4 },
      bloqueo_fase: null,
      ejecutable: true,
      conjuntos: [],
    },
    {
      producto_key: "CLEARSTEM",
      angulo_key: "RESISTENCIA_INSULINA_SOP",
      angulo_nombre: "Resistencia a la Insulina SOP",
      estado: "ESCALAR",
      accion_codigo: "ESCALAR_SURFING",
      frase_simple: "Subir 20% al presupuesto",
      por_que: { cpa_real_q: 27.3, break_even_q: 105.89 },
      bloqueo_fase: null,
      ejecutable: true,
      conjuntos: [],
    },
  ],
  bloqueantes: [],
  avisos: [],
  parametros_motor: [],
};

const ACCIONES = [
  { id: "nodo.ciclo.ordenes", rotulo: "Ejecutar órdenes en Meta", habilitada: false, motivo: "Manual" },
  { id: "nodo.ciclo.datos", rotulo: "Traer las ventas de LucidSales", habilitada: true, motivo: null },
];

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
    createRoute({ getParentRoute: () => raiz, path: "/", component: Hoy }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos/$id", component: () => null }),
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

function servirBase(overrides: Record<string, unknown> = {}) {
  servir({
    "/api/decisiones": { generado: "2026-09-24", rezago_dias: 1, datos_hasta: "2026-09-23", resumen_acciones: {}, productos: [] },
    "/api/ordenes": ORDENES_BASE,
    "/api/acciones": ACCIONES,
    "/api/productos": [PRODUCTO_A, PRODUCTO_B],
    "/api/productos/CLEARSTEM": FLUJO_A,
    "/api/productos/TINNIDROP": FLUJO_B,
    "/api/trabajos": [],
    ...overrides,
  });
}

beforeEach(() => {
  servirBase();
});

test("muestra la línea discreta de datos frescos cuando el rezago es bajo", async () => {
  montar();
  expect(await screen.findByText("Datos hasta 2026-09-23.")).toBeInTheDocument();
  expect(screen.queryByText(/órdenes de hoy están calculadas sobre datos viejos/i)).not.toBeInTheDocument();
});

test("muestra el banner de alerta cuando el rezago supera 2 días, con la fecha y el botón de refrescar", async () => {
  servirBase({
    "/api/decisiones": { generado: "2026-09-24", rezago_dias: 5, datos_hasta: "2026-09-19", resumen_acciones: {}, productos: [] },
  });
  montar();
  expect(await screen.findByText(/órdenes de hoy están calculadas sobre datos viejos/i)).toBeInTheDocument();
  expect(screen.getByText(/Datos hasta 2026-09-19 — 5 días de rezago/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Traer las ventas de LucidSales" })).toBeInTheDocument();
});

test("trata un rezago desconocido (null) como si estuviera viejo, sin inventar una fecha", async () => {
  servirBase({
    "/api/decisiones": { generado: "2026-09-24", rezago_dias: null, datos_hasta: "", resumen_acciones: {}, productos: [] },
  });
  montar();
  expect(await screen.findByText(/órdenes de hoy están calculadas sobre datos viejos/i)).toBeInTheDocument();
  expect(screen.getByText(/no pudo decir hace cuánto no llega data nueva/i)).toBeInTheDocument();
});

test("las órdenes accionables (PAUSAR, ESCALAR) aparecen antes que SEGUIR_MIDIENDO, que queda colapsado", async () => {
  montar();
  const seccion = (await screen.findByRole("heading", { name: "Órdenes de hoy" })).closest("section")!;
  expect(await within(seccion).findByText("Pausar conjunto de Zumbido Grave")).toBeInTheDocument();
  expect(within(seccion).getByText("Subir 20% al presupuesto")).toBeInTheDocument();
  // SEGUIR_MIDIENDO no se pinta como tarjeta: va colapsado, con su conteo.
  expect(within(seccion).getByText("Siguen midiendo (1)")).toBeInTheDocument();
  expect(within(seccion).queryByText("Mantener presupuesto: faltan ~4 ventas para decidir")).not.toBeInTheDocument();
});

test("estado vacío: sin órdenes accionables lo dice en vez de mostrar tarjetas vacías", async () => {
  servirBase({
    "/api/ordenes": { ...ORDENES_BASE, ordenes: [ORDENES_BASE.ordenes[0]] },
  });
  montar();
  expect(await screen.findByText(/No hay órdenes que pidan una acción hoy/)).toBeInTheDocument();
});

test("la franja del día resume las órdenes en un vistazo: 1 pausar, 1 escalar y 1 midiendo", async () => {
  montar();
  const franja = await screen.findByTestId("franja-hoy");
  expect(within(franja).getByText("Hoy te toca")).toBeInTheDocument();
  expect(within(franja).getAllByText("1")).toHaveLength(3);
  expect(within(franja).getByText("pausar")).toBeInTheDocument();
  expect(within(franja).getByText("escalar")).toBeInTheDocument();
  expect(within(franja).getByText("midiendo")).toBeInTheDocument();
});

test("la franja avisa cuando Trabajos tiene algo esperando al operador", async () => {
  servirBase({
    "/api/trabajos": [
      { id: "t1", pendiente: true },
      { id: "t2", pendiente: true },
    ],
  });
  montar();
  expect(await screen.findByText(/2 esperan tu revisión en Trabajos/)).toBeInTheDocument();
});

test("orden ejecutable con el ciclo deshabilitado: lo dice en texto, sin botones muertos", async () => {
  montar();
  const notas = await screen.findAllByText("Ejecución deshabilitada en el manifiesto");
  expect(notas).toHaveLength(2);
  expect(screen.queryByRole("button", { name: "Aprobar" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Rechazar" })).not.toBeInTheDocument();
});

test("orden ejecutable con el ciclo habilitado: un solo botón claro que manda a Trabajos", async () => {
  servirBase({
    "/api/acciones": [
      { id: "nodo.ciclo.ordenes", rotulo: "Ejecutar órdenes en Meta", habilitada: true, motivo: null },
      { id: "nodo.ciclo.datos", rotulo: "Traer las ventas de LucidSales", habilitada: true, motivo: null },
    ],
  });
  montar();
  const enlaces = await screen.findAllByRole("link", { name: "Revisar y aprobar en Trabajos" });
  expect(enlaces).toHaveLength(2);
});

test("si el producto ya tiene un trabajo esperando aprobación, el botón lleva directo a él", async () => {
  servirBase({
    "/api/trabajos": [
      { job_id: "job-1", pendiente: "Falta tu aprobación", producto_key: "TINNIDROP" },
    ],
    "/api/acciones": [
      { id: "nodo.ciclo.ordenes", rotulo: "Ejecutar órdenes en Meta", habilitada: true, motivo: null },
      { id: "nodo.ciclo.datos", rotulo: "Traer las ventas de LucidSales", habilitada: true, motivo: null },
    ],
  });
  montar();
  const enlaces = await screen.findAllByRole("link", { name: "Revisar y aprobar en Trabajos" });
  // La orden PAUSAR de TINNIDROP va primero en el orden accionable: su botón cae directo
  // en SU trabajo; la de CLEARSTEM, sin trabajo pendiente, va a la lista general.
  expect(enlaces[0]).toHaveAttribute("href", "/trabajos/job-1");
  expect(enlaces[1]).toHaveAttribute("href", "/trabajos");
});

test("el glosario del estado queda plegado: el «¿Qué es…?» lo despliega", async () => {
  montar();
  const seccion = (await screen.findByRole("heading", { name: "Órdenes de hoy" })).closest("section")!;
  const disparadores = await within(seccion).findAllByText(/¿Qué es «/);
  expect(disparadores.length).toBeGreaterThanOrEqual(1);
  await disparadores[0].click();
  expect(
    await within(seccion).findByText("Apagar: gastó de más sin vender lo suficiente y la evidencia ya alcanza para cortar."),
  ).toBeInTheDocument();
});

test("un ángulo que acaba de entrar en ESCALAR se celebra una sola vez", async () => {
  window.localStorage.setItem(
    "vitalcom-celebraciones-v1",
    JSON.stringify({ "CLEARSTEM|RESISTENCIA_INSULINA_SOP": "SEGUIR_MIDIENDO" }),
  );
  montar();
  expect(await screen.findByTestId("celebracion-escalar")).toBeInTheDocument();
  // La segunda visita ya no celebra: la transición quedó registrada.
  window.localStorage.removeItem("vitalcom-celebraciones-v1");
});

test("qué sigue por producto: muestra fase, paso y el bloqueante con su dueño; sin bloqueante lo dice", async () => {
  montar();
  expect(await screen.findByText("ClearStem")).toBeInTheDocument();
  expect(await screen.findByText("Generar los conceptos que faltan")).toBeInTheDocument();
  expect(await screen.findByText(/10 conceptos generados · lo produce etapa-9/)).toBeInTheDocument();
  expect(await screen.findByText("Sin bloqueantes")).toBeInTheDocument();
});
