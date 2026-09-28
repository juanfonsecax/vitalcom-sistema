/**
 * Hoy.tsx — pantalla de entrada («/»): las tres preguntas del día, en el orden que fija la
 * metodología (CLAUDE.md, invariante 13), no la preferencia de diseño:
 *   1. ¿Está fresca la data?     banner de rezago de `_DECISIONES.json`, arriba de todo.
 *   2. ¿Qué ordena el motor hoy?  las órdenes de `decidir.py` (`/api/ordenes`), accionables
 *      primero (PAUSAR, ESCALAR, RENOVAR), agrupadas en una sección por estado — la tarjeta
 *      grande de cada estado (arriba) baja hasta la suya; SEGUIR_MIDIENDO queda colapsado,
 *      porque solo dice "esperá", y su tarjeta es la que lo abre.
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
import {
  AlertTriangle,
  BellRing,
  ChevronDown,
  CircleCheck,
  Hourglass,
  Power,
  RefreshCw,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import { api, type OrdenItem, type Producto } from "../api/cliente";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { tituloDelPasoActual } from "../componentes/resumen";
import { cn, Problema } from "../componentes/ui";
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

/** El filete de color a la izquierda de cada tarjeta de orden: el estado se lee de reojo,
 * antes de leer una sola palabra. Una celda ESCALAR bloqueada por fase toma el filete de
 * "esperar" (ámbar), igual que su badge. */
const FILETE_ESTADO_ORDEN: Record<string, string> = {
  ESCALAR: "border-l-estado-escalar",
  PAUSAR: "border-l-estado-pausar",
  RENOVAR: "border-l-estado-renovar",
  SEGUIR_MIDIENDO: "border-l-estado-seguir",
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
      className={cn(
        "relative border-l-4 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:fill-mode-backwards motion-safe:duration-300 motion-safe:transition-transform motion-safe:hover:-translate-y-0.5",
        escalarBloqueado ? FILETE_ESTADO_ORDEN.SEGUIR_MIDIENDO : (FILETE_ESTADO_ORDEN[orden.estado] ?? "border-l-border"),
        orden.estado === "ESCALAR" && !escalarBloqueado && "brillo-escalar",
        celebrar && "ring-1 ring-estado-escalar/40",
      )}
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
        {escalarBloqueado && (
          <p className="rounded-lg border border-estado-seguir/40 bg-estado-seguir/10 p-2.5 text-sm text-estado-seguir">
            <strong>¿Qué significa esto?</strong> Este ángulo ya es rentable y vale como ganador —
            pero tu metodología prohíbe subirle presupuesto mientras la fase de testeo sigue abierta.
            Hoy no se hace nada con esta orden: seguí el testeo, y el presupuesto se sube cuando la
            fase cierre.
          </p>
        )}
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-border/60 bg-muted/30 p-3">
          <div>
            <span className="block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              CPA observado
            </span>
            <span
              key={String(pq.cpa_real_q)}
              className="block text-2xl font-bold tabular-nums text-foreground motion-safe:animate-in motion-safe:zoom-in-95 motion-safe:duration-300"
            >
              {pq.cpa_real_q != null ? `Q${pq.cpa_real_q}` : "Sin datos"}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              Break-even
            </span>
            <span
              key={String(pq.break_even_q)}
              className="block text-2xl font-bold tabular-nums text-foreground motion-safe:animate-in motion-safe:zoom-in-95 motion-safe:duration-300"
            >
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
          <Collapsible>
            <CollapsibleTrigger className="text-xs text-muted-foreground underline underline-offset-2 transition-colors hover:text-foreground">
              Ver la nota técnica del motor
            </CollapsibleTrigger>
            <CollapsibleContent>
              <p className="mt-1 rounded border border-estado-seguir/40 bg-estado-seguir/10 p-2 text-xs text-estado-seguir">
                <strong>Nota de fase:</strong> {orden.bloqueo_fase}
              </p>
            </CollapsibleContent>
          </Collapsible>
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
        ) : escalarBloqueado ? (
          <Button
            size="sm"
            variant="outline"
            render={<Link to="/producto/$clave" params={{ clave: orden.producto_key }} />}
          >
            Ver el avance de su fase
          </Button>
        ) : (
          <Button
            size="sm"
            variant="outline"
            render={<Link to="/producto/$clave" params={{ clave: orden.producto_key }} />}
          >
            Ver el producto
          </Button>
        )}
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

/** La Cabina: el resumen del día como tarjetas grandes — una por estado de decisión, con su
 * color, su ícono y su brillo. Se cuentan de las mismas órdenes que se pintan abajo (es
 * contar tarjetas, no calcular el negocio: los estados ya los decidió `decidir.py`).
 * Cada tarjeta de estado se toca y baja hasta SU sección de órdenes (`onIrASeccion`); la de
 * Trabajos sigue siendo un enlace a `/trabajos`. Si Trabajos tiene algo esperando al operador,
 * también ocupa su tarjeta — y su aviso vive acá, no escondido en Ajustes. */
const RESUMEN_DE_ESTADO: Record<string, { icono: LucideIcon; etiqueta: string; clases: string }> = {
  PAUSAR: {
    icono: Power,
    etiqueta: "Pausar",
    clases: "border-estado-pausar/40 bg-estado-pausar/10 text-estado-pausar brillo-pausar",
  },
  ESCALAR: {
    icono: TrendingUp,
    etiqueta: "Escalar",
    clases: "border-estado-escalar/40 bg-estado-escalar/10 text-estado-escalar brillo-escalar",
  },
  RENOVAR: {
    icono: RefreshCw,
    etiqueta: "Renovar",
    clases: "border-estado-renovar/40 bg-estado-renovar/10 text-estado-renovar brillo-renovar",
  },
  MIDIENDO: {
    icono: Hourglass,
    etiqueta: "Midiendo",
    clases: "border-estado-seguir/40 bg-estado-seguir/10 text-estado-seguir",
  },
};

const CLASES_ENTRADA_RESUMEN =
  "motion-safe:animate-in motion-safe:fade-in motion-safe:zoom-in-95 motion-safe:fill-mode-backwards motion-safe:duration-300";

/** Una tarjeta del resumen: con `enlace` navega (Trabajos), con `alHacerClick` se toca y baja
 * hasta su grupo de órdenes de la sección 2, y sin ninguna de las dos queda quieta, solo para
 * leer. El botón copia intactas las clases de la tarjeta (mismo color, brillo y animación)
 * más lo que un botón de ancho completo alineado a la izquierda necesita, con el foco visible
 * que ya usa el `Button` del sistema (`ui/button.tsx`). */
function TarjetaResumen({
  icono: Icono,
  etiqueta,
  cantidad,
  clases,
  indice,
  testid,
  enlace,
  alHacerClick,
}: {
  icono: LucideIcon;
  etiqueta: string;
  cantidad: number;
  clases: string;
  indice: number;
  testid?: string;
  enlace?: string;
  alHacerClick?: () => void;
}) {
  const cuerpo = (
    <>
      <Icono className="size-5" />
      <p className="mt-2 text-4xl font-bold tabular-nums leading-none">{cantidad}</p>
      <p className="mt-1.5 text-sm font-medium">{etiqueta}</p>
    </>
  );
  const base = cn(
    "relative overflow-hidden rounded-xl border p-4 transition-transform motion-safe:hover:-translate-y-1",
    clases,
    CLASES_ENTRADA_RESUMEN,
  );
  if (alHacerClick) {
    return (
      <button
        type="button"
        data-testid={testid}
        onClick={alHacerClick}
        className={cn(
          base,
          "w-full text-left cursor-pointer outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
        )}
        style={{ animationDelay: `${indice * 70}ms` }}
      >
        {cuerpo}
      </button>
    );
  }
  if (enlace) {
    return (
      <Link
        to={enlace}
        data-testid={testid}
        className={base}
        style={{ animationDelay: `${indice * 70}ms` }}
      >
        {cuerpo}
      </Link>
    );
  }
  return (
    <div data-testid={testid} className={base} style={{ animationDelay: `${indice * 70}ms` }}>
      {cuerpo}
    </div>
  );
}

function FranjaDelDia({
  ordenes,
  pendientesDeTrabajos,
  onIrASeccion,
}: {
  ordenes: OrdenItem[];
  pendientesDeTrabajos: number;
  onIrASeccion?: (estado: string) => void;
}) {
  const conteo: Record<string, number> = {};
  let enMedicion = 0;
  for (const orden of ordenes) {
    if (orden.estado === "SEGUIR_MIDIENDO") enMedicion += 1;
    else conteo[orden.estado] = (conteo[orden.estado] ?? 0) + 1;
  }

  const tarjetas: { estado: string; cantidad: number }[] = [];
  for (const estado of ["PAUSAR", "ESCALAR", "RENOVAR"] as const) {
    if ((conteo[estado] ?? 0) > 0) tarjetas.push({ estado, cantidad: conteo[estado] });
  }
  if (enMedicion > 0) tarjetas.push({ estado: "MIDIENDO", cantidad: enMedicion });

  return (
    <div data-testid="franja-hoy" className="space-y-2">
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Hoy te toca</p>
      {tarjetas.length === 0 && pendientesDeTrabajos === 0 ? (
        <div
          className={`flex items-center gap-3 rounded-xl border border-border bg-card/60 p-4 ${CLASES_ENTRADA_RESUMEN}`}
        >
          <CircleCheck className="size-5 text-estado-escalar" />
          <p className="text-sm font-medium">Ninguna acción sobre Meta hoy — el motor midió y todas las celdas siguen su curso.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {tarjetas.map((t, i) => {
            const resumen = RESUMEN_DE_ESTADO[t.estado];
            return (
              <TarjetaResumen
                key={t.estado}
                icono={resumen.icono}
                etiqueta={resumen.etiqueta}
                cantidad={t.cantidad}
                clases={resumen.clases}
                indice={i}
                testid={`resumen-${t.estado.toLowerCase()}`}
                alHacerClick={() => onIrASeccion?.(t.estado)}
              />
            );
          })}
          {pendientesDeTrabajos > 0 && (
            <TarjetaResumen
              icono={BellRing}
              etiqueta="esperan tu revisión en Trabajos"
              cantidad={pendientesDeTrabajos}
              clases="border-estado-seguir/40 bg-estado-seguir/10 text-estado-seguir"
              indice={tarjetas.length}
              testid="resumen-trabajos"
              enlace="/trabajos"
            />
          )}
        </div>
      )}
    </div>
  );
}

/** Sección 2: las órdenes de hoy. Nunca reordena por número, solo por ESTADO (invariante 13:
 * la conversación corta, nunca corona): una sección por estado en el orden de
 * `PRIORIDAD_ACCIONABLE` (PAUSAR → ESCALAR → RENOVAR), cada una con el badge del color de su
 * tarjeta grande, para que arriba y abajo se lea el mismo idioma. Las tarjetas de la franja
 * bajan hasta su sección (`irASeccion`); "Siguen midiendo" nace cerrado, controlado, y la
 * tarjeta «Midiendo» es la única que lo abre antes de bajar. */
function SeccionOrdenes() {
  const ordenesQuery = useQuery({ queryKey: ["ordenes"], queryFn: () => api.ordenes() });
  const accionesQuery = useQuery({ queryKey: ["acciones"], queryFn: () => api.acciones() });
  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const ordenes = ordenesQuery.data?.ordenes ?? [];
  const recienEscalaron = usarEscalaresNuevos(ordenes);
  const [midiendoAbierto, setMidiendoAbierto] = useState(false);

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

  /** El viaje de una tarjeta de la franja hasta sus órdenes. «Midiendo» primero abre el grupo
   * colapsado (cerrado no tendría adónde bajar); el scroll espera un tick a que el panel
   * termine de montarse, y el encadenado opcional de `scrollIntoView` es por jsdom, que no lo
   * implementa. El ancla (`seccion-XXX`) existe solo cuando la sección tiene contenido. */
  const irASeccion = (estado: string) => {
    if (estado === "MIDIENDO") setMidiendoAbierto(true);
    window.setTimeout(() => {
      document.getElementById(`seccion-${estado}`)?.scrollIntoView?.({ behavior: "smooth", block: "start" });
    }, 50);
  };

  // Las accionables ya vienen ordenadas por PRIORIDAD_ACCIONABLE: agrupar las consecutivas
  // del mismo estado produce una sección por estado, en el orden que fija la metodología.
  const grupos: { estado: string; ordenes: OrdenItem[] }[] = [];
  for (const orden of accionables) {
    const ultimo = grupos[grupos.length - 1];
    if (ultimo && ultimo.estado === orden.estado) {
      ultimo.ordenes.push(orden);
    } else {
      grupos.push({ estado: orden.estado, ordenes: [orden] });
    }
  }

  return (
    <div className="space-y-4">
      <FranjaDelDia ordenes={ordenes} pendientesDeTrabajos={pendientes} onIrASeccion={irASeccion} />

      {accionables.length === 0 ? (
        <Card>
          <CardContent className="py-6 text-center text-sm text-muted-foreground">
            No hay órdenes que pidan una acción hoy. El motor midió y todas las celdas siguen su
            curso.
          </CardContent>
        </Card>
      ) : (
        grupos.map((grupo) => {
          const etiqueta = RESUMEN_DE_ESTADO[grupo.estado]?.etiqueta ?? TEXTO_ORDEN[grupo.estado] ?? grupo.estado;
          const clase = CLASE_ESTADO_ORDEN[grupo.estado] ?? "";
          return (
            <section key={grupo.estado} id={`seccion-${grupo.estado}`} className="scroll-mt-6 space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={`border-transparent ${clase}`}>
                  {etiqueta}
                </Badge>
                <span className="text-xs text-muted-foreground">{grupo.ordenes.length} celda(s)</span>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {grupo.ordenes.map((orden, i) => (
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
            </section>
          );
        })
      )}

      {enMedicion.length > 0 && (
        <div id="seccion-MIDIENDO" className="scroll-mt-6">
          <Collapsible open={midiendoAbierto} onOpenChange={setMidiendoAbierto}>
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
        </div>
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
