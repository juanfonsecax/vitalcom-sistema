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

Pedidos de publicar-meta que reconoce por su marca: `SNAPSHOT_EN:` (vuelca lo que «Meta» tiene),
`IMAGENES_EN:` (lee la biblioteca de imágenes; `VITALCOM_FAKE_NO_GUARDA_IMAGENES=1` simula que no guardó
el volcado) y `LLAMADAS_JSON:` (ejecuta la orden aprobada).

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
    """Agrega una línea. Con candado: dos etapas en paralelo son dos procesos, y en Windows dos `append`
    a la vez pueden pisarse (se perdía una línea)."""
    carpeta = Path.cwd() / "PRODUCTOS"
    if not carpeta.is_dir():
        return
    candado = carpeta / (nombre + ".candado")
    limite = time.monotonic() + 10
    while True:
        try:
            fd = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > limite:
                raise
            time.sleep(0.01)
    try:
        with open(carpeta / nombre, "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(dato, ensure_ascii=False) + "\n")
    finally:
        os.close(fd)
        os.remove(candado)


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

EXISTENTE = Path.cwd() / "PRODUCTOS" / "_meta_existente.json"
NIVEL = {"ads_create_campaign": "campaign", "ads_create_ad_set": "adset", "ads_create_ad": "ad"}


def entidades() -> list[dict]:
    return json.loads(EXISTENTE.read_text(encoding="utf-8")) if EXISTENTE.is_file() else []


def nombre_de(args: dict) -> str:
    return args.get("campaign_name") or args.get("ad_set_name") or args.get("ad_name") or args.get("name") or ""


emitir({"type": "system", "subtype": "init", "session_id": SESION, "model": "fake", "tools": permitidas})

if "PASO_ETAPA:" in prompt:
    # Un paso de una skill corrida de a una etapa (wf_pasos). `VITALCOM_FAKE_PASO_MODO` es un JSON
    # {etapa: modo} con modo exito · pregunta · error · sin_task · dormir:N. Cada corrida anota su
    # inicio y su fin en `PRODUCTOS/_pasos.log` (así se prueba que un grupo corre a la vez).
    etapa = prompt.split("PASO_ETAPA:", 1)[1].strip().splitlines()[0].strip()
    modo_paso = json.loads(os.environ.get("VITALCOM_FAKE_PASO_MODO") or "{}").get(etapa, "exito")
    inicio = time.time()
    if modo_paso.startswith("dormir:"):
        time.sleep(float(modo_paso.split(":", 1)[1]))
    texto, final = f"Paso de {etapa} hecho (fake).", {"subtype": "success", "is_error": False}
    if resume:
        texto = f"Seguí {etapa} con: {prompt.split(chr(10))[0]}"
    elif "/" in etapa:
        texto = f"SCRIPT {etapa} corrido (fake)."
    elif modo_paso != "sin_task":
        previos = next((l for l in prompt.splitlines() if "salidas anteriores" in l), "")
        emitir({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"t-{etapa}", "name": "Task", "input": {"subagent_type": etapa}}]}})
        emitir({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t-{etapa}", "content": [
            {"type": "text", "text": f"SALIDA DE {etapa} (fake)\n{previos}"}]}]}})
    if modo_paso == "pregunta" and not resume:
        texto = f"{etapa} dice NO APTO.\nPREGUNTA_OPERADOR: ¿Sigo igual o cambio de producto?"
    elif modo_paso == "error":
        final, texto = {"subtype": "error_during_execution", "is_error": True}, f"{etapa} falló (fake)."
    anotar("_pasos.log", {"etapa": etapa, "inicio": inicio, "fin": time.time(), "resume": resume})
    emitir({"type": "assistant", "message": {"content": [{"type": "text", "text": texto}]}})
    emitir({"type": "result", **final, "result": texto, "total_cost_usd": 0.01, "num_turns": 2, "session_id": SESION})
    sys.exit(0)

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
elif "SNAPSHOT_EN:" in prompt:
    # el paso 1 de publicar-meta: SOLO lectura, y vuelca lo que «Meta» tiene
    destino = prompt.split("SNAPSHOT_EN:", 1)[1].strip().splitlines()[0].strip()
    if os.environ.get("VITALCOM_FAKE_META_SIN_MCP") == "1":
        texto = "CUENTA_SIN_MCP"
    else:
        for lectura in ("ads_get_ad_accounts", "ads_get_ad_entities", "ads_get_user_pages"):
            if f"mcp__claude_ai_META_MCP__{lectura}" in permitidas:
                anotar("_meta_llamadas.log", {"herramienta": lectura, "lectura": True})
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        Path(destino).write_text(json.dumps({"cuenta_alias": "GTR 7", "ad_entities": entidades()}), encoding="utf-8")
        texto = "SNAPSHOT_LISTO"
elif "IMAGENES_EN:" in prompt:
    # leer la biblioteca de imágenes: SOLO ads_get_ad_images, y vuelca lo que «Meta» tiene con esos nombres
    destino = prompt.split("IMAGENES_EN:", 1)[1].strip().splitlines()[0].strip()
    buscar = json.loads(prompt.split("BUSCAR_JSON:", 1)[1].strip().splitlines()[0])
    if "mcp__claude_ai_META_MCP__ads_get_ad_images" in permitidas:
        anotar("_meta_llamadas.log", {"herramienta": "ads_get_ad_images", "lectura": True})
    biblioteca = Path.cwd() / "PRODUCTOS" / "_meta_imagenes.json"
    imagenes = json.loads(biblioteca.read_text(encoding="utf-8")) if biblioteca.is_file() else []
    encontradas = [i for i in imagenes if any(b.lower() in i["name"].lower() for b in buscar)]
    if os.environ.get("VITALCOM_FAKE_NO_GUARDA_IMAGENES") != "1":
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        Path(destino).write_text(json.dumps({"imagenes": encontradas}), encoding="utf-8")
    texto = "IMAGENES_LEIDAS"
elif "LLAMADAS_JSON:" in prompt:
    # el paso 3: solo «corren» las herramientas que vienen por nombre exacto en --allowedTools
    llamadas = json.loads(prompt.split("LLAMADAS_JSON:", 1)[1].strip().splitlines()[0])
    hechas: list[str] = []
    texto = ""
    for llamada in llamadas:
        nombre = f"mcp__claude_ai_META_MCP__{llamada['tool']}"
        emitir({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": nombre, "input": llamada["args"]}]}})
        if nombre not in permitidas:
            emitir({"type": "user", "message": {"content": [
                {"type": "tool_result", "is_error": True, "content": "denegado"}]}})
            final = {"subtype": "success", "is_error": True}
            texto = f"La llamada {llamada['n']} fue denegada (fake)."
            break
        if os.environ.get("VITALCOM_FAKE_META_FALLA_EN") == str(llamada["n"]):
            final = {"subtype": "success", "is_error": True}
            texto = f"La llamada {llamada['n']} falló (fake). EJECUTADAS: {','.join(hechas)}"
            break
        anotar("_meta_llamadas.log", {"herramienta": llamada["tool"], "n": llamada["n"], "args": llamada["args"]})
        if llamada["tool"] in NIVEL:
            EXISTENTE.write_text(json.dumps([*entidades(), {
                "id": f"id-{llamada['n']}", "nivel": NIVEL[llamada["tool"]],
                "name": nombre_de(llamada["args"]), "status": "PAUSED"}]), encoding="utf-8")
        hechas.append(str(llamada["n"]))
    else:
        texto = f"EJECUTADAS: {','.join(hechas)}"
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
