/**
 * arranque.test.tsx — «datos para arrancar» en la ficha del producto.
 *
 * Congela: el encabezado muestra la foto (y la amplía) o el botón para subirla; el formulario de la
 * foto llama a la acción `producto.cargar_packshot` con el archivo y lo declarado; la tarjeta «Para
 * arrancar te falta» lista SOLO lo que falta, con el arreglo en línea de cada cosa que tiene escritor,
 * una frase (sin comandos) para lo que no lo tiene, y desaparece cuando no falta nada.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { afterEach, expect, test, vi } from "vitest";
import { ProductoDetalle } from "../pantallas/ProductoDetalle";

const FLUJO = {
  producto_key: "CLEARSTEM",
  nombre: "Clearstem",
  estado_producto: "VIVO",
  fase: "PAUSADO",
  fase_titulo: "",
  nodo_actual: null,
  estado: "EXCEPCION",
  ejecutor: "",
  como: "",
  evaluado_el: "2026-09-28",
  bloqueantes: [],
  falta_para_cumplir: [],
  entradas: [],
  nodos: [],
  avisos: [],
  ordenes: [],
};

const ITEM_OK = { clave: "costo_q", rotulo: "Costo del producto", estado: "ok", detalle: "Q57", como_resolver: "", accion: null };
const FALTA_FOTO = {
  clave: "packshot",
  rotulo: "Foto del producto (packshot)",
  estado: "falta",
  detalle: "No hay foto declarada.",
  como_resolver: "Subí la foto del producto tal como se ve en la mano.",
  accion: "producto.cargar_packshot",
};
const FALTA_PAGE = {
  clave: "page_id",
  rotulo: "Página de Facebook",
  estado: "falta",
  detalle: "Falta el page_id.",
  como_resolver: "Pegá el número de la página de Facebook.",
  accion: "producto.cargar_page_id",
};
const FALTA_PRECIO = {
  clave: "precio",
  rotulo: "Precio de venta",
  estado: "falta",
  detalle: "No hay una escalera de precios activa.",
  como_resolver: "Pasale a Claude a cuánto vendés 1, 2 y 3 unidades y él la deja cargada.",
  accion: null,
};

function datos(items: unknown[], packshot: unknown = null) {
  const faltan = (items as { estado: string }[]).filter((i) => i.estado === "falta").length;
  return { ok: true, producto_key: "CLEARSTEM", completo: faltan === 0, faltan, packshot, items, avisos: [] };
}

const PACKSHOT = {
  archivo: "CLEARSTEM_PACKSHOT.png",
  url: "/api/productos/CLEARSTEM/media/CLEARSTEM_PACKSHOT.png",
  marca_impresa: "CLEARSTEM",
  color_envase: "blanco",
  formato_envase: "frasco 60 cápsulas",
};

const llamadas: { url: string; init?: RequestInit }[] = [];

function servir(respuestas: Record<string, unknown>) {
  llamadas.length = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      llamadas.push({ url, init });
      const cuerpo = respuestas[new URL(url, "http://x").pathname];
      return { ok: cuerpo !== undefined, status: cuerpo === undefined ? 404 : 200, json: async () => cuerpo } as Response;
    }),
  );
}

function montar() {
  const raiz = createRootRoute();
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/productos", component: () => null }),
    createRoute({ getParentRoute: () => raiz, path: "/producto/$clave", component: ProductoDetalle }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: ["/producto/CLEARSTEM"] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

test("con packshot, el encabezado muestra la miniatura y un clic la amplía", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([ITEM_OK], PACKSHOT),
  });
  montar();
  const foto = await screen.findByAltText("Foto de Clearstem");
  expect(foto).toHaveAttribute("src", PACKSHOT.url);
  expect(screen.queryByText("Subí la foto del producto")).not.toBeInTheDocument();
  fireEvent.click(foto.closest("button")!);
  expect(screen.getAllByAltText("Foto de Clearstem")).toHaveLength(2);
});

test("sin packshot, el encabezado ofrece subirla y el formulario explica para qué sirve", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([FALTA_FOTO]),
  });
  montar();
  const boton = await screen.findByRole("button", { name: "Subí la foto del producto" });
  expect(screen.queryByAltText("Foto de Clearstem")).not.toBeInTheDocument();
  fireEvent.click(boton);
  expect(await screen.findByText(/para que el producto salga igual en todos los anuncios/)).toBeInTheDocument();
  expect(screen.getByLabelText("Marca impresa")).toBeInTheDocument();
  expect(screen.getByLabelText("Color del envase")).toBeInTheDocument();
  expect(screen.getByLabelText("Formato del envase")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Guardar foto" })).toBeDisabled();
});

test("el formulario llama a producto.cargar_packshot con el archivo y lo declarado", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([FALTA_FOTO]),
    "/api/productos/CLEARSTEM/cargar/producto.cargar_packshot": { ok: true },
  });
  montar();
  fireEvent.click(await screen.findByRole("button", { name: "Subí la foto del producto" }));
  const archivo = new File(["x"], "mi foto.png", { type: "image/png" });
  fireEvent.change(await screen.findByLabelText("Foto del producto"), { target: { files: [archivo] } });
  fireEvent.change(screen.getByLabelText("Marca impresa"), { target: { value: " CLEARSTEM " } });
  fireEvent.change(screen.getByLabelText("Color del envase"), { target: { value: "blanco con verde" } });
  fireEvent.change(screen.getByLabelText("Formato del envase"), { target: { value: "frasco 60 cápsulas" } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar foto" }));
  await waitFor(() => expect(llamadas.some((l) => l.url.endsWith("/cargar/producto.cargar_packshot"))).toBe(true));
  const envio = llamadas.find((l) => l.url.endsWith("/cargar/producto.cargar_packshot"))!;
  expect(envio.init?.method).toBe("POST");
  const form = envio.init?.body as FormData;
  expect(form.get("archivo")).toBeInstanceOf(File);
  expect(JSON.parse(form.get("datos") as string)).toEqual({
    marca_impresa: "CLEARSTEM",
    color_envase: "blanco con verde",
    formato_envase: "frasco 60 cápsulas",
  });
  // Al terminar recarga los datos y el flujo.
  await waitFor(() => expect(llamadas.filter((l) => l.url.endsWith("/datos")).length).toBeGreaterThan(1));
});

test("cambiar una foto ya cargada pide reemplazar y arranca con lo declarado", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([ITEM_OK], PACKSHOT),
    "/api/productos/CLEARSTEM/cargar/producto.cargar_packshot": { ok: true },
  });
  montar();
  fireEvent.click(await screen.findByRole("button", { name: "Cambiar foto" }));
  expect(await screen.findByText("Cambiar la foto del producto")).toBeInTheDocument();
  expect(screen.getByLabelText("Marca impresa")).toHaveValue("CLEARSTEM");
  fireEvent.change(screen.getByLabelText("Foto del producto"), {
    target: { files: [new File(["x"], "nueva.jpg", { type: "image/jpeg" })] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Guardar foto" }));
  await waitFor(() => expect(llamadas.some((l) => l.url.endsWith("/cargar/producto.cargar_packshot"))).toBe(true));
  const form = llamadas.find((l) => l.url.endsWith("/cargar/producto.cargar_packshot"))!.init?.body as FormData;
  expect(JSON.parse(form.get("datos") as string).reemplazar).toBe(true);
});

test("la tarjeta lista solo lo que falta, con su arreglo o su frase, y sin comandos", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([ITEM_OK, FALTA_FOTO, FALTA_PAGE, FALTA_PRECIO]),
    "/api/productos/CLEARSTEM/cargar/producto.cargar_page_id": { ok: true },
  });
  montar();
  expect(await screen.findByText("Para arrancar te falta")).toBeInTheDocument();
  expect(screen.queryByText("Costo del producto")).not.toBeInTheDocument();
  expect(screen.getByText("Precio de venta")).toBeInTheDocument();
  // El que no tiene escritor: una frase de a quién le toca, sin campo ni comando.
  expect(screen.getByText(/Pasale a Claude a cuánto vendés 1, 2 y 3 unidades/)).toBeInTheDocument();
  expect(screen.queryByText(/python|\.py/i)).not.toBeInTheDocument();
  // El de la página: campo + botón que llama a su escritor.
  const campo = screen.getByLabelText("Número de la página de Facebook");
  const guardar = screen.getByRole("button", { name: "Guardar página" });
  expect(guardar).toBeDisabled();
  fireEvent.change(campo, { target: { value: "1279576438561754" } });
  fireEvent.click(guardar);
  await waitFor(() => expect(llamadas.some((l) => l.url.endsWith("/cargar/producto.cargar_page_id"))).toBe(true));
  const form = llamadas.find((l) => l.url.endsWith("/cargar/producto.cargar_page_id"))!.init?.body as FormData;
  expect(JSON.parse(form.get("datos") as string)).toEqual({ page_id: "1279576438561754" });
});

test("el costo y la cuenta tienen su arreglo en línea", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([
      { clave: "costo_q", rotulo: "Costo del producto", estado: "falta", detalle: "", como_resolver: "Decinos el costo.", accion: "producto.cambiar_costo" },
      { clave: "cuenta", rotulo: "Cuenta publicitaria", estado: "falta", detalle: "", como_resolver: "Elegí la cuenta.", accion: "producto.cargar_cuenta" },
    ]),
    "/api/cuentas": [
      { cuenta_alias: "GTR 7", estado_cuenta: "ACTIVE", moneda: "USD" },
      { cuenta_alias: "GTR 2", estado_cuenta: "RETIRADA", moneda: "USD" },
    ],
    "/api/productos/CLEARSTEM/cargar/producto.cargar_cuenta": { ok: true },
  });
  montar();
  expect(await screen.findByLabelText("Costo en quetzales")).toBeInTheDocument();
  const selector = await screen.findByLabelText("Cuenta publicitaria");
  await waitFor(() => expect(screen.getByRole("option", { name: "GTR 7" })).toBeInTheDocument());
  expect(screen.queryByRole("option", { name: "GTR 2" })).not.toBeInTheDocument();
  fireEvent.change(selector, { target: { value: "GTR 7" } });
  fireEvent.click(screen.getByRole("button", { name: "Asignar cuenta" }));
  await waitFor(() => expect(llamadas.some((l) => l.url.endsWith("/cargar/producto.cargar_cuenta"))).toBe(true));
});

test("sin faltantes la tarjeta no se dibuja; si el motor no responde, la ficha se ve igual", async () => {
  servir({
    "/api/productos/CLEARSTEM": FLUJO,
    "/api/productos/CLEARSTEM/datos": datos([ITEM_OK], PACKSHOT),
  });
  const primera = montar();
  await screen.findByAltText("Foto de Clearstem");
  expect(screen.queryByText("Para arrancar te falta")).not.toBeInTheDocument();
  primera.unmount();

  servir({ "/api/productos/CLEARSTEM": FLUJO });
  montar();
  expect(await screen.findByText("Clearstem")).toBeInTheDocument();
  expect(screen.queryByText("Para arrancar te falta")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Subí la foto del producto" })).not.toBeInTheDocument();
});
