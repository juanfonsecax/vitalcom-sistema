import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, test, vi } from "vitest";
import { FranjaMetaFalso } from "../componentes/FranjaMetaFalso";

function servir(metaFalso: boolean) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const ruta = new URL(url, "http://localhost").pathname;
      if (ruta === "/api/claude/estado") {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            logueado: true,
            detalle: "yo@x.com",
            credencial_prohibida: [],
            meta_falso: metaFalso,
          }),
        } as Response;
      }
      return { ok: false, status: 404, json: async () => ({}) } as Response;
    }),
  );
}

function montar() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <FranjaMetaFalso />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

test("la franja roja de META FALSO se muestra si la perilla está activa", async () => {
  servir(true);
  montar();
  expect(await screen.findByRole("alert")).toBeInTheDocument();
  expect(screen.getByText(/META FALSO — nada llega a Meta/)).toBeInTheDocument();
});

test("la franja roja no se muestra si la perilla está inactiva", async () => {
  servir(false);
  montar();
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.queryByText(/META FALSO — nada llega a Meta/)).toBeNull();
});
