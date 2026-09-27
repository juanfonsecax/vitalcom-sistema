/**
 * BarraLateral.tsx — navegación principal, estilo Linear.
 *
 * Cinco entradas fijas (Hoy · Productos · Resultados · Trabajos · Ajustes): las cuatro
 * preguntas del operador, más la sala de máquinas. Trabajos subió al menú principal
 * (antes vivía solo detrás de Ajustes) porque es la ÚNICA pantalla desde la que se
 * aprueban acciones en Meta, orden por orden — y su insignia de pendientes vive acá.
 * Las pantallas internas (Órdenes, Salud, Guía, Nuevo producto) siguen en sus URLs de
 * siempre y se alcanzan desde Ajustes; Órdenes también se enlaza desde Hoy, cuyo
 * detalle del motor extiende.
 *
 * Colapsa a solo-íconos en escritorio (SidebarTrigger) y se vuelve panel off-canvas
 * (Sheet) bajo 768px — ambos comportamientos vienen del componente `Sidebar` de shadcn/ui.
 */
import type { ReactNode } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { CalendarCheck, ListChecks, Package, Settings, SlidersHorizontal } from "lucide-react";

import { api } from "../api/cliente";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";

type ClaveNav = "hoy" | "productos" | "resultados" | "trabajos" | "ajustes";

const RUTAS_AJUSTES = ["/ajustes", "/ordenes", "/salud", "/guia", "/nuevo"];

function claveActiva(ruta: string): ClaveNav {
  if (ruta === "/") return "hoy";
  if (ruta === "/productos" || ruta.startsWith("/producto/")) return "productos";
  if (ruta === "/resultados") return "resultados";
  if (ruta === "/trabajos" || ruta.startsWith("/trabajos/")) return "trabajos";
  return RUTAS_AJUSTES.some((base) => ruta === base || ruta.startsWith(`${base}/`)) ? "ajustes" : "hoy";
}


function BarraLateral() {
  const { pathname } = useLocation();
  const activa = claveActiva(pathname);
  const trabajos = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const pendientes = (trabajos.data ?? []).filter((t) => t.pendiente).length;

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-1.5 text-sm font-semibold tracking-tight">
          <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs">
            V
          </span>
          <span className="truncate group-data-[collapsible=icon]:hidden">
            VitalCom <span className="text-muted-foreground">Guatemala</span>
          </span>
          <SidebarTrigger className="ml-auto hidden md:flex" />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton render={<Link to="/" />} isActive={activa === "hoy"} tooltip="Hoy">
                  <CalendarCheck />
                  <span>Hoy</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  render={<Link to="/productos" />}
                  isActive={activa === "productos"}
                  tooltip="Productos"
                >
                  <Package />
                  <span>Productos</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  render={<Link to="/resultados" />}
                  isActive={activa === "resultados"}
                  tooltip="Resultados"
                >
                  <SlidersHorizontal />
                  <span>Resultados</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  render={<Link to="/trabajos" />}
                  isActive={activa === "trabajos"}
                  tooltip="Trabajos"
                >
                  <ListChecks />
                  <span>Trabajos</span>
                </SidebarMenuButton>
                {pendientes > 0 && (
                  <SidebarMenuBadge title="Trabajos que esperan tu aprobación o tu respuesta">
                    {pendientes}
                  </SidebarMenuBadge>
                )}
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton render={<Link to="/ajustes" />} isActive={activa === "ajustes"} tooltip="Ajustes">
                  <Settings />
                  <span>Ajustes</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}

/** El marco de toda la app: barra lateral + barra superior angosta (con el disparador móvil) + contenido. */
export function Marco({ banner, children }: { banner?: ReactNode; children: ReactNode }) {
  return (
    <SidebarProvider>
      <BarraLateral />
      <SidebarInset>
        {banner}
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-3 md:hidden">
          <SidebarTrigger />
          <span className="text-sm font-semibold tracking-tight">
            VitalCom <span className="text-muted-foreground">Guatemala</span>
          </span>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
