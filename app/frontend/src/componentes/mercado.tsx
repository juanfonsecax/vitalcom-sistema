/**
 * mercado.tsx — la bandera de cada producto y el selector de mercado (multi-mercado, D2).
 *
 * El selector («Todos · 🇬🇹 Guatemala · 🇨🇴 Colombia») se recuerda por navegador en
 * localStorage (envuelto en try/catch: sin storage la pantalla sigue andando con «Todos»).
 */
import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/cliente";
import { banderaDe, TODOS } from "../dinero";
import { cn } from "./ui";

export const CLAVE_MERCADO = "vitalcom-mercado-v1";

/** La bandera + el código, chico, junto al nombre de un producto. */
export function BanderaMercado({ mercado, className }: { mercado?: string | null; className?: string }) {
  if (!mercado) return null;
  return (
    <span
      data-testid="bandera-mercado"
      title={`Mercado ${mercado}`}
      aria-label={`Mercado ${mercado}`}
      className={cn("inline-flex shrink-0 items-center gap-1 text-[11px] font-medium text-muted-foreground", className)}
    >
      {banderaDe(mercado) && <span aria-hidden="true">{banderaDe(mercado)}</span>}
      <span>{mercado}</span>
    </span>
  );
}

function leerSeleccion(): string {
  try {
    return window.localStorage.getItem(CLAVE_MERCADO) || TODOS;
  } catch {
    return TODOS;
  }
}

/** El mercado elegido y cómo cambiarlo; persiste por navegador. Default «Todos». */
export function usarMercadoSeleccionado(): [string, (mercado: string) => void] {
  const [seleccion, setSeleccion] = useState<string>(leerSeleccion);
  const cambiar = useCallback((mercado: string) => {
    setSeleccion(mercado);
    try {
      window.localStorage.setItem(CLAVE_MERCADO, mercado);
    } catch {
      /* sin localStorage se pierde el recuerdo, nunca la pantalla */
    }
  }, []);
  return [seleccion, cambiar];
}

export function SelectorMercado({
  seleccion,
  onCambiar,
}: {
  seleccion: string;
  onCambiar: (mercado: string) => void;
}) {
  const mercados = useQuery({ queryKey: ["mercados"], queryFn: api.mercados });
  const opciones = [
    { valor: TODOS, texto: "Todos" },
    ...(mercados.data ?? []).map((m) => ({ valor: m.mercado, texto: `${banderaDe(m.mercado)} ${m.pais}`.trim() })),
  ];
  return (
    <div role="group" aria-label="Mercado" data-testid="selector-mercado" className="inline-flex flex-wrap items-center gap-1.5">
      {opciones.map((opcion) => (
        <button
          key={opcion.valor}
          type="button"
          aria-pressed={seleccion === opcion.valor}
          onClick={() => onCambiar(opcion.valor)}
          className={cn(
            "rounded-lg border px-3 py-1 text-sm transition-colors",
            seleccion === opcion.valor
              ? "border-primary bg-primary/10 font-medium text-foreground"
              : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          {opcion.texto}
        </button>
      ))}
    </div>
  );
}
