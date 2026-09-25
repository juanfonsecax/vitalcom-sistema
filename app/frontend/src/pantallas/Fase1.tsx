/**
 * Fase1.tsx — pantalla de FASE 1 (Hito 4)
 *
 * Muestra el recorrido completo de FASE 1:
 *  a) Avance (los 9 pasos, botón Armar FASE 1 y Reintentar)
 *  b) Investigación (salidas de etapa-1b, etapa-1 y etapa-0 legibles)
 *  c) Avatares y ángulos (fichas con nivel de conciencia, sin TOFU/MOFU/BOFU, y texto de etapa-2)
 *  d) Anuncios (copies, imagen o aviso de falta de pieza, y prompt_imagen con Copiar)
 *  e) Flujo LucidBot (bloques con Copiar, instrucciones >> aparte y nunca en el copiado)
 *  f) Estructura de campaña (campaña, conjuntos, lanzamiento 4 AM, presupuesto, bloqueantes)
 *  g) Checklist (faltantes y bloqueos con su escritor: page_id, cuenta, piezas individuales, transcripciones)
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import {
  api,
  type CampanaF1,
  type ChecklistF1,
  type CorridaF1,
  type FlujoBot,
  type PasoDeCorrida,
} from "../api/cliente";
import { Cargando, Chip, Problema, Tarjeta, cn, type Tono } from "../componentes/ui";

export type TabId =
  | "avance"
  | "investigacion"
  | "angulos"
  | "anuncios"
  | "flujo-bot"
  | "campana"
  | "checklist";

export const ESTADO_PASO_TONO: Record<string, Tono> = {
  PENDIENTE: "neutro",
  CORRIENDO: "dato",
  EXITO: "bien",
  HEREDADO: "bien",
  ESPERA_RESPUESTA: "aviso",
  FALLIDO: "alto",
};

export const ESTADO_PASO_PALABRAS: Record<string, string> = {
  PENDIENTE: "Pendiente",
  CORRIENDO: "Corriendo",
  EXITO: "Terminó bien",
  HEREDADO: "Heredado de la corrida anterior",
  ESPERA_RESPUESTA: "Esperando respuesta",
  FALLIDO: "Falló",
};

export function palabrasDeEstado(estado: string | null | undefined): string {
  if (!estado) return "Pendiente";
  return ESTADO_PASO_PALABRAS[estado] ?? estado;
}

export function Copiar({ texto, label = "copiar" }: { texto: string; label?: string }) {
  const [copiado, setCopiado] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard?.writeText(texto).then(() => {
          setCopiado(true);
          setTimeout(() => setCopiado(false), 2000);
        });
      }}
      className="rounded border border-zinc-700 bg-zinc-800/80 px-2 py-1 text-xs text-zinc-200 hover:border-zinc-500 hover:bg-zinc-700"
    >
      {copiado ? "Copiado ✓" : label}
    </button>
  );
}

export function formatearNegrita(texto: string): React.ReactNode {
  const partes = texto.split(/(\*\*[^*]+\*\*)/g);
  return partes.map((parte, i) => {
    if (parte.startsWith("**") && parte.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-zinc-100">
          {parte.slice(2, -2)}
        </strong>
      );
    }
    return parte;
  });
}

export function TextoLegible({ texto }: { texto: string | null | undefined }) {
  if (!texto) {
    return (
      <p className="text-xs italic text-zinc-500">
        Pendiente: esta etapa todavía no ha generado contenido.
      </p>
    );
  }

  const lineas = texto.split("\n");
  const elementos: React.ReactNode[] = [];
  let bloqueLista: string[] = [];

  const volcarLista = (key: string) => {
    if (bloqueLista.length > 0) {
      elementos.push(
        <ul key={key} className="my-2 list-disc space-y-1 pl-5 text-sm text-zinc-300">
          {bloqueLista.map((item, idx) => (
            <li key={idx}>{formatearNegrita(item)}</li>
          ))}
        </ul>,
      );
      bloqueLista = [];
    }
  };

  lineas.forEach((linea, idx) => {
    const lim = linea.trim();
    if (lim.startsWith("- ") || lim.startsWith("* ")) {
      bloqueLista.push(lim.slice(2));
      return;
    }
    volcarLista(`lista-${idx}`);

    if (lim.startsWith("### ")) {
      elementos.push(
        <h4 key={idx} className="mt-4 mb-1 text-sm font-semibold text-sky-300">
          {lim.slice(4)}
        </h4>,
      );
    } else if (lim.startsWith("## ")) {
      elementos.push(
        <h3
          key={idx}
          className="mt-5 mb-2 border-b border-zinc-800 pb-1 text-base font-semibold text-zinc-100"
        >
          {lim.slice(3)}
        </h3>,
      );
    } else if (lim.startsWith("# ")) {
      elementos.push(
        <h2 key={idx} className="mt-6 mb-3 text-lg font-bold text-zinc-100">
          {lim.slice(2)}
        </h2>,
      );
    } else if (lim.length > 0) {
      elementos.push(
        <p key={idx} className="my-1.5 text-sm leading-relaxed text-zinc-300">
          {formatearNegrita(lim)}
        </p>
      );
    }
  });
  volcarLista("lista-final");

  return <div className="space-y-1">{elementos}</div>;
}

export function extraerTextoAngulo(
  etapa2Texto: string | null | undefined,
  indice: number,
): string | null {
  if (!etapa2Texto) return null;
  const bloques = etapa2Texto.split(/(?:^|\n)(?=#{0,3}\s*ÁNGULO\s+\d+\s*—)/i);
  const prefijo = `ÁNGULO ${indice}`;
  const bloqueExacto = bloques.find((b) =>
    b.trim().toUpperCase().startsWith(prefijo.toUpperCase()),
  );
  if (bloqueExacto) return bloqueExacto.trim();
  return null;
}

/* ──────────────── Pestaña Avance ──────────────── */
function TabAvance({
  clave,
  corrida,
  onArmarExito,
}: {
  clave: string;
  corrida: CorridaF1 | undefined;
  onArmarExito: (jobId: string) => void;
}) {
  const [confirmando, setConfirmando] = useState(false);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const accionesQuery = useQuery({
    queryKey: ["acciones", "F1.paquete", clave],
    queryFn: () => api.acciones("F1.paquete", clave),
  });
  const accionF1 = (accionesQuery.data || []).find((a) => a.id === "nodo.F1.paquete");

  const armar = useMutation({
    mutationFn: () =>
      api.pedirAccion("nodo.F1.paquete", { producto_key: clave }, true),
    onSuccess: (data) => {
      setConfirmando(false);
      onArmarExito(data.job_id);
    },
    onError: (err) => {
      setErrorAccion(err instanceof Error ? err.message : String(err));
    },
  });

  const reintentar = useMutation({
    mutationFn: (jobId: string) => api.reintentar(jobId, true),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["fase1-corrida", clave] });
      onArmarExito(data.job_id);
    },
    onError: (err) => {
      setErrorAccion(err instanceof Error ? err.message : String(err));
    },
  });

  const c = corrida?.corrida;
  const pasos: PasoDeCorrida[] = c?.pasos || [];

  return (
    <div className="space-y-6">
      <Tarjeta className="flex flex-wrap items-center justify-between gap-4 border-sky-800/40 bg-sky-950/20">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100">
            Armado de FASE 1 · 9 pasos
          </h2>
          <p className="text-sm text-zinc-400">
            Ejecuta etapa por etapa respetando los grupos en paralelo.
          </p>
          {c?.job_id && (
            <div className="mt-2 flex items-center gap-3 text-xs">
              <span className="text-zinc-400">Trabajo actual:</span>
              <Link
                to="/trabajos/$id"
                params={{ id: c.job_id }}
                className="font-mono text-sky-400 underline hover:text-sky-300"
              >
                /trabajos/{c.job_id}
              </Link>
              {c.retomado_de && (
                <span className="text-zinc-500">
                  (retomado de {c.retomado_de.slice(0, 8)})
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {c?.job_id && c.estado === "FALLIDO" && (
            <button
              type="button"
              onClick={() => reintentar.mutate(c.job_id!)}
              disabled={reintentar.isPending}
              className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
            >
              {reintentar.isPending ? "Retomando…" : "Retomar"}
            </button>
          )}
          <button
            type="button"
            onClick={() => setConfirmando(true)}
            className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500"
          >
            Armar FASE 1
          </button>
        </div>
      </Tarjeta>

      {/* Si la acción no está disponible, mostrar el porqué que devuelve la API */}
      {accionF1 && accionF1.disponible === false && (() => {
        const porQue = accionF1.por_que as Record<string, any> | null | undefined;
        const bloqueantes = Array.isArray(porQue?.bloqueantes) ? porQue.bloqueantes : [];
        return (
          <Tarjeta className="border-amber-800/60 bg-amber-950/20 text-xs space-y-1">
            <h4 className="font-semibold text-amber-200">
              La acción «Armar FASE 1» no está disponible en este momento:
            </h4>
            {Boolean(porQue?.motivo) && (
              <p className="text-amber-300">{String(porQue?.motivo)}</p>
            )}
            {bloqueantes.length > 0 && (
              <div className="text-amber-300">
                <span>Falta resolver para poder armar:</span>
                <ul className="mt-1 list-disc pl-5">
                  {bloqueantes.map((b: any, idx: number) => (
                    <li key={idx}>
                      {String(b.dato || JSON.stringify(b))} (dueño: {String(b.dueno || "operador")})
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {Boolean(porQue?.nodo_actual) && (
              <p className="text-zinc-400">
                Paso actual del producto:{" "}
                <span className="font-mono text-zinc-200">{String(porQue?.nodo_actual)}</span>{" "}
                (estado: {String(porQue?.estado ?? "")})
              </p>
            )}
          </Tarjeta>
        );
      })()}

      {errorAccion && (
        <div className="rounded-lg border border-rose-900 bg-rose-950/40 p-3 text-sm text-rose-300">
          <strong>Error:</strong> {errorAccion}
        </div>
      )}

      {confirmando && (
        <Tarjeta className="border-amber-700 bg-amber-950/30">
          <h3 className="font-semibold text-amber-200">¿Confirmar Armar FASE 1?</h3>
          <p className="mt-1 text-sm text-zinc-300">
            Esta acción llamará a Claude Code para ejecutar las etapas de FASE 1: investigación
            de mercado, los 6 ángulos, copies, flujo LucidBot y la estructura de campaña.
            Modificará archivos en <code>PRODUCTOS/</code> y <code>Ads/</code>.
          </p>
          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={() => armar.mutate()}
              disabled={armar.isPending}
              className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
            >
              {armar.isPending ? "Iniciando…" : "Sí, confirmar y ejecutar"}
            </button>
            <button
              type="button"
              onClick={() => setConfirmando(false)}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
            >
              Cancelar
            </button>
          </div>
        </Tarjeta>
      )}

      {pasos.length === 0 ? (
        <Tarjeta>
          <p className="text-sm text-zinc-400">
            No hay pasos registrados todavía. Hacé clic en <strong>Armar FASE 1</strong> para
            iniciar la corrida.
          </p>
        </Tarjeta>
      ) : (
        <div className="space-y-3">
          {pasos.map((p) => {
            const tono = ESTADO_PASO_TONO[p.estado] ?? "neutro";
            return (
              <Tarjeta key={p.n} className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-zinc-400">
                      Paso {p.n}
                    </span>
                    <span className="font-medium text-zinc-100">
                      {p.etapas.join(" ∥ ")}
                    </span>
                  </div>
                  <Chip tono={tono}>{palabrasDeEstado(p.estado)}</Chip>
                </div>
                {p.miembros && p.miembros.length > 0 && (
                  <div className="mt-2 space-y-1.5 border-t border-zinc-800/80 pt-2 text-xs text-zinc-400">
                    {p.miembros.map((m) => (
                      <div
                        key={m.etapa}
                        className="flex flex-wrap items-center justify-between gap-2 rounded bg-zinc-950/40 px-2 py-1"
                      >
                        <span className="font-mono text-zinc-300">{m.etapa}</span>
                        <div className="flex items-center gap-3">
                          {m.duracion_s !== null && m.duracion_s !== undefined && (
                            <span>{m.duracion_s.toFixed(1)}s</span>
                          )}
                          {m.costo_equivalente_usd !== null &&
                            m.costo_equivalente_usd !== undefined && (
                              <span>${m.costo_equivalente_usd.toFixed(2)}</span>
                            )}
                          <Chip tono={ESTADO_PASO_TONO[m.estado] ?? "neutro"}>
                            {palabrasDeEstado(m.estado)}
                          </Chip>
                        </div>
                        {m.pregunta && (
                          <div className="w-full text-amber-300">
                            Pregunta pendiente: {m.pregunta}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Tarjeta>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ──────────────── Pestaña Investigación ──────────────── */
function TabInvestigacion({ corrida }: { corrida: CorridaF1 | undefined }) {
  const etapas = corrida?.etapas || [];
  const etapa1b = etapas.find((e) => e.etapa === "etapa-1b");
  const etapa1 = etapas.find((e) => e.etapa === "etapa-1");
  const etapa0 = etapas.find((e) => e.etapa === "etapa-0");

  return (
    <div className="space-y-6">
      <Tarjeta>
        <h3 className="text-lg font-semibold text-sky-400">
          Investigación de mercado y voz del cliente (etapa-1b)
        </h3>
        <p className="mb-4 text-xs text-zinc-500">
          Salida textual estructurada de etapa-1b: dolores, deseos, objeciones y testimonios de la
          competencia.
        </p>
        <TextoLegible texto={etapa1b?.texto} />
      </Tarjeta>

      <Tarjeta>
        <h3 className="text-lg font-semibold text-sky-400">
          Costeo y arquitectura de oferta (etapa-1)
        </h3>
        <p className="mb-4 text-xs text-zinc-500">
          Estructura de precios de Guatemala, CPA objetivo y break-even.
        </p>
        <TextoLegible texto={etapa1?.texto} />
      </Tarjeta>

      <Tarjeta>
        <h3 className="text-lg font-semibold text-sky-400">
          Transcripciones y ángulos iniciales (etapa-0)
        </h3>
        <p className="mb-4 text-xs text-zinc-500">
          Extracción de testimonios y ángulos desde los videos de la competencia.
        </p>
        <TextoLegible texto={etapa0?.texto} />
      </Tarjeta>
    </div>
  );
}

/* ──────────────── Pestaña Avatares y Ángulos ──────────────── */
function TabAngulos({
  campana,
  corrida,
}: {
  campana: CampanaF1 | undefined;
  corrida: CorridaF1 | undefined;
}) {
  const conjuntos = (campana?.plan_fuente as any)?.conjuntos || [];
  const etapa2 = (corrida?.etapas || []).find((e) => e.etapa === "etapa-2");

  if (conjuntos.length === 0) {
    return (
      <Tarjeta>
        <p className="text-sm text-zinc-400">
          No hay plan de ángulos cargado todavía. Se genera al armar FASE 1.
        </p>
      </Tarjeta>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-3 text-xs text-amber-300">
        <strong>Doctrina de embudo:</strong> Embudo: pendiente de decisión del operador (la doctrina dice tres cosas distintas).
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {conjuntos.map((c: any, index: number) => {
          const textoAngulo = extraerTextoAngulo(etapa2?.texto, c.n || index + 1);
          return (
            <Tarjeta key={c.angulo_key || index} className="space-y-3">
              <div className="border-b border-zinc-800 pb-2">
                <span className="font-mono text-xs text-sky-400">Ángulo {c.n || index + 1}</span>
                <h3 className="text-base font-semibold text-zinc-100">{c.angulo_titulo}</h3>
                <p className="font-mono text-xs text-zinc-500">{c.angulo_key}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded bg-zinc-950/60 p-2">
                  <span className="text-zinc-500">Avatar:</span>
                  <p className="font-medium text-zinc-200">
                    {c.avatar_genero} · {c.avatar_edad}
                  </p>
                </div>
                <div className="rounded bg-zinc-950/60 p-2">
                  <span className="text-zinc-500">Nivel de conciencia:</span>
                  <p className="font-medium text-zinc-200">{c.nivel_conciencia}</p>
                </div>
                <div className="rounded bg-zinc-950/60 p-2">
                  <span className="text-zinc-500">Formato:</span>
                  <p className="font-medium text-zinc-200">{c.formato}</p>
                </div>
                <div className="rounded bg-zinc-950/60 p-2">
                  <span className="text-zinc-500">Embudo:</span>
                  <p className="text-amber-400 font-medium">Pendiente de decisión</p>
                </div>
              </div>

              <div className="rounded border border-amber-800/40 bg-amber-950/30 px-2 py-1 text-[11px] text-amber-300">
                Embudo: pendiente de decisión del operador (la doctrina dice tres cosas distintas)
              </div>

              <div className="border-t border-zinc-800/80 pt-2">
                <span className="text-xs font-semibold text-zinc-400">
                  Ficha producida por etapa-2:
                </span>
                <div className="mt-1 max-h-60 overflow-y-auto rounded bg-zinc-950 p-2.5 text-xs">
                  {textoAngulo ? (
                    <TextoLegible texto={textoAngulo} />
                  ) : etapa2?.texto ? (
                    <div className="space-y-1">
                      <span className="text-zinc-500 italic">
                        (Mostrando salida general de etapa-2)
                      </span>
                      <TextoLegible texto={etapa2.texto} />
                    </div>
                  ) : (
                    <p className="italic text-zinc-500">Sin salida de etapa-2 todavía.</p>
                  )}
                </div>
              </div>
            </Tarjeta>
          );
        })}
      </div>
    </div>
  );
}

/* ──────────────── Pestaña Anuncios ──────────────── */
function TabAnuncios({
  campana,
}: {
  campana: CampanaF1 | undefined;
}) {
  const lanzadorConjuntos =
    (campana?.lanzador as any)?.plan?.conjuntos ||
    (campana?.plan_fuente as any)?.conjuntos ||
    [];
  const piezas = campana?.piezas || [];

  if (lanzadorConjuntos.length === 0) {
    return (
      <Tarjeta>
        <p className="text-sm text-zinc-400">
          No hay anuncios generados todavía. Se producen al completar las etapas de FASE 1.
        </p>
      </Tarjeta>
    );
  }

  return (
    <div className="space-y-6">
      {lanzadorConjuntos.map((cj: any, index: number) => {
        const pieza = piezas.find(
          (p) =>
            p.angulo_key === cj.angulo_key ||
            p.n === cj.n ||
            (cj.archivo_creativo && p.archivo === cj.archivo_creativo),
        );
        const textos = cj.copy?.textos || [];
        const titulos = cj.copy?.titulos || [];
        const descripcion = cj.copy?.descripcion;

        return (
          <Tarjeta key={cj.nombre || index} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2">
              <div>
                <h3 className="font-semibold text-zinc-100">{cj.nombre}</h3>
                <p className="text-xs text-zinc-400">
                  {cj.angulo_titulo} · Formato: {cj.formato} ·{" "}
                  {cj.lleva_precio ? "Lleva precio" : "Sin precio"}
                </p>
              </div>
              <Chip tono={cj.lleva_precio ? "bien" : "neutro"}>
                {cj.lleva_precio ? "Con precio" : "Sin precio"}
              </Chip>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              {/* Creativo / Imagen */}
              <div className="space-y-2">
                <span className="text-xs font-medium text-zinc-400">Creativo visual:</span>
                {pieza?.url ? (
                  <div className="flex flex-col items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950 p-2">
                    {pieza.archivo?.endsWith(".mp4") || pieza.archivo?.endsWith(".mov") ? (
                      <video
                        src={pieza.url}
                        controls
                        className="max-h-64 rounded object-contain"
                      />
                    ) : (
                      <img
                        src={pieza.url}
                        alt={pieza.archivo || "Creativo"}
                        className="max-h-64 rounded object-contain"
                      />
                    )}
                    <span className="mt-1 font-mono text-[11px] text-zinc-500">
                      {pieza.archivo}
                    </span>
                  </div>
                ) : (
                  <div className="flex h-48 flex-col items-center justify-center rounded-lg border border-amber-900/60 bg-amber-950/20 p-4 text-center">
                    <span className="text-sm font-semibold text-amber-300">
                      falta la pieza
                    </span>
                    <span className="mt-1 font-mono text-xs text-zinc-500">
                      {cj.archivo_creativo || "Archivo no encontrado"}
                    </span>
                    <p className="mt-2 text-xs text-zinc-400">
                      Podés subirla en la pestaña <strong>Checklist</strong>.
                    </p>
                  </div>
                )}

                {cj.prompt_imagen && (
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 text-xs">
                    <div className="flex items-center justify-between pb-1">
                      <span className="font-semibold text-zinc-400">Prompt de imagen:</span>
                      <Copiar texto={cj.prompt_imagen} />
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-zinc-300 whitespace-pre-wrap">
                      {cj.prompt_imagen}
                    </p>
                  </div>
                )}
              </div>

              {/* Textos y Copies */}
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-zinc-400">Textos principales:</span>
                    {textos.length > 0 && <Copiar texto={textos.join("\n\n---\n\n")} />}
                  </div>
                  {textos.map((t: string, tIdx: number) => (
                    <div
                      key={tIdx}
                      className="mt-1 rounded bg-zinc-950 p-2.5 text-xs text-zinc-200 whitespace-pre-wrap"
                    >
                      {t}
                    </div>
                  ))}
                </div>

                {titulos.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-zinc-400">Títulos:</span>
                    <ul className="mt-1 space-y-1">
                      {titulos.map((tit: string, titIdx: number) => (
                        <li
                          key={titIdx}
                          className="flex items-center justify-between rounded bg-zinc-950 px-2 py-1 text-xs text-zinc-200"
                        >
                          <span>{tit}</span>
                          <Copiar texto={tit} />
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {descripcion && (
                  <div>
                    <span className="text-xs font-medium text-zinc-400">Descripción:</span>
                    <div className="mt-1 flex items-center justify-between rounded bg-zinc-950 px-2 py-1 text-xs text-zinc-200">
                      <span>{descripcion}</span>
                      <Copiar texto={descripcion} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Tarjeta>
        );
      })}
    </div>
  );
}

/* ──────────────── Pestaña Flujo LucidBot ──────────────── */
function TabFlujoBot({
  flujoBot,
  onVerSalidas,
}: {
  flujoBot: FlujoBot | undefined;
  onVerSalidas: () => void;
}) {
  const secciones = flujoBot?.secciones || [];

  if (secciones.length === 0) {
    return (
      <Tarjeta>
        <p className="text-sm text-zinc-400">
          No hay flujo LucidBot generado todavía.
        </p>
      </Tarjeta>
    );
  }

  return (
    <div className="space-y-6">
      {(!flujoBot?.ok ||
        (flujoBot?.faltan && flujoBot.faltan.length > 0) ||
        (flujoBot?.prohibiciones && flujoBot.prohibiciones.length > 0)) && (
        <Tarjeta className="border-amber-800/60 bg-amber-950/20 space-y-2">
          <h4 className="font-semibold text-amber-200">
            {flujoBot?.ok ? "Avisos del flujo LucidBot" : "Flujo incompleto — faltan datos"}
          </h4>
          {flujoBot?.faltan && flujoBot.faltan.length > 0 && (
            <div className="space-y-1 text-xs text-amber-300">
              <span className="font-medium text-amber-100">Faltan variables o bloques:</span>
              <ul className="list-disc pl-5 space-y-0.5">
                {flujoBot.faltan.map((f: any, idx: number) => (
                  <li key={idx}>
                    {typeof f === "string"
                      ? f
                      : `${f.variable || f.dato || JSON.stringify(f)} (dueño: ${f.dueno || "etapa-5"})`}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {flujoBot?.prohibiciones && flujoBot.prohibiciones.length > 0 && (
            <div className="space-y-1 text-xs text-rose-300">
              <span className="font-medium text-rose-200">Prohibiciones:</span>
              <ul className="list-disc pl-5 space-y-0.5">
                {flujoBot.prohibiciones.map((p: string, idx: number) => (
                  <li key={idx}>⚠️ {p}</li>
                ))}
              </ul>
            </div>
          )}
        </Tarjeta>
      )}

      {secciones.map((sec, secIdx) => (
        <div key={secIdx} className="space-y-3">
          <h3 className="text-base font-semibold text-sky-400 border-b border-zinc-800 pb-1">
            {sec.titulo}
          </h3>

          {sec.instrucciones && sec.instrucciones.length > 0 && (
            <div className="rounded bg-zinc-950/60 p-2.5 text-xs text-zinc-500 space-y-0.5">
              {sec.instrucciones.map((inst, iIdx) => (
                <p key={iIdx}>&gt;&gt; {inst}</p>
              ))}
            </div>
          )}

          <div className="space-y-4">
            {sec.bloques.map((b, bIdx) => (
              <Tarjeta key={bIdx} className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="font-medium text-zinc-200">{b.titulo}</h4>
                  <Copiar texto={b.pegar} label="Copiar texto a pegar" />
                </div>

                {/* Lo que se pega: instrucciones NO van acá */}
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                    Texto para pegar en LucidBot:
                  </span>
                  <pre className="mt-1 max-h-56 overflow-y-auto whitespace-pre-wrap rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-200 border border-zinc-800">
                    {b.pegar || <span className="italic text-zinc-600">(Bloque vacío)</span>}
                  </pre>
                </div>

                {/* Bloques pendientes */}
                {b.pendientes && b.pendientes.length > 0 && (
                  <div className="flex items-center justify-between rounded border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-xs text-amber-300">
                    <span>
                      <strong>lo escribe etapa-5:</strong> {b.pendientes.join(", ")}
                    </span>
                    <button
                      type="button"
                      onClick={onVerSalidas}
                      className="underline hover:text-amber-200"
                    >
                      Ver salida de etapa-5 →
                    </button>
                  </div>
                )}

                {/* Instrucciones >> completamente aparte, en gris */}
                {b.instrucciones && b.instrucciones.length > 0 && (
                  <div className="rounded border border-zinc-800/80 bg-zinc-900/40 p-2 text-xs text-zinc-500">
                    <span className="block font-semibold text-zinc-400">
                      Instrucciones operativas (NO se pegan en LucidBot):
                    </span>
                    <ul className="mt-1 space-y-0.5">
                      {b.instrucciones.map((inst, instIdx) => (
                        <li key={instIdx}>&gt;&gt; {inst}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Tarjeta>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ──────────────── Pestaña Estructura de Campaña ──────────────── */
function TabCampana({
  campana,
}: {
  campana: CampanaF1 | undefined;
}) {
  const plan: any = (campana?.lanzador as any)?.plan || campana?.plan_fuente;
  if (!plan) {
    return (
      <Tarjeta>
        <p className="text-sm text-zinc-400">
          No hay estructura de campaña generada todavía. Se produce al correr FASE 1.
        </p>
      </Tarjeta>
    );
  }

  const campanas = plan.campanas || [];
  const conjuntos = plan.conjuntos || [];
  const lanzamiento = plan.lanzamiento;
  const presupuesto = plan.presupuesto;
  const bloqueantes = plan.bloqueantes || [];
  const faltantes = plan.faltantes || [];

  return (
    <div className="space-y-6">
      <Tarjeta className="space-y-3 border-sky-800/40 bg-sky-950/20">
        <h3 className="text-base font-semibold text-zinc-100">Campaña de lanzamiento</h3>
        {campanas.map((c: any, idx: number) => (
          <div key={idx} className="grid grid-cols-1 gap-2 text-xs md:grid-cols-3">
            <div className="rounded bg-zinc-950 p-2.5">
              <span className="text-zinc-500">Nombre en Meta:</span>
              <p className="font-mono font-medium text-zinc-200">{c.nombre}</p>
            </div>
            <div className="rounded bg-zinc-950 p-2.5">
              <span className="text-zinc-500">Objetivo:</span>
              <p className="font-medium text-zinc-200">{c.objetivo}</p>
            </div>
            <div className="rounded bg-zinc-950 p-2.5">
              <span className="text-zinc-500">Lanzamiento programado:</span>
              <p className="font-medium text-amber-300">
                {lanzamiento?.fecha || lanzamiento?.legible || "Día siguiente"} · 4:00 AM
              </p>
            </div>
          </div>
        ))}
        {presupuesto && (
          <div className="mt-2 text-xs text-zinc-400">
            Presupuesto: ${presupuesto.total_dia_usd || 17.94} USD/día (
            {presupuesto.por_que || "protegido por conjunto"})
          </div>
        )}
      </Tarjeta>

      {/* Bloqueantes de campaña */}
      {bloqueantes.length > 0 && (
        <Tarjeta className="border-rose-900/60 bg-rose-950/20 space-y-2">
          <h4 className="font-semibold text-rose-300">
            Bloqueos de lanzamiento ({bloqueantes.length})
          </h4>
          <ul className="list-disc pl-5 text-xs text-rose-200 space-y-1">
            {bloqueantes.map((b: any, idx: number) => (
              <li key={idx}>
                {typeof b === "string"
                  ? b
                  : `${b.falta || b.dato || JSON.stringify(b)} (lo produce: ${b.lo_produce || b.dueno || "etapa"})`}
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      {/* Faltantes de campaña */}
      {faltantes.length > 0 && (
        <Tarjeta className="border-amber-900/60 bg-amber-950/20 space-y-2">
          <h4 className="font-semibold text-amber-300">
            Faltantes de campaña ({faltantes.length})
          </h4>
          <ul className="list-disc pl-5 text-xs text-amber-200 space-y-1">
            {faltantes.map((f: any, idx: number) => (
              <li key={idx}>
                {typeof f === "string" ? f : `${f.falta || f.dato || JSON.stringify(f)}`}
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      <div>
        <h4 className="text-sm font-semibold text-zinc-200 mb-3">
          Conjuntos de anuncios ({conjuntos.length})
        </h4>
        <div className="space-y-3">
          {conjuntos.map((cj: any, idx: number) => (
            <Tarjeta key={idx} className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="font-mono text-xs text-sky-400">#{cj.n || idx + 1}</span>{" "}
                  <strong className="text-sm text-zinc-100">{cj.nombre}</strong>
                </div>
                <div className="flex items-center gap-2">
                  <Chip tono="dato">${cj.presupuesto_usd || "2.99"} USD/día</Chip>
                  <Chip tono="neutro">{cj.banda_edad || "Amplio"}</Chip>
                </div>
              </div>
              <p className="text-xs text-zinc-400">
                Banda: {cj.banda_edad} ({cj.banda_por_que || "según avatar"})
              </p>
              {cj.anuncios && cj.anuncios.length > 0 && (
                <div className="mt-2 space-y-1 text-xs">
                  <span className="text-zinc-500">Anuncios:</span>
                  <ul className="space-y-0.5 font-mono text-[11px] text-zinc-300">
                    {cj.anuncios.map((ad: any, aIdx: number) => (
                      <li key={aIdx} className="rounded bg-zinc-950 px-2 py-0.5">
                        {ad.nombre || ad.letra}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Tarjeta>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ──────────────── Pestaña Checklist ──────────────── */
function TabChecklist({
  clave,
  checklist,
  onRecargar,
}: {
  clave: string;
  checklist: ChecklistF1 | undefined;
  onRecargar: () => void;
}) {
  const [valoresTexto, setValoresTexto] = useState<Record<string, string>>({});
  const [archivosSeleccionados, setArchivosSeleccionados] = useState<Record<string, File>>({});
  const [archivosTranscripcion, setArchivosTranscripcion] = useState<File[]>([]);
  const [tituloTranscripcion, setTituloTranscripcion] = useState<string>("");
  const [cargando, setCargando] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);

  // Obtener cuentas de la API (_DIM_CUENTAS)
  const cuentasQuery = useQuery({
    queryKey: ["cuentas"],
    queryFn: () => api.cuentas(),
  });
  const cuentas = cuentasQuery.data || [];

  const faltan = checklist?.faltan || [];
  const bloqueantes = checklist?.paquete?.bloqueantes || [];

  const handleCargar = async (
    accionId: string,
    datos: Record<string, unknown>,
    archivo?: File,
    claveCarga?: string,
  ) => {
    setCargando(claveCarga || accionId);
    setMensaje(null);
    try {
      await api.cargarDato(clave, accionId, datos, archivo);
      setMensaje({ tipo: "ok", texto: "Dato guardado con éxito ✓" });
      onRecargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err instanceof Error ? err.message : String(err) });
    } finally {
      setCargando(null);
    }
  };

  return (
    <div className="space-y-6">
      {mensaje && (
        <div
          className={cn(
            "rounded-lg p-3 text-sm",
            mensaje.tipo === "ok"
              ? "border border-emerald-900 bg-emerald-950/40 text-emerald-300"
              : "border border-rose-900 bg-rose-950/40 text-rose-300",
          )}
        >
          {mensaje.texto}
        </div>
      )}

      {/* Bloqueantes del paquete de publicación */}
      {bloqueantes.length > 0 && (
        <Tarjeta className="space-y-4 border-amber-800/60 bg-amber-950/20">
          <h3 className="font-semibold text-amber-200">
            Bloqueos del paquete de publicación ({bloqueantes.length})
          </h3>
          <div className="space-y-4">
            {bloqueantes.map((b, idx) => {
              // Caso 1: Clave page_id
              if (b.clave === "page_id" || b.escritor === "producto.cargar_page_id") {
                const valor = valoresTexto["page_id"] ?? "";
                return (
                  <div key={idx} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-zinc-100">{b.falta}</span>
                      <Chip tono="alto">Falta Page ID</Chip>
                    </div>
                    <div className="flex gap-2 items-center">
                      <input
                        type="text"
                        placeholder="Ej: 1279576438561754"
                        value={valor}
                        onChange={(e) =>
                          setValoresTexto((prev) => ({ ...prev, page_id: e.target.value }))
                        }
                        className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-sky-500"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          handleCargar(
                            "producto.cargar_page_id",
                            { page_id: valor.trim() },
                            undefined,
                            "page_id",
                          )
                        }
                        disabled={!valor.trim() || cargando === "page_id"}
                        className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
                      >
                        {cargando === "page_id" ? "Guardando…" : "Guardar Page ID"}
                      </button>
                    </div>
                  </div>
                );
              }

              // Caso 2: Clave cuenta
              if (b.clave === "cuenta" || b.escritor === "producto.cargar_cuenta") {
                const cuentaPorDefecto = cuentas.length > 0 ? cuentas[0].cuenta_alias : "GTR 7";
                const valor = valoresTexto["cuenta"] ?? cuentaPorDefecto;
                return (
                  <div key={idx} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-zinc-100">{b.falta}</span>
                      <Chip tono="alto">Falta Cuenta</Chip>
                    </div>
                    <div className="flex gap-2 items-center">
                      <select
                        value={valor}
                        onChange={(e) =>
                          setValoresTexto((prev) => ({ ...prev, cuenta: e.target.value }))
                        }
                        className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:border-sky-500"
                      >
                        {cuentas.length > 0 ? (
                          cuentas.map((c) => (
                            <option key={c.cuenta_alias} value={c.cuenta_alias}>
                              {c.cuenta_alias} ({c.sube_media_local === "SI" ? "Media local MCP" : "Biblioteca"}) — {c.moneda}
                            </option>
                          ))
                        ) : (
                          <>
                            <option value="GTR 7">GTR 7 (Media local MCP)</option>
                            <option value="GTR 0">GTR 0</option>
                            <option value="GTR 1">GTR 1</option>
                            <option value="GTR 3">GTR 3</option>
                            <option value="GTR 13">GTR 13</option>
                          </>
                        )}
                      </select>
                      <button
                        type="button"
                        onClick={() =>
                          handleCargar(
                            "producto.cargar_cuenta",
                            { cuenta: valor },
                            undefined,
                            "cuenta",
                          )
                        }
                        disabled={cargando === "cuenta"}
                        className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
                      >
                        {cargando === "cuenta" ? "Guardando…" : "Asignar cuenta"}
                      </button>
                    </div>
                  </div>
                );
              }

              // Caso 3: Clave piezas (un campo por archivo en b.archivos)
              if (b.clave === "piezas" || b.escritor === "producto.cargar_pieza") {
                const listaArchivos = b.archivos && b.archivos.length > 0 ? b.archivos : ["pieza_1.png"];
                return (
                  <div key={idx} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-zinc-100">{b.falta}</span>
                      <Chip tono="alto">Faltan {listaArchivos.length} pieza(s)</Chip>
                    </div>
                    <div className="space-y-2">
                      {listaArchivos.map((arch) => {
                        const file = archivosSeleccionados[arch];
                        const keyCarga = `pieza_${arch}`;
                        return (
                          <div
                            key={arch}
                            className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-800 bg-zinc-900/60 p-2"
                          >
                            <span className="font-mono text-xs text-zinc-300">{arch}</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="file"
                                aria-label={`Subir archivo para ${arch}`}
                                accept=".png,.jpg,.jpeg,.mp4,.mov"
                                onChange={(e) => {
                                  if (e.target.files?.[0]) {
                                    const f = e.target.files[0];
                                    setArchivosSeleccionados((prev) => ({ ...prev, [arch]: f }));
                                  }
                                }}
                                className="text-xs text-zinc-400 file:mr-2 file:rounded file:border-0 file:bg-zinc-800 file:px-2 file:py-1 file:text-xs file:text-zinc-200"
                              />
                              <button
                                type="button"
                                onClick={() =>
                                  handleCargar("producto.cargar_pieza", { archivo: arch }, file, keyCarga)
                                }
                                disabled={!file || cargando === keyCarga}
                                className="rounded bg-sky-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
                              >
                                {cargando === keyCarga ? "Subiendo…" : "Subir pieza"}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              }

              // Caso 4: Sin escritor conocido
              return (
                <div key={idx} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <span className="text-sm font-medium text-zinc-200">{b.falta}</span>
                  <p className="text-xs text-zinc-500">lo produce: {b.lo_produce || "etapa"}</p>
                </div>
              );
            })}
          </div>
        </Tarjeta>
      )}

      {/* Preflight */}
      <Tarjeta className="border-zinc-800 space-y-2">
        <h3 className="font-semibold text-zinc-200">Verificaciones de publicación (Preflight)</h3>
        <p className="text-xs text-zinc-400">
          La vinculación con WhatsApp de la FanPage y los permisos de cuenta en Meta:{" "}
          <strong className="text-zinc-300">se verifica al publicar (contra Meta)</strong>.
        </p>
        {(() => {
          const preflightList = Array.isArray((checklist?.paquete as any)?.preflight)
            ? ((checklist?.paquete as any).preflight as any[])
            : [];
          if (preflightList.length === 0) return null;
          return (
            <ul className="mt-2 space-y-1 text-xs text-zinc-400 border-t border-zinc-800/80 pt-2">
              {preflightList.map((pf: any, idx: number) => (
                <li key={idx} className="flex items-center justify-between">
                  <span>{String(pf.verificar || JSON.stringify(pf))}</span>
                  <span className="text-zinc-500 italic">se verifica al publicar (contra Meta)</span>
                </li>
              ))}
            </ul>
          );
        })()}
      </Tarjeta>

      {/* Faltantes de flujo.py */}
      <div>
        <h3 className="text-base font-semibold text-zinc-100 mb-3">
          Requisitos del flujo ({faltan.length})
        </h3>
        {faltan.length === 0 ? (
          <Tarjeta>
            <p className="text-sm text-emerald-400">✓ Todos los requisitos del paso están cumplidos.</p>
          </Tarjeta>
        ) : (
          <div className="space-y-3">
            {faltan.map((item, idx) => {
              const tieneTranscripcion =
                item.escritores?.includes("producto.cargar_transcripcion") ||
                item.dato.toLowerCase().includes("transcripci");
              const tieneCosto =
                item.escritores?.includes("producto.cambiar_costo") ||
                item.dato.toLowerCase().includes("costo");

              return (
                <Tarjeta key={idx} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-zinc-100">{item.dato}</span>
                    <Chip tono={item.ok ? "bien" : "alto"}>{item.ok ? "OK" : "Falta"}</Chip>
                  </div>
                  {item.observado && (
                    <p className="text-xs text-zinc-400">Observado: {item.observado}</p>
                  )}

                  {tieneTranscripcion && (
                    <div className="mt-2 space-y-2 rounded bg-zinc-950 p-3 text-xs border border-zinc-800">
                      <span className="font-semibold text-zinc-300">
                        Subir transcripción TXT (uno o varios archivos, con título opcional):
                      </span>
                      <div className="flex flex-wrap items-center gap-2">
                        <input
                          type="file"
                          multiple
                          accept=".txt"
                          aria-label="Archivo de transcripción TXT"
                          onChange={(e) => {
                            if (e.target.files) {
                              setArchivosTranscripcion(Array.from(e.target.files));
                            }
                          }}
                          className="text-xs text-zinc-400 file:mr-2 file:rounded file:border-0 file:bg-zinc-800 file:px-2 file:py-1 file:text-xs file:text-zinc-200"
                        />
                        <input
                          type="text"
                          placeholder="Título opcional"
                          value={tituloTranscripcion}
                          onChange={(e) => setTituloTranscripcion(e.target.value)}
                          className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={async () => {
                            if (archivosTranscripcion.length === 0) return;
                            setCargando("transcripcion");
                            setMensaje(null);
                            try {
                              for (const arch of archivosTranscripcion) {
                                const datos = tituloTranscripcion.trim()
                                  ? { titulo: tituloTranscripcion.trim() }
                                  : {};
                                await api.cargarDato(
                                  clave,
                                  "producto.cargar_transcripcion",
                                  datos,
                                  arch,
                                );
                              }
                              setMensaje({
                                tipo: "ok",
                                texto: `Se subieron ${archivosTranscripcion.length} transcripción(es) ✓`,
                              });
                              setArchivosTranscripcion([]);
                              setTituloTranscripcion("");
                              onRecargar();
                            } catch (err) {
                              setMensaje({
                                tipo: "error",
                                texto: err instanceof Error ? err.message : String(err),
                              });
                            } finally {
                              setCargando(null);
                            }
                          }}
                          disabled={
                            archivosTranscripcion.length === 0 || cargando === "transcripcion"
                          }
                          className="rounded bg-sky-600 px-3 py-1 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
                        >
                          {cargando === "transcripcion"
                            ? "Subiendo…"
                            : `Subir TXT (${archivosTranscripcion.length || 0})`}
                        </button>
                      </div>
                      {archivosTranscripcion.length > 0 && (
                        <p className="text-[11px] text-zinc-500">
                          Seleccionados: {archivosTranscripcion.map((f) => f.name).join(", ")}
                        </p>
                      )}
                    </div>
                  )}

                  {tieneCosto && (
                    <div className="mt-2 flex items-center gap-2 rounded bg-zinc-950 p-2 text-xs">
                      <input
                        type="number"
                        placeholder="Costo en Q"
                        value={valoresTexto["costo"] ?? ""}
                        onChange={(e) =>
                          setValoresTexto((prev) => ({ ...prev, costo: e.target.value }))
                        }
                        className="w-32 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          handleCargar(
                            "producto.cambiar_costo",
                            { costo: valoresTexto["costo"] },
                            undefined,
                            "costo",
                          )
                        }
                        disabled={!valoresTexto["costo"] || cargando === "costo"}
                        className="rounded bg-sky-600 px-3 py-1 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
                      >
                        {cargando === "costo" ? "Guardando…" : "Guardar costo"}
                      </button>
                    </div>
                  )}

                  {!tieneTranscripcion && !tieneCosto && (
                    <p className="text-xs text-zinc-500">
                      lo produce: {item.dueno || "etapa"}
                    </p>
                  )}
                </Tarjeta>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/* ──────────────── PANTALLA PRINCIPAL FASE 1 ──────────────── */
export function Fase1() {
  // strict: false (no un "from" fijo) porque ProductoDetalle (P4/T3) puede montar esta pantalla
  // como la pestaña "Fase 1" mientras la URL activa es la ficha a secas (`/producto/$clave`),
  // no necesariamente `/producto/$clave/fase1` — igual que ya hacían Fase2 y Fase3.
  const { clave } = useParams({ strict: false }) as { clave: string };
  const navigate = useNavigate();
  const [tab, setTab] = useState<TabId>("avance");

  const corrida = useQuery({
    queryKey: ["fase1-corrida", clave],
    queryFn: () => api.fase1Corrida(clave),
  });
  const campana = useQuery({
    queryKey: ["fase1-campana", clave],
    queryFn: () => api.fase1Campana(clave),
  });
  const flujoBot = useQuery({
    queryKey: ["flujo-bot", clave],
    queryFn: () => api.flujoBot(clave),
  });
  const checklist = useQuery({
    queryKey: ["checklist", clave],
    queryFn: () => api.checklist(clave),
  });

  if (corrida.isLoading) return <Cargando que={`FASE 1 de ${clave}`} />;
  if (corrida.error) return <Problema error={corrida.error} />;

  const faltanCount =
    (checklist.data?.faltan?.filter((f) => !f.ok).length || 0) +
    (checklist.data?.paquete?.bloqueantes?.length || 0);

  const tabs: { id: TabId; label: string; badge?: number }[] = [
    { id: "avance", label: "Avance" },
    { id: "investigacion", label: "Investigación" },
    { id: "angulos", label: "Avatares y ángulos" },
    { id: "anuncios", label: "Anuncios" },
    { id: "flujo-bot", label: "Flujo LucidBot" },
    { id: "campana", label: "Estructura de campaña" },
    { id: "checklist", label: "Checklist", badge: faltanCount },
  ];

  return (
    <div className="space-y-6">
      {/* Sin breadcrumb propio ni "Ver recorrido en el grafo": ProductoDetalle (P4/T3) ya los da
          — esta pantalla vive dentro de su pestaña "Fase 1", nunca sola. */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">
          FASE 1 · {clave}
        </h1>
        <p className="text-sm text-zinc-400">
          6 ángulos × 1 concepto fijo · Investigación, Anuncios, Bot y Lanzador
        </p>
      </div>

      {/* Selector de pestañas */}
      <div className="flex flex-wrap gap-1 border-b border-zinc-800 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
              tab === t.id
                ? "bg-sky-600 text-white"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100",
            )}
          >
            {t.label}
            {t.badge !== undefined && t.badge > 0 && (
              <span className="rounded-full bg-amber-600 px-1.5 py-0.2 text-[10px] font-bold text-white">
                {t.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Contenido de la pestaña activa */}
      {tab === "avance" && (
        <TabAvance
          clave={clave}
          corrida={corrida.data}
          onArmarExito={(jobId) => navigate({ to: `/trabajos/${jobId}` as any })}
        />
      )}
      {tab === "investigacion" && <TabInvestigacion corrida={corrida.data} />}
      {tab === "angulos" && (
        <TabAngulos campana={campana.data} corrida={corrida.data} />
      )}
      {tab === "anuncios" && <TabAnuncios campana={campana.data} />}
      {tab === "flujo-bot" && (
        <TabFlujoBot
          flujoBot={flujoBot.data}
          onVerSalidas={() => setTab("investigacion")}
        />
      )}
      {tab === "campana" && <TabCampana campana={campana.data} />}
      {tab === "checklist" && (
        <TabChecklist
          clave={clave}
          checklist={checklist.data}
          onRecargar={() => {
            checklist.refetch();
            campana.refetch();
            corrida.refetch();
          }}
        />
      )}
    </div>
  );
}
