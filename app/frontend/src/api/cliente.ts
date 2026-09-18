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

export class ErrorDeContrato extends Error {
  constructor(
    message: string,
    readonly estado: number,
  ) {
    super(message);
  }
}

async function pedir<T>(ruta: string): Promise<T> {
  const respuesta = await fetch(ruta);
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
};
