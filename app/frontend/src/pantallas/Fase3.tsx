/**
 * Fase3.tsx — Pantalla de FASE 3: optimización del flujo LucidBot.
 *
 * El ángulo y el concepto ya están validados (concepto ganador 2 de 2, el mismo gate de
 * siempre): acá la variable es el FLUJO del bot, no la estructura de Meta ni el presupuesto
 * (invariante 6, mismo presupuesto). Muestra:
 *  1. Semáforo del gate de entrada (concepto ganador en 2 de 2) — igual al que usaba FASE 4.
 *  2. Qué hacer: etapa-5 reescribe el flujo hacia el ganador (`F3.reescribir`), con el botón real
 *     de la acción cuando el manifiesto la habilita.
 *  3. Los eventos CAMBIO_BOT/EXCEPCION_CAMBIO_BOT registrados.
 *  4. El gate duro de salida hacia FASE 4 (`gate_f4`, PROHIBIDO_ESCALAR_CIERRE_BAJO): mensajes,
 *     cierre % contra el piso de 10 % y el benchmark de referencia 15-20 %, tal como lo calculó
 *     `flujo.py` — esta pantalla no resta, no divide, no compara: solo muestra los campos del
 *     contrato.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api } from "../api/cliente";
import { Button } from "@/components/ui/button";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";
import { cierreEnPalabras } from "../lenguaje";

export function Fase3({ clave: claveProp }: { clave?: string }) {
  const params = useParams({ strict: false }) as { clave?: string };
  const clave = claveProp || params.clave || "";
  const queryClient = useQueryClient();
  const consulta = useQuery({
    queryKey: ["fase3", clave],
    queryFn: () => api.fase3(clave),
  });

  const [confirmando, setConfirmando] = useState(false);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const accionesQuery = useQuery({
    queryKey: ["acciones", "F3.reescribir", clave],
    queryFn: () => api.acciones("F3.reescribir", clave),
  });
  const accionReescribir = (accionesQuery.data || []).find((a) => a.id === "nodo.F3.reescribir");

  const reescribir = useMutation({
    mutationFn: () => api.pedirAccion("nodo.F3.reescribir", { producto_key: clave }, true),
    onSuccess: () => {
      setConfirmando(false);
      queryClient.invalidateQueries({ queryKey: ["acciones", "F3.reescribir", clave] });
    },
    onError: (err) => {
      setErrorAccion(err instanceof Error ? err.message : String(err));
    },
  });

  if (consulta.isLoading) return <Cargando que="el tablero de FASE 3" />;
  if (consulta.error) return <Problema error={consulta.error} />;

  const d = consulta.data;
  if (!d) return null;

  const gateEntrada = d.entrada.ok;
  const gate = d.gate_f4;
  const tieneCambioBot = d.eventos_cambio_bot.length > 0;
  const gateF4Cumplido = d.entrada_f4.ok;

  return (
    <div className="space-y-6">
      {/* Encabezado — sin "Volver a la ficha": ProductoDetalle (P4/T3) ya da esa vuelta, esta
          pantalla vive dentro de su pestaña "Fase 3". */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            FASE 3 · Flujo LucidBot ({clave})
          </h1>
          <p className="text-sm text-zinc-400">
            Ángulo y concepto ya validados, mismo presupuesto · se optimiza el CIERRE del bot · <Info termino="fase_3" />
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/producto/$clave/fase2"
            params={{ clave }}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            ← Ver FASE 2 (Conceptos)
          </Link>
          <Link
            to="/producto/$clave/fase4"
            params={{ clave }}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            Ver FASE 4 (Escalado) →
          </Link>
        </div>
      </div>

      {/* Semáforo del Gate de Entrada: Concepto Ganador en 2 de 2 (el mismo de siempre) */}
      <Tarjeta
        className={`border-2 p-5 ${
          gateEntrada ? "border-emerald-600 bg-emerald-950/20" : "border-amber-600/80 bg-amber-950/20"
        }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Gate de Entrada a FASE 3
              </span>
              <Chip tono={gateEntrada ? "bien" : "aviso"}>
                {gateEntrada ? "✓ GATE CUMPLIDO" : "⚠ GATE PENDIENTE"}
              </Chip>
            </div>
            <h2 className="text-lg font-bold text-zinc-100">Concepto Ganador Replicado en 2 de 2</h2>
            <p className="text-xs text-zinc-300">
              {d.entrada.regla || "Regla de replicación: un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido."}
            </p>
          </div>
          <div className="rounded-lg bg-zinc-900/80 p-3 text-right">
            <span className="text-[11px] uppercase text-zinc-400">Evidencia del Motor</span>
            <div className="mt-1 font-mono text-xs font-semibold text-zinc-200">
              {d.entrada.observado || "Sin datos de replicación"}
            </div>
          </div>
        </div>
      </Tarjeta>

      {/* Qué hacer en esta fase */}
      <Tarjeta className="space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <h3 className="text-sm font-bold text-zinc-200">
            Reescribir el flujo hacia el ángulo + concepto ganador
          </h3>
          <Chip tono={d.nodo_reescribir?.cumplido ? "bien" : "aviso"}>
            {d.nodo_reescribir?.cumplido ? "CUMPLIDO" : d.nodo_reescribir ? "PENDIENTE" : "N/D"}
          </Chip>
        </div>
        <ol className="list-decimal space-y-1.5 pl-5 text-xs text-zinc-300">
          <li>
            <strong className="text-zinc-100">etapa-11</strong> ya diagnosticó el cierre y la
            congruencia anuncio↔bot en FASE 2 (<code className="text-zinc-400">F2.etapa-11</code>,
            evento <code className="text-zinc-400">DIAGNOSTICO_CONGRUENCIA</code>).
          </li>
          <li>
            <strong className="text-zinc-100">etapa-5</strong> redacta los bloques de juicio del
            flujo (<code className="text-zinc-400">PLANTILLAS_FLUJO_BOT.md</code> reglas A-G) a
            partir de ese brief.
          </li>
          <li>
            Vos aplicás el cambio en LucidBot a mano (no es un objeto de Meta, no hay MCP) y anexás
            el evento <code className="text-zinc-400">CAMBIO_BOT</code> — o{" "}
            <code className="text-zinc-400">EXCEPCION_CAMBIO_BOT</code> si decidís saltarte la
            reescritura — con <code className="text-zinc-400">registrar_evento.py</code>.
          </li>
        </ol>

        {accionReescribir && (
          <div className="flex flex-wrap items-center gap-3 border-t border-zinc-800 pt-3">
            <Button
              type="button"
              size="sm"
              onClick={() => setConfirmando(true)}
              disabled={accionReescribir.disponible === false}
            >
              Reescribir el flujo (etapa-5)
            </Button>
            {accionReescribir.disponible === false && accionReescribir.por_que && (
              <span className="text-xs text-amber-300">
                {String((accionReescribir.por_que as Record<string, unknown>)?.motivo ?? "No disponible todavía")}
              </span>
            )}
          </div>
        )}

        {errorAccion && (
          <div className="rounded-lg border border-rose-900 bg-rose-950/40 p-3 text-sm text-rose-300">
            <strong>Error:</strong> {errorAccion}
          </div>
        )}

        {confirmando && (
          <div className="rounded-lg border border-amber-700 bg-amber-950/30 p-3">
            <h4 className="font-semibold text-amber-200">¿Confirmar la reescritura del flujo?</h4>
            <p className="mt-1 text-xs text-zinc-300">
              Esta acción llama a Claude Code (etapa-5) para redactar los bloques de juicio del
              flujo LucidBot. Modifica <code>PRODUCTOS/_DIM_FLUJO_BOT.csv</code>; el CAMBIO_BOT en
              sí lo registrás vos después de aplicarlo a mano en LucidBot.
            </p>
            <div className="mt-3 flex gap-2">
              <Button
                type="button"
                size="sm"
                onClick={() => reescribir.mutate()}
                disabled={reescribir.isPending}
              >
                {reescribir.isPending ? "Iniciando…" : "Sí, confirmar y ejecutar"}
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => setConfirmando(false)}>
                Cancelar
              </Button>
            </div>
          </div>
        )}
      </Tarjeta>

      {/* Eventos CAMBIO_BOT registrados */}
      <Tarjeta className="space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <h3 className="text-sm font-bold text-zinc-200">
            Eventos <Info termino="cambio_bot" />
          </h3>
          <Chip tono={tieneCambioBot ? "bien" : "aviso"}>
            {tieneCambioBot ? `${d.eventos_cambio_bot.length} registrado(s)` : "Ninguno todavía"}
          </Chip>
        </div>
        {tieneCambioBot ? (
          <ul className="space-y-1.5 text-xs text-zinc-300">
            {d.eventos_cambio_bot.map((ev, i) => (
              <li key={i} className="rounded bg-zinc-950 p-2">
                <span className="font-mono font-semibold text-zinc-100">{ev.evento}</span>{" "}
                <span className="text-zinc-400">· {ev.fecha}</span>
                {ev.motivo && <div className="mt-0.5 text-zinc-400">{ev.motivo}</div>}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-zinc-400">
            Todavía no hay <code className="text-zinc-300">CAMBIO_BOT</code> ni{" "}
            <code className="text-zinc-300">EXCEPCION_CAMBIO_BOT</code> registrado para este
            producto. Se registra con{" "}
            <code className="text-zinc-300">
              python Ads/_TOOLS/registrar_evento.py --producto {clave || "&lt;PK&gt;"} --evento CAMBIO_BOT
            </code>{" "}
            el mismo día que apliques el cambio en LucidBot.
          </p>
        )}
      </Tarjeta>

      {/* Gate duro de salida hacia FASE 4: cierre post-CAMBIO_BOT */}
      <Tarjeta
        className={`space-y-3 border-2 p-5 ${
          gateF4Cumplido ? "border-emerald-600 bg-emerald-950/20" : "border-amber-600/80 bg-amber-950/20"
        }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-800 pb-2">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Gate duro hacia FASE 4
              </span>
              <Chip tono={gateF4Cumplido ? "bien" : "aviso"}>
                {gateF4Cumplido ? "✓ DESBLOQUEA FASE 4" : "⚠ SE QUEDA EN FASE 3"}
              </Chip>
            </div>
            <h3 className="text-sm font-bold text-zinc-200">
              <Info termino="cierre_post_cambio_bot" />
            </h3>
          </div>
        </div>

        {gate ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-zinc-950 p-3 text-xs text-zinc-300 space-y-1">
              <div>
                <span className="text-zinc-400">Mensajes desde el CAMBIO_BOT:</span>{" "}
                <span className="font-mono font-semibold text-zinc-100">
                  {gate.mensajes ?? "s/d"}
                </span>{" "}
                <span className="text-zinc-500">(mínimo {gate.min_mensajes ?? "?"})</span>
              </div>
              <div>
                <span className="text-zinc-400">Ventas en esa ventana:</span>{" "}
                <span className="font-mono font-semibold text-zinc-100">{gate.ventas ?? "s/d"}</span>
              </div>
              <div>
                <span className="text-zinc-400">Fecha de corte:</span>{" "}
                <span className="font-mono text-zinc-200">{gate.fecha_cambio_bot ?? "sin CAMBIO_BOT todavía"}</span>
              </div>
            </div>
            <div className="rounded-lg bg-zinc-950 p-3 text-xs text-zinc-300 space-y-1">
              <div>
                <span className="text-zinc-400">Cierre observado:</span>{" "}
                <span className="font-mono font-semibold text-zinc-100">
                  {cierreEnPalabras(
                    gate.cierre_pct ?? null,
                    gate.cierre_meta_min_pct != null ? String(gate.cierre_meta_min_pct) : undefined,
                    gate.cierre_meta_max_pct != null ? String(gate.cierre_meta_max_pct) : undefined,
                  )}
                </span>
              </div>
              <div>
                <span className="text-zinc-400">Piso duro (PROHIBIDO_ESCALAR_CIERRE_BAJO):</span>{" "}
                <span className="font-mono font-semibold text-zinc-100">{gate.min_cierre_pct ?? "?"} %</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-zinc-400">
            Todavía no hay data de este gate: el producto ni siquiera entró a FASE 3.
          </p>
        )}

        <p className="text-[11px] text-zinc-500">
          {gate?.explicacion || d.entrada_f4.observado}
        </p>
      </Tarjeta>
    </div>
  );
}
