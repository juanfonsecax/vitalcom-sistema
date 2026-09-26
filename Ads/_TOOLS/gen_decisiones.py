#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_decisiones.py — reconstruye el warehouse y corre el motor de decision.

Es el camino COMPLETO por el que una orden de pausar, escalar o renovar llega al operador:
primero refresca la capa analitica (dbt build sobre los CSV), y recien despues corre
Ads/_TOOLS/decidir.py --escribir, que persiste PRODUCTOS/_DECISIONES.json (T6: decidir.py
por defecto SOLO LEE/calcula; --escribir es el flag que lo hace tocar disco). La aplicacion
(VISTAS/APP.html) dibuja ese JSON de forma nativa.

POR QUE EXISTE, si decidir.py ya corre solo:
    decidir.py lee el warehouse. Si nadie lo reconstruye, el motor decide sobre una capa
    analitica vieja mientras la app muestra una fecha fresca. Este archivo es el unico
    lugar donde `dbt build` se invoca, asi que el manifiesto lo declara como el generador
    de la vista `decisiones` — no a decidir.py pelado.

NO DIBUJA HTML. Hasta el 07-sep-2026 tambien renderizaba VISTAS/DECISIONES.html, una
segunda superficie para los mismos datos que quedo a la deriva: seguia pintando el estado
INDECIDIBLE_ESTRUCTURAL que el motor unificado ya no emite, no conocia RENOVAR, y crasheaba
con KeyError('por_que') contra el contrato actual del motor. Nadie lo noto porque solo se
invocaba como fallback. La vista retirada salio del repo el 22-sep-2026 (T9, junto con el
resto de `_ARCHIVO/`) — queda en el historial de git, no en el arbol de trabajo. Un dato,
un dueno: las decisiones se ven en la app.

USO:
    python Ads/_TOOLS/gen_decisiones.py           # warehouse + motor
    python Ads/_TOOLS/gen_decisiones.py --sin-dbt # solo el motor
"""
import os
import sys
import json
import datetime
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WH = os.path.join(BASE, "warehouse")
JSON = os.path.join(BASE, "PRODUCTOS", "_DECISIONES.json")
# Mismo tenant y mismo override que decidir.py (DECIDIR_TENANT_ID).
TENANT_ID = os.environ.get("DECIDIR_TENANT_ID") or "vitalcom"


def correr(cmd, cwd, env=None):
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
    r = subprocess.run(cmd, cwd=cwd, env=e, shell=True,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _capa_analitica(estado, detalle):
    """{estado, detalle, generado} — lo que el header/la app muestran de la capa analitica.

    ESTADO in {"OK", "FALLO", "OMITIDO"}. "FALLO" es lo nuevo (g07-cimientos T2, 22-sep-2026):
    hasta esta fecha un `dbt build` roto solo imprimia un aviso en consola (linea 57 de este
    archivo) y el operador nunca lo veia -- la capa analitica podia estar VIEJA o rota por dias
    sin que nadie lo notara donde de verdad mira: la app / el header de ordenes."""
    return {"estado": estado, "detalle": detalle,
            "generado": datetime.datetime.now().isoformat(timespec="seconds")}


def _escribir_capa_analitica(capa):
    """Inyecta `capa_analitica` en la decision que decidir.py acaba de escribir.

    decidir.py no conoce el resultado de dbt (corre despues, en un proceso aparte) -- por eso
    esto post-procesa la decision en vez de que decidir.py la reciba como argumento.
    P3: la verdad es raw.decisiones_json. Se lee de Postgres, se inyecta y se reescribe por
    db/escribir.reemplazar_decision(), que regenera _DECISIONES.json como espejo. Escribir el
    JSON directo en disco dejaba el espejo distinto de la base (lo detecta la guardia de drift).
    Postgres caido -> error, nunca escritura directa del JSON."""
    db_dir = os.path.join(BASE, "db")
    if db_dir not in sys.path:
        sys.path.insert(0, db_dir)
    import cargar as db_cargar  # noqa: E402
    import escribir as db_escribir  # noqa: E402

    prod_dir = os.path.dirname(JSON)
    con = db_cargar.conectar()
    try:
        db_escribir.verificar_decision_sincronizada(con, prod_dir, tenant_id=TENANT_ID)
        data = db_escribir.leer_decision_actual(con, tenant_id=TENANT_ID)
        if data is None:
            return
        data["capa_analitica"] = capa
        db_escribir.reemplazar_decision(con, data, prod_dir=prod_dir, tenant_id=TENANT_ID)
    finally:
        con.close()


def main():
    capa = _capa_analitica("OMITIDO", "warehouse/ no existe")
    if "--sin-dbt" not in sys.argv:
        if os.path.isdir(WH):
            rc, log = correr("python -m dbt.cli.main build --no-use-colors", WH,
                             {"DBT_PROFILES_DIR": "."})
            if rc == 0:
                linea = next((l for l in log.splitlines() if "PASS=" in l), "(sin resumen)")
                print("  dbt build ->", linea.strip()[-70:])
                capa = _capa_analitica("OK", linea.strip()[-200:])
            else:
                # No es fatal para decidir.py (cae a los CSV directos), pero ya NO se esconde
                # solo en stdout: se escribe en _DECISIONES.json para que la app lo muestre.
                detalle = next((l for l in log.splitlines() if "ERROR" in l.upper()), log[-200:])
                print("  ! aviso: dbt no corrio o fallo. El motor leera los CSV directamente "
                      "y la capa analitica queda VIEJA hasta que se arregle.")
                capa = _capa_analitica("FALLO", detalle.strip()[-300:])
        else:
            print("  ! aviso: no existe warehouse/, se omite dbt build")
    else:
        capa = _capa_analitica("OMITIDO", "--sin-dbt")

    rc, log = correr("python Ads/_TOOLS/decidir.py --escribir", BASE)
    if rc != 0:
        print(log[-1500:])
        return 1
    print(log.rstrip())
    _escribir_capa_analitica(capa)
    print("  escrito PRODUCTOS/_DECISIONES.json  ->  lo dibuja VISTAS/APP.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
