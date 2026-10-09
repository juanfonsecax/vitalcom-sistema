"""trabajos.py — lo que se sabe de un trabajo y lo que el operador puede hacerle (diseño §3.6, §3.7, §3.10).

Es la cara de LECTURA del runner: arma el estado que ve la pantalla a partir de DBOS (estado, eventos
publicados por el workflow) y de la bitácora (el sello y el resultado). Las cosas que sí hacen
algo —aprobar, responder, avisar que subió las imágenes, reintentar, cancelar— entregan al runner una decisión del operador; no
ejecutan nada por su cuenta.

Estados que ve el operador: ENCOLADO · CORRIENDO · ESPERA_APROBACION · ESPERA_RESPUESTA · ESPERA_MEDIA · EXITO ·
SIN_CUMPLIR · RECHAZADO · CADUCADO · FALLIDO · INTERRUMPIDO · CSV_INVALIDO · CANCELADO · OTRA_VERSION.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dbos import DBOS

from . import acciones, bitacora, workflows
from .acciones import ErrorDeAccion

ESTADOS_QUE_SE_REINTENTAN = ("FALLIDO", "INTERRUMPIDO", "CADUCADO")
ESTADOS_EN_CURSO = ("ENCOLADO", "CORRIENDO", "ESPERA_APROBACION", "ESPERA_RESPUESTA", "ESPERA_MEDIA")
MAXIMO_A_LISTAR = 200


def _iso(milisegundos: int | None) -> str | None:
    if not milisegundos:
        return None
    return datetime.fromtimestamp(milisegundos / 1000).astimezone().isoformat(timespec="seconds")


def _argumentos(estado_dbos: Any) -> list[Any]:
    entrada = getattr(estado_dbos, "input", None) or {}
    argumentos = entrada.get("args") if isinstance(entrada, dict) else getattr(entrada, "args", None)
    return list(argumentos or [])


def _resultado_de(estado_dbos: Any) -> dict[str, Any] | None:
    salida = getattr(estado_dbos, "output", None)
    return salida if isinstance(salida, dict) else None


def estado_visible(estado_dbos: Any, publicado: dict[str, Any] | None) -> str:
    """El estado que ve el operador: sale de DBOS y de lo que el workflow publicó."""
    situacion = estado_dbos.status
    if situacion == "ENQUEUED":
        return "ENCOLADO"
    if situacion == "PENDING":
        if estado_dbos.app_version != workflows.APP_VERSION:
            return "OTRA_VERSION"
        return (publicado or {}).get("estado", "CORRIENDO")
    if situacion == "SUCCESS":
        return (_resultado_de(estado_dbos) or {}).get("estado", "EXITO")
    if situacion == "CANCELLED":
        return "CANCELADO"
    return "FALLIDO"


def _rotulo(accion_id: str) -> str:
    try:
        return acciones.por_id_para_el_runner(accion_id)["rotulo"]
    except ErrorDeAccion:
        return accion_id


def _resumen(estado_dbos: Any) -> dict[str, Any]:
    argumentos = _argumentos(estado_dbos)
    accion_id = argumentos[1] if len(argumentos) > 1 else ""
    parametros = argumentos[2] if len(argumentos) > 2 and isinstance(argumentos[2], dict) else {}
    publicado = workflows.publicado(estado_dbos.workflow_id, "estado") if estado_dbos.status == "PENDING" else None
    pendiente = workflows.publicado(estado_dbos.workflow_id, "pendiente") if estado_dbos.status == "PENDING" else None
    estado = estado_visible(estado_dbos, publicado)
    return {
        "job_id": estado_dbos.workflow_id, "accion_id": accion_id, "rotulo": _rotulo(accion_id),
        "producto_key": parametros.get("producto_key"), "angulo_key": parametros.get("angulo_key"),
        "estado": estado,
        "iniciado": _iso(estado_dbos.created_at),
        "terminado": _iso(estado_dbos.completed_at or estado_dbos.updated_at) if estado not in ESTADOS_EN_CURSO else None,
        "app_version": estado_dbos.app_version, "otra_version": estado == "OTRA_VERSION",
        "pendiente": (pendiente or {}).get("tipo"),
    }


def listar(estado: str | None = None, producto_key: str | None = None, limite: int = 50) -> list[dict[str, Any]]:
    """Los trabajos, los más nuevos primero. Solo los padres: cada unidad de escritura es un detalle."""
    encontrados = DBOS.list_workflows(
        queue_name=workflows.COLA_TRABAJOS, sort_desc=True, limit=MAXIMO_A_LISTAR, load_output=True, load_input=True)
    filas = [_resumen(e) for e in encontrados]
    if estado:
        filas = [f for f in filas if f["estado"] == estado]
    if producto_key:
        filas = [f for f in filas if f["producto_key"] == producto_key]
    return filas[:limite]


def _existente(job_id: str) -> Any:
    encontrados = DBOS.list_workflows(workflow_ids=[job_id])
    if not encontrados:
        raise ErrorDeAccion(404, "TRABAJO_NO_EXISTE", f"No hay ningún trabajo «{job_id}».")
    return encontrados[0]


def detalle(job_id: str) -> dict[str, Any]:
    """El resumen + el sello, lo pendiente completo (la orden o la pregunta) y el resultado."""
    estado_dbos = _existente(job_id)
    resumen = _resumen(estado_dbos)
    carpeta = bitacora.buscar_corrida(job_id)
    trabajo = bitacora.leer_trabajo(carpeta) if carpeta else None
    resultado = _resultado_de(estado_dbos) or (trabajo or {}).get("resultado")
    pendiente = workflows.publicado(job_id, "pendiente") if estado_dbos.status == "PENDING" else None
    sello = (trabajo or {}).get("sello") or {}
    argumentos = _argumentos(estado_dbos)
    return {
        **resumen,
        "parametros": argumentos[2] if len(argumentos) > 2 and isinstance(argumentos[2], dict) else {},
        "sello": {clave: sello.get(clave) for clave in ("hoy", "iniciado", "manifiesto_sha", "app_version", "argv", "ejecutor")},
        "pendiente_completo": pendiente,
        "unidades": (resultado or {}).get("unidades", []),
        "resultado": resultado,
        "run_dir": bitacora.ruta_relativa(carpeta) if carpeta else None,
        "error": getattr(estado_dbos, "error", None) if resumen["estado"] == "FALLIDO" else None,
    }


# ── lo que el operador decide ─────────────────────────────────────────────────

def aprobar(job_id: str, orden_id: int, decision: str, huella: str, nota: str = "") -> None:
    """Aprueba o rechaza UNA orden. La huella es la de lo que la pantalla mostró: si no coincide, no se envía."""
    if decision not in ("APROBADA", "RECHAZADA"):
        raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "La decisión es APROBADA o RECHAZADA.", campo="decision")
    _existente(job_id)
    pendiente = workflows.publicado(job_id, "pendiente")
    if not pendiente or pendiente.get("tipo") != "aprobacion" or pendiente.get("orden_id") != orden_id:
        raise ErrorDeAccion(409, "NO_ESPERA_ESA_ORDEN", "Este trabajo no está esperando la aprobación de esa orden.")
    if pendiente.get("hash") != huella:
        raise ErrorDeAccion(409, "HASH_DISTINTO",
                            "La orden cambió desde que la viste: volvé a abrirla y revisala antes de aprobar.")
    workflows.enviar_aprobacion(job_id, orden_id, decision, huella, nota)


def responder(job_id: str, n: int, texto: str) -> None:
    _existente(job_id)
    pendiente = workflows.publicado(job_id, "pendiente")
    if not pendiente or pendiente.get("tipo") != "pregunta" or pendiente.get("n") != n:
        raise ErrorDeAccion(409, "NO_ESPERA_ESA_RESPUESTA", "Este trabajo no está esperando esa respuesta.")
    if not texto.strip():
        raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "La respuesta está vacía.", campo="texto")
    workflows.responder(job_id, n, texto.strip())


def avisar_media_subida(job_id: str, vuelta: int) -> None:
    """El operador dice que ya subió las imágenes a la biblioteca de Meta. El runner lo verifica leyéndola."""
    _existente(job_id)
    pendiente = workflows.publicado(job_id, "pendiente")
    if not pendiente or pendiente.get("tipo") != "subida_media" or pendiente.get("vuelta") != vuelta:
        raise ErrorDeAccion(409, "NO_ESPERA_IMAGENES", "Este trabajo no está esperando que subas imágenes.")
    workflows.avisar_media_subida(job_id, vuelta)


def cancelar(job_id: str) -> str:
    """Corta el subproceso vivo, cancela el trabajo y deja que `tras_escribir` corra igual."""
    estado_dbos = _existente(job_id)
    if estado_visible(estado_dbos, workflows.publicado(job_id, "estado")) not in (*ESTADOS_EN_CURSO, "OTRA_VERSION"):
        raise ErrorDeAccion(409, "YA_TERMINO", "Ese trabajo ya terminó: no hay nada que cancelar.")
    workflows.cancelar(job_id)
    carpeta = bitacora.buscar_corrida(job_id)
    if carpeta:
        previo = bitacora.leer_trabajo(carpeta) or {}
        bitacora.reescribir_trabajo(carpeta, {**previo, "estado": "CANCELADO"})
        workflows.limpiar_tras_cancelar(job_id, bitacora.ruta_relativa(carpeta))
    return "CANCELADO"


def reintentar(job_id: str, confirmado: bool) -> dict[str, Any]:
    """Un trabajo NUEVO con los mismos parámetros (invariante 5).

    No se hereda ni el sello ni una aprobación: lo aprobado ayer no vale hoy. Pasa por las mismas
    puertas que un pedido normal (confirmación, nodo listo, sesión de Claude). Una acción con
    `pasos` (Armar FASE 1) RETOMA: hereda los pasos que terminaron bien si los insumos no cambiaron
    (lo decide `workflows.paso_preparar_pasos`, no esta función).
    """
    estado_dbos = _existente(job_id)
    estado = estado_visible(estado_dbos, None)
    if estado not in ESTADOS_QUE_SE_REINTENTAN:
        raise ErrorDeAccion(409, "NO_SE_REINTENTA", f"Un trabajo en estado {estado} no se reintenta.")
    argumentos = _argumentos(estado_dbos)
    accion_id, parametros = argumentos[1], argumentos[2]
    try:
        con_pasos = bool(acciones.por_id_para_el_runner(accion_id).get("pasos"))
    except ErrorDeAccion:
        con_pasos = False
    return {"accion_id": accion_id, "parametros": parametros, "confirmado": confirmado,
            "retomar_de": job_id if con_pasos else None}


def descartar_otra_version(job_id: str) -> str:
    """«Marcar fallido»: un trabajo de una versión vieja del runner ya no es el mismo código; no se continúa."""
    estado_dbos = _existente(job_id)
    if estado_visible(estado_dbos, None) != "OTRA_VERSION":
        raise ErrorDeAccion(409, "NO_ES_DE_OTRA_VERSION", "Ese trabajo es de esta versión de la app.")
    DBOS.cancel_workflow(job_id, cancel_children=True)
    return "CANCELADO"

