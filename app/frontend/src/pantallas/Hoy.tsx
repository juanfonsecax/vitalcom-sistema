/**
 * Hoy.tsx — pantalla de entrada («/»): las tres preguntas del día, en el orden que fija la
 * metodología (CLAUDE.md, invariante 13), no la preferencia de diseño:
 *   1. ¿Está fresca la data?     banner de rezago de `_DECISIONES.json`, arriba de todo.
 *   2. ¿Qué ordena el motor hoy?  las órdenes de `decidir.py` (`/api/ordenes`), accionables
 *      primero (PAUSAR, ESCALAR, RENOVAR); SEGUIR_MIDIENDO queda colapsado, porque solo dice
 *      "esperá".
 *   3. ¿Qué sigue en cada producto?  el nodo de `flujo.py` (`/api/productos`), con su
 *      bloqueante y quién lo produce.
 *
 * La pantalla no calcula ni decide nada: cada número y cada estado salen tal cual del
 * contrato. Reutiliza las mismas piezas de traducción de `lenguaje.ts` y `componentes/resumen.tsx`
 * que ya usan `Ordenes.tsx` y `Tablero.tsx`, para no fijar una tercera vez la misma regla de
 * negocio (glosario por estado, título sin ambigüedad de una orden ESCALAR bloqueada, quién
 * hace cada paso).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, ChevronDown } from "lucide-react";

import { api, type OrdenItem, type Producto } from "../api/cliente";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { tituloDelPasoActual } from "../componentes/resumen";
import { Problema } from "../componentes/ui";
import {
  glosarioDeOrden,
  progresoVentasEnPalabras,
  quienLoHace,
  TEXTO_ORDEN,
  tituloDeOrden,
  ventasFaltantesEnPalabras,
  veredictoDeOrden,
} from "../lenguaje";

/** La acción declarada del ciclo de recolección nocturna (skill `recopilar-lucidsales`,
 * `VISTAS/_MANIFIESTO.json` → `nodo.ciclo.datos`). Si el manifiesto no la trae, no se inventa
 * un botón: el banner solo avisa. */
const ACCION_REFRESCAR_DATOS = "nodo.ciclo.datos";
const ACCION_CICLO_ORDENES = "nodo.ciclo.ordenes";

/** El orden fijo de las órdenes accionables (invariante 13): PAUSAR corta primero, ESCALAR y
 * RENOVAR ponen o mueven plata. SEGUIR_MIDIENDO nunca entra acá — significa "todavía no". */
const PRIORIDAD_ACCIONABLE: Record<string, number> = { PAUSAR: 0, ESCALAR: 1, RENOVAR: 2 };

/** El color de cada estado de orden con los tokens de status del sistema (T1,
 * `src/estilos.css`): uno por `decidir.py`, nunca reinventado por pantalla. Una celda ESCALAR
 * bloqueada por fase toma el color de "esperar" (ámbar), no el de escalar. */
const CLASE_ESTADO_ORDEN: Record<string, string> = {
  ESCALAR: "bg-estado-escalar text-estado-escalar-foreground",
  PAUSAR: "bg-estado-pausar text-estado-pausar-foreground",
  RENOVAR: "bg-estado-renovar text-estado-renovar-foreground",
  SEGUIR_MIDIENDO: "bg-estado-seguir text-estado-seguir-foreground",
};

/** El banner de rezago de arriba de todo: sale de `_DECISIONES.json`, no de las órdenes. Un
 * `rezago_dias` ausente se trata como desconocido — nunca como "fresco". */
function BannerDatos() {
  const decisiones = useQuery({ queryKey: ["decisiones"], queryFn: api.decisiones });
  const acciones = useQuery({ queryKey: ["acciones"], queryFn: () => api.acciones() });
  const cola = useQueryClient();
  const refrescar = useMutation({
    mutationFn: () => api.pedirAccion(ACCION_REFRESCAR_DATOS, {}, false),
    onSuccess: () => cola.invalidateQueries({ queryKey: ["decisiones"] }),
  });

  if (decisiones.isLoading) return <Skeleton className="h-14 w-full" />;
  if (decisiones.error) return <Problema error={decisiones.error} />;

  const rezago = decisiones.data?.rezago_dias ?? null;
  const datosHasta = decisiones.data?.datos_hasta;
  const stale = rezago === null || rezago > 2;

  if (!stale) {
    return (
      <p className="text-sm text-muted-foreground">
        Datos hasta {datosHasta || "—"}.
      </p>
    );
  }

  const accionRefrescar = (acciones.data ?? []).find((a) => a.id === ACCION_REFRESCAR_DATOS);

  return (
    <Alert variant="destructive">
      <AlertTriangle />
      <AlertTitle>Las órdenes de hoy están calculadas sobre datos viejos</AlertTitle>
      <AlertDescription>
        <p>
          {rezago === null
            ? "El motor no pudo decir hace cuánto no llega data nueva de ventas."
            : `Datos hasta ${datosHasta || "fecha desconocida"} — ${rezago} día${rezago === 1 ? "" : "s"} de rezago.`}{" "}
          Refrescá la data antes de actuar sobre estas órdenes: una decisión sobre data vieja es
          una decisión a ciegas (invariante 13).
        </p>
        {accionRefrescar && (
          <div className="mt-2">
            <Button
              size="sm"
              disabled={!accionRefrescar.habilitada || refrescar.isPending}
              onClick={() => refrescar.mutate()}
              title={accionRefrescar.habilitada ? undefined : (accionRefrescar.motivo ?? undefined)}
            >
              {refrescar.isPending ? "Pidiendo…" : accionRefrescar.rotulo}
            </Button>
            {refrescar.isSuccess && (
              <p className="mt-1 text-xs text-muted-foreground">
                Encolado. Seguí el progreso en{" "}
                <Link to="/trabajos" className="underline">
                  Trabajos
                </Link>
                .
              </p>
            )}
            {refrescar.isError && (
              <p className="mt-1 text-xs text-destructive">
                {refrescar.error instanceof Error ? refrescar.error.message : String(refrescar.error)}
              </p>
            )}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}

/** Una tarjeta de orden, compacta: el mismo titular sin ambigüedad y el mismo glosario por
 * ESTADO que `Ordenes.tsx` (`lenguaje.ts`), nunca recalculados acá. */
function TarjetaOrdenDelDia({ orden, cicloHabilitado }: { orden: OrdenItem; cicloHabilitado: boolean }) {
  const escalarBloqueado = orden.estado === "ESCALAR" && Boolean(orden.bloqueo_fase);
  const titulo = tituloDeOrden(orden.estado, orden.frase_simple, orden.bloqueo_fase);
  const glosarioDelEstado = glosarioDeOrden(orden.estado, orden.bloqueo_fase);
  const veredicto = veredictoDeOrden(orden.estado, orden.bloqueo_fase);
  const pq = orden.por_que ?? {};
  const clase = escalarBloqueado ? CLASE_ESTADO_ORDEN.SEGUIR_MIDIENDO : (CLASE_ESTADO_ORDEN[orden.estado] ?? "");
  const texto = escalarBloqueado ? "Escalar bloqueado por fase" : (TEXTO_ORDEN[orden.estado] ?? orden.estado);

  return (
    <Card>
      <CardHeader className="gap-2">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <Link
              to="/producto/$clave"
              params={{ clave: orden.producto_key }}
              className="truncate font-medium hover:underline"
            >
              {orden.producto_key}
            </Link>
            <p className="truncate text-xs text-muted-foreground">
              {orden.angulo_nombre || orden.angulo_key}
            </p>
          </div>
          <Badge variant="outline" className={`shrink-0 border-transparent ${clase}`}>
            {texto}
          </Badge>
        </div>
        <CardTitle className="text-sm font-semibold">{titulo}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-muted-foreground">
        {veredicto && <p>{veredicto}</p>}
        {glosarioDelEstado && (
          <p>
            <strong className="text-foreground">{glosarioDelEstado.rotulo}:</strong> {glosarioDelEstado.que_es}
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="block">CPA observado</span>
            <span className="font-medium text-foreground">
              {pq.cpa_real_q != null ? `Q${pq.cpa_real_q}` : "Sin datos"}
            </span>
          </div>
          <div>
            <span className="block">Break-even</span>
            <span className="font-medium text-foreground">
              {pq.break_even_q != null ? `Q${pq.break_even_q}` : "No fijado"}
            </span>
          </div>
        </div>
        {orden.bloqueo_fase && (
          <p className="rounded border border-estado-seguir/40 bg-estado-seguir/10 p-2 text-estado-seguir-foreground">
            <strong>Nota de fase:</strong> {orden.bloqueo_fase}
          </p>
        )}
      </CardContent>
      <div className="flex items-center justify-between border-t px-(--card-spacing) pt-3 text-xs">
        <span className="text-muted-foreground">{orden.ejecutable ? "Listo para revisión" : "Solo informativo"}</span>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!cicloHabilitado || !orden.ejecutable}
            title={!cicloHabilitado ? "Ejecución deshabilitada en manifiesto" : "Rechazar orden"}
          >
            Rechazar
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={!cicloHabilitado || !orden.ejecutable}
            title={!cicloHabilitado ? "Ejecución deshabilitada en manifiesto" : "Aprobar orden en Meta"}
          >
            Aprobar
          </Button>
        </div>
      </div>
    </Card>
  );
}

/** Una fila resumida de SEGUIR_MIDIENDO: solo dice cuánto falta, sin repetir la tarjeta entera —
 * el bloque colapsado existe para no tapar las órdenes que sí piden una acción hoy. */
function FilaEnMedicion({ orden }: { orden: OrdenItem }) {
  const pq = orden.por_que ?? {};
  const progreso =
    pq.ventas_actual != null && pq.ventas_necesarias != null
      ? progresoVentasEnPalabras(pq.ventas_actual as number, pq.ventas_necesarias as number)
      : ventasFaltantesEnPalabras(pq.faltan_ventas as number | null | undefined, orden.estado);
  return (
    <li className="flex items-center justify-between gap-3 border-b border-border/60 px-3 py-2 text-sm last:border-b-0">
      <div className="min-w-0">
        <Link to="/producto/$clave" params={{ clave: orden.producto_key }} className="font-medium hover:underline">
          {orden.producto_key}
        </Link>
        <span className="ml-2 text-muted-foreground">{orden.angulo_nombre || orden.angulo_key}</span>
      </div>
      <span className="shrink-0 text-xs text-muted-foreground">{progreso}</span>
    </li>
  );
}

/** Sección 2: las órdenes de hoy. Agrupa por si piden una acción o no — nunca reordena por
 * número, solo por ESTADO (invariante 13: la conversación corta, nunca corona). */
function SeccionOrdenes() {
  const ordenesQuery = useQuery({ queryKey: ["ordenes"], queryFn: () => api.ordenes() });
  const accionesQuery = useQuery({ queryKey: ["acciones"], queryFn: () => api.acciones() });

  if (ordenesQuery.isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (ordenesQuery.error) return <Problema error={ordenesQuery.error} />;

  const ordenes = ordenesQuery.data?.ordenes ?? [];
  const accionCiclo = (accionesQuery.data ?? []).find((a) => a.id === ACCION_CICLO_ORDENES);
  const cicloHabilitado = accionCiclo?.habilitada ?? false;

  const accionables = ordenes
    .filter((o) => o.estado !== "SEGUIR_MIDIENDO")
    .sort((a, b) => (PRIORIDAD_ACCIONABLE[a.estado] ?? 99) - (PRIORIDAD_ACCIONABLE[b.estado] ?? 99));
  const enMedicion = ordenes.filter((o) => o.estado === "SEGUIR_MIDIENDO");

  return (
    <div className="space-y-4">
      {accionables.length === 0 ? (
        <Card>
          <CardContent className="py-6 text-center text-sm text-muted-foreground">
            No hay órdenes que pidan una acción hoy. El motor midió y todas las celdas siguen su
            curso.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {accionables.map((orden, i) => (
            <TarjetaOrdenDelDia
              key={`${orden.producto_key}-${orden.angulo_key}-${i}`}
              orden={orden}
              cicloHabilitado={cicloHabilitado}
            />
          ))}
        </div>
      )}

      {enMedicion.length > 0 && (
        <Collapsible>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm text-muted-foreground hover:bg-muted/50">
            <span>Siguen midiendo ({enMedicion.length})</span>
            <ChevronDown className="size-4" />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <ul className="mt-2 rounded-lg border">
              {enMedicion.map((orden, i) => (
                <FilaEnMedicion key={`${orden.producto_key}-${orden.angulo_key}-${i}`} orden={orden} />
              ))}
            </ul>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}

/** Una fila de "qué sigue": producto, fase, paso vigente y el primer bloqueante con su dueño.
 * Comparte `tituloDelPasoActual`/`quienLoHace` con `Tablero.tsx` — el mismo dato, nunca
 * recalculado. */
function FilaSiguientePaso({ producto }: { producto: Producto }) {
  const flujo = useQuery({ queryKey: ["flujo", producto.producto_key], queryFn: () => api.producto(producto.producto_key) });
  const nodos = flujo.data?.nodos;
  const paso = tituloDelPasoActual(nodos, flujo.data?.nodo_actual ?? producto.nodo_actual, flujo.data?.como);
  const quien = quienLoHace(flujo.data?.ejecutor || producto.siguiente_ejecutor);
  const bloqueantes = flujo.data?.bloqueantes ?? [];
  const primero = bloqueantes[0];

  return (
    <Link
      to="/producto/$clave"
      params={{ clave: producto.producto_key }}
      className="flex flex-col gap-1 border-b border-border/60 px-3 py-2 text-sm last:border-b-0 hover:bg-muted/50 sm:grid sm:grid-cols-[1fr_5rem_1fr_1fr] sm:items-center sm:gap-3"
    >
      <span className="font-medium">{producto.nombre_display || producto.producto_key}</span>
      <span className="text-xs text-muted-foreground">{producto.fase ?? "—"}</span>
      <span className="truncate text-muted-foreground">
        {flujo.isLoading ? <Skeleton className="h-4 w-32" /> : paso}
      </span>
      <span className="truncate text-xs text-muted-foreground">
        {flujo.isLoading ? (
          <Skeleton className="h-4 w-24" />
        ) : bloqueantes.length === 0 ? (
          "Sin bloqueantes"
        ) : (
          `${primero!.dato} · lo produce ${primero!.dueno || quien}${bloqueantes.length > 1 ? ` (+${bloqueantes.length - 1} más)` : ""}`
        )}
      </span>
    </Link>
  );
}

/** Sección 3: el nodo vigente de cada producto (`flujo.py`), qué lo frena y quién lo produce. */
function SeccionSiguientePaso() {
  const productos = useQuery({ queryKey: ["productos"], queryFn: api.productos });

  if (productos.isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }
  if (productos.error) return <Problema error={productos.error} />;

  const lista = productos.data ?? [];
  if (lista.length === 0) {
    return <p className="text-sm text-muted-foreground">Todavía no hay productos cargados.</p>;
  }

  return (
    <div className="rounded-lg border">
      {lista.map((producto) => (
        <FilaSiguientePaso key={producto.producto_key} producto={producto} />
      ))}
    </div>
  );
}

export function Hoy() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Hoy</h1>
        <p className="text-sm text-muted-foreground">
          Lo que hay que mirar para operar el día: la data, las órdenes del motor y qué sigue en
          cada producto.
        </p>
      </header>

      <section>
        <BannerDatos />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Órdenes de hoy</h2>
        <SeccionOrdenes />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Qué sigue en cada producto</h2>
        <SeccionSiguientePaso />
      </section>
    </div>
  );
}
