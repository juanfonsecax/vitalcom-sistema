"""api_fases.py — endpoints para FASE 2, FASE 3 y el ciclo de fatiga / reingreso."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import contratos

router = APIRouter(prefix="/api/productos", tags=["fases"])


class ReingresoPeticion(BaseModel):
    motivo: str = Field(default="Ángulo agotado / fatiga", description="Motivo del retorno a F1")


@router.get("/{producto_key}/fase2")
def obtener_fase2(producto_key: str) -> dict[str, Any]:
    """Detalle completo de FASE 2: ángulo ganador, 10 conceptos con blueprints, prompts y carriles."""
    try:
        return contratos.fase2_detalle(producto_key)
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{producto_key}/fase3")
def obtener_fase3(producto_key: str) -> dict[str, Any]:
    """Detalle completo de FASE 3: gate 2de2 con evidencia, plan CBO 1-1-7 y expansión multicuenta."""
    try:
        return contratos.fase3_detalle(producto_key)
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
