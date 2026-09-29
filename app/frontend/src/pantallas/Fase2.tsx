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
import { api, type ConceptoFase2 } from "../api/cliente";
import { trabajoPendientePorProducto } from "../componentes/resumen";
import {
  AnguloEnTesteoAhora,
  AngulosEnFila,
  AngulosQueNoFuncionaron,
  OrdenesDeRenovacion,
  type OrdenMotor,
} from "../componentes/angulosFase2";
import { BanderaMercado } from "../componentes/mercado";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Cargando, Chip, Info, Problema, Tarjeta, type Tono } from "../componentes/ui";
import { BotonCopiarTexto, ImagenDeReferencia, Lightbox } from "../componentes/copiar";
import { GenerarPromptsDelAngulo } from "../componentes/generarPrompts";

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

  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos });
  const [anguloElegido, setAnguloElegido] = useState<string | null>(null);
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

  // Galería agrupada por ángulo, en el orden de los ángulos; arranca en el #1.
  const clavesDeConceptos = Array.from(new Set(d.conceptos.map((c) => c.angulo_key || "")));
  const ordenAngulos = angulos.map((a) => a.angulo_key);
  const gruposGaleria = [
    ...ordenAngulos.filter((k) => clavesDeConceptos.includes(k)),
    ...clavesDeConceptos.filter((k) => !ordenAngulos.includes(k)),
  ];
  const grupoActivo =
    anguloElegido && gruposGaleria.includes(anguloElegido)
      ? anguloElegido
      : gruposGaleria.includes(principal?.angulo_key ?? "")
        ? (principal?.angulo_key ?? "")
        : (gruposGaleria[0] ?? "");
  const conceptosVisibles = d.conceptos.filter((c) => (c.angulo_key || "") === grupoActivo);
  const hayPromptsPendientes = conceptosVisibles.some((c) => c.prompt_origen !== "paquete" || !c.prompt);
  const anguloActivo = angulos.find((a) => a.angulo_key === grupoActivo);

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
            Estructura 1-1-5 + 1-1-5 + 1-2-5 · 10 conceptos con ángulo y copy fijos · <Info termino="fase_2" />{" "}
            <BanderaMercado mercado={d.mercado} />
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
            Ver FASE 3 (Flujo LucidBot) →
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

      {/* Cada ángulo en su propio bloque: el #1 en testeo ahora, los demás en fila o descartados. */}
      <AnguloEnTesteoAhora angulo={principal} paso={d.nodo_actual} perfil={d} />
      <AngulosEnFila angulos={enFila} perfil={d} />
      <AngulosQueNoFuncionaron angulos={noFuncionaron} trabajoPendiente={trabajoPendiente} perfil={d} />

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
            Galería de Conceptos ({conceptosVisibles.length} de 10)
          </h2>
          <span className="text-xs text-zinc-400">
            Copiá el prompt, generá en tu IA favorita (ChatGPT web, Midjourney) y subí la pieza terminada.
          </span>
        </div>

        {gruposGaleria.length > 1 && (
          <div className="mb-3 flex flex-wrap gap-2" role="tablist" aria-label="Ángulo de la galería">
            {gruposGaleria.map((k) => (
              <button
                key={k}
                type="button"
                role="tab"
                aria-selected={k === grupoActivo}
                onClick={() => setAnguloElegido(k)}
                className={`rounded-full border px-3 py-1 font-mono text-xs ${
                  k === grupoActivo
                    ? "border-emerald-700 bg-emerald-950/50 text-emerald-200"
                    : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                {k || "Sin ángulo"}
              </button>
            ))}
          </div>
        )}

        {hayPromptsPendientes && (
          <GenerarPromptsDelAngulo generar={anguloActivo?.generar} clave={clave} angulo={grupoActivo} />
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {conceptosVisibles.map((c, i) => (
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

              {/* Imagen de referencia del swipe (IMAGEN 1 del prompt): la estructura ganadora
                  que hay que replicar. Click para ampliar. */}
              {c.referencia_url && (
                <ImagenDeReferencia
                  url={c.referencia_url}
                  alt={`Referencia de swipe para ${c.canonico_id}`}
                  etiqueta="Imagen de referencia (IMAGEN 1)"
                  onAmpliar={setImagenAmpliada}
                />
              )}

              {/* Caja de Prompt Resuelto — el prompt REAL de armar_prompts_fase2.py (nunca uno
                  inventado); si todavía no se generó el paquete, el botón de arriba lo genera. */}
              {c.prompt_origen === "paquete" && c.prompt ? (
                <div className="rounded-lg border border-border bg-muted/40 p-2.5">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Prompt definitivo — copiar y pegar
                    </span>
                    <BotonCopiarTexto texto={c.prompt!} />
                  </div>
                  <pre className="max-h-56 overflow-y-auto whitespace-pre-wrap break-words rounded-md bg-background/60 p-2 font-mono text-[11px] leading-relaxed text-foreground">
                    {c.prompt}
                  </pre>
                  <p className="mt-1.5 text-[11px] text-muted-foreground">
                    Pegá la imagen de referencia + este prompt junto con la foto del producto en tu
                    creador de imágenes con IA (ChatGPT web). Cuando la imagen esté lista, subila acá
                    mismo.
                  </p>
                </div>
              ) : (
                <div className="rounded-lg border border-amber-800/50 bg-amber-950/20 p-2.5">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">
                    Prompt pendiente de generar
                  </span>
                  <p className="mt-1 text-[11px] text-amber-200/90">
                    Todavía no existe el paquete creativo de este ángulo. Se genera con el botón
                    «Generar los prompts de este ángulo» (nunca se inventa un prompt genérico).
                  </p>
                  {c.comando_generar && (
                    <Collapsible>
                      <CollapsibleTrigger className="mt-1.5 text-[11px] text-zinc-400 underline underline-offset-2 hover:text-zinc-200">
                        Detalle técnico
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-words rounded-md bg-background/60 p-2 font-mono text-[11px] leading-relaxed text-amber-100">
                          {c.comando_generar}
                        </pre>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                </div>
              )}

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
