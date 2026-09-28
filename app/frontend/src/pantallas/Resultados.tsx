/**
 * Resultados.tsx — el dinero, según DOCTRINA/CONTABILIDAD.md, nunca otro cálculo (T4).
 *
 * La pantalla no calcula nada: todo número sale tal cual de `gen_pl.py --json` (T4a), leído
 * por `GET /api/resultados` / `/api/resultados/historial`. Decidido 24-sep-2026 por la
 * metodología: se muestra el P&L real (VISTA A · COHORTE y VISTA B · CAJA), nunca la
 * atribución semanal de `gen_finanzas.py` (capa 1, puede estar inflada) y nunca ROAS.
 *
 * `gen_pl.py` necesita el export de Dropi que el operador baja a mano (cadencia semanal,
 * DOCTRINA/CONTABILIDAD.md §5) — por eso la pantalla siempre ofrece "Cargar export de Dropi",
 * con o sin datos previos, y cada período cargado queda marcado PRELIMINAR mientras su cohorte
 * no llegue a `dias_cohorte_maduro` (la bandera la decide el script, nunca esta pantalla).
 */
import { useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ArrowUpDown, UploadCloud } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart as RechartsLineChart,
  XAxis,
} from "recharts";

import { api, ErrorDeContrato, type Resultados as ResultadosDatos } from "../api/cliente";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn, Info, Problema } from "../componentes/ui";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type EconomiaUnitaria = {
  producto_key: string;
  pct_entrega: number;
  entregadas: number;
  devueltas: number;
  ticket_promedio_q: number;
  margen_antes_publicidad_q: number;
  cpa_real_q: number;
  ganancia_por_venta_q: number;
};

const FORMATO_Q = new Intl.NumberFormat("es-GT", {
  style: "currency",
  currency: "GTQ",
  maximumFractionDigits: 0,
});
const FORMATO_FECHA = new Intl.DateTimeFormat("es-GT", { day: "numeric", month: "short", year: "numeric" });

function formatoQ(valor: number | null | undefined): string {
  return valor == null ? "—" : FORMATO_Q.format(valor);
}

function fechaCorta(iso: string | undefined): string {
  if (!iso) return "—";
  const fecha = new Date(`${iso}T00:00:00`);
  return Number.isNaN(fecha.getTime()) ? iso : FORMATO_FECHA.format(fecha);
}

// Ver `Productos.tsx`: llamadas UNA sola vez, nunca dentro del componente (T3, bug del click
// colgado por reasignar el row-model en cada render).
const CORE_ROW_MODEL = getCoreRowModel<EconomiaUnitaria>();
const SORTED_ROW_MODEL = getSortedRowModel<EconomiaUnitaria>();

const COLUMNAS: ColumnDef<EconomiaUnitaria>[] = [
  { accessorKey: "producto_key", header: "Producto" },
  {
    accessorKey: "pct_entrega",
    header: ({ column }) => (
      <button
        type="button"
        className="inline-flex items-center gap-1"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Entrega
        {column.getIsSorted() === "asc" ? (
          <ArrowUp className="size-3" />
        ) : column.getIsSorted() === "desc" ? (
          <ArrowDown className="size-3" />
        ) : (
          <ArrowUpDown className="size-3 opacity-50" />
        )}
      </button>
    ),
    cell: ({ row }) => (
      <span title={`${row.original.entregadas} entregadas · ${row.original.devueltas} devueltas`}>
        {row.original.pct_entrega.toFixed(1)}%
      </span>
    ),
  },
  {
    accessorKey: "ticket_promedio_q",
    header: "Ticket promedio",
    cell: ({ getValue }) => formatoQ(getValue<number>()),
  },
  {
    accessorKey: "margen_antes_publicidad_q",
    header: "Break-even del CPA",
    cell: ({ getValue }) => formatoQ(getValue<number>()),
  },
  {
    accessorKey: "cpa_real_q",
    header: "CPA real",
    cell: ({ getValue }) => formatoQ(getValue<number>()),
  },
  {
    accessorKey: "ganancia_por_venta_q",
    header: ({ column }) => (
      <button
        type="button"
        className="inline-flex items-center gap-1"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Ganancia por venta
        {column.getIsSorted() === "asc" ? (
          <ArrowUp className="size-3" />
        ) : column.getIsSorted() === "desc" ? (
          <ArrowDown className="size-3" />
        ) : (
          <ArrowUpDown className="size-3 opacity-50" />
        )}
      </button>
    ),
    cell: ({ getValue }) => {
      const valor = getValue<number>();
      return (
        <span className={valor < 0 ? "text-estado-pausar font-medium" : "text-estado-escalar font-medium"}>
          {formatoQ(valor)}
        </span>
      );
    },
  },
];

/** Las 4 tarjetas del encabezado (dashboard-01 `SectionCards`): venta bruta, margen logístico
 * (con la aclaración de CONTABILIDAD.md — no es la ganancia), margen de contribución y el
 * resultado neto. Todas del MISMO período, así que comparten la misma bandera preliminar. */
function TarjetasKpi({ datos }: { datos: ResultadosDatos }) {
  const er = (datos.vista_a_cohorte as Record<string, unknown> | undefined)?.["estado_de_resultados"] as
    | Record<string, number>
    | undefined;
  const preliminar = Boolean((datos.vista_a_cohorte as Record<string, unknown> | undefined)?.["preliminar"]);
  if (!er) return null;

  const tarjetas: {
    titulo: string;
    termino: Parameters<typeof Info>[0]["termino"];
    valor: number | undefined;
    esNeto?: boolean;
  }[] = [
    { titulo: "Venta bruta entregada", termino: "vista_cohorte", valor: er.venta_bruta_entregada_q },
    { titulo: "Margen logístico", termino: "margen_logistico", valor: er.margen_logistico_q },
    { titulo: "Margen de contribución", termino: "margen_contribucion", valor: er.margen_contribucion_q },
    { titulo: "Resultado neto", termino: "vista_cohorte", valor: er.resultado_neto_q, esNeto: true },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {tarjetas.map((tarjeta) => {
        const valor = tarjeta.valor;
        // El resultado neto es EL número de la pantalla: se colorea por signo con el mismo
        // criterio que la tabla de economía unitaria, y su tarjeta lleva el brillo que la
        // vuelve protagonista. En cero o sin dato no hay nada que celebrar ni que frenar:
        // primer plano neutro, sin brillo.
        const positivo = tarjeta.esNeto && valor != null && valor > 0;
        const negativo = tarjeta.esNeto && valor != null && valor < 0;
        return (
          <Card key={tarjeta.titulo} className={cn(positivo && "brillo-escalar", negativo && "brillo-pausar")}>
            <CardHeader>
              <CardDescription className="flex items-center">
                {tarjeta.titulo}
                <Info termino={tarjeta.termino} />
              </CardDescription>
              <CardTitle className="text-3xl font-bold tabular-nums">
                <span
                  key={String(valor)}
                  className={cn(
                    "inline-block motion-safe:animate-in motion-safe:zoom-in-95 motion-safe:duration-300",
                    positivo && "text-estado-escalar",
                    negativo && "text-estado-pausar",
                  )}
                >
                  {formatoQ(valor)}
                </span>
              </CardTitle>
            </CardHeader>
            {preliminar && (
              <CardFooter>
                <Badge variant="outline" className="border-estado-seguir text-estado-seguir">
                  Preliminar
                </Badge>
                <Info termino="cohorte_preliminar" />
              </CardFooter>
            )}
          </Card>
        );
      })}
    </div>
  );
}

const CONFIG_GRAFICO = {
  margen_contribucion_q: { label: "Margen de contribución", color: "var(--chart-1)" },
  resultado_neto_q: { label: "Resultado neto", color: "var(--chart-2)" },
} satisfies ChartConfig;

/** Tendencia por período: un punto por CADA `_PL_*.json` que el operador cargó de verdad
 * (T4a, `gen_pl.py --json`). Nunca una interpolación ni la serie semanal de atribución. */
function GraficoDeTendencia() {
  const historial = useQuery({ queryKey: ["resultados", "historial"], queryFn: api.historialResultados });
  if (historial.isLoading) return <Skeleton className="h-64 w-full" />;
  if (historial.error) return null; // el error ya se muestra arriba, con los resultados vigentes
  const puntos = (historial.data ?? []).map((item) => {
    const er = (item.vista_a_cohorte as Record<string, unknown> | undefined)?.["estado_de_resultados"] as
      | Record<string, number>
      | undefined;
    const periodo = item.periodo as Record<string, string> | undefined;
    return {
      periodo: fechaCorta(periodo?.desde),
      margen_contribucion_q: er?.margen_contribucion_q ?? null,
      resultado_neto_q: er?.resultado_neto_q ?? null,
    };
  });
  if (puntos.length < 2) {
    return (
      <p className="text-sm text-muted-foreground">
        Todavía hay un solo período cargado: la tendencia aparece desde el segundo export de Dropi.
      </p>
    );
  }
  return (
    <ChartContainer config={CONFIG_GRAFICO} className="h-64 w-full">
      <RechartsLineChart data={puntos} margin={{ left: 12, right: 12 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="periodo" tickLine={false} axisLine={false} tickMargin={8} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line dataKey="margen_contribucion_q" type="monotone" stroke="var(--color-margen_contribucion_q)" strokeWidth={2} dot={false} />
        <Line dataKey="resultado_neto_q" type="monotone" stroke="var(--color-resultado_neto_q)" strokeWidth={2} dot={false} />
      </RechartsLineChart>
    </ChartContainer>
  );
}

/** VISTA B · CAJA (DOCTRINA/CONTABILIDAD.md §2): cuánto dinero se movió de verdad en la
 * ventana, según el historial de cartera de Dropi. Dict libre cuyo dueño es `gen_pl.py`
 * (T4a): esta tarjeta pinta las claves tal cual vienen y se salta en silencio cualquier
 * fila que el script no mandó — nunca calcula ni rellena. Los prefijos (+)/(−)/(=) son
 * rótulos de dirección; el monto crudo de cada fila es del script, tal cual. */
type FilaDeCaja = { signo: string; rotulo: string; valor: number; heroe?: boolean };

function TarjetaCaja({ caja }: { caja: Record<string, unknown> | null | undefined }) {
  const numero = (
    datos: Record<string, unknown> | null | undefined,
    clave: string,
  ): number | undefined => {
    const valor = datos?.[clave];
    return typeof valor === "number" && Number.isFinite(valor) ? valor : undefined;
  };
  const objeto = (
    datos: Record<string, unknown> | null | undefined,
    clave: string,
  ): Record<string, unknown> | undefined => {
    const valor = datos?.[clave];
    return typeof valor === "object" && valor !== null ? (valor as Record<string, unknown>) : undefined;
  };

  const filas: FilaDeCaja[] = [];
  const nEntradas = numero(caja, "n_entradas_ganancia_ordenes");
  const entradas = numero(caja, "entradas_ganancia_ordenes_q");
  if (entradas !== undefined) {
    filas.push({
      signo: "(+)",
      rotulo: `Entradas por ganancia de órdenes${nEntradas !== undefined ? ` (${nEntradas})` : ""}`,
      valor: entradas,
    });
  }
  const nDevoluciones = numero(caja, "n_cobros_devolucion");
  const devoluciones = numero(caja, "cobros_devolucion_q");
  if (devoluciones !== undefined) {
    filas.push({
      signo: "(−)",
      rotulo: `Cobros de devolución${nDevoluciones !== undefined ? ` (${nDevoluciones})` : ""}`,
      valor: devoluciones,
    });
  }
  const nOtrasSalidas = numero(caja, "n_otras_salidas");
  const otrasSalidas = numero(caja, "otras_salidas_q");
  if (otrasSalidas !== undefined && nOtrasSalidas !== undefined && nOtrasSalidas > 0) {
    filas.push({ signo: "(−)", rotulo: `Otras salidas (${nOtrasSalidas})`, valor: otrasSalidas });
  }
  const neto = numero(caja, "neto_acreditado_cartera_q");
  if (neto !== undefined) {
    filas.push({ signo: "(=)", rotulo: "Neto acreditado en la cartera", valor: neto, heroe: true });
  }
  const personal = numero(caja, "personal_y_otros_q");
  if (personal !== undefined) {
    filas.push({ signo: "(−)", rotulo: "Personal y otros", valor: personal });
  }
  const publicidad = numero(caja, "publicidad_cobrada_banco_q");
  if (publicidad !== undefined) {
    filas.push({ signo: "(−)", rotulo: "Publicidad cobrada por el banco", valor: publicidad });
    const gastosFijos = numero(caja, "gastos_fijos_q");
    if (gastosFijos !== undefined) {
      filas.push({ signo: "(−)", rotulo: "Gastos fijos del negocio", valor: gastosFijos });
    }
    const cajaDelNegocio = numero(caja, "caja_que_genero_el_negocio_q");
    if (cajaDelNegocio !== undefined) {
      filas.push({
        signo: "(=)",
        rotulo: "Caja que generó el negocio",
        valor: cajaDelNegocio,
        heroe: true,
      });
    }
    const retiros = numero(caja, "retiros_personales_q");
    if (retiros !== undefined) {
      filas.push({ signo: "(−)", rotulo: "Retiros personales (no son del negocio)", valor: retiros });
    }
    const enLaCuenta = numero(caja, "caja_que_quedo_en_la_cuenta_q");
    if (enLaCuenta !== undefined) {
      filas.push({ signo: "(=)", rotulo: "Caja que quedó en la cuenta", valor: enLaCuenta, heroe: true });
    }
  } else {
    const antesDePublicidad = numero(caja, "caja_antes_de_publicidad_q");
    if (antesDePublicidad !== undefined) {
      filas.push({
        signo: "(=)",
        rotulo: "Caja antes de publicidad",
        valor: antesDePublicidad,
        heroe: true,
      });
    }
  }

  const arrastre = objeto(caja, "arrastre");
  const cohorteVsCaja = objeto(caja, "cohorte_vs_caja_q");
  const notaArrastre = arrastre
    ? `Arrastre: ${numero(arrastre, "n_acreditaciones_previas") ?? "—"} de ${numero(arrastre, "n_acreditaciones_total") ?? "—"} acreditaciones (${formatoQ(numero(arrastre, "monto_previo_q"))}) vienen de órdenes tomadas antes de la ventana — eso es exactamente lo que la vista de cohorte no ve.`
    : null;
  const notaCohorteVsCaja = cohorteVsCaja
    ? `Cohorte vs caja en esta ventana: ${formatoQ(numero(cohorteVsCaja, "cohorte_margen_contribucion_q"))} vs ${formatoQ(numero(cohorteVsCaja, "caja_antes_de_publicidad_q"))}. No tienen por qué coincidir y ninguna está mal: miden cosas distintas.`
    : null;

  return (
    <Card data-testid="caja-vista-b">
      <CardHeader>
        <CardTitle className="flex items-center gap-1 text-base">
          Caja de la ventana
          <Info termino="vista_caja" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!caja ? (
          <p className="text-sm text-muted-foreground">
            No se puede calcular la caja: falta el historial de cartera de Dropi. Lo que muestran
            las tarjetas de arriba es cohorte — mide si la pauta rindió, no el saldo de la cuenta.
          </p>
        ) : (
          <>
            <dl className="space-y-1.5">
              {filas.map((fila) => (
                <div
                  key={fila.rotulo}
                  className={"flex items-baseline justify-between gap-4" + (fila.heroe ? " border-t pt-2" : "")}
                >
                  <dt className={"text-sm " + (fila.heroe ? "font-medium" : "text-muted-foreground")}>
                    <span className="mr-1.5 font-mono text-xs text-muted-foreground">{fila.signo}</span>
                    {fila.rotulo}
                  </dt>
                  <dd className={"tabular-nums " + (fila.heroe ? "text-xl font-semibold" : "text-sm")}>
                    {formatoQ(fila.valor)}
                  </dd>
                </div>
              ))}
            </dl>
            {(notaArrastre || notaCohorteVsCaja) && (
              <div className="mt-4 space-y-1 border-t pt-3">
                {notaArrastre && <p className="text-xs text-muted-foreground">{notaArrastre}</p>}
                {notaCohorteVsCaja && <p className="text-xs text-muted-foreground">{notaCohorteVsCaja}</p>}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

/** La tabla de economía unitaria por producto — mismo patrón seguro que `Productos.tsx` (T3):
 * row-models a nivel de módulo, datos memoizados de verdad, tarjetas en vez de `<table>` bajo
 * 768px para nunca duplicar la fila en el DOM. */
function TablaPorProducto({ filas }: { filas: EconomiaUnitaria[] }) {
  const [orden, setOrden] = useState<SortingState>([]);
  const esMovil = useIsMobile();
  const datos = useMemo(() => filas, [filas]);
  const tabla = useReactTable({
    data: datos,
    columns: COLUMNAS,
    state: { sorting: orden },
    onSortingChange: setOrden,
    getCoreRowModel: CORE_ROW_MODEL,
    getSortedRowModel: SORTED_ROW_MODEL,
  });

  if (!filas.length) {
    return <p className="text-sm text-muted-foreground">Sin órdenes entregadas en este período.</p>;
  }

  if (esMovil) {
    return (
      <div className="flex flex-col gap-3">
        {filas.map((fila) => (
          <Card key={fila.producto_key}>
            <CardHeader>
              <CardTitle className="text-sm">{fila.producto_key}</CardTitle>
              <CardDescription>
                {fila.pct_entrega.toFixed(1)}% de entrega · {fila.entregadas} entregadas / {fila.devueltas} devueltas
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Ticket promedio</span>
              <span className="text-right tabular-nums">{formatoQ(fila.ticket_promedio_q)}</span>
              <span className="text-muted-foreground">Break-even del CPA</span>
              <span className="text-right tabular-nums">{formatoQ(fila.margen_antes_publicidad_q)}</span>
              <span className="text-muted-foreground">CPA real</span>
              <span className="text-right tabular-nums">{formatoQ(fila.cpa_real_q)}</span>
              <span className="text-muted-foreground">Ganancia por venta</span>
              <span
                className={
                  "text-right font-medium tabular-nums " +
                  (fila.ganancia_por_venta_q < 0 ? "text-estado-pausar" : "text-estado-escalar")
                }
              >
                {formatoQ(fila.ganancia_por_venta_q)}
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        {tabla.getHeaderGroups().map((grupo) => (
          <TableRow key={grupo.id}>
            {grupo.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {tabla.getRowModel().rows.map((fila) => (
          <TableRow key={fila.id}>
            {fila.getVisibleCells().map((celda) => (
              <TableCell key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** "Cargar export de Dropi": el único gesto que produce un P&L nuevo. Siempre visible — con o
 * sin carga previa — porque `gen_pl.py` no corre solo (DOCTRINA/CONTABILIDAD.md §5: el
 * operador lo baja a mano, cadencia semanal, ventana de 60 días móviles). */
function CargarExport() {
  const cola = useQueryClient();
  const [dropi, setDropi] = useState<File | null>(null);
  const [banco, setBanco] = useState<File | null>(null);
  const [cartera, setCartera] = useState<File | null>(null);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");

  const cargar = useMutation({
    mutationFn: () => {
      const formulario = new FormData();
      formulario.append("dropi", dropi as File);
      if (banco) formulario.append("banco", banco);
      if (cartera) formulario.append("cartera", cartera);
      if (desde) formulario.append("desde", desde);
      if (hasta) formulario.append("hasta", hasta);
      return api.cargarResultados(formulario);
    },
    onSuccess: () => {
      cola.invalidateQueries({ queryKey: ["resultados"] });
      setDropi(null);
      setBanco(null);
      setCartera(null);
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <UploadCloud className="size-4" />
          Cargar export de Dropi
        </CardTitle>
        <CardDescription>
          Ventana de 60 días móviles, no el mes calendario (DOCTRINA/CONTABILIDAD.md §5). El
          extracto bancario y la cartera son opcionales: sin ellos solo se calcula VISTA A ·
          COHORTE.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="dropi-xlsx">Export de órdenes de Dropi *</Label>
          <Input
            id="dropi-xlsx"
            type="file"
            accept=".xlsx"
            onChange={(evento) => setDropi(evento.target.files?.[0] ?? null)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cartera-xlsx">Historial de cartera (opcional)</Label>
          <Input
            id="cartera-xlsx"
            type="file"
            accept=".xlsx"
            onChange={(evento) => setCartera(evento.target.files?.[0] ?? null)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="banco-pdf">Extracto bancario (opcional)</Label>
          <Input
            id="banco-pdf"
            type="file"
            accept=".pdf"
            onChange={(evento) => setBanco(evento.target.files?.[0] ?? null)}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="desde">Desde</Label>
            <Input id="desde" type="date" value={desde} onChange={(evento) => setDesde(evento.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="hasta">Hasta</Label>
            <Input id="hasta" type="date" value={hasta} onChange={(evento) => setHasta(evento.target.value)} />
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-3">
        <Button onClick={() => cargar.mutate()} disabled={!dropi || cargar.isPending}>
          {cargar.isPending ? "Calculando…" : "Calcular el P&L"}
        </Button>
        {cargar.isError && (
          <Alert variant="destructive">
            <AlertTitle>No se pudo calcular</AlertTitle>
            <AlertDescription>{(cargar.error as Error).message}</AlertDescription>
          </Alert>
        )}
      </CardFooter>
    </Card>
  );
}

function EstadoVacio() {
  return (
    <Alert>
      <UploadCloud className="size-4" />
      <AlertTitle>Todavía no hay ningún export de Dropi cargado</AlertTitle>
      <AlertDescription>
        El estado de resultados real (DOCTRINA/CONTABILIDAD.md) sale de un export que Dropi no
        entrega por API: el operador lo baja a mano cada semana, con una ventana de 60 días
        móviles. Cargá el primero abajo para ver VISTA A · COHORTE (y VISTA B · CAJA si además
        subís la cartera).
      </AlertDescription>
    </Alert>
  );
}

export function Resultados() {
  const resultados = useQuery({ queryKey: ["resultados"], queryFn: api.resultados, retry: false });

  const noHayCarga = resultados.error instanceof ErrorDeContrato && resultados.error.estado === 404;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Resultados</h1>
        <p className="text-sm text-muted-foreground">
          El estado de resultados real, tal como lo manda DOCTRINA/CONTABILIDAD.md — nunca ROAS
          ni la atribución semanal de los anuncios.
        </p>
      </div>

      {resultados.isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((n) => (
            <Skeleton key={n} className="h-28 w-full" />
          ))}
        </div>
      )}

      {!resultados.isLoading && resultados.error && !noHayCarga && <Problema error={resultados.error} />}
      {!resultados.isLoading && noHayCarga && <EstadoVacio />}

      {resultados.data && (
        <>
          <p className="text-sm text-muted-foreground">
            Última carga: {fechaCorta((resultados.data.periodo as Record<string, string>)?.generado)} · período{" "}
            {fechaCorta((resultados.data.periodo as Record<string, string>)?.desde)}–
            {fechaCorta((resultados.data.periodo as Record<string, string>)?.hasta)}
          </p>
          <TarjetasKpi datos={resultados.data} />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tendencia por período</CardTitle>
              <CardDescription>Cada punto es un export de Dropi que el operador realmente cargó.</CardDescription>
            </CardHeader>
            <CardContent>
              <GraficoDeTendencia />
            </CardContent>
          </Card>
          <TarjetaCaja caja={resultados.data.vista_b_caja} />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Economía unitaria por producto</CardTitle>
              <CardDescription>Cuánto deja cada venta, del período vigente (§4).</CardDescription>
            </CardHeader>
            <CardContent>
              <TablaPorProducto
                filas={((resultados.data.vista_a_cohorte as Record<string, unknown>)?.["economia_unitaria"] ??
                  []) as EconomiaUnitaria[]}
              />
            </CardContent>
          </Card>
        </>
      )}

      <CargarExport />
    </div>
  );
}
