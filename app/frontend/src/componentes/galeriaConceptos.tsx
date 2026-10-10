/**
 * galeriaConceptos.tsx — la galería de conceptos de UN ángulo, plegable, debajo de la tarjeta de
 * ese ángulo (el ángulo es la unidad de trabajo), y la tarjeta de cada concepto.
 *
 * Los rótulos de rango («Conceptos 1–5» / «Conceptos 6–10») salen de la estructura que declara el
 * backend (`campanas`); acá no se inventa ninguna cifra.
 */
import { ChevronDown } from "lucide-react";
import { api, type AnguloFase2, type CampanaFase2, type ConceptoFase2 } from "../api/cliente";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Chip, Tarjeta, type Tono } from "./ui";
import { BotonCopiarTexto, ImagenDeReferencia } from "./copiar";
import { BotonFabricarConceptos } from "./fabricarConceptos";
import { BotonMarcarGenerados } from "./marcarGenerados";
import { GenerarPromptsDelAngulo } from "./generarPrompts";
import { responsableEnPalabras } from "./situacion";

const TONOS_ESTADO: Record<string, Tono> = {
  GENERADO: "bien",
  PUBLICADO: "bien",
  PENDIENTE_GENERAR: "aviso",
};

const NUMERO_EN_PALABRAS: Record<number, string> = { 2: "dos", 3: "tres", 4: "cuatro" };

export interface AccionesDeConcepto {
  /** El producto de la galería: la miniatura se pide a su carpeta de media. */
  clave: string;
  subiendoArchivo: string | null;
  onSubir: (concepto: ConceptoFase2, archivo: File) => void;
  onAmpliar: (url: string) => void;
}

/** Una tarjeta de concepto: prompt real para copiar, imagen de referencia y subida de la pieza. */
export function TarjetaConcepto({
  c,
  i,
  acciones,
  mostrarAngulo = false,
}: {
  c: ConceptoFase2;
  i: number;
  acciones: AccionesDeConcepto;
  mostrarAngulo?: boolean;
}) {
  const { clave, subiendoArchivo, onSubir, onAmpliar } = acciones;
  // `?v=` es el mtime del archivo: al re-subir cambia y el navegador no muestra la imagen vieja.
  const urlImagen = c.archivo_existe
    ? `${api.urlMedia(clave, c.archivo)}${c.archivo_version ? `?v=${encodeURIComponent(c.archivo_version)}` : ""}`
    : null;
  return (
    <Tarjeta className="space-y-3 border-zinc-800 bg-zinc-900/50">
      <div className="flex items-start justify-between gap-2 border-b border-zinc-800 pb-2">
        <div>
          {mostrarAngulo && (
            <span className="mb-1 block font-mono text-[11px] text-zinc-400">{c.angulo_key || "Sin ángulo"}</span>
          )}
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

      {c.dispositivo && <p className="text-xs text-zinc-400 italic">«{c.dispositivo}»</p>}

      {/* Imagen de referencia del swipe (IMAGEN 1 del prompt): la estructura ganadora
          que hay que replicar. Click para ampliar. */}
      {c.referencia_url && (
        <ImagenDeReferencia
          url={c.referencia_url}
          alt={`Referencia de swipe para ${c.canonico_id}`}
          etiqueta="Imagen de referencia (IMAGEN 1)"
          onAmpliar={onAmpliar}
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

      {urlImagen && (
        <button
          type="button"
          onClick={() => onAmpliar(urlImagen)}
          className="block w-full overflow-hidden rounded-lg border border-border bg-background/60"
          title="Ver la imagen en tamaño completo"
        >
          <img
            src={urlImagen}
            alt={`Imagen de ${c.creativo_id}`}
            loading="lazy"
            className="h-32 w-full object-contain"
          />
        </button>
      )}

      {/* Botón de Carga de Imagen */}
      <div className="flex items-center justify-between pt-1 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-zinc-400">{c.archivo}</span>
          {c.archivo_existe && <span className="text-[11px] font-medium text-emerald-400">✓ En disco</span>}
        </div>
        {c.puede_subir && (
          <label
            className="cursor-pointer rounded border border-zinc-700 bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const file = e.dataTransfer.files?.[0];
              if (file && subiendoArchivo !== c.creativo_id) onSubir(c, file);
            }}
          >
            {subiendoArchivo === c.creativo_id ? "Subiendo..." : c.archivo_existe ? "Reemplazar imagen" : "Subir imagen"}
            <input
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              data-testid={`subir-${c.creativo_id}`}
              disabled={subiendoArchivo === c.creativo_id}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onSubir(c, file);
                e.target.value = "";
              }}
            />
          </label>
        )}
      </div>
    </Tarjeta>
  );
}

/** «Conceptos 1–5» con el guion largo, el mismo que usa el checklist del backend. */
const rango = (desde: number, hasta: number) => `${desde}–${hasta}`;

/** Qué decir cuando el ángulo todavía no tiene ningún concepto: sale del rol, no del producto. */
function sinConceptosDe(rol: string): string {
  return rol === "ganador_activo"
    ? `Todavía sin conceptos: los fabrica la ${responsableEnPalabras("etapa-9")}.`
    : "Todavía sin conceptos: se fabrican cuando el #1 cierre su FASE 2";
}

/** La galería plegable de un ángulo. El #1 nace abierta; los que esperan, cerradas. */
export function GaleriaDeConceptos({
  angulo,
  conceptos,
  requeridos,
  campanas,
  abierta,
  clave,
  acciones,
}: {
  angulo: AnguloFase2;
  conceptos: ConceptoFase2[];
  requeridos: number;
  campanas: CampanaFase2[];
  abierta: boolean;
  clave: string;
  acciones: AccionesDeConcepto;
}) {
  const hayPromptsPendientes = conceptos.some((c) => c.prompt_origen !== "paquete" || !c.prompt);

  // Rangos (1–5 / 6–10) según la estructura que declara el backend; sin estructura, un solo grupo.
  let acumulado = 0;
  const grupos: { brazo: string; desde: number; hasta: number; conceptos: ConceptoFase2[] }[] = campanas.map((c) => {
    const desde = acumulado + 1;
    acumulado += c.conceptos;
    return { brazo: c.brazo, desde, hasta: acumulado, conceptos: conceptos.filter((x) => x.campana === c.brazo) };
  });
  if (grupos.length === 0) {
    grupos.push({ brazo: "", desde: 1, hasta: conceptos.length, conceptos });
  } else {
    const sinCampana = conceptos.filter((x) => !grupos.some((g) => g.brazo === x.campana));
    grupos[grupos.length - 1].conceptos.push(...sinCampana);
  }

  const encabezado = `Galería de conceptos (${angulo.conceptos_listos ?? 0}${requeridos ? ` de ${requeridos}` : ""})`;
  const lineaDeCampanas =
    campanas.length > 1 && requeridos
      ? `Los ${requeridos} conceptos se publican en ${NUMERO_EN_PALABRAS[campanas.length] ?? campanas.length} campañas de ${campanas[0].conceptos}; la tercera repite los mismos.`
      : null;

  return (
    <div className="space-y-2">
    {/* El botón de fabricar va pegado al encabezado de la galería, visible aunque ésta esté cerrada. */}
    <BotonFabricarConceptos fabricar={angulo.fabricar} angulo={angulo.angulo_key} clave={clave} />
    <BotonMarcarGenerados marcar={angulo.marcar} angulo={angulo.angulo_key} clave={clave} />
    <details
      open={abierta}
      className="group rounded-xl border border-zinc-800 bg-zinc-950/40"
      data-testid={`galeria-${angulo.angulo_key}`}
    >
      <summary className="flex cursor-pointer select-none items-center justify-between gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-zinc-100 hover:bg-zinc-900/60">
        <span>{encabezado}</span>
        <ChevronDown aria-hidden className="size-4 shrink-0 text-zinc-400 transition-transform group-open:rotate-180" />
      </summary>
      <div className="space-y-4 px-4 pb-4">
        {conceptos.length === 0 ? (
          <p className="text-sm text-zinc-400">{sinConceptosDe(angulo.rol)}</p>
        ) : (
          <>
            <p className="text-xs text-zinc-400">
              Copiá el prompt, generá en tu IA favorita (ChatGPT web, Midjourney) y subí la pieza terminada.
              {lineaDeCampanas && <span className="mt-1 block">{lineaDeCampanas}</span>}
            </p>

            {hayPromptsPendientes && (
              <GenerarPromptsDelAngulo generar={angulo.generar} clave={clave} angulo={angulo.angulo_key} />
            )}

            {grupos.map((g) => {
              const total = g.hasta - g.desde + 1;
              return (
                <section key={g.brazo} data-testid={`grupo-${angulo.angulo_key}-${g.brazo || "unico"}`}>
                  {g.brazo && (
                    <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                      <h3 className="text-sm font-semibold text-zinc-200">Conceptos {rango(g.desde, g.hasta)}</h3>
                      <span className="text-xs text-zinc-400">
                        {g.conceptos.length} de {total} conceptos
                      </span>
                    </div>
                  )}
                  {g.brazo && g.conceptos.length < total && (
                    <p className="mb-2 rounded-lg border border-amber-800/50 bg-amber-950/20 px-3 py-2 text-xs text-amber-200">
                      {g.conceptos.length === 0
                        ? `Conceptos ${rango(g.desde, g.hasta)} pendientes: todavía no existen para este ángulo.`
                        : `Faltan ${total - g.conceptos.length} de los conceptos ${rango(g.desde, g.hasta)}.`}
                    </p>
                  )}
                  <div className="grid gap-4 md:grid-cols-2">
                    {g.conceptos.map((c, i) => (
                      <TarjetaConcepto key={c.creativo_id || i} c={c} i={i} acciones={acciones} />
                    ))}
                  </div>
                </section>
              );
            })}
          </>
        )}
      </div>
    </details>
    </div>
  );
}

/** Los conceptos cuyo ángulo no está en el ranking (F1 sueltos, filas pendientes…): visibles, plegados. */
export function OtrosConceptos({
  conceptos,
  acciones,
}: {
  conceptos: ConceptoFase2[];
  acciones: AccionesDeConcepto;
}) {
  if (conceptos.length === 0) return null;
  return (
    <details open={false} className="group rounded-xl border border-zinc-800 bg-zinc-900/30" data-testid="otros-conceptos">
      <summary className="flex cursor-pointer select-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold text-zinc-200 hover:bg-zinc-900/60">
        <span>Otros conceptos registrados ({conceptos.length})</span>
        <ChevronDown aria-hidden className="size-4 shrink-0 text-zinc-400 transition-transform group-open:rotate-180" />
      </summary>
      <div className="grid gap-4 px-4 pb-4 md:grid-cols-2">
        {conceptos.map((c, i) => (
          <TarjetaConcepto key={c.creativo_id || i} c={c} i={i} acciones={acciones} mostrarAngulo />
        ))}
      </div>
    </details>
  );
}
