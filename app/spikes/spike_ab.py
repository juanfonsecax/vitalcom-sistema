"""Spike A + B: Claude Code headless desde Python, cwd=SISTEMA, con el entorno que tendría la app
lanzada desde iniciar.bat (sin las variables que inyecta la sesión del escritorio).
A: ¿carga el subagente etapa-1 y las skills, corren los hooks, llega stream-json, qué auth usa?
B: ¿aparece el conector de Meta (claude.ai) y responde ads_get_ad_accounts (solo lectura)?"""
import json, os, subprocess, sys, time
EXE = os.environ.get("CLAUDE_EXE") or os.environ["CLAUDE_CODE_EXECPATH"]
BASE = r"C:\Users\juand\Downloads\AGENTES LUCID\Profesional en Eccomerce gestion\SISTEMA"
OUT = os.path.dirname(os.path.abspath(__file__))
env = {k: v for k, v in os.environ.items()
       if not (k.startswith("CLAUDE") or k.startswith("ANTHROPIC") or k in ("AI_AGENT", "BAGGAGE"))}

def correr(nombre, prompt, herramientas):
    cmd = [EXE, "-p", prompt, "--output-format", "stream-json", "--verbose", "--include-hook-events",
           "--permission-mode", "dontAsk", "--allowedTools", *herramientas, "--max-budget-usd", "2"]
    t0 = time.time()
    r = subprocess.run(cmd, env=env, cwd=BASE, capture_output=True, text=True, encoding="utf-8", timeout=900)
    crudo = os.path.join(OUT, f"{nombre}.jsonl"); open(crudo, "w", encoding="utf-8").write(r.stdout)
    ev = [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]
    init = next((e for e in ev if e.get("type") == "system" and e.get("subtype") == "init"), {})
    fin = next((e for e in reversed(ev) if e.get("type") == "result"), {})
    hooks = sorted({f"{e.get('hook_event', e.get('hook_name', '?'))}" for e in ev if "hook" in str(e.get("subtype", ""))})
    tareas = [b for e in ev if e.get("type") == "assistant" for b in e["message"]["content"]
              if b.get("type") == "tool_use"]
    print(f"== {nombre}: exit={r.returncode} {time.time()-t0:.0f}s eventos={len(ev)}")
    print("  apiKeySource:", init.get("apiKeySource"), "| model:", init.get("model"))
    print("  agents:", init.get("agents")); print("  skills:", init.get("skills"))
    print("  mcp_servers:", init.get("mcp_servers"))
    print("  meta_tools:", [t for t in init.get("tools", []) if "ads_get_ad_accounts" in t])
    print("  hooks vistos:", hooks)
    print("  tool_use:", [(b["name"], str(b["input"])[:120]) for b in tareas])
    print("  resultado:", fin.get("subtype"), "| costo_usd:", fin.get("total_cost_usd"), "| turns:", fin.get("num_turns"))
    print("  texto:", (fin.get("result") or "")[:1500]); print("  stderr:", r.stderr[-800:])

if "a" in sys.argv[1:]:
    correr("spikeA", "Usá la herramienta Task con subagent_type etapa-1 para costear un PRODUCTO DE PRUEBA "
           "llamado SPIKE_TEST con costo Q60, tipo suplemento, avatar mujer 35-55. Es una prueba: no escribas "
           "ningún archivo ni CSV. Devolvé la tabla de precios que te entregue el subagente.",
           ["Task", "Agent", "Read", "Bash(python Ads/_TOOLS/costear.py:*)"])
if "b" in sys.argv[1:]:
    correr("spikeB", "Llamá SOLO a la herramienta de Meta ads_get_ad_accounts (lectura) y listá nombre, id y "
           "moneda de cada cuenta. Si esa herramienta no existe en esta sesión, decí exactamente 'NO_DISPONIBLE'.",
           ["mcp__*"])
