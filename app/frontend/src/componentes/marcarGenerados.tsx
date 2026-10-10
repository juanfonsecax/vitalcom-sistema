/**
 * marcarGenerados.tsx — el botón «Marcar como generadas las imágenes que ya subiste (N)» de un ángulo.
 *
 * N y los parámetros los entrega el backend (`AnguloFase2.marcar`, `contratos._marcar`): acá no se
 * cuenta nada. La acción solo pasa a GENERADO los conceptos IMAGEN cuyo archivo ya está en disco;
 * no toca Meta. Mismo mecanismo de trabajos que los botones vecinos (`api.pedirAccion`).
 */
import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { MarcarGenerados } from "../api/cliente";
import { ProgresoDelTrabajo, useLanzarAccion } from "./generarPrompts";
import { Button } from "@/components/ui/button";

export function BotonMarcarGenerados({
  marcar,
  angulo,
  clave,
}: {
  marcar: MarcarGenerados | null | undefined;
  angulo: string;
  clave: string;
}) {
  const queryClient = useQueryClient();
  const { trabajo, error, lanzar } = useLanzarAccion(
    marcar?.accion_id ?? "",
    (marcar?.parametros ?? {}) as Record<string, string>,
    false,
  );
  const recargar = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    queryClient.invalidateQueries({ queryKey: ["datos", clave] });
  }, [queryClient, clave]);

  if (!marcar || marcar.listos <= 0) return null;

  return (
    <div className="space-y-2" data-testid={`marcar-${angulo}`}>
      <div className="flex flex-wrap items-center justify-end gap-3">
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={lanzar.isPending || !!trabajo || !marcar.habilitada}
          onClick={() => lanzar.mutate()}
        >
          {lanzar.isPending ? "Marcando…" : `Marcar como generadas las imágenes que ya subiste (${marcar.listos})`}
        </Button>
      </div>
      {error && <p className="text-xs text-rose-300">{error}</p>}
      {trabajo && <ProgresoDelTrabajo trabajo={trabajo} alTerminar={recargar} />}
    </div>
  );
}
