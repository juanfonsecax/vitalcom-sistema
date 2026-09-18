/**
 * La pantalla Trabajos muestra lo que dice la API y solo deja aprobar con la orden a la vista.
 *
 * La API y el `EventSource` se simulan: que el backend cumpla el contrato lo prueban
 * `test_trabajos.py` y `test_meta.py`. Acá se verifica lo que ve y hace el operador.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createMemoryHistory, createRootRoute, createRoute, createRouter } from "@tanstack/react-router";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Trabajos } from "../pantallas/Trabajos";

const BASE = {
  accion_id: "nodo.F1.publicar",
  rotulo: "Publicar FASE 1 en Meta (PAUSED)",
  producto_key: "TINNIDROP",
  iniciado: "2026-09-18T10:15:02-06:00",
  terminado: null,
  app_version: "wf-1",
  otra_version: false,
  parametros: { producto_key: "TINNIDROP", cuenta: "GTR 7" },
  sello: {},
  unidades: [],
  resultado: null,
  run_dir: "PRODUCTOS/_AUDITORIAS/app_runs/2026-09/x",
  error: null,
};

const ORDEN = {
  tipo: "aprobacion",
  orden_id: 1,
  hash: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  caduca_horas: 12,
  orden: {
    tipo: "paquete_publicacion",
    producto: "TINNIDROP",
    fase: "1",
    brazo: "UNICO",
    cuenta: "GTR 7",
    manifiesto: null,
    llamadas: [
      { n: 1, tool: "ads_create_campaign", args: { campaign_name: "GTR7_TINNIDROP_F1", status: "PAUSED" } },
      { n: 2, tool: "ads_create_ad_set", args: { ad_set_name: "CJ1", status: "PAUSED" } },
    ],
  },
};

type Llamada = { url: string; metodo: string; cuerpo: unknown };
let llamadas: Llamada[] = [];
let respuestas: Record<string, unknown> = {};

function servir() {
  llamadas = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, opciones?: RequestInit) => {
      const ruta = new URL(url, "http://x").pathname;
      llamadas.push({ url: ruta, metodo: opciones?.method ?? "GET", cuerpo: opciones?.body ? JSON.parse(String(opciones.body)) : undefined });
      const cuerpo = respuestas[`${opciones?.method ?? "GET"} ${ruta}`];
      return { ok: cuerpo !== undefined, status: cuerpo === undefined ? 404 : 200, json: async () => cuerpo, statusText: "no" } as Response;
    }),
  );
}

class FuenteFalsa {
  static todas: FuenteFalsa[] = [];
  escuchas: Record<string, ((e: MessageEvent) => void)[]> = {};
  onopen: (() => void) | null = null;
  cerrada = false;
  constructor(readonly url: string) {
    FuenteFalsa.todas.push(this);
  }
  addEventListener(nombre: string, fn: (e: MessageEvent) => void) {
    (this.escuchas[nombre] ??= []).push(fn);
  }
  emitir(nombre: string, datos: unknown) {
    for (const fn of this.escuchas[nombre] ?? []) fn({ data: JSON.stringify(datos) } as MessageEvent);
  }
  close() {
    this.cerrada = true;
  }
}

function montar(id?: string) {
  const raiz = createRootRoute();
  const rutas = [
    createRoute({ getParentRoute: () => raiz, path: "/trabajos", component: Trabajos }),
    createRoute({ getParentRoute: () => raiz, path: "/trabajos/$id", component: Trabajos }),
  ];
  const router = createRouter({
    routeTree: raiz.addChildren(rutas),
    history: createMemoryHistory({ initialEntries: [id ? `/trabajos/${id}` : "/trabajos"] }),
  });
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router as never} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  FuenteFalsa.todas = [];
  vi.stubGlobal("EventSource", FuenteFalsa);
  respuestas = { "GET /api/claude/estado": { logueado: true, detalle: "yo@x.com", credencial_prohibida: [] } };
  servir();
});

afterEach(() => vi.unstubAllGlobals());

test("la lista muestra el estado en palabras y avisa lo que espera al operador", async () => {
  respuestas["GET /api/trabajos"] = [
    { ...BASE, job_id: "j1", estado: "ESPERA_APROBACION", pendiente: "aprobacion" },
    { ...BASE, job_id: "j2", accion_id: "nodo.ciclo.motor", rotulo: "Correr el motor de decisión", producto_key: null, estado: "FALLIDO", pendiente: null },
  ];
  montar();
  expect(await screen.findByText("espera tu aprobación")).toBeInTheDocument();
  expect(screen.getByText("Falta tu aprobación")).toBeInTheDocument();
  expect(screen.getByText("falló")).toBeInTheDocument();
  expect(screen.getByText("Correr el motor de decisión")).toBeInTheDocument();
  expect(await screen.findByText("Claude: sesión abierta")).toBeInTheDocument();
});

test("sin trabajos lo dice", async () => {
  respuestas["GET /api/trabajos"] = [];
  montar();
  expect(await screen.findByText(/No hay trabajos todavía/)).toBeInTheDocument();
});

test("Claude sin sesión se avisa con el paso a seguir", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/claude/estado"] = { logueado: false, detalle: "sin sesión", credencial_prohibida: [] };
  montar();
  expect(await screen.findByText(/Claude: sin sesión/)).toBeInTheDocument();
});

test("la orden a aprobar se ve completa y aprobar manda la huella de lo que se vio", async () => {
  respuestas["GET /api/trabajos"] = [{ ...BASE, job_id: "j1", estado: "ESPERA_APROBACION", pendiente: "aprobacion" }];
  respuestas["GET /api/trabajos/j1"] = { ...BASE, job_id: "j1", estado: "ESPERA_APROBACION", pendiente: "aprobacion", pendiente_completo: ORDEN };
  respuestas["POST /api/trabajos/j1/aprobaciones/1"] = { ok: true };
  montar("j1");

  expect(await screen.findByText("Esperando tu aprobación")).toBeInTheDocument();
  expect(screen.getByText("Todo nace en pausa", { exact: false })).toBeInTheDocument();
  const llamadasVistas = screen.getByLabelText("Llamadas a Meta");
  expect(llamadasVistas).toHaveTextContent("Crear la campaña");
  expect(llamadasVistas).toHaveTextContent("GTR7_TINNIDROP_F1");
  expect(llamadasVistas).toHaveTextContent("Crear un conjunto de anuncios");
  expect(screen.getByText(ORDEN.hash.slice(0, 12))).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Aprobar/ }));
  await waitFor(() => expect(llamadas.some((l) => l.metodo === "POST" && l.url === "/api/trabajos/j1/aprobaciones/1")).toBe(true));
  const envio = llamadas.find((l) => l.metodo === "POST")!;
  expect(envio.cuerpo).toEqual({ decision: "APROBADA", hash: ORDEN.hash, nota: "" });
});

const SUBIDA = {
  tipo: "subida_media",
  vuelta: 2,
  cuenta: "GTR7",
  cuenta_id: "598687956219141",
  carpeta: "C:\\SISTEMA\\PRODUCTOS\\_AUDITORIAS\\app_runs\\2026-09\\x\\subir_a_meta",
  faltan: ["falta subir 1 imagen(es): PX_2_V2"],
  archivos: [
    { archivo: "PX_1.png", nombre_en_biblioteca: "PX_1_V3", archivo_a_subir: "PX_1_V3.png", estado: "OK", hashes: ["h1"] },
    { archivo: "PX_2.png", nombre_en_biblioteca: "PX_2_V2", archivo_a_subir: "PX_2_V2.png", estado: "POR_SUBIR", hashes: [] },
  ],
};

test("las imágenes a subir se ven con su nombre exacto y la cuenta, y «Ya las subí» avisa esa vuelta", async () => {
  respuestas["GET /api/trabajos"] = [{ ...BASE, job_id: "j4", estado: "ESPERA_MEDIA", pendiente: "subida_media" }];
  respuestas["GET /api/trabajos/j4"] = { ...BASE, job_id: "j4", estado: "ESPERA_MEDIA", pendiente: "subida_media", pendiente_completo: SUBIDA };
  respuestas["POST /api/trabajos/j4/media/2"] = { ok: true };
  montar("j4");

  expect(await screen.findByText("Subí estas imágenes a Meta")).toBeInTheDocument();
  expect(screen.getByText("biblioteca de medios de la cuenta GTR7", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("Falta que subas las imágenes a Meta")).toBeInTheDocument();
  const lista = screen.getByLabelText("Imágenes para subir");
  expect(lista).toHaveTextContent("PX_1_V3.png");
  expect(lista).toHaveTextContent("encontrada");
  expect(lista).toHaveTextContent("PX_2_V2.png");
  expect(lista).toHaveTextContent("falta subir");
  expect(screen.getByText("· falta subir 1 imagen(es): PX_2_V2")).toBeInTheDocument();
  expect(screen.getByText(SUBIDA.carpeta)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Ya las subí" }));
  await waitFor(() => expect(llamadas.some((l) => l.metodo === "POST" && l.url === "/api/trabajos/j4/media/2")).toBe(true));
});

test("la orden muestra qué archivo es cada hash", async () => {
  const conImagenes = {
    ...ORDEN,
    orden: { ...ORDEN.orden, imagenes: [{ archivo: "PX_1.png", nombre_en_biblioteca: "PX_1_V3", image_hash: "hash-uno" }] },
  };
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j1"] = { ...BASE, job_id: "j1", estado: "ESPERA_APROBACION", pendiente: "aprobacion", pendiente_completo: conImagenes };
  montar("j1");
  const imagenes = await screen.findByLabelText("Imágenes de la orden");
  expect(imagenes).toHaveTextContent("PX_1_V3");
  expect(imagenes).toHaveTextContent("PX_1.png");
  expect(imagenes).toHaveTextContent("hash-uno");
});

test("rechazar manda RECHAZADA con la misma huella", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j1"] = { ...BASE, job_id: "j1", estado: "ESPERA_APROBACION", pendiente: "aprobacion", pendiente_completo: ORDEN };
  respuestas["POST /api/trabajos/j1/aprobaciones/1"] = { ok: true };
  montar("j1");
  fireEvent.click(await screen.findByRole("button", { name: "Rechazar" }));
  await waitFor(() => expect(llamadas.some((l) => l.metodo === "POST")).toBe(true));
  expect(llamadas.find((l) => l.metodo === "POST")!.cuerpo).toMatchObject({ decision: "RECHAZADA", hash: ORDEN.hash });
});

test("la pregunta de Claude se responde con el número de pregunta", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j3"] = {
    ...BASE, job_id: "j3", accion_id: "nodo.F2.etapa-11", rotulo: "Diagnosticar el cierre del bot", estado: "ESPERA_RESPUESTA",
    pendiente: "pregunta", pendiente_completo: { tipo: "pregunta", n: 2, texto: "¿Sigo con el ángulo A o con el B?" },
  };
  respuestas["POST /api/trabajos/j3/respuesta"] = { ok: true };
  montar("j3");
  expect(await screen.findByText("¿Sigo con el ángulo A o con el B?")).toBeInTheDocument();
  const boton = screen.getByRole("button", { name: "Responder" });
  expect(boton).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Tu respuesta"), { target: { value: "Seguí con el A" } });
  fireEvent.click(boton);
  await waitFor(() => expect(llamadas.some((l) => l.url === "/api/trabajos/j3/respuesta")).toBe(true));
  expect(llamadas.find((l) => l.url === "/api/trabajos/j3/respuesta")!.cuerpo).toEqual({ n: 2, texto: "Seguí con el A" });
});

test("un trabajo de otra versión ofrece marcar fallido o empezar de nuevo, y nunca continuar", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j4"] = { ...BASE, job_id: "j4", estado: "OTRA_VERSION", otra_version: true, app_version: "wf-0", pendiente: null, pendiente_completo: null };
  montar("j4");
  expect(await screen.findByRole("button", { name: "Marcar fallido" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Empezar de nuevo" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /continuar/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Aprobar/ })).not.toBeInTheDocument();
});

test("un trabajo fallido se reintenta completo y uno en curso se cancela en dos pasos", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j5"] = { ...BASE, job_id: "j5", estado: "FALLIDO", pendiente: null, pendiente_completo: null, resultado: { detalle: "no hay videos" } };
  const { unmount } = montar("j5");
  expect(await screen.findByRole("button", { name: "Reintentar completo" })).toBeInTheDocument();
  expect(screen.getByText("no hay videos")).toBeInTheDocument();
  unmount();

  respuestas["GET /api/trabajos/j6"] = { ...BASE, job_id: "j6", estado: "CORRIENDO", pendiente: null, pendiente_completo: null };
  respuestas["POST /api/trabajos/j6/cancelar"] = { estado: "CANCELADO" };
  montar("j6");
  fireEvent.click(await screen.findByRole("button", { name: "Cancelar trabajo" }));
  expect(llamadas.some((l) => l.url.endsWith("/cancelar"))).toBe(false); // el primer clic solo pregunta
  fireEvent.click(screen.getByRole("button", { name: "Sí, cancelar" }));
  await waitFor(() => expect(llamadas.some((l) => l.url === "/api/trabajos/j6/cancelar")).toBe(true));
});

test("el registro en vivo muestra las líneas que llegan por SSE", async () => {
  respuestas["GET /api/trabajos"] = [];
  respuestas["GET /api/trabajos/j7"] = { ...BASE, job_id: "j7", estado: "CORRIENDO", pendiente: null, pendiente_completo: null };
  montar("j7");
  await screen.findByText("Lo que va pasando");
  const fuente = FuenteFalsa.todas.at(-1)!;
  expect(fuente.url).toBe("/api/trabajos/j7/eventos");
  fuente.onopen?.();
  fuente.emitir("linea", { unidad: 1, texto: "arrancó etapa-2", tipo: "claude" });
  fuente.emitir("linea", { unidad: 1, texto: "cargando el flujo", tipo: "salida" });
  expect(await screen.findByText("arrancó etapa-2")).toBeInTheDocument();
  expect(screen.getByText("cargando el flujo")).toBeInTheDocument();
  expect(await screen.findByText("en vivo")).toBeInTheDocument();
  fuente.emitir("fin", { estado: "EXITO", resultado: null });
  await waitFor(() => expect(fuente.cerrada).toBe(true));
});
