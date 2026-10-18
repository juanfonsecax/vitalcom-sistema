/**
 * verificarPublicada.tsx — el botón «Ya publiqué la campaña — verificar» de un brazo de FASE 2.
 *
 * Los brazos que se ofrecen y los parámetros salen del backend (`Fase2Detalle.publicaciones`,
 * `contratos._publicaciones_fase2`): un brazo aparece solo si tiene su paquete de publicación. La
 * acción lee Meta (solo lectura), corre el gate y graba los ids; acá se muestra el mensaje que
 * devuelve (`mensaje_operador`) cuando el trabajo termina. No se decide nada en la pantalla.
 */
import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type PublicacionFase2 } from "../api/cliente";
import { ProgresoDelTrabajo, useLanzarAccion } from "./generarPrompts";
import { Button } from "@/components/ui/button";

function MensajeDelTrabajo({ trabajo }: { trabajo: string }) {
  const detalle = useQuery({ queryKey: ["trabajo", trabajo], queryFn: () => api.trabajo(trabajo) });
  const estado = detalle.data?.estado;
  if (estado !== "EXITO" && estado !== "FALLIDO") return null;
  const unidad = (detalle.data?.unidades?.[0] ?? {}) as { json?: { mensaje_operador?: string } };
  const mensaje = unidad.json?.mensaje_operador;
  if (!mensaje) return null;
  return (
    <p
      role="status"
      data-testid="mensaje-verificacion"
      className={estado === "EXITO" ? "text-xs text-emerald-300" : "text-xs text-rose-300"}
    >
      {mensaje}
    </p>
  );
}

function BotonDeUnBrazo({ publicacion, clave }: { publicacion: PublicacionFase2; clave: string }) {
  const queryClient = useQueryClient();
  const { trabajo, error, lanzar } = useLanzarAccion(
    publicacion.accion_id,
    publicacion.parametros as Record<string, string>,
    false,
  );
  const recargar = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["fase2", clave] });
    queryClient.invalidateQueries({ queryKey: ["datos", clave] });
  }, [queryClient, clave]);

  return (
    <div className="space-y-1.5" data-testid={`verificar-${publicacion.brazo}`}>
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={lanzar.isPending || !!trabajo || !publicacion.habilitada}
        onClick={() => lanzar.mutate()}
      >
        {lanzar.isPending ? "Verificando…" : `Ya publiqué la campaña ${publicacion.brazo} — verificar`}
      </Button>
      {error && <p className="text-xs text-rose-300">{error}</p>}
      {trabajo && <ProgresoDelTrabajo trabajo={trabajo} alTerminar={recargar} />}
      {trabajo && <MensajeDelTrabajo trabajo={trabajo} />}
    </div>
  );
}

export function VerificarPublicadas({
  publicaciones,
  clave,
}: {
  publicaciones: PublicacionFase2[] | null | undefined;
  clave: string;
}) {
  if (!publicaciones || publicaciones.length === 0) return null;
  return (
    <div className="flex flex-wrap items-start gap-4" data-testid="verificar-publicadas">
      {publicaciones.map((p) => (
        <BotonDeUnBrazo key={p.brazo} publicacion={p} clave={clave} />
      ))}
    </div>
  );
}
