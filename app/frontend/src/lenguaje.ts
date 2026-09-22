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

const FASE_POR_ID: Record<string, (typeof FASES)[number]> = Object.fromEntries(
  FASES.map((f) => [f.id, f]),
);

/** Qué significa la fase en una frase, para quien no se sabe el vocabulario de memoria. */
export function faseEnUnaFrase(fase: string | null | undefined): string {
  if (!fase) return "Todavía no tiene fase asignada.";
  const f = FASE_POR_ID[fase];
  return f ? `${f.rotulo}: ${f.que}.` : `Fase ${fase}.`;
}

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

/** Los estados de un trabajo del runner, dichos en palabras de todos los días. El código crudo se muestra al lado. */
export const ESTADO_DE_TRABAJO: Record<string, { texto: string; tono: Tono; enCurso: boolean }> = {
  ENCOLADO: { texto: "en la fila", tono: "dato", enCurso: true },
  CORRIENDO: { texto: "corriendo", tono: "dato", enCurso: true },
  ESPERA_APROBACION: { texto: "espera tu aprobación", tono: "aviso", enCurso: true },
  ESPERA_RESPUESTA: { texto: "espera tu respuesta", tono: "aviso", enCurso: true },
  ESPERA_MEDIA: { texto: "espera que subas las imágenes", tono: "aviso", enCurso: true },
  EXITO: { texto: "terminó bien", tono: "bien", enCurso: false },
  SIN_CUMPLIR: { texto: "terminó, pero el paso sigue pendiente", tono: "aviso", enCurso: false },
  RECHAZADO: { texto: "lo rechazaste", tono: "neutro", enCurso: false },
  CADUCADO: { texto: "caducó sin respuesta", tono: "aviso", enCurso: false },
  FALLIDO: { texto: "falló", tono: "alto", enCurso: false },
  INTERRUMPIDO: { texto: "se interrumpió a mitad", tono: "alto", enCurso: false },
  CSV_INVALIDO: { texto: "dejó un CSV inválido", tono: "alto", enCurso: false },
  CANCELADO: { texto: "cancelado", tono: "neutro", enCurso: false },
  OTRA_VERSION: { texto: "quedó de una versión vieja de la app", tono: "aviso", enCurso: true },
};

export function trabajoEnPalabras(estado: string | null | undefined) {
  if (!estado) return { texto: "sin estado", tono: "neutro" as Tono, enCurso: false };
  return (
    ESTADO_DE_TRABAJO[estado] ?? { texto: estado.toLowerCase().replace(/_/g, " "), tono: "neutro" as Tono, enCurso: false }
  );
}

/** Los estados de un trabajo que se pueden volver a correr completos. */
export const SE_REINTENTAN = ["FALLIDO", "INTERRUMPIDO", "CADUCADO"];

/** El veredicto del motor en una frase, elegido por su ESTADO (nunca por comparar números acá). */
export const VEREDICTO_POR_ESTADO: Record<string, string> = {
  ESCALAR: "El motor dice que la evidencia alcanza para escalar.",
  PAUSAR: "El motor dice que la evidencia alcanza para pausar.",
  RENOVAR:
    "El ángulo tiene historia rentable; lo que se cansó en los últimos días es el creativo, no el dolor que vende.",
  SEGUIR_MIDIENDO: "Todavía no alcanza evidencia para decidir: se mantiene el presupuesto tal cual.",
};

/** El veredicto de la CELDA ESCALAR bloqueada por fase: rentable y evidencia de ganador, pero la
 * doctrina de fase (invariantes 6 y 13) prohíbe mover plata en pleno testeo. Nunca compara números
 * acá — la condición es el ESTADO más la presencia de `bloqueo_fase`, ambos del motor. */
const VEREDICTO_ESCALAR_BLOQUEADO =
  "La celda es rentable y cuenta como evidencia de ganador, pero en pleno testeo no se mueve plata.";

export function veredictoDeOrden(
  estado: string | null | undefined,
  bloqueoFase?: string | null,
): string {
  if (estado === "ESCALAR" && bloqueoFase) return VEREDICTO_ESCALAR_BLOQUEADO;
  if (!estado) return "";
  return VEREDICTO_POR_ESTADO[estado] ?? "";
}

/**
 * El titular de la orden, sin ambigüedad. Cuando el estado es ESCALAR pero la fase todavía no
 * lo permite (`bloqueo_fase`), la doctrina manda NO mover presupuesto (invariante 13): el titular
 * dice eso primero, la frase original del motor queda de contexto abajo.
 */
export function tituloDeOrden(
  estado: string | null | undefined,
  fraseSimple: string,
  bloqueoFase: string | null | undefined,
): string {
  if (estado === "ESCALAR" && bloqueoFase) {
    return "No subir presupuesto: mantener el que ya tiene hasta cerrar la fase.";
  }
  return fraseSimple;
}

/**
 * Cuántas ventas faltan para que el motor pueda decidir (A8). Nunca compara ni deriva números:
 * es una traducción de dos campos del motor —`faltan_ventas` y `estado`— a una frase.
 *   - hay número → se dice tal cual (`~N ventas`).
 *   - sin número y el motor sigue midiendo → el motor no llegó a calcularlo (0 ventas, o CPA
 *     pegado al break-even; ver `decidir.py`).
 *   - sin número y cualquier otro estado (ESCALAR, PAUSAR, RENOVAR) → el motor ya decidió sin
 *     necesitar ese conteo.
 */
export function ventasFaltantesEnPalabras(
  faltanVentas: number | null | undefined,
  estado: string | null | undefined,
): string {
  if (faltanVentas != null) return `~${faltanVentas} ventas`;
  if (estado === "SEGUIR_MIDIENDO") return "El motor no calculó cuántas faltan";
  return "No aplica";
}

/** Los tres relojes del motor (`_PARAMETROS_DECISION.csv`), explicados en una línea cada uno.
 * El VALOR sale siempre del contrato; acá solo va la explicación fija de qué mide cada uno. */
export const EXPLICACION_DEL_RELOJ: Record<string, string> = {
  ventana_dias: "Sobre cuántos días se calcula el CPA y el intervalo de confianza.",
  ventana_fatiga_dias: "Cuántos días recientes se comparan contra la ventana, para detectar fatiga.",
  duracion_testeo_fase2_dias: "Cuánto rueda la 1-1-5 de FASE 2 antes de coronar un concepto ganador.",
};

/** Cada herramienta de Meta, dicha por lo que hace. */
export const LLAMADA_DE_META: Record<string, string> = {
  ads_create_campaign: "Crear la campaña",
  ads_create_ad_set: "Crear un conjunto de anuncios",
  ads_create_creative: "Crear un creativo",
  ads_create_ad: "Crear un anuncio",
  ads_creative_upload_media: "Subir una imagen o video",
  ads_activate_entity: "Activar (empieza a gastar)",
  ads_update_entity: "Cambiar algo que ya existe",
};
