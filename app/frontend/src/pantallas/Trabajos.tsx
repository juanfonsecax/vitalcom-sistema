/**
 * Trabajos — todo lo que el runner está haciendo o hizo, y lo que espera de vos.
 *
 * La lista es de los trabajos (más nuevos primero). Al abrir uno: su estado en palabras (con el
 * código crudo al lado), el log en vivo, y —si está esperando— la orden completa para aprobar
 * o la pregunta de Claude para responder. Aprobar solo existe acá, con la orden a la vista: la
 * huella que viaja es la de lo que se está mirando, así que lo que se aprueba es lo que se vio.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import {
  api,
  ErrorDeContrato,
  type Pendiente,
  type Trabajo,
  type TrabajoDetalle,
} from "../api/cliente";
import { usarProgreso } from "../api/progreso";
import { Cargando, Chip, Problema, Tarjeta, cn } from "../componentes/ui";
import { LLAMADA_DE_META, SE_REINTENTAN, trabajoEnPalabras } from "../lenguaje";

const CADA_CUANTO_SE_MIRA_LA_LISTA_MS = 3000;

function EstadoDeTrabajo({ estado }: { estado: string }) {
  const { texto, tono } = trabajoEnPalabras(estado);
  return (
    <Chip tono={tono} titulo={estado}>
      {texto}
    </Chip>
  );
}

function hora(iso: string | null | undefined) {
  if (!iso) return "";
  const fecha = new Date(iso);
  return fecha.toLocaleString("es-GT", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function ListaDeTrabajos({ actual }: { actual: string | undefined }) {
  const lista = useQuery({
    queryKey: ["trabajos"],
    queryFn: api.trabajos,
    refetchInterval: CADA_CUANTO_SE_MIRA_LA_LISTA_MS,
  });
  if (lista.isPending) return <Cargando que="los trabajos" />;
  if (lista.error) return <Problema error={lista.error} />;
  if (lista.data.length === 0) {
    return <p className="text-sm text-zinc-500">No hay trabajos todavía. Cuando pidas una acción, aparece acá.</p>;
  }
  return (
    <ul className="space-y-2" aria-label="Trabajos">
      {lista.data.map((trabajo: Trabajo) => (
        <li key={trabajo.job_id}>
          <Link
            to="/trabajos/$id"
            params={{ id: trabajo.job_id }}
            className={cn(
              "block rounded-lg border p-3 text-sm hover:border-zinc-500",
              trabajo.job_id === actual ? "border-sky-700 bg-sky-950/30" : "border-zinc-800",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-zinc-100">{trabajo.rotulo || trabajo.accion_id}</span>
              <EstadoDeTrabajo estado={trabajo.estado} />
            </div>
            <div className="mt-1 flex justify-between text-xs text-zinc-500">
              <span>{trabajo.producto_key ?? "sin producto"}</span>
              <span>{hora(trabajo.iniciado)}</span>
            </div>
            {trabajo.pendiente && (
              <p className="mt-1 text-xs text-amber-300">
                {trabajo.pendiente === "aprobacion" ? "Falta tu aprobación" : "Claude te hizo una pregunta"}
              </p>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function OrdenParaAprobar({ id, pendiente }: { id: string; pendiente: Extract<Pendiente, { tipo: "aprobacion" }> }) {
  const cola = useQueryClient();
  const decidir = useMutation({
    mutationFn: (decision: "APROBADA" | "RECHAZADA") => api.aprobar(id, pendiente.orden_id, decision, pendiente.hash),
    onSettled: () => cola.invalidateQueries({ queryKey: ["trabajo", id] }),
  });
  const { orden } = pendiente;
  return (
    <Tarjeta className="space-y-4 border-amber-800 bg-amber-950/20">
      <div>
        <h2 className="font-medium text-amber-200">Esperando tu aprobación</h2>
        <p className="text-sm text-zinc-300">
          Esto es lo que se va a hacer en Meta, tal cual. <strong>Todo nace en pausa</strong>: no gasta hasta que lo
          actives. Si no aprobás, no pasa nada.
        </p>
      </div>
      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        {[
          ["Producto", orden.producto],
          ["Fase", orden.fase],
          ["Brazo", orden.brazo],
          ["Cuenta", orden.cuenta],
        ].map(([rotulo, valor]) => (
          <div key={rotulo}>
            <dt className="text-xs text-zinc-500">{rotulo}</dt>
            <dd className="text-zinc-100">{valor ?? "—"}</dd>
          </div>
        ))}
      </dl>
      <ol className="space-y-2" aria-label="Llamadas a Meta">
        {orden.llamadas.map((llamada) => (
          <li key={llamada.n} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
            <div className="flex items-baseline gap-2 text-sm">
              <span className="text-zinc-500">{llamada.n}.</span>
              <span className="font-medium text-zinc-100">{LLAMADA_DE_META[llamada.tool] ?? llamada.tool}</span>
              <code className="text-xs text-zinc-500">{llamada.tool}</code>
            </div>
            <pre className="mt-1 overflow-x-auto text-xs text-zinc-400">{JSON.stringify(llamada.args, null, 2)}</pre>
          </li>
        ))}
        {orden.llamadas.length === 0 && (
          <li className="text-sm text-zinc-400">Meta ya tiene todo: no hay nada nuevo que crear.</li>
        )}
      </ol>
      <p className="text-xs text-zinc-500">
        Huella de esta orden: <code>{pendiente.hash.slice(0, 12)}</code>. La aprobación vale {pendiente.caduca_horas} horas
        desde que la das; pasado ese tiempo se vuelve a pedir.
      </p>
      {decidir.error && <p className="text-sm text-rose-300">{decidir.error.message}</p>}
      <div className="flex gap-3">
        <button
          type="button"
          disabled={decidir.isPending}
          onClick={() => decidir.mutate("APROBADA")}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:bg-zinc-800"
        >
          Aprobar (queda en pausa)
        </button>
        <button
          type="button"
          disabled={decidir.isPending}
          onClick={() => decidir.mutate("RECHAZADA")}
          className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:border-zinc-500 disabled:opacity-50"
        >
          Rechazar
        </button>
      </div>
    </Tarjeta>
  );
}

function PreguntaDeClaude({ id, pendiente }: { id: string; pendiente: Extract<Pendiente, { tipo: "pregunta" }> }) {
  const cola = useQueryClient();
  const [texto, setTexto] = useState("");
  const responder = useMutation({
    mutationFn: () => api.responder(id, pendiente.n, texto),
    onSuccess: () => setTexto(""),
    onSettled: () => cola.invalidateQueries({ queryKey: ["trabajo", id] }),
  });
  return (
    <Tarjeta className="space-y-3 border-amber-800 bg-amber-950/20">
      <h2 className="font-medium text-amber-200">Claude necesita una decisión tuya</h2>
      <p className="whitespace-pre-wrap text-sm text-zinc-200">{pendiente.texto}</p>
      <textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        rows={3}
        aria-label="Tu respuesta"
        className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-600"
      />
      {responder.error && <p className="text-sm text-rose-300">{responder.error.message}</p>}
      <button
        type="button"
        disabled={responder.isPending || texto.trim() === ""}
        onClick={() => responder.mutate()}
        className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:bg-zinc-800 disabled:text-zinc-500"
      >
        Responder
      </button>
    </Tarjeta>
  );
}

function Acciones({ trabajo }: { trabajo: TrabajoDetalle }) {
  const cola = useQueryClient();
  const navegar = (id: string) => {
    window.location.assign(`/trabajos/${id}`);
  };
  const [seguro, setSeguro] = useState(false);
  const refrescar = () => cola.invalidateQueries({ queryKey: ["trabajos"] }).then(() => cola.invalidateQueries({ queryKey: ["trabajo", trabajo.job_id] }));
  const cancelar = useMutation({ mutationFn: () => api.cancelar(trabajo.job_id), onSettled: refrescar });
  const descartar = useMutation({ mutationFn: () => api.descartar(trabajo.job_id), onSettled: refrescar });
  const reintentar = useMutation({
    mutationFn: () => api.reintentar(trabajo.job_id, true),
    onSuccess: (nuevo) => navegar(nuevo.job_id),
  });
  const empezarDeNuevo = useMutation({
    mutationFn: () => api.pedirAccion(trabajo.accion_id, trabajo.parametros, true),
    onSuccess: (nuevo) => navegar(nuevo.job_id),
  });
  const { enCurso } = trabajoEnPalabras(trabajo.estado);
  const error = cancelar.error ?? descartar.error ?? reintentar.error ?? empezarDeNuevo.error;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-3">
        {trabajo.otra_version && (
          <>
            <button type="button" onClick={() => descartar.mutate()} className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:border-zinc-500">
              Marcar fallido
            </button>
            <button type="button" onClick={() => empezarDeNuevo.mutate()} className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500">
              Empezar de nuevo
            </button>
          </>
        )}
        {SE_REINTENTAN.includes(trabajo.estado) && (
          <button type="button" onClick={() => reintentar.mutate()} disabled={reintentar.isPending} className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50">
            Reintentar completo
          </button>
        )}
        {enCurso && !trabajo.otra_version && !seguro && (
          <button type="button" onClick={() => setSeguro(true)} className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:border-rose-700 hover:text-rose-300">
            Cancelar trabajo
          </button>
        )}
        {enCurso && !trabajo.otra_version && seguro && (
          <>
            <span className="self-center text-sm text-zinc-300">¿Seguro? Se corta lo que esté corriendo.</span>
            <button type="button" onClick={() => cancelar.mutate()} className="rounded-lg bg-rose-700 px-4 py-2 text-sm font-medium text-white hover:bg-rose-600">
              Sí, cancelar
            </button>
            <button type="button" onClick={() => setSeguro(false)} className="rounded-lg px-3 py-2 text-sm text-zinc-400 hover:text-zinc-100">
              No
            </button>
          </>
        )}
      </div>
      {trabajo.otra_version && (
        <p className="text-sm text-amber-300">
          Este trabajo quedó de una versión anterior de la app: el código ya no es el mismo, así que no se puede continuar.
          Marcalo como fallido o empezalo de nuevo con los mismos datos.
        </p>
      )}
      {SE_REINTENTAN.includes(trabajo.estado) && (
        <p className="text-xs text-zinc-500">
          Reintentar corre todo desde cero con los mismos datos. Una aprobación de antes no se hereda.
        </p>
      )}
      {error && <p className="text-sm text-rose-300">{error.message}</p>}
    </div>
  );
}

function Resultado({ trabajo }: { trabajo: TrabajoDetalle }) {
  const resultado = trabajo.resultado as {
    detalle?: string;
    flujo?: { falta_para_cumplir?: { dato: string; dueno?: string }[] } | null;
  } | null;
  if (!resultado) return null;
  const falta = resultado.flujo?.falta_para_cumplir ?? [];
  return (
    <Tarjeta className="space-y-2">
      <h2 className="font-medium text-zinc-100">Cómo terminó</h2>
      {resultado.detalle && <p className="text-sm text-zinc-300">{resultado.detalle}</p>}
      {falta.length > 0 && (
        <div>
          <p className="text-sm text-zinc-400">Lo que falta para dar el paso por cumplido:</p>
          <ul className="mt-1 space-y-1 text-sm text-zinc-200">
            {falta.map((f) => (
              <li key={f.dato}>
                · {f.dato}
                {f.dueno && <span className="text-zinc-500"> — lo produce: {f.dueno}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {trabajo.unidades.map((unidad, i) => {
        const u = unidad as { costo_equivalente_usd?: number | null; unidad_n?: number };
        return u.costo_equivalente_usd != null ? (
          <p key={i} className="text-xs text-zinc-500">
            Claude, paso {u.unidad_n ?? i + 1}: costo equivalente US${u.costo_equivalente_usd} en precio de API — con tu suscripción no
            se cobra.
          </p>
        ) : null;
      })}
      {trabajo.run_dir && (
        <p className="text-xs text-zinc-500">
          Rastro completo en <code>{trabajo.run_dir}</code>
        </p>
      )}
    </Tarjeta>
  );
}

function DetalleDeTrabajo({ id }: { id: string }) {
  const cola = useQueryClient();
  const detalle = useQuery({
    queryKey: ["trabajo", id],
    queryFn: () => api.trabajo(id),
    refetchInterval: (consulta) =>
      trabajoEnPalabras(consulta.state.data?.estado).enCurso ? 2000 : false,
  });
  const progreso = usarProgreso(id, () => {
    cola.invalidateQueries({ queryKey: ["trabajo", id] });
    cola.invalidateQueries({ queryKey: ["trabajos"] });
  });

  if (detalle.isPending) return <Cargando que="el trabajo" />;
  if (detalle.error) {
    const error = detalle.error;
    return <Problema error={error instanceof ErrorDeContrato ? error : new Error(String(error))} />;
  }
  const trabajo = detalle.data;
  const pendiente = trabajo.pendiente_completo as Pendiente | null;

  return (
    <div className="space-y-4">
      <header>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-semibold">{trabajo.rotulo || trabajo.accion_id}</h1>
          <EstadoDeTrabajo estado={trabajo.estado} />
          <code className="text-xs text-zinc-500">{trabajo.estado}</code>
        </div>
        <p className="text-sm text-zinc-500">
          {trabajo.producto_key ?? "sin producto"} · empezó {hora(trabajo.iniciado)}
          {trabajo.terminado ? ` · terminó ${hora(trabajo.terminado)}` : ""}
        </p>
      </header>

      {pendiente?.tipo === "aprobacion" && <OrdenParaAprobar id={id} pendiente={pendiente} />}
      {pendiente?.tipo === "pregunta" && <PreguntaDeClaude id={id} pendiente={pendiente} />}

      <Acciones trabajo={trabajo} />
      <Resultado trabajo={trabajo} />

      <Tarjeta className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-zinc-100">Lo que va pasando</h2>
          <span className="text-xs text-zinc-500">{progreso.conectado ? "en vivo" : "sin conexión en vivo"}</span>
        </div>
        <pre
          aria-label="Registro en vivo"
          className="max-h-96 overflow-auto rounded-lg bg-zinc-950 p-3 text-xs leading-relaxed"
        >
          {progreso.lineas.length === 0 && <span className="text-zinc-600">Todavía no hay líneas.</span>}
          {progreso.lineas.map((linea, i) => (
            <div
              key={i}
              className={cn(
                linea.tipo === "error" && "text-rose-300",
                linea.tipo === "comando" && "text-sky-300",
                linea.tipo === "claude" && "text-emerald-300",
                linea.tipo === "salida" && "text-zinc-300",
              )}
            >
              <span className="text-zinc-600">{linea.unidad}· </span>
              {linea.texto}
            </div>
          ))}
        </pre>
      </Tarjeta>
    </div>
  );
}

function EstadoDeClaude() {
  const claude = useQuery({ queryKey: ["claude"], queryFn: api.claude, staleTime: 60_000 });
  if (!claude.data) return null;
  return claude.data.logueado ? (
    <Chip tono="bien">Claude: sesión abierta</Chip>
  ) : (
    <Chip tono="alto" titulo={claude.data.detalle}>
      Claude: sin sesión — abrí una terminal, corré <code>claude</code> y <code>/login</code>
    </Chip>
  );
}

export function Trabajos() {
  const { id } = useParams({ strict: false }) as { id?: string };
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Trabajos</h1>
          <p className="text-sm text-zinc-400">Lo que la app está haciendo por vos, y lo que espera de vos.</p>
        </div>
        <EstadoDeClaude />
      </header>
      <p className="text-xs text-zinc-500">
        Si tenés una sesión de Claude Code abierta trabajando en el sistema, esperá a que termine antes de pedir una
        acción acá: no comparten turno de escritura.
      </p>
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <ListaDeTrabajos actual={id} />
        <div className="min-w-0">{id ? <DetalleDeTrabajo id={id} key={id} /> : <p className="text-sm text-zinc-500">Elegí un trabajo de la lista.</p>}</div>
      </div>
    </div>
  );
}
