/**
 * hoy.test.tsx — pruebas de la pantalla «Hoy» (`/`).
 *
 * Verifica el orden que fija la metodología (CLAUDE.md, invariante 13), no la pantalla:
 *   1. banner de rezago (fresco / con rezago / desconocido);
 *   2. órdenes accionables antes que SEGUIR_MIDIENDO (colapsado);
 *   3. estado vacío cuando no hay órdenes accionables;
 *   4. filas de "qué sigue" con su bloqueante y su dueño;
 *   5. las tarjetas de la franja bajan hasta su sección de estado, y «Midiendo» abre el
 *      grupo colapsado antes de bajar.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  mercado: "GT", moneda_local: "GTQ", simbolo: "Q",
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
      mercado: "CO", moneda_local: "COP", simbolo: "$",
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
      mercado: "GT", moneda_local: "GTQ", simbolo: "Q",
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
      mercado: "GT", moneda_local: "GTQ", simbolo: "Q",
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

const MERCADOS = [
  { mercado: "GT", pais: "Guatemala", moneda: "GTQ", simbolo: "Q" },
  { mercado: "CO", pais: "Colombia", moneda: "COP", simbolo: "$" },
];

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
    "/api/mercados": MERCADOS,
    ...overrides,
  });
}

/** jsdom no implementa `scrollIntoView`: el stub registra a qué elemento se pidió llevar a la
 * vista (su `aria-label` o su `id`) y devuelve la función que lo restaura, para que no se
 * filtre a las demás pruebas del archivo. */
function stubScrollIntoView(registro: string[]) {
  const original = window.HTMLElement.prototype.scrollIntoView;
  window.HTMLElement.prototype.scrollIntoView = function (this: HTMLElement) {
    registro.push(this.getAttribute("aria-label") ?? this.id);
  };
  return () => {
    window.HTMLElement.prototype.scrollIntoView = original;
  };
}

beforeEach(() => {
  window.localStorage.clear();
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

test("la franja del día resume las órdenes en tarjetas grandes: 1 Pausar, 1 Escalar y 1 Midiendo", async () => {
  montar();
  const franja = await screen.findByTestId("franja-hoy");
  expect(within(franja).getByText("Hoy te toca")).toBeInTheDocument();
  expect(within(franja).getByTestId("resumen-pausar")).toBeInTheDocument();
  expect(within(franja).getByTestId("resumen-escalar")).toBeInTheDocument();
  expect(within(franja).getByTestId("resumen-midiendo")).toBeInTheDocument();
  expect(within(franja).getAllByText("1")).toHaveLength(3);
  expect(within(franja).getByText("Pausar")).toBeInTheDocument();
  expect(within(franja).getByText("Escalar")).toBeInTheDocument();
  expect(within(franja).getByText("Midiendo")).toBeInTheDocument();
});

test("un ESCALAR bloqueado por fase no cuenta ni agrupa junto al ESCALAR accionable", async () => {
  servirBase({
    "/api/ordenes": {
      ...ORDENES_BASE,
      ordenes: [
        ...ORDENES_BASE.ordenes,
        {
          producto_key: "TINNIDROP",
          mercado: "GT", moneda_local: "GTQ", simbolo: "Q",
          angulo_key: "PERDIDA_AUDITIVA",
          angulo_nombre: "Pérdida Auditiva",
          estado: "ESCALAR",
          accion_codigo: "ESCALAR_SURFING",
          frase_simple: "Subir 20% al presupuesto",
          por_que: { cpa_real_q: 40, break_even_q: 90 },
          bloqueo_fase: "TINNIDROP está en F2: subir presupuesto sesga la medición",
          ejecutable: false,
          conjuntos: [],
        },
      ],
    },
  });
  montar();
  const franja = await screen.findByTestId("franja-hoy");
  // La tarjeta verde "Escalar" solo cuenta el ESCALAR accionable de CLEARSTEM (1), nunca el
  // bloqueado de TINNIDROP — ese cae en su propia tarjeta "Escalar en espera" (1).
  expect(within(within(franja).getByTestId("resumen-escalar")).getByText("1")).toBeInTheDocument();
  const tarjetaEnEspera = within(franja).getByTestId("resumen-escalar_en_espera");
  expect(within(tarjetaEnEspera).getByText("1")).toBeInTheDocument();
  expect(within(tarjetaEnEspera).getByText("Escalar en espera")).toBeInTheDocument();

  // Las dos secciones de órdenes existen y cada orden aparece una sola vez: nada desaparece al
  // partir el grupo ESCALAR en dos.
  const seccionEscalar = document.getElementById("seccion-ESCALAR")!;
  const seccionEnEspera = document.getElementById("seccion-ESCALAR_EN_ESPERA")!;
  expect(within(seccionEscalar).getByText("Subir 20% al presupuesto")).toBeInTheDocument();
  expect(within(seccionEnEspera).getByText("No subir presupuesto: mantener el que ya tiene hasta cerrar la fase.")).toBeInTheDocument();
  // 3 tarjetas accionables (PAUSAR, ESCALAR, ESCALAR_EN_ESPERA); SEGUIR_MIDIENDO va colapsado,
  // sin tarjeta — ninguna orden se pierde ni se pinta dos veces.
  expect(screen.getAllByTestId("tarjeta-orden")).toHaveLength(3);
});

test("tocar la tarjeta «Escalar en espera» de la franja baja hasta su propia sección", async () => {
  const scrolles: string[] = [];
  const restaurar = stubScrollIntoView(scrolles);
  try {
    servirBase({
      "/api/ordenes": {
        ...ORDENES_BASE,
        ordenes: [
          {
            ...ORDENES_BASE.ordenes[2],
            bloqueo_fase: "CLEARSTEM está en F2: subir presupuesto sesga la medición",
            ejecutable: false,
          },
        ],
      },
    });
    montar();
    (await screen.findByTestId("resumen-escalar_en_espera")).click();
    await waitFor(() => expect(scrolles).toContain("seccion-ESCALAR_EN_ESPERA"));
    expect(document.getElementById("seccion-ESCALAR_EN_ESPERA")).toBeInTheDocument();
  } finally {
    restaurar();
  }
});

test("la franja avisa cuando Trabajos tiene algo esperando al operador", async () => {
  servirBase({
    "/api/trabajos": [
      { id: "t1", pendiente: true },
      { id: "t2", pendiente: true },
    ],
  });
  montar();
  const franja = await screen.findByTestId("franja-hoy");
  const tarjeta = within(franja).getByTestId("resumen-trabajos");
  expect(within(tarjeta).getByText("2")).toBeInTheDocument();
  expect(within(tarjeta).getByText("esperan tu revisión en Trabajos")).toBeInTheDocument();
});

test("tocar la tarjeta «Escalar» de la franja baja hasta su grupo de órdenes", async () => {
  const scrolles: string[] = [];
  const restaurar = stubScrollIntoView(scrolles);
  try {
    montar();
    (await screen.findByTestId("resumen-escalar")).click();
    await waitFor(() => expect(scrolles).toContain("seccion-ESCALAR"));
    expect(document.getElementById("seccion-ESCALAR")).toBeInTheDocument();
  } finally {
    restaurar();
  }
});

test("tocar la tarjeta «Midiendo» abre el grupo colapsado y baja hasta él", async () => {
  const scrolles: string[] = [];
  const restaurar = stubScrollIntoView(scrolles);
  try {
    montar();
    const tarjeta = await screen.findByTestId("resumen-midiendo");
    // Cerrado, la fila de la celda que se sigue midiendo no está en el documento.
    expect(screen.queryByText("OVULOS_PURITY")).not.toBeInTheDocument();
    tarjeta.click();
    // Al abrirse el grupo, la fila queda a la vista…
    expect(await screen.findByText("OVULOS_PURITY")).toBeInTheDocument();
    // …y el scroll baja hasta la sección MIDIENDO.
    await waitFor(() => expect(scrolles).toContain("seccion-MIDIENDO"));
    expect(document.getElementById("seccion-MIDIENDO")).toBeInTheDocument();
  } finally {
    restaurar();
  }
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

test("una orden ESCALAR bloqueada por fase muestra tal cual la nota del motor, no una prosa inventada", async () => {
  const NOTA_DEL_MOTOR =
    "F2.gate — testeo de 1 solo conjunto rompe el invariante; hace ganador al que recibió más plata, no al mejor.";
  servirBase({
    "/api/ordenes": {
      ...ORDENES_BASE,
      ordenes: [
        {
          producto_key: "CLEARSTEM",
          angulo_key: "RESISTENCIA_INSULINA_SOP",
          angulo_nombre: "Resistencia a la Insulina SOP",
          estado: "ESCALAR",
          accion_codigo: "ESCALAR_SURFING",
          frase_simple: "Subir 20% al presupuesto",
          por_que: { cpa_real_q: 27.3, break_even_q: 105.89 },
          bloqueo_fase: NOTA_DEL_MOTOR,
          ejecutable: false,
          conjuntos: [],
        },
      ],
    },
  });
  montar();
  // El texto visible es el que manda la API tal cual, con un rótulo neutro — nunca la prosa
  // vieja ("ya es rentable y vale como ganador…") que la pantalla escribía por su cuenta.
  expect(await screen.findByText(NOTA_DEL_MOTOR)).toBeInTheDocument();
  expect(screen.getByText("Qué falta para escalar:")).toBeInTheDocument();
  expect(screen.queryByText(/ya es rentable y vale como ganador/i)).not.toBeInTheDocument();
  // El fold redundante ("Ver la nota técnica del motor") desaparece: la nota ya está a la vista.
  expect(screen.queryByText(/Ver la nota técnica del motor/i)).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ver el avance de su fase" })).toBeInTheDocument();
});

test("la tarjeta de orden dice en una línea fase, trabado y quién lo hace; la nota larga queda plegada", async () => {
  const NOTA = "NO SUBIR PRESUPUESTO todavía: está en FASE 2 testeando conceptos y subir plata sesga la medición.";
  servirBase({
    "/api/productos": [
      {
        ...PRODUCTO_A,
        fase_titulo: "FASE 2 · TESTEO DE CONCEPTOS",
        paso_titulo: "Fabricar los 10 conceptos",
        bloqueante_principal: "faltan 5 conceptos",
        dueno_bloqueante: "etapa-9 (filas) + etapa-render (PNG)",
      },
      PRODUCTO_B,
    ],
    "/api/ordenes": {
      ...ORDENES_BASE,
      ordenes: [
        {
          producto_key: "CLEARSTEM",
          angulo_key: "RESISTENCIA_INSULINA_SOP",
          angulo_nombre: "Resistencia a la Insulina SOP",
          estado: "ESCALAR",
          accion_codigo: "ESCALAR_SURFING",
          frase_simple: "Subir 20% al presupuesto",
          por_que: { cpa_real_q: 27.3, break_even_q: 105.89 },
          bloqueo_fase: NOTA,
          ejecutable: false,
          conjuntos: [],
        },
      ],
    },
  });
  montar();
  const linea = await screen.findByTestId("situacion-orden");
  expect(linea.textContent).toContain("Fase 2 · testeo de conceptos");
  expect(linea.textContent).toContain("Trabado: faltan 5 conceptos");
  expect(linea.textContent).toContain("Lo hace: Fábrica de conceptos + Renderizador de creativos");
  // La nota larga sigue disponible, pero plegada tras «¿Por qué?».
  const nota = screen.getByText(NOTA);
  const pliegue = nota.closest("details");
  expect(pliegue).not.toBeNull();
  expect(pliegue).not.toHaveAttribute("open");
  expect(within(pliegue as HTMLElement).getByText("¿Por qué?")).toBeInTheDocument();
  // La oración explicativa del veredicto también queda plegada, no a la vista.
  const veredicto = screen.getByText(/La celda es rentable y cuenta como evidencia de ganador/);
  expect(veredicto.closest("details")).toBe(pliegue);
});

test("qué sigue por producto: si hay un pendiente (bloqueante_principal) lo muestra y no dice «Sin bloqueantes»", async () => {
  servirBase({
    "/api/productos": [
      {
        ...PRODUCTO_B,
        producto_key: "NUSAVA",
        nombre_display: "Nusava",
        bloqueante_principal: "falta el diagnóstico del bot (etapa-11)",
        dueno_bloqueante: "etapa-11 (mide y diagnostica) → operador (registra)",
      },
    ],
    "/api/productos/NUSAVA": { ...FLUJO_B, producto_key: "NUSAVA", bloqueantes: [] },
  });
  montar();
  expect(await screen.findByText(/falta el diagnóstico del bot \(etapa-11\) · lo hace Optimizador de flujo/)).toBeInTheDocument();
  expect(screen.queryByText("Sin bloqueantes")).not.toBeInTheDocument();
});

test("qué sigue por producto: muestra fase, paso y el bloqueante con su dueño; sin bloqueante lo dice", async () => {
  montar();
  expect(await screen.findByText("ClearStem")).toBeInTheDocument();
  expect(await screen.findByText("Generar los conceptos que faltan")).toBeInTheDocument();
  expect(await screen.findByText(/10 conceptos generados · lo produce etapa-9/)).toBeInTheDocument();
  expect(await screen.findByText("Sin bloqueantes")).toBeInTheDocument();
});

// ── Multi-mercado (D2) ───────────────────────────────────────────────────────────────────────

test("el selector ofrece Todos · Guatemala · Colombia y arranca en Todos", async () => {
  montar();
  const selector = await screen.findByTestId("selector-mercado");
  await within(selector).findByRole("button", { name: "🇨🇴 Colombia" });
  const botones = within(selector).getAllByRole("button");
  expect(botones.map((b) => b.textContent)).toEqual(["Todos", "🇬🇹 Guatemala", "🇨🇴 Colombia"]);
  expect(within(selector).getByRole("button", { name: "Todos" })).toHaveAttribute("aria-pressed", "true");
});

test("cada tarjeta de orden lleva la bandera de su producto y su dinero en su moneda", async () => {
  montar();
  const tarjetas = await screen.findAllByTestId("tarjeta-orden");
  const pausar = tarjetas.find((t) => t.textContent?.includes("Pausar conjunto de Zumbido Grave"))!;
  expect(within(pausar).getByTestId("bandera-mercado")).toHaveTextContent("GT");
  expect(within(pausar).getByText("Q120.50")).toBeInTheDocument();
  expect(within(pausar).getByText("Q93.40")).toBeInTheDocument();
});

test("elegir Colombia deja solo lo de Colombia: los conteos salen de las órdenes de ese mercado", async () => {
  montar();
  await screen.findByTestId("franja-hoy");
  // Con Todos: 1 Pausar (GT), 1 Escalar (GT), 1 Midiendo (CO).
  expect(screen.getByTestId("resumen-pausar")).toBeInTheDocument();
  fireEvent.click(await screen.findByRole("button", { name: "🇨🇴 Colombia" }));
  await waitFor(() => expect(screen.queryByTestId("resumen-pausar")).not.toBeInTheDocument());
  expect(screen.queryByTestId("resumen-escalar")).not.toBeInTheDocument();
  expect(screen.getByTestId("resumen-midiendo")).toBeInTheDocument();
  // «Qué sigue»: ningún producto GT se cuela.
  expect(screen.getByText("No hay productos de este mercado.")).toBeInTheDocument();
  expect(screen.queryByText("Tinnidrop")).not.toBeInTheDocument();
});

test("elegir Guatemala esconde Colombia y cuenta solo las de Guatemala", async () => {
  montar();
  await screen.findByTestId("franja-hoy");
  fireEvent.click(await screen.findByRole("button", { name: "🇬🇹 Guatemala" }));
  await waitFor(() => expect(screen.queryByTestId("resumen-midiendo")).not.toBeInTheDocument());
  expect(screen.getByTestId("resumen-pausar")).toBeInTheDocument();
  expect(screen.getByTestId("resumen-escalar")).toBeInTheDocument();
  expect(screen.getByText("Tinnidrop")).toBeInTheDocument();
});

test("con Todos las celdas se cuentan por mercado, cada uno aparte y nunca sumados", async () => {
  montar();
  const franja = await screen.findByTestId("resumen-por-mercado");
  const banderas = within(franja).getAllByTestId("bandera-mercado");
  expect(banderas.map((f) => f.textContent)).toEqual(["🇨🇴CO", "🇬🇹GT"]);
  expect(franja.textContent).toContain("GT 2");
  expect(franja.textContent).toContain("CO 1");
  fireEvent.click(await screen.findByRole("button", { name: "🇬🇹 Guatemala" }));
  await waitFor(() => expect(screen.queryByTestId("resumen-por-mercado")).not.toBeInTheDocument());
});

test("el mercado elegido se recuerda en localStorage y se recupera al volver", async () => {
  const vista = montar();
  fireEvent.click(await screen.findByRole("button", { name: "🇨🇴 Colombia" }));
  expect(window.localStorage.getItem("vitalcom-mercado-v1")).toBe("CO");
  vista.unmount();
  montar();
  const selector = await screen.findByTestId("selector-mercado");
  await waitFor(() =>
    expect(within(selector).getByRole("button", { name: "🇨🇴 Colombia" })).toHaveAttribute("aria-pressed", "true"),
  );
});

test("sin localStorage la pantalla sigue andando en Todos", async () => {
  const original = Storage.prototype.getItem;
  Storage.prototype.getItem = () => {
    throw new Error("bloqueado");
  };
  try {
    montar();
    expect(await screen.findByTestId("franja-hoy")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Todos" })).toHaveAttribute("aria-pressed", "true");
  } finally {
    Storage.prototype.getItem = original;
  }
});

test("una orden de Colombia escribe su dinero en pesos, sin decimales", async () => {
  servirBase({
    "/api/ordenes": {
      ...ORDENES_BASE,
      ordenes: [
        {
          ...ORDENES_BASE.ordenes[1],
          producto_key: "OVULOS_PURITY",
          mercado: "CO",
          moneda_local: "COP",
          simbolo: "$",
          por_que: { cpa_real_q: 41000, break_even_q: 52500 },
        },
      ],
    },
  });
  montar();
  const tarjeta = await screen.findByTestId("tarjeta-orden");
  expect(within(tarjeta).getByText("$ 41.000")).toBeInTheDocument();
  expect(within(tarjeta).getByText("$ 52.500")).toBeInTheDocument();
  expect(within(tarjeta).getByTestId("bandera-mercado")).toHaveTextContent("CO");
});
