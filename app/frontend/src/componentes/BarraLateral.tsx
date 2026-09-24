/**
 * BarraLateral.tsx — navegación principal, estilo Linear.
 *
 * Cuatro secciones fijas (Hoy · Productos · Resultados · Ajustes): las preguntas del
 * operador, no la maquinaria interna. Las pantallas viejas (Fase1/2/3, Trabajos, Salud,
 * Guía, Órdenes, Nuevo producto) siguen en sus URLs de siempre; Ajustes es su punto de
 * entrada mientras T2-T5 las absorben.
 *
 * Colapsa a solo-íconos en escritorio (SidebarTrigger) y se vuelve panel off-canvas
 * (Sheet) bajo 768px — ambos comportamientos vienen del componente `Sidebar` de shadcn/ui.
 */
import { useState, type ReactNode } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { CalendarCheck, ChevronsUpDown, Laptop, Moon, Package, Settings, SlidersHorizontal, Sun } from "lucide-react";

import { api } from "../api/cliente";
import { useTema, type Tema } from "./tema";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";

type ClaveNav = "hoy" | "productos" | "resultados" | "ajustes";

const RUTAS_AJUSTES = ["/ajustes", "/ordenes", "/trabajos", "/salud", "/guia", "/nuevo"];

function claveActiva(ruta: string): ClaveNav {
  if (ruta === "/") return "hoy";
  if (ruta === "/productos" || ruta.startsWith("/producto/")) return "productos";
  if (ruta === "/resultados") return "resultados";
  return RUTAS_AJUSTES.some((base) => ruta === base || ruta.startsWith(`${base}/`)) ? "ajustes" : "hoy";
}

const OPCIONES_TEMA: { valor: Tema; etiqueta: string; icono: ReactNode }[] = [
  { valor: "light", etiqueta: "Claro", icono: <Sun className="size-4" /> },
  { valor: "dark", etiqueta: "Oscuro", icono: <Moon className="size-4" /> },
  { valor: "system", etiqueta: "Del sistema", icono: <Laptop className="size-4" /> },
];

/** Alternador claro/oscuro/sistema, en el pie de la barra lateral. */
function AlternadorTema() {
  const { tema, setTema } = useTema();
  const [abierto, setAbierto] = useState(false);
  const actual = OPCIONES_TEMA.find((o) => o.valor === tema) ?? OPCIONES_TEMA[2];
  return (
    <DropdownMenu open={abierto} onOpenChange={setAbierto}>
      <DropdownMenuTrigger
        render={
          <SidebarMenuButton>
            {actual.icono}
            <span>Tema: {actual.etiqueta}</span>
            <ChevronsUpDown className="ml-auto size-3.5 opacity-60" />
          </SidebarMenuButton>
        }
      />
      <DropdownMenuContent align="start" className="w-48">
        {OPCIONES_TEMA.map((opcion) => (
          <DropdownMenuItem key={opcion.valor} onClick={() => setTema(opcion.valor)}>
            {opcion.icono}
            {opcion.etiqueta}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
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
                <SidebarMenuButton render={<Link to="/productos" />} isActive={activa === "productos"} tooltip="Productos">
                  <Package />
                  <span>Productos</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton render={<Link to="/resultados" />} isActive={activa === "resultados"} tooltip="Resultados">
                  <SlidersHorizontal />
                  <span>Resultados</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton render={<Link to="/ajustes" />} isActive={activa === "ajustes"} tooltip="Ajustes">
                  <Settings />
                  <span>Ajustes</span>
                </SidebarMenuButton>
                {pendientes > 0 && (
                  <SidebarMenuBadge title="Trabajos que esperan tu aprobación o tu respuesta">
                    {pendientes}
                  </SidebarMenuBadge>
                )}
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <Separator className="mb-1" />
        <SidebarMenu>
          <SidebarMenuItem>
            <AlternadorTema />
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
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
