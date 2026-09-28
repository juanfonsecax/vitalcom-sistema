/**
 * ordenes.test.tsx — pruebas de la pantalla «Órdenes de hoy».
 *
 * Verifica:
 *   1. Muestra tarjetas con los estados (ESCALAR, PAUSAR, RENOVAR, SEGUIR_MIDIENDO).
 *   2. Alerta de rezago si la data tiene más de 2 días.
 *   3. Bloque de ganadores detectados por venta con enlace a FASE 2 / etapa-11.
 *   4. Botones respetan si la acción está deshabilitada en el manifiesto.
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
import { Ordenes } from "../pantallas/Ordenes";

const DATOS_ORDENES = {
  schema: "ordenes/1",
  rezago_dias: 3,
  pendientes_registro: [],
  llamadas: [
    {
      llamada: 1,
      tool: "ads_update_entity",
      entidad_nombre: "TINNIDROP · CONJUNTO 1",
      omitir: false,
      valor_antes: { daily_budget: "1000" },
      valor_despues: { daily_budget: "1200" },
      args: { entity_id: "238510001", entity_type: "adset" },
    },
  ],
  ordenes: [
    {
      producto_key: "CLEARSTEM",
      angulo_key: "RESISTENCIA_INSULINA_SOP",
      angulo_nombre: "Resistencia a la Insulina SOP",
      estado: "ESCALAR",
      accion_codigo: "ESCALAR_SURFING",
      frase_simple: "Subir 20% al presupuesto de Resistencia a la Insulina SOP",
      por_que: {
        frase: "Subir 20% al presupuesto",
        cpa_real_q: 27.3,
        ic: [19.4, 27.3, 39.6],
        break_even_q: 105.89,
        cpa_objetivo_q: 30.8,
        faltan_ventas: null,
        rezago_dias: 3,
        cierre_pct: 18.2,
      },
      bloqueo_fase: "CLEARSTEM está en F2: subir presupuesto sesga la medición",
      ejecutable: false,
      conjuntos: ["CLEARSTEM · SOP"],
    },
    {
      producto_key: "TINNIDROP",
      angulo_key: "ZUMBIDO_GRAVE",
      angulo_nombre: "Zumbido Grave",
      estado: "PAUSAR",
      accion_codigo: "PAUSAR_CELDA",
      frase_simple: "Pausar conjunto de Zumbido Grave",
      por_que: {
        frase: "Pausar conjunto",
        cpa_real_q: 120.5,
        ic: [98.2, 120.5, 145.0],
        break_even_q: 93.4,
        cpa_objetivo_q: 45.0,
        faltan_ventas: null,
        rezago_dias: 3,
      },
      bloqueo_fase: null,
      ejecutable: true,
      conjuntos: ["TINNIDROP · ZUMBIDO"],
    },
    {
      producto_key: "NUSAVA",
      angulo_key: "FATIGA_CRONICA",
      angulo_nombre: "Fatiga Crónica",
      estado: "RENOVAR",
      accion_codigo: "RENOVAR_CREATIVO",
      frase_simple: "Renovar creativo para Fatiga Crónica (rotar concepto en F2)",
      por_que: {
        frase: "Renovar creativo",
        cpa_real_q: 85.0,
        ic: [70.0, 85.0, 110.0],
        break_even_q: 92.6,
        cpa_objetivo_q: 40.0,
        faltan_ventas: null,
        rezago_dias: 3,
      },
      bloqueo_fase: null,
      ejecutable: false,
      conjuntos: ["NUSAVA · FATIGA"],
    },
    {
      producto_key: "OVULOS_PURITY",
      angulo_key: "INFECCION_RECURRENTE",
      angulo_nombre: "Infección Recurrente",
      estado: "SEGUIR_MIDIENDO",
      accion_codigo: "SEGUIR_MIDIENDO",
      frase_simple: "Mantener presupuesto de Infección Recurrente: faltan ~4 ventas para decidir",
      por_que: {
        frase: "Mantener presupuesto",
        cpa_real_q: null,
        ic: null,
        break_even_q: 80.0,
        cpa_objetivo_q: 35.0,
        faltan_ventas: 4,
        ventas_actual: 3,
        ventas_necesarias: 7,
        rezago_dias: 3,
      },
      bloqueo_fase: null,
      ejecutable: false,
      conjuntos: ["OVULOS · INFECCION"],
    },
  ],
  bloqueantes: [],
  avisos: [],
  parametros_motor: [
    { parametro: "ventana_dias", valor: "14", unidad: "dias", dueno: "GUIA_MADRE_PARAMETRIZADA.md", por_que: "" },
    { parametro: "ventana_fatiga_dias", valor: "3", unidad: "dias", dueno: "decidir.py", por_que: "" },
    { parametro: "duracion_testeo_fase2_dias", valor: "3", unidad: "dias", dueno: "decidir.py", por_que: "" },
    { parametro: "cierre_meta_min_pct", valor: "15", unidad: "porcentaje", dueno: "GUIA_MADRE_PARAMETRIZADA.md", por_que: "" },
    { parametro: "cierre_meta_max_pct", valor: "20", unidad: "porcentaje", dueno: "GUIA_MADRE_PARAMETRIZADA.md", por_que: "" },
  ],
};

const GANADORES = [
  {
    producto_key: "TINNIDROP",
    nombre: "Tinnidrop Importado Original",
    fase: "F2",
    nodo_actual: "F2.etapa-11",
    angulo_ganador: "PERDIDA_AUDITIVA (histórico 104v CPA Q65.5 ≤ BE Q93.4)",
    siguiente_paso: {
      nodo: "F2.etapa-11",
      etapa: "etapa-11",
      titulo: "Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)",
      ejecutor: "subagente etapa-11",
      enlace: "/producto/TINNIDROP",
    },
  },
];

const ACCIONES = [
  {
    id: "nodo.ciclo.ordenes",
    rotulo: "Ejecutar órdenes en Meta",
    habilitada: false,
    motivo: "Deshabilitado por doctrina: revisión manual requerida",
  },
];

/** `pendientes_registro` tal cual lo emite gen_ordenes.py: conjuntos NUESTROS cuyo gasto ya
 * cuenta a nivel producto pero sin fila de `angulo_key`; `lo_produce` trae el paso dueño del
 * registro (etapa-6) con el archivo que da de alta. */
const PENDIENTES_REGISTRO = [
  {
    cuenta_alias: "GTR 7",
    campana: "LUMINIVA · F1 · TEST",
    conjunto: "LUMINIVA · SIN-REGISTRO",
    producto_key: "LUMINIVA",
    spend_usd: 12.34,
    anuncios: 3,
    lo_produce: "ETAPA-6 / _DIM_CONJUNTOS.csv",
  },
  {
    cuenta_alias: "GTR 7",
    campana: "COLLAGENIX · F1 · TEST",
    conjunto: "COLLAGENIX · SIN-REGISTRO",
    producto_key: "COLLAGENIX",
    spend_usd: 8.5,
    anuncios: 2,
    lo_produce: "ETAPA-6 / _DIM_CONJUNTOS.csv",
  },
];

function servir(respuestas: Record<string, unknown>) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const parsed = new URL(url, "http://x");
      const cuerpo = respuestas[parsed.pathname];
      return {
        ok: cuerpo !== undefined,
        status: cuerpo === undefined ? 404 : 200,
        json: async () => cuerpo,
      } as Response;
    }),
  );
}

function renderizar() {
  const raiz = createRootRoute();
  const rutaOrdenes = createRoute({ getParentRoute: () => raiz, path: "/ordenes", component: Ordenes });
  const rutaTrabajos = createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: () => null });
  const rutaTrabajo = createRoute({ getParentRoute: () => raiz, path: "/trabajos/$id", component: () => null });
  const router = createRouter({
    routeTree: raiz.addChildren([rutaOrdenes, rutaTrabajos, rutaTrabajo]),
    history: createMemoryHistory({ initialEntries: ["/ordenes"] }),
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  servir({
    "/api/ordenes": DATOS_ORDENES,
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES,
    "/api/trabajos": [],
  });
});

test("muestra las órdenes de hoy con sus estados y explicaciones", async () => {
  renderizar();
  expect(await screen.findByText("Órdenes de hoy")).toBeInTheDocument();
  // Los 4 estados. La orden ESCALAR con bloqueo_fase muestra el titular sin ambigüedad
  // (invariante 13: no subir presupuesto en pleno testeo), no la frase cruda del motor.
  expect(
    await screen.findByText("No subir presupuesto: mantener el que ya tiene hasta cerrar la fase."),
  ).toBeInTheDocument();
  expect(screen.getByText(/Orden original del motor: Subir 20% al presupuesto/)).toBeInTheDocument();
  expect(await screen.findByText("Pausar conjunto de Zumbido Grave")).toBeInTheDocument();
  expect(await screen.findByText("Renovar creativo para Fatiga Crónica (rotar concepto en F2)")).toBeInTheDocument();
  expect(await screen.findByText("Mantener presupuesto de Infección Recurrente: faltan ~4 ventas para decidir")).toBeInTheDocument();
});

test("ESCALAR con bloqueo_fase no se contradice: chip, veredicto y glosario dicen todos que no se mueve plata", async () => {
  renderizar();
  // El chip ya no dice "Escalar (+20%)" para esta celda: diría lo contrario del titular.
  expect(await screen.findByText("Escalar bloqueado por fase")).toBeInTheDocument();
  expect(screen.queryByText("Escalar (+20%)")).not.toBeInTheDocument();
  // El veredicto narrado explica la aparente contradicción en vez de repetir "evidencia para escalar".
  expect(
    screen.getByText(/La celda es rentable y cuenta como evidencia de ganador, pero en pleno testeo/),
  ).toBeInTheDocument();
  // La línea de glosario de ESCALAR ("Poner más plata…") queda oculta en esta tarjeta; la
  // "Nota de fase" (bloqueo_fase) sigue mostrándose como siempre.
  expect(screen.queryByText(/Poner más plata: la evidencia alcanza/)).not.toBeInTheDocument();
  expect(screen.getByText(/CLEARSTEM está en F2: subir presupuesto sesga la medición/)).toBeInTheDocument();
});

test("narra la frase de IC vs break-even y el veredicto del motor", async () => {
  renderizar();
  // Tres de las cuatro órdenes traen IC y break-even completos (SEGUIR_MIDIENDO no trae IC):
  // la frase narrada aparece en esas tres tarjetas.
  expect((await screen.findAllByText(/Cada venta te está costando entre/)).length).toBe(3);
  // PAUSAR: cpa_real_q 120.5, ic [98.2, 120.5, 145.0], break_even_q 93.4
  expect(screen.getByText("Q98.2")).toBeInTheDocument();
  expect(screen.getByText("Q145")).toBeInTheDocument();
  // Q93.4 (el break-even de PAUSAR) aparece dos veces: en la frase narrada y en la grilla de
  // métricas de siempre — el mismo dato, nunca recalculado.
  expect(screen.getAllByText("Q93.4").length).toBe(2);
  expect(screen.getByText(/evidencia alcanza para pausar/)).toBeInTheDocument();
});

test("explica cada estado con las palabras del glosario, RENOVAR incluido", async () => {
  renderizar();
  expect(
    await screen.findByText(/El ángulo vende, pero el anuncio se cansó\. Se cambia el creativo/),
  ).toBeInTheDocument();
});

test("el veredicto narrado de RENOVAR habla de historia rentable, no de que 'sigue' rentable hoy", async () => {
  renderizar();
  // NUSAVA/RENOVAR trae ic + break_even_q completos → la frase narrada aparece con este veredicto.
  expect(
    await screen.findByText(
      /El ángulo tiene historia rentable; lo que se cansó en los últimos días es el creativo/,
    ),
  ).toBeInTheDocument();
});

test("ventas faltantes: número tal cual, null en SEGUIR_MIDIENDO dice que el motor no lo calculó, null en cualquier otro estado dice 'No aplica'", async () => {
  servir({
    "/api/ordenes": {
      ...DATOS_ORDENES,
      ordenes: DATOS_ORDENES.ordenes.map((o) =>
        o.producto_key === "OVULOS_PURITY"
          ? { ...o, por_que: { ...o.por_que, faltan_ventas: null, ventas_actual: null, ventas_necesarias: null } }
          : o,
      ),
    },
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES,
    "/api/trabajos": [],
  });
  renderizar();
  // SEGUIR_MIDIENDO sin faltan_ventas (0 ventas, o CPA pegado al break-even): el motor no calculó
  // un conteo, y la pantalla nunca inventa "volumen suficiente" en su lugar.
  expect(await screen.findByText("El motor no calculó cuántas faltan")).toBeInTheDocument();
  // ESCALAR, PAUSAR y RENOVAR ya decidieron sin necesitar ese conteo (faltan_ventas: null en el
  // fixture base): tampoco es "volumen suficiente", es que el dato no aplica a ese estado.
  expect(screen.getAllByText("No aplica").length).toBe(3);
});

test("barra de progreso de ventas: con ventas_actual y ventas_necesarias del motor, se dibuja '3 de 7 ventas'", async () => {
  renderizar();
  // OVULOS_PURITY (SEGUIR_MIDIENDO) trae ventas_actual: 3, ventas_necesarias: 7 en el fixture base.
  const rotulo = "3 de 7 ventas";
  expect(await screen.findByLabelText(rotulo)).toBeInTheDocument();
  expect(screen.getByText(rotulo)).toBeInTheDocument();
  const barra = screen.getByLabelText(rotulo) as HTMLProgressElement;
  expect(barra.tagName).toBe("PROGRESS");
  expect(barra.value).toBe(3);
  expect(barra.max).toBe(7);
});

test("barra de progreso de ventas: sin ventas_actual/ventas_necesarias, no se dibuja la barra y sigue el texto de siempre", async () => {
  renderizar();
  // Las otras tres órdenes (ESCALAR, PAUSAR, RENOVAR) no traen esos campos en su por_que.
  await screen.findByText("3 de 7 ventas");
  expect(document.querySelectorAll("progress")).toHaveLength(1);
  expect(screen.getAllByText("No aplica").length).toBe(3);
});

test("cierre: con el dato del motor y la meta del contrato, muestra ambos; sin cierre_pct dice 'Sin datos'", async () => {
  renderizar();
  // CLEARSTEM trae cierre_pct 18.2 y parametros_motor trae la meta 15-20: se juntan en una frase.
  expect(await screen.findByText("18.2 % · meta 15-20 % (referencia)")).toBeInTheDocument();
  // TINNIDROP (PAUSAR), NUSAVA (RENOVAR) y OVULOS_PURITY (SEGUIR_MIDIENDO) no traen cierre_pct en
  // su por_que: la pantalla nunca inventa un número ni revienta, dice que no hay dato — se cuenta
  // por el rótulo del bloque de "Cierre" (no por el texto "Sin datos", que también usa CPA).
  const bloquesDeCierre = await screen.findAllByText("Cierre (mensajes → ventas):");
  expect(bloquesDeCierre).toHaveLength(4);
  const sinDatoDeCierre = bloquesDeCierre.filter(
    (rotulo) => rotulo.nextElementSibling?.textContent === "Sin datos",
  );
  expect(sinDatoDeCierre).toHaveLength(3);
});

test("cierre: si el contrato todavía no trae la meta (CSV sin regenerar), se muestra solo el cierre real", async () => {
  servir({
    "/api/ordenes": {
      ...DATOS_ORDENES,
      parametros_motor: DATOS_ORDENES.parametros_motor.filter(
        (p) => !p.parametro.startsWith("cierre_meta"),
      ),
    },
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES,
    "/api/trabajos": [],
  });
  renderizar();
  expect(await screen.findByText("18.2 %")).toBeInTheDocument();
  expect(screen.queryByText(/meta 15-20/)).not.toBeInTheDocument();
});

test("el panel «cómo mide el motor» muestra los tres relojes con su valor real", async () => {
  renderizar();
  expect(await screen.findByText("Cómo mide el motor")).toBeInTheDocument();
  expect(screen.getByText(/Sobre cuántos días se calcula el CPA/)).toBeInTheDocument();
  expect(screen.getByText(/detectar fatiga/)).toBeInTheDocument();
  expect(screen.getByText(/coronar un concepto ganador/)).toBeInTheDocument();
  // El valor viene del contrato (`parametros_motor`), no inventado en la pantalla.
  expect(screen.getAllByText("3 dias").length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText("14 dias")).toBeInTheDocument();
});

test("si un reloj no está en el contrato, la pantalla lo dice en vez de inventar un número", async () => {
  servir({
    "/api/ordenes": { ...DATOS_ORDENES, parametros_motor: [] },
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES,
    "/api/trabajos": [],
  });
  renderizar();
  expect(await screen.findByText("Cómo mide el motor")).toBeInTheDocument();
  expect(screen.getAllByText("sin dato en el contrato").length).toBe(3);
});

test("muestra banner de alerta cuando la data tiene rezago > 2 dias", async () => {
  renderizar();
  expect(await screen.findByText(/Aviso de datos con rezago:/i)).toBeInTheDocument();
  expect(screen.getByText(/La data tiene 3 días de retraso/i)).toBeInTheDocument();
});

test("anuncia ganadores detectados por venta y su enlace al siguiente paso", async () => {
  renderizar();
  expect(await screen.findByText(/ganadores detectados por venta/i)).toBeInTheDocument();
  expect(screen.getByText("Tinnidrop Importado Original")).toBeInTheDocument();
  expect(screen.getByText(/PERDIDA_AUDITIVA/)).toBeInTheDocument();
  expect(screen.getByText(/Optimizar el CIERRE del bot/)).toBeInTheDocument();
});

test("no hay botones Aprobar/Rechazar muertos: la aprobación vive solo en Trabajos", async () => {
  renderizar();
  await screen.findByText("Órdenes de hoy");
  expect(screen.queryByRole("button", { name: "Aprobar" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Rechazar" })).not.toBeInTheDocument();
  // Con el ciclo deshabilitado en manifiesto (ACCIONES del fixture), la orden PAUSAR ejecutable
  // lo dice en texto en vez de ofrecer un botón que no puede hacer nada.
  expect(await screen.findByText("Ejecución deshabilitada en el manifiesto")).toBeInTheDocument();
});

test("con el ciclo habilitado, la orden ejecutable manda a Trabajos — directo a SU trabajo si ya hay uno pendiente", async () => {
  const ACCIONES_HABILITADAS = [
    { id: "nodo.ciclo.ordenes", rotulo: "Ejecutar órdenes en Meta", habilitada: true, motivo: null },
  ];
  servir({
    "/api/ordenes": DATOS_ORDENES,
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES_HABILITADAS,
    "/api/trabajos": [{ job_id: "job-9", pendiente: "Falta tu aprobación", producto_key: "TINNIDROP" }],
  });
  renderizar();
  const enlace = await screen.findByRole("link", { name: "Revisar y aprobar en Trabajos" });
  // TINNIDROP (PAUSAR, ejecutable) ya tiene un trabajo pendiente: el botón cae directo en él.
  expect(enlace).toHaveAttribute("href", "/trabajos/job-9");
});

test("sin conjuntos pendientes de registro no se muestra la tarjeta (cero ruido visual)", async () => {
  renderizar();
  await screen.findByText("Órdenes de hoy");
  expect(screen.queryByTestId("pendientes-registro")).not.toBeInTheDocument();
});

test("lista los conjuntos de Meta sin registrar con su gasto y quién da de alta la fila", async () => {
  servir({
    "/api/ordenes": { ...DATOS_ORDENES, pendientes_registro: PENDIENTES_REGISTRO },
    "/api/ganadores": GANADORES,
    "/api/acciones": ACCIONES,
    "/api/trabajos": [],
  });
  renderizar();
  expect(await screen.findByTestId("pendientes-registro")).toBeInTheDocument();
  expect(screen.getByText("Conjuntos de Meta sin registrar")).toBeInTheDocument();
  expect(screen.getByText(/Su gasto ya cuenta en el producto/)).toBeInTheDocument();
  // Filas tal cual el fixture: conjunto (font-mono), gasto y el paso que registra.
  expect(screen.getByText("LUMINIVA · SIN-REGISTRO")).toBeInTheDocument();
  expect(screen.getByText("COLLAGENIX · SIN-REGISTRO")).toBeInTheDocument();
  expect(screen.getByText("12.34")).toBeInTheDocument();
  expect(screen.getAllByText("ETAPA-6 / _DIM_CONJUNTOS.csv")).toHaveLength(2);
});
