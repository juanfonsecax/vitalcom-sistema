/**
 * Fase2.tsx — Pantalla de FASE 2: Testeo de Conceptos y Ciclo de Fatiga.
 *
 * Muestra:
 *  1. Ganador #1 con sus métricas.
 *  2. Carriles de ganadores secundarios (#2 y #3) escalonados (~3 días).
 *  3. Galería de 10 conceptos con blueprints de origen, prompts listos para copiar y subida manual.
 *  4. Módulo de fatiga creativa (RENOVAR) y botón «Nuevos ángulos para este producto» (retorno a F1 excluyendo probados).
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api, type ConceptoFase2 } from "../api/cliente";
import { Cargando, Chip, Info, Problema, Tarjeta, type Tono } from "../componentes/ui";

const TONOS_ESTADO: Record<string, Tono> = {
  GENERADO: "bien",
  PUBLICADO: "bien",
  PENDIENTE_GENERAR: "aviso",
};

export function Fase2({ clave: claveProp }: { clave?: string }) {
  const params = useParams({ strict: false }) as { clave?: string };
  const clave = claveProp || params.clave || "";
  const queryClient = useQueryClient();
  const consulta = useQuery({
    queryKey: ["fase2", clave],
    queryFn: () => api.fase2(clave),
  });

  const [copiadoId, setCopiadoId] = useState<string | null>(null);
  const [subiendoArchivo, setSubiendoArchivo] = useState<string | null>(null);
  const [mensajeSubida, setMensajeSubida] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);
  const [modalReingreso, setModalReingreso] = useState(false);
  const [motivoReingreso, setMotivoReingreso] = useState("Ángulo agotado / fatiga de ventas");

  const mutacionReingreso = useMutation({
    mutationFn: (motivo: string) => api.reingresoF1(clave, motivo),
    onSuccess: () => {
      setModalReingreso(false);
      queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
      queryClient.invalidateQueries({ queryKey: ["producto", clave] });
    },
  });

  if (consulta.isLoading) return <Cargando que="el tablero de FASE 2" />;
  if (consulta.error) return <Problema error={consulta.error} />;

  const d = consulta.data;
  if (!d) return null;

  const copiarPrompt = (id: string, texto: string) => {
    navigator.clipboard.writeText(texto).then(() => {
      setCopiadoId(id);
      setTimeout(() => setCopiadoId(null), 2500);
    });
  };

  const subirImagen = async (concepto: ConceptoFase2, archivo: File) => {
    setSubiendoArchivo(concepto.creativo_id);
    setMensajeSubida(null);
    try {
      await api.cargarDato(
        clave,
        "producto.cargar_pieza",
        {
          producto_key: clave,
          archivo: concepto.archivo,
          origen: archivo.name,
        },
        archivo,
      );
      setMensajeSubida({ tipo: "ok", texto: `Pieza ${concepto.archivo} subida correctamente.` });
      queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al subir la pieza";
      setMensajeSubida({ tipo: "error", texto: msg });
    } finally {
      setSubiendoArchivo(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Encabezado — sin "Volver a la ficha": ProductoDetalle (P4/T3) ya da esa vuelta, esta
          pantalla vive dentro de su pestaña "Fase 2". */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            FASE 2 · Testeo de Conceptos ({clave})
          </h1>
          <p className="text-sm text-zinc-400">
            Estructura 1-1-5 + 1-1-5 + 1-2-5 · 10 conceptos con ángulo y copy fijos · <Info termino="fase_2" />
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Chip tono={d.conceptos_generados >= 10 ? "bien" : "aviso"}>
            {d.conceptos_generados} de 10 conceptos listos
          </Chip>
          <Link
            to="/producto/$clave/fase3"
            params={{ clave }}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            Ver FASE 3 (Escalado) →
          </Link>
        </div>
      </div>

      {/* Banner de Reingreso Activo (si ya volvió a F1) */}
      {d.reingreso_activo && (
        <div className="rounded-xl border border-sky-800/80 bg-sky-950/40 p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-semibold text-sky-200">
                🔄 Reingreso a FASE 1 activo desde el {d.reingreso_activo.fecha}
              </h3>
              <p className="mt-1 text-xs text-sky-300">
                {d.reingreso_activo.motivo}
              </p>
              <div className="mt-2 text-xs text-zinc-400">
                Ángulos excluidos para no repetir:{" "}
                <span className="font-mono text-zinc-300">
                  {d.reingreso_activo.angulos_excluidos.join(", ") || "ninguno"}
                </span>
              </div>
            </div>
            <Link
              to="/producto/$clave/fase1"
              params={{ clave }}
              className="rounded-md border border-sky-700 bg-sky-900/60 px-2.5 py-1 text-xs font-medium text-sky-200 hover:bg-sky-800"
            >
              Ir a FASE 1 →
            </Link>
          </div>
        </div>
      )}

      {/* Ángulo Ganador Principal */}
      <Tarjeta className="border-emerald-800/50 bg-emerald-950/20">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
              Ángulo Ganador Coronado por Ventas
            </span>
            <h2 className="text-lg font-bold text-zinc-100">{d.angulo_ganador}</h2>
            <p className="mt-1 text-xs text-zinc-400">
              Este ángulo se mantiene fijo para todos los conceptos de esta fase.
            </p>
          </div>
          <div className="text-right">
            <span className="text-xs text-zinc-400">Paso actual</span>
            <div className="font-mono text-sm font-semibold text-emerald-300">
              {d.nodo_actual || "Al día"}
            </div>
          </div>
        </div>
      </Tarjeta>

      {/* Carriles Escalonados para Ganadores Secundarios */}
      {d.carriles_secundarios.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-200">
              Carriles Escalonados · Ganadores Secundarios (#2 y #3)
            </h3>
            <span className="text-xs text-zinc-500">
              Cadencia: ~3 días de separación (CALENDARIO_ESCALADO §1)
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {d.carriles_secundarios.map((c) => (
              <Tarjeta key={c.angulo_key} className="border-zinc-800 bg-zinc-900/40 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-zinc-200">{c.angulo_key}</span>
                  <Chip tono="aviso">{c.estado_motor}</Chip>
                </div>
                <p className="mt-2 text-xs text-zinc-400">{c.accion || "Ganador en lista para escalonar"}</p>
                <div className="mt-3 text-right text-xs text-amber-400">
                  ⏱ {c.fecha_estimada}
                </div>
              </Tarjeta>
            ))}
          </div>
        </div>
      )}

      {/* Alertas de Fatiga y Botón de Retorno a F1 */}
      <Tarjeta className="border-amber-800/40 bg-amber-950/20 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-amber-200">
              Ciclo de Fatiga & Renovación
            </h3>
            <p className="mt-1 text-xs text-zinc-300">
              Si el ángulo ganador se cansa o las órdenes del motor emiten <span className="font-mono text-amber-300">RENOVAR</span>, rotamos creativos en F2. Si el ángulo ya no rinde, volvemos a FASE 1 con ángulos frescos.
            </p>
          </div>
          <button
            onClick={() => setModalReingreso(true)}
            className="rounded-lg border border-amber-700 bg-amber-900/60 px-3 py-1.5 text-xs font-semibold text-amber-100 hover:bg-amber-800"
          >
            Nuevos ángulos para este producto →
          </button>
        </div>

        {/* Modal / Diálogo de Confirmación de Reingreso */}
        {modalReingreso && (
          <div className="mt-4 rounded-lg border border-zinc-700 bg-zinc-900 p-4 shadow-xl">
            <h4 className="text-sm font-bold text-zinc-100">
              ¿Confirmar retorno a FASE 1 para {clave}?
            </h4>
            <p className="mt-1 text-xs text-zinc-300">
              El producto reingresará a FASE 1 para investigar y testear una nueva tanda de 6 ángulos. Se excluirán automáticamente los ángulos que ya corrieron:
            </p>
            <div className="mt-2 rounded bg-zinc-950 p-2 font-mono text-xs text-zinc-400">
              {d.fatiga.angulos_probados.join(", ") || "Ningún ángulo previo registrado"}
            </div>
            <div className="mt-3">
              <label className="text-xs text-zinc-400">Motivo del reingreso:</label>
              <input
                type="text"
                value={motivoReingreso}
                onChange={(e) => setMotivoReingreso(e.target.value)}
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200"
              />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setModalReingreso(false)}
                className="rounded px-3 py-1 text-xs text-zinc-400 hover:text-zinc-200"
              >
                Cancelar
              </button>
              <button
                disabled={mutacionReingreso.isPending}
                onClick={() => mutacionReingreso.mutate(motivoReingreso)}
                className="rounded bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-500"
              >
                {mutacionReingreso.isPending ? "Registrando..." : "Sí, volver a F1"}
              </button>
            </div>
          </div>
        )}
      </Tarjeta>

      {/* Notificación de Subida */}
      {mensajeSubida && (
        <div
          className={`rounded-lg p-3 text-xs ${
            mensajeSubida.tipo === "ok"
              ? "border border-emerald-800 bg-emerald-950/60 text-emerald-200"
              : "border border-rose-800 bg-rose-950/60 text-rose-200"
          }`}
        >
          {mensajeSubida.texto}
        </div>
      )}

      {/* Galería de los 10 Conceptos */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-bold text-zinc-100">
            Galería de Conceptos ({d.conceptos.length} de 10)
          </h2>
          <span className="text-xs text-zinc-400">
            Copiá el prompt, generá en tu IA favorita (ChatGPT web, Midjourney) y subí la pieza terminada.
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {d.conceptos.map((c, i) => (
            <Tarjeta key={c.creativo_id || i} className="space-y-3 border-zinc-800 bg-zinc-900/50">
              <div className="flex items-start justify-between gap-2 border-b border-zinc-800 pb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-sky-400">{c.canonico_id || `C${i + 1}`}</span>
                    <Chip tono={c.rol_embudo === "TOFU" ? "aviso" : c.rol_embudo === "BOFU" ? "bien" : "dato"}>
                      {c.rol_embudo}
                    </Chip>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-200">{c.blueprint_nombre}</h3>
                </div>
                <Chip tono={TONOS_ESTADO[c.estado] || "neutro"}>{c.estado}</Chip>
              </div>

              {c.dispositivo && (
                <p className="text-xs text-zinc-400 italic">
                  «{c.dispositivo}»
                </p>
              )}

              {/* Caja de Prompt Resuelto */}
              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-2.5">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Prompt Multimodal Listo
                  </span>
                  <button
                    onClick={() => copiarPrompt(c.creativo_id, c.prompt)}
                    className="rounded border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[11px] font-medium text-zinc-200 hover:bg-zinc-700"
                  >
                    {copiadoId === c.creativo_id ? "✓ Copiado" : "Copiar Prompt"}
                  </button>
                </div>
                <p className="line-clamp-3 font-mono text-[11px] text-zinc-300">
                  {c.prompt}
                </p>
              </div>

              {/* Botón de Carga de Imagen */}
              <div className="flex items-center justify-between pt-1 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-zinc-400">{c.archivo}</span>
                  {c.archivo_existe && (
                    <span className="text-[11px] font-medium text-emerald-400">✓ En disco</span>
                  )}
                </div>
                <label className="cursor-pointer rounded border border-zinc-700 bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-200 hover:bg-zinc-700">
                  {subiendoArchivo === c.creativo_id ? "Subiendo..." : "Subir imagen"}
                  <input
                    type="file"
                    accept="image/png,image/jpeg"
                    className="hidden"
                    disabled={subiendoArchivo === c.creativo_id}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) subirImagen(c, file);
                    }}
                  />
                </label>
              </div>
            </Tarjeta>
          ))}
        </div>
      </div>
    </div>
  );
}
