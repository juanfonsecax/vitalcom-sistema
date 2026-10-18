"""api_ordenes.py — endpoints para las órdenes literales de Meta y ganadores detectados.

La app no calcula ni decide: `gen_ordenes.py` genera las órdenes a partir de `_DECISIONES.json`
y `flujo.py` / `_FLUJO.json` dictamina los ganadores. La app solo los sirve a la pantalla.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from . import contratos
from .modelos import Ganador, OrdenesRespuesta

router = APIRouter(prefix="/api", tags=["ordenes"])


@router.get("/ordenes", response_model=OrdenesRespuesta)
def obtener_ordenes(producto: str | None = Query(None, description="Filtrar órdenes por producto_key")) -> OrdenesRespuesta:
    """Las órdenes vigentes de Meta generadas por gen_ordenes.py.
    
    Traduce _DECISIONES.json a llamadas literales de Meta y motivos comprensibles para el operador.
    """
    try:
        data = contratos.ordenes(producto_key=producto)
        # Cada orden lleva el mercado de SU producto (resolver de D1): las cifras `*_q` viajan en la
        # moneda local de ese mercado y la pantalla necesita saber cuál es.
        perfiles: dict[str, dict[str, str]] = {}
        for orden in data.get("ordenes", []):
            clave = orden.get("producto_key", "")
            if clave not in perfiles:
                perfiles[clave] = contratos.perfil_de_producto(clave)
            orden.update(perfiles[clave])
        # Los avisos son del sistema entero (no de un producto): solo viajan en la vista sin filtro.
        avisos = [] if producto else contratos.avisos_claude()
        return OrdenesRespuesta(
            **data, parametros_motor=contratos.parametros_decision(), avisos_claude=avisos
        )
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/ganadores", response_model=list[Ganador])
def obtener_ganadores() -> list[Ganador]:
    """Lista de productos que cuentan con ángulo ganador confirmado por ventas según el flujo."""
    try:
        lista = contratos.ganadores()
        return [Ganador(**item, **contratos.perfil_de_producto(item["producto_key"])) for item in lista]
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
