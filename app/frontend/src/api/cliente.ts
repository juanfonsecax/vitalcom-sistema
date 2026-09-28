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
export type CorridaF1 = components["schemas"]["CorridaF1"];
export type PasoDeCorrida = components["schemas"]["PasoDeCorrida"];
export type MiembroDePaso = components["schemas"]["MiembroDePaso"];
export type SalidaDeEtapa = components["schemas"]["SalidaDeEtapa"];
export type CampanaF1 = components["schemas"]["CampanaF1"];
export type PiezaF1 = components["schemas"]["PiezaF1"];
export type BloqueDeFlujo = components["schemas"]["BloqueDeFlujo"];
export type SeccionDeFlujo = components["schemas"]["SeccionDeFlujo"];
export type FlujoBot = components["schemas"]["FlujoBot"];
export type ItemDeChecklist = components["schemas"]["ItemDeChecklist"];
export type BloqueoDelPaquete = components["schemas"]["BloqueoDelPaquete"];
export type PaqueteF1 = components["schemas"]["PaqueteF1"];
export type ChecklistF1 = components["schemas"]["ChecklistF1"];
export type Cuenta = components["schemas"]["Cuenta"];
export type FanPage = components["schemas"]["FanPage"];
export type OrdenItem = components["schemas"]["OrdenItem"];
export type OrdenesRespuesta = components["schemas"]["OrdenesRespuesta"];
export type ParametroMotor = components["schemas"]["ParametroMotor"];
export type Ganador = components["schemas"]["Ganador"];
export type Resultados = components["schemas"]["Resultados"];

/** Lo que el workflow deja pendiente para el operador: una orden a aprobar, una pregunta de Claude o
 * las imágenes que tiene que subir a mano a la biblioteca de Meta. */
export type LlamadaDeMeta = { n: number; tool: string; args: Record<string, unknown> };
export type ImagenDeLaOrden = { archivo: string; nombre_en_biblioteca: string; image_hash: string };
export type ImagenPorSubir = {
  archivo: string;
  nombre_en_biblioteca: string;
  archivo_a_subir: string;
  estado: "POR_SUBIR" | "OK" | "REPETIDA" | "SIN_LISTADO";
  hashes: string[];
};
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
        imagenes?: ImagenDeLaOrden[];
      };
    }
  | { tipo: "pregunta"; n: number; texto: string }
  | {
      tipo: "subida_media";
      vuelta: number;
      cuenta: string;
      cuenta_id: string;
      carpeta: string;
      archivos: ImagenPorSubir[];
      faltan: string[];
    };

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
  cuentas: () => pedir<Cuenta[]>("/api/cuentas"),
  fanpages: () => pedir<FanPage[]>("/api/fanpages"),
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
  avisarImagenesSubidas: (id: string, vuelta: number) =>
    pedir<unknown>(`/api/trabajos/${encodeURIComponent(id)}/media/${vuelta}`, { method: "POST" }),
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
  fase1Corrida: (clave: string) =>
    pedir<CorridaF1>(`/api/productos/${encodeURIComponent(clave)}/fase1/corrida`),
  fase1Campana: (clave: string) =>
    pedir<CampanaF1>(`/api/productos/${encodeURIComponent(clave)}/fase1/campana`),
  flujoBot: (clave: string) =>
    pedir<FlujoBot>(`/api/productos/${encodeURIComponent(clave)}/flujo-bot`),
  checklist: (clave: string) =>
    pedir<ChecklistF1>(`/api/productos/${encodeURIComponent(clave)}/checklist`),
  urlMedia: (clave: string, archivo: string) =>
    `/api/productos/${encodeURIComponent(clave)}/media/${encodeURIComponent(archivo)}`,
  cargarDato: (clave: string, accionId: string, datos: Record<string, unknown>, archivo?: File) => {
    const form = new FormData();
    form.append("datos", JSON.stringify(datos));
    if (archivo) {
      form.append("archivo", archivo);
    }
    return pedir<Record<string, unknown>>(
      `/api/productos/${encodeURIComponent(clave)}/cargar/${encodeURIComponent(accionId)}`,
      { method: "POST", body: form },
    );
  },
  ordenes: (producto?: string) =>
    pedir<OrdenesRespuesta>(producto ? `/api/ordenes?producto=${encodeURIComponent(producto)}` : "/api/ordenes"),
  ganadores: () => pedir<Ganador[]>("/api/ganadores"),
  fase2: (clave: string) => pedir<Fase2Detalle>(`/api/productos/${encodeURIComponent(clave)}/fase2`),
  fase3: (clave: string) => pedir<Fase3Detalle>(`/api/productos/${encodeURIComponent(clave)}/fase3`),
  fase4: (clave: string) => pedir<Fase4Detalle>(`/api/productos/${encodeURIComponent(clave)}/fase4`),
  resultados: () => pedir<Resultados>("/api/resultados"),
  historialResultados: () => pedir<Resultados[]>("/api/resultados/historial"),
  cargarResultados: (formulario: FormData) =>
    pedir<Resultados>("/api/resultados/cargar", { method: "POST", body: formulario }),
  reingresoF1: (clave: string, motivo?: string) =>
    pedir<{ ok: boolean; producto_key: string; fase_destino: string; angulos_excluidos: string[]; motivo: string }>(
      `/api/productos/${encodeURIComponent(clave)}/reingreso-f1`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motivo: motivo ?? "Ángulo agotado / fatiga" }),
      },
    ),
};

export type ConceptoFase2 = components["schemas"]["ConceptoFase2"];
export type AnguloFase2 = components["schemas"]["AnguloFase2"];
export type FatigaFase2 = components["schemas"]["FatigaFase2"];
export type ReingresoActivo = components["schemas"]["ReingresoActivo"];
export type Fase2Detalle = components["schemas"]["Fase2Detalle"];

export type EventoCambioBot = components["schemas"]["EventoCambioBot"];
export type CierrePostCambioBot = components["schemas"]["CierrePostCambioBot"];
export type Fase3Detalle = components["schemas"]["Fase3Detalle"];

export type PlanCbo = components["schemas"]["PlanCbo"];
export type ExpansionEscalado = components["schemas"]["ExpansionEscalado"];
export type FatigaEscalado = components["schemas"]["FatigaEscalado"];
export type Fase4Detalle = components["schemas"]["Fase4Detalle"];
