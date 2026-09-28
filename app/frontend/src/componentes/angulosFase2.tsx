/**
 * angulosFase2.tsx — los bloques por ÁNGULO de la pantalla de FASE 2.
 *
 * Todo lo que se muestra viene ya decidido del backend (`contratos.angulos_de_fase2`, que
 * junta `_DECISIONES.json`, `_ESTADO_ANGULOS.csv` y el orden de `flujo.py`): acá no se
 * calcula ni se ordena nada. Cada ángulo va en su propio bloque; el detalle técnico queda
 * plegado, nunca se quita.
 */
import { Link } from "@tanstack/react-router";
import type { AnguloFase2 } from "../api/cliente";
import { Chip, Tarjeta, type Tono } from "./ui";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const TONO_VEREDICTO: Record<string, Tono> = {
  ESCALAR: "escalar",
  PAUSAR: "pausar",
  RENOVAR: "renovar",
  SEGUIR_MIDIENDO: "seguir",
};

const PALABRA_VEREDICTO: Record<string, string> = {
  ESCALAR: "Rinde bien",
  PAUSAR: "Hay que pausarlo",
  RENOVAR: "Cambiar el creativo",
  SEGUIR_MIDIENDO: "Sigue midiéndose",
};

function Dato({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div>
      <span className="block text-[10px] font-medium uppercase tracking-wide text-zinc-400">{rotulo}</span>
      <span className="block text-xl font-bold tabular-nums text-zinc-100">{valor}</span>
    </div>
  );
}

function CifrasClave({ a }: { a: AnguloFase2 }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <Dato rotulo="Ventas" valor={a.ventas_acum != null ? String(a.ventas_acum) : "—"} />
      <Dato rotulo="Cuesta cada venta" valor={a.cpa_real_q != null ? `Q${a.cpa_real_q}` : "—"} />
      <Dato rotulo="Cierra" valor={a.cierre_pct != null ? `${a.cierre_pct}%` : "—"} />
    </div>
  );
}

function DetalleTecnico({ a }: { a: AnguloFase2 }) {
  const filas: [string, string][] = [
    ["Veredicto del motor", a.estado ?? "sin veredicto"],
    ["Estado del ángulo", a.estado_angulo || "sin perfil"],
    ["Último día con gasto", a.ultimo_dia_gasto || "—"],
    ["Rango probable del costo por venta", a.ic ? `Q${a.ic[0]} a Q${a.ic[2]}` : "—"],
    ["Gasto acumulado", a.spend_acum_q != null ? `Q${a.spend_acum_q}` : "—"],
  ];
  return (
    <Collapsible>
      <CollapsibleTrigger className="text-xs text-zinc-400 underline underline-offset-2 hover:text-zinc-200">
        Ver detalle técnico
      </CollapsibleTrigger>
      <CollapsibleContent>
        <dl className="mt-2 space-y-1 text-xs text-zinc-400">
          {filas.map(([rotulo, valor]) => (
            <div key={rotulo} className="flex justify-between gap-3">
              <dt>{rotulo}</dt>
              <dd className="font-mono text-zinc-300">{valor}</dd>
            </div>
          ))}
        </dl>
        {a.accion_sugerida && <p className="mt-2 text-xs text-zinc-400">Orden del motor: {a.accion_sugerida}</p>}
      </CollapsibleContent>
    </Collapsible>
  );
}

/** El #1: el ángulo que está en su Fase 2 ahora. */
export function AnguloEnTesteoAhora({ angulo, paso }: { angulo: AnguloFase2 | undefined; paso: string }) {
  if (!angulo) {
    return (
      <Tarjeta className="border-zinc-800 bg-zinc-900/40">
        <h2 className="text-base font-bold text-zinc-100">Todavía no hay un ángulo ganador</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Un ángulo entra a esta fase cuando gana por ventas. Mientras tanto, mirá abajo cómo va cada uno.
        </p>
      </Tarjeta>
    );
  }
  return (
    <div data-testid="angulo-en-testeo">
    <Tarjeta className="border-emerald-800/50 bg-emerald-950/20">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            En testeo de conceptos ahora
          </span>
          <h2 className="mt-1 text-lg font-bold text-zinc-100">{angulo.angulo_key}</h2>
          <p className="mt-1 text-xs text-zinc-400">
            Es el #1 por ventas. Este ángulo queda fijo y solo cambia el creativo.
          </p>
        </div>
        {angulo.estado && (
          <Chip tono={TONO_VEREDICTO[angulo.estado] ?? "neutro"}>
            {PALABRA_VEREDICTO[angulo.estado] ?? angulo.estado}
          </Chip>
        )}
      </div>
      <div className="mt-4">
        <CifrasClave a={angulo} />
      </div>
      <div className="mt-3 space-y-2">
        <DetalleTecnico a={angulo} />
        {paso && <p className="text-[11px] text-zinc-500">Paso del flujo: <span className="font-mono">{paso}</span></p>}
      </div>
    </Tarjeta>
    </div>
  );
}

/** #2, #3…: ganadores que esperan su turno. Cada uno tendrá su propia Fase 2. */
export function AngulosEnFila({ angulos }: { angulos: AnguloFase2[] }) {
  if (angulos.length === 0) return null;
  return (
    <section className="space-y-3" data-testid="angulos-en-fila">
      <h3 className="text-sm font-semibold text-zinc-200">En fila</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {angulos.map((a) => (
          <Tarjeta key={a.angulo_key} className="space-y-3 border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-xs font-semibold text-zinc-200">{a.angulo_key}</span>
              <Chip tono="aviso">#{a.posicion} en la fila</Chip>
            </div>
            <CifrasClave a={a} />
            <p className="text-xs text-amber-300">
              Entra a su propia Fase 2 cuando el #1 cierre la suya, unos 3 días después.
            </p>
            <DetalleTecnico a={a} />
          </Tarjeta>
        ))}
      </div>
    </section>
  );
}

/** Los que no ganaron: apagados, con orden de pausa, o todavía midiéndose. */
export function AngulosQueNoFuncionaron({
  angulos,
  trabajoPendiente,
}: {
  angulos: AnguloFase2[];
  trabajoPendiente?: string;
}) {
  if (angulos.length === 0) return null;
  return (
    <section className="space-y-2" data-testid="angulos-no-funcionaron">
      <h3 className="text-sm font-semibold text-zinc-200">Ángulos que no funcionaron</h3>
      <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/30">
        {angulos.map((a) => (
          <li key={a.angulo_key} className="space-y-1 px-4 py-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-mono text-xs text-zinc-200">{a.angulo_key}</span>
              <span className="flex items-center gap-2">
                <Chip tono={a.estado === "PAUSAR" ? "pausar" : a.rol === "midiendo" ? "seguir" : "neutro"}>
                  {a.etiqueta}
                </Chip>
                {a.estado === "PAUSAR" &&
                  (trabajoPendiente ? (
                    <Link
                      to="/trabajos/$id"
                      params={{ id: trabajoPendiente }}
                      className="text-xs text-zinc-300 underline underline-offset-2"
                    >
                      Revisar en Trabajos
                    </Link>
                  ) : (
                    <Link to="/trabajos" className="text-xs text-zinc-300 underline underline-offset-2">
                      Ver en Trabajos
                    </Link>
                  ))}
              </span>
            </div>
            <DetalleTecnico a={a} />
          </li>
        ))}
      </ul>
    </section>
  );
}

export type OrdenMotor = { celda?: string; estado?: string; accion?: string };

/** Las órdenes concretas del motor para renovar creativos (no la doctrina genérica). */
export function OrdenesDeRenovacion({ ordenes }: { ordenes: OrdenMotor[] }) {
  const renovar = ordenes.filter((o) => o.estado === "RENOVAR");
  return (
    <div className="mt-3 space-y-2" data-testid="ordenes-renovar">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-300">Qué hacer</h4>
      {renovar.length === 0 ? (
        <p className="text-sm text-zinc-300">Hoy el motor no pide renovar ningún creativo de este producto.</p>
      ) : (
        renovar.map((o) => (
          <div key={o.celda} className="rounded-lg border border-amber-800/50 bg-amber-950/30 p-3">
            <span className="font-mono text-xs font-semibold text-amber-200">{o.celda}</span>
            <p className="mt-1 text-sm text-zinc-200">{o.accion}</p>
          </div>
        ))
      )}
    </div>
  );
}
