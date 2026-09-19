/**
 * Producto — la línea de tiempo F1 → F2 → F3 con el paso actual resaltado.
 *
 * Todo lo que se ve sale de `flujo.py <pk> --json`: los pasos, su estado, lo que cada uno
 * produce y quién es el dueño de cada dato. La pantalla no reordena ni completa nada.
 */
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { api, type Nodo, type Requisito } from "../api/cliente";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";
import { FASES, estadoEnPalabras, pasoCorto, quienLoHace } from "../lenguaje";

function Dato({ requisito }: { requisito: Requisito }) {
  return (
    <li className="flex gap-2 text-sm">
      <span className={requisito.ok ? "text-emerald-400" : "text-rose-400"}>
        {requisito.ok ? "✓" : "✗"}
      </span>
      <span>
        <span className="text-zinc-200">{requisito.dato}</span>
        <span className="block text-xs text-zinc-500">
          {requisito.observado}
          {requisito.dueno && <> · lo produce {requisito.dueno}</>}
        </span>
      </span>
    </li>
  );
}

function Paso({ nodo, esActual }: { nodo: Nodo; esActual: boolean }) {
  const estado = estadoEnPalabras(nodo.estado);
  return (
    <Tarjeta
      className={
        esActual
          ? "border-sky-700 bg-sky-950/30 ring-1 ring-sky-800"
          : nodo.estado === "NO_APLICA"
            ? "opacity-50"
            : undefined
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-medium text-zinc-100">
          {esActual && <span className="mr-2 text-sky-400">▸ estás acá</span>}
          {nodo.titulo || pasoCorto(nodo.id)}
        </h3>
        <Chip tono={estado.tono}>{estado.texto}</Chip>
      </div>
      <p className="mt-1 font-mono text-[11px] text-zinc-600">{nodo.id}</p>
      <p className="mt-2 text-sm text-zinc-400">{nodo.como}</p>
      <p className="mt-2 text-xs text-zinc-500">
        {quienLoHace(nodo.ejecutor_tipo)} · {nodo.ejecutor}
      </p>
      {nodo.produce.length > 0 && (
        <ul className="mt-3 space-y-2 border-t border-zinc-800 pt-3">
          {nodo.produce.map((r) => (
            <Dato key={r.dato} requisito={r} />
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

export function ProductoDetalle() {
  const { clave } = useParams({ from: "/producto/$clave" });
  const flujo = useQuery({ queryKey: ["flujo", clave], queryFn: () => api.producto(clave) });

  if (flujo.isLoading) return <Cargando que={`el recorrido de ${clave}`} />;
  if (flujo.error) return <Problema error={flujo.error} />;
  const d = flujo.data!;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <Link to="/" className="text-xs text-zinc-500 hover:text-zinc-300">
            ← portafolio
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">{d.nombre || d.producto_key}</h1>
          <p className="text-sm text-zinc-400">
            {d.fase_titulo} · paso actual <span className="font-mono">{d.nodo_actual}</span>
          </p>
        </div>
        <Link
          to="/producto/$clave/fase1"
          params={{ clave }}
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500"
        >
          Pantalla FASE 1 →
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {FASES.map((fase) => (
          <div
            key={fase.id}
            className={`flex-1 rounded-lg border p-3 ${
              d.fase === fase.id
                ? "border-sky-700 bg-sky-950/40"
                : "border-zinc-800 bg-zinc-900/40 opacity-60"
            }`}
          >
            <p className="text-sm font-medium text-zinc-100">
              {fase.rotulo}
              <Info termino={fase.id === "F1" ? "fase_1" : fase.id === "F2" ? "fase_2" : "fase_3"} />
            </p>
            <p className="text-xs text-zinc-500">{fase.que}</p>
          </div>
        ))}
      </div>

      {d.entradas.length > 0 && (
        <Tarjeta>
          <p className="text-xs uppercase tracking-wide text-zinc-500">
            Para pasar a la fase siguiente
            <Info termino="ganador_por_venta" />
          </p>
          <ul className="mt-2 space-y-2">
            {(d.entradas as Requisito[]).map((e, i) => (
              <Dato key={i} requisito={e} />
            ))}
          </ul>
        </Tarjeta>
      )}

      {d.bloqueantes.length > 0 && (
        <Tarjeta className="border-rose-900 bg-rose-950/30">
          <p className="text-sm font-medium text-rose-200">Esto frena el paso de ahora</p>
          <ul className="mt-2 space-y-2">
            {d.bloqueantes.map((b) => (
              <Dato key={b.dato} requisito={b} />
            ))}
          </ul>
        </Tarjeta>
      )}

      <div className="space-y-3">
        {d.nodos.map((nodo) => (
          <Paso key={nodo.id} nodo={nodo} esActual={nodo.id === d.nodo_actual} />
        ))}
      </div>
    </div>
  );
}
