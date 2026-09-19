/**
 * Fase3.tsx — Pantalla de FASE 3: Escalado CBO 1-1-7 y Expansión.
 *
 * Muestra:
 *  1. Semáforo del gate «concepto ganador en 2 de 2» con la evidencia real de flujo.py.
 *  2. Estructura 1-1-7 CBO explicada en lenguaje simple.
 *  3. Expansión horizontal por Post ID, multicuenta y multifanpage.
 *  4. Botón de retorno a F1 en caso de agotamiento del escalado.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api } from "../api/cliente";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";

export function Fase3({ clave: claveProp }: { clave?: string }) {
  const params = useParams({ strict: false }) as { clave?: string };
  const clave = claveProp || params.clave || "";
  const queryClient = useQueryClient();
  const consulta = useQuery({
    queryKey: ["fase3", clave],
    queryFn: () => api.fase3(clave),
  });

  const [modalReingreso, setModalReingreso] = useState(false);
  const [motivoReingreso, setMotivoReingreso] = useState("Escalado agotado / fatiga de microángulos");

  const mutacionReingreso = useMutation({
    mutationFn: (motivo: string) => api.reingresoF1(clave, motivo),
    onSuccess: () => {
      setModalReingreso(false);
      queryClient.invalidateQueries({ queryKey: ["fase3", clave] });
      queryClient.invalidateQueries({ queryKey: ["producto", clave] });
    },
  });

  if (consulta.isLoading) return <Cargando que="el tablero de FASE 3" />;
  if (consulta.error) return <Problema error={consulta.error} />;

  const d = consulta.data;
  if (!d) return null;

  const gateCumplido = d.gate_2de2.ok;

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Link to="/producto/$clave" params={{ clave }} className="text-xs text-zinc-400 hover:text-zinc-200">
              ← Volver a la ficha de {clave}
            </Link>
          </div>
          <h1 className="mt-1 text-2xl font-bold text-zinc-100">
            FASE 3 · Escalado CBO ({clave})
          </h1>
          <p className="text-sm text-zinc-400">
            Estructura 1-1-7 CBO · Presupuesto a nivel campaña · Replicación por Post ID · <Info termino="fase_3" />
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
        </div>
      </div>

      {/* Semáforo del Gate: Concepto Ganador en 2 de 2 */}
      <Tarjeta
        className={`border-2 p-5 ${
          gateCumplido
            ? "border-emerald-600 bg-emerald-950/20"
            : "border-amber-600/80 bg-amber-950/20"
        }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Gate de Entrada a FASE 3
              </span>
              <Chip tono={gateCumplido ? "bien" : "aviso"}>
                {gateCumplido ? "✓ GATE CUMPLIDO" : "⚠ GATE PENDIENTE"}
              </Chip>
            </div>
            <h2 className="text-lg font-bold text-zinc-100">
              Concepto Ganador Replicado en 2 de 2
            </h2>
            <p className="text-xs text-zinc-300">
              {d.gate_2de2.regla || "Regla de replicación: un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido."}
            </p>
          </div>

          <div className="rounded-lg bg-zinc-900/80 p-3 text-right">
            <span className="text-[11px] uppercase text-zinc-500">Evidencia del Motor</span>
            <div className="mt-1 font-mono text-xs font-semibold text-zinc-200">
              {d.gate_2de2.observado || "Sin datos de replicación"}
            </div>
          </div>
        </div>
      </Tarjeta>

      {/* Estructura CBO 1-1-7 */}
      <div className="grid gap-4 md:grid-cols-2">
        <Tarjeta className="space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <h3 className="text-sm font-bold text-zinc-200">Estructura de Campaña 1-1-7 CBO</h3>
            <Chip tono={d.plan_cbo.tiene_plan ? "bien" : "aviso"}>
              {d.plan_cbo.estado}
            </Chip>
          </div>
          <p className="text-xs text-zinc-400">
            {d.plan_cbo.descripcion}
          </p>
          <div className="rounded-lg bg-zinc-950 p-3 text-xs text-zinc-300 space-y-1.5">
            <div>
              <span className="font-semibold text-zinc-400">1 Campaña CBO:</span> Presupuesto inicial optimizado automáticamente por Meta.
            </div>
            <div>
              <span className="font-semibold text-zinc-400">1 Conjunto de Anuncios:</span> Audiencia abierta de Guatemala (+25 años).
            </div>
            <div>
              <span className="font-semibold text-zinc-400">7 Anuncios Gemelos:</span> La misma imagen ganadora con 7 hooks/microángulos distintos para maximizar alcance.
            </div>
          </div>
          {d.plan_cbo.archivo && (
            <div className="text-[11px] text-emerald-400 font-mono">
              ✓ Archivo de plan generado: {d.plan_cbo.archivo}
            </div>
          )}
        </Tarjeta>

        {/* Expansión Horizontal */}
        <Tarjeta className="space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <h3 className="text-sm font-bold text-zinc-200">Expansión Horizontal (Multi-Cuenta)</h3>
            <Chip tono={d.expansion.post_id ? "bien" : "dato"}>
              {d.expansion.post_id ? "Post ID Activo" : "Cuenta Principal"}
            </Chip>
          </div>
          <p className="text-xs text-zinc-400">
            Replicación de la pieza ganadora en cuentas secundarias usando el mismo <span className="font-mono text-zinc-300">post_id</span> para compartir prueba social (likes, comentarios y compartidos).
          </p>
          <div className="rounded-lg bg-zinc-950 p-3 text-xs space-y-2">
            <div>
              <span className="text-zinc-500">Cuenta Principal:</span>{" "}
              <span className="font-mono font-semibold text-zinc-200">{d.expansion.cuenta_primaria}</span>
            </div>
            <div>
              <span className="text-zinc-500">Cuentas con réplica ({d.expansion.cuentas_activas.length}):</span>{" "}
              <span className="font-mono text-zinc-300">{d.expansion.cuentas_activas.join(", ")}</span>
            </div>
            {d.expansion.page_id && (
              <div>
                <span className="text-zinc-500">FanPage ID:</span>{" "}
                <span className="font-mono text-zinc-300">{d.expansion.page_id}</span>
              </div>
            )}
          </div>
        </Tarjeta>
      </div>

      {/* Módulo de Fatiga en Escalado */}
      <Tarjeta className="border-zinc-800 bg-zinc-900/40 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-zinc-200">
              ¿El escalado llegó a su techo?
            </h3>
            <p className="mt-1 text-xs text-zinc-400">
              Si la frecuencia sube, el CPA se degrada y los 7 microángulos ya se agotaron, podemos reiniciar el ciclo buscando ángulos frescos en FASE 1.
            </p>
          </div>
          <button
            onClick={() => setModalReingreso(true)}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-semibold text-zinc-200 hover:bg-zinc-700"
          >
            Nuevos ángulos para este producto →
          </button>
        </div>

        {/* Modal de Reingreso */}
        {modalReingreso && (
          <div className="mt-4 rounded-lg border border-zinc-700 bg-zinc-900 p-4 shadow-xl">
            <h4 className="text-sm font-bold text-zinc-100">
              Confirmar retorno a FASE 1 desde FASE 3
            </h4>
            <p className="mt-1 text-xs text-zinc-300">
              Se iniciará una nueva investigación para descubrir ángulos frescos. Se excluirán los ángulos históricos:
            </p>
            <div className="mt-2 rounded bg-zinc-950 p-2 font-mono text-xs text-zinc-400">
              {d.fatiga.angulos_probados.join(", ") || "Ningún ángulo previo"}
            </div>
            <div className="mt-3">
              <label className="text-xs text-zinc-400">Motivo:</label>
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
                {mutacionReingreso.isPending ? "Registrando..." : "Confirmar retorno a F1"}
              </button>
            </div>
          </div>
        )}
      </Tarjeta>
    </div>
  );
}
