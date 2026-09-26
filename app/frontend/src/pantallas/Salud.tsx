/**
 * Salud — qué dato está viejo y quién lo produce.
 *
 * Sale de `VISTAS/_ESTADO.json`, que arma `gen_app.py` mirando el `mtime` de cada archivo.
 * La app no calcula la edad: la muestra, junto con el comando que la refresca.
 */
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/cliente";
import { Cargando, Chip, Problema, Tarjeta, type Tono } from "../componentes/ui";

type EstadoVista = {
  existe: boolean;
  edad_dias?: number;
  clase?: string;
  etiqueta?: string;
  detalle?: string;
};

type Vista = {
  id: string;
  rotulo: string;
  sub?: string;
  dueno?: string;
  genera?: string;
  estado?: EstadoVista;
};

const TONO_POR_CLASE: Record<string, Tono> = {
  ok: "bien",
  tibia: "aviso",
  vieja: "alto",
  falta: "alto",
};

export function Salud() {
  const salud = useQuery({ queryKey: ["salud"], queryFn: api.salud });
  const sistema = useQuery({ queryKey: ["sistema"], queryFn: api.sistema });

  if (salud.isLoading) return <Cargando que="la salud del sistema" />;
  if (salud.error) return <Problema error={salud.error} />;

  const vistas = (salud.data?.vistas ?? []) as Vista[];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Salud del sistema</h1>
        <p className="text-sm text-zinc-400">
          Qué vista está fresca, de cuándo es y con qué comando se regenera. Generado el{" "}
          {salud.data?.generado}.
        </p>
        {sistema.data && (
          <p className="mt-1 font-mono text-[11px] text-zinc-400">
            corriendo sobre {sistema.data.base}
          </p>
        )}
      </header>

      <div className="grid gap-3 md:grid-cols-2">
        {vistas.map((vista) => (
          <Tarjeta key={vista.id} className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-zinc-100">{vista.rotulo}</p>
                <p className="text-xs text-zinc-400">{vista.sub}</p>
              </div>
              <Chip tono={TONO_POR_CLASE[vista.estado?.clase ?? ""] ?? "neutro"}>
                {vista.estado?.existe ? (vista.estado?.etiqueta ?? "sin fecha") : "no existe"}
              </Chip>
            </div>
            {vista.estado?.detalle && (
              <p className="text-xs text-zinc-400">{vista.estado.detalle}</p>
            )}
            {vista.dueno && <p className="text-xs text-zinc-400">Lo produce: {vista.dueno}</p>}
            {vista.genera && (
              <code className="rounded bg-zinc-950 px-2 py-1 text-[11px] text-zinc-400">
                {vista.genera}
              </code>
            )}
          </Tarjeta>
        ))}
      </div>
    </div>
  );
}
