"""`claude.py` y el workflow de Claude (`wf_claude`), contra el Claude de mentira (diseño §3.5(c), §3.8).

Ninguna prueba llama al Claude real ni a Meta: `fake_claude.py` habla el mismo stream-json y solo
«ejecuta» una herramienta de Meta si viene por nombre exacto en `--allowedTools`.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import sistema_de_juguete as juguete

from vitalcom_app import acciones, claude, workflows

JOB = "a" * 32
PARAMETROS = {"producto_key": "TINNIDROP"}


def _pedir(cliente, accion_id="nodo.F2.etapa-11", parametros=None, **extra):
    return cliente.post(f"/api/acciones/{accion_id}", json={
        "parametros": PARAMETROS if parametros is None else parametros, "confirmado": True, **extra})


def _terminar(job_id=JOB, tope_s=60):
    resultado = workflows.esperar_resultado(job_id, tope_s)
    assert resultado is not None, "el trabajo no terminó"
    return resultado


def _argv_de_claude(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_claude_argv.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x] if archivo.is_file() else []


def _meta_llamadas(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_meta_llamadas.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x] if archivo.is_file() else []


def _esperar_estado(job_id: str, estado: str, tope_s: float = 30) -> None:
    limite = time.monotonic() + tope_s
    while time.monotonic() < limite:
        publicado = workflows.publicado(job_id, "estado")
        if publicado and publicado.get("estado") == estado:
            return
        time.sleep(0.1)
    raise AssertionError(f"el trabajo no llegó a {estado}")


# ── claude.py, sin DBOS ───────────────────────────────────────────────────────

def test_claude_credencial_prohibida_se_niega_con_un_mensaje_claro(sistema_de_juguete, monkeypatch):
    for nombre in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        monkeypatch.setenv(nombre, "secreta")
        with pytest.raises(claude.ClaudeNoDisponible) as error:
            claude.correr(prompt="hola", herramientas=["Read"], presupuesto_usd=1, tiempo_max_s=30,
                          escribir_linea=lambda _l: None)
        assert error.value.codigo == "CLAUDE_CREDENCIAL_PROHIBIDA" and nombre in error.value.detalle
        assert not (sistema_de_juguete / "PRODUCTOS" / "_claude_argv.log").exists(), "ni siquiera arrancó"
        monkeypatch.delenv(nombre)
    assert claude.estado_sesion(forzar=True)["credencial_prohibida"] == []


def test_el_entorno_del_subproceso_no_hereda_lo_de_claude(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "desktop")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://ejemplo.invalid")
    monkeypatch.setenv("VITALCOM_PROPIA", "queda")
    entorno = claude.entorno_del_subproceso()
    assert not [k for k in entorno if k.startswith(("CLAUDE", "ANTHROPIC"))]
    assert entorno["VITALCOM_PROPIA"] == "queda"


def test_los_flags_del_spike_y_nunca_bare(sistema_de_juguete):
    argv = claude.armar_argv(prompt="hola", herramientas=["Task", "Read"], presupuesto_usd=3)
    assert "--bare" not in argv and "--dangerously-skip-permissions" not in argv
    for pareja in (["--output-format", "stream-json"], ["--permission-mode", "dontAsk"],
                   ["--max-budget-usd", "3"], ["-p", "hola"]):
        assert argv[argv.index(pareja[0]) + 1] == pareja[1]
    assert "--verbose" in argv and "--include-hook-events" in argv
    assert argv[argv.index("--allowedTools") + 1:argv.index("--allowedTools") + 3] == ["Task", "Read"]
    assert "--resume" not in argv, "--resume solo con un session_id"
    assert claude.armar_argv(prompt="x", herramientas=["Read"], presupuesto_usd=1, resume="s-1")[
        claude.armar_argv(prompt="x", herramientas=["Read"], presupuesto_usd=1, resume="s-1").index("--resume") + 1
    ] == "s-1"


def test_un_comodin_de_mcp_se_rechaza(sistema_de_juguete):
    with pytest.raises(ValueError):
        claude.correr(prompt="x", herramientas=["mcp__claude_ai_META_MCP__*"], presupuesto_usd=1,
                      tiempo_max_s=10, escribir_linea=lambda _l: None)


def test_la_pregunta_se_extrae_de_la_marca():
    assert claude.pregunta_del_texto("Listo.\nPREGUNTA_OPERADOR: ¿A o B?\n(A) uno (B) dos") == "¿A o B?\n(A) uno (B) dos"
    assert claude.pregunta_del_texto("sin preguntas") is None
    assert claude.pregunta_del_texto("PREGUNTA_OPERADOR:   ") is None


def test_el_binario_se_resuelve_en_orden(sistema_de_juguete, monkeypatch, tmp_path):
    monkeypatch.delenv("VITALCOM_CLAUDE_CMD")
    falso = tmp_path / "claude-declarado.exe"
    falso.write_text("", encoding="utf-8")
    monkeypatch.setenv("VITALCOM_CLAUDE_EXE", str(falso))
    assert claude.resolver_binario() == [str(falso)]
    monkeypatch.setenv("VITALCOM_CLAUDE_CMD", json.dumps(["python", "otro.py"]))
    assert claude.resolver_binario() == ["python", "otro.py"], "VITALCOM_CLAUDE_CMD tiene prioridad"


def test_un_wrapper_cmd_del_path_nunca_se_usa(monkeypatch, tmp_path):
    """cmd.exe corta los argumentos en el primer salto de línea: el prompt y los flags se pierden."""
    monkeypatch.delenv("VITALCOM_CLAUDE_CMD", raising=False)
    monkeypatch.delenv("VITALCOM_CLAUDE_EXE", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "sin_escritorio"))
    wrapper = tmp_path / "npm" / "claude.CMD"
    wrapper.parent.mkdir()
    wrapper.write_text("", encoding="utf-8")
    monkeypatch.setattr(claude.shutil, "which", lambda _nombre: str(wrapper))
    monkeypatch.setattr(claude.Path, "home", lambda: tmp_path / "home")

    with pytest.raises(claude.ClaudeNoDisponible):
        claude.resolver_binario()

    nativo = tmp_path / "home" / ".local" / "bin" / "claude.exe"
    nativo.parent.mkdir(parents=True)
    nativo.write_text("", encoding="utf-8")
    assert claude.resolver_binario() == [str(nativo)]


def test_perilla_meta_falso_solo_aplica_a_herramientas_mcp(monkeypatch, tmp_path):
    monkeypatch.delenv("VITALCOM_CLAUDE_CMD", raising=False)
    monkeypatch.delenv("VITALCOM_CLAUDE_CMD_META", raising=False)
    falso_exe = tmp_path / "claude-normal.exe"
    falso_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("VITALCOM_CLAUDE_EXE", str(falso_exe))

    # Sin perilla, con o sin mcp__ usa el normal
    assert claude.resolver_binario(["Read"]) == [str(falso_exe)]
    assert claude.resolver_binario(["mcp__claude_ai_META_MCP__ads_get_ad_accounts"]) == [str(falso_exe)]
    assert claude.meta_falso() is False

    # Con la perilla puesta
    meta_cmd = ["python", "tests/fake_claude.py"]
    monkeypatch.setenv("VITALCOM_CLAUDE_CMD_META", json.dumps(meta_cmd))
    assert claude.meta_falso() is True

    # Llamada sin mcp__ sigue usando el normal
    assert claude.resolver_binario(["Read", "Task"]) == [str(falso_exe)]
    # Llamada con mcp__ usa el comando de Meta falso
    assert claude.resolver_binario(["Read", "mcp__claude_ai_META_MCP__ads_get_ad_accounts"]) == meta_cmd


def test_resumir_eventos_para_la_pantalla():
    assert claude.resumir_evento({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Task", "input": {"subagent_type": "etapa-2"}}]}}) == "arrancó etapa-2"
    assert claude.resumir_evento({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": "fase-1-angulos"}}]}}) == "cargó la skill fase-1-angulos"
    assert claude.resumir_evento({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "Voy a leer el flujo\nsegunda línea"}]}}) == "Voy a leer el flujo"
    assert claude.resumir_evento({"type": "result", "subtype": "success"}) == "Claude terminó: success"
    assert claude.resumir_evento({"type": "user"}) is None


# ── la puerta: sesión de Claude ───────────────────────────────────────────────

def test_sin_sesion_de_claude_503(cliente_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_SIN_SESION", "1")
    respuesta = _pedir(cliente_juguete)
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "CLAUDE_SIN_SESION"
    assert "/login" in respuesta.json()["detail"]


def test_credencial_prohibida_en_el_entorno_503(cliente_juguete, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secreta")
    respuesta = _pedir(cliente_juguete)
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "CLAUDE_CREDENCIAL_PROHIBIDA"


# ── wf_claude ─────────────────────────────────────────────────────────────────

def test_un_nodo_de_claude_cumplido_termina_en_exito(cliente_juguete, sistema_de_juguete):
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    assert _pedir(cliente_juguete, job_id=JOB).status_code == 202
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert resultado["unidades"][0]["costo_equivalente_usd"] == 0.0123, "el costo es equivalente, no un gasto"
    carpeta = sistema_de_juguete / resultado["run_dir"]
    assert (carpeta / "1_claude.jsonl").read_text(encoding="utf-8").count('"type": "result"') == 1
    scripts = [c["script"] for c in juguete.llamadas(sistema_de_juguete)]
    assert {"hook_csv.py", "gen_app.py"} <= set(scripts), "tras_escribir corre también después de Claude"


def test_el_veredicto_lo_da_flujo_no_lo_que_claude_dice(cliente_juguete, sistema_de_juguete):
    # F2.etapa-11 pide un DIAGNOSTICO_CONGRUENCIA (no un CAMBIO_BOT -- la reescritura corre en
    # F3.entrada). El fixture solo necesita representar "algo falta".
    falta = [{"dato": "DIAGNOSTICO_CONGRUENCIA registrado en _EVENTOS.csv", "ok": False, "dueno": "operador"}]
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", falta=falta)})
    _pedir(cliente_juguete, job_id=JOB)
    resultado = _terminar()
    assert resultado["estado"] == "SIN_CUMPLIR", "Claude dijo «Listo», pero el nodo sigue pendiente"
    assert resultado["flujo"]["falta_para_cumplir"] == falta, "lo que falta, tal cual lo dice flujo.py"


def test_un_error_de_claude_es_fallido_con_su_detalle(cliente_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "error")
    _pedir(cliente_juguete, job_id=JOB)
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO"
    assert "error_during_execution" in resultado["detalle"]


def test_el_prompt_del_nodo_sale_del_manifiesto(cliente_juguete, sistema_de_juguete):
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    _pedir(cliente_juguete, job_id=JOB)
    _terminar()
    corrida = _argv_de_claude(sistema_de_juguete)[0]
    prompt = corrida["argv"][corrida["argv"].index("-p") + 1]
    assert "F2.etapa-11" in prompt and "TINNIDROP" in prompt and JOB in prompt
    assert "subagente `etapa-fake`" in prompt, "el ejecutor es el texto que devuelve flujo.py"
    assert "PREGUNTA_OPERADOR:" in prompt
    assert corrida["env_prohibido"] == [], "el subproceso no hereda las variables CLAUDE*/ANTHROPIC*"
    assert "--bare" not in corrida["argv"]


def test_una_accion_global_no_le_pide_a_flujo_un_producto(sistema_de_juguete):
    # `prompt_del_nodo` en sí (no la ruta HTTP): una acción SIN producto (nodo.ciclo.datos, el
    # botón "Traer las ventas de LucidSales", pasó a ejecutor_tipo=script en T4 y ya no corre
    # por wf_claude) es el único caso "global" real del manifiesto. La acción de este test
    # (nodo.F2.etapa-11, un subagente que SÍ requiere producto_key) se construye a mano SIN
    # parámetros para seguir cubriendo el comportamiento genérico de wf_claude ante una acción
    # global, sin depender de que exista un botón de skill/subagente sin producto.
    accion = acciones.buscar("nodo.F2.etapa-11", interna_ok=True)
    sello = {"job_id": JOB, "accion": accion, "parametros": {}, "ejecutor": "x",
             "claude": acciones.cargar().bloque["claude"], "run_dir": "r"}
    prompt = workflows.prompt_del_nodo(sello)
    assert "flujo.py" not in prompt and "acción global" in prompt


def test_la_pregunta_de_claude_espera_respuesta_y_continua_con_resume(cliente_juguete, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "pregunta")
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    _pedir(cliente_juguete, job_id=JOB)
    _esperar_estado(JOB, "ESPERA_RESPUESTA")
    pendiente = workflows.publicado(JOB, "pendiente")
    assert pendiente["tipo"] == "pregunta" and "¿Sigo con el ángulo A o con el B?" in pendiente["texto"]
    assert (sistema_de_juguete / "PRODUCTOS" / "_claude_argv.log").read_text(encoding="utf-8").count("\n") == 1

    workflows.responder(JOB, pendiente["n"], "Seguí con el A")
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    primera, segunda = _argv_de_claude(sistema_de_juguete)
    assert primera["resume"] is None and segunda["resume"] == "fake-1", "--resume solo con el session_id previo"
    assert segunda["argv"][segunda["argv"].index("-p") + 1] == "Seguí con el A"
    assert workflows.publicado(JOB, "pendiente") is None, "lo pendiente se limpia al resolverlo"


def test_una_pregunta_que_nadie_responde_caduca(cliente_juguete, sistema_de_juguete, monkeypatch):
    manifiesto = juguete.manifiesto_real()
    manifiesto["acciones"]["claude"]["respuesta_max_horas"] = 0.0005  # 1,8 s
    juguete.escribir_manifiesto(sistema_de_juguete, manifiesto)
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "pregunta")
    _pedir(cliente_juguete, job_id=JOB)
    resultado = _terminar()
    assert resultado["estado"] == "CADUCADO"
    assert len(_argv_de_claude(sistema_de_juguete)) == 1, "no se ejecutó nada más"


# ── Meta: nada de escritura en los workflows de Claude ────────────────────────

def test_ninguna_accion_de_claude_recibe_herramientas_de_meta(sistema_de_juguete):
    """`spec_de_claude` es lo único que arma `allowedTools` de `wf_claude`: ni una herramienta de MCP."""
    for accion in acciones.declaradas():
        if accion["ejecutor_tipo"] not in ("subagente", "skill"):
            continue
        sello = {"job_id": JOB, "accion": accion, "parametros": {"producto_key": "TINNIDROP"},
                 "ejecutor": "x", "claude": acciones.cargar().bloque["claude"], "run_dir": "r"}
        herramientas = workflows.spec_de_claude(sello)["claude"]["herramientas"]
        assert not [h for h in herramientas if h.startswith("mcp__") or "*" in h], accion["id"]


def test_claude_no_puede_escribir_en_meta_desde_wf_claude(cliente_juguete, sistema_de_juguete, monkeypatch):
    """Aunque Claude lo intente, sin el nombre exacto en `allowedTools` la llamada no corre."""
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "llamar:ads_create_campaign,ads_get_ad_accounts,ads_activate_entity")
    _pedir(cliente_juguete, job_id=JOB)
    _terminar()
    assert _meta_llamadas(sistema_de_juguete) == [], "ninguna llamada a Meta salió de un workflow de Claude"
    permitidas = _argv_de_claude(sistema_de_juguete)[0]["permitidas"]
    assert not [h for h in permitidas if "META" in h]


# ── una caída con Claude corriendo ────────────────────────────────────────────

def test_caida_de_claude_queda_interrumpido_con_su_rastro(sistema_de_juguete, monkeypatch):
    """Claude corre (log parcial), el proceso muere, y al relanzar NO se repite: INTERRUMPIDO."""
    from test_workflows import _correr_driver, _una_linea_json

    monkeypatch.setenv("VITALCOM_FAKE_MODO", "dormir:25")
    murio = _correr_driver(sistema_de_juguete, "arrancar", "nodo.F2.etapa-11", JOB,
                           json.dumps(PARAMETROS), "3")
    assert murio.returncode == 3, murio.stderr[-400:]
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "exito")
    retomo = _correr_driver(sistema_de_juguete, "retomar", JOB)
    resultado = _una_linea_json(retomo.stdout)
    assert resultado["estado"] == "INTERRUMPIDO", resultado
    carpeta = sistema_de_juguete / resultado["run_dir"]
    assert (carpeta / "1.inicio").is_file() and not (carpeta / "1.fin").exists()
    assert '"type": "system"' in (carpeta / "1_claude.jsonl").read_text(encoding="utf-8"), "el log parcial quedó"
    assert len(_argv_de_claude(sistema_de_juguete)) == 1, "Claude no se volvió a correr solo"
