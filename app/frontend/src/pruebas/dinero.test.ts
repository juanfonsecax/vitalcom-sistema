/**
 * dinero.test.ts — el formateo de dinero por mercado y las utilidades de mercado (D2 multi-mercado).
 */
import { expect, test } from "vitest";
import {
  banderaDe,
  conSimbolo,
  contarPorMercado,
  etiquetaDeMercado,
  filtrarPorMercado,
  formatearDinero,
  nombreDeMoneda,
  TODOS,
} from "../dinero";

const GT = { mercado: "GT", moneda_local: "GTQ", simbolo: "Q" };
const CO = { mercado: "CO", moneda_local: "COP", simbolo: "$" };

test("GTQ: símbolo pegado, miles con coma y dos decimales", () => {
  expect(formatearDinero(1234.5, GT)).toBe("Q1,234.50");
  expect(formatearDinero("98.2", GT)).toBe("Q98.20");
  expect(formatearDinero(145, GT)).toBe("Q145.00");
  expect(formatearDinero(1234567.891, GT)).toBe("Q1,234,567.89");
});

test("COP: símbolo con espacio, miles con punto y sin decimales", () => {
  expect(formatearDinero(41000, CO)).toBe("$ 41.000");
  expect(formatearDinero("7000", CO)).toBe("$ 7.000");
  expect(formatearDinero(1234567.6, CO)).toBe("$ 1.234.568");
  expect(formatearDinero(950, CO)).toBe("$ 950");
});

test("negativos con signo delante y cero sin signo", () => {
  expect(formatearDinero(-30, GT)).toBe("-Q30.00");
  expect(formatearDinero(-41000, CO)).toBe("-$ 41.000");
  expect(formatearDinero(-0.001, GT)).toBe("Q0.00");
});

test("el mismo monto se escribe distinto según el mercado, nunca con la moneda del otro", () => {
  expect(formatearDinero(80, GT)).toBe("Q80.00");
  expect(formatearDinero(80, CO)).toBe("$ 80");
});

test("las opciones pueden fijar los decimales (estado de resultados sin centavos)", () => {
  expect(formatearDinero(12345.67, GT, { decimales: 0 })).toBe("Q12,346");
});

test("sin monto se ve el guion; sin perfil conocido no se inventa un formato", () => {
  expect(formatearDinero(null, GT)).toBe("—");
  expect(formatearDinero(undefined, CO)).toBe("—");
  expect(formatearDinero("abc", GT)).toBe("—");
  expect(formatearDinero(null, GT, { vacio: "Sin datos" })).toBe("Sin datos");
  expect(formatearDinero(41.5, {})).toBe("41.5 (moneda sin declarar)");
  expect(formatearDinero(41.5, { moneda_local: "MXN", simbolo: "$" })).toBe("41.5 MXN");
});

test("conSimbolo respeta el texto del script tal cual", () => {
  expect(conSimbolo(30.8, "Q")).toBe("Q30.8");
  expect(conSimbolo(null, "Q")).toBe("—");
});

test("banderas y etiquetas de mercado", () => {
  expect(banderaDe("GT")).toBe("🇬🇹");
  expect(banderaDe("CO")).toBe("🇨🇴");
  expect(banderaDe("MX")).toBe("");
  expect(etiquetaDeMercado("GT")).toBe("🇬🇹 GT");
  expect(etiquetaDeMercado("CO")).toBe("🇨🇴 CO");
  expect(etiquetaDeMercado("MX")).toBe("MX");
  expect(nombreDeMoneda("GTQ")).toBe("quetzales");
  expect(nombreDeMoneda("COP")).toBe("pesos colombianos");
});

const ITEMS = [
  { id: 1, mercado: "GT" },
  { id: 2, mercado: "CO" },
  { id: 3, mercado: "GT" },
];

test("el filtro deja solo el mercado elegido; «Todos» no filtra", () => {
  expect(filtrarPorMercado(ITEMS, "GT").map((i) => i.id)).toEqual([1, 3]);
  expect(filtrarPorMercado(ITEMS, "CO").map((i) => i.id)).toEqual([2]);
  expect(filtrarPorMercado(ITEMS, TODOS)).toHaveLength(3);
});

test("los totales por mercado son conteos separados, nunca un solo número combinado", () => {
  expect(contarPorMercado(ITEMS)).toEqual({ GT: 2, CO: 1 });
  expect(contarPorMercado([{ mercado: "" }])).toEqual({ "sin mercado": 1 });
});
