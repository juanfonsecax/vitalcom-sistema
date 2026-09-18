"""Spike C: workflow DBOS de 3 pasos con espera de aprobación (recv) sobre SQLite.
Corrida 1 (MATAR=1): muere a mitad del paso 2. Corrida 2: retoma, recibe la aprobación y termina."""
import os, sys, time
from dbos import DBOS, SetWorkflowID

DBOS(config={"name": "spike-c", "system_database_url": "sqlite:///dbos.sqlite"})
LOG = "log.txt"
def anotar(s):
    with open(LOG, "a", encoding="utf-8") as f: f.write(f"{time.strftime('%H:%M:%S')} pid={os.getpid()} {s}\n")

@DBOS.step()
def paso1():
    anotar("paso1 ejecutado (costear)"); return {"p1u": 199}

@DBOS.step()
def paso2(dato):
    anotar("paso2 inicio")
    if os.environ.get("MATAR") == "1":
        anotar("paso2 -> os._exit(1) simulando caída del proceso"); os._exit(1)
    anotar("paso2 fin"); return dato["p1u"] * 1

@DBOS.step()
def paso3(v):
    anotar(f"paso3 ejecutado (publicar) con v={v}"); return "publicado"

@DBOS.workflow()
def flujo():
    d = paso1()
    v = paso2(d)
    anotar("esperando aprobación (recv)")
    ok = DBOS.recv("aprobacion", timeout_seconds=60)
    anotar(f"aprobación recibida: {ok}")
    if ok != "APROBADA": return "rechazada"
    return paso3(v)

if __name__ == "__main__":
    DBOS.launch()   # al lanzar, DBOS recupera los workflows PENDING de esta máquina
    if sys.argv[1] == "arrancar":
        with SetWorkflowID("wf-spike-1"):
            flujo()
    else:
        time.sleep(3)
        DBOS.send("wf-spike-1", "APROBADA", "aprobacion")
        h = DBOS.retrieve_workflow("wf-spike-1")
        print("RESULTADO:", h.get_result(), "| estado:", h.get_status().status)
    DBOS.destroy()
