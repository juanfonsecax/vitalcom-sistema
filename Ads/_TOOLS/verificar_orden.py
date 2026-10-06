#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verificar_orden.py — GATE DE LA ORDEN: verifica que Meta quedó en el estado ordenado.

POR QUE EXISTE (Hito 5, 19-sep-2026):
------------------------------------
Cierra el ciclo de ejecución en Meta: compara el snapshot fresco de Meta obtenido
tras la ejecución contra la orden literal generada por gen_ordenes.py.
Confirma que cada ads_update_entity tuvo el efecto deseado (status PAUSED o daily_budget actualizado).

USO:
    python Ads/_TOOLS/verificar_orden.py --orden orden.json --snapshot snapshot.json
    python Ads/_TOOLS/verificar_orden.py --producto TINNIDROP --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
"""
import argparse
import io
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presupuesto_meta as pm  # dueño único de las unidades de presupuesto de Meta

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")


def cargar_snapshot(ruta):
    if not ruta or not os.path.exists(ruta):
        return {}
    with io.open(ruta, encoding="utf-8") as fh:
        d = json.load(fh)
    objetos = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
    if isinstance(objetos, str):
        try:
            objetos = json.loads(objetos)
        except Exception:
            objetos = []
    moneda = (str(d.get("moneda") or "").strip().upper() if isinstance(d, dict) else "")
    out = {}
    for o in objetos:
        nombre = (o.get("name") or "").strip()
        oid = (o.get("id") or "").strip()
        nivel = (o.get("nivel") or o.get("entity_type") or "").strip().lower()
        status = (o.get("status") or o.get("effective_status") or "").strip().upper()
        daily_budget = o.get("daily_budget")
        item = {
            "id": oid,
            "name": nombre,
            "nivel": nivel,
            "status": status,
            "daily_budget": daily_budget,
            "moneda": moneda,
        }
        if nombre:
            out[nombre] = item
        if oid:
            out[oid] = item
    return out


def verificar(orden_data, snapshot_ruta):
    if not os.path.exists(snapshot_ruta):
        return False, [f"No existe el archivo de snapshot {snapshot_ruta}"]

    meta_objs = cargar_snapshot(snapshot_ruta)
    llamadas = orden_data.get("llamadas", [])
    discrepancias = []

    for ll in llamadas:
        # Si fue omitida por idempotencia previa, no se exige cambio nuevo pero sí que esté en estado destino
        eid = ll.get("args", {}).get("entity_id") or ll.get("entidad", {}).get("id")
        nombre_ent = ll.get("entidad", {}).get("nombre")
        fields = ll.get("args", {}).get("fields", {})

        meta_ent = meta_objs.get(eid) or (meta_objs.get(nombre_ent) if nombre_ent else None)
        if not meta_ent:
            discrepancias.append(
                f"Llamada #{ll.get('n')}: entidad '{eid}' ({nombre_ent}) no existe en el snapshot de Meta."
            )
            continue

        if "status" in fields:
            status_esperado = str(fields["status"]).strip().upper()
            status_real = str(meta_ent.get("status", "")).strip().upper()
            if status_real != status_esperado:
                discrepancias.append(
                    f"Llamada #{ll.get('n')}: status de '{nombre_ent}' ({eid}) es '{status_real}', esperado '{status_esperado}'."
                )

        if "daily_budget" in fields:
            # Expected is an integer in minor units; the snapshot's real budget is converted
            # through presupuesto_meta (Meta object or plain number + top-level moneda).
            try:
                esperado_menor = int(round(float(fields["daily_budget"])))
            except (TypeError, ValueError):
                esperado_menor = None
            budget_real_raw = meta_ent.get("daily_budget")
            mayor, moneda = pm.leer_presupuesto(budget_real_raw, meta_ent.get("moneda") or None)
            real_menor = pm.a_unidad_menor(mayor, moneda) if mayor is not None else None

            if esperado_menor is None or real_menor is None or abs(real_menor - esperado_menor) > 1:
                discrepancias.append(
                    f"Llamada #{ll.get('n')}: daily_budget de '{nombre_ent}' ({eid}) es '{budget_real_raw}', esperado '{fields['daily_budget']}' (unidad menor)."
                )

    return len(discrepancias) == 0, discrepancias


def main():
    parser = argparse.ArgumentParser(description="Verifica que Meta quedó en el estado ordenado.")
    parser.add_argument("--orden", help="Ruta al archivo JSON de la orden")
    parser.add_argument("--producto", help="Producto key (para generar orden al vuelo si no se pasó --orden)")
    parser.add_argument("--snapshot", required=True, help="Ruta al snapshot fresco de Meta")
    parser.add_argument("--escribir", action="store_true", help="Bandera de escritura (compatibilidad con contrato)")
    args = parser.parse_args()

    if args.orden and os.path.exists(args.orden):
        with io.open(args.orden, encoding="utf-8") as fh:
            orden_data = json.load(fh)
    elif args.producto:
        # Generar orden al vuelo
        from gen_ordenes import generar_ordenes
        orden_data = generar_ordenes(producto_filtro=args.producto, ruta_snapshot=args.snapshot)
    else:
        print("ERROR: Debe especificar --orden o --producto.")
        return 2

    ok, fallas = verificar(orden_data, args.snapshot)

    print("=" * 78)
    print(f"VERIFICACIÓN DE ORDEN CONTRA META  ·  {orden_data.get('producto', 'GENERAL')}")
    print("=" * 78)
    print(f"  Snapshot analizado: {args.snapshot}")
    print(f"  Total llamadas verificadas: {len(orden_data.get('llamadas', []))}")
    print()

    if not ok:
        print("  FALLO DE VERIFICACIÓN:")
        for f in fallas:
            print(f"    X {f}")
        print()
        print("  La orden no coincide con el estado real de Meta.")
        return 1

    print("  VERIFICACIÓN EXITOSA: Todas las entidades en Meta coinciden con la orden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
