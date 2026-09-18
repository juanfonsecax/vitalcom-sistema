"""Spike F (Hito 4): ¿sirve ads_creative_upload_media con LOCAL_FILE en headless?
Candado: allowedTools NO incluye ninguna herramienta de Meta, así que la sesión no puede llamar a Meta
aunque quisiera (dontAsk niega lo no autorizado). Solo mira la definición de la herramienta."""
import json, os, subprocess, time
EXE = os.environ.get("CLAUDE_EXE") or os.environ["CLAUDE_CODE_EXECPATH"]
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
env = {k: v for k, v in os.environ.items()
       if not (k.startswith("CLAUDE") or k.startswith("ANTHROPIC") or k in ("AI_AGENT", "BAGGAGE"))}
PROMPT = ("NO llames a ninguna herramienta de Meta. Solo usá ToolSearch con la consulta "
          "'select:mcp__claude_ai_META_MCP__ads_creative_upload_media' para cargar su definición y copiá "
          "TEXTUAL la sección de la descripción sobre 'Local files' y los valores permitidos de upload_source. "
          "Después respondé: ¿esta sesión (claude -p, sin pantalla) soporta 'interactive MCP Apps'? "
          "Si la herramienta no existe, decí 'NO_DISPONIBLE'.")
cmd = [EXE, "-p", PROMPT, "--output-format", "stream-json", "--verbose", "--permission-mode", "dontAsk",
       "--allowedTools", "ToolSearch", "--max-budget-usd", "1"]
t0 = time.time()
r = subprocess.run(cmd, env=env, cwd=BASE, capture_output=True, text=True, encoding="utf-8", timeout=600)
open(os.path.join(OUT, "spikeF.jsonl"), "w", encoding="utf-8").write(r.stdout)
ev = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]
init = next((e for e in ev if e.get("type") == "system" and e.get("subtype") == "init"), {})
fin = next((e for e in reversed(ev) if e.get("type") == "result"), {})
usos = [(b["name"], str(b["input"])[:150]) for e in ev if e.get("type") == "assistant"
        for b in e["message"]["content"] if b.get("type") == "tool_use"]
print(f"exit={r.returncode} {time.time()-t0:.0f}s")
print("mcp_servers:", [(s.get("name"), s.get("status")) for s in init.get("mcp_servers", [])])
print("upload en init:", [t for t in init.get("tools", []) if "upload_media" in t])
print("tool_use:", usos)
print("resultado:", fin.get("subtype"), "| costo:", fin.get("total_cost_usd"))
print("texto:", (fin.get("result") or "")[:2500])
