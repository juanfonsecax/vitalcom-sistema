/**
 * resultados.test.tsx — pruebas de la pantalla «Resultados» (`/resultados`, T4b).
 *
 * Verifica lo que decidió la metodología, no la pantalla: el P&L real (`gen_pl.py --json`),
 * la bandera PRELIMINAR tal cual la manda el script, el estado vacío cuando nadie cargó
 * todavía un export, y que un error real (no un 404 de "no hay carga") se muestra como falla,
 * no como estado vacío.
 */
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, test, vi } from "vitest";
import { Resultados } from "../pantallas/Resultados";

const RESULTADOS_MADURO = {
  periodo: { desde: "2026-08-01", hasta: "2026-08-31", generado: "2026-09-10" },
  vista_a_cohorte: {
    preliminar: false,
    edad_dias: 15,
    dias_maduro_umbral: 10,
    entregadas: 40,
    devueltas: 6,
    en_transito: 0,
    pct_resuelto: 100,
    estado_de_resultados: {
      venta_bruta_entregada_q: 10000,
      margen_logistico_q: 6000,
      margen_contribucion_q: 4500,
      resultado_neto_q: 3000,
    },
    economia_unitaria: [
      {
        producto_key: "TINNIDROP",
        pct_entrega: 87.0,
        entregadas: 40,
        devueltas: 6,
        ticket_promedio_q: 250,
        margen_antes_publicidad_q: 120,
        cpa_real_q: 90,
        ganancia_por_venta_q: 30,
      },
      {
        producto_key: "NUSAVA",
        pct_entrega: 70.0,
        entregadas: 10,
        devueltas: 4,
        ticket_promedio_q: 200,
        margen_antes_publicidad_q: 50,
        cpa_real_q: 80,
        ganancia_por_venta_q: -30,
      },
    ],
  },
  vista_b_caja: null,
  alertas: [],
  integridad: { cuadre_dropi: true, cuadre_extracto: null, maduracion: true },
  fallos: [],
  ok: true,
};

const RESULTADOS_PRELIMINAR = {
  ...RESULTADOS_MADURO,
  vista_a_cohorte: { ...RESULTADOS_MADURO.vista_a_cohorte, preliminar: true, edad_dias: 2 },
};

function servir(respuestas: Record<string, unknown | { estado: number }>) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const ruta = new URL(url, "http://x").pathname;
      const cuerpo = respuestas[ruta];
      if (cuerpo === undefined) {
        return { ok: false, status: 404, json: async () => ({ detail: "no hay carga" }) } as Response;
      }
      if (typeof cuerpo === "object" && cuerpo !== null && "estado" in cuerpo) {
        const { estado } = cuerpo as { estado: number };
        return { ok: false, status: estado, json: async () => ({ detail: "algo falló" }) } as Response;
      }
      return { ok: true, status: 200, json: async () => cuerpo } as Response;
    }),
  );
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
  servir({ "/api/resultados/historial": [] });
});

test("sin carga previa muestra el estado vacío, no un error", async () => {
  montar();
  expect(await screen.findByText(/todavía no hay ningún export de dropi cargado/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /calcular el p&l/i })).toBeDisabled();
});

test("con un período cargado y maduro, las tarjetas muestran los montos sin la etiqueta preliminar", async () => {
  servir({ "/api/resultados": RESULTADOS_MADURO, "/api/resultados/historial": [RESULTADOS_MADURO] });
  montar();
  expect(await screen.findByText("Margen logístico")).toBeInTheDocument();
  expect(screen.getByText(/Q\s?6,000/)).toBeInTheDocument();
  expect(screen.getByText(/Q\s?4,500/)).toBeInTheDocument();
  expect(screen.getByText(/Q\s?3,000/)).toBeInTheDocument();
  expect(screen.queryByText("Preliminar")).not.toBeInTheDocument();
});

test("un período por debajo de dias_cohorte_maduro se marca Preliminar (no lo calcula la pantalla)", async () => {
  servir({ "/api/resultados": RESULTADOS_PRELIMINAR, "/api/resultados/historial": [RESULTADOS_PRELIMINAR] });
  montar();
  await screen.findByText("Margen logístico");
  expect(screen.getAllByText("Preliminar").length).toBeGreaterThan(0);
});

test("la tabla de economía unitaria marca en rojo la ganancia por venta negativa", async () => {
  servir({ "/api/resultados": RESULTADOS_MADURO, "/api/resultados/historial": [RESULTADOS_MADURO] });
  montar();
  const negativa = await screen.findByText(/-Q\s?30/);
  expect(negativa.className).toContain("estado-pausar");
  const positiva = screen.getByText(/^Q\s?30$/);
  expect(positiva.className).toContain("estado-escalar");
});

test("con un solo período cargado, el gráfico avisa que la tendencia empieza en el segundo", async () => {
  servir({ "/api/resultados": RESULTADOS_MADURO, "/api/resultados/historial": [RESULTADOS_MADURO] });
  montar();
  expect(await screen.findByText(/la tendencia aparece desde el segundo export/i)).toBeInTheDocument();
});

test("un error real (no 404) se muestra como falla del sistema, nunca como estado vacío", async () => {
  servir({ "/api/resultados": { estado: 500 }, "/api/resultados/historial": [] });
  montar();
  expect(await screen.findByText(/no pude leer el sistema/i)).toBeInTheDocument();
  expect(screen.queryByText(/todavía no hay ningún export de dropi cargado/i)).not.toBeInTheDocument();
});
