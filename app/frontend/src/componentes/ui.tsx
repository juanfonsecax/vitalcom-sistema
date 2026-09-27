/**
 * ui.tsx — las piezas visuales compartidas.
 *
 * Están escritas a mano, en el estilo de shadcn/ui (Tailwind + clases compuestas) pero sin
 * su CLI, que instala componentes desde un registro remoto. Son cuatro piezas chicas y la
 * app no necesita más por ahora; cuando haga falta un componente con comportamiento
 * (diálogo, menú), se trae shadcn/ui en serio en vez de reinventarlo.
 */
import { useState, type ReactNode } from "react";
import { GLOSARIO, type ClaveGlosario } from "../glosario";

export function cn(...clases: (string | false | undefined)[]) {
  return clases.filter(Boolean).join(" ");
}

export function Tarjeta({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div data-slot="card" className={cn("rounded-xl border border-border bg-card p-5", className)}>
      {children}
    </div>
  );
}

const TONOS = {
  neutro: "bg-zinc-800 text-zinc-300 border-zinc-700",
  bien: "bg-emerald-950 text-emerald-300 border-emerald-800",
  aviso: "bg-amber-950 text-amber-300 border-amber-800",
  alto: "bg-rose-950 text-rose-300 border-rose-800",
  dato: "bg-sky-950 text-sky-300 border-sky-800",
} as const;

export type Tono = keyof typeof TONOS;

export function Chip({
  children,
  tono = "neutro",
  titulo,
}: {
  children: ReactNode;
  tono?: Tono;
  titulo?: string;
}) {
  return (
    <span
      title={titulo}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
        TONOS[tono],
      )}
    >
      {children}
    </span>
  );
}

/**
 * El (i) del glosario vivo: cada palabra técnica explica qué es y quién manda sobre ella.
 * Funciona con clic (no solo hover) para que también sirva en pantalla táctil.
 */
export function Info({ termino }: { termino: ClaveGlosario }) {
  const [abierto, setAbierto] = useState(false);
  const { rotulo, que_es, dueno } = GLOSARIO[termino];
  return (
    <span className="relative inline-block">
      <button
        type="button"
        aria-label={`Qué es ${rotulo}`}
        aria-expanded={abierto}
        onClick={() => setAbierto((v) => !v)}
        onBlur={() => setAbierto(false)}
        className="ml-1 h-4 w-4 rounded-full border border-muted-foreground/60 text-[10px] leading-none text-muted-foreground hover:border-foreground hover:text-foreground transition-colors"
      >
        i
      </button>
      {abierto && (
        <span
          role="tooltip"
          className="absolute left-1/2 z-20 mt-2 w-72 -translate-x-1/2 rounded-lg border border-border bg-popover p-3 text-xs font-normal text-foreground shadow-xl"
        >
          <strong className="block text-foreground">{rotulo}</strong>
          {que_es}
          {dueno && <em className="mt-1 block not-italic text-muted-foreground">Lo produce: {dueno}</em>}
        </span>
      )}
    </span>
  );
}

export function Cargando({ que }: { que: string }) {
  return <p className="animate-pulse text-sm text-muted-foreground">Leyendo {que}…</p>;
}

export function Problema({ error }: { error: unknown }) {
  const mensaje = error instanceof Error ? error.message : String(error);
  return (
    <Tarjeta className="border-rose-900 bg-rose-950/40">
      <p className="text-sm text-rose-200">
        <strong>No pude leer el sistema.</strong> {mensaje}
      </p>
      <p className="mt-2 text-xs text-rose-300/70">
        La app solo muestra lo que el motor produce. Si falta un archivo, lo genera su dueño; la
        app no lo inventa.
      </p>
    </Tarjeta>
  );
}
