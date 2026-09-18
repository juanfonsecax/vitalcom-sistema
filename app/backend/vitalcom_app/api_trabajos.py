"""api_trabajos.py — los trabajos del runner: ver, seguir en vivo, aprobar, responder, reintentar, cancelar.

Todo lo que cambia algo es una DECISIÓN del operador que se le entrega al runner; ninguno de estos
endpoints ejecuta un comando. La lectura sale de DBOS y de la bitácora (`trabajos.py`).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from . import api_acciones, claude, sse, trabajos, workflows
from .modelos import (
    AccionEncolada, DecisionDeOrden, EstadoDeClaude, PedidoAccion, Reintento, RespuestaDeClaude, Trabajo,
    TrabajoDetalle,
)

router = APIRouter(prefix="/api/trabajos", tags=["trabajos"])
router_claude = APIRouter(prefix="/api/claude", tags=["trabajos"])


@router.get("", response_model=list[Trabajo])
def listar_trabajos(estado: str | None = None, producto_key: str | None = None, limite: int = 50) -> list[Trabajo]:
    """Los trabajos, los más nuevos primero. Un pendiente de otra versión sale como `OTRA_VERSION`."""
    return [Trabajo(**fila) for fila in trabajos.listar(estado, producto_key, limite)]


@router.get("/{job_id}", response_model=TrabajoDetalle)
def ver_trabajo(job_id: str) -> TrabajoDetalle:
    return TrabajoDetalle(**trabajos.detalle(job_id))


@router.get("/{job_id}/eventos", response_class=StreamingResponse)
def seguir_trabajo(job_id: str, request: Request) -> StreamingResponse:
    """El progreso en vivo (SSE). Con `Last-Event-ID` sigue desde donde quedó el navegador."""
    trabajos._existente(job_id)  # un 404 tiene que ser un 404, no una conexión que se cierra sola
    return StreamingResponse(
        sse.generar(job_id, request.headers.get("last-event-id")), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{job_id}/aprobaciones/{orden_id}", status_code=202)
def decidir_orden(job_id: str, orden_id: int, decision: DecisionDeOrden) -> dict:
    """Aprueba o rechaza UNA orden. La huella tiene que ser la de lo que la pantalla mostró."""
    trabajos.aprobar(job_id, orden_id, decision.decision, decision.hash, decision.nota)
    return {"job_id": job_id, "orden_id": orden_id, "decision": decision.decision}


@router.post("/{job_id}/respuesta", status_code=202)
def responder_a_claude(job_id: str, respuesta: RespuestaDeClaude) -> dict:
    trabajos.responder(job_id, respuesta.n, respuesta.texto)
    return {"job_id": job_id, "n": respuesta.n}


@router.post("/{job_id}/reintentar", status_code=202, response_model=AccionEncolada)
def reintentar_trabajo(job_id: str, cuerpo: Reintento | None = None) -> AccionEncolada:
    """Un trabajo NUEVO con los mismos parámetros y corrida completa. Pasa por las mismas puertas que un pedido."""
    pedido = trabajos.reintentar(job_id, bool(cuerpo and cuerpo.confirmado))
    accion, valores = api_acciones.validar_pedido(
        pedido["accion_id"], PedidoAccion(parametros=pedido["parametros"], confirmado=pedido["confirmado"]))
    nuevo, _repetido = workflows.encolar(accion, valores, uuid.uuid4().hex)
    return AccionEncolada(
        job_id=nuevo, accion_id=accion["id"], estado="ENCOLADO",
        url_estado=f"/api/trabajos/{nuevo}", url_eventos=f"/api/trabajos/{nuevo}/eventos",
    )


@router.post("/{job_id}/cancelar")
def cancelar_trabajo(job_id: str) -> dict:
    return {"job_id": job_id, "estado": trabajos.cancelar(job_id)}


@router.post("/{job_id}/descartar")
def descartar_trabajo_de_otra_version(job_id: str) -> dict:
    """«Marcar fallido»: un trabajo de una versión vieja del runner no se continúa."""
    return {"job_id": job_id, "estado": trabajos.descartar_otra_version(job_id)}


@router_claude.get("/estado", response_model=EstadoDeClaude)
def estado_de_claude() -> EstadoDeClaude:
    """¿Hay sesión de Claude? La pantalla lo mira antes de ofrecer un botón que lo necesite."""
    return EstadoDeClaude(**claude.estado_sesion())
