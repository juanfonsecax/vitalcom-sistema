"""fase1.py — lo que muestran las pantallas de FASE 1 (Hito 4). Solo lectura: NO calcula nada.

Cada pantalla sale de un dueño que ya existe:
  * Avance e investigación, ángulos (texto): la última corrida de «Armar FASE 1» — `pasos.json` y
    `etapas/NN_<etapa>.md`, lo que devolvió cada etapa tal cual (`workflows.wf_pasos`).
  * Anuncios y estructura de campaña: `PRODUCTOS/_LANZADOR.json` (lo deriva `gen_lanzador.py` de
    `_PLAN.json`) y el `_PLAN.json` mismo (avatar y nivel de conciencia de cada ángulo).
  * Flujo LucidBot: `gen_flujo_bot.py <pk> --json --parcial` (por bloques, las `>>` aparte).
  * Checklist: lo que `flujo.py` dice que falta + los bloqueos de `gen_publicacion.py --solo-paquete`,
    cada uno con la acción escritora que lo resuelve (manifiesto: `datos_del_operador` y
    `escritores_de_bloqueo`).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from . import acciones, bitacora, contratos
from .config import python_del_sistema, ruta

ACCION_F1 = "nodo.F1.paquete"
GEN_FLUJO_BOT = ("Ads", "_TOOLS", "gen_flujo_bot.py")
GEN_PUBLICACION = ("Ads", "_TOOLS", "gen_publicacion.py")
LANZADOR = ("PRODUCTOS", "_LANZADOR.json")
EXTENSIONES_DE_MEDIA = {".png", ".jpg", ".jpeg", ".mp4", ".mov"}


def _correr_json(argv: list[str], tope_s: int = 120) -> dict[str, Any] | None:
    """Un script del motor en modo --json. Su salida manda; si no hay JSON, None (no se inventa)."""
    completado = subprocess.run(argv, cwd=str(ruta()), capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=tope_s)
    try:
        return json.loads(completado.stdout)
    except json.JSONDecodeError:
        return None


# ── la última corrida de «Armar FASE 1» ───────────────────────────────────────

def ultima_corrida(producto_key: str) -> Path | None:
    """La carpeta de la corrida más nueva de Armar FASE 1 del producto que tenga `pasos.json`."""
    raiz = bitacora.raiz()
    if not raiz.is_dir():
        return None
    sufijo = f"_{bitacora._limpio(ACCION_F1)}_{bitacora._limpio(producto_key)}_"
    candidatas = [c for c in raiz.glob("*/*") if sufijo in c.name and (c / "pasos.json").is_file()]
    return max(candidatas, key=lambda c: c.name) if candidatas else None


def corrida(producto_key: str) -> dict[str, Any]:
    carpeta = ultima_corrida(producto_key)
    if carpeta is None:
        return {"producto_key": producto_key, "corrida": None, "etapas": []}
    tablero = json.loads((carpeta / "pasos.json").read_text(encoding="utf-8"))
    trabajo = bitacora.leer_trabajo(carpeta) or {}
    sello = trabajo.get("sello") or {}
    etapas = []
    for paso in tablero.get("pasos", []):
        for miembro in paso.get("miembros", []):
            archivo = carpeta / "etapas" / miembro["salida"]
            etapas.append({
                "paso": paso["n"], "etapa": miembro["etapa"], "archivo": miembro["salida"],
                "texto": archivo.read_text(encoding="utf-8") if archivo.is_file() else None,
            })
    congelados = carpeta / "etapas" / "00_INPUTS_CONGELADOS.md"
    return {
        "producto_key": producto_key,
        "corrida": {
            "job_id": sello.get("job_id"), "run_dir": bitacora.ruta_relativa(carpeta),
            "iniciado": sello.get("iniciado"), "estado": trabajo.get("estado"),
            "retomado_de": tablero.get("retomado_de"), "pasos": tablero.get("pasos", []),
        },
        "inputs_congelados": congelados.read_text(encoding="utf-8") if congelados.is_file() else None,
        "etapas": etapas,
    }


# ── anuncios y estructura de campaña ──────────────────────────────────────────

def _url_de_media(producto_key: str, carpeta_media: str, archivo: str | None) -> str | None:
    if not archivo or not carpeta_media:
        return None
    return f"/api/productos/{producto_key}/media/{archivo}" if ruta("Ads", carpeta_media, archivo).is_file() else None


def campana(producto_key: str) -> dict[str, Any]:
    """El lanzador del producto (nombres, presupuesto, banda, fecha 4 AM, copy y pieza por conjunto) y el
    `_PLAN.json` de origen (avatar y nivel de conciencia por ángulo). Tal cual: la app no deriva nada."""
    fila = contratos.fila_de_producto(producto_key)
    lanzador = next((p for p in (contratos._leer_json(LANZADOR).get("productos") or [])
                     if p.get("producto_key") == producto_key), None) if ruta(*LANZADOR).is_file() else None
    slug = fila.get("slug_carpeta") or producto_key
    plan_json = ruta("PRODUCTOS", slug, "_PLAN.json")
    plan_fuente = json.loads(plan_json.read_text(encoding="utf-8")) if plan_json.is_file() else None
    carpeta_media = fila.get("carpeta_media") or ""
    piezas = []
    for conjunto in ((lanzador or {}).get("plan") or {}).get("conjuntos") or (plan_fuente or {}).get("conjuntos") or []:
        archivo = conjunto.get("archivo_creativo")
        piezas.append({"n": conjunto.get("n"), "angulo_key": conjunto.get("angulo_key"), "archivo": archivo,
                       "url": _url_de_media(producto_key, carpeta_media, archivo)})
    return {"producto_key": producto_key, "lanzador": lanzador, "plan_fuente": plan_fuente, "piezas": piezas,
            "lanzador_generado": (contratos._leer_json(LANZADOR).get("generado") if ruta(*LANZADOR).is_file() else None)}


def ruta_de_media(producto_key: str, archivo: str) -> Path | None:
    """El archivo de la carpeta de media del producto, si existe y es media. Nunca sale de esa carpeta."""
    if not archivo or archivo != Path(archivo).name or Path(archivo).suffix.lower() not in EXTENSIONES_DE_MEDIA:
        return None
    carpeta_media = contratos.fila_de_producto(producto_key).get("carpeta_media")
    if not carpeta_media:
        return None
    candidato = ruta("Ads", carpeta_media, archivo)
    return candidato if candidato.is_file() else None


# ── flujo LucidBot ────────────────────────────────────────────────────────────

def flujo_bot(producto_key: str) -> dict[str, Any]:
    """`gen_flujo_bot.py <pk> --json --parcial`: por bloques, con lo que falta marcado como PENDIENTE."""
    salida = _correr_json([python_del_sistema(), str(ruta(*GEN_FLUJO_BOT)), producto_key, "--json", "--parcial"])
    if salida is None:
        return {"producto_key": producto_key, "ok": False, "faltan": [], "avisos": [],
                "prohibiciones": ["gen_flujo_bot.py no devolvió JSON"]}
    return salida


# ── checklist de bloqueos ─────────────────────────────────────────────────────

def _escritores_por_dato(nodo: str | None) -> dict[str, list[str]]:
    """{dato: [acción escritora, alternativas…]} de la acción del nodo (manifiesto)."""
    for accion in acciones.cargar().lista():
        if nodo and accion.get("nodo") and acciones.es_el_mismo_nodo(accion["nodo"], nodo):
            return {d["dato"]: [a for a in [d.get("accion"), *(d.get("alternativas") or [])] if a]
                    for d in accion.get("datos_del_operador") or []}
    return {}


def _con_escritores(item: dict[str, Any], escritores: dict[str, list[str]]) -> dict[str, Any]:
    return {**item, "escritores": escritores.get(item.get("dato", ""), [])}


def checklist(producto_key: str) -> dict[str, Any]:
    flujo = contratos.flujo(producto_key)
    nodo = flujo.get("nodo_actual")
    escritores = _escritores_por_dato(nodo)
    faltan = [_con_escritores(x, escritores) for x in (flujo.get("falta_para_cumplir") or flujo.get("bloqueantes") or [])]
    # La cuenta y la página se ofrecen desde que se arma el paquete: llegan como bloqueos con `clave`
    # de gen_publicacion.py (page_id es del paquete; la cuenta, de la publicación).
    paquete = None
    if nodo in ("F1.paquete", "F1.publicar"):
        salida = _correr_json([python_del_sistema(), str(ruta(*GEN_PUBLICACION)), "--producto", producto_key,
                               "--fase", "1", "--solo-paquete", "--json"])
        if salida is not None:
            mapa = acciones.cargar().bloque.get("escritores_de_bloqueo") or {}
            paquete = {
                "bloqueantes": [{**b, "escritor": mapa.get(b.get("clave"))} for b in salida.get("bloqueantes") or []],
                "avisos": salida.get("avisos") or [],
                "preflight": salida.get("preflight"),
            }
    return {"producto_key": producto_key, "nodo_actual": nodo, "estado": flujo.get("estado"),
            "ejecutor": flujo.get("ejecutor"), "faltan": faltan, "paquete": paquete}


def escritores_permitidos() -> set[str]:
    """Las acciones que la pantalla puede pedir como «cargar un dato»: las que el manifiesto nombra como
    escritoras de un dato del operador o de un bloqueo, y que son scripts internos."""
    bloque = acciones.cargar().bloque
    nombradas = set((bloque.get("escritores_de_bloqueo") or {}).values())
    for accion in acciones.cargar().lista():
        for dato in accion.get("datos_del_operador") or []:
            nombradas |= {a for a in [dato.get("accion"), *(dato.get("alternativas") or [])] if a}
    # Solo las que COMPLETAN un producto que ya existe (reciben su producto_key): el alta tiene su pantalla.
    return {a["id"] for a in acciones.cargar().lista()
            if a["id"] in nombradas and a.get("ejecutor_tipo") == "script" and a.get("visibilidad") == "interna"
            and (a.get("parametros") or {}).get("producto_key", {}).get("tipo") == "producto_key"}
