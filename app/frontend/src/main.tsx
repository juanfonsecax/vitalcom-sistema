/**
 * main.tsx — arranque, rutas y caché.
 *
 * Tres pantallas en el Hito 1: Portafolio, Producto y Salud. Todas de solo lectura.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
import "./estilos.css";

function Marco() {
  return (
    <div className="min-h-screen">
      <nav className="border-b border-zinc-800 bg-zinc-900/60">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
          <span className="font-semibold tracking-tight">
            VitalCom <span className="text-zinc-500">Guatemala</span>
          </span>
          <Link to="/" className="text-sm text-zinc-400 hover:text-zinc-100" activeProps={{ className: "text-sm text-sky-300" }}>
            Portafolio
          </Link>
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
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/salud", component: Salud }),
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
