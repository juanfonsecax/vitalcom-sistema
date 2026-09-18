/**
 * lenguaje.ts — cómo se dice en pantalla lo que el motor dice en clave.
 *
 * Esto NO cambia ningún dato: traduce etiquetas a palabras de todos los días y elige un
 * color. El valor crudo (`LISTO_PARA_EJECUTAR`, `F2.etapa-11`) siempre se sigue mostrando
 * al lado, para que lo que se ve en la app y lo que dice la consola sean lo mismo.
 */
import type { Tono } from "./componentes/ui";

export const ESTADO_EN_PALABRAS: Record<string, { texto: string; tono: Tono }> = {
  LISTO_PARA_EJECUTAR: { texto: "listo para ejecutar", tono: "bien" },
  BLOQUEADO: { texto: "bloqueado", tono: "alto" },
  CUMPLIDO: { texto: "hecho", tono: "bien" },
  PENDIENTE: { texto: "pendiente", tono: "neutro" },
  NO_APLICA: { texto: "no aplica", tono: "neutro" },
  EN_CURSO: { texto: "en curso", tono: "dato" },
  // VARICOSE vive acá: pausado por decisión, fuera del recorrido normal del grafo.
  EXCEPCION: { texto: "fuera del recorrido normal", tono: "aviso" },
  PAUSADO: { texto: "pausado", tono: "aviso" },
};

export function estadoEnPalabras(estado: string | null | undefined) {
  if (!estado) return { texto: "sin evaluar", tono: "neutro" as Tono };
  return ESTADO_EN_PALABRAS[estado] ?? { texto: estado.toLowerCase().replace(/_/g, " "), tono: "neutro" as Tono };
}

export const FASES = [
  { id: "F1", rotulo: "FASE 1 · ángulos", que: "6 ángulos distintos, un concepto fijo" },
  { id: "F2", rotulo: "FASE 2 · conceptos", que: "el ángulo ganador, 10 conceptos" },
  { id: "F3", rotulo: "FASE 3 · escalado", que: "ya no se mide: se compra volumen" },
] as const;

export const ESTADO_PRODUCTO: Record<string, Tono> = {
  VIVO: "bien",
  PAUSADO: "aviso",
  NUEVO: "dato",
  RETIRADO: "neutro",
};

/** El nombre del paso sin el prefijo de fase: `F2.etapa-11` → `etapa-11`. */
export function pasoCorto(nodo: string | null | undefined) {
  if (!nodo) return "";
  const punto = nodo.indexOf(".");
  return punto === -1 ? nodo : nodo.slice(punto + 1);
}

/**
 * Cómo se lee un ejecutor en pantalla. El texto que da `flujo.py` es operativo
 * ("subagente etapa-11 (Task, subagent_type=etapa-11)"); acá se dice quién lo hace.
 */
export function quienLoHace(ejecutor: string | null | undefined): string {
  if (!ejecutor) return "sin ejecutor declarado";
  const texto = ejecutor.toLowerCase();
  if (texto.startsWith("operador")) return "lo hacés vos";
  if (texto.includes("subagente") || texto.includes("skill")) return "lo hace Claude";
  if (texto.includes("script")) return "lo hace un script";
  if (texto.includes("mcp")) return "se ejecuta en Meta, con tu aprobación";
  return ejecutor;
}

/** Los días de rezago, dichos como los diría una persona. */
export function rezagoEnPalabras(dias: number | null | undefined) {
  if (dias === null || dias === undefined) return { texto: "sin dato de rezago", tono: "neutro" as Tono };
  if (dias <= 0) return { texto: "data de hoy", tono: "bien" as Tono };
  if (dias === 1) return { texto: "data de ayer", tono: "bien" as Tono };
  if (dias <= 2) return { texto: `data de hace ${dias} días`, tono: "aviso" as Tono };
  return { texto: `data de hace ${dias} días — decidir así es decidir a ciegas`, tono: "alto" as Tono };
}
