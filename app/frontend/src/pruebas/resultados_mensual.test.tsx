/**
 * resultados_mensual.test.tsx — la vista «Mes a mes» de Resultados.
 *
 * Verifica lo que decide la metodología, no el dibujo: cada número sale tal cual de
 * `gen_pl_mensual.py --json` (`GET /api/resultados/mensual`), un mes sin Dropi muestra «—» y no un
 * cero, la bandera PRELIMINAR y la lista de faltantes viajan del script, el retiro personal queda
 * aparte del resultado y Colombia no inventa cifras.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, test, vi } from "vitest";
import { Resultados } from "../pantallas/Resultados";

const MERCADOS = [
  { mercado: "GT", pais: "Guatemala", moneda: "GTQ", simbolo: "Q" },
  { mercado: "CO", pais: "Colombia", moneda: "COP", simbolo: "$" },
];

const SIN_DETALLE = { q: 0, detalle: [] };

const SIN_CARTERA = {
  cubre_mes: false,
  saldo_cierre_q: null,
  fecha_corte: null,
  retiros_personales_q: null,
  transferencias_propias_q: null,
  sin_clasificar_q: null,
  retiros: [],
  devoluciones: { origen: null, reales: 0, estimadas: 0 },
};

const CARTERA_SEPTIEMBRE = {
  cubre_mes: true,
  saldo_cierre_q: 94867.12,
  fecha_corte: "2026-09-30",
  retiros_personales_q: 5000,
  transferencias_propias_q: 0,
  sin_clasificar_q: 0,
  retiros: [{ fecha: "2026-09-14", hora: "10:11", concepto: "retiro papa", monto_q: 5000, clasificacion: "RETIRO_PERSONAL" }],
  devoluciones: { origen: "MIXTO", reales: 50, estimadas: 1 },
};

const CARTERA_OCTUBRE = {
  cubre_mes: true,
  saldo_cierre_q: 7530.08,
  fecha_corte: "2026-10-13",
  retiros_personales_q: 5000,
  transferencias_propias_q: 90000,
  sin_clasificar_q: 70,
  retiros: [
    { fecha: "2026-10-01", hora: "08:28", concepto: "Retiro a LLC DFF VENTURES RETIRO PROPIO", monto_q: 90000, clasificacion: "TRANSFERENCIA_PROPIA" },
    { fecha: "2026-10-09", hora: "14:38", concepto: "Retiro papa", monto_q: 5000, clasificacion: "RETIRO_PERSONAL" },
    { fecha: "2026-10-12", hora: "09:00", concepto: "pago raro", monto_q: 70, clasificacion: "SIN_CLASIFICAR" },
  ],
  devoluciones: { origen: "REAL", reales: 3, estimadas: 0 },
};

const AGOSTO = {
  mes: "2026-08",
  desde: "2026-08-01",
  hasta: "2026-08-31",
  preliminar: null,
  edad_dias: null,
  dias_maduro_umbral: 10,
  ordenes: { total: 0, entregadas: 0, devueltas: 0, en_transito: 0, pct_resuelto: null },
  venta_entregada_q: null,
  costo_producto_q: null,
  flete_q: null,
  margen_logistico_q: null,
  devoluciones_q: null,
  personal_q: null,
  otros_q: null,
  costos_operativos_q: null,
  margen_contribucion_q: null,
  publicidad: { usd: 1978.3, q: 15075, meta_usd: 698.92, lucidsales_fallback_usd: 1279.38, tasa: 7.62 },
  margen_operativo_q: null,
  banco_facebook: { usd: 1871.89, cargos: 75 },
  gastos_fijos: { q: 364, detalle: [] },
  retiros_personales: {
    q: 6870,
    detalle: [{ nombre: "MINIMED GEDIATRIA", monto_usd: 901.59, monto_q: 6870, categoria: "retiro_socio", mercado: "COMPARTIDO", parte: 1 }],
  },
  cargos_sin_clasificar: [],
  cartera: SIN_CARTERA,
  resultado_neto_q: null,
  por_producto: [],
  faltantes: ["Sin órdenes de Dropi en 2026-08: cargá el export de Dropi que cubra el mes (ingerir_dropi.py)."],
};

const SEPTIEMBRE = {
  mes: "2026-09",
  desde: "2026-09-01",
  hasta: "2026-09-30",
  preliminar: false,
  edad_dias: 13,
  dias_maduro_umbral: 10,
  ordenes: { total: 306, entregadas: 249, devueltas: 51, en_transito: 5, pct_resuelto: 98.4 },
  venta_entregada_q: 56241,
  costo_producto_q: 17473,
  flete_q: 8934,
  margen_logistico_q: 29834,
  devoluciones_q: 1429,
  personal_q: 996,
  otros_q: 518,
  costos_operativos_q: 29350,
  margen_contribucion_q: 26891,
  publicidad: { usd: 2188.04, q: 16673, meta_usd: 2188.04, lucidsales_fallback_usd: 0, tasa: 7.62 },
  margen_operativo_q: 10218,
  banco_facebook: { usd: 2193.06, cargos: 114 },
  gastos_fijos: {
    q: 1629,
    detalle: [
      { nombre: "THE LUCID HOLDING", monto_usd: 88, monto_q: 670.56, categoria: "software", mercado: "COMPARTIDO", parte: 1 },
      { nombre: "Proxy-Cheap", monto_usd: 52.27, monto_q: 398.3, categoria: "infraestructura", mercado: "COMPARTIDO", parte: 1 },
    ],
  },
  retiros_personales: SIN_DETALLE,
  cargos_sin_clasificar: [],
  cartera: CARTERA_SEPTIEMBRE,
  resultado_neto_q: 8589,
  por_producto: [
    {
      producto_key: "CLEARSTEM", ordenes: 114, entregadas: 95, devueltas: 19, en_transito: 0,
      venta_entregada_q: 22131, margen_antes_publicidad_q: 11000, pauta_q: 5000, ganancia_q: 4824,
    },
    {
      producto_key: "TINNIDROP", ordenes: 141, entregadas: 114, devueltas: 27, en_transito: 0,
      venta_entregada_q: 24419, margen_antes_publicidad_q: 9000, pauta_q: 7000, ganancia_q: 2438,
    },
  ],
  faltantes: [],
};

const OCTUBRE = {
  ...SEPTIEMBRE,
  mes: "2026-10",
  desde: "2026-10-01",
  hasta: "2026-10-31",
  preliminar: true,
  edad_dias: 0,
  venta_entregada_q: 9765,
  resultado_neto_q: 2295,
  gastos_fijos: SIN_DETALLE,
  cartera: CARTERA_OCTUBRE,
  banco_facebook: { usd: 141.31, cargos: 8 },
  por_producto: [
    {
      producto_key: "NUSAVA", ordenes: 5, entregadas: 4, devueltas: 1, en_transito: 0,
      venta_entregada_q: 900, margen_antes_publicidad_q: 400, pauta_q: 36, ganancia_q: 364,
    },
  ],
  faltantes: ["Mes en curso (datos hasta el 2026-10-13): el resultado todavía puede cambiar."],
};

const MENSUAL_GT = {
  mercado: "GT",
  moneda: "GTQ",
  generado: "2026-10-13",
  meses: [AGOSTO, SEPTIEMBRE, OCTUBRE],
  faltantes: [],
  cobertura: {
    dropi: { desde: "2026-09-01", hasta: "2026-10-13", ordenes: 359 },
    banco: { desde: "2026-08-06", hasta: "2026-10-12", movimientos: 207 },
  },
};

const MENSUAL_CO = {
  mercado: "CO",
  moneda: "COP",
  generado: "2026-10-13",
  meses: [],
  faltantes: ["Colombia: sin datos todavía. Hoy solo GT tiene órdenes de Dropi y extracto bancario cargados."],
  cobertura: {},
};

type Respuesta = unknown | { estado: number };

function servir(respuestas: Record<string, Respuesta>) {
  const fetchFalso = vi.fn(async (url: string, init?: RequestInit) => {
    const direccion = new URL(url, "http://x");
    const ruta = direccion.pathname;
    const clave = direccion.searchParams.get("mercado") ? `${ruta}?mercado=${direccion.searchParams.get("mercado")}` : ruta;
    const cuerpo = respuestas[clave] ?? respuestas[ruta];
    if (cuerpo === undefined) {
      return { ok: false, status: 404, json: async () => ({ detail: "no hay" }) } as Response;
    }
    if (typeof cuerpo === "object" && cuerpo !== null && "estado" in cuerpo) {
      const { estado } = cuerpo as { estado: number };
      return { ok: false, status: estado, json: async () => ({ detail: "algo falló" }) } as Response;
    }
    void init;
    return { ok: true, status: 200, json: async () => cuerpo } as Response;
  });
  vi.stubGlobal("fetch", fetchFalso);
  return fetchFalso;
}

function montar() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <Resultados />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": MENSUAL_GT,
    "/api/resultados/mensual?mercado=CO": MENSUAL_CO,
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
});

test("la vista mes a mes es la de entrada y trae todos los rubros del estado de resultados", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  for (const rubro of [
    "Venta bruta entregada",
    "Costo de producto",
    "Flete de entrega",
    "Margen logístico",
    "Devoluciones",
    "Personal",
    "Otros gastos operativos",
    "Margen de contribución",
    "Publicidad",
    "Margen operativo",
    "Gastos fijos",
    "Resultado neto",
    "El banco cobró Facebook",
  ]) {
    expect(within(tabla).getByText(rubro)).toBeInTheDocument();
  }
  expect(screen.getByRole("tab", { name: "Mes a mes" })).toHaveAttribute("aria-selected", "true");
});

test("los montos salen tal cual del script, en quetzales, y el banco en dólares", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  expect(within(tabla).getByText("Q56,241")).toBeInTheDocument();
  expect(within(tabla).getByText("Q8,589")).toBeInTheDocument();
  expect(within(tabla).getByText("$2,193.06")).toBeInTheDocument();
  expect(within(tabla).getByText("$1,871.89")).toBeInTheDocument();
});

test("un mes sin órdenes de Dropi muestra guiones, no ceros, y no pinta resultado", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  const fila = within(tabla).getByText("Venta bruta entregada").closest("tr")!;
  const celdas = within(fila).getAllByRole("cell");
  expect(celdas[1]).toHaveTextContent("—");
  expect(celdas[2]).toHaveTextContent("Q56,241");
});

test("el mes que el script marca preliminar lleva la insignia; el maduro no", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  expect(screen.getAllByText("Preliminar")).toHaveLength(1);
  const cabecera = screen.getByRole("button", { name: /oct 2026/i }).closest("th")!;
  expect(within(cabecera).getByText("Preliminar")).toBeInTheDocument();
});

test("el retiro personal se muestra aparte, fuera de las líneas del resultado", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  const fila = within(tabla).getByText(/Retiros personales del banco/).closest("tr")!;
  expect(fila).toHaveTextContent("Q6,870");
  expect(fila).toHaveTextContent("fuera del resultado");
  // el neto de agosto sigue sin dato: el retiro no lo toca
  const neto = within(tabla).getByText("Resultado neto").closest("tr")!;
  expect(within(neto).getAllByRole("cell")[1]).toHaveTextContent("—");
});

test("el detalle del mes elegido trae el desglose por producto y la fuente de la pauta", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  // por defecto: el último mes con resultado (octubre); se elige septiembre
  fireEvent.click(screen.getByRole("button", { name: /sep 2026/i }));
  const detalle = await screen.findByTestId("detalle-del-mes");
  expect(within(detalle).getByText("CLEARSTEM")).toBeInTheDocument();
  expect(within(detalle).getByText("TINNIDROP")).toBeInTheDocument();
  expect(within(detalle).queryByText("NUSAVA")).not.toBeInTheDocument();
  expect(within(detalle).getByText("Q4,824")).toBeInTheDocument();
  expect(detalle).toHaveTextContent("Meta $2,188.04");
  expect(detalle).toHaveTextContent("LucidSales");
  expect(detalle).toHaveTextContent("THE LUCID HOLDING");
});

test("los faltantes del script se listan tal cual", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  fireEvent.click(screen.getByRole("button", { name: /ago 2026/i }));
  const faltantes = await screen.findByTestId("faltantes");
  expect(faltantes).toHaveTextContent("Sin órdenes de Dropi en 2026-08");
});

test("hay un gráfico mes a mes", async () => {
  montar();
  expect(await screen.findByTestId("grafico-mensual")).toBeInTheDocument();
});

test("Colombia pide su propio mercado y sale sin datos, sin cifras de Guatemala", async () => {
  const fetchFalso = servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": MENSUAL_GT,
    "/api/resultados/mensual?mercado=CO": MENSUAL_CO,
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
  montar();
  await screen.findByTestId("tabla-mensual");
  fireEvent.click(await screen.findByRole("button", { name: "🇨🇴 Colombia" }));
  const vacio = await screen.findByTestId("mensual-sin-datos");
  expect(vacio).toHaveTextContent("sin datos todavía");
  expect(screen.queryByTestId("tabla-mensual")).not.toBeInTheDocument();
  expect(screen.queryByText("Q56,241")).not.toBeInTheDocument();
  const pedidos = fetchFalso.mock.calls.map(([url]) => String(url));
  expect(pedidos.some((u) => u.includes("/api/resultados/mensual?mercado=CO"))).toBe(true);
});

test("subir un export de Dropi lo manda a guardar y refresca", async () => {
  const fetchFalso = servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": MENSUAL_GT,
    "/api/resultados/mensual/cargar": { dropi: { nuevas: 3 } },
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
  montar();
  await screen.findByTestId("tabla-mensual");
  const entrada = screen.getByLabelText(/export de órdenes de dropi/i);
  fireEvent.change(entrada, { target: { files: [new File(["x"], "ordenes.xlsx")] } });
  fireEvent.click(screen.getByRole("button", { name: /guardar en el historial/i }));
  await waitFor(() => {
    const llamada = fetchFalso.mock.calls.find(([url]) => String(url).includes("/mensual/cargar"));
    expect(llamada).toBeTruthy();
    expect((llamada![1] as RequestInit).method).toBe("POST");
  });
  expect(await screen.findByText(/3 órdenes nuevas/i)).toBeInTheDocument();
});

test("sin ningún archivo el botón de guardar está apagado", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  expect(screen.getByRole("button", { name: /guardar en el historial/i })).toBeDisabled();
});

test("un error real del script se muestra como falla, no como estado vacío", async () => {
  servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": { estado: 503 },
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
  montar();
  expect(await screen.findByText(/no pude leer el sistema/i)).toBeInTheDocument();
});

test("los movimientos de caja van en su propia sección, después del resultado neto, y dicen que no afectan la ganancia", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  const seccion = within(tabla).getByText("Movimientos de caja (no afectan la ganancia)");
  const neto = within(tabla).getByText("Resultado neto");
  expect(neto.compareDocumentPosition(seccion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  for (const rubro of [
    "Retiros personales desde Dropi",
    "Transferencias a cuenta propia",
    "Retiros sin clasificar",
    "Saldo de la billetera de Dropi",
  ]) {
    const fila = within(tabla).getByText(rubro).closest("tr")!;
    expect(seccion.compareDocumentPosition(fila) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  }
});

test("la billetera de Dropi muestra retiros, transferencias, sin clasificar y saldo tal cual; un mes sin cartera, guiones", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  const celdas = (rotulo: string) => within(within(tabla).getByText(rotulo).closest("tr")!).getAllByRole("cell");
  // columnas: rótulo, ago (sin cartera), sep, oct
  expect(celdas("Retiros personales desde Dropi").map((c) => c.textContent)).toEqual(
    expect.arrayContaining(["—", "Q5,000"]),
  );
  expect(celdas("Retiros personales desde Dropi")[1]).toHaveTextContent("—");
  expect(celdas("Retiros personales desde Dropi")[3]).toHaveTextContent("Q5,000");
  expect(celdas("Transferencias a cuenta propia")[3]).toHaveTextContent("Q90,000");
  expect(celdas("Retiros sin clasificar")[3]).toHaveTextContent("Q70");
  expect(celdas("Saldo de la billetera de Dropi")[1]).toHaveTextContent("—");
  expect(celdas("Saldo de la billetera de Dropi")[2]).toHaveTextContent("Q94,867");
  expect(celdas("Saldo de la billetera de Dropi")[3]).toHaveTextContent("Q7,530");
});

test("el costo de las devoluciones dice si es real, mixto o estimado", async () => {
  montar();
  const tabla = await screen.findByTestId("tabla-mensual");
  const fila = within(tabla).getByText("Devoluciones").closest("tr")!;
  const celdas = within(fila).getAllByRole("cell");
  expect(celdas[2]).toHaveTextContent("50 de 51 cobradas en la billetera");
  expect(celdas[3]).toHaveTextContent("costo real de la billetera");
  expect(celdas[1]).not.toHaveTextContent("billetera");
});

test("el detalle del mes lista los retiros de la billetera y marca el que no se pudo clasificar", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  // por defecto: el último mes con resultado (octubre)
  const detalle = await screen.findByTestId("detalle-del-mes");
  const billetera = within(detalle).getByTestId("detalle-billetera");
  expect(billetera).toHaveTextContent("Retiro a LLC DFF VENTURES RETIRO PROPIO");
  expect(billetera).toHaveTextContent("A cuenta propia");
  expect(billetera).toHaveTextContent("Retiro personal");
  const sinClasificar = within(billetera).getByText("pago raro").closest("li")!;
  expect(sinClasificar).toHaveTextContent("Sin clasificar");
  expect(billetera).toHaveTextContent("No tocan la ganancia");
  expect(billetera).toHaveTextContent("al 2026-10-13");
});

test("un mes sin cartera cargada lo dice en el detalle", async () => {
  montar();
  await screen.findByTestId("tabla-mensual");
  fireEvent.click(screen.getByRole("button", { name: /ago 2026/i }));
  const detalle = await screen.findByTestId("detalle-del-mes");
  expect(within(detalle).getByTestId("detalle-billetera")).toHaveTextContent("Sin historial de cartera");
});

test("subir el historial de cartera lo manda a guardar junto con el resto", async () => {
  const fetchFalso = servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": MENSUAL_GT,
    "/api/resultados/mensual/cargar": { cartera: { nuevas: 5, actualizadas: 0 } },
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
  montar();
  await screen.findByTestId("tabla-mensual");
  const entrada = screen.getByLabelText(/historial de cartera de dropi/i);
  fireEvent.change(entrada, { target: { files: [new File(["x"], "historial de cartera.xlsx")] } });
  fireEvent.click(screen.getByRole("button", { name: /guardar en el historial/i }));
  await waitFor(() => {
    const llamada = fetchFalso.mock.calls.find(([url]) => String(url).includes("/mensual/cargar"));
    expect(llamada).toBeTruthy();
    const cuerpo = (llamada![1] as RequestInit).body as FormData;
    expect(cuerpo.get("cartera")).toBeInstanceOf(File);
    expect(cuerpo.get("dropi")).toBeNull();
  });
  expect(await screen.findByText(/cartera: 5 movimientos nuevos/i)).toBeInTheDocument();
});

test("la pestaña Último export sigue ahí y recuerda la elección", async () => {
  servir({
    "/api/mercados": MERCADOS,
    "/api/resultados/mensual": MENSUAL_GT,
    "/api/resultados": { estado: 404 },
    "/api/resultados/historial": [],
  });
  montar();
  await screen.findByTestId("tabla-mensual");
  fireEvent.click(screen.getByRole("tab", { name: "Último export" }));
  expect(await screen.findByText(/todavía no hay ningún export de dropi cargado/i)).toBeInTheDocument();
  expect(screen.queryByTestId("tabla-mensual")).not.toBeInTheDocument();
  expect(window.localStorage.getItem("vitalcom-resultados-vista")).toBe("periodo");
});
