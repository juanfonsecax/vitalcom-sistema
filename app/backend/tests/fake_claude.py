"""Un Claude Code de mentira: habla el mismo stream-json y NUNCA llama a Claude ni a Meta.

`VITALCOM_CLAUDE_CMD='["python", "tests/fake_claude.py"]'` lo pone en lugar del binario. Se guioniza con
`VITALCOM_FAKE_MODO`:

  exito              termina bien (por defecto)
  pregunta           la primera vez termina con `PREGUNTA_OPERADOR: …`; con `--resume` termina bien
  error              termina con `is_error: true`
  dormir:N           duerme N segundos y termina bien (para caídas y cancelaciones)
  llamar:t1,t2       intenta usar esas herramientas de Meta; solo «corren» las que están en
                     `--allowedTools` por nombre exacto (como `dontAsk`); cada una que corre anota
                     una línea en `PRODUCTOS/_meta_llamadas.log`

Cada corrida anota su argv y las variables prohibidas que ve en `PRODUCTOS/_claude_argv.log`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

argv = sys.argv[1:]
modo = os.environ.get("VITALCOM_FAKE_MODO", "exito")
SESION = "fake-" + os.environ.get("VITALCOM_FAKE_SESION", "1")


def emitir(evento: dict) -> None:
    sys.stdout.write(json.dumps(evento, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def anotar(nombre: str, dato: dict) -> None:
    carpeta = Path.cwd() / "PRODUCTOS"
    if carpeta.is_dir():
        with open(carpeta / nombre, "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(dato, ensure_ascii=False) + "\n")


def valor_de(bandera: str) -> str | None:
    return argv[argv.index(bandera) + 1] if bandera in argv else None


if argv[:2] == ["auth", "status"]:
    con_sesion = os.environ.get("VITALCOM_FAKE_SIN_SESION") != "1"
    print(json.dumps({"loggedIn": con_sesion, "authMethod": "claude.ai", "email": "prueba@ejemplo.com"}))
    sys.exit(0)

prompt = valor_de("-p") or ""
resume = valor_de("--resume")
permitidas: list[str] = []
if "--allowedTools" in argv:
    for pieza in argv[argv.index("--allowedTools") + 1:]:
        if pieza.startswith("--"):
            break
        permitidas.append(pieza)
anotar("_claude_argv.log", {
    "argv": argv, "resume": resume, "permitidas": permitidas,
    "env_prohibido": sorted(k for k in os.environ if k.startswith(("CLAUDE", "ANTHROPIC"))),
})

emitir({"type": "system", "subtype": "init", "session_id": SESION, "model": "fake", "tools": permitidas})
emitir({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Task", "input": {"subagent_type": "etapa-fake"}}]}})

texto = "Listo: el nodo se ejecutó (fake)."
final = {"subtype": "success", "is_error": False}

if modo == "pregunta" and not resume:
    texto = "Necesito una decisión.\nPREGUNTA_OPERADOR: ¿Sigo con el ángulo A o con el B?"
elif modo == "pregunta" and resume:
    texto = f"Gracias, seguí con: {prompt}"
elif modo == "error":
    final = {"subtype": "error_during_execution", "is_error": True}
    texto = "Algo salió mal (fake)."
elif modo.startswith("dormir:"):
    time.sleep(float(modo.split(":", 1)[1]))
elif modo.startswith("llamar:"):
    for herramienta in modo.split(":", 1)[1].split(","):
        nombre = f"mcp__claude_ai_META_MCP__{herramienta}"
        emitir({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": nombre, "input": {"campo": "valor"}}]}})
        if nombre in permitidas:
            anotar("_meta_llamadas.log", {"herramienta": herramienta, "prompt": prompt[:80]})
            emitir({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok (fake)"}]}})
        else:
            emitir({"type": "user", "message": {"content": [
                {"type": "tool_result", "is_error": True, "content": "permiso denegado (dontAsk)"}]}})
    texto = "Llamadas intentadas (fake)."

emitir({"type": "assistant", "message": {"content": [{"type": "text", "text": texto}]}})
emitir({"type": "result", **final, "result": texto, "total_cost_usd": 0.0123, "num_turns": 3,
        "session_id": SESION})
sys.exit(0)
