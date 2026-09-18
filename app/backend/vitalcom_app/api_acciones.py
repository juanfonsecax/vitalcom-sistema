"""api_acciones.py — `GET/POST /api/acciones`: lo que la pantalla puede pedir.

Cada respuesta de error lleva `{"detail": <frase para el operador>, "codigo": <código>}`
(diseño §2.5). La validación corre en el orden de la tabla del diseño: la primera que falla corta.
"""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter

from . import acciones, workflows
from .acciones import ErrorDeAccion
from .modelos import Accion, AccionEncolada, PedidoAccion

router = APIRouter(prefix="/api/acciones", tags=["acciones"])

_JOB_ID = re.compile(r"^[0-9a-f]{32}$")


@router.get("", response_model=list[Accion])
def listar_acciones(nodo: str | None = None, producto_key: str | None = None) -> list[Accion]:
    """Las acciones con botón. Con `producto_key`, cada una dice si está disponible ahora."""
    return [Accion(**fila) for fila in acciones.listar(nodo=nodo, producto_key=producto_key)]


def validar_pedido(accion_id: str, pedido: PedidoAccion) -> tuple[dict, dict]:
    """Los pasos 1-9 del contrato. Devuelve (acción, parámetros validados) o levanta el error."""
    accion = acciones.buscar(accion_id)                                   # 1, 2, 3
    if not accion.get("habilitada"):                                      # 4
        raise ErrorDeAccion(409, "ACCION_DESHABILITADA",
                            "Esta acción todavía no está habilitada.", motivo=accion.get("motivo"))
    if accion["ejecutor_tipo"] == "operador":                             # 5
        raise ErrorDeAccion(409, "ES_DEL_OPERADOR",
                            "Este paso lo hace el operador: la app solo puede ayudar a cargar cada dato.",
                            datos_del_operador=accion.get("datos_del_operador") or [])
    if pedido.job_id is not None and not _JOB_ID.fullmatch(pedido.job_id):
        raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "«job_id» tiene que ser 32 caracteres hexadecimales.",
                            campo="job_id")
    valores = acciones.validar_parametros(accion, pedido.parametros)      # 6
    if accion.get("requiere_confirmacion") and pedido.confirmado is not True:   # 7
        raise ErrorDeAccion(428, "FALTA_CONFIRMACION",
                            "Falta tu confirmación: esta acción cambia archivos del sistema.",
                            escribe=accion.get("escribe", []), tiempo_max_s=accion.get("tiempo_max_s"),
                            toca_meta=accion.get("toca_meta"))
    acciones.exigir_nodo_listo(accion, valores)                           # 9 (el 8, Claude, llega con claude.py)
    return accion, valores


@router.post("/{accion_id}", status_code=202, response_model=AccionEncolada)
def pedir_accion(accion_id: str, pedido: PedidoAccion) -> AccionEncolada:
    """Pide una acción declarada. 202 con el `job_id`; el progreso va por `/api/trabajos/{id}`."""
    accion, valores = validar_pedido(accion_id, pedido)
    job_id, repetido = workflows.encolar(accion, valores, pedido.job_id or uuid.uuid4().hex)
    return AccionEncolada(
        job_id=job_id, accion_id=accion["id"], estado="ENCOLADO", repetido=repetido,
        url_estado=f"/api/trabajos/{job_id}", url_eventos=f"/api/trabajos/{job_id}/eventos",
    )
