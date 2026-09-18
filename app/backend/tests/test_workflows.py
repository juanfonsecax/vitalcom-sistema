"""El runner de DBOS: serialización, fallos, caídas y la versión de los workflows (diseño §3, §4).

Todo sobre el sistema de juguete: el manifiesto y el FLUJO son los reales, los scripts son
falsos. Ninguna prueba llama a Claude ni a Meta.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import sistema_de_juguete as juguete

from vitalcom_app import workflows

PAQUETE = Path(__file__).resolve().parents[1] / "vitalcom_app"
BACKEND = Path(__file__).resolve().parents[1]

# Una fila por versión del runner: la huella de sus pasos. Cambiar los pasos sin subir
# `APP_VERSION` (y sin agregar la fila) hace fallar `test_version_de_workflows`.
HUELLAS = {
    "wf-1": "b493adfba080558e38876df1c0e08f400951d8c3fae26519f92647ac447a98cf",
    "wf-2": "25afdfd96202ac32cf4ca0d38a78b91a6af5d4aadb34c8d6aef657c515cd0b61",  # publicar espera las imágenes subidas a mano
    "wf-3": "eb8ad85d7d1a6de342cc0e0a09c938f6e9b609c589d3126d01bf968d4ee2fe33",  # una skill de a un paso (Armar FASE 1)
}

JOB_A = "a" * 32
JOB_B = "b" * 32


def _pedir(cliente, accion_id, parametros=None, **extra):
    return cliente.post(f"/api/acciones/{accion_id}",
                        json={"parametros": parametros or {}, "confirmado": True, **extra})


def _terminar(job_id: str, tope_s: float = 60) -> dict:
    resultado = workflows.esperar_resultado(job_id, tope_s)
    assert resultado is not None, f"el trabajo {job_id[:8]} no terminó en {tope_s} s"
    return resultado


# El script falso que anota `inicio`/`fin` con marca de tiempo y duerme.
DORMILON = '''import json, pathlib, sys, time
BASE = pathlib.Path(__file__).resolve().parents[2]
def anotar(evento):
    with open(BASE / "PRODUCTOS" / "_marcas.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"s": pathlib.Path(__file__).name, "e": evento, "t": time.time()}) + "\\n")
anotar("inicio")
time.sleep(1.5)
anotar("fin")
if "--json" in sys.argv:
    print(json.dumps({"ok": True}))
'''


def _marcas(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_marcas.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x]


# ── el camino feliz y los fallos ──────────────────────────────────────────────

def test_un_script_que_sale_bien_termina_en_exito_y_regenera(cliente_juguete, sistema_de_juguete):
    assert _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB_A).status_code == 202
    resultado = _terminar(JOB_A)
    assert resultado["estado"] == "EXITO", resultado
    scripts = [c["script"] for c in juguete.llamadas(sistema_de_juguete)]
    assert scripts[0] == "gen_decisiones.py"
    assert scripts[1:] == ["hook_csv.py", "flujo.py", "gen_app.py"], "tras_escribir, en su orden"
    assert (sistema_de_juguete / resultado["run_dir"] / "trabajo.json").is_file()


def test_el_detalle_de_un_fallo_es_el_del_script(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "transcribir_videos.py", (
        "import json\nprint(json.dumps({'ok': False, 'detalle': 'no hay videos en la carpeta'}))\n"
        "raise SystemExit(1)\n"))
    _pedir(cliente_juguete, "producto.transcribir", {"producto_key": "TINNIDROP", "modelo": "small"}, job_id=JOB_A)
    resultado = _terminar(JOB_A)
    assert resultado["estado"] == "FALLIDO"
    assert resultado["detalle"] == "no hay videos en la carpeta"
    scripts = [c["script"] for c in juguete.llamadas(sistema_de_juguete)]
    assert "hook_csv.py" in scripts, "una escritura a medias igual cambió el disco: tras_escribir corre"


def test_un_csv_invalido_lo_dice_aunque_el_comando_salio_bien(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "hook_csv.py", "import sys\nsys.stderr.write('CSV roto')\nsys.exit(2)\n")
    _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB_A)
    resultado = _terminar(JOB_A)
    assert resultado["estado"] == "CSV_INVALIDO"


def test_un_script_que_pasa_su_tope_se_corta(cliente_juguete, sistema_de_juguete, monkeypatch):
    juguete.escribir_script(sistema_de_juguete, "gen_decisiones.py", "import time\ntime.sleep(30)\n")
    manifiesto = juguete.manifiesto_real()
    for accion in manifiesto["acciones"]["lista"]:
        if accion["id"] == "nodo.ciclo.motor":
            accion["tiempo_max_s"] = 1
    juguete.escribir_manifiesto(sistema_de_juguete, manifiesto)
    _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB_A)
    inicio = time.monotonic()
    resultado = _terminar(JOB_A)
    assert resultado["estado"] == "FALLIDO" and "tope" in resultado["detalle"]
    assert time.monotonic() - inicio < 25, "no esperó los 30 s del script"


# ── dos escrituras se serializan ──────────────────────────────────────────────

def test_dos_escrituras_se_serializan(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "gen_decisiones.py", DORMILON)
    juguete.escribir_script(sistema_de_juguete, "transcribir_videos.py", DORMILON)
    _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB_A)
    _pedir(cliente_juguete, "producto.transcribir", {"producto_key": "TINNIDROP", "modelo": "small"}, job_id=JOB_B)
    assert _terminar(JOB_A)["estado"] == "EXITO" and _terminar(JOB_B)["estado"] == "EXITO"

    tramos: dict[str, dict[str, float]] = {}
    for marca in _marcas(sistema_de_juguete):
        tramos.setdefault(marca["s"], {})[marca["e"]] = marca["t"]
    (a, b) = sorted(tramos.values(), key=lambda t: t["inicio"])
    assert a["fin"] <= b["inicio"], f"los intervalos se solaparon: {a} {b}"


def test_mismo_producto_409_ya_en_curso(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "transcribir_videos.py", DORMILON)
    parametros = {"producto_key": "TINNIDROP", "modelo": "small"}
    assert _pedir(cliente_juguete, "producto.transcribir", parametros, job_id=JOB_A).status_code == 202
    segundo = _pedir(cliente_juguete, "producto.transcribir", parametros, job_id=JOB_B)
    assert segundo.status_code == 409, segundo.text
    assert segundo.json()["codigo"] == "YA_EN_CURSO" and segundo.json()["job_id"] == JOB_A
    _terminar(JOB_A)
    tercero = _pedir(cliente_juguete, "producto.transcribir", parametros, job_id="c" * 32)
    assert tercero.status_code == 202, "cuando el primero termina, el producto queda libre"
    _terminar("c" * 32)


# ── una caída a mitad de un paso ──────────────────────────────────────────────

def _correr_driver(sistema: Path, *argumentos: str, tope_s: float = 120) -> subprocess.CompletedProcess:
    entorno = {**os.environ, "VITALCOM_BASE": str(sistema), "PYTHONPATH": str(BACKEND),
               "VITALCOM_DATOS": str(sistema.parent / "datos"), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(Path(__file__).with_name("driver_caida.py")), *argumentos],
                          cwd=str(BACKEND), env=entorno, capture_output=True, text=True,
                          encoding="utf-8", timeout=tope_s)


def _una_linea_json(salida: str) -> dict:
    return json.loads([x for x in salida.splitlines() if x.startswith("{")][-1])


def test_caida_de_un_script_idempotente_retoma_sola(sistema_de_juguete):
    """`gen_decisiones.py` es idempotente: al relanzar, el runner lo corre otra vez y termina."""
    murio = _correr_driver(sistema_de_juguete, "arrancar", "nodo.ciclo.motor", JOB_A)
    assert murio.returncode == 3, "el proceso tenía que morir a mitad del paso: " + murio.stderr[-400:]
    retomo = _correr_driver(sistema_de_juguete, "retomar", JOB_A)
    assert retomo.returncode == 0, retomo.stderr[-600:]
    resultado = _una_linea_json(retomo.stdout)
    assert resultado["estado"] == "EXITO", resultado

    carpeta = sistema_de_juguete / resultado["run_dir"]
    assert len((carpeta / "1.inicio").read_text(encoding="utf-8").splitlines()) == 2, "los dos intentos quedan"
    fines = [json.loads(x) for x in (carpeta / "1.fin").read_text(encoding="utf-8").splitlines()]
    assert fines[0].get("roto") is True and fines[1]["estado"] == "EXITO"
    assert [c["script"] for c in juguete.llamadas(sistema_de_juguete)].count("gen_decisiones.py") == 1


def test_caida_de_un_paso_no_idempotente_queda_interrumpido_con_rastro(sistema_de_juguete):
    """Si `nodo.ciclo.motor` se declara NO idempotente, una caída a mitad lo deja INTERRUMPIDO y no lo repite."""
    manifiesto = juguete.manifiesto_real()
    for accion in manifiesto["acciones"]["lista"]:
        if accion["id"] == "nodo.ciclo.motor":
            accion["idempotente"] = False
    juguete.escribir_manifiesto(sistema_de_juguete, manifiesto)
    assert _correr_driver(sistema_de_juguete, "arrancar", "nodo.ciclo.motor", JOB_A).returncode == 3
    retomo = _correr_driver(sistema_de_juguete, "retomar", JOB_A)
    resultado = _una_linea_json(retomo.stdout)
    assert resultado["estado"] == "INTERRUMPIDO", resultado
    carpeta = sistema_de_juguete / resultado["run_dir"]
    assert (carpeta / "1.inicio").is_file() and not (carpeta / "1.fin").exists(), "empezó y nunca terminó"
    assert "gen_decisiones.py" not in [c["script"] for c in juguete.llamadas(sistema_de_juguete)], (
        "un paso no idempotente no se repite solo"
    )


# ── la versión de los workflows ───────────────────────────────────────────────

ORDENADORES = ("DBOS.set_event", "DBOS.recv")


def _pasos_que_llama(arbol: ast.Module, funcion: str, _vistas: frozenset[str] = frozenset()) -> list[str]:
    """Los pasos, `set_event`, `recv` y `enqueue` que un workflow llama, en orden de ejecución.

    Una función auxiliar del módulo que contiene alguno se expande en el lugar de la llamada:
    para DBOS solo cuenta el orden en que los pasos se ejecutan, no en qué función viven.
    """
    funciones = {n.name: n for n in arbol.body if isinstance(n, ast.FunctionDef)}
    pasos_declarados = {
        nombre for nombre, n in funciones.items()
        if any(ast.unparse(d) == "DBOS.step()" for d in n.decorator_list)
    }
    workflows_declarados = {
        nombre for nombre, n in funciones.items()
        if any(ast.unparse(d) == "DBOS.workflow()" for d in n.decorator_list)
    }
    encontrados: list[tuple[int, int, list[str]]] = []
    for nodo in ast.walk(funciones[funcion]):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = ast.unparse(nodo.func)
        if nombre in pasos_declarados or nombre in ORDENADORES:
            encontrados.append((nodo.lineno, nodo.col_offset, [nombre]))
        elif isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "enqueue":
            cola = ast.unparse(nodo.func.value)
            etiqueta = "escritura" if "COLA_ESCRITURA" in cola else "trabajos" if "COLA_TRABAJOS" in cola else cola
            encontrados.append((nodo.lineno, nodo.col_offset, [f"enqueue:{etiqueta}"]))
        elif nombre in funciones and nombre not in workflows_declarados and nombre not in _vistas:
            expandido = _pasos_que_llama(arbol, nombre, _vistas | {funcion})
            if expandido:
                encontrados.append((nodo.lineno, nodo.col_offset, expandido))
    return [paso for _l, _c, grupo in sorted(encontrados, key=lambda t: (t[0], t[1])) for paso in grupo]


def test_version_de_workflows():
    """Los pasos declarados en `PASOS` son los que el código llama, y su huella va con la versión."""
    arbol = ast.parse((PAQUETE / "workflows.py").read_text(encoding="utf-8"))
    for funcion, declarados in workflows.PASOS.items():
        assert _pasos_que_llama(arbol, funcion) == declarados, (
            f"{funcion}: los pasos que llama no son los de PASOS. Si cambiaron, subí APP_VERSION."
        )
    huella = hashlib.sha256(json.dumps(workflows.PASOS, sort_keys=True).encode("utf-8")).hexdigest()
    assert HUELLAS.get(workflows.APP_VERSION) in (huella, "PENDIENTE"), (
        f"Cambiaron los pasos de los workflows: subí APP_VERSION (hoy «{workflows.APP_VERSION}») y agregá "
        f"su fila en HUELLAS con {huella}."
    )
    assert HUELLAS.get(workflows.APP_VERSION) != "PENDIENTE", f"falta fijar la huella: {huella}"


# ── estructurales: el runner no arma comandos a mano ──────────────────────────

def test_ningun_literal_de_script_en_el_runner():
    """Todo argv sale del manifiesto (`acciones.resolver`): ni un `.py` literal en el runner."""
    for nombre in ("workflows.py", "escrituras.py", "acciones.py", "api_acciones.py", "main.py"):
        arbol = ast.parse((PAQUETE / nombre).read_text(encoding="utf-8"))
        docstrings = {
            id(n.body[0].value) for n in ast.walk(arbol)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)
        }
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docstrings:
                assert not nodo.value.endswith(".py") or nombre == "acciones.py", (
                    f"{nombre}:{nodo.lineno} «{nodo.value}»: los scripts se declaran en el manifiesto"
                )
    # `acciones.py` conoce UN script: el validador del manifiesto.
    arbol = ast.parse((PAQUETE / "acciones.py").read_text(encoding="utf-8"))
    scripts = {n.value for n in ast.walk(arbol)
               if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(".py")}
    assert scripts <= {"gen_app.py"}, scripts


def test_nunca_shell_true():
    for archivo in PAQUETE.rglob("*.py"):
        assert "shell=True" not in archivo.read_text(encoding="utf-8"), archivo.name


def test_las_unidades_de_escritura_toman_el_turno():
    arbol = ast.parse((PAQUETE / "workflows.py").read_text(encoding="utf-8"))
    for funcion in ("paso_ejecutar", "paso_tras_escribir"):
        nodo = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == funcion)
        assert "Cola(" in ast.unparse(nodo), f"{funcion} tiene que escribir bajo el turno de escritura"
