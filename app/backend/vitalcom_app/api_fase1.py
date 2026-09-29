"""api_fase1.py — las pantallas de FASE 1 (Hito 4) y la carga de un dato desde el checklist.

Lectura: lo arma `fase1.py` desde los dueños de cada dato. Escritura: SOLO acciones escritoras que el
manifiesto nombra para un dato del operador o un bloqueo (`fase1.escritores_permitidos`), por el runner y
su cola, igual que el alta. No hay un endpoint que escriba por su cuenta.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import acciones, contratos, fase1, subidas, workflows
from .acciones import ErrorDeAccion
from .modelos import CampanaF1, ChecklistF1, CorridaF1, DatosParaArrancar, FlujoBot

router = APIRouter(prefix="/api/productos", tags=["fase1"])
TOPE_DE_LA_CARGA_S = 120


def _exigir_producto(producto_key: str) -> None:
    if not contratos.fila_de_producto(producto_key):
        raise HTTPException(status_code=404, detail=f"«{producto_key}» no tiene fila en _DIM_PRODUCTOS.csv.")


@router.get("/{producto_key}/fase1/corrida", response_model=CorridaF1)
def corrida_de_fase1(producto_key: str) -> CorridaF1:
    """La última corrida de «Armar FASE 1»: el avance por paso y lo que devolvió cada etapa, textual."""
    _exigir_producto(producto_key)
    return CorridaF1(**fase1.corrida(producto_key))


@router.get("/{producto_key}/fase1/campana", response_model=CampanaF1)
def campana_de_fase1(producto_key: str) -> CampanaF1:
    """Anuncios y estructura de campaña: `_LANZADOR.json` y el `_PLAN.json` de origen, tal cual."""
    _exigir_producto(producto_key)
    return CampanaF1(**fase1.campana(producto_key))


@router.get("/{producto_key}/flujo-bot", response_model=FlujoBot)
def flujo_bot(producto_key: str) -> FlujoBot:
    """El flujo LucidBot por bloques (`gen_flujo_bot.py --json --parcial`): lo que se pega y las `>>` aparte."""
    _exigir_producto(producto_key)
    return FlujoBot(**fase1.flujo_bot(producto_key))


@router.get("/{producto_key}/checklist", response_model=ChecklistF1)
def checklist(producto_key: str) -> ChecklistF1:
    """Lo que falta para seguir, cada cosa con la acción que la resuelve (si la carga el operador)."""
    _exigir_producto(producto_key)
    return ChecklistF1(**fase1.checklist(producto_key))


@router.get("/{producto_key}/datos", response_model=DatosParaArrancar)
def datos_para_arrancar(producto_key: str) -> DatosParaArrancar:
    """Los datos que el producto necesita para arrancar (foto, precio, página, cuenta, costo, perfil, referencia)."""
    _exigir_producto(producto_key)
    return DatosParaArrancar(**fase1.datos_para_arrancar(producto_key))


@router.get("/{producto_key}/media/{archivo}", response_class=FileResponse)
def media(producto_key: str, archivo: str) -> FileResponse:
    """Una pieza de la carpeta de media del producto (para verla en la pantalla). Nunca sale de esa carpeta."""
    encontrado = fase1.ruta_de_media(producto_key, archivo)
    if encontrado is None:
        raise HTTPException(status_code=404, detail=f"«{archivo}» no está en la carpeta de media de {producto_key}.")
    return FileResponse(encontrado)


@router.post("/{producto_key}/cargar/{accion_id}")
def cargar_dato(producto_key: str, accion_id: str, datos: str = Form("{}"),
                archivo: UploadFile | None = File(None)) -> dict:
    """Carga UN dato del checklist con su acción escritora y espera el resultado (como el alta)."""
    _exigir_producto(producto_key)
    if accion_id not in fase1.escritores_permitidos():
        raise ErrorDeAccion(403, "NO_ES_UN_ESCRITOR", f"«{accion_id}» no es la escritora de un dato del checklist.")
    accion = acciones.por_id_para_el_runner(accion_id)
    try:
        parametros = json.loads(datos or "{}")
    except json.JSONDecodeError as error:
        raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "«datos» no es JSON.", campo="datos") from error
    if not isinstance(parametros, dict):
        raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "«datos» tiene que ser un objeto.", campo="datos")
    parametros["producto_key"] = producto_key
    de_archivo = next((n for n, e in accion.get("parametros", {}).items() if e.get("tipo") == "archivo_temporal"), None)
    try:
        with subidas.carpeta_temporal() as temporal:
            if de_archivo:
                if archivo is None:
                    raise ErrorDeAccion(422, "PARAMETRO_INVALIDO", "Falta el archivo.", campo="archivo")
                parametros[de_archivo] = str(subidas.guardar(archivo.file, archivo.filename or "archivo", temporal))
            valores = acciones.validar_parametros(accion, parametros)
            job_id, _repetido = workflows.encolar(accion, valores, uuid.uuid4().hex)
            resultado = workflows.esperar_resultado(job_id, TOPE_DE_LA_CARGA_S)
    except subidas.SubidaRechazada as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if resultado is None:
        raise HTTPException(status_code=409, detail="La carga no alcanzó a terminar: hay otro cambio en curso. "
                                                    "Probá de nuevo en un momento.")
    unidad = resultado["unidades"][0]
    if resultado["estado"] != "EXITO":
        raise HTTPException(status_code=422, detail=unidad.get("detalle") or resultado["detalle"])
    return unidad.get("json") or {"ok": True}
