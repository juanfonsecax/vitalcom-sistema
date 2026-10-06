/**
 * situacion.tsx — la línea corta que dice dónde está el producto y qué hace falta:
 * «Fase 2 · testeo de conceptos — Paso: … — Trabado: … — Lo hace: …».
 *
 * Todo sale de los datos que ya sirve el backend (`flujo.py`): el título de la fase, el paso,
 * el primer pendiente y su dueño. Acá solo se ordena y se traduce el dueño a un nombre legible;
 * ningún texto se escribe por producto.
 */
import type { ReactNode } from "react";

/** Nombre legible de cada etapa-subagente (`.claude/agents/ETAPA-*.md`). */
const NOMBRE_DE_ETAPA: Record<string, string> = {
  "etapa-producto": "Validador de producto",
  "etapa-0": "Clasificador de videos",
  "etapa-1": "Costeo",
  "etapa-1b": "Voz del cliente",
  "etapa-2": "Fichas de ángulo",
  "etapa-3": "Microángulos",
  "etapa-4": "Copywriter de anuncios",
  "etapa-5": "Flujo del bot",
  "etapa-6": "Planificador de lanzamiento",
  "etapa-7": "Monitor de métricas",
  "etapa-9": "Fábrica de conceptos",
  "etapa-10": "Lector concepto-métrica",
  "etapa-11": "Optimizador de flujo",
  "etapa-render": "Renderizador de creativos",
  "etapa-guardar-producto": "Guardado del producto",
};

/** Nombre corto de cada script que corre solo (sin rutas ni flags en pantalla). */
const NOMBRE_DE_SCRIPT: Record<string, string> = {
  "recopilar_lucidsales.py": "el sistema (recolección de LucidSales)",
  "bajar_lucidsales.py": "el sistema (recolección de LucidSales)",
  "gen_decisiones.py": "el sistema (motor de decisiones)",
  "decidir.py": "el sistema (motor de decisiones)",
  "gen_publicacion.py": "el sistema (generador del paquete)",
  "verificar_publicacion.py": "el sistema (verificación de la publicación)",
  "verificar_producto.py": "el sistema (verificador del producto)",
  "gen_plan.py": "el sistema (validador del plan)",
  "gen_manual.py": "el sistema (generador del manual)",
  "gen_flujo_bot.py": "el sistema (generador del flujo del bot)",
  "registrar_evento.py": "el sistema (registro de eventos)",
};

const SCRIPT_EN_TEXTO = /([\w-]+\.py)\b/g;

const ETAPA_EN_TEXTO = /etapa-(?:guardar-producto|producto|render|\d+b?)/gi;

/** Quién hace algo, dicho como persona: el nombre de la etapa si el texto la nombra; si no,
 * el del script (sin rutas ni flags) o una categoría (vos, el sistema, Claude). Nunca devuelve el comando operativo crudo. */
export function responsableEnPalabras(texto: string | null | undefined): string {
  if (!texto) return "sin ejecutor declarado";
  const etapas = Array.from(new Set((texto.match(ETAPA_EN_TEXTO) ?? []).map((e) => e.toLowerCase())));
  const nombres = etapas.map((e) => NOMBRE_DE_ETAPA[e]).filter(Boolean);
  if (nombres.length > 0) return nombres.join(" + ");
  const scripts = Array.from(new Set(Array.from(texto.matchAll(SCRIPT_EN_TEXTO), (m) => m[1].toLowerCase())));
  if (scripts.length > 0) {
    return Array.from(new Set(scripts.map((x) => NOMBRE_DE_SCRIPT[x] ?? "el sistema"))).join(" + ");
  }
  const minuscula = texto.toLowerCase();
  if (minuscula.startsWith("operador")) return "vos";
  if (minuscula.includes("script")) return "el sistema";
  if (minuscula.includes("mcp")) return "Meta, con tu aprobación";
  if (minuscula.includes("subagente") || minuscula.includes("skill")) return "Claude";
  return texto;
}

export interface DatosDeSituacion {
  fase?: string | null;
  faseTitulo?: string | null;
  paso?: string | null;
  trabadoPor?: string | null;
  /** Dueño del pendiente (`dueno_bloqueante`). */
  dueno?: string | null;
  /** Ejecutor del paso vigente: quien lo hace cuando nada frena. */
  ejecutor?: string | null;
}

function nombreDeFase(fase?: string | null, titulo?: string | null): string {
  if (titulo) {
    const minuscula = titulo.toLowerCase();
    return minuscula.charAt(0).toUpperCase() + minuscula.slice(1);
  }
  if (!fase) return "Sin fase";
  const numero = /^F(?:ASE)?\s*(\d+)/i.exec(fase);
  return numero ? `Fase ${numero[1]}` : fase;
}

export function resumenDeSituacion(d: DatosDeSituacion) {
  return {
    fase: nombreDeFase(d.fase, d.faseTitulo),
    paso: d.paso || null,
    trabado: d.trabadoPor || null,
    loHace: responsableEnPalabras(d.dueno || d.ejecutor),
  };
}

/** La línea completa en texto plano (la usa el título accesible y las pruebas). */
export function lineaDeSituacion(d: DatosDeSituacion): string {
  const r = resumenDeSituacion(d);
  return [
    r.fase,
    r.paso ? `Paso: ${r.paso}` : null,
    r.trabado ? `Trabado: ${r.trabado}` : "Nada lo frena",
    `Lo hace: ${r.loHace}`,
  ]
    .filter(Boolean)
    .join(" — ");
}

export function LineaDeSituacion({
  datos,
  testid,
  className = "text-sm",
  prefijo,
}: {
  datos: DatosDeSituacion;
  testid?: string;
  className?: string;
  /** Algo antes de la fase, p. ej. «Validada»/«Sin validar» en FASE 2. */
  prefijo?: ReactNode;
}) {
  const r = resumenDeSituacion(datos);
  const partes: ReactNode[] = [
    <strong key="fase">{r.fase}</strong>,
    ...(prefijo ? [prefijo] : []),
    ...(r.paso ? [`Paso: ${r.paso}`] : []),
    r.trabado ? `Trabado: ${r.trabado}` : "Nada lo frena",
    `Lo hace: ${r.loHace}`,
  ];
  return (
    <p data-testid={testid} className={className}>
      {partes.map((parte, i) => (
        <span key={i}>
          {i > 0 && " — "}
          {parte}
        </span>
      ))}
    </p>
  );
}
