/**
 * La tabla de Guatemala muestra las cifras de costear.py sin tocarlas.
 * 30.8 se ve «Q30.8», no «Q30.80»: si hay que formatear, lo decide el script.
 */
import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { TablaGuatemala } from "../componentes/TablaGuatemala";
import type { Costeo } from "../api/cliente";

// Salida real de `python Ads/_TOOLS/costear.py 60 --json` (17-sep-2026).
const COSTEO_60: Costeo = {
  costo_ingresado: 60.0,
  fila_usada: 60.0,
  criterio_de_fila: "exacta",
  precio_1u: 199,
  cpa_objetivo: 28.51,
  cpa_base: 30.8,
  cpa_break_even: 69.56,
  valor_envio: 43.37,
  utilidad_esperada: 38.76,
  escalera: [
    { unidades: 1, precio: 199, costo_pedido: 60.0 },
    { unidades: 2, precio: 299, costo_pedido: 120.0 },
    { unidades: 3, precio: 399, costo_pedido: 180.0 },
  ],
  arranque: { p1u_minimo: 181.43, multiplo_necesario: 3.02, decision: "1U", nota: "1 unidad viable, con 2u/3u/4u como upsell." },
  fuente: "PRODUCTOS/_DIM_COSTEO.csv",
  origen_escalera: "OPERADOR",
};

test("la escalera y los umbrales salen tal cual del script", () => {
  render(<TablaGuatemala costeo={COSTEO_60} simbolo="Q" />);
  const escalera = screen.getByTestId("escalera");
  for (const precio of ["Q199", "Q299", "Q399"]) expect(within(escalera).getByText(precio)).toBeInTheDocument();
  const umbrales = screen.getByTestId("umbrales");
  expect(within(umbrales).getByText("Q28.51")).toBeInTheDocument();
  expect(within(umbrales).getByText("Q69.56")).toBeInTheDocument();
  expect(within(umbrales).getByText("Q43.37")).toBeInTheDocument();
  expect(within(umbrales).getByText("Q38.76")).toBeInTheDocument();
});

test("no redondea ni agrega decimales", () => {
  render(<TablaGuatemala costeo={{ ...COSTEO_60, cpa_objetivo: 30.8 }} simbolo="Q" />);
  expect(screen.getByText("Q30.8")).toBeInTheDocument();
  expect(screen.queryByText("Q30.80")).not.toBeInTheDocument();
});

test("un costo sin fila propia repite el criterio del script, sin inventar otro", () => {
  // Salida real de `costear.py 41`: TINNIDROP cuesta Q41 y usa la fila Q40 (la más cercana).
  render(
    <TablaGuatemala
      costeo={{ ...COSTEO_60, costo_ingresado: 41, fila_usada: 40, criterio_de_fila: "más cercana" }}
      simbolo="Q"
    />,
  );
  const aviso = screen.getByTestId("aviso-fila");
  expect(aviso).toHaveTextContent("usa la fila Q40 (criterio: más cercana)");
  expect(aviso).not.toHaveTextContent("superior, Q40");
});

test("pasar el techo de la tabla se avisa en rojo", () => {
  render(
    <TablaGuatemala
      costeo={{ ...COSTEO_60, costo_ingresado: 400, fila_usada: 130, criterio_de_fila: "TECHO DE TABLA EXCEDIDO" }}
      simbolo="Q"
    />,
  );
  expect(screen.getByTestId("aviso-fila")).toHaveTextContent("pasa la última fila");
  expect(screen.getByTestId("aviso-fila")).toHaveClass("text-rose-300");
});

test("con costo exacto no hay aviso de fila", () => {
  render(<TablaGuatemala costeo={COSTEO_60} simbolo="Q" />);
  expect(screen.queryByTestId("aviso-fila")).not.toBeInTheDocument();
});
