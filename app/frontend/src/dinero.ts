/**
 * dinero.ts — el formateo de dinero y las banderas de mercado, en un solo lugar.
 *
 * Reglas (multi-mercado, D2):
 *   · El dinero se escribe con la moneda del MERCADO del producto, que trae la API
 *     (`mercado`, `moneda_local`, `simbolo`). Acá nunca se deduce el mercado de una clave de producto.
 *   · Nunca se suman montos de mercados distintos: la app no suma plata (la suma el motor); lo que
 *     se agrupa por mercado son CONTEOS (`contarPorMercado`).
 *   · GTQ → «Q1,234.50» · COP → «$ 41.000» (es-CO, sin decimales). Una moneda que no está en
 *     `FORMATOS` no se adivina: se escribe el número tal cual con su código.
 */

/** Lo mínimo que la API entrega de un mercado para poder escribir un monto. */
export type PerfilMoneda = {
  mercado?: string | null;
  moneda_local?: string | null;
  simbolo?: string | null;
};

type Formato = { decimales: number; miles: string; decimal: string; espacio: string };

const FORMATOS: Record<string, Formato> = {
  GTQ: { decimales: 2, miles: ",", decimal: ".", espacio: "" },
  COP: { decimales: 0, miles: ".", decimal: ",", espacio: " " },
};

/** «Todos» no es un mercado: es la ausencia de filtro. */
export const TODOS = "TODOS";

export function formatearDinero(
  monto: number | string | null | undefined,
  perfil: PerfilMoneda | null | undefined,
  opciones: { decimales?: number; vacio?: string } = {},
): string {
  const vacio = opciones.vacio ?? "—";
  if (monto === null || monto === undefined || monto === "") return vacio;
  const numero = typeof monto === "number" ? monto : Number(monto);
  if (!Number.isFinite(numero)) return vacio;

  const formato = FORMATOS[perfil?.moneda_local ?? ""];
  const simbolo = perfil?.simbolo ?? "";
  if (!formato || !simbolo) {
    // Sin perfil conocido no se inventa un formato: el número crudo y la moneda que declara la API.
    return `${String(numero)} ${perfil?.moneda_local || "(moneda sin declarar)"}`;
  }
  const decimales = opciones.decimales ?? formato.decimales;
  const [entera, fraccion] = Math.abs(numero).toFixed(decimales).split(".");
  const agrupada = entera.replace(/\B(?=(\d{3})+(?!\d))/g, formato.miles);
  const cuerpo = fraccion ? `${agrupada}${formato.decimal}${fraccion}` : agrupada;
  const negativo = numero < 0 && Number(cuerpo.replace(/[^\d]/g, "")) !== 0 ? "-" : "";
  return `${negativo}${simbolo}${formato.espacio}${cuerpo}`;
}

/** Símbolo + el texto tal como lo escribió el motor (sin tocar decimales ni separadores). Solo para
 * salidas de script que se muestran «byte a byte» (`TablaGuatemala`, salida de `costear.py`). */
export function conSimbolo(valor: number | string | null | undefined, simbolo: string, vacio = "—"): string {
  return valor === null || valor === undefined ? vacio : `${simbolo}${String(valor)}`;
}

const NOMBRES_MONEDA: Record<string, string> = { GTQ: "quetzales", COP: "pesos colombianos" };

/** «quetzales», «pesos colombianos»; el código de la moneda si no hay nombre declarado. */
export function nombreDeMoneda(moneda: string | null | undefined): string {
  return NOMBRES_MONEDA[moneda ?? ""] ?? (moneda || "moneda del mercado");
}

const BANDERAS: Record<string, string> = { GT: "🇬🇹", CO: "🇨🇴" };

/** La bandera de un mercado; vacía si no hay una declarada (el código igual se muestra al lado). */
export function banderaDe(mercado: string | null | undefined): string {
  return BANDERAS[mercado ?? ""] ?? "";
}

/** «🇬🇹 GT», o solo el código si no hay bandera. */
export function etiquetaDeMercado(mercado: string | null | undefined): string {
  const codigo = mercado ?? "";
  const bandera = banderaDe(codigo);
  return bandera ? `${bandera} ${codigo}` : codigo || "sin mercado";
}

/** Deja solo los ítems del mercado elegido (`TODOS` = todos). Trabaja sobre el `mercado` que trae
 * cada ítem de la API. */
export function filtrarPorMercado<T extends { mercado?: string | null }>(items: T[], seleccion: string): T[] {
  return seleccion === TODOS ? items : items.filter((item) => item.mercado === seleccion);
}

/** Cuántos ítems hay por mercado. Son CONTEOS: los montos de mercados distintos nunca se mezclan
 * ni se suman en el frontend. */
export function contarPorMercado<T extends { mercado?: string | null }>(items: T[]): Record<string, number> {
  const conteo: Record<string, number> = {};
  for (const item of items) {
    const clave = item.mercado || "sin mercado";
    conteo[clave] = (conteo[clave] ?? 0) + 1;
  }
  return conteo;
}
