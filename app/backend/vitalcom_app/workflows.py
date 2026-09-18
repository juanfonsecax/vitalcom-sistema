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
import json
import os
import signal
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dbos import DBOS, SetEnqueueOptions, SetWorkflowID
from dbos._error import DBOSQueueDeduplicatedError

from . import acciones, bitacora, claude, contratos
from .acciones import ErrorDeAccion
from .config import base, datos_de_la_app, python_del_sistema, ruta
from .escrituras import Cola, SistemaOcupado

APP_VERSION = "wf-1"
NOMBRE_DE_LA_APP = "vitalcom-app"
COLA_TRABAJOS = "trabajos"
COLA_ESCRITURA = "escritura"
SONDEO_DE_RESULTADO_S = 0.2
MAXIMO_DE_PREGUNTAS = 5
TOPE_DE_TEXTO_DE_CLAUDE = 4000
TOPE_DE_ESPERA_DEL_TURNO_S = 3600

# Los pasos que cada workflow llama, en orden. Si esta lista cambia, cambia la versión.
PASOS: dict[str, list[str]] = {
    "wf_unidad": ["paso_ejecutar", "paso_tras_escribir"],
    "wf_script": [
        "paso_sellar", "DBOS.set_event", "enqueue:escritura", "paso_leer_flujo", "paso_cerrar",
        "DBOS.set_event",
    ],
    "wf_claude": [
        "paso_sellar", "DBOS.set_event", "enqueue:escritura", "DBOS.set_event", "DBOS.set_event",
        "DBOS.recv", "DBOS.set_event", "DBOS.set_event", "enqueue:escritura", "paso_leer_flujo",
        "paso_cerrar", "DBOS.set_event",
    ],
}

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


def correr_claude(job_id: str, n: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Una llamada headless a Claude Code. La salida cruda va a `<n>_claude.jsonl` en la bitácora."""
    carpeta = ruta(spec["run_dir"])
    pedido = spec["claude"]
    try:
        with bitacora.abrir_log(carpeta, f"{n}_claude.jsonl") as log:
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
    return {**resumen, "estado": "EXITO"}


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
            resumen = correr_script(job_id, n, spec) if spec["tipo"] == "script" else correr_claude(job_id, n, spec)
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
    if spec["escribe"]:
        tras = paso_tras_escribir(job_id, n, spec)
        resultado = {**resultado, "tras": tras}
    return resultado


# ── el padre de las acciones de script ────────────────────────────────────────

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
        "claude": acciones.cargar().bloque.get("claude") if accion["ejecutor_tipo"] in ("subagente", "skill") else None,
        "manifiesto_sha": acciones.sha_del_manifiesto(), "hoy": reservados["hoy"],
        "iniciado": iniciado, "run_dir": run_dir, "app_version": APP_VERSION,
        "argv": acciones.resolver(accion, valores, reservados) if accion["ejecutor_tipo"] == "script" else None,
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


# ── lo que usan los endpoints ─────────────────────────────────────────────────

_PADRES = {"script": wf_script, "subagente": wf_claude, "skill": wf_claude}


def existe(job_id: str) -> bool:
    return bool(DBOS.list_workflows(workflow_ids=[job_id], load_input=False, load_output=False))


def _activo_de(clave: str) -> str | None:
    for estado in DBOS.list_workflows(queue_name=COLA_TRABAJOS, status=["ENQUEUED", "PENDING"],
                                      load_input=False, load_output=False):
        if getattr(estado, "deduplication_id", None) == clave:
            return estado.workflow_id
    return None


def encolar(accion: dict[str, Any], valores: dict[str, Any], job_id: str) -> tuple[str, bool]:
    """Pone el trabajo en la cola `trabajos`. Devuelve (job_id, repetido)."""
    if existe(job_id):
        return job_id, True
    padre = _PADRES.get(accion["ejecutor_tipo"])
    if padre is None:
        raise ErrorDeAccion(501, "RUNNER_PENDIENTE", "Este tipo de acción todavía no está conectado al runner.")
    clave = valores.get("producto_key") or accion["id"]
    try:
        with SetWorkflowID(job_id), SetEnqueueOptions(deduplication_id=clave):
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
