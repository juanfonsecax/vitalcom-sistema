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
import { useEffect, useState, type CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, BellRing, ChevronDown } from "lucide-react";

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

/** Celebración (E3): las claves de los ángulos que acaban de entrar en ESCALAR respecto de
 * tu última visita. La comparación es de PANTALLA — qué estado se mostró la vez anterior
 * (localStorage) contra el que trae el motor hoy —, nada que el motor no haya dicho ya.
 * La primera visita no celebra: sin línea base no hay transición que celebrar. */
const CLAVE_CELEBRACION = "vitalcom-celebraciones-v1";

function usarEscalaresNuevos(ordenes: OrdenItem[]) {
  const [nuevos, setNuevos] = useState<string[]>([]);
  useEffect(() => {
    if (ordenes.length === 0) return;
    let previos: Record<string, string> = {};
    try {
      previos = JSON.parse(window.localStorage.getItem(CLAVE_CELEBRACION) ?? "{}") as Record<string, string>;
    } catch {
      previos = {};
    }
    const actuales: Record<string, string> = {};
    const recien: string[] = [];
    for (const orden of ordenes) {
      const clave = `${orden.producto_key}|${orden.angulo_key}`;
      actuales[clave] = orden.estado;
      if (
        orden.estado === "ESCALAR" &&
        !orden.bloqueo_fase &&
        previos[clave] !== undefined &&
        previos[clave] !== "ESCALAR"
      ) {
        recien.push(clave);
      }
    }
    try {
      window.localStorage.setItem(CLAVE_CELEBRACION, JSON.stringify(actuales));
    } catch {
      /* sin espacio en localStorage se pierde la celebración, nunca la pantalla */
    }
    if (recien.length > 0) setNuevos(recien);
  }, [ordenes]);
  return nuevos;
}

/** Las 16 piezas del confeti, fijas (sin azar): posiciones y giros predeterminados para que
 * la celebración sea igual en cada visita y no haya sorpresas entre navegadas. */
const CONFETI: { left: number; dx: number; giro: number; delay: number }[] = Array.from(
  { length: 16 },
  (_, i) => ({
    left: 6 + i * 6,
    dx: ((i * 7) % 29) - 14,
    giro: 120 + i * 15,
    delay: i * 16,
  }),
);

const COLORES_CONFETI = ["var(--estado-escalar)", "var(--estado-seguir)", "var(--primary)"];

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

/** Una tarjeta de orden: el mismo titular sin ambigüedad y el mismo glosario por ESTADO
 * que `Ordenes.tsx` (`lenguaje.ts`), nunca recalculados acá. El par CPA ↔ break-even es
 * el protagonista visual — es la pregunta que toda orden contesta — y el glosario queda
 * plegado en un "¿Qué es…?" para no tapar el número con prosa. Los botones Aprobar/Rechazar
 * que antes no hacían nada se reemplazan por UN camino claro: si la orden se puede ejecutar,
 * el botón manda a Trabajos, que es donde vive el flujo real de aprobación. */
function TarjetaOrdenDelDia({
  orden,
  cicloHabilitado,
  indice = 0,
  celebrar = false,
  trabajoPendiente,
}: {
  orden: OrdenItem;
  cicloHabilitado: boolean;
  indice?: number;
  celebrar?: boolean;
  trabajoPendiente?: string;
}) {
  const escalarBloqueado = orden.estado === "ESCALAR" && Boolean(orden.bloqueo_fase);
  const titulo = tituloDeOrden(orden.estado, orden.frase_simple, orden.bloqueo_fase);
  const glosarioDelEstado = glosarioDeOrden(orden.estado, orden.bloqueo_fase);
  const veredicto = veredictoDeOrden(orden.estado, orden.bloqueo_fase);
  const pq = orden.por_que ?? {};
  const clase = escalarBloqueado ? CLASE_ESTADO_ORDEN.SEGUIR_MIDIENDO : (CLASE_ESTADO_ORDEN[orden.estado] ?? "");
  const texto = escalarBloqueado ? "Escalar bloqueado por fase" : (TEXTO_ORDEN[orden.estado] ?? orden.estado);

  return (
    <Card
      data-testid="tarjeta-orden"
      className={`relative motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:fill-mode-backwards motion-safe:duration-300 motion-safe:transition-transform motion-safe:hover:-translate-y-0.5${celebrar ? " ring-1 ring-estado-escalar/40" : ""}`}
      style={{ animationDelay: `${Math.min(indice, 8) * 60}ms` }}
    >
      {celebrar && (
        <span data-testid="celebracion-escalar" className="celebracion" aria-hidden="true">
          {CONFETI.map((pieza, i) => (
            <span
              key={i}
              style={
                {
                  left: `${pieza.left}%`,
                  backgroundColor: COLORES_CONFETI[i % COLORES_CONFETI.length],
                  animationDelay: `${pieza.delay}ms`,
                  "--dx": `${pieza.dx}px`,
                  "--giro": `${pieza.giro}deg`,
                } as CSSProperties
              }
            />
          ))}
        </span>
      )}
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
        <CardTitle className="text-base font-semibold">{titulo}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {veredicto && <p className="text-sm text-muted-foreground">{veredicto}</p>}
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-border/60 bg-muted/30 p-3">
          <div>
            <span className="block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              CPA observado
            </span>
            <span className="text-xl font-semibold tabular-nums text-foreground">
              {pq.cpa_real_q != null ? `Q${pq.cpa_real_q}` : "Sin datos"}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              Break-even
            </span>
            <span className="text-xl font-semibold tabular-nums text-foreground">
              {pq.break_even_q != null ? `Q${pq.break_even_q}` : "No fijado"}
            </span>
          </div>
        </div>
        {glosarioDelEstado && (
          <Collapsible>
            <CollapsibleTrigger className="text-xs text-muted-foreground underline underline-offset-2 transition-colors hover:text-foreground">
              ¿Qué es «{glosarioDelEstado.rotulo}»?
            </CollapsibleTrigger>
            <CollapsibleContent>
              <p className="mt-1 text-xs text-muted-foreground">{glosarioDelEstado.que_es}</p>
            </CollapsibleContent>
          </Collapsible>
        )}
        {orden.bloqueo_fase && (
          <p className="rounded border border-estado-seguir/40 bg-estado-seguir/10 p-2 text-estado-seguir">
            <strong>Nota de fase:</strong> {orden.bloqueo_fase}
          </p>
        )}
      </CardContent>
      <div className="flex items-center justify-between gap-2 border-t px-(--card-spacing) pt-3 text-xs">
        <span className="text-muted-foreground">{orden.ejecutable ? "Listo para revisión" : "Solo informativo"}</span>
        {orden.ejecutable && cicloHabilitado ? (
          trabajoPendiente ? (
            <Button size="sm" render={<Link to="/trabajos/$id" params={{ id: trabajoPendiente }} />}>
              Revisar y aprobar en Trabajos
            </Button>
          ) : (
            <Button size="sm" render={<Link to="/trabajos" />}>
              Revisar y aprobar en Trabajos
            </Button>
          )
        ) : orden.ejecutable && !cicloHabilitado ? (
          <span className="text-right text-muted-foreground">Ejecución deshabilitada en el manifiesto</span>
        ) : null}
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

/** La franja que resume el día en un vistazo: cuántas órdenes piden cada acción, contadas de
 * las mismas órdenes que se pintan abajo (es contar tarjetas, no calcular el negocio: los
 * estados ya los decidió `decidir.py`). Si Trabajos tiene algo esperando al operador, se
 * avisa acá — antes ese aviso vivía solo en la insignia de Ajustes. */
const ETIQUETA_FRANJA: Record<string, string> = {
  PAUSAR: "pausar",
  ESCALAR: "escalar",
  RENOVAR: "renovar",
};

const CLASE_FRANJA: Record<string, string> = {
  PAUSAR: "text-estado-pausar",
  ESCALAR: "text-estado-escalar",
  RENOVAR: "text-estado-renovar",
};

function FranjaDelDia({
  ordenes,
  pendientesDeTrabajos,
}: {
  ordenes: OrdenItem[];
  pendientesDeTrabajos: number;
}) {
  const conteo: Record<string, number> = {};
  let enMedicion = 0;
  for (const orden of ordenes) {
    if (orden.estado === "SEGUIR_MIDIENDO") enMedicion += 1;
    else conteo[orden.estado] = (conteo[orden.estado] ?? 0) + 1;
  }
  const acciones = (["PAUSAR", "ESCALAR", "RENOVAR"] as const).filter((clave) => (conteo[clave] ?? 0) > 0);

  return (
    <div
      data-testid="franja-hoy"
      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card/60 p-4"
    >
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Hoy te toca</p>
        {acciones.length === 0 && enMedicion === 0 ? (
          <p className="mt-1 text-lg font-semibold">Ninguna acción sobre Meta</p>
        ) : (
          <p className="mt-1 flex flex-wrap items-baseline gap-x-5 gap-y-1 text-2xl font-bold">
            {acciones.map((clave) => (
              <span key={clave} className="flex items-baseline gap-1">
                <span className={`tabular-nums ${CLASE_FRANJA[clave]}`}>{conteo[clave]}</span>
                <span className="text-sm font-semibold text-muted-foreground">{ETIQUETA_FRANJA[clave]}</span>
              </span>
            ))}
            {enMedicion > 0 && (
              <span className="flex items-baseline gap-1">
                <span className="tabular-nums text-estado-seguir">{enMedicion}</span>
                <span className="text-sm font-semibold text-muted-foreground">midiendo</span>
              </span>
            )}
          </p>
        )}
      </div>
      {pendientesDeTrabajos > 0 && (
        <Link
          to="/trabajos"
          className="inline-flex items-center gap-2 rounded-lg border border-estado-seguir/40 bg-estado-seguir/10 px-3 py-1.5 text-sm text-estado-seguir transition-colors hover:bg-estado-seguir/20"
        >
          <BellRing className="size-4" />
          {pendientesDeTrabajos} {pendientesDeTrabajos === 1 ? "espera" : "esperan"} tu revisión en Trabajos
        </Link>
      )}
    </div>
  );
}

/** Sección 2: las órdenes de hoy. Agrupa por si piden una acción o no — nunca reordena por
 * número, solo por ESTADO (invariante 13: la conversación corta, nunca corona). */
function SeccionOrdenes() {
  const ordenesQuery = useQuery({ queryKey: ["ordenes"], queryFn: () => api.ordenes() });
  const accionesQuery = useQuery({ queryKey: ["acciones"], queryFn: () => api.acciones() });
  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const ordenes = ordenesQuery.data?.ordenes ?? [];
  const recienEscalaron = usarEscalaresNuevos(ordenes);

  if (ordenesQuery.isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (ordenesQuery.error) return <Problema error={ordenesQuery.error} />;

  const accionCiclo = (accionesQuery.data ?? []).find((a) => a.id === ACCION_CICLO_ORDENES);
  const cicloHabilitado = accionCiclo?.habilitada ?? false;
  const pendientes = (trabajos.data ?? []).filter((t) => t.pendiente).length;

  /** Si el producto ya tiene un trabajo esperando aprobación, el botón de su orden lleva
   * directo a ESE trabajo (el más nuevo primero) en vez de a la lista general. La
   * aprobación sigue existiendo una sola vez — en Trabajos, con la orden a la vista y
   * confirmación orden por orden; acá solo se acorta el camino, nunca se aprueba directo. */
  const trabajoPendientePorProducto = new Map<string, string>();
  for (const t of trabajos.data ?? []) {
    if (t.pendiente && t.producto_key && !trabajoPendientePorProducto.has(t.producto_key)) {
      trabajoPendientePorProducto.set(t.producto_key, t.job_id);
    }
  }

  const accionables = ordenes
    .filter((o) => o.estado !== "SEGUIR_MIDIENDO")
    .sort((a, b) => (PRIORIDAD_ACCIONABLE[a.estado] ?? 99) - (PRIORIDAD_ACCIONABLE[b.estado] ?? 99));
  const enMedicion = ordenes.filter((o) => o.estado === "SEGUIR_MIDIENDO");

  return (
    <div className="space-y-4">
      <FranjaDelDia ordenes={ordenes} pendientesDeTrabajos={pendientes} />

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
              indice={i}
              celebrar={recienEscalaron.includes(`${orden.producto_key}|${orden.angulo_key}`)}
              trabajoPendiente={trabajoPendientePorProducto.get(orden.producto_key)}
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
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-lg font-semibold">Órdenes de hoy</h2>
          <Link
            to="/ordenes"
            className="shrink-0 text-xs text-muted-foreground underline-offset-2 transition-colors hover:text-foreground hover:underline"
          >
            Detalle extendido del motor en Órdenes →
          </Link>
        </div>
        <SeccionOrdenes />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Qué sigue en cada producto</h2>
        <SeccionSiguientePaso />
      </section>
    </div>
  );
}
