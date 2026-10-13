"""api_finanzas.py — el estado de resultados mes a mes y la carga de los datos que lo alimentan.

La lectura corre `gen_pl_mensual.py` (solo lee); la carga pasa por las acciones del manifiesto
`finanzas.ingerir_dropi`, `finanzas.ingerir_cartera` y `finanzas.ingerir_banco`, que son las que
escriben `_FACT_ORDENES_DROPI.csv`, `_FACT_CARTERA_DROPI.csv` y `_FACT_BANCO.csv`. La app no calcula ni escribe: el archivo subido
entra por el temporal de la subida y lo guarda el script.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from . import acciones, contratos, workflows
from .acciones import ErrorDeAccion
from .api_fase1 import TOPE_DE_LA_CARGA_S, ejecutar_con_archivo
from .modelos import ResultadoMensual

router = APIRouter(prefix="/api/resultados", tags=["resultados"])

ACCION_DROPI = "finanzas.ingerir_dropi"
ACCION_CARTERA = "finanzas.ingerir_cartera"
ACCION_BANCO = "finanzas.ingerir_banco"


@router.get("/mensual", response_model=ResultadoMensual)
def resultado_mensual(mercado: str = Query("GT", description="GT o CO")) -> ResultadoMensual:
    """El estado de resultados de cada mes de un mercado, tal como lo calcula `gen_pl_mensual.py`.
    Colombia (y un mes sin datos) salen vacíos con su nota en `faltantes`: nunca ceros inventados."""
    clave = mercado.strip().upper()
    if clave not in {m["mercado"] for m in contratos.mercados()}:
        raise HTTPException(status_code=422, detail=f"«{mercado}» no es un mercado del sistema.")
    return ResultadoMensual(**contratos.resultado_mensual(clave))


@router.post("/mensual/cargar", status_code=201)
def cargar_mensual(
    dropi: UploadFile | None = File(None, description="export de órdenes de Dropi (.xlsx)"),
    cartera: UploadFile | None = File(None, description="historial de cartera de Dropi (.xlsx)"),
    banco: UploadFile | None = File(None, description="extracto bancario de Relay (.pdf)"),
    cuenta: str = Form("", description="últimos 4 dígitos de la cuenta; vacío = la del extracto"),
) -> dict[str, Any]:
    """Guarda lo que el operador sube: el export de órdenes de Dropi, el historial de cartera de Dropi
    y/o un extracto bancario, cada uno con su acción escritora. Se pueden subir por separado (Dropi es
    semanal, el banco mensual)."""
    if dropi is None and cartera is None and banco is None:
        raise HTTPException(
            status_code=422, detail="Subí un export de Dropi, el historial de cartera o un extracto bancario."
        )
    resultado: dict[str, Any] = {}
    guardados: list[str] = []
    for clave, accion_id, archivo, nombre in (
        ("dropi", ACCION_DROPI, dropi, "el export de Dropi"),
        ("cartera", ACCION_CARTERA, cartera, "el historial de cartera"),
    ):
        if archivo is None:
            continue
        try:
            resultado[clave] = ejecutar_con_archivo(accion_id, {}, archivo)
        except HTTPException as error:
            if guardados:
                error.detail = f"{error.detail} (ya quedó guardado: {', '.join(guardados)})"
            raise
        guardados.append(nombre)
    if banco is not None:
        parametros = {"cuenta": cuenta.strip()} if cuenta.strip() else {}
        try:
            resultado["banco"] = ejecutar_con_archivo(ACCION_BANCO, parametros, banco)
        except HTTPException as error:
            if guardados:
                error.detail = f"{error.detail} (ya quedó guardado: {', '.join(guardados)})"
            raise
    return resultado


def persistir_en_finanzas(ruta_dropi: Path | None, ruta_banco: Path | None) -> dict[str, Any]:
    """Guarda en los hechos de finanzas lo que `resultados.cargar_pl` acaba de calcular, con los
    mismos archivos. Es un efecto aparte: si falla, el P&L ya calculado se entrega igual y el error
    viaja en el resultado (nunca se traga en silencio)."""
    salida: dict[str, Any] = {}
    for clave, accion_id, ruta in (("dropi", ACCION_DROPI, ruta_dropi), ("banco", ACCION_BANCO, ruta_banco)):
        if ruta is None:
            continue
        try:
            accion = acciones.por_id_para_el_runner(accion_id)
            valores = acciones.validar_parametros(accion, {"archivo": str(ruta)})
            job_id, _repetido = workflows.encolar(accion, valores, uuid.uuid4().hex)
            hecho = workflows.esperar_resultado(job_id, TOPE_DE_LA_CARGA_S)
            if hecho is None:
                salida[clave] = {"error": "No alcanzó a terminar: hay otro cambio en curso."}
                continue
            unidad = hecho["unidades"][0]
            if hecho["estado"] != "EXITO":
                salida[clave] = {"error": unidad.get("detalle") or hecho["detalle"]}
            else:
                salida[clave] = unidad.get("json") or {"ok": True}
        except (ErrorDeAccion, HTTPException) as error:
            salida[clave] = {"error": str(getattr(error, "detalle", None) or getattr(error, "detail", error))}
    return salida
