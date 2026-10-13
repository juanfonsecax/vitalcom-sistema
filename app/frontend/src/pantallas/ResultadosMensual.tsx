/**
 * ResultadosMensual.tsx — «Mes a mes»: el estado de resultados de cada mes de un mercado.
 *
 * La pantalla no calcula nada: cada número sale tal cual de `gen_pl_mensual.py --json`
 * (`GET /api/resultados/mensual`), que usa la fórmula de `gen_pl.py` (DOCTRINA/CONTABILIDAD.md).
 * Un valor `null` es un dato que no se pudo medir (el mes no tiene órdenes de Dropi): se escribe
 * «—», nunca un cero. La insignia PRELIMINAR y la lista de faltantes también las decide el script.
 * El retiro personal se muestra aparte: nunca entra al resultado. Lo mismo la billetera de Dropi
 * (retiros, transferencias a cuenta propia, saldo): son movimientos de caja, van en su propia sección
 * y no tocan la ganancia.
 */
import { useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UploadCloud } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, XAxis } from "recharts";

import { api, type CarteraDelMes, type MesDelPL, type ProductoDelMes } from "../api/cliente";
import { BanderaMercado } from "../componentes/mercado";
import { cn, Problema } from "../componentes/ui";
import { formatearDinero, type PerfilMoneda } from "../dinero";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** «2026-09» → «sep 2026». */
function nombreDelMes(mes: string): string {
  const [anio, numero] = mes.split("-");
  return `${MESES[Number(numero) - 1] ?? numero} ${anio}`;
}

const PERFIL_USD: PerfilMoneda = { mercado: "US", moneda_local: "USD", simbolo: "$" };

function perfilDe(moneda: string, simbolo: string): PerfilMoneda {
  return { moneda_local: moneda, simbolo };
}

/** Una fila del estado de resultados: el rótulo, de qué campo sale y cómo se pinta. */
type Rubro = {
  rotulo: string;
  signo?: string;
  valor: (mes: MesDelPL) => number | null | undefined;
  /** Los subtotales (=) y el resultado van en negrita. */
  fuerte?: boolean;
  dolares?: boolean;
  nota?: string;
};

const RUBROS: Rubro[] = [
  { rotulo: "Venta bruta entregada", signo: "(+)", valor: (m) => m.venta_entregada_q },
  { rotulo: "Costo de producto", signo: "(−)", valor: (m) => m.costo_producto_q },
  { rotulo: "Flete de entrega", signo: "(−)", valor: (m) => m.flete_q },
  { rotulo: "Margen logístico", signo: "(=)", valor: (m) => m.margen_logistico_q, fuerte: true },
  { rotulo: "Devoluciones", signo: "(−)", valor: (m) => m.devoluciones_q },
  { rotulo: "Personal", signo: "(−)", valor: (m) => m.personal_q },
  { rotulo: "Otros gastos operativos", signo: "(−)", valor: (m) => m.otros_q },
  { rotulo: "Margen de contribución", signo: "(=)", valor: (m) => m.margen_contribucion_q, fuerte: true },
  { rotulo: "Publicidad", signo: "(−)", valor: (m) => m.publicidad.q },
  { rotulo: "Margen operativo", signo: "(=)", valor: (m) => m.margen_operativo_q, fuerte: true },
  { rotulo: "Gastos fijos", signo: "(−)", valor: (m) => m.gastos_fijos.q },
  { rotulo: "Resultado neto", signo: "(=)", valor: (m) => m.resultado_neto_q, fuerte: true },
];

/** Movimientos de caja de la billetera de Dropi: NO afectan la ganancia. */
const RUBROS_DE_CAJA: { rotulo: string; valor: (c: CarteraDelMes) => number | null | undefined; alerta?: boolean }[] = [
  { rotulo: "Retiros personales desde Dropi", valor: (c) => c.retiros_personales_q },
  { rotulo: "Transferencias a cuenta propia", valor: (c) => c.transferencias_propias_q },
  { rotulo: "Retiros sin clasificar", valor: (c) => c.sin_clasificar_q, alerta: true },
  { rotulo: "Saldo de la billetera de Dropi", valor: (c) => c.saldo_cierre_q },
];

const CLASE_DE_RETIRO: Record<string, string> = {
  RETIRO_PERSONAL: "Retiro personal",
  TRANSFERENCIA_PROPIA: "A cuenta propia",
  SIN_CLASIFICAR: "Sin clasificar",
};

/** Debajo del costo de devoluciones: de dónde sale (cobro real de la billetera o promedio). */
function origenDeDevoluciones(mes: MesDelPL): string | null {
  const d = mes.cartera.devoluciones;
  if (d.origen === "REAL") return "costo real de la billetera";
  if (d.origen === "MIXTO") return `${d.reales} de ${d.reales + d.estimadas} cobradas en la billetera; el resto, promedio`;
  if (d.origen === "ESTIMADO") return "promedio estimado";
  return null;
}

const CONFIG_GRAFICO = {
  venta_entregada_q: { label: "Venta entregada", color: "var(--chart-1)" },
  costos_operativos_q: { label: "Costos operativos", color: "var(--chart-3)" },
  pauta_q: { label: "Pauta", color: "var(--chart-4)" },
  resultado_neto_q: { label: "Resultado neto", color: "var(--estado-escalar)" },
} satisfies ChartConfig;

function GraficoMensual({ meses }: { meses: MesDelPL[] }) {
  const puntos = meses.map((mes) => ({
    mes: nombreDelMes(mes.mes),
    venta_entregada_q: mes.venta_entregada_q ?? null,
    costos_operativos_q: mes.costos_operativos_q ?? null,
    pauta_q: mes.publicidad.q,
    resultado_neto_q: mes.resultado_neto_q ?? null,
  }));
  return (
    <ChartContainer config={CONFIG_GRAFICO} className="h-64 w-full" data-testid="grafico-mensual">
      <BarChart data={puntos} margin={{ left: 12, right: 12 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="mes" tickLine={false} axisLine={false} tickMargin={8} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        <Bar dataKey="venta_entregada_q" fill="var(--color-venta_entregada_q)" radius={3} />
        <Bar dataKey="costos_operativos_q" fill="var(--color-costos_operativos_q)" radius={3} />
        <Bar dataKey="pauta_q" fill="var(--color-pauta_q)" radius={3} />
        <Bar dataKey="resultado_neto_q" fill="var(--color-resultado_neto_q)" radius={3}>
          {puntos.map((punto) => (
            <Cell
              key={punto.mes}
              fill={punto.resultado_neto_q != null && punto.resultado_neto_q < 0 ? "var(--estado-pausar)" : "var(--color-resultado_neto_q)"}
            />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

function TablaMensual({
  meses,
  perfil,
  seleccionado,
  onElegir,
}: {
  meses: MesDelPL[];
  perfil: PerfilMoneda;
  seleccionado: string;
  onElegir: (mes: string) => void;
}) {
  const dinero = (valor: number | null | undefined) => formatearDinero(valor, perfil, { decimales: 0 });
  const dolares = (valor: number | null | undefined) => formatearDinero(valor, PERFIL_USD);
  return (
    <Table data-testid="tabla-mensual">
      <TableHeader>
        <TableRow>
          <TableHead />
          {meses.map((mes) => (
            <TableHead key={mes.mes} className="text-right">
              <button
                type="button"
                onClick={() => onElegir(mes.mes)}
                aria-pressed={mes.mes === seleccionado}
                className={cn("font-medium underline-offset-4 hover:underline", mes.mes === seleccionado && "underline")}
              >
                {nombreDelMes(mes.mes)}
              </button>
              {mes.preliminar && (
                <div>
                  <Badge variant="outline" className="border-estado-seguir text-estado-seguir">
                    Preliminar
                  </Badge>
                </div>
              )}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {RUBROS.map((rubro) => (
          <TableRow key={rubro.rotulo} className={cn(rubro.fuerte && "font-semibold")}>
            <TableCell className="whitespace-nowrap">
              <span className="mr-1.5 font-mono text-xs text-muted-foreground">{rubro.signo}</span>
              {rubro.rotulo}
            </TableCell>
            {meses.map((mes) => {
              const valor = rubro.valor(mes);
              const neto = rubro.rotulo === "Resultado neto";
              const origen = rubro.rotulo === "Devoluciones" ? origenDeDevoluciones(mes) : null;
              return (
                <TableCell
                  key={mes.mes}
                  className={cn(
                    "text-right tabular-nums",
                    neto && valor != null && valor > 0 && "text-estado-escalar",
                    neto && valor != null && valor < 0 && "text-estado-pausar",
                  )}
                >
                  {dinero(valor)}
                  {origen && <div className="text-[11px] font-normal text-muted-foreground">{origen}</div>}
                </TableCell>
              );
            })}
          </TableRow>
        ))}
        <TableRow className="text-muted-foreground">
          <TableCell className="whitespace-nowrap">
            Retiros personales del banco <span className="text-xs">(fuera del resultado)</span>
          </TableCell>
          {meses.map((mes) => (
            <TableCell key={mes.mes} className="text-right tabular-nums">
              {dinero(mes.retiros_personales.q)}
            </TableCell>
          ))}
        </TableRow>
        <TableRow className="text-muted-foreground">
          <TableCell className="whitespace-nowrap">El banco cobró Facebook</TableCell>
          {meses.map((mes) => (
            <TableCell key={mes.mes} className="text-right tabular-nums">
              {dolares(mes.banco_facebook.usd)}
            </TableCell>
          ))}
        </TableRow>
        <TableRow className="text-muted-foreground">
          <TableCell className="whitespace-nowrap">Órdenes entregadas / devueltas / en tránsito</TableCell>
          {meses.map((mes) => (
            <TableCell key={mes.mes} className="text-right tabular-nums">
              {mes.ordenes.total
                ? `${mes.ordenes.entregadas} / ${mes.ordenes.devueltas} / ${mes.ordenes.en_transito}`
                : "—"}
            </TableCell>
          ))}
        </TableRow>
        <TableRow className="bg-muted/40 hover:bg-muted/40">
          <TableCell colSpan={meses.length + 1} className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Movimientos de caja (no afectan la ganancia)
          </TableCell>
        </TableRow>
        {RUBROS_DE_CAJA.map((rubro) => (
          <TableRow key={rubro.rotulo} className="text-muted-foreground">
            <TableCell className="whitespace-nowrap">{rubro.rotulo}</TableCell>
            {meses.map((mes) => {
              const valor = rubro.valor(mes.cartera);
              return (
                <TableCell
                  key={mes.mes}
                  className={cn("text-right tabular-nums", rubro.alerta && valor != null && valor > 0 && "text-estado-seguir")}
                >
                  {dinero(valor)}
                </TableCell>
              );
            })}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Detalle({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{titulo}</h3>
      {children}
    </div>
  );
}

function DetalleBilletera({ mes, perfil }: { mes: MesDelPL; perfil: PerfilMoneda }) {
  const dinero = (valor: number | null | undefined) => formatearDinero(valor, perfil, { decimales: 0 });
  const c = mes.cartera;
  const origen = origenDeDevoluciones(mes);
  return (
    <Detalle titulo="Billetera de Dropi">
      <div data-testid="detalle-billetera" className="flex flex-col gap-1.5">
        {c.saldo_cierre_q == null ? (
          <p className="text-sm text-muted-foreground">
            Sin historial de cartera en este mes: no hay retiros ni saldo, y las devoluciones usan el promedio.
          </p>
        ) : (
          <>
            <p className="text-sm">
              {mes.preliminar ? `Saldo al ${c.fecha_corte}` : `Saldo al cierre (${c.fecha_corte})`}: {dinero(c.saldo_cierre_q)}. No tocan la
              ganancia: son movimientos de caja.
            </p>
            {c.retiros.length === 0 ? (
              <p className="text-sm text-muted-foreground">Sin retiros este mes.</p>
            ) : (
              <ul className="text-sm">
                {c.retiros.map((r) => (
                  <li key={`${r.fecha}-${r.hora}-${r.monto_q}`} className="flex justify-between gap-4">
                    <span>
                      {r.fecha} · <span>{r.concepto}</span>{" "}
                      <Badge
                        variant="outline"
                        className={cn(r.clasificacion === "SIN_CLASIFICAR" && "border-estado-seguir text-estado-seguir")}
                      >
                        {CLASE_DE_RETIRO[r.clasificacion] ?? r.clasificacion}
                      </Badge>
                    </span>
                    <span className="tabular-nums">{dinero(r.monto_q)}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
        {origen && (
          <p className="text-xs text-muted-foreground">
            Costo de las devoluciones: {origen} ({mes.cartera.devoluciones.reales} reales,{" "}
            {mes.cartera.devoluciones.estimadas} estimadas).
          </p>
        )}
      </div>
    </Detalle>
  );
}

function DetalleDelMes({ mes, perfil }: { mes: MesDelPL; perfil: PerfilMoneda }) {
  const dinero = (valor: number | null | undefined) => formatearDinero(valor, perfil, { decimales: 0 });
  const dolares = (valor: number | null | undefined) => formatearDinero(valor, PERFIL_USD);
  const productos: ProductoDelMes[] = mes.por_producto;
  return (
    <Card data-testid="detalle-del-mes">
      <CardHeader>
        <CardTitle className="text-base">{nombreDelMes(mes.mes)} · detalle</CardTitle>
        <CardDescription>
          {mes.preliminar
            ? "Cohorte preliminar: las devoluciones tardan ~8 días en confirmarse, así que este mes todavía puede empeorar."
            : mes.preliminar === false
              ? `Cohorte maduro (${mes.edad_dias} días de edad): resultado concluyente.`
              : "Sin órdenes de Dropi: no hay resultado que concluir."}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <Detalle titulo="Por producto">
          {productos.length === 0 ? (
            <p className="text-sm text-muted-foreground">Sin productos con órdenes ni pauta este mes.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead className="text-right">Ventas entregadas</TableHead>
                  <TableHead className="text-right">Margen antes de publicidad</TableHead>
                  <TableHead className="text-right">Pauta</TableHead>
                  <TableHead className="text-right">Ganancia</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productos.map((p) => (
                  <TableRow key={p.producto_key}>
                    <TableCell>{p.producto_key}</TableCell>
                    <TableCell className="text-right tabular-nums">{dinero(p.venta_entregada_q)}</TableCell>
                    <TableCell className="text-right tabular-nums">{dinero(p.margen_antes_publicidad_q)}</TableCell>
                    <TableCell className="text-right tabular-nums">{dinero(p.pauta_q)}</TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-medium tabular-nums",
                        p.ganancia_q != null && p.ganancia_q < 0 && "text-estado-pausar",
                        p.ganancia_q != null && p.ganancia_q > 0 && "text-estado-escalar",
                      )}
                    >
                      {dinero(p.ganancia_q)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Detalle>

        <Detalle titulo="De dónde sale la pauta">
          <p className="text-sm">
            Meta {dolares(mes.publicidad.meta_usd)} · LucidSales (donde Meta no cubre){" "}
            {dolares(mes.publicidad.lucidsales_fallback_usd)} · en total {dolares(mes.publicidad.usd)} ={" "}
            {dinero(mes.publicidad.q)}
          </p>
          <p className="text-xs text-muted-foreground">
            El banco cobró Facebook {dolares(mes.banco_facebook.usd)}
            {mes.banco_facebook.cargos != null ? ` en ${mes.banco_facebook.cargos} cargos` : ""}; son fechas de
            cobro, no de gasto, así que no tienen por qué coincidir con la pauta del mes.
          </p>
        </Detalle>

        <Detalle titulo="Gastos fijos del negocio">
          {mes.gastos_fijos.detalle.length === 0 ? (
            <p className="text-sm text-muted-foreground">Ninguno confirmado en este mes.</p>
          ) : (
            <ul className="text-sm">
              {mes.gastos_fijos.detalle.map((d) => (
                <li key={d.nombre} className="flex justify-between gap-4">
                  <span>
                    {d.nombre} <span className="text-xs text-muted-foreground">{d.categoria}</span>
                  </span>
                  <span className="tabular-nums">{dinero(d.monto_q)}</span>
                </li>
              ))}
            </ul>
          )}
        </Detalle>

        <DetalleBilletera mes={mes} perfil={perfil} />

        {mes.retiros_personales.detalle.length > 0 && (
          <Detalle titulo="Retiros personales (no son del negocio)">
            <ul className="text-sm">
              {mes.retiros_personales.detalle.map((d) => (
                <li key={d.nombre} className="flex justify-between gap-4">
                  <span>{d.nombre}</span>
                  <span className="tabular-nums">{dinero(d.monto_q)}</span>
                </li>
              ))}
            </ul>
          </Detalle>
        )}
      </CardContent>
    </Card>
  );
}

function Faltantes({ globales, mes }: { globales: string[]; mes: MesDelPL | undefined }) {
  const lista = [...globales, ...(mes?.faltantes ?? [])];
  if (!lista.length) return null;
  return (
    <Alert data-testid="faltantes">
      <AlertTitle>Lo que falta {mes ? `· ${nombreDelMes(mes.mes)}` : ""}</AlertTitle>
      <AlertDescription>
        <ul className="list-disc pl-5">
          {lista.map((texto) => (
            <li key={texto}>{texto}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}

/** Subir un export de Dropi, su historial de cartera y/o un extracto bancario: el script los guarda. */
function CargarHistorial() {
  const cola = useQueryClient();
  const [dropi, setDropi] = useState<File | null>(null);
  const [cartera, setCartera] = useState<File | null>(null);
  const [banco, setBanco] = useState<File | null>(null);
  const [cuenta, setCuenta] = useState("");
  const cargar = useMutation({
    mutationFn: () => {
      const formulario = new FormData();
      if (dropi) formulario.append("dropi", dropi);
      if (cartera) formulario.append("cartera", cartera);
      if (banco) formulario.append("banco", banco);
      if (cuenta.trim()) formulario.append("cuenta", cuenta.trim());
      return api.cargarMensual(formulario);
    },
    onSuccess: () => {
      cola.invalidateQueries({ queryKey: ["resultados"] });
      setDropi(null);
      setCartera(null);
      setBanco(null);
    },
  });
  const resumen = cargar.data;
  const frases = [
    resumen?.dropi ? `Dropi: ${String(resumen.dropi.nuevas ?? 0)} órdenes nuevas, ${String(resumen.dropi.actualizadas ?? 0)} actualizadas.` : null,
    resumen?.cartera ? `Cartera: ${String(resumen.cartera.nuevas ?? 0)} movimientos nuevos.` : null,
    resumen?.banco ? `Banco: ${String(resumen.banco.nuevas ?? 0)} movimientos nuevos.` : null,
  ].filter(Boolean);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <UploadCloud className="size-4" />
          Cargar datos al historial
        </CardTitle>
        <CardDescription>
          Cada archivo se guarda una sola vez: subir de nuevo el mismo no cambia nada, y un export más nuevo
          actualiza el estatus de las órdenes que ya estaban. Dropi se baja cada semana (órdenes y cartera); el extracto, cada mes.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mensual-dropi">Export de órdenes de Dropi (.xlsx)</Label>
          <Input id="mensual-dropi" type="file" accept=".xlsx" onChange={(e) => setDropi(e.target.files?.[0] ?? null)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mensual-cartera">Historial de cartera de Dropi (.xlsx)</Label>
          <Input id="mensual-cartera" type="file" accept=".xlsx" onChange={(e) => setCartera(e.target.files?.[0] ?? null)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mensual-banco">Extracto bancario de Relay (.pdf)</Label>
          <Input id="mensual-banco" type="file" accept=".pdf" onChange={(e) => setBanco(e.target.files?.[0] ?? null)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mensual-cuenta">Últimos 4 de la cuenta (opcional)</Label>
          <Input
            id="mensual-cuenta"
            inputMode="numeric"
            maxLength={4}
            placeholder="se toma del extracto"
            value={cuenta}
            onChange={(e) => setCuenta(e.target.value)}
          />
        </div>
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-3">
        <Button onClick={() => cargar.mutate()} disabled={(!dropi && !cartera && !banco) || cargar.isPending}>
          {cargar.isPending ? "Guardando…" : "Guardar en el historial"}
        </Button>
        {cargar.isSuccess && frases.length > 0 && (
          <p className="text-sm text-muted-foreground">{frases.join(" ")}</p>
        )}
        {cargar.isError && (
          <Alert variant="destructive">
            <AlertTitle>No se pudo guardar</AlertTitle>
            <AlertDescription>{(cargar.error as Error).message}</AlertDescription>
          </Alert>
        )}
      </CardFooter>
    </Card>
  );
}

export function ResultadosMensual({ mercado }: { mercado: string }) {
  const datos = useQuery({
    queryKey: ["resultados", "mensual", mercado],
    queryFn: () => api.resultadoMensual(mercado),
    retry: false,
  });
  const [elegido, setElegido] = useState<string | null>(null);

  if (datos.isLoading) return <Skeleton className="h-64 w-full" />;
  if (datos.error) return <Problema error={datos.error} />;
  if (!datos.data) return null;

  const meses = datos.data.meses;
  const perfil = perfilDe(datos.data.moneda, mercado === "GT" ? "Q" : "$");
  const conResultado = [...meses].reverse().find((m) => m.resultado_neto_q != null);
  const mesElegido = meses.find((m) => m.mes === elegido) ?? conResultado ?? meses[meses.length - 1];

  if (!meses.length) {
    return (
      <div className="flex flex-col gap-6">
        <Alert data-testid="mensual-sin-datos">
          <UploadCloud className="size-4" />
          <AlertTitle>
            <BanderaMercado mercado={mercado} /> {mercado}: sin datos todavía
          </AlertTitle>
          <AlertDescription>
            {datos.data.faltantes.length ? datos.data.faltantes.join(" ") : "No hay nada cargado para este mercado."}
          </AlertDescription>
        </Alert>
        {mercado === "GT" && <CargarHistorial />}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6" data-testid="resultados-mensual">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Mes a mes</CardTitle>
          <CardDescription>
            Venta entregada, costos, pauta y resultado neto de cada mes. Los retiros personales no entran al
            resultado.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <GraficoMensual meses={meses} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Estado de resultados por mes</CardTitle>
          <CardDescription>
            Elegí un mes para ver su detalle. «—» es un dato que no se pudo medir, no un cero.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <TablaMensual
            meses={meses}
            perfil={perfil}
            seleccionado={mesElegido?.mes ?? ""}
            onElegir={setElegido}
          />
        </CardContent>
      </Card>

      <Faltantes globales={datos.data.faltantes} mes={mesElegido} />
      {mesElegido && <DetalleDelMes mes={mesElegido} perfil={perfil} />}
      <CargarHistorial />
    </div>
  );
}
