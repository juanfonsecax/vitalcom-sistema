"""claude.py — el ÚNICO punto que invoca Claude Code headless (diseño Hito 3, §3.8).

Todo lo que este módulo hace está medido en el spike del Hito 0 (A y B), no supuesto:
  * Con `ANTHROPIC_API_KEY` o `CLAUDE_CODE_OAUTH_TOKEN` en el entorno se pierde el conector de
    Meta y se cobra aparte: si están, la app se NIEGA a correr y lo dice.
  * El subproceso no hereda las variables `CLAUDE*`/`ANTHROPIC*` de una sesión de escritorio.
  * Flags: `-p … --output-format stream-json --verbose --include-hook-events --permission-mode
    dontAsk --allowedTools … --max-budget-usd N`. NUNCA `--bare` (salta los hooks).
  * `dontAsk` no autoriza herramientas de MCP: cada una va por nombre exacto en `allowedTools`,
    y quien decide cuáles es la acción del manifiesto, no este módulo.
  * El `costo_usd` del resultado es un equivalente en precio de API: con la suscripción no se
    cobra. Se guarda como «equivalente».

Para las pruebas, `VITALCOM_CLAUDE_CMD` (una lista JSON, p. ej. `["python", "tests/fake_claude.py"]`)
tiene prioridad sobre el binario: ninguna prueba llama al Claude real.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import base

PREFIJOS_QUE_NO_SE_HEREDAN = ("CLAUDE", "ANTHROPIC")
VARIABLES_QUE_NO_SE_HEREDAN = ("AI_AGENT", "BAGGAGE")
CREDENCIALES_PROHIBIDAS = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
MARCA_DE_PREGUNTA = "PREGUNTA_OPERADOR:"
VIGENCIA_DE_LA_SESION_S = 60


class ClaudeNoDisponible(RuntimeError):
    """No se puede correr Claude: sin binario, sin sesión o con una credencial prohibida."""

    def __init__(self, codigo: str, detalle: str) -> None:
        super().__init__(detalle)
        self.codigo = codigo
        self.detalle = detalle


@dataclass
class ResultadoClaude:
    ok: bool
    subtype: str
    session_id: str
    texto_final: str
    pregunta: str | None
    costo_equivalente_usd: float | None
    num_turns: int | None
    duracion_s: float


# ── el binario y el entorno ───────────────────────────────────────────────────

def _version_de(carpeta: Path) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", carpeta.name)) or (0,)


def meta_falso() -> bool:
    """Indica si la perilla VITALCOM_CLAUDE_CMD_META está encendida."""
    return bool(os.environ.get("VITALCOM_CLAUDE_CMD_META"))


def resolver_binario(herramientas: list[str] | None = None) -> list[str]:
    """`VITALCOM_CLAUDE_CMD` → `VITALCOM_CLAUDE_EXE` → PATH → `~/.local/bin` → la app de escritorio.

    Del PATH nunca se toma un wrapper `.cmd`/`.bat` (cmd.exe trunca el prompt en el primer salto de línea).

    Si `herramientas` incluye alguna herramienta con prefijo `mcp__` y existe la variable
    `VITALCOM_CLAUDE_CMD_META`, se usa esa lista (Meta falso).
    """
    if herramientas and any(h.startswith("mcp__") for h in herramientas):
        comando_meta = os.environ.get("VITALCOM_CLAUDE_CMD_META")
        if comando_meta:
            lista = json.loads(comando_meta)
            if not isinstance(lista, list) or not all(isinstance(x, str) for x in lista) or not lista:
                raise ClaudeNoDisponible("CLAUDE_SIN_BINARIO", "VITALCOM_CLAUDE_CMD_META tiene que ser una lista JSON de textos.")
            return lista

    comando = os.environ.get("VITALCOM_CLAUDE_CMD")
    if comando:
        lista = json.loads(comando)
        if not isinstance(lista, list) or not all(isinstance(x, str) for x in lista) or not lista:
            raise ClaudeNoDisponible("CLAUDE_SIN_BINARIO", "VITALCOM_CLAUDE_CMD tiene que ser una lista JSON de textos.")
        return lista
    declarado = os.environ.get("VITALCOM_CLAUDE_EXE")
    if declarado and Path(declarado).is_file():
        return [declarado]
    en_el_path = shutil.which("claude")
    # Un wrapper .cmd/.bat pasa por cmd.exe, que corta los argumentos en el primer salto de
    # línea: el prompt multilínea y los flags que le siguen se pierden sin error.
    if en_el_path and Path(en_el_path).suffix.lower() not in (".cmd", ".bat"):
        return [en_el_path]
    for nombre in ("claude.exe", "claude"):
        candidato = Path.home() / ".local" / "bin" / nombre
        if candidato.is_file():
            return [str(candidato)]
    escritorio = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude-code"
    if escritorio.is_dir():
        for carpeta in sorted((c for c in escritorio.iterdir() if c.is_dir()), key=_version_de, reverse=True):
            for nombre in ("claude.exe", "claude"):
                if (carpeta / nombre).is_file():
                    return [str(carpeta / nombre)]
    raise ClaudeNoDisponible(
        "CLAUDE_SIN_BINARIO",
        "No encuentro Claude Code en esta máquina. Declará su ruta en VITALCOM_CLAUDE_EXE.",
    )


def credenciales_prohibidas_presentes() -> list[str]:
    return [nombre for nombre in CREDENCIALES_PROHIBIDAS if os.environ.get(nombre)]


def entorno_del_subproceso() -> dict[str, str]:
    """El entorno de la app menos todo lo que heredaría de una sesión de escritorio."""
    return {
        clave: valor for clave, valor in os.environ.items()
        if not clave.startswith(PREFIJOS_QUE_NO_SE_HEREDAN) and clave not in VARIABLES_QUE_NO_SE_HEREDAN
    }


def exigir_sin_credenciales() -> None:
    presentes = credenciales_prohibidas_presentes()
    if presentes:
        raise ClaudeNoDisponible(
            "CLAUDE_CREDENCIAL_PROHIBIDA",
            f"La variable {presentes[0]} está definida: con ella Claude pierde el conector de Meta y se "
            "cobra aparte. Quitala del entorno antes de arrancar la app.",
        )


# ── la sesión ─────────────────────────────────────────────────────────────────

_sesion: dict[str, Any] = {"hasta": 0.0, "valor": None}


def estado_sesion(forzar: bool = False) -> dict[str, Any]:
    """`claude auth status`: ¿hay sesión? Se recuerda 60 s para no lanzar un proceso por pantalla."""
    ahora = time.monotonic()
    if not forzar and _sesion["valor"] is not None and ahora < _sesion["hasta"]:
        return _sesion["valor"]
    valor: dict[str, Any] = {
        "logueado": False,
        "detalle": "",
        "credencial_prohibida": credenciales_prohibidas_presentes(),
        "meta_falso": meta_falso(),
    }
    try:
        completado = subprocess.run(
            [*resolver_binario(), "auth", "status"], env=entorno_del_subproceso(), cwd=str(base()),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            stdin=subprocess.DEVNULL,
        )
        estado = json.loads(completado.stdout)
        valor["logueado"] = bool(estado.get("loggedIn"))
        valor["detalle"] = estado.get("email") or estado.get("authMethod") or ""
        if not valor["logueado"]:
            valor["detalle"] = "Claude: sin sesión — abrí una terminal, corré `claude` y `/login`."
    except ClaudeNoDisponible as error:
        valor["detalle"] = error.detalle
    except (json.JSONDecodeError, subprocess.SubprocessError, OSError) as error:
        valor["detalle"] = f"No pude preguntarle a Claude por su sesión: {error}"
    _sesion["valor"], _sesion["hasta"] = valor, ahora + VIGENCIA_DE_LA_SESION_S
    return valor


def olvidar_sesion() -> None:
    _sesion["valor"], _sesion["hasta"] = None, 0.0


def exigir_sesion() -> None:
    """Para el endpoint (paso 8 del contrato): sin credencial prohibida y con sesión abierta."""
    exigir_sin_credenciales()
    estado = estado_sesion()
    if not estado["logueado"]:
        raise ClaudeNoDisponible("CLAUDE_SIN_SESION", estado["detalle"] or "Claude: sin sesión.")


# ── correr ────────────────────────────────────────────────────────────────────

def armar_argv(*, prompt: str, herramientas: list[str], presupuesto_usd: float,
               resume: str | None = None) -> list[str]:
    argv = [*resolver_binario(herramientas), "-p", prompt, "--output-format", "stream-json", "--verbose",
            "--include-hook-events", "--permission-mode", "dontAsk"]
    if resume:
        argv += ["--resume", resume]
    argv.extend(["--allowedTools", *herramientas, "--max-budget-usd", str(presupuesto_usd)])
    return argv


def pregunta_del_texto(texto: str) -> str | None:
    """Lo que sigue a `PREGUNTA_OPERADOR:` (hasta el final del texto), o None."""
    posicion = texto.rfind(MARCA_DE_PREGUNTA)
    if posicion < 0:
        return None
    return texto[posicion + len(MARCA_DE_PREGUNTA):].strip() or None


def resumir_evento(evento: dict[str, Any]) -> str | None:
    """Una línea legible para la pantalla por cada evento del stream-json (el crudo queda en la bitácora)."""
    tipo = evento.get("type")
    if tipo == "system" and evento.get("subtype") == "init":
        return f"Claude arrancó ({evento.get('model', 'modelo sin nombre')})"
    if tipo == "assistant":
        piezas = []
        for bloque in (evento.get("message") or {}).get("content", []) or []:
            if bloque.get("type") == "tool_use":
                entrada = bloque.get("input") or {}
                if bloque.get("name") in ("Task", "Agent") and entrada.get("subagent_type"):
                    piezas.append(f"arrancó {entrada['subagent_type']}")
                elif bloque.get("name") == "Skill" and entrada.get("skill"):
                    piezas.append(f"cargó la skill {entrada['skill']}")
                else:
                    piezas.append(f"usó {bloque.get('name')}")
            elif bloque.get("type") == "text" and (bloque.get("text") or "").strip():
                piezas.append((bloque["text"].strip().splitlines() or [""])[0][:160])
        return " · ".join(piezas) or None
    if tipo == "result":
        return f"Claude terminó: {evento.get('subtype')}"
    return None


def _texto_del_resultado(contenido: Any) -> str:
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return "\n".join(b.get("text", "") for b in contenido if isinstance(b, dict) and b.get("type") == "text")
    return ""


def salida_de_subagente(lineas: Iterable[str], subagente: str) -> str | None:
    """La respuesta FINAL, textual, del subagente `subagente` lanzado con Task/Agent en una corrida.

    Medido el 18-sep-2026 (Hito 4): el stream-json trae, en el evento `user` de primer nivel, el
    `tool_result` de la llamada Task con el texto completo que devolvió el subagente. La app lo guarda
    tal cual: el orquestador no tiene que volver a copiarlo (ni puede recortarlo). Si el subagente se
    lanzó más de una vez en la corrida, vale la última respuesta que no fue un error.
    """
    llamadas: set[str] = set()
    ultima: str | None = None
    for linea in lineas:
        if not linea.lstrip().startswith("{"):
            continue
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if evento.get("parent_tool_use_id"):
            continue  # lo que pasa DENTRO del subagente no es su respuesta
        for bloque in (evento.get("message") or {}).get("content", []) or []:
            if not isinstance(bloque, dict):
                continue
            if (evento.get("type") == "assistant" and bloque.get("type") == "tool_use"
                    and bloque.get("name") in ("Task", "Agent")
                    and (bloque.get("input") or {}).get("subagent_type") == subagente):
                llamadas.add(bloque.get("id", ""))
            elif (evento.get("type") == "user" and bloque.get("type") == "tool_result"
                  and bloque.get("tool_use_id") in llamadas and not bloque.get("is_error")):
                texto = _texto_del_resultado(bloque.get("content")).strip()
                if texto:
                    ultima = texto
    return ultima


def correr(
    *, prompt: str, herramientas: list[str], presupuesto_usd: float, tiempo_max_s: int,
    escribir_linea: Callable[[str], None], resume: str | None = None,
    al_arrancar: Callable[[subprocess.Popen], None] | None = None,
    debe_cortar: Callable[[], bool] | None = None,
    matar: Callable[[subprocess.Popen], None] | None = None,
) -> ResultadoClaude:
    """Una llamada headless. Cada línea de stdout va tal cual a `escribir_linea` (la bitácora)."""
    exigir_sin_credenciales()
    if any(h.startswith("mcp__") and "*" in h for h in herramientas):
        raise ValueError("una herramienta de MCP va por su nombre exacto, nunca con comodín.")
    argv = armar_argv(prompt=prompt, herramientas=herramientas, presupuesto_usd=presupuesto_usd, resume=resume)
    inicio = time.monotonic()
    proceso = subprocess.Popen(
        argv, cwd=str(base()), env=entorno_del_subproceso(), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=(os.name != "nt"),
    )
    if al_arrancar:
        al_arrancar(proceso)
    eventos: list[dict[str, Any]] = []
    errores: list[str] = []

    def _leer_stdout() -> None:
        for crudo in iter(proceso.stdout.readline, b""):
            linea = crudo.decode("utf-8", errors="replace").rstrip("\r\n")
            escribir_linea(linea)
            if linea.lstrip().startswith("{"):
                try:
                    eventos.append(json.loads(linea))
                except json.JSONDecodeError:
                    pass

    def _leer_stderr() -> None:
        for crudo in iter(proceso.stderr.readline, b""):
            errores.append(crudo.decode("utf-8", errors="replace"))

    hilos = [threading.Thread(target=_leer_stdout, daemon=True), threading.Thread(target=_leer_stderr, daemon=True)]
    for hilo in hilos:
        hilo.start()
    motivo = ""
    while True:
        try:
            proceso.wait(timeout=0.5)
            break
        except subprocess.TimeoutExpired:
            if debe_cortar and debe_cortar():
                motivo = "cancelado"
            elif tiempo_max_s and time.monotonic() - inicio > tiempo_max_s:
                motivo = "timeout"
            if motivo:
                (matar or (lambda p: p.kill()))(proceso)
                proceso.wait()
                break
    for hilo in hilos:
        hilo.join(timeout=5)

    final = next((e for e in reversed(eventos) if e.get("type") == "result"), {})
    session_id = final.get("session_id") or next((e["session_id"] for e in eventos if e.get("session_id")), "")
    texto = final.get("result") or ""
    subtype = motivo or final.get("subtype") or ("sin_resultado" if proceso.returncode == 0 else f"salida_{proceso.returncode}")
    if not texto and not final and errores:
        texto = "".join(errores)[-600:]
    return ResultadoClaude(
        ok=(subtype == "success" and not final.get("is_error")),
        subtype=subtype,
        session_id=session_id,
        texto_final=texto,
        pregunta=pregunta_del_texto(texto),
        costo_equivalente_usd=final.get("total_cost_usd"),
        num_turns=final.get("num_turns"),
        duracion_s=round(time.monotonic() - inicio, 1),
    )
