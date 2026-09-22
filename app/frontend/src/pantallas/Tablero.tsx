/**
 * Tablero — la primera pantalla: una tarjeta por producto que contesta tres preguntas.
 *   1. ¿Dónde estoy?    fase y paso vigentes (derivados, nunca declarados a mano)
 *   2. ¿Qué me frena?   los bloqueantes, con el nombre de quien produce el dato que falta
 *   3. ¿Qué sigue?      el ejecutor que declara el grafo
 * Más la edad de la data, porque una orden fresca sobre data vieja es una orden a ciegas.
 */
import { useQueries, useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, type Flujo, type Producto } from "../api/cliente";
import { AvisosDelRecorrido, BannerRezago, tituloDelPasoActual, type MotorInfo } from "../componentes/resumen";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";
import type { ClaveGlosario } from "../glosario";
import { ESTADO_PRODUCTO, estadoEnPalabras, faseEnUnaFrase, quienLoHace, rezagoEnPalabras } from "../lenguaje";

/** La clave del glosario para la fase, o `undefined` si `producto.fase` no es F1/F2/F3 (p. ej.
 * "PAUSADO" en un producto excepcionado como VARICOSE): sin fase válida, no hay (i) que mostrar. */
function claveGlosarioDeFase(fase: string | null | undefined): ClaveGlosario | undefined {
  if (fase === "F1") return "fase_1";
  if (fase === "F2") return "fase_2";
  if (fase === "F3") return "fase_3";
  return undefined;
}

/** La tarjeta de UN producto: en qué fase está, qué significa, quién sigue y qué lo frena.
 * Comparte con el resumen de ProductoDetalle las piezas de `componentes/resumen.tsx`
 * (`MotorInfo`, el título del paso y el banner de rezago) — no se llaman entre sí. */
export function TarjetaProducto({ producto, flujo }: { producto: Producto; flujo?: Flujo }) {
  const estado = estadoEnPalabras(producto.estado_flujo);
  const bloqueantes = flujo?.bloqueantes ?? [];
  const falta = flujo?.falta_para_cumplir ?? [];
  const motor = (flujo?.motor ?? null) as MotorInfo | null;
  const tituloDelPaso = tituloDelPasoActual(flujo?.nodos, flujo?.nodo_actual, flujo?.como);
  const ejecutorCrudo = flujo?.ejecutor || producto.siguiente_ejecutor || "";
  const quien = quienLoHace(ejecutorCrudo);
  const claveFase = claveGlosarioDeFase(producto.fase);

  return (
    <Tarjeta className="flex flex-col gap-4">
      <BannerRezago
        motor={motor}
        className="rounded-lg border border-amber-800 bg-amber-950/40 px-3 py-2 text-xs text-amber-200"
      />

      <div className="flex items-start justify-between gap-3">
        <div>
          <Link
            to="/producto/$clave"
            params={{ clave: producto.producto_key }}
            className="text-lg font-semibold text-zinc-100 hover:text-sky-300"
          >
            {producto.nombre_display || producto.producto_key}
          </Link>
          <p className="text-xs text-zinc-500">
            {producto.producto_key} · {producto.cuenta_alias || "sin cuenta"}
          </p>
        </div>
        <Chip tono={ESTADO_PRODUCTO[producto.estado] ?? "neutro"}>{producto.estado.toLowerCase()}</Chip>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-zinc-500">
          En qué fase está
          {claveFase && <Info termino={claveFase} />}
        </p>
        <p className="mt-1 text-sm text-zinc-200">{faseEnUnaFrase(producto.fase)}</p>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-zinc-500">
          El paso de ahora — y qué sigue
          <Info termino="nodo" />
        </p>
        <p className="mt-1 text-sm text-zinc-200">
          {tituloDelPaso} <Chip tono={estado.tono}>{estado.texto}</Chip>
        </p>
        <p className="mt-1 text-xs text-zinc-500">{quien}</p>
        {ejecutorCrudo && <p className="text-xs text-zinc-600">{ejecutorCrudo}</p>}
        {producto.nodo_actual && (
          <p className="mt-1 font-mono text-[11px] text-zinc-600" title="Id interno del paso en el grafo">
            {producto.nodo_actual}
          </p>
        )}
      </div>

      <div>
        <p className="text-xs uppercase tracking-wide text-zinc-500">
          Esto te bloquea
          <Info termino="bloqueante" />
        </p>
        {bloqueantes.length === 0 ? (
          <p className="mt-1 text-sm text-emerald-300">
            Nada lo frena.
            {falta.length > 0 && (
              <span className="text-zinc-400">
                {" "}
                Al terminar, este paso deja {falta.length} dato{falta.length > 1 ? "s" : ""} que
                todavía no {falta.length > 1 ? "existen" : "existe"}.
              </span>
            )}
          </p>
        ) : (
          <ul className="mt-1 space-y-1">
            {bloqueantes.map((b) => (
              <li key={b.dato} className="text-sm text-zinc-200">
                {b.dato}
                <span className="block text-xs text-zinc-500">
                  {b.observado} · lo produce {b.dueno}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <AvisosDelRecorrido avisos={flujo?.avisos} variante="compacta" />

      <p className="text-[11px] text-zinc-600">Evaluado el {producto.evaluado_el ?? "—"}</p>
    </Tarjeta>
  );
}

export function Tablero() {
  const productos = useQuery({ queryKey: ["productos"], queryFn: api.productos });
  const decisiones = useQuery({ queryKey: ["decisiones"], queryFn: api.decisiones });
  const detalles = useQueries({
    queries: (productos.data ?? []).map((p) => ({
      queryKey: ["flujo", p.producto_key],
      queryFn: () => api.producto(p.producto_key),
    })),
  });

  if (productos.isLoading) return <Cargando que="el portafolio" />;
  if (productos.error) return <Problema error={productos.error} />;

  const rezago = rezagoEnPalabras(decisiones.data?.rezago_dias);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Portafolio</h1>
          <p className="text-sm text-zinc-400">
            Dónde está cada producto, qué lo bloquea y qué sigue. La fase se deriva de la data;
            nadie la declara a mano.
          </p>
        </div>
        <Chip tono={rezago.tono} titulo="Hasta cuándo llega la data de ventas">
          {rezago.texto}
          {decisiones.data?.datos_hasta ? ` (hasta ${decisiones.data.datos_hasta})` : ""}
        </Chip>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(productos.data ?? []).map((producto, i) => (
          <TarjetaProducto
            key={producto.producto_key}
            producto={producto}
            flujo={detalles[i]?.data}
          />
        ))}
      </div>
    </div>
  );
}
