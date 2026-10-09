/**
 * fabricarConceptos.tsx — el botón «Generar los conceptos que faltan (N)» de un ángulo ganador.
 *
 * N y los parámetros los entrega el backend (`AnguloFase2.fabricar`): acá no se resta nada. Mismo
 * patrón de confirmación que «Armar FASE 1» (aviso en la propia pantalla, «Sí, confirmar y ejecutar»)
 * y mismo mecanismo de trabajos que el botón de prompts: `api.pedirAccion` → `/api/trabajos/{id}`.
 * La fábrica solo crea conceptos y sus prompts; no renderiza ni toca Meta.
 */
import { useCallback, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type FabricarConceptos } from "../api/cliente";
import { trabajoEnPalabras } from "../lenguaje";
import { Tarjeta } from "./ui";
import { ProgresoDelTrabajo } from "./generarPrompts";
import { responsableEnPalabras } from "./situacion";
import { Button } from "@/components/ui/button";

export function BotonFabricarConceptos({
  fabricar,
  angulo,
  clave,
}: {
  fabricar: FabricarConceptos | null | undefined;
  angulo: string;
  clave: string;
}) {
  const queryClient = useQueryClient();
  const [confirmando, setConfirmando] = useState(false);
  const [lanzado, setLanzado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const lanzar = useMutation({
    mutationFn: () => api.pedirAccion(fabricar!.accion_id, fabricar!.parametros, true),
    onMutate: () => setError(null),
    onSuccess: (r) => {
      setConfirmando(false);
      setLanzado(r.job_id);
    },
    onError: (e) => setError(e instanceof Error ? e.message : String(e)),
  });

  // El trabajo que sigue la pantalla: el que acaba de lanzar o el que el backend dice que ya corre.
  const trabajo = lanzado ?? fabricar?.trabajo_en_curso ?? null;
  const detalle = useQuery({
    queryKey: ["trabajo", trabajo],
    queryFn: () => api.trabajo(trabajo!),
    enabled: !!trabajo,
    refetchInterval: (consulta) => (trabajoEnPalabras(consulta.state.data?.estado).enCurso ? 2000 : false),
  });
  const recargar = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    queryClient.invalidateQueries({ queryKey: ["datos", clave] });
  }, [queryClient, clave]);

  if (!fabricar || fabricar.faltan <= 0) return null;

  const generando = lanzar.isPending || (!!trabajo && (!detalle.data || trabajoEnPalabras(detalle.data.estado).enCurso));
  const quien = responsableEnPalabras("etapa-9");

  return (
    <div className="space-y-2" data-testid={`fabricar-${angulo}`}>
      <div className="flex flex-wrap items-center justify-end gap-3">
        <Button
          type="button"
          size="sm"
          disabled={generando || !fabricar.habilitada}
          onClick={() => setConfirmando(true)}
        >
          {generando ? "Generando…" : `Generar los conceptos que faltan (${fabricar.faltan})`}
        </Button>
      </div>

      {confirmando && !generando && (
        <Tarjeta className="border-amber-700 bg-amber-950/30" >
          <div data-testid="confirmar-fabricar">
            <p className="text-sm text-zinc-200">
              La {quien} va a crear {fabricar.faltan} conceptos nuevos para {angulo} y dejar sus prompts listos. No toca
              Meta ni mueve plata. Tarda unos minutos.
            </p>
            <div className="mt-3 flex gap-3">
              <Button type="button" size="sm" disabled={lanzar.isPending} onClick={() => lanzar.mutate()}>
                {lanzar.isPending ? "Iniciando…" : "Sí, confirmar y ejecutar"}
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => setConfirmando(false)}>
                Cancelar
              </Button>
            </div>
          </div>
        </Tarjeta>
      )}

      {error && <p className="text-xs text-rose-300">{error}</p>}
      {trabajo && <ProgresoDelTrabajo trabajo={trabajo} alTerminar={recargar} />}
    </div>
  );
}
