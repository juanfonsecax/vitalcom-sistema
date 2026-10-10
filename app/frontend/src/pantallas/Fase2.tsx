/**
 * Fase2.tsx — Pantalla de FASE 2: Testeo de Conceptos y Ciclo de Fatiga.
 *
 * Muestra:
 *  1. El ángulo #1, en testeo de conceptos ahora, con sus cifras clave.
 *  2. Los ganadores en fila (#2, #3…): cada uno tendrá su propia Fase 2, escalonada.
 *  3. Los ángulos que no funcionaron, con la etiqueta que dicen los datos.
 *  4. Galería de conceptos agrupada por ángulo (arranca en el #1), prompts listos para copiar y subida manual.
 *  5. Ciclo de fatiga: las órdenes concretas del motor (RENOVAR) y el botón «Nuevos ángulos para este producto».
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api, type AnguloFase2, type ConceptoFase2 } from "../api/cliente";
import { trabajoPendientePorProducto } from "../componentes/resumen";
import {
  AnguloEnTesteoAhora,
  AngulosEnFila,
  AngulosQueNoFuncionaron,
  OrdenesDeRenovacion,
  type OrdenMotor,
} from "../componentes/angulosFase2";
import { BanderaMercado } from "../componentes/mercado";
import { LineaDeSituacion, responsableEnPalabras } from "../componentes/situacion";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";
import { Lightbox } from "../componentes/copiar";
import { GaleriaDeConceptos, OtrosConceptos } from "../componentes/galeriaConceptos";

export function Fase2({ clave: claveProp }: { clave?: string }) {
  const params = useParams({ strict: false }) as { clave?: string };
  const clave = claveProp || params.clave || "";
  const queryClient = useQueryClient();
  const consulta = useQuery({
    queryKey: ["fase2", clave],
    queryFn: () => api.fase2(clave),
  });

  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos });
  const [subiendoArchivo, setSubiendoArchivo] = useState<string | null>(null);
  const [mensajeSubida, setMensajeSubida] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);
  const [modalReingreso, setModalReingreso] = useState(false);
  const [motivoReingreso, setMotivoReingreso] = useState("Ángulo agotado / fatiga de ventas");
  const [imagenAmpliada, setImagenAmpliada] = useState<string | null>(null);

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

  // El backend ya decidió rol y orden de cada ángulo; acá solo se reparten en bloques.
  const angulos = d.angulos ?? [];
  const principal = angulos.find((a) => a.rol === "ganador_activo");
  const enFila = angulos.filter((a) => a.rol === "ganador_en_fila");
  const noFuncionaron = angulos.filter((a) => a.rol === "perdedor" || a.rol === "midiendo");
  const trabajoPendiente = trabajoPendientePorProducto(trabajos.data).get(clave);

  // Cada ángulo del ranking lleva SU galería (filtrada por angulo_key). Los conceptos de un ángulo
  // que no está en el ranking (F1 sueltos, filas sin ángulo…) no se descartan: van a «Otros».
  const clavesDelRanking = new Set([principal, ...enFila].filter(Boolean).map((a) => a!.angulo_key));
  const conceptosDe = (k: string) => d.conceptos.filter((c) => (c.angulo_key || "") === k);
  const otrosConceptos = d.conceptos.filter((c) => !clavesDelRanking.has(c.angulo_key || ""));

  const subirImagen = async (concepto: ConceptoFase2, archivo: File) => {
    setSubiendoArchivo(concepto.creativo_id);
    setMensajeSubida(null);
    try {
      await api.subirImagenDeConcepto(clave, concepto.creativo_id, archivo);
      setMensajeSubida({ tipo: "ok", texto: `Imagen ${concepto.archivo} cargada y concepto marcado como generado.` });
      queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al subir la pieza";
      setMensajeSubida({ tipo: "error", texto: msg });
    } finally {
      setSubiendoArchivo(null);
    }
  };

  const accionesDeConcepto = { subiendoArchivo, onSubir: subirImagen, onAmpliar: setImagenAmpliada };
  const galeriaDe = (a: AnguloFase2, abierta: boolean) => (
    <GaleriaDeConceptos
      angulo={a}
      conceptos={conceptosDe(a.angulo_key)}
      requeridos={d.conceptos_requeridos ?? 0}
      campanas={d.campanas ?? []}
      abierta={abierta}
      clave={clave}
      acciones={accionesDeConcepto}
    />
  );

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
            Estructura 1-1-5 + 1-1-5 + 1-2-5 · {d.conceptos_requeridos ? `${d.conceptos_requeridos} conceptos` : "Conceptos"} con ángulo y copy fijos · <Info termino="fase_2" />{" "}
            <BanderaMercado mercado={d.mercado} />
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Chip tono={d.conceptos_generados >= (d.conceptos_requeridos ?? 0) ? "bien" : "aviso"}>
            {d.conceptos_requeridos
              ? `${d.conceptos_generados} de ${d.conceptos_requeridos} conceptos listos${
                  d.conceptos_faltan > 0
                    ? ` · faltan ${d.conceptos_faltan} · los fabrica la ${responsableEnPalabras("etapa-9")}`
                    : ""
                }`
              : `${d.conceptos_generados} conceptos listos`}
          </Chip>
          <Link
            to="/producto/$clave/fase3"
            params={{ clave }}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            Ver FASE 3 (Flujo LucidBot) →
          </Link>
        </div>
      </div>

      {/* El estado de la fase en una línea: dónde está, qué la frena y quién lo hace. */}
      <LineaDeSituacion
        testid="estado-de-fase"
        className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-sm text-zinc-300"
        prefijo={d.fase_validada ? "Validada" : "Sin validar"}
        datos={{
          fase: d.fase,
          faseTitulo: d.fase_titulo,
          paso: d.paso_titulo,
          trabadoPor: d.bloqueante_principal,
          dueno: d.dueno_bloqueante,
          ejecutor: d.ejecutor,
        }}
      />

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

      {/* Cada ángulo en su propio bloque: el #1 en testeo ahora, los demás en fila o descartados. */}
      <section className="space-y-4" data-testid="que-hacer-ahora">
        <h2 className="text-base font-bold text-zinc-100">¿Qué hacer ahora?</h2>
        <AnguloEnTesteoAhora
          angulo={principal}
          paso={d.nodo_actual}
          perfil={d}
          galeria={principal ? galeriaDe(principal, true) : undefined}
        />
        <AngulosEnFila angulos={enFila} perfil={d} galeriaDe={(a) => galeriaDe(a, false)} />
      </section>

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

      {/* Alertas de Fatiga y Botón de Retorno a F1 */}
      <Tarjeta className="border-amber-800/40 bg-amber-950/20 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-amber-200">
              Ciclo de Fatiga & Renovación
            </h3>
            <OrdenesDeRenovacion ordenes={(d.fatiga?.ordenes ?? []) as OrdenMotor[]} />
            <Collapsible>
              <CollapsibleTrigger className="mt-3 text-xs text-zinc-400 underline underline-offset-2 hover:text-zinc-200">
                ¿Cómo funciona la renovación?
              </CollapsibleTrigger>
              <CollapsibleContent>
                <p className="mt-1 text-xs text-zinc-300">
                  Si un ángulo ganador se cansa o el motor emite <span className="font-mono text-amber-300">RENOVAR</span>,
                  se rotan los creativos en FASE 2 y el ángulo se mantiene. Si el ángulo ya no rinde, se vuelve a FASE 1
                  con ángulos frescos.
                </p>
              </CollapsibleContent>
            </Collapsible>
          </div>
          <Button
            onClick={() => setModalReingreso(true)}
            variant="outline"
            size="sm"
          >
            Nuevos ángulos para este producto →
          </Button>
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
              {(d.fatiga?.angulos_probados ?? []).join(", ") || "Ningún ángulo previo registrado"}
            </div>
            <div className="mt-3">
              <label className="text-xs text-zinc-400">Motivo del reingreso:</label>
              <Input
                type="text"
                value={motivoReingreso}
                onChange={(e) => setMotivoReingreso(e.target.value)}
                className="mt-1"
              />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button
                onClick={() => setModalReingreso(false)}
                variant="outline"
                size="sm"
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                disabled={mutacionReingreso.isPending}
                onClick={() => mutacionReingreso.mutate(motivoReingreso)}
              >
                {mutacionReingreso.isPending ? "Registrando..." : "Sí, volver a F1"}
              </Button>
            </div>
          </div>
        )}
      </Tarjeta>

      {/* Apagados al final, plegados y sin botones de acción. */}
      <AngulosQueNoFuncionaron angulos={noFuncionaron} trabajoPendiente={trabajoPendiente} perfil={d} />

      {/* Conceptos de ángulos fuera del ranking: no se pierden, pero no estorban. */}
      <OtrosConceptos conceptos={otrosConceptos} acciones={accionesDeConcepto} />

      {/* Lightbox — imagen de referencia ampliada */}
      {imagenAmpliada && (
        <Lightbox
          url={imagenAmpliada}
          alt="Referencia de swipe ampliada"
          onCerrar={() => setImagenAmpliada(null)}
        />
      )}
    </div>
  );
}
