/**
 * fase2.test.tsx — Pruebas unitarias de la pantalla Fase2 (Hito 6).
 *
 * Verifica:
 * 1. Muestra el #1 en testeo, los ganadores en fila y los ángulos que no funcionaron.
 * 2. Galería de 10 conceptos con blueprints, chips de rol y prompts.
 * 3. Botón para copiar el prompt al portapapeles.
 * 4. Modal de confirmación para reingreso a FASE 1 por fatiga y envío de la mutación.
 * 5. Banner informativo cuando ya existe un reingreso activo.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Fase2 } from "../pantallas/Fase2";

let respuestas: Record<string, unknown> = {};
let llamadasFetch: { url: string; metodo: string; cuerpo?: any }[] = [];

function simularFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, opciones?: RequestInit) => {
      const ruta = new URL(url, "http://localhost").pathname;
      const metodo = opciones?.method ?? "GET";
      let cuerpoParseado: any = undefined;
      if (opciones?.body && typeof opciones.body === "string") {
        try {
          cuerpoParseado = JSON.parse(opciones.body);
        } catch {
          cuerpoParseado = opciones.body;
        }
      }
      llamadasFetch.push({
        url: ruta,
        metodo,
        cuerpo: cuerpoParseado,
      });
      const cuerpo = respuestas[`${metodo} ${ruta}`];
      return {
        ok: cuerpo !== undefined,
        status: cuerpo === undefined ? 404 : 200,
        json: async () => cuerpo,
        statusText: cuerpo === undefined ? "Not Found" : "OK",
      } as Response;
    }),
  );
}

function renderizar(clave = "TINNIDROP") {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const raiz = createRootRoute();
  const ruta = createRoute({
    getParentRoute: () => raiz,
    path: "/producto/$clave/fase2",
    component: Fase2,
  });
  const historia = createMemoryHistory({
    initialEntries: [`/producto/${clave}/fase2`],
  });
  const router = createRouter({ routeTree: raiz.addChildren([ruta]), history: historia });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const ANGULO_BASE = {
  conceptos_listos: 0,
  posicion: null,
  etiqueta: "",
  estado_angulo: "",
  dias_sin_gasto: 0,
  ultimo_dia_gasto: "2026-09-25",
  estado: null,
  accion_sugerida: null,
  ventas_acum: null,
  cpa_real_q: null,
  cierre_pct: null,
  ic: null,
  spend_acum_q: null,
};

const GENERAR_LISTO = {
  accion_id: "producto.armar_prompts_fase2",
  parametros: { producto_key: "TINNIDROP", angulo_key: "ACCESIBILIDAD_MEDICO" },
  habilitada: true,
  motivo: "",
  listo: true,
  faltan: [],
  accion_perfil: null,
  aviso: "",
};

const GENERAR_EN_FILA = {
  accion_id: "producto.armar_prompts_fase2",
  parametros: { producto_key: "TINNIDROP", angulo_key: "NOCHES_SIN_DORMIR" },
  habilitada: false,
  motivo: "Se genera cuando le toque su Fase 2.",
  listo: false,
  faltan: [],
  accion_perfil: null,
  aviso: "",
};

const FALTA_PACKSHOT = {
  clave: "packshot",
  rotulo: "Foto del producto (packshot)",
  estado: "falta",
  detalle: "No hay foto declarada.",
  como_resolver: "Subí la foto del producto tal como se ve en la mano.",
  accion: "producto.cargar_packshot",
};

const FALTA_PERFIL = {
  clave: "perfil_creativo",
  rotulo: "Perfil creativo del ángulo #1",
  estado: "falta",
  detalle: "No hay perfil creativo del ángulo ACCESIBILIDAD_MEDICO.",
  como_resolver: "Claude lo prepara.",
  accion: null,
};

/** FASE2_MOCK con el descriptor del #1 cambiado (y el de la fila siempre deshabilitado). */
function fase2Con(generar: Record<string, unknown>) {
  return {
    ...FASE2_MOCK,
    angulos: FASE2_MOCK.angulos.map((a) =>
      a.angulo_key === "ACCESIBILIDAD_MEDICO"
        ? { ...a, generar }
        : a.angulo_key === "NOCHES_SIN_DORMIR"
          ? { ...a, generar: GENERAR_EN_FILA }
          : a,
    ),
  };
}

const FASE2_MOCK = {
  producto_key: "TINNIDROP",
  mercado: "GT", moneda_local: "GTQ", simbolo: "Q",
  fase: "FASE 2",
  nodo_actual: "F2.etapa-11",
  angulo_ganador: "ACCESIBILIDAD_MEDICO",
  conceptos_generados: 10,
  conceptos_requeridos: 10,
  campanas: [
    { brazo: "A", conceptos: 5 },
    { brazo: "B", conceptos: 5 },
  ],
  angulos: [
    {
      ...ANGULO_BASE,
      angulo_key: "ACCESIBILIDAD_MEDICO",
      rol: "ganador_activo",
      posicion: 1,
      estado: "ESCALAR",
      estado_angulo: "ESCALANDO",
      ventas_acum: 91,
      cpa_real_q: 41.5,
      cierre_pct: 18.2,
      ic: [30, 41.5, 60],
      accion_sugerida: "NO SUBIR PRESUPUESTO todavía",
      cpa_acum_q: 38.5,
      cpa_ventana_q: 96,
      cpa_be_q: 105.89,
      semaforo_acum: "verde",
      semaforo_ventana: "ambar",
      conceptos_listos: 1,
      orden_motor: "NO SUBIR PRESUPUESTO (TINNIDROP en F2): mantener hasta cerrar la fase.",
      checklist: [
        { clave: "generar", rotulo: "Conceptos generados", cumplido: false, detalle: "2 de 10 (Conceptos 1–5: 2 de 5 · Conceptos 6–10: 0 de 5)" },
        { clave: "publicar", rotulo: "Publicados en Meta", cumplido: true, detalle: "10 de 10 con anuncio en Meta" },
        { clave: "lanzar", rotulo: "Lanzado", cumplido: false, detalle: "Sin LANZAMIENTO de FASE 2 registrado" },
      ],
      generar: GENERAR_LISTO,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "NOCHES_SIN_DORMIR",
      rol: "ganador_en_fila",
      posicion: 2,
      estado: "RENOVAR",
      ventas_acum: 24,
      cpa_real_q: 77,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "DETERIORO_COGNITIVO",
      rol: "ganador_en_fila",
      posicion: 3,
      ventas_acum: 105,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "ME_DIJERON_NO_CURA",
      rol: "perdedor",
      etiqueta: "ya apagado (40 días sin gastar)",
      estado_angulo: "APAGADO_ABANDONO",
      dias_sin_gasto: 40,
    },
    {
      ...ANGULO_BASE,
      angulo_key: "MANCHAS_OSCURAS",
      rol: "perdedor",
      etiqueta: "el motor ordena pausarlo",
      estado: "PAUSAR",
      accion_sugerida: "PAUSAR: el costo por venta supera el break-even",
    },
    {
      ...ANGULO_BASE,
      angulo_key: "VERGUENZA_PIERNAS",
      rol: "midiendo",
      etiqueta: "midiendo",
      estado: "SEGUIR_MIDIENDO",
    },
  ],
  conceptos: [
    {
      creativo_id: "TINNIDROP_F2_C01",
      angulo_key: "ACCESIBILIDAD_MEDICO",
      canonico_id: "C01",
      blueprint_id: "BP-01",
      blueprint_nombre: "Before / After Split",
      rol_embudo: "TOFU",
      dispositivo: "Comparativa visual directa",
      prompt: "Fotografía publicitaria hiperrealista dividida al medio...",
      prompt_origen: "paquete",
      referencia_url: "/api/swipe/_IMG/Camila_Recomienda/15_foto.jpg",
      comando_generar: null,
      archivo: "TINNIDROP_F2_C01.png",
      archivo_existe: true,
      estado: "GENERADO",
      numero: 1,
      campana: "A",
    },
    {
      creativo_id: "TINNIDROP_F2_C02",
      angulo_key: "ACCESIBILIDAD_MEDICO",
      canonico_id: "C02",
      blueprint_id: "BP-04",
      blueprint_nombre: "Social Proof Wall",
      rol_embudo: "BOFU",
      dispositivo: "Capturas de chats de clientes satisfechos",
      prompt: null,
      prompt_origen: "pendiente",
      referencia_url: null,
      comando_generar: "python Ads/_TOOLS/armar_prompts_fase2.py TINNIDROP ACCESIBILIDAD_MEDICO",
      archivo: "TINNIDROP_F2_C02.png",
      archivo_existe: false,
      estado: "PENDIENTE_GENERAR",
      numero: 2,
      campana: "A",
    },
  ],
  fatiga: {
    ordenes: [
      { celda: "NOCHES_SIN_DORMIR", estado: "RENOVAR", accion: "RENOVAR CREATIVO: rotá el concepto, no apagues" },
      { celda: "ACCESIBILIDAD_MEDICO", estado: "ESCALAR", accion: "NO SUBIR PRESUPUESTO todavía" },
    ],
    angulos_probados: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
  },
  reingreso_activo: null,
};

beforeEach(() => {
  respuestas = {};
  llamadasFetch = [];
  simularFetch();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("renderiza el #1 en testeo, la fila, los que no funcionaron y la galería", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/FASE 2 · Testeo de Conceptos \(TINNIDROP\)/i)).toBeDefined();
  });

  // (a) el #1, con sus cifras clave
  const hero = await screen.findByTestId("angulo-en-testeo");
  expect(hero.textContent).toContain("En testeo de conceptos ahora");
  expect(hero.textContent).toContain("ACCESIBILIDAD_MEDICO");
  expect(hero.textContent).toContain("91");
  expect(hero.textContent).toContain("Q41.50");
  expect(hero.textContent).toContain("18.2%");
  expect(screen.getByText("F2.etapa-11")).toBeDefined();

  // (b) en fila: #2 y #3, con la regla y sin fechas inventadas
  const fila = screen.getByTestId("angulos-en-fila");
  expect(fila.textContent).toContain("NOCHES_SIN_DORMIR");
  expect(fila.textContent).toContain("DETERIORO_COGNITIVO");
  expect(fila.textContent).toContain("#2 en la fila");
  expect(fila.textContent).toContain("#3 en la fila");
  expect(screen.getAllByText(/Entra a su propia Fase 2 cuando el #1 cierre la suya/i)).toHaveLength(2);
  expect(screen.queryByText(/Esperar ~3 días/i)).toBeNull();

  // Conceptos
  expect(screen.getByText("Before / After Split")).toBeDefined();
  expect(screen.getByText("Social Proof Wall")).toBeDefined();
  expect(screen.getByText("C01")).toBeDefined();
  expect(screen.getByText("C02")).toBeDefined();
  expect(screen.getByText("✓ En disco")).toBeDefined();
});

test("los ángulos que no funcionaron llevan la etiqueta que dicen los datos", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["GET /api/trabajos"] = [
    { job_id: "job-77", producto_key: "TINNIDROP", pendiente: { tipo: "aprobacion" } },
  ];
  renderizar("TINNIDROP");

  const lista = await screen.findByTestId("angulos-no-funcionaron");
  // plegados por defecto: se ve el conteo, no las filas
  expect(lista.textContent).toContain("Ángulos que no funcionaron (3)");
  expect(lista.textContent).not.toContain("ME_DIJERON_NO_CURA");
  fireEvent.click(screen.getByText(/Ángulos que no funcionaron \(3\)/));
  expect(lista.textContent).toContain("ME_DIJERON_NO_CURA");
  expect(lista.textContent).toContain("ya apagado (40 días sin gastar)");
  expect(lista.textContent).toContain("MANCHAS_OSCURAS");
  expect(lista.textContent).toContain("el motor ordena pausarlo");
  expect(lista.textContent).toContain("VERGUENZA_PIERNAS");
  expect(lista.textContent).toContain("midiendo");
  // la orden de pausa lleva a Trabajos, donde vive la aprobación
  await waitFor(() => {
    const enlace = screen.getByRole("link", { name: "Revisar en Trabajos" });
    expect(enlace.getAttribute("href")).toContain("/trabajos/job-77");
  });
  // el detalle técnico sigue ahí, plegado
  expect(screen.getAllByText("Ver detalle técnico").length).toBeGreaterThan(0);
});

test("la fatiga muestra la orden concreta del motor como «Qué hacer» y pliega la doctrina", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const bloque = await screen.findByTestId("ordenes-renovar");
  expect(bloque.textContent).toContain("Qué hacer");
  expect(bloque.textContent).toContain("NOCHES_SIN_DORMIR");
  expect(bloque.textContent).toContain("RENOVAR CREATIVO: rotá el concepto, no apagues");
  // solo las órdenes de renovar; la de escalar no es de este bloque
  expect(bloque.textContent).not.toContain("NO SUBIR PRESUPUESTO");
  expect(screen.getByText("¿Cómo funciona la renovación?")).toBeDefined();
});

test("cada ángulo lleva SU galería debajo de su tarjeta: la del #1 abierta, la de los que esperan cerrada", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    conceptos: [
      ...FASE2_MOCK.conceptos,
      {
        ...FASE2_MOCK.conceptos[0],
        creativo_id: "TINNIDROP_F2_N01",
        angulo_key: "NOCHES_SIN_DORMIR",
        canonico_id: "N01",
        blueprint_nombre: "Testimonio de noche",
      },
    ],
  };
  renderizar("TINNIDROP");

  const g1 = await screen.findByTestId("galeria-ACCESIBILIDAD_MEDICO");
  const g2 = screen.getByTestId("galeria-NOCHES_SIN_DORMIR");
  expect(screen.queryAllByRole("tab")).toHaveLength(0); // ya no hay pestañas: el ángulo es el bloque
  expect(screen.getByTestId("bloque-ACCESIBILIDAD_MEDICO")).toContainElement(g1);
  expect(screen.getByTestId("bloque-NOCHES_SIN_DORMIR")).toContainElement(g2);
  expect(g1.textContent).toContain("Before / After Split");
  expect(g1.textContent).not.toContain("Testimonio de noche");
  expect(g2.textContent).toContain("Testimonio de noche");
  expect(g1.querySelector("summary")?.textContent).toContain("Galería de conceptos (1 de 10)");
  expect(g1).toHaveAttribute("open");
  expect(g2).not.toHaveAttribute("open");
  const tarjeta1 = screen.getByTestId("angulo-en-testeo");
  expect(tarjeta1.compareDocumentPosition(g1) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(g1.compareDocumentPosition(g2) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("un ángulo en fila sin conceptos lo dice dentro de su galería", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");
  const g = await screen.findByTestId("galeria-DETERIORO_COGNITIVO");
  expect(g.textContent).toContain("Todavía sin conceptos: se fabrican cuando el #1 cierre su FASE 2");
  expect(g).not.toHaveAttribute("open");
});

test("los conceptos de ángulos fuera del ranking no desaparecen: van a «Otros conceptos registrados»", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    conceptos: [
      ...FASE2_MOCK.conceptos,
      { ...FASE2_MOCK.conceptos[0], creativo_id: "TINNIDROP_X1", angulo_key: "DOLOR_EMOCIONAL_MASCULINO", canonico_id: "X1", blueprint_nombre: "Pieza de otro ángulo" },
      { ...FASE2_MOCK.conceptos[0], creativo_id: "TINNIDROP_X2", angulo_key: "", canonico_id: "X2", blueprint_nombre: "Pieza sin ángulo" },
    ],
  };
  renderizar("TINNIDROP");
  const otros = await screen.findByTestId("otros-conceptos");
  expect(otros.textContent).toContain("Otros conceptos registrados (2)");
  expect(otros.textContent).toContain("Pieza de otro ángulo");
  expect(otros.textContent).toContain("DOLOR_EMOCIONAL_MASCULINO");
  expect(otros.textContent).toContain("Pieza sin ángulo");
  expect(otros).not.toHaveAttribute("open");
  expect(screen.getByTestId("galeria-ACCESIBILIDAD_MEDICO").textContent).not.toContain("Pieza de otro ángulo");
});

test("sin ganador no inventa un #1 y lo dice", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = { ...FASE2_MOCK, angulo_ganador: "", angulos: [] };
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Todavía no hay un ángulo ganador")).toBeDefined();
  });
  expect(screen.queryByTestId("angulos-en-fila")).toBeNull();
});

test("botón de copiar prompt invoca clipboard.writeText", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  const writeTextMock = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", {
    clipboard: { writeText: writeTextMock },
  });

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getAllByText("Copiar").length).toBeGreaterThan(0);
  });

  const botones = screen.getAllByText("Copiar");
  fireEvent.click(botones[0]);

  expect(writeTextMock).toHaveBeenCalledWith(
    "Fotografía publicitaria hiperrealista dividida al medio...",
  );

  await waitFor(() => {
    expect(screen.getByText("Copiado")).toBeDefined();
  });
});

const BOTON_GENERAR = "Generar los prompts de este ángulo";

test("concepto pendiente remite al botón; el comando queda solo en el detalle técnico plegado", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Prompt pendiente de generar")).toBeDefined();
  });

  expect(screen.getByText(/Se genera con el botón/)).toBeDefined();
  expect(screen.getByText("Detalle técnico")).toBeDefined();
});

test("el #1 listo: el botón está habilitado, lanza la acción con sus parámetros y recarga al terminar", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["POST /api/acciones/producto.armar_prompts_fase2"] = {
    job_id: "abc123", accion_id: "producto.armar_prompts_fase2", estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/abc123", url_eventos: "/api/trabajos/abc123/eventos",
  };
  respuestas["GET /api/trabajos/abc123"] = { job_id: "abc123", estado: "EXITO", unidades: [{ json: { ok: true } }] };
  renderizar("TINNIDROP");

  const boton = await screen.findByRole("button", { name: BOTON_GENERAR });
  expect((boton as HTMLButtonElement).disabled).toBe(false);
  const antes = llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length;
  fireEvent.click(boton);

  await waitFor(() => {
    const llamada = llamadasFetch.find((l) => l.url === "/api/acciones/producto.armar_prompts_fase2" && l.metodo === "POST");
    expect(llamada?.cuerpo).toEqual({
      parametros: { producto_key: "TINNIDROP", angulo_key: "ACCESIBILIDAD_MEDICO" },
      confirmado: false,
    });
  });
  await waitFor(() => {
    expect(llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length).toBeGreaterThan(antes);
  });
});

test("un trabajo que falla dice el motivo en palabras y no muestra comandos", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["POST /api/acciones/producto.armar_prompts_fase2"] = {
    job_id: "mal1", accion_id: "producto.armar_prompts_fase2", estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/mal1", url_eventos: "/api/trabajos/mal1/eventos",
  };
  respuestas["GET /api/trabajos/mal1"] = {
    job_id: "mal1", estado: "FALLIDO", resultado: { detalle: "x" },
    unidades: [{ json: { ok: false, motivo: "TINNIDROP no tiene packshot declarado en PRODUCTOS/_DIM_ENVASE.csv." } }],
  };
  renderizar("TINNIDROP");
  fireEvent.click(await screen.findByRole("button", { name: BOTON_GENERAR }));
  expect(await screen.findByText(/no tiene packshot declarado/)).toBeDefined();
});

test("si falta el packshot: dice cuál dato, deshabilita el botón y lleva a «Para arrancar te falta»", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2Con({
    ...GENERAR_LISTO, listo: false, faltan: [FALTA_PACKSHOT],
  });
  renderizar("TINNIDROP");

  expect(await screen.findByText("Antes de generarlos falta:")).toBeDefined();
  expect(screen.getByText("No hay foto declarada.")).toBeDefined();
  expect(screen.getByText("Subí la foto del producto tal como se ve en la mano.")).toBeDefined();
  expect((screen.getByRole("button", { name: BOTON_GENERAR }) as HTMLButtonElement).disabled).toBe(true);

  const destino = document.createElement("div");
  destino.id = "para-arrancar";
  const desplazar = vi.fn();
  destino.scrollIntoView = desplazar;
  document.body.appendChild(destino);
  fireEvent.click(screen.getByText("Resolverlo en «Para arrancar te falta»"));
  expect(desplazar).toHaveBeenCalled();
  destino.remove();
  expect(llamadasFetch.some((l) => l.metodo === "POST")).toBe(false);
});

test("si falta el perfil creativo: lo prepara Claude, sin comando y sin acción habilitada queda pendiente", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2Con({
    ...GENERAR_LISTO, listo: false, faltan: [FALTA_PERFIL],
  });
  renderizar("TINNIDROP");

  expect(await screen.findByText("Claude prepara el perfil creativo de este ángulo.")).toBeDefined();
  expect(screen.getByText(/Queda pendiente de Claude/)).toBeDefined();
  expect(screen.queryByRole("button", { name: "Pedirle a Claude el perfil creativo" })).toBeNull();
  expect((screen.getByRole("button", { name: BOTON_GENERAR }) as HTMLButtonElement).disabled).toBe(true);
});

test("si el manifiesto habilita la acción del perfil, se ofrece y se lanza con confirmación", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2Con({
    ...GENERAR_LISTO, listo: false, faltan: [FALTA_PERFIL], accion_perfil: "nodo.F2.conceptos",
  });
  respuestas["POST /api/acciones/nodo.F2.conceptos"] = {
    job_id: "perfil1", accion_id: "nodo.F2.conceptos", estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/perfil1", url_eventos: "/api/trabajos/perfil1/eventos",
  };
  respuestas["GET /api/trabajos/perfil1"] = { job_id: "perfil1", estado: "EN_CURSO" };
  renderizar("TINNIDROP");

  fireEvent.click(await screen.findByRole("button", { name: "Pedirle a Claude el perfil creativo" }));
  await waitFor(() => {
    const llamada = llamadasFetch.find((l) => l.url === "/api/acciones/nodo.F2.conceptos" && l.metodo === "POST");
    expect(llamada?.cuerpo).toEqual({ parametros: { producto_key: "TINNIDROP" }, confirmado: true });
  });
});

test("un ganador en fila muestra «se genera cuando le toque su Fase 2» y no se puede pedir", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...fase2Con(GENERAR_LISTO),
    conceptos: [
      ...FASE2_MOCK.conceptos,
      { ...FASE2_MOCK.conceptos[1], creativo_id: "TINNIDROP_F2_C09", angulo_key: "NOCHES_SIN_DORMIR", canonico_id: "C09" },
    ],
  };
  renderizar("TINNIDROP");

  expect(await screen.findByText("Se genera cuando le toque su Fase 2.")).toBeDefined();
  const enFila = within(screen.getByTestId("galeria-NOCHES_SIN_DORMIR"));
  expect((enFila.getByRole("button", { name: BOTON_GENERAR }) as HTMLButtonElement).disabled).toBe(true);
});

test("concepto con paquete muestra la imagen de referencia y el botón de copiar imagen", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByAltText("Referencia de swipe para C01")).toBeDefined();
  });

  expect(screen.getByText("Copiar imagen")).toBeDefined();
});

test("modal de reingreso por fatiga confirma y envía mutación a F1", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  respuestas["POST /api/productos/TINNIDROP/reingreso-f1"] = {
    producto_key: "TINNIDROP",
    ok: true,
    nodo_destino: "F1.etapa-0",
    angulos_excluidos: ["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"],
    motivo: "Ángulo agotado / fatiga de ventas",
  };

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText("Nuevos ángulos para este producto →")).toBeDefined();
  });

  fireEvent.click(screen.getByText("Nuevos ángulos para este producto →"));

  // Verificar que abre el modal mostrando los ángulos excluidos
  expect(screen.getByText(/¿Confirmar retorno a FASE 1 para TINNIDROP\?/i)).toBeDefined();
  expect(screen.getByText(/ACCESIBILIDAD_MEDICO, NOCHES_SIN_DORMIR/i)).toBeDefined();

  // Confirmar
  fireEvent.click(screen.getByText("Sí, volver a F1"));

  await waitFor(() => {
    const llamada = llamadasFetch.find(
      (l) => l.url === "/api/productos/TINNIDROP/reingreso-f1" && l.metodo === "POST",
    );
    expect(llamada).toBeDefined();
    expect(llamada?.cuerpo?.motivo).toBe("Ángulo agotado / fatiga de ventas");
  });
});

test("muestra banner de reingreso activo cuando existe", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    reingreso_activo: {
      fecha: "2026-09-19 15:30:00",
      motivo: "Fatiga creativa severa",
      angulos_excluidos: ["ACCESIBILIDAD_MEDICO"],
    },
  };

  renderizar("TINNIDROP");

  await waitFor(() => {
    expect(screen.getByText(/Reingreso a FASE 1 activo desde el 2026-09-19 15:30:00/i)).toBeDefined();
  });

  expect(screen.getByText("Fatiga creativa severa")).toBeDefined();
  expect(screen.getByText("Ir a FASE 1 →")).toBeDefined();
});

test("un ángulo perdedor con filas viejas de conceptos no tiene galería propia: sus piezas van a «Otros»", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    conceptos: [
      ...FASE2_MOCK.conceptos,
      {
        ...FASE2_MOCK.conceptos[0],
        creativo_id: "TINNIDROP_R1_VIEJO",
        angulo_key: "ME_DIJERON_NO_CURA",
        canonico_id: "",
        blueprint_nombre: "Pieza vieja de FASE 1",
      },
    ],
  };
  renderizar("TINNIDROP");

  await screen.findByText("Before / After Split");
  expect(screen.queryByTestId("galeria-ME_DIJERON_NO_CURA")).toBeNull();
  expect(screen.getByTestId("otros-conceptos").textContent).toContain("Pieza vieja de FASE 1");
});

test("«Qué hacer ahora»: el checklist del #1 marca los pasos cumplidos y deja los pendientes", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const bloque = await screen.findByTestId("que-hacer-ahora");
  expect(bloque.textContent).toContain("Qué hacer ahora");
  const pasos = Array.from(bloque.querySelectorAll('[data-testid="checklist-angulo"] li'));
  expect(pasos.map((p) => [p.getAttribute("data-cumplido"), p.textContent])).toEqual([
    ["no", expect.stringContaining("Conceptos generados2 de 10 (Conceptos 1–5: 2 de 5 · Conceptos 6–10: 0 de 5)")],
    ["si", expect.stringContaining("Publicados en Meta")],
    ["no", expect.stringContaining("Sin LANZAMIENTO de FASE 2 registrado")],
  ]);
});

test("el costo por venta se pinta contra el punto de equilibrio con el semáforo del backend", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const acum = (await screen.findAllByTestId("cpa-acum"))[0];
  const ventana = screen.getAllByTestId("cpa-ventana")[0];
  expect(acum.textContent).toContain("Q38.50");
  expect(acum.getAttribute("data-semaforo")).toBe("verde");
  expect(acum.className).toContain("emerald");
  expect(ventana.textContent).toContain("Q96.00");
  expect(ventana.getAttribute("data-semaforo")).toBe("ambar");
  expect(ventana.className).toContain("amber");
  expect(screen.getAllByTestId("cpa-vs-be")[0].textContent).toContain("Q105.89");
  expect(screen.getAllByTestId("orden-motor")[0].textContent).toContain("NO SUBIR PRESUPUESTO (TINNIDROP en F2)");
});

test("rojo cuando el backend dice rojo", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    angulos: FASE2_MOCK.angulos.map((a) =>
      a.angulo_key === "ACCESIBILIDAD_MEDICO" ? { ...a, cpa_acum_q: 130, semaforo_acum: "rojo" } : a,
    ),
  };
  renderizar("TINNIDROP");
  const acum = (await screen.findAllByTestId("cpa-acum"))[0];
  expect(acum.className).toContain("rose");
});

test("la galería rotula por rango de conceptos (no por «Campaña A/B») y dice cuáles faltan", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const galeria = await screen.findByTestId("galeria-ACCESIBILIDAD_MEDICO");
  expect(galeria.textContent).not.toContain("Campaña");
  expect(galeria.textContent).toContain("Los 10 conceptos se publican en dos campañas de 5; la tercera repite los mismos.");
  const a = within(galeria).getByTestId("grupo-ACCESIBILIDAD_MEDICO-A");
  expect(a.textContent).toContain("Conceptos 1–5");
  expect(a.textContent).toContain("2 de 5 conceptos");
  expect(a.textContent).toContain("Faltan 3 de los conceptos 1–5");
  const b = within(galeria).getByTestId("grupo-ACCESIBILIDAD_MEDICO-B");
  expect(b.textContent).toContain("Conceptos 6–10");
  expect(b.textContent).toContain("Conceptos 6–10 pendientes");
  expect(a.textContent).toContain("Before / After Split");
  expect(b.textContent).not.toContain("Before / After Split");
  expect(galeria.textContent!.split("la tercera repite los mismos").length - 1).toBe(1);
});

test("los ángulos apagados quedan plegados al final y sin botones de acción", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = FASE2_MOCK;
  renderizar("TINNIDROP");

  const apagados = await screen.findByTestId("angulos-no-funcionaron");
  expect(apagados.querySelectorAll("button").length).toBe(1); // solo el plegable
  expect(apagados.textContent).not.toContain(BOTON_GENERAR);
  const galeria = screen.getByTestId("galeria-ACCESIBILIDAD_MEDICO");
  expect(galeria.compareDocumentPosition(apagados) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("el estado de la fase en una línea y «Qué hacer ahora» va primero", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    conceptos_generados: 5,
    conceptos_faltan: 5,
    fase_validada: false,
    fase_titulo: "FASE 2 · TESTEO DE CONCEPTOS",
    paso_titulo: "Fabricar los 10 conceptos",
    bloqueante_principal: "faltan 5 conceptos",
    dueno_bloqueante: "etapa-9 (filas) + etapa-render (PNG)",
    ejecutor: "subagente `etapa-9`",
    reingreso_activo: { fecha: "2026-09-30", motivo: "fatiga", angulos_excluidos: [] },
  };
  renderizar("TINNIDROP");

  const estado = await screen.findByTestId("estado-de-fase");
  expect(estado.textContent).toContain("Fase 2 · testeo de conceptos");
  expect(estado.textContent).toContain("Sin validar");
  expect(estado.textContent).toContain("Paso: Fabricar los 10 conceptos");
  expect(estado.textContent).toContain("Trabado: faltan 5 conceptos");
  expect(estado.textContent).toContain("Lo hace: Fábrica de conceptos + Renderizador de creativos");

  // El chip de conceptos dice cuántos faltan y quién los fabrica.
  expect(
    screen.getByText("5 de 10 conceptos listos · faltan 5 · los fabrica la Fábrica de conceptos"),
  ).toBeInTheDocument();

  // Orden: estado → «Qué hacer ahora» → banner de reingreso → galería.
  const quehacer = screen.getByTestId("que-hacer-ahora");
  const pos = (a: Node, b: Node) => a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING;
  expect(pos(estado, quehacer)).toBeTruthy();
  expect(pos(quehacer, screen.getByText(/Reingreso a FASE 1 activo/))).toBeTruthy();
});

test("la tarjeta del ángulo dice un veredicto corto y pliega el texto largo del motor en «¿Por qué?»", async () => {
  const LARGO = "NO SUBIR PRESUPUESTO todavía: TINNIDROP ya es ganador pero está testeando conceptos y subir plata sesga la medición.";
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    angulos: FASE2_MOCK.angulos.map((a) =>
      a.angulo_key === "ACCESIBILIDAD_MEDICO" ? { ...a, bloqueo_fase: "F2.gate", orden_motor: LARGO } : a,
    ),
  };
  renderizar("TINNIDROP");
  const bloque = (await screen.findAllByTestId("orden-motor-bloque"))[0];
  expect(bloque.textContent).toContain("No subir presupuesto: mantener el que ya tiene hasta cerrar la fase.");
  const largo = screen.getAllByTestId("orden-motor")[0];
  expect(largo.textContent).toContain(LARGO);
  const pliegue = largo.closest("details");
  expect(pliegue).not.toBeNull();
  expect(pliegue).not.toHaveAttribute("open");
});

test("orden de la pantalla: estado, un bloque por ángulo (tarjeta + galería), reingreso, fatiga, no funcionaron, otros", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = {
    ...FASE2_MOCK,
    reingreso_activo: { fecha: "2026-09-30", motivo: "fatiga", angulos_excluidos: [] },
    conceptos: [
      ...FASE2_MOCK.conceptos,
      { ...FASE2_MOCK.conceptos[0], creativo_id: "TINNIDROP_X1", angulo_key: "DOLOR_EMOCIONAL_MASCULINO", canonico_id: "X1" },
    ],
  };
  renderizar("TINNIDROP");
  await screen.findByTestId("otros-conceptos");
  const en = [
    screen.getByTestId("estado-de-fase"),
    screen.getByTestId("bloque-ACCESIBILIDAD_MEDICO"),
    screen.getByTestId("bloque-NOCHES_SIN_DORMIR"),
    screen.getByTestId("bloque-DETERIORO_COGNITIVO"),
    screen.getByText(/Reingreso a FASE 1 activo/),
    screen.getByTestId("ordenes-renovar"),
    screen.getByTestId("angulos-no-funcionaron"),
    screen.getByTestId("otros-conceptos"),
  ];
  for (let i = 0; i < en.length - 1; i++) {
    expect(en[i].compareDocumentPosition(en[i + 1]) & Node.DOCUMENT_POSITION_FOLLOWING, `posición ${i}`).toBeTruthy();
  }
  expect(screen.queryByText(/^Galería de Conceptos \(/)).toBeNull();
});

// ── «Generar los conceptos que faltan (N)» por ángulo ganador ─────────────────────────────────

const ACCION_FABRICAR = "producto.fabricar_conceptos_fase2";

function fabricarDe(angulo: string, faltan: number, extra: Record<string, unknown> = {}) {
  return {
    accion_id: ACCION_FABRICAR,
    parametros: { producto_key: "TINNIDROP", angulo_key: angulo, n: String(faltan) },
    faltan,
    habilitada: true,
    trabajo_en_curso: null,
    ...extra,
  };
}

/** #1 y #2 con conceptos por fabricar, #3 completo, y un perdedor que (por error) trajera el campo. */
function fase2ConBotones(extra1: Record<string, unknown> = {}) {
  const fabricar: Record<string, unknown> = {
    ACCESIBILIDAD_MEDICO: fabricarDe("ACCESIBILIDAD_MEDICO", 8, extra1),
    NOCHES_SIN_DORMIR: fabricarDe("NOCHES_SIN_DORMIR", 10),
    DETERIORO_COGNITIVO: fabricarDe("DETERIORO_COGNITIVO", 0),
  };
  return {
    ...FASE2_MOCK,
    angulos: FASE2_MOCK.angulos.map((a) => (fabricar[a.angulo_key] ? { ...a, fabricar: fabricar[a.angulo_key] } : a)),
  };
}

const TEXTO_BOTON = (n: number) => `Generar los conceptos que faltan (${n})`;

test("fabricar: el botón aparece en cada ángulo ganador con conceptos por hacer, con su N, y nunca en los perdedores", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones();
  renderizar("TINNIDROP");

  const b1 = await within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO")).findByRole("button", { name: TEXTO_BOTON(8) });
  expect(b1).toBeEnabled();
  const g1 = screen.getByTestId("galeria-ACCESIBILIDAD_MEDICO");
  // el botón vive pegado al encabezado de su galería (justo antes), dentro del bloque de su ángulo
  expect(b1.compareDocumentPosition(g1) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(
    within(screen.getByTestId("bloque-NOCHES_SIN_DORMIR")).getByRole("button", { name: TEXTO_BOTON(10) }),
  ).toBeEnabled();
  // N = 0 → sin botón
  expect(within(screen.getByTestId("bloque-DETERIORO_COGNITIVO")).queryByRole("button", { name: /Generar los conceptos que faltan/ })).toBeNull();
  // perdedores: ni botón ni nada
  const apagados = screen.getByTestId("angulos-no-funcionaron");
  expect(within(apagados).queryByRole("button", { name: /Generar los conceptos que faltan/ })).toBeNull();
  expect(screen.getAllByRole("button", { name: /Generar los conceptos que faltan/ })).toHaveLength(2);
});

test("fabricar: pide confirmación con la explicación en palabras y no lanza nada hasta confirmar", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones();
  respuestas[`POST /api/acciones/${ACCION_FABRICAR}`] = {
    job_id: "job-fab-1", accion_id: ACCION_FABRICAR, estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/job-fab-1", url_eventos: "/api/trabajos/job-fab-1/eventos",
  };
  respuestas["GET /api/trabajos/job-fab-1"] = { job_id: "job-fab-1", estado: "CORRIENDO", unidades: [] };
  renderizar("TINNIDROP");

  const bloque = within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO"));
  fireEvent.click(await bloque.findByRole("button", { name: TEXTO_BOTON(8) }));

  const aviso = await bloque.findByTestId("confirmar-fabricar");
  expect(aviso.textContent).toContain(
    "La Fábrica de conceptos va a crear 8 conceptos nuevos para ACCESIBILIDAD_MEDICO y dejar sus prompts listos. No toca Meta ni mueve plata. Tarda unos minutos.",
  );
  expect(llamadasFetch.some((l) => l.metodo === "POST")).toBe(false);

  // cancelar cierra el aviso sin lanzar nada
  fireEvent.click(within(aviso).getByRole("button", { name: "Cancelar" }));
  await waitFor(() => expect(bloque.queryByTestId("confirmar-fabricar")).toBeNull());
  expect(llamadasFetch.some((l) => l.metodo === "POST")).toBe(false);

  // confirmar lanza la acción del manifiesto con confirmación explícita
  fireEvent.click(await bloque.findByRole("button", { name: TEXTO_BOTON(8) }));
  fireEvent.click(within(await bloque.findByTestId("confirmar-fabricar")).getByRole("button", { name: "Sí, confirmar y ejecutar" }));
  await waitFor(() => {
    const llamada = llamadasFetch.find((l) => l.url === `/api/acciones/${ACCION_FABRICAR}` && l.metodo === "POST");
    expect(llamada?.cuerpo).toEqual({
      parametros: { producto_key: "TINNIDROP", angulo_key: "ACCESIBILIDAD_MEDICO", n: "8" },
      confirmado: true,
    });
  });
});

test("fabricar: mientras el trabajo corre el botón dice «Generando…», no se puede volver a apretar y linkea al trabajo", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones();
  respuestas[`POST /api/acciones/${ACCION_FABRICAR}`] = {
    job_id: "job-fab-2", accion_id: ACCION_FABRICAR, estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/job-fab-2", url_eventos: "/api/trabajos/job-fab-2/eventos",
  };
  respuestas["GET /api/trabajos/job-fab-2"] = { job_id: "job-fab-2", estado: "CORRIENDO", unidades: [] };
  renderizar("TINNIDROP");

  const bloque = within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO"));
  fireEvent.click(await bloque.findByRole("button", { name: TEXTO_BOTON(8) }));
  fireEvent.click(within(await bloque.findByTestId("confirmar-fabricar")).getByRole("button", { name: "Sí, confirmar y ejecutar" }));

  const generando = await bloque.findByRole("button", { name: "Generando…" });
  expect(generando).toBeDisabled();
  expect(bloque.queryByRole("button", { name: TEXTO_BOTON(8) })).toBeNull();
  expect(await bloque.findByRole("link", { name: /Ver el progreso en vivo/ })).toBeInTheDocument();
  // el otro ángulo sigue libre
  expect(
    within(screen.getByTestId("bloque-NOCHES_SIN_DORMIR")).getByRole("button", { name: TEXTO_BOTON(10) }),
  ).toBeEnabled();
});

test("fabricar: un trabajo que ya corre (lo dice el backend) bloquea el botón al cargar la pantalla", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones({ trabajo_en_curso: "job-previo" });
  respuestas["GET /api/trabajos/job-previo"] = { job_id: "job-previo", estado: "CORRIENDO", unidades: [] };
  renderizar("TINNIDROP");

  const bloque = within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO"));
  expect(await bloque.findByRole("button", { name: "Generando…" })).toBeDisabled();
});

test("fabricar: al terminar bien la galería se recarga (vuelve a pedir el detalle de FASE 2)", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones({ trabajo_en_curso: "job-listo" });
  respuestas["GET /api/trabajos/job-listo"] = { job_id: "job-listo", estado: "EXITO", unidades: [] };
  renderizar("TINNIDROP");

  await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO");
  await waitFor(() => {
    const cargas = llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2" && l.metodo === "GET");
    expect(cargas.length).toBeGreaterThanOrEqual(2);
  });
});

test("fabricar: si la acción está deshabilitada el botón se ve pero no se puede apretar", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConBotones({ habilitada: false });
  renderizar("TINNIDROP");
  const bloque = within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO"));
  expect(await bloque.findByRole("button", { name: TEXTO_BOTON(8) })).toBeDisabled();
});

// ── «Marcar como generadas las imágenes que ya subiste» por ángulo ────────────────────────────

const ACCION_MARCAR = "producto.marcar_conceptos_generados";
const TEXTO_MARCAR = (n: number) => `Marcar como generadas las imágenes que ya subiste (${n})`;

function fase2ConMarcar() {
  const marcar: Record<string, unknown> = {
    ACCESIBILIDAD_MEDICO: {
      accion_id: ACCION_MARCAR,
      parametros: { producto_key: "TINNIDROP", angulo_key: "ACCESIBILIDAD_MEDICO" },
      listos: 3,
      habilitada: true,
    },
  };
  return {
    ...FASE2_MOCK,
    angulos: FASE2_MOCK.angulos.map((a) => (marcar[a.angulo_key] ? { ...a, marcar: marcar[a.angulo_key] } : a)),
  };
}

test("marcar: el botón aparece solo en el ángulo con imágenes listas y lanza la acción con producto y ángulo", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConMarcar();
  respuestas[`POST /api/acciones/${ACCION_MARCAR}`] = {
    job_id: "job-mar-1", accion_id: ACCION_MARCAR, estado: "ENCOLADO", repetido: false,
    url_estado: "/api/trabajos/job-mar-1", url_eventos: "/api/trabajos/job-mar-1/eventos",
  };
  respuestas["GET /api/trabajos/job-mar-1"] = { job_id: "job-mar-1", estado: "EXITO", unidades: [{ json: { ok: true } }] };
  renderizar("TINNIDROP");

  const boton = await within(await screen.findByTestId("bloque-ACCESIBILIDAD_MEDICO")).findByRole("button", { name: TEXTO_MARCAR(3) });
  expect(screen.getAllByRole("button", { name: /Marcar como generadas/ })).toHaveLength(1);
  const antes = llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length;
  fireEvent.click(boton);

  await waitFor(() => {
    const llamada = llamadasFetch.find((l) => l.url === `/api/acciones/${ACCION_MARCAR}` && l.metodo === "POST");
    expect(llamada?.cuerpo).toEqual({
      parametros: { producto_key: "TINNIDROP", angulo_key: "ACCESIBILIDAD_MEDICO" },
      confirmado: false,
    });
  });
  await waitFor(() => {
    expect(llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length).toBeGreaterThan(antes);
  });
});

// ── subir la imagen renderizada a mano sobre la tarjeta del concepto ──────────────────────────

function fase2ConSubida(puede: Record<string, boolean>) {
  return {
    ...FASE2_MOCK,
    conceptos: FASE2_MOCK.conceptos.map((c) => ({
      ...c,
      formato: puede[c.creativo_id] ? "IMAGEN" : "VIDEO",
      puede_subir: !!puede[c.creativo_id],
    })),
  };
}

test("subir: el control aparece solo en los conceptos que admiten imagen", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConSubida({ TINNIDROP_F2_C01: true });
  renderizar("TINNIDROP");

  await screen.findByText("Social Proof Wall");
  expect(screen.getAllByTestId(/^subir-/)).toHaveLength(1);
  expect(screen.getByText("Reemplazar imagen")).toBeDefined();
  expect(screen.getByTestId("subir-TINNIDROP_F2_C01")).toBeDefined();
  expect(screen.queryByTestId("subir-TINNIDROP_F2_C02")).toBeNull();
});

test("subir: el archivo va al endpoint del concepto y la galería se recarga", async () => {
  respuestas["GET /api/productos/TINNIDROP/fase2"] = fase2ConSubida({ TINNIDROP_F2_C02: true });
  respuestas["POST /api/productos/TINNIDROP/conceptos/TINNIDROP_F2_C02/imagen"] = { ok: true };
  renderizar("TINNIDROP");

  const control = (await screen.findByTestId("subir-TINNIDROP_F2_C02")) as HTMLInputElement;
  const antes = llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length;
  const archivo = new File([new Uint8Array([137, 80, 78, 71])], "descarga (3).png", { type: "image/png" });
  fireEvent.change(control, { target: { files: [archivo] } });

  await waitFor(() => {
    expect(
      llamadasFetch.some(
        (l) => l.metodo === "POST" && l.url === "/api/productos/TINNIDROP/conceptos/TINNIDROP_F2_C02/imagen",
      ),
    ).toBe(true);
  });
  await waitFor(() => {
    expect(llamadasFetch.filter((l) => l.url === "/api/productos/TINNIDROP/fase2").length).toBeGreaterThan(antes);
  });
  expect(llamadasFetch.some((l) => l.url.includes("/cargar/"))).toBe(false);
});
