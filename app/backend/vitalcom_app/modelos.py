"""modelos.py — la forma de lo que la app sirve, para que el frontend no redefina campos.

Los modelos son deliberadamente permisivos (`extra="allow"`): el dueño de cada contrato es
el motor, y si `flujo.py` o `decidir.py` agregan un campo, la app lo pasa sin romperse.
Lo que sí se fija es lo que la pantalla necesita para dibujar.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    model_config = ConfigDict(extra="allow")


class Producto(Base):
    """Fila de `_DIM_PRODUCTOS.csv` + fase y nodo vigentes de `_ESTADO_FLUJO.csv`."""

    producto_key: str
    nombre_display: str = ""
    estado: str = ""
    cuenta_alias: str = ""
    moneda: str = ""
    # Los montos viajan como el CSV los escribe: texto, sin convertir ni redondear.
    costo_q: str = ""
    precio_base_q: str = ""
    cpa_base_q: str = ""
    cpa_be_q: str = ""
    campaign_id: str = ""
    fase_bitacora: str = ""  # la columna `fase` del CSV; quedó como bitácora
    # Derivado por flujo.py (esto es lo que manda):
    fase: str | None = None
    nodo_actual: str | None = None
    estado_flujo: str | None = None
    bloqueantes: int | None = None
    siguiente_ejecutor: str | None = None
    evaluado_el: str | None = None


class Requisito(Base):
    dato: str = ""
    ok: bool = False
    observado: str = ""
    dueno: str = ""
    regla: str = ""


class Nodo(Base):
    id: str
    titulo: str = ""
    ejecutor: str = ""
    ejecutor_tipo: str = ""
    como: str = ""
    estado: str = ""
    cumplido: bool = False
    ciclo: bool = False
    secuencia: list[Any] = []
    produce: list[Requisito] = []
    avisos: list[Any] = []


class Flujo(Base):
    """Salida de `flujo.py <pk> --json`, la vista completa del producto en el grafo."""

    producto_key: str
    nombre: str = ""
    estado_producto: str = ""
    fase: str = ""
    fase_titulo: str = ""
    nodo_actual: str = ""
    estado: str = ""
    ejecutor: str = ""
    como: str = ""
    evaluado_el: str = ""
    bloqueantes: list[Requisito] = []
    falta_para_cumplir: list[Requisito] = []
    entradas: list[Any] = []
    nodos: list[Nodo] = []
    avisos: list[Any] = []
    ordenes: list[Any] = []
    avance: dict[str, Any] | None = None
    motor: dict[str, Any] | None = None


class Salud(Base):
    """`VISTAS/_ESTADO.json`: frescura por vista, calculada por gen_app.py."""

    generado: str = ""
    version: int | None = None
    secciones: list[Any] = []
    vistas: list[Any] = []
    salud: dict[str, Any] | None = None
    meta_falso: bool = False


class CapaAnalitica(Base):
    """Estado del último `dbt build` (g07-cimientos T2). "FALLO" significa que el motor está
    leyendo los CSV directamente y la capa analitica quedó vieja — visible aca, no solo en stdout."""

    estado: str = "DESCONOCIDO"
    detalle: str = ""
    generado: str = ""


class Decisiones(Base):
    """`_DECISIONES.json`: lo que dictó `decidir.py`. La app no lo reinterpreta."""

    generado: str = ""
    datos_desde: str = ""
    datos_hasta: str = ""
    rezago_dias: int | None = None
    motor: str = ""
    ventana_dias: int | None = None
    resumen_acciones: dict[str, int] = {}
    cobertura_gasto: dict[str, int] = {}
    capa_analitica: CapaAnalitica | None = None
    productos: list[Any] = []


class Escalera(Base):
    unidades: int
    precio: float
    costo_pedido: float


class Costeo(Base):
    """Salida de `costear.py --json`. Las cifras salen de `_DIM_COSTEO.csv`, nunca de acá."""

    costo_ingresado: float
    fila_usada: float
    criterio_de_fila: str = ""
    precio_1u: float | None = None
    cpa_objetivo: float | None = None
    cpa_base: float | None = None
    cpa_break_even: float | None = None
    valor_envio: float | None = None
    utilidad_esperada: float | None = None
    escalera: list[Escalera] = []
    arranque: dict[str, Any] = {}
    fuente: str = ""
    origen_escalera: str = ""


class Resultados(Base):
    """Salida de `gen_pl.py --json` (T4a): el estado de resultados real, DOCTRINA/CONTABILIDAD.md.

    `vista_a_cohorte` y `vista_b_caja` quedan como dict libre: su forma exacta la fija
    `gen_pl.py`, no la app (regla de oro: la app no calcula ni redefine el contrato). La
    bandera de cohorte PRELIMINAR vive en `vista_a_cohorte["preliminar"]`, tal cual la decide
    el script con `dias_cohorte_maduro` de `_PARAMETROS_FINANZAS.csv`.
    """

    periodo: dict[str, Any] = {}
    vista_a_cohorte: dict[str, Any] = {}
    vista_b_caja: dict[str, Any] | None = None
    alertas: list[str] = []
    integridad: dict[str, Any] = {}
    fallos: list[str] = []
    ok: bool = True


class Accion(Base):
    """Una acción con botón, tal como la declara `VISTAS/_MANIFIESTO.json` (diseño §2.5)."""

    id: str
    rotulo: str
    nodo: str | None = None
    ejecutor_tipo: str
    parametros: dict[str, Any] = {}
    requiere_confirmacion: bool
    aprobacion: str
    toca_meta: bool
    escribe: list[str] = []
    habilitada: bool
    motivo: str | None = None
    tiempo_max_s: int
    datos_del_operador: list[Any] | None = None
    # Solo con `producto_key`: si se puede pedir ahora, y por qué sí o por qué no.
    disponible: bool | None = None
    por_que: dict[str, Any] | None = None


class PedidoAccion(BaseModel):
    """El cuerpo de `POST /api/acciones/{id}`."""

    parametros: dict[str, Any] = {}
    confirmado: bool = False
    job_id: str | None = None


class AccionEncolada(Base):
    job_id: str
    accion_id: str
    estado: str
    url_estado: str
    url_eventos: str
    repetido: bool = False


class Trabajo(Base):
    """Un trabajo del runner, para la lista de la pantalla Trabajos."""

    job_id: str
    accion_id: str = ""
    rotulo: str = ""
    producto_key: str | None = None
    estado: str
    iniciado: str | None = None
    terminado: str | None = None
    app_version: str = ""
    otra_version: bool = False
    pendiente: str | None = None  # "aprobacion" | "pregunta" | "subida_media" | None


class TrabajoDetalle(Trabajo):
    """El trabajo completo: lo pendiente con todo su detalle (la orden o la pregunta) y el resultado."""

    parametros: dict[str, Any] = {}
    sello: dict[str, Any] = {}
    pendiente_completo: dict[str, Any] | None = None
    unidades: list[Any] = []
    resultado: dict[str, Any] | None = None
    run_dir: str | None = None
    error: str | None = None


class DecisionDeOrden(BaseModel):
    decision: str  # APROBADA | RECHAZADA
    hash: str      # la huella de la orden que la pantalla mostró
    nota: str = ""


class RespuestaDeClaude(BaseModel):
    n: int
    texto: str


class Reintento(BaseModel):
    confirmado: bool = False


class EstadoDeClaude(Base):
    logueado: bool
    detalle: str = ""
    credencial_prohibida: list[str] = []
    meta_falso: bool = False


class Cuenta(Base):
    cuenta_alias: str
    cuenta_id: str
    moneda: str
    mcp_habilitado: str
    sube_media_local: str
    estado_cuenta: str


# ── FASE 1 (Hito 4) ───────────────────────────────────────────────────────────

class MiembroDePaso(Base):
    etapa: str
    salida: str
    estado: str = "PENDIENTE"  # PENDIENTE · CORRIENDO · EXITO · HEREDADO · ESPERA_RESPUESTA · FALLIDO …
    detalle: str | None = None
    pregunta: str | None = None
    duracion_s: float | None = None
    costo_equivalente_usd: float | None = None


class PasoDeCorrida(Base):
    n: int
    etapas: list[str]
    estado: str = "PENDIENTE"
    miembros: list[MiembroDePaso] = []


class Corrida(Base):
    job_id: str | None = None
    run_dir: str
    iniciado: str | None = None
    estado: str | None = None
    retomado_de: str | None = None
    pasos: list[PasoDeCorrida] = []


class SalidaDeEtapa(Base):
    paso: int
    etapa: str
    archivo: str
    texto: str | None = None  # lo que devolvió la etapa, textual; None si todavía no corrió


class CorridaF1(Base):
    """La última corrida de «Armar FASE 1»: avance y lo que devolvió cada etapa."""

    producto_key: str
    corrida: Corrida | None = None
    inputs_congelados: str | None = None
    etapas: list[SalidaDeEtapa] = []


class PiezaF1(Base):
    n: int | None = None
    angulo_key: str | None = None
    archivo: str | None = None
    url: str | None = None  # None = el archivo todavía no está en disco


class CampanaF1(Base):
    """El lanzador del producto (`_LANZADOR.json`) y el `_PLAN.json` de origen, tal cual."""

    producto_key: str
    lanzador: dict[str, Any] | None = None
    plan_fuente: dict[str, Any] | None = None
    piezas: list[PiezaF1] = []
    lanzador_generado: str | None = None


class BloqueDeFlujo(Base):
    titulo: str
    pegar: str
    instrucciones: list[str] = []
    pendientes: list[str] = []


class SeccionDeFlujo(Base):
    titulo: str
    instrucciones: list[str] = []
    bloques: list[BloqueDeFlujo] = []


class FlujoBot(Base):
    """`gen_flujo_bot.py --json --parcial`: el flujo por bloques, las instrucciones `>>` aparte."""

    producto_key: str
    ok: bool
    faltan: list[dict[str, Any]] = []
    avisos: list[str] = []
    prohibiciones: list[str] = []
    encabezado: dict[str, Any] | None = None
    secciones: list[SeccionDeFlujo] = []


class ItemDeChecklist(Base):
    dato: str
    ok: bool = False
    observado: str | None = None
    dueno: str | None = None
    escritores: list[str] = []


class BloqueoDelPaquete(Base):
    falta: str
    lo_produce: str
    ambito: str
    clave: str | None = None
    archivos: list[str] = []
    escritor: str | None = None


class PaqueteF1(Base):
    bloqueantes: list[BloqueoDelPaquete] = []
    avisos: list[str] = []
    preflight: Any = None


class ChecklistF1(Base):
    """Lo que falta (de `flujo.py`) y los bloqueos del paquete (de `gen_publicacion.py`), con su escritor."""

    producto_key: str
    nodo_actual: str | None = None
    estado: str | None = None
    ejecutor: str | None = None
    faltan: list[ItemDeChecklist] = []
    paquete: PaqueteF1 | None = None


class OrdenItem(Base):
    producto_key: str
    angulo_key: str
    angulo_nombre: str = ""
    estado: str
    accion_codigo: str | None = None
    frase_simple: str
    por_que: dict[str, Any] = {}
    bloqueo_fase: str | None = None
    ejecutable: bool = True
    conjuntos: list[str] = []


class PendienteRegistro(Base):
    """Un conjunto NUESTRO de Meta (producto_key clasificado) que todavía no
    tiene fila de `angulo_key` en `_DIM_CONJUNTOS.csv`. Su gasto ya cuenta a nivel producto
    (invariante 1, `flujo.py`/`gasto.py` agregan por `coalesce(angulo_key, conjunto)`); lo único
    pendiente es la fila de registro, que da de alta ETAPA-6 — ver `lo_produce`."""

    cuenta_alias: str = ""
    campana: str = ""
    conjunto: str = ""
    producto_key: str = ""
    spend_usd: float = 0.0
    anuncios: int = 0
    lo_produce: str = ""


class ParametroMotor(Base):
    """Una fila de `_PARAMETROS_DECISION.csv`, tal cual: un reloj o umbral del motor de decisión."""

    parametro: str
    valor: str = ""
    unidad: str = ""
    dueno: str = ""
    por_que: str = ""


class OrdenesRespuesta(Base):
    schema_version: str = Field(alias="schema", default="")
    rezago_dias: int = 0
    capa_analitica: CapaAnalitica | None = None
    pendientes_registro: list[PendienteRegistro] = []
    llamadas: list[Any] = []
    ordenes: list[OrdenItem] = []
    bloqueantes: list[Any] = []
    avisos: list[str] = []
    # Los relojes del motor (ventana_dias, ventana_fatiga_dias, duracion_testeo_fase2_dias, …),
    # leídos tal cual de `_PARAMETROS_DECISION.csv`: la pantalla los explica, no los inventa.
    parametros_motor: list[ParametroMotor] = []


class GanadorPaso(Base):
    nodo: str = ""
    etapa: str = ""
    titulo: str = ""
    ejecutor: str = ""
    enlace: str = ""


class Ganador(Base):
    producto_key: str
    nombre: str = ""
    fase: str = ""
    nodo_actual: str = ""
    angulo_ganador: str = ""
    siguiente_paso: GanadorPaso

