/**
 * main.tsx — arranque, rutas y caché.
 *
 * Portafolio, Producto, Nuevo producto, Trabajos (lo que el runner hace y espera de vos) y Salud.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import {
  Link,
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { Tablero } from "./pantallas/Tablero";
import { ProductoDetalle } from "./pantallas/ProductoDetalle";
import { Salud } from "./pantallas/Salud";
import { NuevoProducto } from "./pantallas/NuevoProducto";
import { Trabajos } from "./pantallas/Trabajos";
import { Fase1 } from "./pantallas/Fase1";
import { Ordenes } from "./pantallas/Ordenes";
import { api } from "./api/cliente";
import "./estilos.css";

/** «Trabajos» con una insignia cuando algo espera una decisión del operador. */
function EnlaceDeTrabajos() {
  const lista = useQuery({ queryKey: ["trabajos"], queryFn: api.trabajos, refetchInterval: 5000 });
  const esperan = (lista.data ?? []).filter((t) => t.pendiente).length;
  return (
    <Link to="/trabajos" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
      Trabajos
      {esperan > 0 && (
        <span
          title="Trabajos que esperan tu aprobación o tu respuesta"
          className="ml-1.5 rounded-full bg-amber-600 px-1.5 py-0.5 text-[10px] font-semibold text-white"
        >
          {esperan}
        </span>
      )}
    </Link>
  );
}

import { FranjaMetaFalso } from "./componentes/FranjaMetaFalso";

function Marco() {
  return (
    <div className="min-h-screen">
      <FranjaMetaFalso />
      <nav className="border-b border-zinc-800 bg-zinc-900/60">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
          <span className="font-semibold tracking-tight">
            VitalCom <span className="text-zinc-500">Guatemala</span>
          </span>
          <Link to="/" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
            Portafolio
          </Link>
          <Link to="/ordenes" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
            Órdenes de hoy
          </Link>
          <Link to="/nuevo" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
            Nuevo producto
          </Link>
          <EnlaceDeTrabajos />
          <Link to="/salud" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
            Salud
          </Link>
        </div>
      </nav>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

const raiz = createRootRoute({ component: Marco });
const rutas = [
  createRoute({ getParentRoute: () => raiz, path: "/", component: Tablero }),
  createRoute({ getParentRoute: () => raiz, path: "/ordenes", component: Ordenes }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase1", component: Fase1 }),
  createRoute({ getParentRoute: () => raiz, path: "/salud", component: Salud }),
  createRoute({ getParentRoute: () => raiz, path: "/nuevo", component: NuevoProducto }),
  createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: Trabajos }),
  createRoute({ getParentRoute: () => raiz, path: "/trabajos/$id", component: Trabajos }),
];

const router = createRouter({ routeTree: raiz.addChildren(rutas) });
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// El motor tarda ~1,5 s por producto: sin reintentos ni refetch al enfocar la ventana.
const cliente = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false, staleTime: 30_000 } },
});

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
