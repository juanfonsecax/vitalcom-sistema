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
  ) {
    super(message);
  }
}

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(ruta, opciones);
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}) as { detail?: string });
    throw new ErrorDeContrato(cuerpo.detail ?? respuesta.statusText, respuesta.status);
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
  transcribir: (clave: string) =>
    pedir<ResultadoTranscripcion>(`/api/productos/${encodeURIComponent(clave)}/transcribir`, {
      method: "POST",
    }),
};
