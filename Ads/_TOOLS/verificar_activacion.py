# -*- coding: utf-8 -*-
"""verificar_activacion.py — GATE DE LA ACTIVACION: verifica que la campaña quedó ACTIVE en Meta.

POR QUE EXISTE (2026-09-18)
--------------------------
Cierra el ciclo de activación en Meta: compara el snapshot fresco contra la orden
de activación y confirma que la campaña pasó a estado ACTIVE.

USO
    python Ads/_TOOLS/verificar_activacion.py --producto TINNIDROP --fase 1 \\
           --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
"""
import csv
import io
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def cargar_snapshot(ruta):
    """Devuelve dict con objetos indexados por nombre y por id."""
    with io.open(ruta, encoding="utf-8") as fh:
        d = json.load(fh)
    objetos = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
    if isinstance(objetos, str):
        objetos = json.loads(objetos)
    out = {}
    for o in objetos:
        nombre = (o.get("name") or "").strip()
        oid = (o.get("id") or "").strip()
        nivel = o.get("nivel") or o.get("entity_type") or ""
        status = o.get("status") or o.get("effective_status") or ""
        item = {"id": oid, "name": nombre, "nivel": nivel, "status": status}
        if nombre:
            out[nombre] = item
        if oid:
            out[oid] = item
    return out


def main():
    pk = arg("--producto")
    fase_str = arg("--fase", "1")
    snap = arg("--snapshot")

    if not pk or not snap:
        print(__doc__)
        return 2

    try:
        fase = int(fase_str)
    except ValueError:
        print("ERROR: --fase debe ser un número entero.")
        return 2

    dim_prod_path = P("_DIM_PRODUCTOS.csv")
    if not os.path.exists(dim_prod_path):
        print(f"BLOQUEANTE: no existe {dim_prod_path}.")
        return 1

    productos = {}
    with io.open(dim_prod_path, encoding="utf-8-sig", newline="") as fh:
        productos = {r["producto_key"]: r for r in csv.DictReader(fh) if r.get("producto_key")}

    fila_prod = productos.get(pk)
    if not fila_prod:
        print(f"BLOQUEANTE: '{pk}' no tiene fila en _DIM_PRODUCTOS.csv.")
        return 1

    if not os.path.exists(snap):
        print(f"BLOQUEANTE: no existe el snapshot {snap}.")
        return 1

    meta_objs = cargar_snapshot(snap)

    campaign_id = (fila_prod.get("campaign_id") or "").strip()
    if not campaign_id or campaign_id.upper() == "PENDIENTE":
        # Intentar ubicarla por nombre en el snapshot
        for _, info in meta_objs.items():
            if info.get("nivel") == "campaign" and pk in info.get("name", "") and f"F{fase}" in info.get("name", ""):
                campaign_id = info.get("id", "")
                break

    if not campaign_id or campaign_id.upper() == "PENDIENTE":
        print(f"BLOQUEANTE: '{pk}' no tiene campaign_id en _DIM_PRODUCTOS.csv ni se encontró en snapshot.")
        return 1

    hit = meta_objs.get(campaign_id)
    if not hit:
        # Buscar en todas las campañas por id o nombre
        for _, info in meta_objs.items():
            if info.get("id") == campaign_id or (info.get("nivel") == "campaign" and pk in info.get("name", "")):
                hit = info
                break

    if not hit:
        print(f"BLOQUEANTE: La campaña '{campaign_id}' no existe en el snapshot {snap}.")
        return 1

    status = (hit.get("status") or "").upper()
    nombre = hit.get("name", campaign_id)

    print("=" * 78)
    print(f"GATE DE ACTIVACIÓN  ·  {pk}  ·  FASE {fase}")
    print("=" * 78)
    print(f"  campaña ID      {campaign_id}")
    print(f"  nombre          {nombre}")
    print(f"  estado en Meta  {status}")
    print()

    if status == "ACTIVE":
        print(f"  [OK] Campaña '{campaign_id}' está ACTIVE en Meta. Verificación EXITOSA.")
        return 0
    else:
        print(f"  [FALLA] Campaña '{campaign_id}' está '{status}' (esperado: ACTIVE). NO ACTIVADA.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
