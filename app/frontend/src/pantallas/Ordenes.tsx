/**
 * Ordenes.tsx — pantalla «Órdenes de hoy».
 *
 * Muestra las órdenes literales generadas por `gen_ordenes.py` a partir de `_DECISIONES.json`.
 * Cuatro estados posibles: ESCALAR, PAUSAR, RENOVAR y SEGUIR_MIDIENDO.
 * Todas con explicación en español simple, números de sustento (CPA, IC, BE, ventas faltantes),
 * banner de rezago si la data tiene más de 2 días, y anuncio de ganadores con enlace al paso doctrinal (etapa-11).
 */
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, type ParametroMotor } from "../api/cliente";
import { Button } from "@/components/ui/button";
import { Cargando, Chip, Problema, Tarjeta, type Tono } from "../componentes/ui";
import {
  cierreEnPalabras,
  EXPLICACION_DEL_RELOJ,
  glosarioDeOrden,
  progresoVentasEnPalabras,
  TEXTO_ORDEN,
  tituloDeOrden,
  ventasFaltantesEnPalabras,
  veredictoDeOrden,
} from "../lenguaje";

/** El tono de decisión de cada estado de orden: los cuatro colores reservados del sistema
 * (estado-escalar/pausar/seguir/renovar de `src/estilos.css`), uno por `decidir.py`, nunca
 * reinventado por pantalla. Una celda ESCALAR bloqueada por fase toma el tono de "esperar"
 * (seguir, ámbar), no el de escalar — igual que `CLASE_ESTADO_ORDEN` en Hoy.tsx. */
const TONO_DECISION: Record<string, Tono> = {
  ESCALAR: "escalar",
  PAUSAR: "pausar",
  RENOVAR: "renovar",
  SEGUIR_MIDIENDO: "seguir",
};

type LlamadaMeta = {
  llamada?: number;
  tool?: string;
  entidad_nombre?: string;
  args?: Record<string, unknown>;
  omitir?: boolean;
  valor_antes?: unknown;
  valor_despues?: unknown;
};

type Bloqueante = {
  falta?: string;
  lo_produce?: string;
  ambito?: string;
};

/** Panel «cómo mide el motor»: los tres relojes de `_PARAMETROS_DECISION.csv`, con su valor real
 * y una línea fija de qué mide cada uno. Si un reloj no está en el contrato, se dice así. */
function PanelDeRelojes({ parametros }: { parametros: ParametroMotor[] }) {
  const porNombre = Object.fromEntries(parametros.map((p) => [p.parametro, p]));
  const relojes = Object.keys(EXPLICACION_DEL_RELOJ) as (keyof typeof EXPLICACION_DEL_RELOJ)[];
  return (
    <Tarjeta className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
        Cómo mide el motor
      </p>
      <ul className="space-y-1.5 text-xs text-zinc-400">
        {relojes.map((clave) => {
          const p = porNombre[clave];
          return (
            <li key={clave}>
              <span className="font-mono text-zinc-300">
                {p ? `${p.valor} ${p.unidad}`.trim() : "sin dato en el contrato"}
              </span>{" "}
              — {EXPLICACION_DEL_RELOJ[clave]}
            </li>
          );
        })}
      </ul>
    </Tarjeta>
  );
}

export function Ordenes() {
  const consultaOrdenes = useQuery({ queryKey: ["ordenes"], queryFn: () => api.ordenes() });
  const consultaGanadores = useQuery({ queryKey: ["ganadores"], queryFn: api.ganadores });
  const consultaAcciones = useQuery({ queryKey: ["acciones"], queryFn: () => api.acciones() });

  if (consultaOrdenes.isLoading || consultaGanadores.isLoading) {
    return <Cargando que="las órdenes del día" />;
  }
  if (consultaOrdenes.error) return <Problema error={consultaOrdenes.error} />;

  const datos = consultaOrdenes.data;
  const ganadores = consultaGanadores.data ?? [];
  const ordenes = datos?.ordenes ?? [];
  const llamadas = (datos?.llamadas ?? []) as LlamadaMeta[];
  const rezago = datos?.rezago_dias ?? 0;
  const bloqueantes = (datos?.bloqueantes ?? []) as Bloqueante[];
  const avisos = (datos?.avisos ?? []) as string[];
  const parametrosMotor = datos?.parametros_motor ?? [];
  // Meta de cierre (benchmark 15-20%, UMBRAL_CIERRE_MINIMO_BOT): sale del mismo contrato que
  // el panel de relojes, nunca hardcodeada acá. Si el operador no regeneró el CSV, no está.
  const porNombreMotor = Object.fromEntries(parametrosMotor.map((p) => [p.parametro, p.valor]));
  const cierreMetaMin = porNombreMotor["cierre_meta_min_pct"];
  const cierreMetaMax = porNombreMotor["cierre_meta_max_pct"];

  // Verificar si la acción del ciclo está habilitada en el manifiesto
  const accionCiclo = (consultaAcciones.data ?? []).find((a) => a.id === "nodo.ciclo.ordenes");
  const cicloHabilitado = accionCiclo?.habilitada ?? false;

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <header className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-100">Órdenes de hoy</h1>
            <p className="text-sm text-zinc-400">
              Decisiones traducidas a llamadas literales para Meta. Ninguna orden se ejecuta sin
              confirmación explícita del operador.
            </p>
          </div>
          <Link
            to="/trabajos"
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            Ver cola de trabajos
          </Link>
        </div>
      </header>

      {/* Alerta de rezago si la data tiene más de 2 días */}
      {rezago > 2 && (
        <div className="rounded-xl border border-amber-800 bg-amber-950/40 p-4 text-amber-200">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-amber-100">Aviso de datos con rezago:</span>
            <span>La data tiene {rezago} días de retraso.</span>
          </div>
          <p className="mt-1 text-xs text-amber-300/80">
            Una decisión sobre datos viejos es una decisión a ciegas (invariante 13). Se recomienda
            refrescar la ingesta de LucidSales y Meta antes de autorizar cambios de presupuesto.
          </p>
        </div>
      )}

      <PanelDeRelojes parametros={parametrosMotor} />

      {/* Banner de Ganadores detectados por venta */}
      {ganadores.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
            Ganadores detectados por venta (invariante 1)
          </h2>
          <div className="grid gap-3 md:grid-cols-2">
            {ganadores.map((g) => (
              <Tarjeta key={g.producto_key} className="border-emerald-800/60 bg-emerald-950/20">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-medium text-emerald-400">FASE 2 ALCANZADA</span>
                    <h3 className="text-lg font-bold text-zinc-100">{g.nombre || g.producto_key}</h3>
                  </div>
                  <Chip tono="bien">{g.fase || "F2"}</Chip>
                </div>
                <p className="mt-2 text-xs text-zinc-300">
                  <strong className="text-zinc-100">Ángulo ganador:</strong> {g.angulo_ganador}
                </p>
                <div className="mt-4 flex items-center justify-between border-t border-emerald-900/40 pt-3">
                  <div className="text-xs text-zinc-400">
                    <span className="block font-medium text-zinc-300">Siguiente paso doctrinal:</span>
                    <span>{g.siguiente_paso?.titulo || "etapa-11 → FASE 2"}</span>
                  </div>
                  <Button
                    size="sm"
                    render={
                      <Link
                        to={g.siguiente_paso?.enlace || `/producto/${g.producto_key}`}
                      />
                    }
                  >
                    Ir al flujo
                  </Button>
                </div>
              </Tarjeta>
            ))}
          </div>
        </section>
      )}

      {/* Lista de Órdenes del día */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-100">
            Acciones recomendadas ({ordenes.length})
          </h2>
          {!cicloHabilitado && (
            <span className="text-xs text-zinc-400">
              Ejecución automática en Meta deshabilitada por doctrina (modo manual/revisión).
            </span>
          )}
        </div>

        {ordenes.length === 0 ? (
          <Tarjeta className="py-8 text-center text-zinc-400">
            No hay órdenes pendientes para hoy. El motor midió y todas las campañas continúan su curso.
          </Tarjeta>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {ordenes.map((orden, idx) => {
              const pq = orden.por_que || {};
              const ic = pq.ic as number[] | undefined;
              // ESCALAR con bloqueo_fase es la celda que la doctrina frena en pleno testeo
              // (invariante 13): chip, titular, veredicto narrado y glosario lo dicen todos igual,
              // nunca "escalar" — solo lookup sobre ESTADO + bloqueo_fase, nunca comparar números.
              const escalarBloqueado = orden.estado === "ESCALAR" && Boolean(orden.bloqueo_fase);
              const titulo = tituloDeOrden(orden.estado, orden.frase_simple, orden.bloqueo_fase);
              const glosarioDelEstado = glosarioDeOrden(orden.estado, orden.bloqueo_fase);
              return (
                <Tarjeta key={`${orden.producto_key}-${orden.angulo_key}-${idx}`} className="flex flex-col justify-between gap-4">
                  <div>
                    {/* Cabecera de la tarjeta */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          to="/producto/$clave"
                          params={{ clave: orden.producto_key }}
                          className="text-base font-bold text-zinc-100 hover:text-sky-300"
                        >
                          {orden.producto_key}
                        </Link>
                        <p className="text-xs text-zinc-400">
                          Ángulo: <span className="font-semibold text-zinc-200">{orden.angulo_nombre || orden.angulo_key}</span>
                        </p>
                      </div>
                      <Chip tono={escalarBloqueado ? "seguir" : (TONO_DECISION[orden.estado] ?? "neutro")}>
                        {escalarBloqueado ? "Escalar bloqueado por fase" : (TEXTO_ORDEN[orden.estado] ?? orden.estado)}
                      </Chip>
                    </div>

                    {/* Titular sin ambigüedad: qué HACER primero, la frase del motor de contexto */}
                    <div className="mt-3 rounded-lg bg-zinc-950/60 p-3 text-sm text-zinc-200 border border-zinc-800/80">
                      <p className="font-semibold text-zinc-100">{titulo}</p>
                      {titulo !== orden.frase_simple && (
                        <p className="mt-1 text-xs text-zinc-400">Orden original del motor: {orden.frase_simple}</p>
                      )}
                    </div>

                    {/* La frase narrada: qué dicen los números, en una oración */}
                    {ic && ic.length === 3 && pq.break_even_q != null && (
                      <p className="mt-2 text-xs text-zinc-400">
                        Cada venta te está costando entre{" "}
                        <span className="font-mono text-zinc-300">Q{ic[0]}</span> y{" "}
                        <span className="font-mono text-zinc-300">Q{ic[2]}</span>; tu techo es{" "}
                        <span className="font-mono text-zinc-300">Q{pq.break_even_q as number}</span>.{" "}
                        {veredictoDeOrden(orden.estado, orden.bloqueo_fase)}
                      </p>
                    )}

                    {/* Por qué este estado, en las palabras del glosario (nunca inventadas acá) */}
                    {glosarioDelEstado && (
                      <p className="mt-2 text-xs text-zinc-400">
                        <strong className="text-zinc-400">{glosarioDelEstado.rotulo}:</strong>{" "}
                        {glosarioDelEstado.que_es}
                      </p>
                    )}

                    {/* Métricas de sustento */}
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-zinc-400">
                      <div>
                        <span className="block text-zinc-400">CPA Observado:</span>
                        <span className="font-semibold text-zinc-200">
                          {pq.cpa_real_q != null ? `Q${pq.cpa_real_q}` : "Sin datos"}
                        </span>
                      </div>
                      <div>
                        <span className="block text-zinc-400">Break-even:</span>
                        <span className="font-semibold text-zinc-200">
                          {pq.break_even_q != null ? `Q${pq.break_even_q}` : "No fijado"}
                        </span>
                      </div>
                      <div>
                        <span className="block text-zinc-400">Intervalo 95%:</span>
                        <span className="font-mono text-zinc-300">
                          {ic && ic.length === 3 ? `[${ic[0]}, ${ic[2]}]` : "No disponible"}
                        </span>
                      </div>
                      <div>
                        <span className="block text-zinc-400">Ventas faltantes:</span>
                        {pq.ventas_actual != null && pq.ventas_necesarias != null ? (
                          <div className="mt-1">
                            <progress
                              className="h-1.5 w-full accent-sky-500"
                              value={pq.ventas_actual as number}
                              max={pq.ventas_necesarias as number}
                              aria-label={progresoVentasEnPalabras(
                                pq.ventas_actual as number,
                                pq.ventas_necesarias as number,
                              )}
                            />
                            <span className="text-zinc-300">
                              {progresoVentasEnPalabras(
                                pq.ventas_actual as number,
                                pq.ventas_necesarias as number,
                              )}
                            </span>
                          </div>
                        ) : (
                          <span className="text-zinc-300">
                            {ventasFaltantesEnPalabras(pq.faltan_ventas as number | null | undefined, orden.estado)}
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="block text-zinc-400">Cierre (mensajes → ventas):</span>
                        <span className="text-zinc-300">
                          {cierreEnPalabras(pq.cierre_pct as number | null | undefined, cierreMetaMin, cierreMetaMax)}
                        </span>
                      </div>
                    </div>

                    {/* Bloqueo de fase o advertencia */}
                    {orden.bloqueo_fase && (
                      <div className="mt-3 rounded border border-amber-900/50 bg-amber-950/20 p-2 text-xs text-amber-300">
                        <strong>Nota de fase:</strong> {orden.bloqueo_fase}
                      </div>
                    )}
                  </div>

                  {/* Acciones de confirmación */}
                  <div className="flex items-center justify-between border-t border-zinc-800 pt-3">
                    <span className="text-xs text-zinc-400">
                      {orden.ejecutable ? "Listo para revisión" : "Solo informativo"}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={!cicloHabilitado || !orden.ejecutable}
                        title={!cicloHabilitado ? "Ejecución deshabilitada en manifiesto" : "Rechazar orden"}
                      >
                        Rechazar
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        disabled={!cicloHabilitado || !orden.ejecutable}
                        title={!cicloHabilitado ? "Ejecución deshabilitada en manifiesto" : "Aprobar orden en Meta"}
                      >
                        Aprobar
                      </Button>
                    </div>
                  </div>
                </Tarjeta>
              );
            })}
          </div>
        )}
      </section>

      {/* Detalle literal de llamadas a Meta */}
      {llamadas.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-base font-semibold text-zinc-100">
            Llamadas literales preparadas para Meta ({llamadas.length})
          </h2>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="divide-y divide-zinc-800 font-mono text-xs">
              {llamadas.map((ll, idx) => (
                <div key={idx} className="py-2.5 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between text-zinc-300">
                    <span>
                      #{ll.llamada} · <span className="font-semibold text-sky-400">{ll.tool}</span> ({ll.entidad_nombre || String(ll.args?.entity_id ?? "")})
                    </span>
                    <Chip tono={ll.omitir ? "neutro" : "bien"}>
                      {ll.omitir ? "omitir (idempotente)" : "por aplicar"}
                    </Chip>
                  </div>
                  <div className="mt-1.5 text-zinc-400">
                    Cambio: <span className="text-rose-300">{JSON.stringify(ll.valor_antes)}</span>
                    {" → "}
                    <span className="text-emerald-300">{JSON.stringify(ll.valor_despues)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Avisos y bloqueantes */}
      {(bloqueantes.length > 0 || avisos.length > 0) && (
        <section className="space-y-2">
          {bloqueantes.map((b, i) => (
            <div key={i} className="rounded-lg border border-rose-900/60 bg-rose-950/30 p-3 text-xs text-rose-300">
              <strong>Bloqueante:</strong> {b.falta} (produce: {b.lo_produce})
            </div>
          ))}
          {avisos.map((a, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-400">
              <strong>Aviso:</strong> {a}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
