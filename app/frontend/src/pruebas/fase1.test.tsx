/**
 * fase1.test.tsx — pruebas de la pantalla Fase1 (Hito 4).
 *
 * Verifica:
 * 1. Las instrucciones >> van aparte y NO entran en el texto copiado al portapapeles.
 * 2. El checklist muestra un campo de archivo por cada pieza faltante.
 * 3. En avatares y ángulos se muestra la frase requerida sobre el embudo TOFU/MOFU/BOFU.
 * 4. En Anuncios, el aviso "falta la pieza" es un botón que lleva al Checklist y deja a la
 *    vista el input del archivo exacto.
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
import { Fase1 } from "../pantallas/Fase1";

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

function renderizar(clave = "TURMERIC") {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const raiz = createRootRoute();
  const ruta = createRoute({
    getParentRoute: () => raiz,
    path: "/producto/$clave/fase1",
    component: Fase1,
  });
  const historia = createMemoryHistory({
    initialEntries: [`/producto/${clave}/fase1`],
  });
  const router = createRouter({ routeTree: raiz.addChildren([ruta]), history: historia });
  return render(
    <QueryClientProvider client={cliente}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  respuestas = {};
  llamadasFetch = [];
  simularFetch();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("las instrucciones >> en Flujo LucidBot NO entran en el texto copiado al portapapeles", async () => {
  respuestas["GET /api/productos/TURMERIC/fase1/corrida"] = {
    producto_key: "TURMERIC",
    corrida: null,
    etapas: [],
  };
  respuestas["GET /api/productos/TURMERIC/fase1/campana"] = {
    producto_key: "TURMERIC",
    lanzador: null,
    plan_fuente: null,
    piezas: [],
  };
  respuestas["GET /api/productos/TURMERIC/checklist"] = {
    producto_key: "TURMERIC",
    nodo_actual: "F1.paquete",
    faltan: [],
    paquete: null,
  };
  respuestas["GET /api/productos/TURMERIC/flujo-bot"] = {
    producto_key: "TURMERIC",
    ok: true,
    secciones: [
      {
        titulo: "BIENVENIDA Y CIERRE",
        instrucciones: ["Instrucción general que nunca se copia"],
        bloques: [
          {
            titulo: "BLOQUE 1 — SALUDO",
            pegar: "¡Hola! Gracias por comunicarte con VitalCom Guatemala.\n¿Deseas conocer más sobre Turmeric?",
            instrucciones: [
              "No insistir si no responde de inmediato.",
              "Responder solo dudas sobre dosis antes del precio.",
            ],
            pendientes: [],
          },
        ],
      },
    ],
  };

  const writeTextMock = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, {
    clipboard: { writeText: writeTextMock },
  });

  renderizar("TURMERIC");

  await waitFor(() => {
    expect(screen.getByText("Flujo LucidBot")).toBeInTheDocument();
  });

  // Cambiar a pestaña Flujo LucidBot
  fireEvent.click(screen.getByText("Flujo LucidBot"));

  await waitFor(() => {
    expect(screen.getByText("BIENVENIDA Y CIERRE")).toBeInTheDocument();
    expect(screen.getByText("BLOQUE 1 — SALUDO")).toBeInTheDocument();
  });

  // Las instrucciones deben verse en pantalla
  expect(
    screen.getByText(">> No insistir si no responde de inmediato."),
  ).toBeInTheDocument();
  expect(
    screen.getByText(">> Responder solo dudas sobre dosis antes del precio."),
  ).toBeInTheDocument();

  // Hacer clic en Copiar texto a pegar
  const botonCopiar = screen.getByText("Copiar texto a pegar");
  fireEvent.click(botonCopiar);

  expect(writeTextMock).toHaveBeenCalledTimes(1);
  const textoCopiado = writeTextMock.mock.calls[0][0];

  // El texto copiado debe ser estrictamente lo de "pegar"
  expect(textoCopiado).toContain("¡Hola! Gracias por comunicarte con VitalCom Guatemala.");
  expect(textoCopiado).toContain("¿Deseas conocer más sobre Turmeric?");

  // Las instrucciones NUNCA deben entrar en el texto copiado
  expect(textoCopiado).not.toContain("No insistir si no responde de inmediato");
  expect(textoCopiado).not.toContain("Responder solo dudas sobre dosis");
  expect(textoCopiado).not.toContain("Instrucción general que nunca se copia");
  expect(textoCopiado).not.toContain(">>");
});

test("el checklist muestra un campo por cada pieza faltante", async () => {
  respuestas["GET /api/productos/TURMERIC/fase1/corrida"] = {
    producto_key: "TURMERIC",
    corrida: null,
    etapas: [],
  };
  respuestas["GET /api/productos/TURMERIC/fase1/campana"] = {
    producto_key: "TURMERIC",
    lanzador: null,
    plan_fuente: null,
    piezas: [],
  };
  respuestas["GET /api/productos/TURMERIC/flujo-bot"] = {
    producto_key: "TURMERIC",
    ok: true,
    secciones: [],
  };
  respuestas["GET /api/productos/TURMERIC/checklist"] = {
    producto_key: "TURMERIC",
    nodo_actual: "F1.publicar",
    estado: "BLOQUEADO",
    ejecutor: "operador",
    faltan: [],
    paquete: {
      bloqueantes: [
        {
          falta: "faltan 3 piezas creativas en disco",
          lo_produce: "operador",
          ambito: "media",
          clave: "piezas",
          archivos: ["TURMERIC_P1.png", "TURMERIC_P2.png", "TURMERIC_P3.png"],
          escritor: "producto.cargar_pieza",
        },
      ],
      avisos: [],
      preflight: null,
    },
  };

  renderizar("TURMERIC");

  await waitFor(() => {
    expect(screen.getByText("Checklist")).toBeInTheDocument();
  });

  fireEvent.click(screen.getByText("Checklist"));

  await waitFor(() => {
    expect(screen.getByText("faltan 3 piezas creativas en disco")).toBeInTheDocument();
  });

  // Cada uno de los tres archivos declarados debe tener su fila con su propio nombre y botón
  expect(screen.getByText("TURMERIC_P1.png")).toBeInTheDocument();
  expect(screen.getByText("TURMERIC_P2.png")).toBeInTheDocument();
  expect(screen.getByText("TURMERIC_P3.png")).toBeInTheDocument();

  expect(screen.getByLabelText("Subir archivo para TURMERIC_P1.png")).toBeInTheDocument();
  expect(screen.getByLabelText("Subir archivo para TURMERIC_P2.png")).toBeInTheDocument();
  expect(screen.getByLabelText("Subir archivo para TURMERIC_P3.png")).toBeInTheDocument();
});

test("la pestaña de avatares y ángulos no muestra TOFU/MOFU/BOFU y muestra la frase exacta de doctrina", async () => {
  respuestas["GET /api/productos/TURMERIC/fase1/corrida"] = {
    producto_key: "TURMERIC",
    corrida: null,
    etapas: [
      {
        paso: 6,
        etapa: "etapa-2",
        archivo: "06_etapa-2.md",
        texto: "### ÁNGULO 1 — Hígado graso y digestión\nTexto detallado del ángulo 1.",
      },
    ],
  };
  respuestas["GET /api/productos/TURMERIC/fase1/campana"] = {
    producto_key: "TURMERIC",
    lanzador: null,
    plan_fuente: {
      conjuntos: [
        {
          n: 1,
          angulo_key: "HIGADO_GRASO",
          angulo_titulo: "Hígado graso y digestión",
          avatar_genero: "MIXTO",
          avatar_edad: "40-65",
          nivel_conciencia: "3A",
          formato: "IMAGEN",
        },
      ],
    },
    piezas: [],
  };
  respuestas["GET /api/productos/TURMERIC/flujo-bot"] = {
    producto_key: "TURMERIC",
    ok: true,
    secciones: [],
  };
  respuestas["GET /api/productos/TURMERIC/checklist"] = {
    producto_key: "TURMERIC",
    nodo_actual: "F1.paquete",
    faltan: [],
    paquete: null,
  };

  renderizar("TURMERIC");

  await waitFor(() => {
    expect(screen.getByText("Avatares y ángulos")).toBeInTheDocument();
  });

  fireEvent.click(screen.getByText("Avatares y ángulos"));

  await waitFor(() => {
    expect(screen.getByText("Hígado graso y digestión")).toBeInTheDocument();
  });

  // NO debe mostrar TOFU/MOFU/BOFU; debe mostrar la frase exacta requerida
  const embudos = screen.getAllByText(
    /Embudo: pendiente de decisión del operador \(la doctrina dice tres cosas distintas\)/,
  );
  expect(embudos.length).toBeGreaterThan(0);
  expect(screen.queryByText(/TOFU/i)).toBeNull();
  expect(screen.queryByText(/MOFU/i)).toBeNull();
  expect(screen.queryByText(/BOFU/i)).toBeNull();
});

test("el botón Armar FASE 1 pide confirmación antes de llamar a la API", async () => {
  respuestas["GET /api/productos/TURMERIC/fase1/corrida"] = {
    producto_key: "TURMERIC",
    corrida: null,
    etapas: [],
  };
  respuestas["GET /api/productos/TURMERIC/fase1/campana"] = {
    producto_key: "TURMERIC",
    lanzador: null,
    plan_fuente: null,
    piezas: [],
  };
  respuestas["GET /api/productos/TURMERIC/flujo-bot"] = {
    producto_key: "TURMERIC",
    ok: true,
    secciones: [],
  };
  respuestas["GET /api/productos/TURMERIC/checklist"] = {
    producto_key: "TURMERIC",
    nodo_actual: "F1.paquete",
    faltan: [],
    paquete: null,
  };
  respuestas["GET /api/acciones"] = [];
  respuestas["POST /api/acciones/nodo.F1.paquete"] = {
    ok: true,
    job_id: "trabajo-fase1-123",
    mensaje: "Iniciado",
  };

  renderizar("TURMERIC");

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Armar FASE 1" })).toBeInTheDocument();
  });

  // 1. Antes de hacer clic, no debe haber llamada POST a la API
  const postAntes = llamadasFetch.filter(
    (l) => l.metodo === "POST" && l.url === "/api/acciones/nodo.F1.paquete",
  );
  expect(postAntes).toHaveLength(0);

  // 2. Hacer clic en "Armar FASE 1"
  fireEvent.click(screen.getByRole("button", { name: "Armar FASE 1" }));

  // 3. Debe aparecer el cuadro de confirmación explícito
  await waitFor(() => {
    expect(screen.getByText("¿Confirmar Armar FASE 1?")).toBeInTheDocument();
  });

  // 4. Todavía NO debe haberse llamado a la API
  const postDuranteConfirmacion = llamadasFetch.filter(
    (l) => l.metodo === "POST" && l.url === "/api/acciones/nodo.F1.paquete",
  );
  expect(postDuranteConfirmacion).toHaveLength(0);

  // 5. Al confirmar explícitamente, se llama a la API con confirmado: true
  const botonConfirmar = screen.getByRole("button", { name: "Sí, confirmar y ejecutar" });
  fireEvent.click(botonConfirmar);

  await waitFor(() => {
    const postDespues = llamadasFetch.filter(
      (l) => l.metodo === "POST" && l.url === "/api/acciones/nodo.F1.paquete",
    );
    expect(postDespues).toHaveLength(1);
    expect(postDespues[0].cuerpo).toEqual({
      parametros: { producto_key: "TURMERIC" },
      confirmado: true,
    });
  });
});

test("«falta la pieza»: el botón lleva al Checklist y deja a la vista el input del archivo exacto", async () => {
  respuestas["GET /api/productos/TURMERIC/fase1/corrida"] = {
    producto_key: "TURMERIC",
    corrida: null,
    etapas: [],
  };
  respuestas["GET /api/productos/TURMERIC/fase1/campana"] = {
    producto_key: "TURMERIC",
    lanzador: null,
    plan_fuente: {
      conjuntos: [
        {
          n: 1,
          angulo_key: "HIGADO_GRASO",
          angulo_titulo: "Hígado graso y digestión",
          nombre: "Conjunto 1 — Hígado graso",
          formato: "IMAGEN",
          lleva_precio: true,
          archivo_creativo: "TURMERIC_P1.png",
          copy: {
            textos: ["¿Te pasa que ya no sabés qué comer sin sentirte pesado?"],
            titulos: ["Título 1"],
            descripcion: "Descripción del anuncio",
          },
        },
      ],
    },
    piezas: [],
  };
  respuestas["GET /api/productos/TURMERIC/flujo-bot"] = {
    producto_key: "TURMERIC",
    ok: true,
    secciones: [],
  };
  respuestas["GET /api/productos/TURMERIC/checklist"] = {
    producto_key: "TURMERIC",
    nodo_actual: "F1.publicar",
    estado: "BLOQUEADO",
    ejecutor: "operador",
    faltan: [],
    paquete: {
      bloqueantes: [
        {
          falta: "falta 1 pieza creativa en disco",
          lo_produce: "operador",
          ambito: "media",
          clave: "piezas",
          archivos: ["TURMERIC_P1.png"],
          escritor: "producto.cargar_pieza",
        },
      ],
      avisos: [],
      preflight: null,
    },
  };

  // jsdom no implementa `scrollIntoView`: el stub registra el `aria-label` de lo que se pidió
  // llevar a la vista, y se restaura al terminar para no filtrarlo a las demás pruebas.
  const scrolles: string[] = [];
  const original = window.HTMLElement.prototype.scrollIntoView;
  window.HTMLElement.prototype.scrollIntoView = function (this: HTMLElement) {
    scrolles.push(this.getAttribute("aria-label") ?? this.id);
  };
  try {
    renderizar("TURMERIC");

    // Ir a Anuncios (la barra tarda un tick en montarse): el conjunto declara
    // TURMERIC_P1.png y ninguna pieza está cargada.
    fireEvent.click(await screen.findByText("Anuncios"));
    await waitFor(() => {
      expect(screen.getByText("falta la pieza")).toBeInTheDocument();
    });

    // El aviso ya no es solo texto: es un botón que lleva al Checklist marcando ese archivo.
    fireEvent.click(screen.getByRole("button", { name: "Subirla en el Checklist" }));

    // El Checklist queda activo, con el input del archivo exacto en su fila marcada…
    const input = await screen.findByLabelText("Subir archivo para TURMERIC_P1.png");
    expect(input).toBeInTheDocument();
    expect(screen.getByText("falta 1 pieza creativa en disco")).toBeInTheDocument();
    expect(input.closest("[data-archivo='TURMERIC_P1.png']")).not.toBeNull();
    // …y el scroll lo deja a la vista.
    await waitFor(() => expect(scrolles).toContain("Subir archivo para TURMERIC_P1.png"));
  } finally {
    window.HTMLElement.prototype.scrollIntoView = original;
  }
});
