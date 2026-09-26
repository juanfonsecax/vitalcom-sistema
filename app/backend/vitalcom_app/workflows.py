"""workflows.py — el runner: DBOS pone el CUÁNDO, el manifiesto pone el QUÉ (diseño Hito 3, §3).

Dos colas:
  * `trabajos` (concurrencia 8, deduplicada por producto): los workflows PADRE. Pueden esperar
    una aprobación durante horas sin trabar a nadie, porque no escriben nada ellos mismos.
  * `escritura` (concurrencia 1, global): cada UNIDAD que escribe. Además toma el candado de
    archivo (`escrituras.Cola`) con latido. Esperar una aprobación nunca retiene este turno.

Reglas que este módulo hace cumplir:
  * Ningún argv se arma acá: sale de `acciones.resolver()`. No hay un solo literal de script.
  * Nada no determinista vive fuera de un paso: la fecha, el manifiesto y el `uuid` se sellan en
    el primer paso del padre y al retomar se usa esa copia (`paso_sellar`).
  * Un paso que se cae a mitad de una acción NO idempotente no se repite: la unidad queda
    `INTERRUMPIDO` con su rastro (invariante 5: rerun completo, nunca parche parcial).
  * El veredicto de un nodo no lo da lo que un script o Claude "dice": lo da `flujo.py`.

`APP_VERSION` se escribe a mano y se sube SOLO si cambia la lista de pasos de un workflow
(`PASOS`); DBOS reemplaza cada paso ya hecho por posición y solo retoma trabajos de su misma
versión. `tests/test_workflows.py::test_version_de_workflows` lo vigila.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dbos import DBOS, SetEnqueueOptions, SetWorkflowID
from dbos._error import DBOSQueueDeduplicatedError

from . import acciones, bitacora, claude, contratos
from .acciones import ErrorDeAccion
from .config import base, datos_de_la_app, python_del_sistema, ruta
from .escrituras import Cola, SistemaOcupado

APP_VERSION = "wf-3"
NOMBRE_DE_LA_APP = "vitalcom-app"
COLA_TRABAJOS = "trabajos"
COLA_ESCRITURA = "escritura"
SONDEO_DE_RESULTADO_S = 0.2
MAXIMO_DE_PREGUNTAS = 5
MAXIMO_DE_APROBACIONES = 3
MAXIMO_DE_MENSAJES_AJENOS = 5
MAXIMO_DE_VUELTAS_DE_MEDIA = 3
CARPETA_DE_SUBIDA = "subir_a_meta"
MARCA_SIN_MCP = "CUENTA_SIN_MCP"
TOPE_DE_TEXTO_DE_CLAUDE = 4000
TOPE_DE_ESPERA_DEL_TURNO_S = 3600

# Los pasos que cada workflow llama, en orden. Si esta lista cambia, cambia la versión.
PASOS: dict[str, list[str]] = {
    "wf_unidad": ["paso_ejecutar", "paso_tras_escribir"],
    "wf_limpieza": ["paso_tras_escribir"],
    "wf_script": [
        "paso_sellar", "DBOS.set_event", "enqueue:escritura", "paso_leer_flujo", "paso_cerrar",
        "DBOS.set_event",
    ],
    "wf_claude": [
        "paso_sellar", "DBOS.set_event", "enqueue:escritura", "DBOS.set_event", "DBOS.set_event",
        "DBOS.recv", "DBOS.set_event", "DBOS.set_event", "enqueue:escritura", "paso_leer_flujo",
        "paso_cerrar", "DBOS.set_event",
    ],
    "wf_pasos": [
        "paso_sellar", "DBOS.set_event", "paso_preparar_pasos", "DBOS.set_event", "enqueue:escritura",
        "DBOS.set_event", "DBOS.set_event", "DBOS.recv", "DBOS.set_event", "DBOS.set_event", "enqueue:escritura",
        "enqueue:escritura", "paso_leer_flujo", "paso_cerrar", "DBOS.set_event",
    ],
    "wf_meta": [
        "paso_sellar", "DBOS.set_event", "enqueue:escritura", "enqueue:escritura",
        # --media biblioteca: leer la biblioteca, elegir nombres, esperar al operador, leer los hashes
        "enqueue:escritura", "enqueue:escritura", "paso_preparar_subida", "DBOS.set_event", "DBOS.set_event",
        "DBOS.recv", "DBOS.set_event", "DBOS.set_event", "enqueue:escritura", "enqueue:escritura",
        "paso_firmar_orden", "DBOS.set_event", "DBOS.set_event", "DBOS.recv", "DBOS.set_event", "paso_registrar_rechazo",
        "paso_sellar_aprobacion", "DBOS.set_event", "enqueue:escritura", "enqueue:escritura",
        "enqueue:escritura", "paso_preparar_evento", "enqueue:escritura", "paso_leer_flujo", "paso_cerrar",
        "DBOS.set_event",
    ],
}

# Lo que se le pide a Claude en cada paso de la publicación. La skill `publicar-meta` es dueña del
# CÓMO; el runner solo pone el CUÁNDO y la compuerta de aprobación entre el paso 2 y el 3.
PROMPT_SNAPSHOT = "\n".join([
    "Sos el ejecutor del paso 1 (PRE-FLIGHT) de la skill publicar-meta, trabajo {job_id}.",
    "SOLO LECTURA: no crees, actualices ni actives nada en Meta.",
    "1. Llamá `ads_get_ad_accounts` y verificá que la cuenta {cuenta} ({cuenta_id}) tenga is_ads_mcp_enabled "
    "e is_queryable. Si no los tiene, terminá tu respuesta con la línea `{marca}` y nada más.",
    "2. Llamá `ads_get_ad_entities` con level=campaign, level=adset y level=ad sobre esa cuenta.",
    "3. Llamá `ads_get_user_pages`.",
    "4. Guardá lo del paso 2 en `{snapshot}` con esta forma exacta: "
    '{{"cuenta_alias":"…","cuenta_id":"…","tomado_el":"<ISO>","ad_entities":[{{"id":"…","nivel":"campaign|adset|ad","name":"…","status":"…"}}]}}',
    "SNAPSHOT_EN: {snapshot}",
])
PROMPT_EJECUCION = "\n".join([
    "Sos el ejecutor del paso 3 de la skill publicar-meta, trabajo {job_id}. El operador APROBÓ esta orden (hash {hash}).",
    "Ejecutá EN ORDEN, de menor a mayor n, SOLO las llamadas de LLAMADAS_JSON, con sus args LITERALES. "
    "Sustituí cada {{{{variable}}}} por el id que devolvió una llamada anterior (guardar_como) o por su valor en VARIABLES_JSON. "
    "No agregues, no cambies ni omitas ninguna. Si una llamada falla, PARÁ ahí y decí cuál fue.",
    "Terminá con una línea `EJECUTADAS: n1,n2,…` con los n que llamaste con éxito.",
    "VARIABLES_JSON: {variables}",
    "LLAMADAS_JSON: {llamadas}",
])

# Las imágenes las sube el operador a mano (decisión del 18-sep-2026, spike F: LOCAL_FILE necesita una
# pantalla). Claude solo LEE la biblioteca; los nombres y los hashes los resuelve `gen_publicacion.py`.
PROMPT_IMAGENES = "\n".join([
    "Sos el lector de la biblioteca de imágenes de Meta para la skill publicar-meta, trabajo {job_id}.",
    "SOLO LECTURA: no subas, crees ni cambies nada en Meta.",
    "Para cada texto de BUSCAR_JSON, llamá `ads_get_ad_images` con ad_account_id={cuenta_id}, name=<ese texto>, "
    "limit=100 y fields=[\"name\",\"hash\"]; si la respuesta trae next_cursor, seguí pidiendo hasta que no traiga.",
    "Guardá TODAS las imágenes que devolvió, sin filtrar ni corregir nombres, en `{destino}` con esta forma exacta: "
    '{{"cuenta_id":"{cuenta_id}","tomado_el":"<ISO>","imagenes":[{{"hash":"…","name":"…"}}]}}',
    "BUSCAR_JSON: {buscar}",
    "IMAGENES_EN: {destino}",
])

ESTADOS_FINALES = ("EXITO", "SIN_CUMPLIR", "RECHAZADO", "CADUCADO", "FALLIDO", "INTERRUMPIDO",
                   "CSV_INVALIDO", "CANCELADO")

_procesos: dict[str, subprocess.Popen] = {}
_cancelados: set[str] = set()
_lock_de_procesos = threading.Lock()


def _ahora() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# ── arranque y cierre de DBOS ─────────────────────────────────────────────────

def iniciar(url_de_base_de_datos: str | None = None) -> None:
    """Configura y lanza DBOS. Al lanzar, DBOS retoma los trabajos PENDING de esta versión."""
    _cancelados.clear()  # las cancelaciones valen para esta vida de la app; cada trabajo tiene su id
    url = url_de_base_de_datos or f"sqlite:///{(datos_de_la_app() / 'dbos.sqlite').as_posix()}"
    DBOS(config={
        "name": NOMBRE_DE_LA_APP,
        "system_database_url": url,
        "application_version": APP_VERSION,
        "log_level": "WARNING",
    })
    DBOS.launch()
    DBOS.register_queue(COLA_TRABAJOS, global_concurrency=8, polling_interval_sec=0.1)
    DBOS.register_queue(COLA_ESCRITURA, global_concurrency=1, polling_interval_sec=0.1)


def detener() -> None:
    DBOS.destroy()


def _cola(nombre: str):  # type: ignore[no-untyped-def]
    cola = DBOS.retrieve_queue(nombre)
    if cola is None:
        raise RuntimeError(f"la cola «{nombre}» no está registrada: ¿corrió `iniciar()`?")
    return cola


# ── subprocesos ───────────────────────────────────────────────────────────────

def _matar_arbol(proceso: subprocess.Popen) -> None:
    """Mata el subproceso y todo lo que arrancó (un script puede lanzar otros)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proceso.pid)],
                           capture_output=True, timeout=30)
        else:
            os.killpg(os.getpgid(proceso.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        proceso.kill()


def _drenar(canal, log, lock: threading.Lock, acumulado: list[str], prefijo: bytes) -> None:  # type: ignore[no-untyped-def]
    for linea in iter(canal.readline, b""):
        with lock:
            log.write(prefijo + linea)
            log.flush()
        acumulado.append(linea.decode("utf-8", errors="replace"))


def _correr_proceso(job_id: str, argv: list[str], log_nombre: str, carpeta: Path,
                    tiempo_max_s: int) -> dict[str, Any]:
    """Corre UN comando (lista de tokens, sin shell), su salida va línea a línea a la bitácora."""
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    inicio = time.monotonic()
    with bitacora.abrir_log(carpeta, log_nombre) as log:
        log.write(f"$ {' '.join(argv)}\n".encode("utf-8"))
        proceso = subprocess.Popen(
            argv, cwd=str(base()), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=entorno, start_new_session=(os.name != "nt"),
        )
        with _lock_de_procesos:
            _procesos[job_id] = proceso
        salida: list[str] = []
        errores: list[str] = []
        lock = threading.Lock()
        hilos = [
            threading.Thread(target=_drenar, args=(proceso.stdout, log, lock, salida, b""), daemon=True),
            threading.Thread(target=_drenar, args=(proceso.stderr, log, lock, errores, b"[stderr] "), daemon=True),
        ]
        for hilo in hilos:
            hilo.start()
        motivo = None
        while True:
            try:
                proceso.wait(timeout=0.5)
                break
            except subprocess.TimeoutExpired:
                if job_id in _cancelados:
                    motivo = "cancelado"
                elif tiempo_max_s and time.monotonic() - inicio > tiempo_max_s:
                    motivo = f"pasó del tope de {tiempo_max_s} s"
                if motivo:
                    _matar_arbol(proceso)
                    proceso.wait()
                    break
        for hilo in hilos:
            hilo.join(timeout=5)
        with _lock_de_procesos:
            _procesos.pop(job_id, None)
    return {
        "codigo_salida": proceso.returncode,
        "motivo_de_corte": motivo,
        "stdout": "".join(salida),
        "stderr": "".join(errores),
        "duracion_s": round(time.monotonic() - inicio, 1),
    }


def _interpretar_salida(spec: dict[str, Any], corrida: dict[str, Any]) -> dict[str, Any]:
    """El veredicto de un script es SUYO: su `detalle`, su `ok`, su código de salida."""
    resumen: dict[str, Any] = {"codigo_salida": corrida["codigo_salida"], "duracion_s": corrida["duracion_s"]}
    if corrida["motivo_de_corte"]:
        estado = "CANCELADO" if corrida["motivo_de_corte"] == "cancelado" else "FALLIDO"
        return {**resumen, "estado": estado, "detalle": f"El comando se cortó: {corrida['motivo_de_corte']}."}
    datos = None
    if spec.get("salida") == "json" and corrida["stdout"].strip():
        try:
            datos = json.loads(corrida["stdout"])
        except json.JSONDecodeError:
            return {**resumen, "estado": "FALLIDO",
                    "detalle": "El script no devolvió JSON: " + (corrida["stdout"] or corrida["stderr"])[-400:]}
        resumen["json"] = datos
    if isinstance(datos, dict) and datos.get("bloqueantes"):
        # el generador de la publicación sale con exit 1 y su JSON trae qué falta y quién lo produce
        return {**resumen, "estado": "FALLIDO", "detalle": _detalle_de_bloqueantes({"json": datos})}
    if corrida["codigo_salida"] != 0 or (isinstance(datos, dict) and datos.get("ok") is False):
        detalle = ((datos or {}).get("detalle") if isinstance(datos, dict) else None) \
            or corrida["stderr"].strip() or corrida["stdout"].strip() or "el comando falló sin decir por qué"
        return {**resumen, "estado": "FALLIDO", "detalle": detalle[-800:]}
    return {**resumen, "estado": "EXITO"}


def correr_script(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    carpeta = ruta(spec["run_dir"])
    corrida = _correr_proceso(job_id, spec["argv"], f"{n}_{spec['accion_id']}.log", carpeta, spec["tiempo_max_s"])
    return _interpretar_salida(spec, corrida)


def _registrar_proceso(job_id: str):  # type: ignore[no-untyped-def]
    def _al_arrancar(proceso: subprocess.Popen) -> None:
        with _lock_de_procesos:
            _procesos[job_id] = proceso

    return _al_arrancar


def correr_claude(job_id: str, n: int, spec: dict[str, Any], nombre_log: str | None = None) -> dict[str, Any]:
    """Una llamada headless a Claude Code. La salida cruda va a `<n>_claude.jsonl` en la bitácora."""
    carpeta = ruta(spec["run_dir"])
    pedido = spec["claude"]
    try:
        with bitacora.abrir_log(carpeta, nombre_log or spec.get("nombre_log") or f"{n}_claude.jsonl") as log:
            def _escribir(linea: str) -> None:
                log.write((linea + "\n").encode("utf-8"))
                log.flush()

            resultado = claude.correr(
                prompt=pedido["prompt"], herramientas=pedido["herramientas"],
                presupuesto_usd=pedido["presupuesto_usd"], tiempo_max_s=spec["tiempo_max_s"],
                escribir_linea=_escribir, resume=pedido.get("resume"),
                al_arrancar=_registrar_proceso(job_id), debe_cortar=lambda: job_id in _cancelados,
                matar=_matar_arbol,
            )
    except claude.ClaudeNoDisponible as error:
        return {"estado": "FALLIDO", "detalle": error.detalle, "codigo": error.codigo}
    finally:
        with _lock_de_procesos:
            _procesos.pop(job_id, None)
    resumen: dict[str, Any] = {
        "session_id": resultado.session_id, "pregunta": resultado.pregunta,
        "texto_final": resultado.texto_final[-TOPE_DE_TEXTO_DE_CLAUDE:],
        "costo_equivalente_usd": resultado.costo_equivalente_usd, "num_turns": resultado.num_turns,
        "duracion_s": resultado.duracion_s, "subtype": resultado.subtype,
    }
    if resultado.subtype == "cancelado":
        return {**resumen, "estado": "CANCELADO", "detalle": "El trabajo se canceló."}
    if resultado.subtype == "timeout":
        return {**resumen, "estado": "FALLIDO",
                "detalle": f"Claude pasó del tope de {spec['tiempo_max_s']} s y se cortó."}
    if not resultado.ok:
        return {**resumen, "estado": "FALLIDO",
                "detalle": f"Claude terminó mal ({resultado.subtype}): {resultado.texto_final[-400:]}"}
    if spec.get("detecta_sin_mcp") and MARCA_SIN_MCP in resultado.texto_final:
        return {**resumen, "estado": "FALLIDO",
                "detalle": "Esta cuenta se pauta a mano: Meta dice que no tiene el MCP habilitado."}
    return {**resumen, "estado": "EXITO"}


def _nombre_de_meta(servidor: str, herramienta: str) -> str:
    return f"mcp__{servidor}__{herramienta}"


def _llamadas_de(paquete: dict[str, Any]) -> list[dict[str, Any]]:
    """Las llamadas que van a Meta: las que el generador NO marcó como ya existentes."""
    return [
        {"n": c["n"], "tool": c["tool"], "args": c["args"]}
        for c in paquete.get("llamadas", []) if not c.get("omitir")
    ]


def _clave_de_llamada(llamada: dict[str, Any]) -> tuple[int, str, str]:
    return (llamada["n"], llamada["tool"], json.dumps(llamada["args"], sort_keys=True, ensure_ascii=False))


def huella_de_la_orden(orden: dict[str, Any]) -> str:
    """sha256 del JSON canónico de la orden: lo que el operador aprueba es exactamente esto."""
    canonico = json.dumps(orden, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _claude_de_lectura(job_id: str, n: int, spec: dict[str, Any], sufijo: str) -> dict[str, Any]:
    """Snapshot fresco de Meta: Claude con SOLO herramientas de lectura."""
    pedido = {**spec, "tipo": "claude", "claude": spec["snapshot_claude"], "detecta_sin_mcp": True}
    return correr_claude(job_id, n, pedido, nombre_log=f"{n}_{sufijo}.jsonl")


def correr_meta_ejecucion(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """M3: el ÚNICO lugar donde Claude recibe herramientas de ESCRITURA de Meta.

    Todo dentro de UN paso, en este orden: (1) la aprobación no puede haber caducado; (2) snapshot
    fresco; (3) el paquete se regenera contra él; (4) lo que va a llamar tiene que ser un SUBCONJUNTO
    de lo aprobado — si aparece algo nuevo, para y pide otra aprobación; (5) recién ahí, Claude
    ejecuta esas llamadas literales, con las herramientas exactas y ninguna otra.
    """
    if datetime.fromisoformat(_ahora()) > datetime.fromisoformat(spec["valida_hasta"]):
        return {"estado": "CADUCADO", "detalle": "La aprobación caducó antes de ejecutar: no se llamó a nada."}
    snapshot = _claude_de_lectura(job_id, n, spec, "snapshot_fresco")
    if snapshot["estado"] != "EXITO":
        return snapshot
    carpeta = ruta(spec["run_dir"])
    corrida = _correr_proceso(job_id, spec["argv_paquete"], f"{n}_regenerar.log", carpeta, spec["tiempo_paquete_s"])
    regenerado = _interpretar_salida({"salida": "json"}, corrida)
    if regenerado["estado"] != "EXITO":
        return {**regenerado, "detalle": _detalle_de_bloqueantes(regenerado)}
    paquete = regenerado["json"]
    aprobadas = {_clave_de_llamada(c) for c in spec["orden"]["llamadas"]}
    nuevas = [c for c in _llamadas_de(paquete) if _clave_de_llamada(c) not in aprobadas]
    if nuevas:
        return {"estado": "PIDE_REAPROBACION", "paquete": paquete,
                "detalle": f"Apareció {len(nuevas)} llamada(s) que no estaban en la orden aprobada: hace falta aprobar otra vez."}
    pendientes = [c for c in paquete["llamadas"] if not c.get("omitir")]
    if not pendientes:
        return {"estado": "EXITO", "ejecutadas": [], "detalle": "Meta ya tiene todo: no había nada que llamar."}
    herramientas_de_escritura = sorted({c["tool"] for c in pendientes})
    fuera_del_manifiesto = [t for t in herramientas_de_escritura if t not in spec["escritura"]]
    if fuera_del_manifiesto:
        return {"estado": "FALLIDO",
                "detalle": f"La orden usa {fuera_del_manifiesto}, que la acción no declara en herramientas_meta.escritura."}
    variables = {c["guardar_como"]: c["id_existente"] for c in paquete["llamadas"]
                 if c.get("omitir") and c.get("id_existente") and c.get("guardar_como")}
    prompt = PROMPT_EJECUCION.format(
        job_id=job_id, hash=spec["hash"], variables=json.dumps(variables, ensure_ascii=False),
        llamadas=json.dumps(pendientes, ensure_ascii=False))
    permitidas = [_nombre_de_meta(spec["servidor"], t) for t in [*spec["lectura"], *herramientas_de_escritura]]
    ejecucion = correr_claude(job_id, n, {
        "run_dir": spec["run_dir"], "tiempo_max_s": spec["tiempo_max_s"],
        "claude": {"prompt": prompt, "herramientas": permitidas, "presupuesto_usd": spec["presupuesto_usd"],
                   "resume": None}}, nombre_log=f"{n}_ejecucion.jsonl")
    if ejecucion["estado"] != "EXITO":
        return {**ejecucion, "detalle": "Una llamada a Meta falló o Claude se cortó: la secuencia quedó a medias. "
                                        "Reintentá y retomará sin duplicar. " + ejecucion.get("detalle", "")}
    return {**ejecucion, "ejecutadas": [c["n"] for c in pendientes]}


def _detalle_de_bloqueantes(resumen: dict[str, Any]) -> str:
    """Los bloqueantes del generador, con el nombre de quien produce cada dato (invariante 4)."""
    bloqueantes = (resumen.get("json") or {}).get("bloqueantes") or []
    if not bloqueantes:
        return resumen.get("detalle", "")
    return "Faltan datos: " + "; ".join(f"{b['falta']} (lo produce: {b['lo_produce']})" for b in bloqueantes)


# Cada tipo de unidad → el NOMBRE de su corredor. Se resuelve por nombre al usarlo, no al importar: así
# una prueba puede reemplazar el corredor (p. ej. uno que muere a mitad) y el runner lo respeta.
_CORREDORES = {"script": "correr_script", "claude": "correr_claude", "meta_ejecucion": "correr_meta_ejecucion",
               "claude_grupo": "correr_grupo"}


# ── la unidad de escritura ────────────────────────────────────────────────────

@DBOS.step()
def paso_ejecutar(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Un solo comando (script o Claude), bajo el turno de escritura y con marca de inicio y fin."""
    carpeta = ruta(spec["run_dir"])
    marca = bitacora.Marca(carpeta, n)
    turno = (
        Cola(esperar=True, tope_s=TOPE_DE_ESPERA_DEL_TURNO_S, job_id=job_id)
        if spec["escribe"] else contextlib.nullcontext()
    )
    try:
        with turno:
            if marca.inicio_sin_fin():
                if not spec["idempotente"]:
                    return {"estado": "INTERRUMPIDO",
                            "detalle": "El proceso se cayó a mitad de este paso. No se repite solo: "
                                       "revisá el rastro y usá «Reintentar» para correrlo completo."}
                marca.cerrar_intento_roto(_ahora())
            marca.iniciar(_ahora())
            resumen = globals()[_CORREDORES[spec["tipo"]]](job_id, n, spec)
            marca.terminar(_ahora(), {"estado": resumen["estado"]})
            return resumen
    except SistemaOcupado as error:
        return {"estado": "FALLIDO", "detalle": f"No conseguí el turno de escritura: {error}"}


@DBOS.step()
def paso_tras_escribir(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Fuera de Claude Code los hooks no corren: el runner los suple después de toda escritura."""
    carpeta = ruta(spec["run_dir"])
    pasos: list[dict[str, Any]] = []
    estado = "EXITO"
    with Cola(esperar=True, tope_s=TOPE_DE_ESPERA_DEL_TURNO_S, job_id=job_id):
        for accion_id in acciones.tras_escribir():
            accion = acciones.por_id_para_el_runner(accion_id)
            argv = acciones.resolver(accion, {}, {})
            corrida = _correr_proceso(job_id, argv, f"{n}_tras_{accion_id}.log", carpeta, accion["tiempo_max_s"])
            pasos.append({"accion": accion_id, "codigo_salida": corrida["codigo_salida"]})
            if corrida["codigo_salida"] == 2 and accion_id == "sistema.barrido_csv":
                estado = "CSV_INVALIDO"
            elif corrida["codigo_salida"] != 0 and estado == "EXITO":
                estado = "FALLIDO"
    return {"estado": estado, "pasos": pasos}


@DBOS.workflow()
def wf_unidad(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    resultado = paso_ejecutar(job_id, n, spec)
    if spec["escribe"] and spec.get("tras", True):
        tras = paso_tras_escribir(job_id, n, spec)
        resultado = {**resultado, "tras": tras}
    return resultado


@DBOS.workflow()
def wf_limpieza(job_id: str, run_dir: str) -> dict[str, Any]:
    """Después de cancelar: una escritura a medias igual cambió el disco, así que `tras_escribir` corre."""
    return paso_tras_escribir(job_id, 0, {"run_dir": run_dir})


# ── el padre de las acciones de script ────────────────────────────────────────

def _sellar_meta(accion: dict[str, Any], valores: dict[str, Any], reservados: dict[str, str]) -> dict[str, Any]:
    """Todo lo que `wf_meta` necesita, derivado del manifiesto y resuelto UNA vez (al retomar se reusa)."""
    ordenes = accion.get("ordenes")
    if not ordenes:
        raise ValueError(f"«{accion['id']}» toca Meta pero no declara de dónde salen sus órdenes.")
    fase = re.match(r"F(\d)", accion.get("nodo") or "")
    cuenta_alias = valores.get("cuenta") or contratos.fila_de_producto(valores.get("producto_key", "")).get("cuenta_alias") or ""
    parametros = {
        **valores, "cuenta": cuenta_alias, "fase": fase.group(1) if fase else "1", "brazo": valores.get("brazo", "UNICO"),
        "evento": ordenes["evento"],
    }
    generador = acciones.por_id_para_el_runner(ordenes["generador"])
    verificador = acciones.por_id_para_el_runner(ordenes["verificador"])
    argv_paquete = acciones.resolver(generador, parametros, reservados)
    cuenta = next((c for c in contratos.cuentas() if c["cuenta_alias"] == cuenta_alias), {})
    return {
        "ordenes": ordenes, "parametros": parametros, "generador": generador, "verificador": verificador,
        "argv_paquete": argv_paquete, "argv_verificar": acciones.resolver(verificador, parametros, reservados),
        "snapshot": argv_paquete[argv_paquete.index("--snapshot") + 1],
        "imagenes": {
            momento: argv_paquete[argv_paquete.index(f"--imagenes-{momento}") + 1]
            for momento in ("antes", "despues") if f"--imagenes-{momento}" in argv_paquete
        },
        "cuenta_id": cuenta.get("cuenta_id", ""), "servidor": acciones.cargar().bloque["claude"]["servidor_meta"],
        "lectura": accion["herramientas_meta"]["lectura"], "escritura": accion["herramientas_meta"]["escritura"],
    }


def _ejecutor_textual(accion: dict[str, Any], producto: str | None) -> str:
    """El texto de `ejecutor` que ya devuelve `flujo.py`; si el nodo no es el actual, el del manifiesto."""
    if producto and accion.get("nodo"):
        flujo = contratos.flujo(producto)
        if acciones.es_el_mismo_nodo(accion["nodo"], flujo.get("nodo_actual", "")) and flujo.get("ejecutor"):
            return flujo["ejecutor"]
    return f"{accion['ejecutor_tipo']} `{accion.get('name')}`"


@DBOS.step()
def paso_sellar(job_id: str, accion_id: str, parametros: dict[str, Any]) -> dict[str, Any]:
    """Todo lo no determinista, de una vez: al retomar se usa esta copia, no el disco de hoy."""
    accion = acciones.por_id_para_el_runner(accion_id)
    valores = acciones.validar_parametros(accion, parametros)
    ahora = datetime.now().astimezone()
    iniciado = ahora.isoformat(timespec="seconds")
    carpeta = bitacora.carpeta_de_corrida(job_id, accion_id, valores.get("producto_key"), iniciado)
    run_dir = bitacora.ruta_relativa(carpeta)
    reservados = {
        "run_dir": run_dir, "job_id": job_id, "hoy": ahora.date().isoformat(),
        "tmp": str(Path(tempfile.gettempdir()) / f"vitalcom-{job_id[:8]}"),
    }
    producto = valores.get("producto_key")
    sello = {
        "job_id": job_id, "accion": accion, "parametros": valores,
        "ejecutor": _ejecutor_textual(accion, producto),
        "claude": acciones.cargar().bloque.get("claude")
        if accion["ejecutor_tipo"] in ("subagente", "skill") or accion.get("toca_meta") else None,
        "manifiesto_sha": acciones.sha_del_manifiesto(), "hoy": reservados["hoy"],
        "iniciado": iniciado, "run_dir": run_dir, "app_version": APP_VERSION,
        "argv": acciones.resolver(accion, valores, reservados) if accion["ejecutor_tipo"] == "script" else None,
        "meta": _sellar_meta(accion, valores, reservados) if accion.get("toca_meta") else None,
    }
    bitacora.reescribir_trabajo(carpeta, {"sello": sello, "estado": "ENCOLADO"})
    return sello


def spec_de_script(sello: dict[str, Any]) -> dict[str, Any]:
    accion = sello["accion"]
    return {
        "tipo": "script", "accion_id": accion["id"], "argv": sello["argv"],
        "idempotente": bool(accion.get("idempotente")), "escribe": accion["escribe"],
        "tiempo_max_s": accion["tiempo_max_s"], "salida": accion.get("salida", "texto"),
        "run_dir": sello["run_dir"],
    }


def prompt_del_nodo(sello: dict[str, Any]) -> str:
    """El «prompt mínimo» del nodo (manifiesto `acciones.claude.prompt_nodo`); la doctrina la carga CLAUDE.md."""
    producto = sello["parametros"].get("producto_key")
    lineas = [
        linea for linea in sello["claude"]["prompt_nodo"]
        # sin producto no hay nada que consultarle a flujo.py
        if producto or "flujo.py {producto_key}" not in linea
    ]
    valores = {
        "{job_id}": sello["job_id"], "{nodo}": sello["accion"].get("nodo") or sello["accion"]["id"],
        "{producto_key}": producto or "(acción global, sin producto)", "{ejecutor}": sello["ejecutor"],
    }
    texto = "\n".join(lineas)
    for marcador, valor in valores.items():
        texto = texto.replace(marcador, valor)
    return texto


def spec_de_claude(sello: dict[str, Any], *, resume: str | None = None, prompt: str | None = None) -> dict[str, Any]:
    """Una unidad de Claude. NUNCA lleva herramientas de Meta: esas solo las recibe `wf_meta`."""
    accion = sello["accion"]
    herramientas = list(dict.fromkeys([*sello["claude"]["herramientas_base"], *accion.get("herramientas", [])]))
    if any(h.startswith("mcp__") or "*" in h for h in herramientas):
        raise ValueError("wf_claude no recibe herramientas de MCP ni comodines.")
    return {
        "tipo": "claude", "accion_id": accion["id"], "idempotente": False, "escribe": accion["escribe"],
        "tiempo_max_s": accion["tiempo_max_s"], "run_dir": sello["run_dir"],
        "claude": {
            "prompt": prompt if prompt is not None else prompt_del_nodo(sello),
            "herramientas": herramientas, "presupuesto_usd": accion["presupuesto_usd"], "resume": resume,
        },
    }


@DBOS.step()
def paso_leer_flujo(sello: dict[str, Any]) -> dict[str, Any] | None:
    """El veredicto es de `flujo.py`: ¿el nodo de esta acción quedó cumplido?"""
    accion = sello["accion"]
    producto = sello["parametros"].get("producto_key")
    if not accion.get("nodo") or not producto:
        return None
    flujo = contratos.flujo(producto)
    nodo = next((x for x in flujo.get("nodos", []) if acciones.es_el_mismo_nodo(accion["nodo"], x["id"])), None)
    if nodo is None:
        return {"nodo": accion["nodo"], "cumplido": None, "estado": None, "falta_para_cumplir": []}
    es_el_actual = acciones.es_el_mismo_nodo(accion["nodo"], flujo.get("nodo_actual", ""))
    return {
        "nodo": nodo["id"], "cumplido": bool(nodo.get("cumplido")), "estado": nodo.get("estado"),
        "falta_para_cumplir": flujo.get("falta_para_cumplir", []) if es_el_actual else [],
    }


def estado_final(unidades: list[dict[str, Any]], situacion: dict[str, Any] | None) -> tuple[str, str]:
    """(estado, detalle). Pura: la cubren las pruebas sin correr nada."""
    for unidad in unidades:
        if unidad["estado"] in ("REAPROBACION_PEDIDA", "MEDIA_PEDIDA"):
            continue  # un paso intermedio: lo que pidió se resolvió (o no) en una unidad posterior
        if unidad["estado"] != "EXITO":
            return unidad["estado"], unidad.get("detalle", "")
        tras = unidad.get("tras") or {}
        if tras.get("estado") in ("CSV_INVALIDO", "FALLIDO"):
            detalle = ("El trabajo terminó, pero el barrido encontró un CSV inválido." if tras["estado"] == "CSV_INVALIDO"
                       else "El trabajo terminó, pero no se pudo regenerar el estado derivado.")
            return tras["estado"], detalle
    if unidades and unidades[-1].get("pregunta"):
        return "SIN_CUMPLIR", "Claude sigue esperando una respuesta después de varias preguntas."
    if situacion is not None and situacion.get("cumplido") is not True:
        return "SIN_CUMPLIR", "El paso terminó bien, pero flujo.py dice que el nodo sigue pendiente."
    return "EXITO", ""


@DBOS.step()
def paso_cerrar(sello: dict[str, Any], unidades: list[dict[str, Any]],
                situacion: dict[str, Any] | None) -> dict[str, Any]:
    estado, detalle = estado_final(unidades, situacion)
    resultado = {
        "job_id": sello["job_id"], "accion_id": sello["accion"]["id"], "estado": estado, "detalle": detalle,
        "unidades": unidades, "flujo": situacion, "terminado": _ahora(), "run_dir": sello["run_dir"],
    }
    carpeta = ruta(sello["run_dir"])
    previo = bitacora.leer_trabajo(carpeta) or {}
    bitacora.reescribir_trabajo(carpeta, {**previo, "estado": estado, "resultado": resultado})
    return resultado


@DBOS.workflow()
def wf_script(job_id: str, accion_id: str, parametros: dict[str, Any]) -> dict[str, Any]:
    sello = paso_sellar(job_id, accion_id, parametros)
    DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 1})
    unidad = _cola(COLA_ESCRITURA).enqueue(wf_unidad, job_id, 1, spec_de_script(sello)).get_result(
        polling_interval_sec=SONDEO_DE_RESULTADO_S)
    situacion = paso_leer_flujo(sello)
    resultado = paso_cerrar(sello, [unidad], situacion)
    DBOS.set_event("estado", {"estado": resultado["estado"]})
    return resultado


@DBOS.workflow()
def wf_claude(job_id: str, accion_id: str, parametros: dict[str, Any]) -> dict[str, Any]:
    """Un nodo = UNA llamada headless. La skill es dueña de su secuencia y de sus paralelos."""
    sello = paso_sellar(job_id, accion_id, parametros)
    DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 1})
    unidad = _cola(COLA_ESCRITURA).enqueue(wf_unidad, job_id, 1, spec_de_claude(sello)).get_result(
        polling_interval_sec=SONDEO_DE_RESULTADO_S)
    unidades = [unidad]
    vueltas = 0
    while unidad["estado"] == "EXITO" and unidad.get("pregunta") and vueltas < MAXIMO_DE_PREGUNTAS:
        vueltas += 1
        DBOS.set_event("pendiente", {"tipo": "pregunta", "n": vueltas, "texto": unidad["pregunta"]})
        DBOS.set_event("estado", {"estado": "ESPERA_RESPUESTA", "unidad": vueltas})
        respuesta = DBOS.recv(f"respuesta:{vueltas}", timeout_seconds=sello["claude"]["respuesta_max_horas"] * 3600)
        DBOS.set_event("pendiente", None)
        if respuesta is None:
            unidades.append({"estado": "CADUCADO", "detalle": "Nadie respondió la pregunta a tiempo."})
            break
        DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": vueltas + 1})
        continuacion = spec_de_claude(sello, resume=unidad["session_id"], prompt=respuesta["texto"])
        unidad = _cola(COLA_ESCRITURA).enqueue(wf_unidad, job_id, vueltas + 1, continuacion).get_result(
            polling_interval_sec=SONDEO_DE_RESULTADO_S)
        unidades.append(unidad)
    situacion = paso_leer_flujo(sello)
    resultado = paso_cerrar(sello, unidades, situacion)
    DBOS.set_event("estado", {"estado": resultado["estado"]})
    return resultado


# ── una skill DE A UN PASO: una llamada de Claude por etapa (diseño Hito 4, aprobado 18-sep-2026) ──
#
# La secuencia NO es de la app: los `pasos` del manifiesto son la `secuencia` de FLUJO.json agrupada
# (gen_app.py, regla V20). Cada paso corre en su propia llamada headless; los de un mismo grupo, a la
# vez. La salida textual de cada etapa se saca del registro (`claude.salida_de_subagente`) y queda en
# `<corrida>/etapas/NN_<etapa>.md`: de ahí la leen las etapas siguientes y las pantallas.

CARPETA_DE_ETAPAS = "etapas"
ARCHIVO_DE_PASOS = "pasos.json"
INPUTS_CONGELADOS = "00_INPUTS_CONGELADOS.md"
# Las columnas de la fila que SON insumos del operador. Las demás (cifras de costeo, estado,
# fase) las escribe la propia corrida: si entraran en la huella, retomar nunca sería posible.
COLUMNAS_INSUMO = ("producto_key", "nombre_display", "slug_carpeta", "costo_q", "moneda", "tasa",
                   "carpeta_transcripciones", "carpeta_media")


def _es_script(etapa: str) -> bool:
    return "/" in etapa


def salida_del_paso(n_paso: int, etapa: str) -> str:
    """`03_lavar_videos.md`, `06_etapa-2.md`: el archivo donde queda lo que devolvió la etapa."""
    nombre = Path(etapa).stem if _es_script(etapa) else etapa
    return f"{n_paso:02d}_{re.sub(r'[^A-Za-z0-9._-]+', '_', nombre)}.md"


def _unidad_del_paso(i: int, vuelta: int = 0) -> int:
    return 100 + 10 * i + vuelta


def huella_de_insumos(producto_key: str) -> str:
    """Los insumos congelados del producto (invariante 5): si cambian, no se retoma, se corre completo.

    Entra la fila (solo sus columnas de insumo), cada transcripción (nombre y contenido), la fila de
    `_DIM_ENVASE.csv` y los bytes del packshot que declara.
    """
    h = hashlib.sha256()
    fila = contratos.fila_de_producto(producto_key)
    h.update(json.dumps({c: fila.get(c, "") for c in COLUMNAS_INSUMO}, sort_keys=True).encode("utf-8"))
    carpeta = ruta("Ads", "1.2 Transcripcion videos", fila.get("carpeta_transcripciones") or producto_key)
    for archivo in sorted(carpeta.glob("*.txt")) if carpeta.is_dir() else []:
        h.update(archivo.name.encode("utf-8"))
        h.update(archivo.read_bytes())
    envase = ruta("PRODUCTOS", "_DIM_ENVASE.csv")
    if envase.is_file():
        with open(envase, encoding="utf-8", newline="") as archivo_csv:
            for fila_envase in csv.DictReader(archivo_csv):
                if fila_envase.get("producto_key") == producto_key:
                    h.update(json.dumps(fila_envase, sort_keys=True).encode("utf-8"))
                    packshot = ruta(*(fila_envase.get("packshot") or "").split("/")) if fila_envase.get("packshot") else None
                    if packshot is not None and packshot.is_file():
                        h.update(packshot.read_bytes())
    return h.hexdigest()


def leer_pasos(carpeta: Path) -> dict[str, Any] | None:
    try:
        return json.loads((carpeta / ARCHIVO_DE_PASOS).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


_lock_de_pasos = threading.Lock()


def _anotar_paso(carpeta: Path, indice: int, cambios: dict[str, Any], miembro: str | None = None) -> None:
    """Actualiza `pasos.json` (lo que la pantalla muestra del avance). Reescritura atómica."""
    with _lock_de_pasos:
        tablero = leer_pasos(carpeta) or {"pasos": []}
        paso = tablero["pasos"][indice]
        if miembro is None:
            paso.update(cambios)
        else:
            next(m for m in paso["miembros"] if m["etapa"] == miembro).update(cambios)
        bitacora.reescribir_en_corrida(carpeta, ARCHIVO_DE_PASOS, json.dumps(tablero, ensure_ascii=False, indent=1))


@DBOS.step()
def paso_preparar_pasos(sello: dict[str, Any], retomar_de: str | None) -> dict[str, Any]:
    """La huella de los insumos, la carpeta de etapas y —si se retoma— lo que se hereda.

    Se hereda SOLO si la corrida anterior es de la misma acción, el mismo producto y los mismos
    insumos, y solo los pasos que terminaron bien, en orden: el primero que no terminó bien y todo
    lo que sigue se corre de nuevo.
    """
    pasos = sello["accion"]["pasos"]
    producto = sello["parametros"]["producto_key"]
    carpeta = ruta(sello["run_dir"])
    huella = huella_de_insumos(producto)
    desde, detalle = 0, ""
    previo_carpeta = bitacora.buscar_corrida(retomar_de) if retomar_de else None
    previo = leer_pasos(previo_carpeta) if previo_carpeta else None
    if retomar_de and previo is None:
        detalle = "No encontré la corrida anterior: se corre completo."
    elif previo is not None and (previo.get("accion_id") != sello["accion"]["id"] or previo.get("producto_key") != producto):
        previo, detalle = None, "La corrida anterior es de otra acción u otro producto: se corre completo."
    elif previo is not None and previo.get("huella") != huella:
        previo, detalle = None, ("Los insumos del producto cambiaron desde la corrida anterior (costo, transcripciones o "
                                 "foto): se corre completo, sin heredar nada (invariante 5).")
    tablero = {"accion_id": sello["accion"]["id"], "producto_key": producto, "huella": huella,
               "retomado_de": retomar_de if previo else None, "pasos": []}
    heredando = previo is not None
    for i, grupo in enumerate(pasos):
        miembros = [{"etapa": e, "salida": salida_del_paso(i + 1, e), "estado": "PENDIENTE"} for e in grupo]
        estado = "PENDIENTE"
        if heredando:
            anterior = (previo.get("pasos") or [])[i] if i < len(previo.get("pasos") or []) else None
            archivos = [previo_carpeta / CARPETA_DE_ETAPAS / m["salida"] for m in miembros]
            if anterior and anterior.get("estado") in ("EXITO", "HEREDADO") and all(a.is_file() for a in archivos):
                for archivo in archivos:
                    bitacora.heredar_de_corrida(previo_carpeta, carpeta, f"{CARPETA_DE_ETAPAS}/{archivo.name}")
                for m in miembros:
                    m["estado"] = "HEREDADO"
                estado, desde = "HEREDADO", i + 1
            else:
                heredando = False
        tablero["pasos"].append({"n": i + 1, "etapas": grupo, "estado": estado, "miembros": miembros})
    if previo is not None and (previo_carpeta / CARPETA_DE_ETAPAS / INPUTS_CONGELADOS).is_file() and desde:
        bitacora.heredar_de_corrida(previo_carpeta, carpeta, f"{CARPETA_DE_ETAPAS}/{INPUTS_CONGELADOS}")
    if previo is not None and desde:
        detalle = f"Retoma desde el paso {desde + 1}: los pasos 1 a {desde} se heredan de la corrida anterior."
    bitacora.reescribir_en_corrida(carpeta, ARCHIVO_DE_PASOS, json.dumps(tablero, ensure_ascii=False, indent=1))
    return {"huella": huella, "desde": desde, "detalle": detalle}


def _prompt_del_paso(sello: dict[str, Any], i: int, etapa: str) -> str:
    pasos = sello["accion"]["pasos"]
    producto = sello["parametros"]["producto_key"]
    fila = contratos.fila_de_producto(producto)
    etapas_dir = f"{sello['run_dir']}/{CARPETA_DE_ETAPAS}"
    otras = [e for e in pasos[i] if e != etapa]
    previos = [INPUTS_CONGELADOS] + [salida_del_paso(j + 1, e) for j in range(i) for e in pasos[j]]
    valores = {
        "{job_id}": sello["job_id"], "{skill}": sello["accion"]["name"], "{producto_key}": producto,
        "{slug}": fila.get("slug_carpeta") or producto, "{etapa}": etapa, "{n}": str(i + 1), "{de}": str(len(pasos)),
        "{etapas_dir}": etapas_dir,
        "{lista_pasos}": " → ".join(" ∥ ".join(g) for g in pasos),
        "{paralelo}": (f" En paralelo, en otra llamada, corre `{'`, `'.join(otras)}`: no la invoques ni esperes su salida."
                       if otras else ""),
        "{previos}": ", ".join(f"{etapas_dir}/{p}" for p in previos),
    }
    texto = "\n".join(sello["claude"]["prompt_paso"])
    for marcador, valor in valores.items():
        texto = texto.replace(marcador, valor)
    return texto


def spec_de_paso(sello: dict[str, Any], i: int, *, solo: str | None = None, resume: str | None = None,
                 prompt: str | None = None, vuelta: int = 0) -> dict[str, Any]:
    """La unidad de un paso: una llamada de Claude por etapa del grupo, todas a la vez.

    Con `solo`/`resume`/`prompt` es la continuación de UNA etapa del grupo después de una pregunta.
    Nunca lleva herramientas de Meta (igual que `spec_de_claude`).
    """
    accion = sello["accion"]
    n = _unidad_del_paso(i, vuelta)
    base_claude = spec_de_claude(sello)["claude"]
    miembros = []
    for etapa in accion["pasos"][i]:
        if solo is not None and etapa != solo:
            continue
        miembros.append({
            "etapa": etapa, "es_script": _es_script(etapa), "salida": salida_del_paso(i + 1, etapa),
            "nombre_log": f"{n}_{Path(salida_del_paso(i + 1, etapa)).stem}.jsonl",
            "claude": {**base_claude, "prompt": prompt if prompt is not None else _prompt_del_paso(sello, i, etapa),
                       "resume": resume},
        })
    return {"tipo": "claude_grupo", "accion_id": accion["id"], "idempotente": False, "escribe": accion["escribe"],
            "tras": False, "tiempo_max_s": accion["tiempo_max_s"], "run_dir": sello["run_dir"], "indice": i,
            "miembros": miembros}


def _correr_miembro(job_id: str, n: int, spec: dict[str, Any], miembro: dict[str, Any]) -> dict[str, Any]:
    carpeta = ruta(spec["run_dir"])
    _anotar_paso(carpeta, spec["indice"], {"estado": "CORRIENDO", "log": miembro["nombre_log"]}, miembro["etapa"])
    resumen = correr_claude(job_id, n, {**spec, "claude": miembro["claude"]}, miembro["nombre_log"])
    resumen = {"etapa": miembro["etapa"], "salida": miembro["salida"], **resumen}
    if resumen["estado"] == "EXITO" and not resumen.get("pregunta"):
        # La etapa pudo correr ANTES de una pregunta (en la primera vuelta) y la continuación solo cerrar:
        # se lee el registro de todas las vueltas de este paso, en orden, y vale la última salida.
        propia = Path(miembro["nombre_log"]).stem.split("_", 1)[1]
        vueltas = sorted((x for x in carpeta.glob(f"*_{propia}.jsonl")
                          if x.name.split("_", 1)[0].isdigit() and int(x.name.split("_", 1)[0]) // 10 == n // 10),
                         key=lambda x: int(x.name.split("_", 1)[0]))
        lineas = [linea for x in vueltas for linea in x.read_text(encoding="utf-8", errors="replace").splitlines()]
        texto = resumen.get("texto_final") if miembro["es_script"] else claude.salida_de_subagente(lineas, miembro["etapa"])
        if texto:
            bitacora.reescribir_en_corrida(carpeta, f"{CARPETA_DE_ETAPAS}/{miembro['salida']}", texto + "\n")
        elif not (carpeta / CARPETA_DE_ETAPAS / miembro["salida"]).is_file():
            resumen = {**resumen, "estado": "FALLIDO",
                       "detalle": f"Claude terminó sin invocar `{miembro['etapa']}`: no hay salida de la etapa que guardar."}
    visible = "ESPERA_RESPUESTA" if resumen["estado"] == "EXITO" and resumen.get("pregunta") else resumen["estado"]
    _anotar_paso(carpeta, spec["indice"], {
        "estado": visible, "detalle": resumen.get("detalle", ""), "pregunta": resumen.get("pregunta"),
        "costo_equivalente_usd": resumen.get("costo_equivalente_usd"), "duracion_s": resumen.get("duracion_s"),
    }, miembro["etapa"])
    return resumen


def _contexto_de_la_pregunta(miembro: dict[str, Any]) -> str:
    texto = miembro.get("texto_final") or ""
    return texto[:texto.rfind(claude.MARCA_DE_PREGUNTA)].strip()[-3000:] if claude.MARCA_DE_PREGUNTA in texto else ""


def correr_grupo(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Las etapas de un paso, cada una en su llamada y todas a la vez. Veredicto: el peor de los miembros."""
    carpeta = ruta(spec["run_dir"])
    _anotar_paso(carpeta, spec["indice"], {"estado": "CORRIENDO"})
    resultados: list[dict[str, Any] | None] = [None] * len(spec["miembros"])

    def _uno(k: int) -> None:
        resultados[k] = _correr_miembro(job_id, n, spec, spec["miembros"][k])

    hilos = [threading.Thread(target=_uno, args=(k,), daemon=True) for k in range(len(spec["miembros"]))]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    miembros = [r or {"estado": "FALLIDO", "detalle": "la etapa no devolvió resultado"} for r in resultados]
    malo = next((m for m in miembros if m["estado"] != "EXITO"), None)
    pregunta = next((m for m in miembros if m.get("pregunta")), None)
    tablero = leer_pasos(carpeta) or {"pasos": []}
    estados = [m["estado"] for m in tablero["pasos"][spec["indice"]]["miembros"]]
    _anotar_paso(carpeta, spec["indice"], {
        "estado": malo["estado"] if malo else ("ESPERA_RESPUESTA" if "ESPERA_RESPUESTA" in estados else "EXITO")})
    return {
        "estado": malo["estado"] if malo else "EXITO",
        "detalle": f"{malo['etapa']}: {malo.get('detalle', '')}" if malo else "",
        "miembros": miembros,
        "pregunta": pregunta.get("pregunta") if pregunta else None,
        "etapa_que_pregunta": pregunta["etapa"] if pregunta else None,
        "session_id": pregunta.get("session_id") if pregunta else None,
        # lo que la etapa dijo ANTES de preguntar (el porqué de un NO APTO): sin esto se decide a ciegas
        "contexto": _contexto_de_la_pregunta(pregunta) if pregunta else None,
    }


@DBOS.workflow()
def wf_pasos(job_id: str, accion_id: str, parametros: dict[str, Any], retomar_de: str | None = None) -> dict[str, Any]:
    """Una skill de varias etapas, una llamada de Claude por etapa (los grupos, en paralelo)."""
    sello = paso_sellar(job_id, accion_id, parametros)
    DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 1})
    inicio = paso_preparar_pasos(sello, retomar_de)
    pasos = sello["accion"]["pasos"]
    unidades: list[dict[str, Any]] = []
    preguntas = 0
    for i in range(inicio["desde"], len(pasos)):
        DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": _unidad_del_paso(i),
                                  "paso": i + 1, "de": len(pasos), "etapas": pasos[i]})
        unidad = _unidad_de(sello, _unidad_del_paso(i), spec_de_paso(sello, i))
        vuelta = 0
        while unidad["estado"] == "EXITO" and unidad.get("pregunta") and vuelta < MAXIMO_DE_PREGUNTAS:
            vuelta += 1
            preguntas += 1
            DBOS.set_event("pendiente", {"tipo": "pregunta", "n": preguntas, "texto": unidad["pregunta"],
                                         "etapa": unidad["etapa_que_pregunta"], "contexto": unidad.get("contexto")})
            DBOS.set_event("estado", {"estado": "ESPERA_RESPUESTA", "unidad": _unidad_del_paso(i, vuelta)})
            respuesta = DBOS.recv(f"respuesta:{preguntas}", timeout_seconds=sello["claude"]["respuesta_max_horas"] * 3600)
            DBOS.set_event("pendiente", None)
            if respuesta is None:
                unidad = {**unidad, "estado": "CADUCADO", "detalle": "Nadie respondió la pregunta a tiempo."}
                break
            DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": _unidad_del_paso(i, vuelta),
                                      "paso": i + 1, "de": len(pasos), "etapas": pasos[i]})
            etapa = unidad["etapa_que_pregunta"]
            continuacion = _unidad_de(sello, _unidad_del_paso(i, vuelta), spec_de_paso(
                sello, i, solo=etapa, resume=unidad["session_id"], vuelta=vuelta,
                prompt=f"{respuesta['texto']}\n\n(Seguí SOLO con el paso de `{etapa}`.)\nPASO_ETAPA: {etapa}"))
            otros = [m for m in unidad["miembros"] if m["etapa"] != unidad["etapa_que_pregunta"]]
            pendientes = [m for m in otros if m.get("pregunta")]
            unidad = {**continuacion, "miembros": otros + continuacion["miembros"]}
            if continuacion["estado"] == "EXITO" and not continuacion.get("pregunta") and pendientes:
                siguiente = pendientes[0]
                unidad.update(pregunta=siguiente["pregunta"], etapa_que_pregunta=siguiente["etapa"],
                              session_id=siguiente["session_id"], contexto=_contexto_de_la_pregunta(siguiente))
        unidades.append(unidad)
        if unidad["estado"] != "EXITO" or unidad.get("pregunta"):
            break
    unidades.insert(0, {"estado": "EXITO", "detalle": inicio["detalle"], "desde": inicio["desde"]})
    limpieza = _cola(COLA_ESCRITURA).enqueue(wf_limpieza, job_id, sello["run_dir"]).get_result(
        polling_interval_sec=SONDEO_DE_RESULTADO_S)
    unidades[-1] = {**unidades[-1], "tras": limpieza}
    situacion = paso_leer_flujo(sello)
    resultado = paso_cerrar(sello, unidades, situacion)
    DBOS.set_event("estado", {"estado": resultado["estado"]})
    return resultado


@DBOS.step()
def paso_firmar_orden(sello: dict[str, Any], paquete: dict[str, Any], orden_id: int) -> dict[str, Any]:
    """La orden que el operador va a ver y aprobar, con su huella. El generador no aporta la hora."""
    meta = sello["meta"]
    orden = {
        "tipo": meta["ordenes"]["tipo"], "producto": sello["parametros"].get("producto_key"),
        "fase": meta["parametros"]["fase"], "brazo": meta["parametros"]["brazo"],
        "cuenta": sello["parametros"].get("cuenta"), "llamadas": _llamadas_de(paquete),
        "manifiesto": paquete.get("manifiesto"),
    }
    if paquete.get("media"):
        # qué archivo de disco es cada hash: sin esto, el operador aprueba hashes que no puede reconocer
        orden["imagenes"] = [
            {"archivo": p["archivo"], "nombre_en_biblioteca": p["nombre_en_biblioteca"], "image_hash": p["image_hash"]}
            for p in paquete["media"]["piezas"]
        ]
    return {"orden_id": orden_id, "hash": huella_de_la_orden(orden), "orden": orden,
            "caduca_horas": meta["ordenes"]["caduca_horas"]}


@DBOS.step()
def paso_sellar_aprobacion(sello: dict[str, Any], firmada: dict[str, Any], aprobacion: dict[str, Any]) -> dict[str, Any]:
    """Cuándo se aprobó y hasta cuándo vale. Una aprobación caduca: no se ejecuta sobre un estado viejo."""
    ahora = datetime.now().astimezone()
    valida_hasta = ahora + timedelta(hours=firmada["caduca_horas"])
    registro = {"orden_id": firmada["orden_id"], "hash": firmada["hash"], "decision": "APROBADA",
                "aprobada_el": ahora.isoformat(timespec="seconds"),
                "valida_hasta": valida_hasta.isoformat(timespec="seconds"), "nota": aprobacion.get("nota", "")}
    bitacora.registrar_aprobacion(ruta(sello["run_dir"]), {**registro, "orden": firmada["orden"]})
    return registro


def _unidad_de(sello: dict[str, Any], n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Una unidad en la cola de escritura, y espera su resultado."""
    return _cola(COLA_ESCRITURA).enqueue(wf_unidad, sello["job_id"], n, spec).get_result(
        polling_interval_sec=SONDEO_DE_RESULTADO_S)


def _spec_de_snapshot(sello: dict[str, Any]) -> dict[str, Any]:
    """Claude con SOLO lectura de Meta. Ninguna herramienta de escritura llega hasta acá."""
    accion, meta = sello["accion"], sello["meta"]
    bloque = sello["claude"]
    prompt = PROMPT_SNAPSHOT.format(
        job_id=sello["job_id"], cuenta=sello["parametros"].get("cuenta"), cuenta_id=meta["cuenta_id"],
        snapshot=meta["snapshot"], marca=MARCA_SIN_MCP)
    herramientas = [*bloque["herramientas_base"], *[_nombre_de_meta(meta["servidor"], t) for t in meta["lectura"]]]
    return {
        "run_dir": sello["run_dir"], "tiempo_max_s": accion["tiempo_max_s"],
        "claude": {"prompt": prompt, "herramientas": herramientas, "presupuesto_usd": accion["presupuesto_usd"],
                   "resume": None},
    }


def spec_de_lectura(sello: dict[str, Any], n: int) -> dict[str, Any]:
    """La unidad M1/M4: un snapshot fresco. Solo escribe el volcado, no un CSV: no dispara `tras_escribir`."""
    accion = sello["accion"]
    base_de_snapshot = _spec_de_snapshot(sello)
    return {"tipo": "claude", "accion_id": accion["id"], "idempotente": False, "escribe": ["Ads/_INGESTA/META/"],
            "tras": False, "tiempo_max_s": accion["tiempo_max_s"], "run_dir": sello["run_dir"],
            "claude": base_de_snapshot["claude"], "nombre_log": f"{n}_snapshot.jsonl", "detecta_sin_mcp": True}


def solo_falta_media(resultado: dict[str, Any]) -> bool:
    """El generador salió con bloqueos y TODOS son de media: lo que falta es que el operador suba."""
    bloqueantes = (resultado.get("json") or {}).get("bloqueantes") or []
    return resultado["estado"] == "FALLIDO" and bool(bloqueantes) and all(b.get("ambito") == "media" for b in bloqueantes)


def spec_de_imagenes(sello: dict[str, Any], n: int, momento: str, paquete: dict[str, Any]) -> dict[str, Any]:
    """Leer la biblioteca de imágenes de la cuenta: Claude con UNA herramienta de Meta, `ads_get_ad_images`.

    Busca por el nombre BASE de cada archivo: `name` de Meta es «contiene», así que trae también los
    `_V2`, `_V3`… que ya existan (antes) y el que el operador acaba de subir (después). Después busca
    además cada nombre elegido, exacto: si `name` resultara exacto y no «contiene», igual lo encuentra.
    """
    accion, meta = sello["accion"], sello["meta"]
    piezas = paquete["media"]["piezas"]
    buscar = sorted({os.path.splitext(p["archivo"])[0] for p in piezas if p.get("archivo")}
                    | {p["nombre_en_biblioteca"] for p in piezas if p.get("nombre_en_biblioteca")})
    prompt = PROMPT_IMAGENES.format(
        job_id=sello["job_id"], cuenta_id=meta["cuenta_id"], destino=meta["imagenes"][momento],
        buscar=json.dumps(buscar, ensure_ascii=False))
    herramientas = [*sello["claude"]["herramientas_base"], _nombre_de_meta(meta["servidor"], "ads_get_ad_images")]
    return {"tipo": "claude", "accion_id": accion["id"], "idempotente": True, "escribe": [], "tras": False,
            "tiempo_max_s": accion["tiempo_max_s"], "run_dir": sello["run_dir"], "nombre_log": f"{n}_imagenes_{momento}.jsonl",
            "claude": {"prompt": prompt, "herramientas": herramientas, "presupuesto_usd": accion["presupuesto_usd"],
                       "resume": None}}


@DBOS.step()
def paso_preparar_subida(sello: dict[str, Any], paquete: dict[str, Any], vuelta: int) -> dict[str, Any]:
    """Lo que el operador tiene que subir: cada pieza copiada con su nombre EXACTO en una carpeta del trabajo.

    Así sube arrastrando la carpeta entera, sin renombrar a mano (un nombre mal tipeado no se encuentra).
    """
    media = paquete["media"]
    carpeta = ruta(sello["run_dir"]) / CARPETA_DE_SUBIDA
    archivos = []
    for pieza in media["piezas"]:
        extension = os.path.splitext(pieza["archivo"])[1]
        destino = f"{pieza['nombre_en_biblioteca']}{extension}"
        if pieza["estado"] != "OK" and pieza.get("ruta") and ruta(pieza["ruta"]).is_file():
            bitacora.copiar_para_subir(ruta(sello["run_dir"]), CARPETA_DE_SUBIDA, ruta(pieza["ruta"]), destino)
        archivos.append({"archivo": pieza["archivo"], "nombre_en_biblioteca": pieza["nombre_en_biblioteca"],
                         "archivo_a_subir": destino, "estado": pieza["estado"], "hashes": pieza.get("hashes", [])})
    return {"tipo": "subida_media", "vuelta": vuelta, "cuenta": media["cuenta_alias"], "cuenta_id": media["cuenta_id"],
            "carpeta": str(carpeta), "archivos": archivos,
            "faltan": [b["falta"] for b in paquete.get("bloqueantes", [])]}


def _pedir_subida(pedido: dict[str, Any], horas: float) -> dict[str, Any] | None:
    """Muestra qué subir y espera el «ya las subí». None = nadie avisó a tiempo."""
    DBOS.set_event("estado", {"estado": "ESPERA_MEDIA", "unidad": pedido["vuelta"]})
    DBOS.set_event("pendiente", pedido)
    aviso = DBOS.recv(f"media:{pedido['vuelta']}", timeout_seconds=horas * 3600)
    DBOS.set_event("pendiente", None)
    return aviso


def _media_de_la_biblioteca(sello: dict[str, Any], unidades: list[dict[str, Any]]) -> None:
    """--media biblioteca: leer la biblioteca, elegir los nombres, esperar al operador y leer los hashes.

    Deja en `unidades[-1]` el paquete regenerado: EXITO con cada hash literal, o FALLIDO con lo que falta.
    Nada de esto escribe en Meta: la única herramienta de Meta que se usa acá es `ads_get_ad_images`.
    """
    _media_pedida(unidades)
    unidades.append(_unidad_de(sello, 21, spec_de_imagenes(sello, 21, "antes", unidades[-1]["json"])))
    if unidades[-1]["estado"] != "EXITO":
        return
    unidades.append(_unidad_de(sello, 22, spec_del_paquete(sello)))
    if not _volcado_leido(unidades, "listado_antes"):
        return
    horas = sello["claude"]["respuesta_max_horas"]
    vuelta = 0
    while solo_falta_media(unidades[-1]) and vuelta < MAXIMO_DE_VUELTAS_DE_MEDIA:
        vuelta += 1
        _media_pedida(unidades)
        pedido = paso_preparar_subida(sello, unidades[-1]["json"], vuelta)
        if _pedir_subida(pedido, horas) is None:
            unidades.append({"estado": "CADUCADO", "detalle": "Nadie avisó que subió las imágenes a tiempo: no se llamó a nada."})
            return
        DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 30 + 2 * vuelta})
        n_lectura = 30 + 2 * vuelta
        unidades.append(_unidad_de(sello, n_lectura, spec_de_imagenes(sello, n_lectura, "despues", unidades[-1]["json"])))
        if unidades[-1]["estado"] != "EXITO":
            return
        unidades.append(_unidad_de(sello, n_lectura + 1, spec_del_paquete(sello)))
        if not _volcado_leido(unidades, "listado_despues"):
            return


def _media_pedida(unidades: list[dict[str, Any]]) -> None:
    """Ese paquete esperaba imágenes y se le pidieron: no es la falla del trabajo, es un paso intermedio."""
    unidades[-1] = {**unidades[-1], "estado": "MEDIA_PEDIDA"}


def _volcado_leido(unidades: list[dict[str, Any]], cual: str) -> bool:
    """Claude dijo que leyó la biblioteca: el paquete regenerado confirma si el volcado está en disco."""
    ultima = unidades[-1]
    media = (ultima.get("json") or {}).get("media") or {}
    if ultima["estado"] == "EXITO" or media.get(cual):
        return True
    if solo_falta_media(ultima):
        unidades[-1] = {**ultima, "detalle": "No quedó guardada la lectura de la biblioteca de imágenes de Meta: "
                                             "reintentá. No se llamó a nada que escriba."}
    return False


def spec_del_paquete(sello: dict[str, Any]) -> dict[str, Any]:
    meta = sello["meta"]
    return {"tipo": "script", "accion_id": meta["generador"]["id"], "argv": meta["argv_paquete"],
            "idempotente": True, "escribe": [], "tiempo_max_s": meta["generador"]["tiempo_max_s"],
            "salida": "json", "run_dir": sello["run_dir"]}


def spec_de_ejecucion(sello: dict[str, Any], firmada: dict[str, Any], aprobacion: dict[str, Any]) -> dict[str, Any]:
    """M3. Todo lo que necesita viaja en el spec: el paso no vuelve a leer el manifiesto."""
    accion, meta = sello["accion"], sello["meta"]
    return {
        "tipo": "meta_ejecucion", "accion_id": accion["id"], "idempotente": False, "tras": False,
        "escribe": ["Ads/_INGESTA/META/"], "tiempo_max_s": accion["tiempo_max_s"], "run_dir": sello["run_dir"],
        "snapshot_claude": _spec_de_snapshot(sello)["claude"], "argv_paquete": meta["argv_paquete"],
        "tiempo_paquete_s": meta["generador"]["tiempo_max_s"], "orden": firmada["orden"], "hash": firmada["hash"],
        "valida_hasta": aprobacion["valida_hasta"], "servidor": meta["servidor"], "lectura": meta["lectura"],
        "escritura": meta["escritura"], "presupuesto_usd": accion["presupuesto_usd"],
    }


def spec_de_verificacion(sello: dict[str, Any]) -> dict[str, Any]:
    meta = sello["meta"]
    return {"tipo": "script", "accion_id": meta["verificador"]["id"], "argv": meta["argv_verificar"],
            "idempotente": True, "escribe": meta["verificador"]["escribe"],
            "tiempo_max_s": meta["verificador"]["tiempo_max_s"], "salida": "texto", "run_dir": sello["run_dir"]}


def firma_del_evento(job_id: str, orden_id: int) -> str:
    return f"app job={job_id} orden={orden_id}"


def _evento_ya_registrado(firma: str) -> bool:
    """`registrar_evento.py` no deduplica: si el proceso murió después de escribir, la firma ya está."""
    archivo = ruta("PRODUCTOS", "_EVENTOS.csv")
    return archivo.is_file() and firma in archivo.read_text(encoding="utf-8", errors="replace")


@DBOS.step()
def paso_preparar_evento(sello: dict[str, Any], orden_id: int) -> dict[str, Any] | None:
    """M5: el evento del lanzamiento, firmado con el trabajo y la orden. None si ya está escrito."""
    meta = sello["meta"]
    firma = firma_del_evento(sello["job_id"], orden_id)
    if _evento_ya_registrado(firma):
        return None
    registrador = acciones.por_id_para_el_runner("evento.registrar")
    fuente_nombre = sello["accion"].get("name") or "activar-meta"
    tipo_ord = meta["ordenes"].get("tipo")
    if tipo_ord == "paquete_publicacion":
        motivo = "Publicación por la app: todo nació PAUSED"
        evento_tipo = "LANZAMIENTO"
    elif tipo_ord == "decision":
        motivo = "Decisión diaria del motor aplicada tras confirmación del operador"
        evento_tipo = "PAUSA"
    else:
        motivo = "Activación FASE 1 por la app a las 4 AM"
        evento_tipo = meta["ordenes"].get("evento", "LANZAMIENTO")
    valores = {"producto_key": sello["parametros"]["producto_key"], "evento": evento_tipo,
               "motivo": motivo, "fuente": f"{fuente_nombre} · confirmado operador · {firma}"}
    if sello["parametros"].get("cuenta") or meta["parametros"].get("cuenta"):
        valores["cuenta"] = sello["parametros"].get("cuenta") or meta["parametros"].get("cuenta")
    return {"tipo": "script", "accion_id": registrador["id"], "argv": acciones.resolver(registrador, valores, {}),
            "idempotente": False, "escribe": registrador["escribe"], "tiempo_max_s": registrador["tiempo_max_s"],
            "salida": "texto", "run_dir": sello["run_dir"]}


@DBOS.step()
def paso_registrar_rechazo(sello: dict[str, Any], firmada: dict[str, Any], aprobacion: dict[str, Any]) -> None:
    bitacora.registrar_aprobacion(ruta(sello["run_dir"]), {
        "orden_id": firmada["orden_id"], "hash": firmada["hash"], "decision": "RECHAZADA",
        "nota": aprobacion.get("nota", "")})


def _pedir_aprobacion(orden_id: int, firmada: dict[str, Any]) -> dict[str, Any] | None:
    """Publica la orden y espera al operador. None = nadie aprobó ni rechazó a tiempo."""
    DBOS.set_event("pendiente", {"tipo": "aprobacion", **firmada})
    DBOS.set_event("estado", {"estado": "ESPERA_APROBACION", "unidad": orden_id})
    respuesta = None
    for _intento in range(MAXIMO_DE_MENSAJES_AJENOS):
        respuesta = DBOS.recv(f"aprobacion:{orden_id}", timeout_seconds=firmada["caduca_horas"] * 3600)
        if respuesta is None or respuesta.get("hash") == firmada["hash"]:
            break  # un mensaje sobre OTRA orden no aprueba esta: se ignora y se sigue esperando
    DBOS.set_event("pendiente", None)
    return respuesta


@DBOS.workflow()
def wf_meta(job_id: str, accion_id: str, parametros: dict[str, Any]) -> dict[str, Any]:
    """Publicar en Meta: snapshot → paquete → [imágenes subidas por el operador] → aprobación por hash →
    ejecución → verificación → evento.

    Ninguna llamada de ESCRITURA ocurre sin una aprobación sellada antes (`paso_sellar_aprobacion`)
    y ninguna herramienta de escritura llega a un paso que no sea el de ejecución.
    """
    sello = paso_sellar(job_id, accion_id, parametros)
    DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 1})
    unidades = [_unidad_de(sello, 1, spec_de_lectura(sello, 1))]
    if unidades[-1]["estado"] == "EXITO":
        unidades.append(_unidad_de(sello, 2, spec_del_paquete(sello)))
    if solo_falta_media(unidades[-1]):
        _media_de_la_biblioteca(sello, unidades)
    paquete = unidades[-1].get("json") if unidades[-1]["estado"] == "EXITO" else None
    orden_id = 0
    sigue = unidades[-1]["estado"] == "EXITO" and paquete is not None
    while sigue:
        orden_id += 1
        firmada = paso_firmar_orden(sello, paquete, orden_id)
        aprobacion = _pedir_aprobacion(orden_id, firmada)
        sigue = False
        if aprobacion is None:
            unidades.append({"estado": "CADUCADO", "detalle": "Nadie aprobó la orden a tiempo: no se llamó a nada."})
        elif aprobacion.get("decision") != "APROBADA":
            paso_registrar_rechazo(sello, firmada, aprobacion)
            unidades.append({"estado": "RECHAZADO", "detalle": "El operador rechazó la orden: no se llamó a nada."})
        else:
            sellada = paso_sellar_aprobacion(sello, firmada, aprobacion)
            DBOS.set_event("estado", {"estado": "CORRIENDO", "unidad": 3})
            unidades.append(_unidad_de(sello, 3, spec_de_ejecucion(sello, firmada, sellada)))
            if unidades[-1]["estado"] == "PIDE_REAPROBACION":
                if orden_id < MAXIMO_DE_APROBACIONES:
                    paquete = unidades[-1]["paquete"]
                    unidades[-1] = {**unidades[-1], "estado": "REAPROBACION_PEDIDA"}
                    sigue = True
                else:
                    unidades[-1] = {**unidades[-1], "estado": "FALLIDO",
                                    "detalle": "La orden cambió tres veces mientras se ejecutaba: no se sigue."}
    if unidades[-1]["estado"] == "EXITO":
        unidades.append(_unidad_de(sello, 4, spec_de_lectura(sello, 4)))
    if unidades[-1]["estado"] == "EXITO":
        unidades.append(_unidad_de(sello, 5, spec_de_verificacion(sello)))
    evento = paso_preparar_evento(sello, orden_id) if unidades[-1]["estado"] == "EXITO" else None
    if evento is not None:
        unidades.append(_unidad_de(sello, 6, evento))
    situacion = paso_leer_flujo(sello)
    resultado = paso_cerrar(sello, unidades, situacion)
    DBOS.set_event("estado", {"estado": resultado["estado"]})
    return resultado


# ── lo que usan los endpoints ─────────────────────────────────────────────────

_PADRES = {"script": wf_script, "subagente": wf_claude, "skill": wf_claude}


def cancelar(job_id: str) -> None:
    """Marca el trabajo como cancelado (el subproceso vivo lo ve en su próximo latido y se corta) y lo cancela en DBOS."""
    _cancelados.add(job_id)
    DBOS.cancel_workflow(job_id, cancel_children=True)


def limpiar_tras_cancelar(job_id: str, run_dir: str) -> None:
    _cola(COLA_ESCRITURA).enqueue(wf_limpieza, job_id, run_dir)


def existe(job_id: str) -> bool:
    return bool(DBOS.list_workflows(workflow_ids=[job_id], load_input=False, load_output=False))


def _activo_de(clave: str) -> str | None:
    for estado in DBOS.list_workflows(queue_name=COLA_TRABAJOS, status=["ENQUEUED", "PENDING"],
                                      load_input=False, load_output=False):
        if getattr(estado, "deduplication_id", None) == clave:
            return estado.workflow_id
    return None


def encolar(accion: dict[str, Any], valores: dict[str, Any], job_id: str,
            retomar_de: str | None = None) -> tuple[str, bool]:
    """Pone el trabajo en la cola `trabajos`. Devuelve (job_id, repetido).

    `retomar_de` solo vale para una acción con `pasos`: el trabajo nuevo hereda los pasos que el
    anterior terminó bien, si los insumos no cambiaron (`paso_preparar_pasos`).
    """
    if existe(job_id):
        return job_id, True
    if accion.get("pasos"):
        padre = wf_pasos
    else:
        padre = wf_meta if accion.get("toca_meta") else _PADRES.get(accion["ejecutor_tipo"])
    if padre is None:
        raise ErrorDeAccion(501, "RUNNER_PENDIENTE", "Este tipo de acción todavía no está conectado al runner.")
    clave = valores.get("producto_key") or accion["id"]
    try:
        with SetWorkflowID(job_id), SetEnqueueOptions(deduplication_id=clave):
            if padre is wf_pasos:
                _cola(COLA_TRABAJOS).enqueue(padre, job_id, accion["id"], valores, retomar_de)
            else:
                _cola(COLA_TRABAJOS).enqueue(padre, job_id, accion["id"], valores)
    except DBOSQueueDeduplicatedError as error:
        raise ErrorDeAccion(
            409, "YA_EN_CURSO", f"Ya hay un trabajo en curso para «{clave}»: esperá a que termine.",
            job_id=_activo_de(clave),
        ) from error
    return job_id, False


def responder(job_id: str, n: int, texto: str) -> None:
    """La respuesta del operador a la pregunta `n` de Claude (el workflow la espera con `recv`)."""
    DBOS.send(job_id, {"texto": texto}, topic=f"respuesta:{n}")


def avisar_media_subida(job_id: str, vuelta: int) -> None:
    """El «ya las subí» del operador (el workflow lo espera con `recv`)."""
    DBOS.send(job_id, {"subidas": True}, topic=f"media:{vuelta}")


def enviar_aprobacion(job_id: str, orden_id: int, decision: str, huella: str, nota: str = "") -> None:
    """La decisión del operador sobre UNA orden, atada a la huella de lo que vio."""
    DBOS.send(job_id, {"decision": decision, "hash": huella, "nota": nota}, topic=f"aprobacion:{orden_id}")


def publicado(job_id: str, clave: str) -> Any:
    """Lo último que el workflow publicó con `set_event` (`estado` o `pendiente`), sin esperar."""
    return DBOS.get_event(job_id, clave, timeout_seconds=0)


def esperar_resultado(job_id: str, tope_s: float) -> dict[str, Any] | None:
    """El resultado del trabajo si termina antes del tope; si no, None (sigue corriendo)."""
    limite = time.monotonic() + tope_s
    while time.monotonic() < limite:
        estados = DBOS.list_workflows(workflow_ids=[job_id], load_input=False, load_output=False)
        if estados and estados[0].status in ("SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"):
            return DBOS.retrieve_workflow(job_id).get_result(polling_interval_sec=SONDEO_DE_RESULTADO_S)
        time.sleep(SONDEO_DE_RESULTADO_S)
    return None


# ── Ciclo diario y ejecución programada (Hito 5) ──────────────────────────────

PASOS_CICLO_NOCTURNO = [
    "nodo.ciclo.datos",
    "ciclo.bajar_meta",
    "nodo.ciclo.motor",
    "sistema.refrescar_flujo",
    "sistema.gen_app",
]

CRON_NOCTURNO = os.environ.get("VITALCOM_CRON_NOCTURNO", "0 2 * * *")


def ejecutar_ciclo_nocturno(job_id: str | None = None) -> dict[str, Any]:
    """Cadena nocturna de 5 pasos:
    recopilar_lucidsales.py -> bajar_meta_insights -> gen_decisiones -> flujo --todo -> gen_app.
    Cada paso es una acción declarada. Si un paso falla, el siguiente no corre.

    `nodo.ciclo.datos` es `ejecutor_tipo: script` desde T4 (26-sep-2026): antes era `skill`
    (una sesión de Claude para dos comandos deterministas) y corría por `wf_claude`; ahora
    `_PADRES` la enruta por `wf_script`, sin ningún caso especial acá — el mapeo genérico por
    `ejecutor_tipo` ya alcanza.

    Excepción (T1b, 22-sep-2026): `ciclo.bajar_meta` puede fallar PARCIAL (código de salida 2 —
    al menos una cuenta de Meta OK, al menos una caída; ver bajar_meta_insights.py). Una falla de
    UNA cuenta (ej. permiso denegado en GTR13) no puede tumbar gen_decisiones/flujo/gen_app para
    TODOS los productos: ese paso se registra como aviso y la cadena sigue (mismo precedente que
    `codigo_salida == 2 and accion_id == "sistema.barrido_csv"` en paso_tras_escribir, arriba).
    Un código de salida 1 de `ciclo.bajar_meta` (todas las cuentas fallaron) sí detiene la cadena,
    igual que cualquier otro paso.
    """
    import uuid
    jid = job_id or uuid.uuid4().hex
    resultados: list[dict[str, Any]] = []
    avisos: list[dict[str, Any]] = []

    for i, a_id in enumerate(PASOS_CICLO_NOCTURNO, 1):
        acc = acciones.por_id_para_el_runner(a_id)
        sub_id = f"{jid[:24]}-{i:02d}"
        jid_encolado, _ = encolar(acc, {}, sub_id)
        res = esperar_resultado(jid_encolado, float(acc.get("tiempo_max_s", 900)))
        resultados.append({"paso": i, "accion_id": a_id, "resultado": res})
        if res is not None and a_id == "ciclo.bajar_meta" and res.get("codigo_salida") == 2:
            avisos.append({"paso": i, "accion_id": a_id, "detalle": res.get("detalle") or
                            "entrega de Meta parcial: al menos una cuenta falló."})
            continue
        if res is None or res.get("estado") != "EXITO":
            detalle = (res.get("detalle") if res else "Tiempo agotado") or f"El paso {a_id} falló."
            return {
                "job_id": jid,
                "estado": "FALLIDO",
                "paso_fallido": i,
                "accion_fallida": a_id,
                "detalle": detalle,
                "pasos": resultados,
                "avisos": avisos,
            }

    detalle = "Ciclo nocturno completado con éxito."
    if avisos:
        detalle = "Ciclo nocturno completado con avisos: " + "; ".join(a["detalle"] for a in avisos)
    return {
        "job_id": jid,
        "estado": "EXITO",
        "detalle": detalle,
        "pasos": resultados,
        "avisos": avisos,
    }


if os.environ.get("VITALCOM_PROGRAMAR_NOCTURNO") == "1":
    @DBOS.scheduled(CRON_NOCTURNO)
    def tarea_ciclo_nocturno_programado(scheduled_time: datetime, actual_time: datetime) -> None:
        """Disparador programado de DBOS (se activa solo si VITALCOM_PROGRAMAR_NOCTURNO=1)."""
        jid = f"nocturno-{actual_time.strftime('%Y%m%d-%H%M%S')}"
        ejecutar_ciclo_nocturno(jid)


# ── Respaldo automático diario de PRODUCTOS/ (Hito 7) ─────────────────────────

CRON_RESPALDO = os.environ.get("VITALCOM_CRON_RESPALDO", "0 3 * * *")


def ejecutar_respaldo_productos(job_id: str | None = None) -> dict[str, Any]:
    """Acción programada o manual de respaldo zip de PRODUCTOS/ con retención de 30 copias."""
    import uuid
    jid = job_id or uuid.uuid4().hex
    acc = acciones.por_id_para_el_runner("sistema.respaldo_productos")
    jid_encolado, _ = encolar(acc, {}, jid)
    res = esperar_resultado(jid_encolado, float(acc.get("tiempo_max_s", 300)))
    if res is None or res.get("estado") != "EXITO":
        detalle = (res.get("detalle") if res else "Tiempo agotado") or "El respaldo de PRODUCTOS/ falló."
        return {
            "job_id": jid,
            "estado": "FALLIDO",
            "accion_fallida": "sistema.respaldo_productos",
            "detalle": detalle,
        }
    return {
        "job_id": jid,
        "estado": "EXITO",
        "detalle": "Respaldo de PRODUCTOS/ completado con éxito.",
        "resultado": res,
    }


if os.environ.get("VITALCOM_PROGRAMAR_RESPALDO") == "1" or os.environ.get("VITALCOM_PROGRAMAR_NOCTURNO") == "1":
    @DBOS.scheduled(CRON_RESPALDO)
    def tarea_respaldo_productos_programado(scheduled_time: datetime, actual_time: datetime) -> None:
        """Disparador programado de DBOS para respaldo de PRODUCTOS/."""
        jid = f"respaldo-{actual_time.strftime('%Y%m%d-%H%M%S')}"
        ejecutar_respaldo_productos(jid)


