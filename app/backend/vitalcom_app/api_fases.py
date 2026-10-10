"""api_fases.py — endpoints para FASE 2, FASE 3, FASE 4 y el ciclo de fatiga / reingreso."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import contratos
from .api_fase1 import ejecutar_con_archivo
from .modelos import Fase2Detalle, Fase3Detalle, Fase4Detalle

router = APIRouter(prefix="/api/productos", tags=["fases"])
router_swipe = APIRouter(prefix="/api/swipe", tags=["fases"])


class ReingresoPeticion(BaseModel):
    motivo: str = Field(default="Ángulo agotado / fatiga", description="Motivo del retorno a F1")


@router.get("/{producto_key}/fase2", response_model=Fase2Detalle)
def obtener_fase2(producto_key: str) -> Fase2Detalle:
    """Detalle completo de FASE 2: ángulo ganador, 10 conceptos con blueprints, prompts y carriles."""
    try:
        return Fase2Detalle(**contratos.fase2_detalle(producto_key), **contratos.perfil_de_producto(producto_key))
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/{producto_key}/conceptos/{creativo_id}/imagen")
def subir_imagen_de_concepto(producto_key: str, creativo_id: str, archivo: UploadFile = File(...)) -> dict[str, Any]:
    """La imagen que el operador renderizó a mano para UN concepto: la acción del manifiesto la deja con
    el nombre de su fila y la marca GENERADO. Un video o un concepto publicado se rechazan acá, antes de correr."""
    fila = next((r for r in contratos._leer_csv(("PRODUCTOS", "_DIM_CREATIVOS.csv"))
                 if r.get("producto_key") == producto_key and r.get("creativo_id") == creativo_id), None)
    if fila is None:
        raise HTTPException(status_code=404, detail=f"«{creativo_id}» no es un concepto de {producto_key}.")
    if (fila.get("formato") or "").strip().upper() != "IMAGEN":
        raise HTTPException(status_code=422, detail=f"«{creativo_id}» no es una imagen: el video no se carga desde acá.")
    if (fila.get("estado") or "").strip() not in contratos._ESTADOS_QUE_ADMITEN_IMAGEN:
        raise HTTPException(status_code=422, detail=f"«{creativo_id}» ya está publicado: su imagen no se pisa.")
    return ejecutar_con_archivo(contratos.ACCION_SUBIR_IMAGEN,
                                {"producto_key": producto_key, "creativo_id": creativo_id}, archivo)


@router_swipe.get("/{ruta_imagen:path}", response_class=FileResponse)
def swipe_imagen(ruta_imagen: str) -> FileResponse:
    """Una imagen de referencia del banco de swipe (`Ads/_SWIPE/`), para la galería de FASE 2 y
    FASE 1. Nunca sale de esa carpeta (path traversal, ruta absoluta o extensión ajena → 404)."""
    encontrado = contratos.ruta_de_swipe(ruta_imagen)
    if encontrado is None:
        raise HTTPException(status_code=404, detail=f"«{ruta_imagen}» no está en Ads/_SWIPE/.")
    return FileResponse(encontrado)


@router.get("/{producto_key}/fase3", response_model=Fase3Detalle)
def obtener_fase3(producto_key: str) -> Fase3Detalle:
    """Detalle completo de FASE 3 (optimización del flujo LucidBot): gate de entrada, estado de
    F3.reescribir/F3.medir_cierre, eventos CAMBIO_BOT y el gate duro de salida hacia FASE 4."""
    try:
        return Fase3Detalle(**contratos.fase3_detalle(producto_key))
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{producto_key}/fase4", response_model=Fase4Detalle)
def obtener_fase4(producto_key: str) -> Fase4Detalle:
    """Detalle completo de FASE 4 (escalado): gate 2de2+CAMBIO_BOT+cierre, plan CBO 1-1-7 y
    expansión multicuenta. Ex-`/fase3`, renombrada B3 (28-sep-2026, cuatro fases)."""
    try:
        return Fase4Detalle(**contratos.fase4_detalle(producto_key))
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/{producto_key}/reingreso-f1")
def post_reingreso_f1(producto_key: str, cuerpo: ReingresoPeticion | None = None) -> dict[str, Any]:
    """Registra el retorno a F1 por fatiga, excluyendo los ángulos ya probados."""
    motivo = cuerpo.motivo if cuerpo else "Ángulo agotado / fatiga"
    try:
        res = contratos.reingreso_f1(producto_key, motivo=motivo)
        if not res.get("ok"):
            raise HTTPException(status_code=422, detail=res.get("error", "Fallo al registrar reingreso"))
        return res
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
