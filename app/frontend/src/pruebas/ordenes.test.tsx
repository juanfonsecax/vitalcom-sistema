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
        rezago_dias: 3,
      },
      bloqueo_fase: null,
      ejecutable: false,
      conjuntos: ["OVULOS · INFECCION"],
    },
  ],
  bloqueantes: [],
  avisos: [],
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
  const router = createRouter({
    routeTree: raiz.addChildren([rutaOrdenes]),
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
  });
});

test("muestra las órdenes de hoy con sus estados y explicaciones", async () => {
  renderizar();
  expect(await screen.findByText("Órdenes de hoy")).toBeInTheDocument();
  // Los 4 estados
  expect(await screen.findByText("Subir 20% al presupuesto de Resistencia a la Insulina SOP")).toBeInTheDocument();
  expect(await screen.findByText("Pausar conjunto de Zumbido Grave")).toBeInTheDocument();
  expect(await screen.findByText("Renovar creativo para Fatiga Crónica (rotar concepto en F2)")).toBeInTheDocument();
  expect(await screen.findByText("Mantener presupuesto de Infección Recurrente: faltan ~4 ventas para decidir")).toBeInTheDocument();
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

test("los botones de acción respetan si el nodo está deshabilitado en manifiesto", async () => {
  renderizar();
  const botonesAprobar = await screen.findAllByRole("button", { name: "Aprobar" });
  expect(botonesAprobar.length).toBeGreaterThan(0);
  // Todos deben estar deshabilitados porque cicloHabilitado es false
  for (const b of botonesAprobar) {
    expect(b).toBeDisabled();
  }
});
