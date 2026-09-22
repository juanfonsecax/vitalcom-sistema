/**
 * resumen.tsx — las piezas del resumen de UN producto, compartidas por Tablero (`TarjetaProducto`)
 * y por ProductoDetalle: qué es `motor` (el `dict` libre de `flujo.py`), el título humano del
 * paso vigente, el banner de rezago de ESE producto, y los avisos que trae el recorrido.
 */
import type { Nodo } from "../api/cliente";
import { rezagoEnPalabras } from "../lenguaje";
import { Tarjeta } from "./ui";

/** La info del motor (`flujo.py`) que no tiene tipo propio en el OpenAPI: es un `dict` libre. */
export type MotorInfo = { rezago_dias?: number; datos_hasta?: string };

/**
 * El título humano del paso vigente: el que declara su nodo en el grafo, o si ese nodo no
 * aparece en la lista (`nodos`), la frase «cómo» que ya arma `flujo.py`. El id crudo
 * (`F2.etapa-11`) nunca es este texto — se muestra aparte, como dato secundario.
 */
export function tituloDelPasoActual(
  nodos: Nodo[] | null | undefined,
  nodoActualId: string | null | undefined,
  como: string | null | undefined,
): string {
  const nodoActual = nodos?.find((n) => n.id === nodoActualId);
  return nodoActual?.titulo || como || "Sin paso vigente";
}

/**
 * El banner amber por producto: se muestra cuando el motor trae más de 2 días de rezago en
 * SU data (invariante 13 — una decisión sobre data vieja es una decisión a ciegas). `className`
 * permite que cada pantalla mantenga su propio tamaño de tarjeta.
 */
export function BannerRezago({
  motor,
  className = "rounded-xl border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-200",
}: {
  motor: MotorInfo | null | undefined;
  className?: string;
}) {
  if (motor?.rezago_dias == null || motor.rezago_dias <= 2) return null;
  const rezago = rezagoEnPalabras(motor.rezago_dias);
  return (
    <div className={className}>
      <strong className="text-amber-100">Data con rezago:</strong> {rezago.texto}. Una decisión
      sobre esto es una decisión a ciegas (invariante 13).
    </div>
  );
}

/**
 * Los avisos que trae `flujo.py` (`avisos: string[]` del contrato `Flujo`).
 * `variante="tarjeta"` es la card completa de ProductoDetalle;
 * `variante="compacta"` es la lista chica que entra en la tarjeta de Tablero.
 */
export function AvisosDelRecorrido({
  avisos,
  variante = "tarjeta",
}: {
  avisos: unknown[] | null | undefined;
  variante?: "tarjeta" | "compacta";
}) {
  const lista = (avisos ?? []) as string[];
  if (lista.length === 0) return null;

  if (variante === "compacta") {
    return (
      <ul className="space-y-1">
        {lista.map((aviso, i) => (
          <li
            key={i}
            className="rounded border border-amber-900/50 bg-amber-950/20 px-2 py-1 text-xs text-amber-300"
          >
            {aviso}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <Tarjeta className="border-amber-800/60 bg-amber-950/20">
      <p className="text-sm font-medium text-amber-200">Avisos del recorrido</p>
      <ul className="mt-2 space-y-2">
        {lista.map((aviso, i) => (
          <li key={i} className="text-xs text-amber-300">
            {aviso}
          </li>
        ))}
      </ul>
    </Tarjeta>
  );
}
