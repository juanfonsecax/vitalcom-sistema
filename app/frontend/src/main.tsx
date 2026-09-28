/**
 * main.tsx — arranque, rutas y caché.
 *
 * Navegación por las preguntas del operador (Hoy / Productos / Resultados / Ajustes,
 * ver componentes/BarraLateral.tsx). Productos (P4/T3) es una tabla; Fase1/2/3 quedaron
 * absorbidas NAVEGACIONALMENTE dentro de ProductoDetalle, como pestañas — sus URLs viejas
 * (`/producto/$clave/faseN`) siguen funcionando. Trabajos, Salud, Guía, Órdenes y Nuevo
 * producto siguen en sus URLs de siempre, alcanzables desde Ajustes.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Outlet, RouterProvider, createRootRoute, createRoute, createRouter } from "@tanstack/react-router";
import { Hoy } from "./pantallas/Hoy";
import { Productos } from "./pantallas/Productos";
import { ProductoDetalle } from "./pantallas/ProductoDetalle";
import { Salud } from "./pantallas/Salud";
import { NuevoProducto } from "./pantallas/NuevoProducto";
import { Trabajos } from "./pantallas/Trabajos";
import { Ordenes } from "./pantallas/Ordenes";
import { Guia } from "./pantallas/Guia";
import { Resultados } from "./pantallas/Resultados";
import { Ajustes } from "./pantallas/Ajustes";
import { FranjaMetaFalso } from "./componentes/FranjaMetaFalso";
import { Marco as MarcoBarraLateral } from "./componentes/BarraLateral";
import "./estilos.css";

function Marco() {
  return (
    <MarcoBarraLateral banner={<FranjaMetaFalso />}>
      <Outlet />
    </MarcoBarraLateral>
  );
}

const raiz = createRootRoute({ component: Marco });
const rutas = [
  createRoute({ getParentRoute: () => raiz, path: "/", component: Hoy }),
  createRoute({ getParentRoute: () => raiz, path: "/productos", component: Productos }),
  createRoute({ getParentRoute: () => raiz, path: "/resultados", component: Resultados }),
  createRoute({ getParentRoute: () => raiz, path: "/ajustes", component: Ajustes }),
  createRoute({ getParentRoute: () => raiz, path: "/ordenes", component: Ordenes }),
  // Las cinco rutas del producto comparten un solo componente: ProductoDetalle lee el pathname
  // para decidir la pestaña activa (Resumen/Fase 1/2/3/4) — ver su docstring (P4/T3).
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase1", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase2", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase3", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/producto/$clave/fase4", component: ProductoDetalle }),
  createRoute({ getParentRoute: () => raiz, path: "/salud", component: Salud }),
  createRoute({ getParentRoute: () => raiz, path: "/guia", component: Guia }),
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
