"""sse.py — el progreso en vivo de un trabajo, como Server-Sent Events (diseño §3.10).

`GET /api/trabajos/{id}/eventos` entrega:
    event: estado     {estado, unidad, detalle}   cuando el estado cambia
    event: pendiente  {…}                         la orden o la pregunta que espera al operador ({} = ya no hay)
    event: linea      {unidad, texto, tipo}       cada línea nueva de los logs de la corrida
    event: fin        {estado, resultado}         el trabajo terminó; se cierra la conexión

Cada evento lleva `id:` = los desplazamientos (en bytes) de todos los logs hasta ahí, así que con
`Last-Event-ID` el navegador sigue desde donde quedó sin repetir ni perder líneas. Se sondea cada
segundo el estado de DBOS y el crecimiento de los logs; el JSON crudo de Claude queda en la bitácora
y acá viaja resumido (`claude.resumir_evento`).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Iterator

from . import bitacora, claude, trabajos, workflows

SONDEO_S = 1.0
LATIDO_CADA_S = 15.0


def _evento(nombre: str, datos: dict[str, Any], id_: str | None = None) -> str:
    cabecera = f"id: {id_}\n" if id_ else ""
    return f"{cabecera}event: {nombre}\ndata: {json.dumps(datos, ensure_ascii=False, default=str)}\n\n"


def _id_de(desplazamientos: dict[str, int]) -> str:
    return "|".join(f"{nombre}:{desde}" for nombre, desde in sorted(desplazamientos.items()))


def _leer_id(ultimo: str | None) -> dict[str, int]:
    salida: dict[str, int] = {}
    for pieza in (ultimo or "").split("|"):
        nombre, _, desde = pieza.rpartition(":")
        if nombre and desde.isdigit():
            salida[nombre] = int(desde)
    return salida


def linea_de(nombre_de_log: str, texto: str) -> dict[str, Any] | None:
    """Un renglón de un log → lo que ve la pantalla. None = no vale la pena mostrarlo."""
    unidad = int(re.match(r"^(\d+)_", nombre_de_log).group(1))  # type: ignore[union-attr]
    if nombre_de_log.endswith(".jsonl"):
        try:
            resumen = claude.resumir_evento(json.loads(texto))
        except json.JSONDecodeError:
            resumen = texto
        return {"unidad": unidad, "texto": resumen, "tipo": "claude"} if resumen else None
    if texto.startswith("[stderr] "):
        return {"unidad": unidad, "texto": texto[len("[stderr] "):], "tipo": "error"}
    if texto.startswith("$ "):
        return {"unidad": unidad, "texto": texto[2:], "tipo": "comando"}
    return {"unidad": unidad, "texto": texto, "tipo": "salida"} if texto.strip() else None


def _lineas_nuevas(carpeta: Path | None, desplazamientos: dict[str, int]) -> Iterator[tuple[dict[str, Any], str]]:
    """Cada línea nueva con SU id: el desplazamiento de todos los logs justo después de esa línea."""
    if carpeta is None:
        return
    for nombre in bitacora.logs_de(carpeta):
        for texto, termina_en in bitacora.leer_incremental(carpeta, nombre, desplazamientos.get(nombre, 0)):
            desplazamientos[nombre] = termina_en
            evento = linea_de(nombre, texto)
            if evento:
                yield evento, _id_de(desplazamientos)


def generar(job_id: str, ultimo_id: str | None = None, sondeo_s: float | None = None) -> Iterator[str]:
    """El flujo de eventos de un trabajo. Termina (con `fin`) cuando el trabajo termina."""
    espera = SONDEO_S if sondeo_s is None else sondeo_s
    desplazamientos = _leer_id(ultimo_id)
    estado_previo: str | None = None
    pendiente_previo: Any = object()
    ultimo_latido = time.monotonic()
    while True:
        estado_dbos = trabajos._existente(job_id)
        en_marcha = estado_dbos.status in ("PENDING", "ENQUEUED")
        publicado = workflows.publicado(job_id, "estado") if estado_dbos.status == "PENDING" else None
        estado = trabajos.estado_visible(estado_dbos, publicado)
        if estado != estado_previo:
            estado_previo = estado
            yield _evento("estado", {"estado": estado, "unidad": (publicado or {}).get("unidad"), "detalle": ""},
                          _id_de(desplazamientos))
        pendiente = workflows.publicado(job_id, "pendiente") if estado_dbos.status == "PENDING" else None
        if pendiente != pendiente_previo:
            pendiente_previo = pendiente
            yield _evento("pendiente", pendiente or {}, _id_de(desplazamientos))
        hubo = False
        for linea, id_ in _lineas_nuevas(bitacora.buscar_corrida(job_id), desplazamientos):
            hubo = True
            yield _evento("linea", linea, id_)
        if not en_marcha or estado == "OTRA_VERSION":
            yield _evento("fin", {"estado": estado, "resultado": trabajos.detalle(job_id).get("resultado")},
                          _id_de(desplazamientos))
            return
        if hubo:
            ultimo_latido = time.monotonic()
        elif time.monotonic() - ultimo_latido > LATIDO_CADA_S:
            ultimo_latido = time.monotonic()
            yield ": latido\n\n"
        time.sleep(espera)
