/**
 * Ajustes.tsx — punta de entrada a las pantallas viejas.
 *
 * Cuentas, FanPages, salud del sistema, trabajos y la guía se organizaban antes por
 * maquinaria interna; hasta que T3/T5 las absorban dentro de Productos/Ajustes de verdad,
 * quedan accesibles acá, en sus URLs de siempre.
 */
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, HeartPulse, PlusCircle, Receipt, Wrench } from "lucide-react";

import { api } from "../api/cliente";

const ENLACES = [
  {
    a: "/ordenes",
    titulo: "Órdenes de hoy",
    descripcion: "El listado operativo de órdenes del día, tal como estaba antes de este rediseño.",
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

export function Ajustes() {
  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const pendientes = (trabajos.data ?? []).filter((t) => t.pendiente).length;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">Ajustes</h1>
        <p className="text-sm text-muted-foreground">
          Cuentas, FanPages y las pantallas de siempre, mientras se reorganizan bajo Hoy /
          Productos / Resultados.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {ENLACES.map(({ a, titulo, descripcion, icono: Icono, contadorClave }) => (
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
                  <span
                    title="Trabajos que esperan tu aprobación o tu respuesta"
                    className="rounded-full bg-estado-seguir px-1.5 py-0.5 text-[10px] font-semibold text-estado-seguir-foreground"
                  >
                    {pendientes}
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{descripcion}</p>
            </div>
            <ArrowUpRight className="mt-0.5 size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        ))}
      </div>
    </div>
  );
}
