/**
 * cliente.ts — el único lugar que habla con la API.
 *
 * Los tipos NO se escriben acá: salen de `esquema.d.ts`, que genera openapi-typescript
 * desde el OpenAPI de FastAPI (`pnpm tipos`). Un contrato, un dueño: si el backend cambia
 * un campo, esto deja de compilar en vez de mentir en pantalla.
 */
import type { components } from "./esquema";

export type Producto = components["schemas"]["Producto"];
export type Flujo = components["schemas"]["Flujo"];
export type Nodo = components["schemas"]["Nodo"];
export type Requisito = components["schemas"]["Requisito"];
export type Salud = components["schemas"]["Salud"];
export type Decisiones = components["schemas"]["Decisiones"];
export type Costeo = components["schemas"]["Costeo"];
export type Accion = components["schemas"]["Accion"];
export type AccionEncolada = components["schemas"]["AccionEncolada"];
export type Trabajo = components["schemas"]["Trabajo"];
export type TrabajoDetalle = components["schemas"]["TrabajoDetalle"];
export type EstadoDeClaude = components["schemas"]["EstadoDeClaude"];

/** Lo que el workflow deja pendiente para el operador: una orden a aprobar o una pregunta de Claude. */
export type LlamadaDeMeta = { n: number; tool: string; args: Record<string, unknown> };
export type Pendiente =
  | {
      tipo: "aprobacion";
      orden_id: number;
      hash: string;
      caduca_horas: number;
      orden: {
        tipo: string;
        producto: string | null;
        fase: string;
        brazo: string;
        cuenta: string | null;
        llamadas: LlamadaDeMeta[];
        manifiesto: Record<string, unknown> | null;
      };
    }
  | { tipo: "pregunta"; n: number; texto: string };

/** Un evento del progreso en vivo (SSE). */
export type LineaEnVivo = { unidad: number; texto: string; tipo: "salida" | "error" | "comando" | "claude" };

/** Lo que devuelve `alta_producto.py --json`: el plan aplicado (o por aplicar). */
export type ResultadoAlta = {
  ok: boolean;
  aplicado: boolean;
  producto_key: string;
  nombre_display: string;
  archivo_datos: string;
  packshot: string;
  carpeta_media: string;
  carpeta_transcripciones: string;
  costo_q: string;
};

export type ResultadoTranscripcion = {
  ok: boolean;
  carpeta_salida: string;
  modelo: string;
  archivos: { video: string; txt: string; estado: string; palabras: number | null }[];
  sin_voz: string[];
};

export class ErrorDeContrato extends Error {
  constructor(
    message: string,
    readonly estado: number,
    /** El `codigo` del contrato de acciones (p. ej. `FALTA_CONFIRMACION`, `NODO_NO_LISTO`). */
    readonly codigo?: string,
  ) {
    super(message);
  }
}

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(ruta, opciones);
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}) as { detail?: string; codigo?: string });
    throw new ErrorDeContrato(cuerpo.detail ?? respuesta.statusText, respuesta.status, cuerpo.codigo);
  }
  return (await respuesta.json()) as T;
}

export const api = {
  productos: () => pedir<Producto[]>("/api/productos"),
  producto: (clave: string) => pedir<Flujo>(`/api/productos/${encodeURIComponent(clave)}`),
  decisiones: () => pedir<Decisiones>("/api/decisiones"),
  salud: () => pedir<Salud>("/api/salud"),
  sistema: () => pedir<{ base: string }>("/api/sistema"),
  costeo: (costo: string) => pedir<Costeo>(`/api/costeo/${encodeURIComponent(costo)}`),
  alta: (formulario: FormData) =>
    pedir<ResultadoAlta>("/api/productos", { method: "POST", body: formulario }),
  claude: () => pedir<EstadoDeClaude>("/api/claude/estado"),
  acciones: (nodo?: string, productoKey?: string) => {
    const filtros = new URLSearchParams();
    if (nodo) filtros.set("nodo", nodo);
    if (productoKey) filtros.set("producto_key", productoKey);
    return pedir<Accion[]>(`/api/acciones?${filtros}`);
  },
  pedirAccion: (id: string, parametros: Record<string, unknown>, confirmado = false) =>
    pedir<AccionEncolada>(`/api/acciones/${encodeURIComponent(id)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parametros, confirmado }),
    }),
  transcribir: (clave: string, modelo = "small") =>
    api.pedirAccion("producto.transcribir", { producto_key: clave, modelo }),
  trabajos: () => pedir<Trabajo[]>("/api/trabajos"),
  trabajo: (id: string) => pedir<TrabajoDetalle>(`/api/trabajos/${encodeURIComponent(id)}`),
  aprobar: (id: string, ordenId: number, decision: "APROBADA" | "RECHAZADA", huella: string) =>
    pedir<unknown>(`/api/trabajos/${encodeURIComponent(id)}/aprobaciones/${ordenId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, hash: huella, nota: "" }),
    }),
  responder: (id: string, n: number, texto: string) =>
    pedir<unknown>(`/api/trabajos/${encodeURIComponent(id)}/respuesta`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ n, texto }),
    }),
  reintentar: (id: string, confirmado: boolean) =>
    pedir<AccionEncolada>(`/api/trabajos/${encodeURIComponent(id)}/reintentar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmado }),
    }),
  cancelar: (id: string) =>
    pedir<unknown>(`/api/trabajos/${encodeURIComponent(id)}/cancelar`, { method: "POST" }),
  descartar: (id: string) =>
    pedir<unknown>(`/api/trabajos/${encodeURIComponent(id)}/descartar`, { method: "POST" }),
};
