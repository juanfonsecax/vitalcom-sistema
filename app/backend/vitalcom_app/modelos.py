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
    moneda: str = ""  # la de la CUENTA publicitaria (Meta cobra en ella), no la de venta
    # Mercado de venta (GT/CO) y de él la moneda y el símbolo en que el producto vende.
    mercado: str = ""
    moneda_local: str = ""
    simbolo: str = ""
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
    # Estado corto (de `_FLUJO.json`, sin una llamada por producto): lo que se lee de un vistazo.
    fase_titulo: str | None = None
    paso_titulo: str | None = None
    bloqueante_principal: str | None = None
    dueno_bloqueante: str | None = None


class Requisito(Base):
    dato: str = ""
    ok: bool = False
    observado: str = ""
    dueno: str = ""
    regla: str = ""
    falta: str | None = None  # el texto corto para el operador (FLUJO.json -> flujo.py)


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
    mercado: str = ""
    moneda_local: str = ""
    simbolo: str = ""
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


class Mercado(Base):
    """Perfil de un mercado (`_DIM_MERCADOS.csv` + tasa de `_PARAMETROS_FINANZAS.csv`)."""

    mercado: str
    pais: str = ""
    moneda: str = ""
    simbolo: str = ""
    persona: str = ""
    registro_sanitario: str = ""
    tasa_moneda_por_usd: float | None = None


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
    angulo_key: str | None = None
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


class FanPage(Base):
    pagina_num: str
    pagina_nombre: str
    identidad: str
    rol: str
    tono: str
    logica: str
    edad_orientacion: str
    page_id: str
    productos_nicho: str


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


class ReferenciaF1(Base):
    """La referencia `ligera` fija de FASE 1 elegida para el producto (una sola, para las 6
    fichas de ángulo) — `PRODUCTOS/_DIM_REFERENCIA_F1.csv`, dueño único `referencia_f1.py`."""

    archivo: str = ""
    url: str | None = None
    motivo: str = ""
    elegido_el: str = ""


class CampanaF1(Base):
    """El lanzador del producto (`_LANZADOR.json`) y el `_PLAN.json` de origen, tal cual."""

    producto_key: str
    lanzador: dict[str, Any] | None = None
    plan_fuente: dict[str, Any] | None = None
    piezas: list[PiezaF1] = []
    lanzador_generado: str | None = None
    referencia_f1: ReferenciaF1 | None = None
    comando_elegir_referencia_f1: str | None = None


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


class PackshotDeclarado(Base):
    """La foto del envase y su identidad física declarada (`_DIM_ENVASE.csv`), con la URL de media para verla."""

    archivo: str
    url: str | None = None
    marca_impresa: str = ""
    color_envase: str = ""
    color_hex: str = ""
    formato_envase: str = ""
    verificado_el: str = ""


class ItemDeDatos(Base):
    """Un dato que el producto necesita para arrancar: ok o falta, con la frase y la acción que lo carga."""

    clave: str
    rotulo: str
    estado: str
    detalle: str = ""
    como_resolver: str = ""
    accion: str | None = None


class DatosParaArrancar(Base):
    """`datos_producto.py`: qué le falta al producto para que el sistema trabaje con él."""

    producto_key: str
    ok: bool = True
    nombre: str = ""
    fase: str | None = None
    angulo_1: str | None = None
    completo: bool = False
    faltan: int = 0
    packshot: PackshotDeclarado | None = None
    items: list[ItemDeDatos] = []
    avisos: list[str] = []


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
    # Mercado del producto de la orden (resolver `Ads/_TOOLS/mercado.py`): el frontend formatea el
    # dinero con esto, nunca lo deduce del `producto_key`.
    mercado: str = ""
    moneda_local: str = ""
    simbolo: str = ""


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


class ObjetoAviso(Base):
    id: str = ""
    nombre: str = ""


class AvisoClaude(Base):
    """Algo que la app NO puede hacer sola (toda escritura en Meta va por el MCP en una sesión de
    Claude). Forma de `Ads/_TOOLS/requiere_claude.py`; `pedirle_a_claude` es la frase exacta que el
    operador pega."""

    codigo: str
    severidad: str
    motivo: str
    pedirle_a_claude: str
    objetos: list[ObjetoAviso] = []


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
    # «Necesita Claude»: conjuntos ciegos del control D+1 (`control_d1.py`). Vacío = la pantalla no
    # muestra nada.
    avisos_claude: list[AvisoClaude] = []


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
    mercado: str = ""
    moneda_local: str = ""
    simbolo: str = ""


class GenerarPrompts(Base):
    """El botón «Generar los prompts de este ángulo»: la acción del manifiesto con sus parámetros, si se
    puede pedir ahora y, si no, qué dato lo frena (de `datos_producto.py`, sin repetir sus chequeos).
    `habilitada` es solo del #1 (el ángulo que está en FASE 2 ahora); el resto se genera cuando le toque."""

    accion_id: str
    parametros: dict[str, str] = {}
    habilitada: bool = False
    motivo: str = ""
    listo: bool = False
    faltan: list[ItemDeDatos] = []
    # Acción del manifiesto que prepara el perfil creativo (concepto), solo si está habilitada; si no, va None
    # y el perfil lo prepara Claude en la sesión.
    accion_perfil: str | None = None
    aviso: str = ""


class PasoChecklist(Base):
    """Un paso del checklist de un ángulo en FASE 2 (`contratos._checklist_angulo`)."""

    clave: str
    rotulo: str
    cumplido: bool = False
    detalle: str = ""


class CampanaFase2(Base):
    """Una campaña de conceptos de FASE 2 (brazo A/B de `_PARAMETROS_PUBLICACION.csv`)."""

    brazo: str
    conceptos: int


class FabricarConceptos(Base):
    """El botón «Generar los conceptos que faltan (N)» de un ángulo ganador (`contratos._fabricar`)."""

    accion_id: str
    parametros: dict[str, str] = {}
    faltan: int = 0
    habilitada: bool = False
    trabajo_en_curso: str | None = None


class MarcarGenerados(Base):
    """El botón «Marcar como generadas las imágenes que ya subiste» de un ángulo (`contratos._marcar`)."""

    accion_id: str
    parametros: dict[str, str] = {}
    listos: int = 0
    habilitada: bool = False


class PublicacionFase2(Base):
    """El botón «Ya publiqué la campaña — verificar» de un brazo de FASE 2 que ya tiene su paquete de
    publicación (`contratos._publicaciones_fase2`)."""

    brazo: str
    accion_id: str
    parametros: dict[str, str] = {}
    habilitada: bool = False


class AnguloFase2(Base):
    """Un ángulo que el producto testeó en FASE 1, con su rol en FASE 2 y el veredicto del motor
    (`decidir.py`) pasado tal cual. Ver `contratos.angulos_de_fase2`."""

    angulo_key: str
    rol: str = "midiendo"  # ganador_activo | ganador_en_fila | perdedor | midiendo
    posicion: int | None = None
    etiqueta: str = ""
    estado_angulo: str = ""
    dias_sin_gasto: int | None = None
    ultimo_dia_gasto: str = ""
    estado: str | None = None
    accion_codigo: str | None = None
    accion_sugerida: str | None = None
    ventas: float | None = None
    ventas_acum: float | None = None
    cpa_real_q: float | None = None
    ic: list[float] | None = None
    cierre_pct: float | None = None
    spend_q: float | None = None
    spend_acum_q: float | None = None
    nivel_prioridad: int | None = None
    faltan_ventas: float | None = None
    ejecutable: bool | None = None
    bloqueo_fase: str | None = None
    generar: GenerarPrompts | None = None
    # CPA contra break-even (`_ESTADO_ANGULOS.csv`); el semáforo lo decide el backend
    # ("verde" | "ambar" | "rojo" | "" sin dato), la pantalla solo pinta.
    cpa_acum_q: float | None = None
    cpa_ventana_q: float | None = None
    cpa_be_q: float | None = None
    semaforo_acum: str = ""
    semaforo_ventana: str = ""
    orden_motor: str = ""
    conceptos_listos: int = 0
    fabricar: FabricarConceptos | None = None
    marcar: MarcarGenerados | None = None
    checklist: list[PasoChecklist] = []


class ConceptoFase2(Base):
    """Un concepto de la galería de FASE 2. El prompt es el REAL de `armar_prompts_fase2.py`
    (`prompt_origen="paquete"`) o None con `comando_generar` cuando todavía no existe — nunca
    un prompt inventado (ver `contratos.resolver_prompt_fase2`)."""

    creativo_id: str = ""
    archivo: str = ""
    canonico_id: str = ""
    angulo_key: str = ""
    blueprint_nombre: str = ""
    dispositivo: str = ""
    cuando_elegirlo: str = ""
    rol_embudo: str = ""
    estado: str = ""
    ad_id: str = ""
    archivo_existe: bool = False
    archivo_version: str = ""  # mtime del archivo en disco; cambia al re-subir y rompe la caché de la miniatura
    formato: str = ""  # IMAGEN | VIDEO
    puede_subir: bool = False  # IMAGEN no publicada y la acción de carga habilitada
    notas: str = ""
    prompt: str | None = None
    prompt_origen: str = "pendiente"
    referencia_url: str | None = None
    comando_generar: str | None = None
    numero: int = 0  # posición dentro de su ángulo (1-based)
    campana: str = ""  # "A" | "B" según `_PARAMETROS_PUBLICACION.csv`


class FatigaFase2(Base):
    ordenes: list[dict[str, Any]] = []
    angulos_probados: list[str] = []
    puede_reingresar: bool = True


class ReingresoActivo(Base):
    """`flujo.py`: un reingreso a F1 activo (evento REINGRESO_F1/FATIGA_ANGULO sin lanzamiento
    posterior), tal cual lo arma `flujo.py:reingreso_activo`."""

    desde: str = ""
    a: str = ""
    fecha: str = ""
    motivo: str = ""
    regla: str = ""
    angulos_excluidos: list[str] = []


class Fase2Detalle(Base):
    """`contratos.fase2_detalle`: todos los ángulos con su rol, 10 conceptos con prompt real y las
    órdenes del motor. `angulo_ganador` es el `angulo_key` del #1 (vacío si aún no hay ganador)."""

    producto_key: str
    mercado: str = ""
    moneda_local: str = ""
    simbolo: str = ""
    fase: str = ""
    nodo_actual: str = ""
    angulo_ganador: str = ""
    angulos: list[AnguloFase2] = []
    conceptos: list[ConceptoFase2] = []
    total_conceptos: int = 0
    conceptos_requeridos: int = 0
    campanas: list[CampanaFase2] = []
    publicaciones: list[PublicacionFase2] = []
    conceptos_generados: int = 0
    conceptos_requeridos_total: int = 0
    conceptos_faltan: int = 0
    fase_validada: bool = False
    ejecutor: str = ""
    fase_titulo: str | None = None
    paso_titulo: str | None = None
    bloqueante_principal: str | None = None
    dueno_bloqueante: str | None = None
    reingreso_activo: ReingresoActivo | None = None
    fatiga: FatigaFase2 | None = None


class EventoCambioBot(Base):
    """Una fila de `_EVENTOS.csv` con evento CAMBIO_BOT o EXCEPCION_CAMBIO_BOT."""

    evento: str = ""
    fecha: str = ""
    motivo: str = ""


class CierrePostCambioBot(Base):
    """`Ads/_TOOLS/flujo.py:medir_cierre_post_cambio_bot` — el gate duro F3→F4
    (PROHIBIDO_ESCALAR_CIERRE_BAJO): mensajes/ventas/cierre% desde el último CAMBIO_BOT (o
    EXCEPCION_CAMBIO_BOT) vigente, los umbrales que se le exigen y el benchmark 15-20% de
    referencia (nunca gate). Estos campos SON el cálculo del motor, pasados tal cual — la app
    nunca los deriva de nuevo."""

    fecha_cambio_bot: str | None = None
    mensajes: float | None = None
    ventas: float | None = None
    cierre_pct: float | None = None
    min_mensajes: float | None = None
    min_cierre_pct: float | None = None
    cierre_meta_min_pct: float | None = None
    cierre_meta_max_pct: float | None = None
    ok: bool = False
    explicacion: str = ""


class Fase3Detalle(Base):
    """`contratos.fase3_detalle`: FASE 3, optimización del flujo LucidBot hacia el ángulo+concepto
    ganador. Gate de entrada (el de siempre, concepto 2de2), los dos nodos de la fase
    (`F3.reescribir`/`F3.medir_cierre`), los eventos CAMBIO_BOT registrados y el gate duro de
    salida hacia FASE 4 (`gate_f4`), calculado por el motor."""

    producto_key: str
    fase: str = ""
    nodo_actual: str = ""
    entrada: Requisito
    nodo_reescribir: Nodo | None = None
    nodo_medir_cierre: Nodo | None = None
    eventos_cambio_bot: list[EventoCambioBot] = []
    gate_f4: CierrePostCambioBot | None = None
    entrada_f4: Requisito


class PlanCbo(Base):
    estructura: str = ""
    descripcion: str = ""
    tiene_plan: bool = False
    estado: str = ""
    archivo: str | None = None


class ExpansionEscalado(Base):
    post_id: bool = False
    cuenta_primaria: str = ""
    cuentas_activas: list[str] = []
    page_id: str = ""


class FatigaEscalado(Base):
    angulos_probados: list[str] = []
    puede_reingresar: bool = True


class Fase4Detalle(Base):
    """`contratos.fase4_detalle` (ex-`fase3_detalle` antes de las cuatro fases, B3): FASE 4,
    escalado. Gate de entrada 2de2+CAMBIO_BOT+cierre (`flujo.py:F4.entrada`), plan CBO 1-1-7 y
    expansión multicuenta."""

    producto_key: str
    fase: str = ""
    nodo_actual: str = ""
    gate_2de2: Requisito
    plan_cbo: PlanCbo
    expansion: ExpansionEscalado
    fatiga: FatigaEscalado



# ── Resultados mes a mes por mercado (`gen_pl_mensual.py --json`) ─────────────────────────────
# La forma la fija el script; los números llegan tal cual (la app no calcula). Todo monto de Dropi
# viaja en la moneda del mercado y el del banco en dólares, como el script los dice.


class PautaDelMes(Base):
    usd: float = 0.0
    q: float = 0.0
    meta_usd: float = 0.0
    lucidsales_fallback_usd: float = 0.0
    tasa: float = 0.0


class ConversionDelMes(Base):
    """La tasa USD -> moneda local con la que el script convirtió la pauta y los gastos del mes, y la
    regla que la dio (VENTANA | ULTIMA_CONOCIDA | PRIMERA_POSTERIOR | PARAMETRO). `costo_q` es informativo: ya está
    dentro de la publicidad."""

    tasa: float = 0.0
    regla: str = "PARAMETRO"
    tasa_parametro: float = 0.0
    transferencias: int = 0
    usd: float = 0.0
    q: float = 0.0
    desde: str | None = None
    hasta: str | None = None
    ventana_dias: int = 90
    costo_q: float = 0.0


class BancoFacebook(Base):
    usd: float | None = None
    cargos: int | None = None


class DetalleDeGasto(Base):
    nombre: str
    monto_usd: float
    monto_q: float
    categoria: str = ""
    mercado: str = ""
    parte: float = 1.0


class GastosDelMes(Base):
    q: float | None = None
    detalle: list[DetalleDeGasto] = []


class OrdenesDelMes(Base):
    total: int = 0
    entregadas: int = 0
    devueltas: int = 0
    en_transito: int = 0
    pct_resuelto: float | None = None


class ProductoDelMes(Base):
    producto_key: str
    ordenes: int = 0
    entregadas: int = 0
    devueltas: int = 0
    en_transito: int = 0
    venta_entregada_q: float | None = None
    margen_antes_publicidad_q: float | None = None
    pauta_q: float = 0.0
    ganancia_q: float | None = None


class RetiroDeCartera(Base):
    """Un retiro de la billetera de Dropi, con el destino que le da `_DIM_RETIROS.csv`."""

    fecha: str
    hora: str = ""
    concepto: str = ""
    monto_q: float
    clasificacion: str  # RETIRO_PERSONAL | TRANSFERENCIA_PROPIA | SIN_CLASIFICAR


class DevolucionesDelMes(Base):
    """De dónde sale el costo de las devoluciones: cobros reales de la billetera o el promedio."""

    origen: str | None = None  # REAL | MIXTO | ESTIMADO; null si el mes no tiene devoluciones
    reales: int = 0
    estimadas: int = 0


class CarteraDelMes(Base):
    """La billetera de Dropi en el mes. Son movimientos de caja: NO afectan la ganancia. Un rubro
    `null` es un dato que la cartera cargada no cubre, nunca un cero."""

    cubre_mes: bool = False
    saldo_cierre_q: float | None = None
    fecha_corte: str | None = None
    retiros_personales_q: float | None = None
    transferencias_propias_q: float | None = None
    sin_clasificar_q: float | None = None
    retiros: list[RetiroDeCartera] = []
    devoluciones: DevolucionesDelMes = DevolucionesDelMes()


class MesDelPL(Base):
    """Un mes del estado de resultados. Una línea en `null` es un dato que no se pudo medir (el mes
    no tiene órdenes de Dropi), nunca un cero: el porqué está en `faltantes`."""

    mes: str
    desde: str
    hasta: str
    preliminar: bool | None = None
    edad_dias: int | None = None
    dias_maduro_umbral: int = 10
    ordenes: OrdenesDelMes = OrdenesDelMes()
    venta_entregada_q: float | None = None
    costo_producto_q: float | None = None
    flete_q: float | None = None
    margen_logistico_q: float | None = None
    devoluciones_q: float | None = None
    personal_q: float | None = None
    otros_q: float | None = None
    costos_operativos_q: float | None = None  # producto + flete + devoluciones + personal + otros
    margen_contribucion_q: float | None = None
    publicidad: PautaDelMes = PautaDelMes()
    conversion: ConversionDelMes = ConversionDelMes()
    margen_operativo_q: float | None = None
    banco_facebook: BancoFacebook = BancoFacebook()
    gastos_fijos: GastosDelMes = GastosDelMes()
    retiros_personales: GastosDelMes = GastosDelMes()
    cargos_sin_clasificar: list[dict[str, Any]] = []
    cartera: CarteraDelMes = CarteraDelMes()
    resultado_neto_q: float | None = None
    por_producto: list[ProductoDelMes] = []
    faltantes: list[str] = []


class ResultadoMensual(Base):
    """Salida de `gen_pl_mensual.py --json`: el P&L de cada mes de un mercado y lo que le falta."""

    mercado: str
    moneda: str = ""
    generado: str = ""
    meses: list[MesDelPL] = []
    faltantes: list[str] = []
    cobertura: dict[str, Any] = {}
