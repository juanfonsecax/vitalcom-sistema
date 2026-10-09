/**
 * generarPrompts.tsx — el botón «Generar los prompts de este ángulo» de la galería de FASE 2.
 *
 * Todo lo que se muestra sale de `angulo.generar` (`contratos._generar_prompts`): la acción del
 * manifiesto con sus parámetros, si se puede pedir ahora y qué dato la frena (de `datos_producto.py`).
 * Acá no se decide nada ni se muestra un comando: si falta un dato, se dice cuál con su frase y se
 * lleva a la tarjeta «Para arrancar te falta»; el perfil creativo lo prepara Claude.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, type GenerarPrompts } from "../api/cliente";
import { trabajoEnPalabras } from "../lenguaje";
import { ID_PARA_ARRANCAR } from "./arranque";
import { Chip, Tarjeta } from "./ui";
import { Button } from "@/components/ui/button";

const CLAVE_PERFIL = "perfil_creativo";
const noHaceNada = () => undefined;

function irALaTarjetaDeArranque() {
  document.getElementById(ID_PARA_ARRANCAR)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

/** Sigue un trabajo hasta que termina y, al terminar bien, avisa para que la pantalla se recargue. */
export function ProgresoDelTrabajo({ trabajo, alTerminar }: { trabajo: string; alTerminar: () => void }) {
  const detalle = useQuery({
    queryKey: ["trabajo", trabajo],
    queryFn: () => api.trabajo(trabajo),
    refetchInterval: (consulta) => (trabajoEnPalabras(consulta.state.data?.estado).enCurso ? 2000 : false),
  });
  const estado = detalle.data?.estado ?? "ENCOLADO";
  const { texto, tono, enCurso } = trabajoEnPalabras(estado);
  const avisado = useRef(false);
  useEffect(() => {
    if (estado === "EXITO" && !avisado.current) {
      avisado.current = true;
      alTerminar();
    }
  }, [estado, alTerminar]);
  const unidad = (detalle.data?.unidades?.[0] ?? {}) as { json?: { motivo?: string } };
  const motivo = unidad.json?.motivo ?? (detalle.data?.resultado as { detalle?: string } | null)?.detalle;
  return (
    <div className="space-y-1 text-xs text-muted-foreground" aria-live="polite">
      <p className="flex flex-wrap items-center gap-2">
        <Chip tono={tono} titulo={estado}>
          {texto}
        </Chip>
        <Link to="/trabajos/$id" params={{ id: trabajo }} className="text-sky-300 hover:text-sky-200">
          Ver el progreso en vivo →
        </Link>
      </p>
      {!enCurso && estado !== "EXITO" && motivo && <p className="text-rose-300">{motivo}</p>}
    </div>
  );
}

/** Lanza una acción del manifiesto y muestra su trabajo; al terminar bien, `alTerminar`. */
function useLanzarAccion(accionId: string, parametros: Record<string, string>, confirmado: boolean) {
  const [trabajo, setTrabajo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lanzar = useMutation({
    mutationFn: () => api.pedirAccion(accionId, parametros, confirmado),
    onMutate: () => setError(null),
    onSuccess: (r) => setTrabajo(r.job_id),
    onError: (e) => setError(e instanceof Error ? e.message : String(e)),
  });
  return { trabajo, error, lanzar };
}

function BotonGenerar({ generar, alTerminar }: { generar: GenerarPrompts; alTerminar: () => void }) {
  const { trabajo, error, lanzar } = useLanzarAccion(generar.accion_id, generar.parametros as Record<string, string>, false);
  return (
    <div className="space-y-2">
      <Button type="button" size="sm" disabled={lanzar.isPending || !!trabajo} onClick={() => lanzar.mutate()}>
        {lanzar.isPending ? "Pidiendo…" : "Generar los prompts de este ángulo"}
      </Button>
      {generar.aviso && <p className="text-xs text-amber-300">{generar.aviso}</p>}
      {error && <p className="text-xs text-rose-300">{error}</p>}
      {trabajo && <ProgresoDelTrabajo trabajo={trabajo} alTerminar={alTerminar} />}
    </div>
  );
}

function PerfilCreativoPendiente({ accionPerfil, clave }: { accionPerfil: string | null; clave: string }) {
  const { trabajo, error, lanzar } = useLanzarAccion(accionPerfil ?? "", { producto_key: clave }, true);
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-amber-100">Claude prepara el perfil creativo de este ángulo.</p>
      {accionPerfil ? (
        <>
          <Button type="button" size="sm" variant="outline" disabled={lanzar.isPending || !!trabajo} onClick={() => lanzar.mutate()}>
            {lanzar.isPending ? "Pidiendo…" : "Pedirle a Claude el perfil creativo"}
          </Button>
          {error && <p className="text-xs text-rose-300">{error}</p>}
          {trabajo && <ProgresoDelTrabajo trabajo={trabajo} alTerminar={noHaceNada} />}
        </>
      ) : (
        <p className="text-xs text-muted-foreground">
          Queda pendiente de Claude: se lo pedís en la sesión y, cuando esté, el botón se habilita solo.
        </p>
      )}
    </div>
  );
}

/** El bloque de arriba de la galería de un ángulo con prompts pendientes. */
export function GenerarPromptsDelAngulo({
  generar,
  clave,
  angulo,
}: {
  generar: GenerarPrompts | null | undefined;
  clave: string;
  angulo: string;
}) {
  const queryClient = useQueryClient();
  const recargar = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    queryClient.invalidateQueries({ queryKey: ["datos", clave] });
  }, [queryClient, clave]);

  if (!generar) {
    return (
      <p className="mb-3 text-xs text-muted-foreground">
        Este ángulo no tiene su propia Fase 2: no se le generan prompts.
      </p>
    );
  }
  if (!generar.habilitada) {
    return (
      <Tarjeta className="mb-3 space-y-1 border-dashed p-3">
        <p className="text-xs text-muted-foreground">{generar.motivo || "Se genera cuando le toque su Fase 2."}</p>
        <Button type="button" size="sm" disabled>
          Generar los prompts de este ángulo
        </Button>
      </Tarjeta>
    );
  }
  return (
    <Tarjeta className="mb-3 space-y-3 border-amber-800/50 bg-amber-950/20 p-3" >
      <p className="text-sm font-semibold text-amber-200">Prompts de {angulo}</p>
      {generar.listo ? (
        <BotonGenerar generar={generar} alTerminar={recargar} />
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-amber-200/90">Antes de generarlos falta:</p>
          <ul className="space-y-2">
            {generar.faltan.map((item) => (
              <li key={item.clave} className="space-y-1 rounded-lg border border-border bg-muted/20 p-2.5">
                <p className="text-xs font-medium text-foreground">
                  {item.rotulo}: <span className="font-normal text-muted-foreground">{item.detalle}</span>
                </p>
                {item.clave === CLAVE_PERFIL ? (
                  <PerfilCreativoPendiente accionPerfil={generar.accion_perfil ?? null} clave={clave} />
                ) : (
                  <>
                    <p className="text-xs text-muted-foreground">{item.como_resolver}</p>
                    {item.accion && (
                      <button
                        type="button"
                        onClick={irALaTarjetaDeArranque}
                        className="text-xs text-sky-300 underline underline-offset-2 hover:text-sky-200"
                      >
                        Resolverlo en «Para arrancar te falta»
                      </button>
                    )}
                  </>
                )}
              </li>
            ))}
          </ul>
          <Button type="button" size="sm" disabled>
            Generar los prompts de este ángulo
          </Button>
        </div>
      )}
    </Tarjeta>
  );
}
