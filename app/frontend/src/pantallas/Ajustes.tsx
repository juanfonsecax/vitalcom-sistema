/**
 * Ajustes.tsx — página de configuración estilo Linear (T5).
 *
 * Reemplaza la grilla de enlaces de T1 por tres secciones verticales:
 *   1. Cuentas publicitarias — solo lectura, `GET /api/cuentas` (`_DIM_CUENTAS.csv`).
 *   2. FanPages — solo lectura, `GET /api/fanpages` (`_DIM_FANPAGES.csv`, nuevo en T5). El
 *      archivo puede no existir todavía en la carpeta donde corre la app (se declaró en otra
 *      rama de SISTEMA): el backend nunca truena por eso, devuelve lista vacía.
 *   3. Sistema — la maquinaria, de-enfatizada: Salud, Trabajos (con su badge de pendientes),
 *      Órdenes, Guía, Nuevo producto, más la carpeta sobre la que corre la app (`GET /api/sistema`).
 *
 * La app no calcula nada acá tampoco: cada tabla es el CSV tal cual, sin traducir ni derivar.
 */
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, HeartPulse, PlusCircle, Receipt, Wrench } from "lucide-react";

import { api } from "../api/cliente";
import { Cargando, Problema } from "../componentes/ui";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const ENLACES_SISTEMA = [
  {
    a: "/ordenes",
    titulo: "Órdenes de hoy",
    descripcion: "El listado operativo de órdenes del día, tal como estaba antes del rediseño.",
    icono: Receipt,
  },
  {
    a: "/trabajos",
    titulo: "Trabajos",
    descripcion: "Lo que el runner está haciendo y lo que espera que confirmes.",
    icono: Wrench,
    contadorClave: "trabajos" as const,
  },
  {
    a: "/salud",
    titulo: "Salud del sistema",
    descripcion: "Chequeos de integridad: CSV, gates y consistencia entre archivos.",
    icono: HeartPulse,
  },
  {
    a: "/guia",
    titulo: "Guía",
    descripcion: "Cómo correr el sistema, paso a paso.",
    icono: BookOpen,
  },
  {
    a: "/nuevo",
    titulo: "Nuevo producto",
    descripcion: "Arrancar un producto desde cero (FASE 0 / FASE 1).",
    icono: PlusCircle,
  },
];

function SeccionCuentas() {
  const cuentas = useQuery({ queryKey: ["cuentas"], queryFn: api.cuentas });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cuentas publicitarias</CardTitle>
        <p className="text-sm text-muted-foreground">
          El portafolio de cuentas de Meta (`_DIM_CUENTAS.csv`): alias, moneda y qué permite cada
          una. Solo lectura.
        </p>
      </CardHeader>
      <CardContent>
        {cuentas.isLoading && <Cargando que="las cuentas" />}
        {cuentas.isError && <Problema error={cuentas.error} />}
        {cuentas.data && cuentas.data.length === 0 && (
          <p className="text-sm text-muted-foreground">Todavía no hay cuentas en _DIM_CUENTAS.csv.</p>
        )}
        {cuentas.data && cuentas.data.length > 0 && (
          <div className="flex flex-col gap-3 sm:hidden">
            {cuentas.data.map((cuenta) => (
              <div key={cuenta.cuenta_alias} className="rounded-lg border border-border p-3 text-sm">
                <div className="font-medium">{cuenta.cuenta_alias}</div>
                <dl className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-muted-foreground">
                  <dt>Moneda</dt>
                  <dd className="text-right">{cuenta.moneda}</dd>
                  <dt>MCP</dt>
                  <dd className="text-right">{cuenta.mcp_habilitado}</dd>
                  <dt>Media local</dt>
                  <dd className="text-right">{cuenta.sube_media_local}</dd>
                  <dt>Estado</dt>
                  <dd className="text-right">{cuenta.estado_cuenta}</dd>
                </dl>
              </div>
            ))}
          </div>
        )}
        {cuentas.data && cuentas.data.length > 0 && (
          <Table className="hidden sm:table">
            <TableHeader>
              <TableRow>
                <TableHead>Alias</TableHead>
                <TableHead>Moneda</TableHead>
                <TableHead>MCP</TableHead>
                <TableHead>Media local</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cuentas.data.map((cuenta) => (
                <TableRow key={cuenta.cuenta_alias}>
                  <TableCell className="font-medium">{cuenta.cuenta_alias}</TableCell>
                  <TableCell>{cuenta.moneda}</TableCell>
                  <TableCell>{cuenta.mcp_habilitado}</TableCell>
                  <TableCell>{cuenta.sube_media_local}</TableCell>
                  <TableCell>{cuenta.estado_cuenta}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function SeccionFanPages() {
  const fanpages = useQuery({ queryKey: ["fanpages"], queryFn: api.fanpages });

  return (
    <Card>
      <CardHeader>
        <CardTitle>FanPages</CardTitle>
        <p className="text-sm text-muted-foreground">
          Las 10 FanPages del catálogo (`_DIM_FANPAGES.csv`): identidad, tono, edad de
          orientación y productos del nicho. Solo lectura.
        </p>
      </CardHeader>
      <CardContent>
        {fanpages.isLoading && <Cargando que="las FanPages" />}
        {fanpages.isError && <Problema error={fanpages.error} />}
        {fanpages.data && fanpages.data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Todavía no hay FanPages declaradas en _DIM_FANPAGES.csv.
          </p>
        )}
        {fanpages.data && fanpages.data.length > 0 && (
          <div className="flex flex-col gap-3 sm:hidden">
            {fanpages.data.map((pagina) => (
              <div key={pagina.pagina_num} className="rounded-lg border border-border p-3 text-sm">
                <div className="font-medium">{pagina.pagina_nombre}</div>
                <p className="mt-1 text-xs text-muted-foreground">{pagina.identidad}</p>
                <dl className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-muted-foreground">
                  <dt>Tono</dt>
                  <dd className="text-right">{pagina.tono}</dd>
                  <dt>Edad</dt>
                  <dd className="text-right">{pagina.edad_orientacion}</dd>
                  <dt>Productos del nicho</dt>
                  <dd className="text-right">{pagina.productos_nicho}</dd>
                </dl>
              </div>
            ))}
          </div>
        )}
        {fanpages.data && fanpages.data.length > 0 && (
          <Table className="hidden sm:table">
            <TableHeader>
              <TableRow>
                <TableHead>Página</TableHead>
                <TableHead>Identidad</TableHead>
                <TableHead>Tono</TableHead>
                <TableHead>Edad de orientación</TableHead>
                <TableHead>Productos del nicho</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fanpages.data.map((pagina) => (
                <TableRow key={pagina.pagina_num}>
                  <TableCell className="font-medium">{pagina.pagina_nombre}</TableCell>
                  <TableCell>{pagina.identidad}</TableCell>
                  <TableCell>{pagina.tono}</TableCell>
                  <TableCell>{pagina.edad_orientacion}</TableCell>
                  <TableCell>{pagina.productos_nicho}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function SeccionSistema() {
  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const sistema = useQuery({ queryKey: ["sistema"], queryFn: api.sistema });
  const pendientes = (trabajos.data ?? []).filter((t) => t.pendiente).length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sistema</CardTitle>
        <p className="text-sm text-muted-foreground">
          La maquinaria interna: solo hace falta entrar acá cuando algo no cuadra.
        </p>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {ENLACES_SISTEMA.map(({ a, titulo, descripcion, icono: Icono, contadorClave }) => (
            <Link
              key={a}
              to={a}
              aria-label={titulo}
              className="group flex items-start gap-3 rounded-xl border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
            >
              <Icono className="mt-0.5 size-5 shrink-0 text-muted-foreground group-hover:text-accent-foreground" />
              <div className="flex-1">
                <div className="flex items-center gap-2 font-medium">
                  {titulo}
                  {contadorClave === "trabajos" && pendientes > 0 && (
                    <Badge
                      variant="secondary"
                      title="Trabajos que esperan tu aprobación o tu respuesta"
                      className="bg-estado-seguir text-estado-seguir-foreground"
                    >
                      {pendientes}
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{descripcion}</p>
              </div>
              <ArrowUpRight className="mt-0.5 size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          ))}
        </div>
        {sistema.data && (
          <p className="font-mono text-xs text-muted-foreground">Corriendo sobre: {sistema.data.base}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function Ajustes() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">Ajustes</h1>
        <p className="text-sm text-muted-foreground">
          Cuentas, FanPages y la maquinaria del sistema, en un solo lugar.
        </p>
      </div>
      <SeccionCuentas />
      <SeccionFanPages />
      <SeccionSistema />
    </div>
  );
}
