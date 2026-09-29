/**
 * Productos.tsx — el portafolio en una tabla densa (P4/T3, reemplaza el grid de tarjetas de
 * Tablero.tsx). Contesta las mismas tres preguntas de siempre:
 *   1. ¿Dónde está?    fase y paso vigentes (derivados, nunca declarados a mano)
 *   2. ¿Qué lo frena?  el primer bloqueante, con el nombre de quien produce el dato que falta
 *   3. ¿Qué sigue?     el ejecutor que declara el grafo
 * Más la edad de la data, porque una orden fresca sobre data vieja es una orden a ciegas
 * (invariante 13). El paso de "una tarjeta por producto" a "una fila por producto" es solo de
 * presentación: la fuente y el cálculo siguen siendo `/api/productos` + `/api/productos/{clave}`
 * (`flujo.py`), igual que en Tablero — nunca se agrega lógica de negocio acá.
 *
 * `getCoreRowModel()`/`getSortedRowModel()` se llaman UNA SOLA VEZ, afuera del componente
 * (`CORE_ROW_MODEL`/`SORTED_ROW_MODEL` abajo) — TanStack Table documenta que llamarlas dentro
 * del render crea una función nueva en cada pasada; acá eso, combinado con un clic real
 * (mousedown/mouseup nativos, no el `fireEvent` sintético de las pruebas), dejaba el clic
 * colgado sin error en pantalla (confirmado con Playwright: `page.mouse.up()` nunca resolvía
 * sobre esta tabla, hasta sacar esas dos llamadas del render).
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
import { useQueries, useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { api, type Flujo, type Producto } from "../api/cliente";
import { useIsMobile } from "@/hooks/use-mobile";
import { tituloDelPasoActual, type MotorInfo } from "../componentes/resumen";
import { Cargando, Chip, Info, Problema } from "../componentes/ui";
import { BanderaMercado, SelectorMercado, usarMercadoSeleccionado } from "../componentes/mercado";
import { filtrarPorMercado } from "../dinero";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ESTADO_PRODUCTO, estadoEnPalabras, faseEnUnaFrase, quienLoHace, rezagoEnPalabras } from "../lenguaje";
import type { ClaveGlosario } from "../glosario";

type Fila = { producto: Producto; flujo?: Flujo };

/** El término del glosario de cada fase, para el (i) de la celda Fase — el mismo mapa que usa
 * la ficha del producto (`ProductoDetalle.tsx`), nunca una segunda opinión. Fases fuera de
 * F1/F2/F3 no llevan (i): no hay glosario que mostrar. */
const CLAVE_GLOSARIO_DE_FASE: Record<string, ClaveGlosario | undefined> = {
  F1: "fase_1",
  F2: "fase_2",
  F3: "fase_3",
};

// Ver el docstring de arriba: llamadas UNA vez, nunca dentro de `Productos()`.
const CORE_ROW_MODEL = getCoreRowModel<Fila>();
const SORTED_ROW_MODEL = getSortedRowModel<Fila>();

/** El rezago DE ESE producto (`flujo.py`), distinto del rezago del sistema que ya muestra el
 * header (`_DECISIONES.json`): un producto puede quedar con su propio motor viejo aunque el
 * resto esté al día — la misma señal que antes daba `BannerRezago` en la tarjeta de Tablero. */
function rezagoDeFila(flujo: Flujo | undefined): string | null {
  const motor = (flujo?.motor ?? null) as MotorInfo | null;
  if (motor?.rezago_dias == null || motor.rezago_dias <= 2) return null;
  return `Rezago de ${motor.rezago_dias} días en la data de este producto`;
}

/** El primer bloqueante en palabras, con su dueño — la misma frase que arma `Hoy.tsx` para "qué
 * sigue en cada producto" (`FilaSiguientePaso`): nunca se calcula distinto según la pantalla. */
function bloqueanteEnPalabras(flujo: Flujo | undefined, quien: string): string {
  if (!flujo) return "…";
  const bloqueantes = flujo.bloqueantes ?? [];
  const primero = bloqueantes[0];
  if (!primero) return "Nada lo frena";
  const extra = bloqueantes.length > 1 ? ` (+${bloqueantes.length - 1} más)` : "";
  return `${primero.dato} · lo produce ${primero.dueno || quien}${extra}`;
}

const columnas: ColumnDef<Fila>[] = [
  {
    id: "producto",
    accessorFn: (f) => f.producto.nombre_display || f.producto.producto_key,
    header: "Producto",
    cell: ({ row }) => {
      const p = row.original.producto;
      return (
        <div className="flex items-start gap-2">
          <Link to="/producto/$clave" params={{ clave: p.producto_key }} className="font-medium hover:underline">
            {p.nombre_display || p.producto_key}
            <span className="block text-xs font-normal text-muted-foreground">{p.producto_key}</span>
          </Link>
          <BanderaMercado mercado={p.mercado} className="mt-0.5" />
        </div>
      );
    },
  },
  {
    id: "fase",
    accessorFn: (f) => f.producto.fase ?? "",
    header: "Fase",
    cell: ({ row }) => {
      const fase = row.original.producto.fase;
      const termino = CLAVE_GLOSARIO_DE_FASE[fase ?? ""];
      return (
        <span className="inline-flex items-center">
          <Badge variant="outline" title={faseEnUnaFrase(fase)}>
            {fase ?? "sin fase"}
          </Badge>
          {termino && <Info termino={termino} />}
        </span>
      );
    },
  },
  {
    id: "paso",
    accessorFn: (f) =>
      tituloDelPasoActual(f.flujo?.nodos, f.flujo?.nodo_actual ?? f.producto.nodo_actual, f.flujo?.como),
    // Sin el (i) del glosario acá adentro: el header de la tabla lo envuelve en un <button> de
    // orden, y anidar el <button> de Info dentro de otro <button> es HTML inválido — el
    // glosario de "nodo" se agrega afuera, como hermano, en el render del <TableHead>.
    header: "Paso actual",
    cell: ({ getValue, row }) => {
      const motor = (row.original.flujo?.motor ?? null) as MotorInfo | null;
      const rezago = rezagoDeFila(row.original.flujo);
      return (
        <div>
          <p>
            {getValue<string>()}
            {rezago && (
              <Chip tono="aviso" titulo={rezago}>
                {motor?.rezago_dias}d de rezago
              </Chip>
            )}
          </p>
          {row.original.producto.nodo_actual && (
            <p className="font-mono text-[11px] text-muted-foreground">{row.original.producto.nodo_actual}</p>
          )}
        </div>
      );
    },
  },
  {
    id: "estado",
    accessorFn: (f) => f.producto.estado_flujo ?? "",
    header: "Estado",
    cell: ({ row }) => {
      const p = row.original.producto;
      const estado = estadoEnPalabras(p.estado_flujo);
      return (
        <span className="inline-flex flex-wrap items-center gap-1">
          <Chip tono={estado.tono}>{estado.texto}</Chip>
          {p.estado && <Chip tono={ESTADO_PRODUCTO[p.estado] ?? "neutro"}>{p.estado}</Chip>}
        </span>
      );
    },
  },
  {
    id: "bloqueante",
    header: () => "Esto lo frena",
    cell: ({ row }) => {
      const { producto, flujo } = row.original;
      const quien = quienLoHace(flujo?.ejecutor || producto.siguiente_ejecutor);
      return <span className="text-sm text-muted-foreground">{bloqueanteEnPalabras(flujo, quien)}</span>;
    },
    enableSorting: false,
  },
  {
    id: "sigue",
    accessorFn: (f) => quienLoHace(f.flujo?.ejecutor || f.producto.siguiente_ejecutor),
    header: "Sigue",
    cell: ({ getValue, row }) => (
      <div>
        <p className="text-sm">{getValue<string>()}</p>
        {(row.original.flujo?.ejecutor || row.original.producto.siguiente_ejecutor) && (
          <p className="text-xs text-muted-foreground">
            {row.original.flujo?.ejecutor || row.original.producto.siguiente_ejecutor}
          </p>
        )}
      </div>
    ),
  },
];

function IconoDeOrden({ estado }: { estado: false | "asc" | "desc" }) {
  if (estado === "asc") return <ArrowUp className="size-3.5" />;
  if (estado === "desc") return <ArrowDown className="size-3.5" />;
  return <ArrowUpDown className="size-3.5 opacity-40" />;
}

export function Productos() {
  const productos = useQuery({ queryKey: ["productos"], queryFn: api.productos });
  const decisiones = useQuery({ queryKey: ["decisiones"], queryFn: api.decisiones });
  const detalles = useQueries({
    queries: (productos.data ?? []).map((p) => ({
      queryKey: ["flujo", p.producto_key],
      queryFn: () => api.producto(p.producto_key),
    })),
  });

  const [busqueda, setBusqueda] = useState("");
  const [mercado, setMercado] = usarMercadoSeleccionado();
  const [orden, setOrden] = useState<SortingState>([]);
  const esMovil = useIsMobile();

  // Memoizado de verdad (no solo `useMemo` con una dependencia que cambia siempre): sin esto,
  // `data` es un array nuevo en cada render, lo que agrava el mismo problema que las factories
  // de arriba — TanStack recalcula de más en cada pasada.
  const datosDeFlujo = detalles.map((d) => d.data);
  const filas: Fila[] = useMemo(
    () => (productos.data ?? []).map((producto, i) => ({ producto, flujo: datosDeFlujo[i] })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [productos.data, ...datosDeFlujo],
  );

  const filasFiltradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const delMercado = filtrarPorMercado(
      filas.map((f) => ({ ...f, mercado: f.producto.mercado })),
      mercado,
    ).map(({ producto, flujo }) => ({ producto, flujo }));
    if (!q) return delMercado;
    return delMercado.filter(({ producto }) =>
      [producto.producto_key, producto.nombre_display, producto.fase, producto.estado_flujo]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q)),
    );
  }, [filas, busqueda, mercado]);

  const tabla = useReactTable({
    data: filasFiltradas,
    columns: columnas,
    state: { sorting: orden },
    onSortingChange: setOrden,
    getCoreRowModel: CORE_ROW_MODEL,
    getSortedRowModel: SORTED_ROW_MODEL,
  });

  if (productos.isLoading) return <Cargando que="el portafolio" />;
  if (productos.error) return <Problema error={productos.error} />;

  const rezago = rezagoEnPalabras(decisiones.data?.rezago_dias);
  const filasRenderizadas = tabla.getRowModel().rows;
  // Contar filas no es calcular el negocio: se cuenta lo que hay en pantalla y cuántas de
  // esas filas muestran bloqueantes — el mismo campo que lee la columna "Esto lo frena".
  const frenados = filasRenderizadas.filter((fila) => (fila.original.flujo?.bloqueantes?.length ?? 0) > 0).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Portafolio</h1>
          <p className="text-sm text-muted-foreground">
            Dónde está cada producto, qué lo bloquea y qué sigue. La fase se deriva de la data;
            nadie la declara a mano.
          </p>
          {filasRenderizadas.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {`${filasRenderizadas.length} producto${filasRenderizadas.length === 1 ? "" : "s"} · ${frenados} frenado${frenados === 1 ? "" : "s"}`}
            </p>
          )}
        </div>
        <Chip tono={rezago.tono} titulo="Hasta cuándo llega la data de ventas">
          {rezago.texto}
          {decisiones.data?.datos_hasta ? ` (hasta ${decisiones.data.datos_hasta})` : ""}
        </Chip>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Mercado</span>
        <SelectorMercado seleccion={mercado} onCambiar={setMercado} />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Input
          placeholder="Buscar por producto, fase o estado…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="max-w-xs"
        />
        <Button size="sm" render={<Link to="/nuevo" />}>
          Nuevo producto
        </Button>
      </div>

      {filasRenderizadas.length === 0 ? (
        <Card>
          <CardContent className="space-y-4 py-6 text-center text-sm text-muted-foreground">
            {busqueda ? (
              "Ningún producto coincide con la búsqueda."
            ) : (productos.data ?? []).length > 0 ? (
              "No hay productos de este mercado."
            ) : (
              <>
                <p>Todavía no hay productos cargados.</p>
                <Button render={<Link to="/nuevo" />}>Dar de alta un producto</Button>
              </>
            )}
          </CardContent>
        </Card>
      ) : esMovil ? (
        /* Móvil (< 768px): las mismas filas, apiladas en tarjetas — sin scroll horizontal. Es
           una decisión de JS (useIsMobile, igual que el propio Sidebar de shadcn en T1), no de
           CSS: nunca hay dos copias de cada fila en el DOM a la vez. */
        <div className="space-y-3">
          {filasRenderizadas.map((fila) => {
            const { producto, flujo } = fila.original;
            const estado = estadoEnPalabras(producto.estado_flujo);
            const quien = quienLoHace(flujo?.ejecutor || producto.siguiente_ejecutor);
            const paso = tituloDelPasoActual(flujo?.nodos, flujo?.nodo_actual ?? producto.nodo_actual, flujo?.como);
            const rezagoFila = rezagoDeFila(flujo);
            const diasRezago = ((flujo?.motor ?? null) as MotorInfo | null)?.rezago_dias ?? null;
            return (
              <Link key={producto.producto_key} to="/producto/$clave" params={{ clave: producto.producto_key }}>
                <Card className="transition-colors hover:bg-muted/50">
                  <CardContent className="space-y-2 pt-4 text-sm">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="flex items-center gap-2 font-medium">
                          {producto.nombre_display || producto.producto_key}
                          <BanderaMercado mercado={producto.mercado} />
                        </p>
                        <p className="text-xs text-muted-foreground">{producto.producto_key}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge variant="outline" title={faseEnUnaFrase(producto.fase)}>
                          {producto.fase ?? "sin fase"}
                        </Badge>
                        <span className="flex flex-wrap justify-end gap-1">
                          <Chip tono={estado.tono}>{estado.texto}</Chip>
                          {producto.estado && (
                            <Chip tono={ESTADO_PRODUCTO[producto.estado] ?? "neutro"}>{producto.estado}</Chip>
                          )}
                        </span>
                      </div>
                    </div>
                    <p>
                      {paso}
                      {rezagoFila && (
                        <Chip tono="aviso" titulo={rezagoFila}>
                          {diasRezago}d de rezago
                        </Chip>
                      )}
                      {producto.nodo_actual && (
                        <span className="ml-1 font-mono text-[11px] text-muted-foreground">
                          {producto.nodo_actual}
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">{bloqueanteEnPalabras(flujo, quien)}</p>
                    <p className="text-xs text-muted-foreground">{quien}</p>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      ) : (
        <Table>
          <TableHeader>
            {tabla.getHeaderGroups().map((grupo) => (
              <TableRow key={grupo.id}>
                {grupo.headers.map((header) => (
                  <TableHead key={header.id}>
                    <span className="inline-flex items-center gap-1">
                      {header.column.getCanSort() ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 hover:text-foreground"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          <IconoDeOrden estado={header.column.getIsSorted()} />
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                      {/* Nunca anidado dentro del <button> de arriba: dos controles interactivos
                          uno dentro del otro es HTML inválido y rompe el click (confirmado con
                          Playwright — el clic sobre el (i) quedaba colgado). */}
                      {header.column.id === "paso" && <Info termino="nodo" />}
                    </span>
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {filasRenderizadas.map((fila) => (
              <TableRow key={fila.id} data-producto={fila.original.producto.producto_key}>
                {fila.getVisibleCells().map((celda) => (
                  <TableCell key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
