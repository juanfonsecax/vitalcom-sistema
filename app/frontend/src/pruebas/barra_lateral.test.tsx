/**
 * barra_lateral.test.tsx — el marco de navegación.
 *
 * Lo que se verifica: que las cinco secciones fijas (Hoy · Productos · Resultados ·
 * Trabajos · Ajustes) estén siempre presentes, y que la sección de la URL actual quede
 * marcada activa — incluso cuando la URL es una hija de Productos (`/producto/$clave`)
 * o de Trabajos (`/trabajos/$id`), que siguen vivas sin ítem propio en la barra.
 */
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
  createMemoryHistory,
} from "@tanstack/react-router";
import { beforeEach, expect, test, vi } from "vitest";
import { Marco } from "../componentes/BarraLateral";

function servir() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => [] }) as Response),
  );
}

function montar(ruta: string) {
  const raiz = createRootRoute({ component: () => <Marco>{null}</Marco> });
  const paginaVacia = () => null;
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/productos", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/resultados", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos/$id", component: paginaVacia }),
    createRoute({ getParentRoute: () => raiz, path: "/ajustes", component: paginaVacia }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: [ruta] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  servir();
});

test("la barra lateral muestra exactamente las cinco secciones fijas", async () => {
  montar("/");
  expect(await screen.findByRole("link", { name: "Hoy" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Productos" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Resultados" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Trabajos" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ajustes" })).toBeInTheDocument();
});

test("marca Trabajos activo en /trabajos/$id, aunque esa ruta no tenga ítem propio", async () => {
  montar("/trabajos/job-1");
  const trabajos = await screen.findByRole("link", { name: "Trabajos" });
  const hoy = screen.getByRole("link", { name: "Hoy" });
  expect(trabajos).toHaveAttribute("data-active");
  expect(hoy).not.toHaveAttribute("data-active");
});

test("marca Hoy activo en la raíz", async () => {
  montar("/");
  const hoy = await screen.findByRole("link", { name: "Hoy" });
  const productos = screen.getByRole("link", { name: "Productos" });
  expect(hoy).toHaveAttribute("data-active");
  expect(productos).not.toHaveAttribute("data-active");
});

test("marca Productos activo en /producto/$clave, aunque esa ruta no tenga ítem propio", async () => {
  montar("/producto/OVULOS_PURITY");
  const productos = await screen.findByRole("link", { name: "Productos" });
  const hoy = screen.getByRole("link", { name: "Hoy" });
  expect(productos).toHaveAttribute("data-active");
  expect(hoy).not.toHaveAttribute("data-active");
});

test("marca Ajustes activo en /ajustes", async () => {
  montar("/ajustes");
  const ajustes = await screen.findByRole("link", { name: "Ajustes" });
  expect(ajustes).toHaveAttribute("data-active");
});
