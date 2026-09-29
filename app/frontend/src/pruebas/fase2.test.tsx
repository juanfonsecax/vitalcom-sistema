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
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  fase: "FASE 2",
  nodo_actual: "F2.etapa-11",
  angulo_ganador: "ACCESIBILIDAD_MEDICO",
  conceptos_generados: 10,
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
  expect(hero.textContent).toContain("Q41.5");
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

test("la galería agrupa por ángulo y arranca en el #1", async () => {
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

  const pestanas = await screen.findAllByRole("tab");
  expect(pestanas.map((t) => t.textContent)).toEqual(["ACCESIBILIDAD_MEDICO", "NOCHES_SIN_DORMIR"]);
  expect(pestanas[0].getAttribute("aria-selected")).toBe("true");
  expect(screen.getByText("Before / After Split")).toBeDefined();
  expect(screen.queryByText("Testimonio de noche")).toBeNull();

  fireEvent.click(pestanas[1]);
  expect(screen.getByText("Testimonio de noche")).toBeDefined();
  expect(screen.queryByText("Before / After Split")).toBeNull();
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

  fireEvent.click(await screen.findByRole("tab", { name: "NOCHES_SIN_DORMIR" }));
  expect(await screen.findByText("Se genera cuando le toque su Fase 2.")).toBeDefined();
  expect((screen.getByRole("button", { name: BOTON_GENERAR }) as HTMLButtonElement).disabled).toBe(true);
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
