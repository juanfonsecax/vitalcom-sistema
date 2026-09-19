#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reingreso_f1.py — REGISTRO DE RETORNO A FASE 1 POR FATIGA.

Cuando un ángulo ganador se fatiga o todos los conceptos fallan, el producto
vuelve a FASE 1 para investigar y probar ángulos frescos.
Este script:
  1. Identifica los ángulos ya probados en _DIM_CONJUNTOS.csv y _FACT_VENTAS.csv.
  2. Registra el evento REINGRESO_F1 en PRODUCTOS/_EVENTOS.csv con la lista de
     ángulos excluidos para que etapa-2 no los repita.
  3. Deja al producto situado en F1 listo para la nueva tanda.

USO:
    python Ads/_TOOLS/reingreso_f1.py --producto TINNIDROP --motivo "Fatiga de ángulo ACCESIBILIDAD_MEDICO"
    python Ads/_TOOLS/reingreso_f1.py --producto TINNIDROP --dry-run --json
"""
import argparse
import csv
import datetime
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD_DIR = os.path.join(BASE_DIR, "PRODUCTOS")


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def angulos_probados(base_dir, pk):
    """Obtiene la lista ordenada y sin duplicados de ángulos testeados por el producto."""
    angulos = set()
    dim_conj = os.path.join(base_dir, "PRODUCTOS", "_DIM_CONJUNTOS.csv")
    for r in leer_csv(dim_conj):
        if (r.get("producto_key") or "").strip() == pk:
            a = (r.get("angulo_key") or "").strip()
            if a:
                angulos.add(a)
    fact_ventas = os.path.join(base_dir, "PRODUCTOS", "_FACT_VENTAS.csv")
    for r in leer_csv(fact_ventas):
        if (r.get("producto_key") or "").strip() == pk:
            cj = (r.get("conjunto") or "").strip()
            for c in leer_csv(dim_conj):
                if (c.get("conjunto_meta") or "").strip() == cj:
                    a = (c.get("angulo_key") or "").strip()
                    if a:
                        angulos.add(a)
    return sorted(angulos)


def anexar_evento(base_dir, fila):
    eventos_path = os.path.join(base_dir, "PRODUCTOS", "_EVENTOS.csv")
    cols = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
            "valor_antes", "valor_despues", "motivo", "fuente_decision"]
    if os.path.exists(eventos_path):
        with io.open(eventos_path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell():
                fh.seek(-1, os.SEEK_END)
                sin_salto = fh.read(1) != b"\n"
            else:
                sin_salto = False
        if sin_salto:
            with io.open(eventos_path, "ab") as fh:
                fh.write(b"\r\n")
    with io.open(eventos_path, "a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n").writerow(fila)


def ejecutar_reingreso(pk, motivo=None, base_dir=None, dry_run=False):
    base_dir = base_dir or BASE_DIR
    prod_csv = os.path.join(base_dir, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    prods = leer_csv(prod_csv)
    p_info = next((p for p in prods if (p.get("producto_key") or "").strip() == pk), None)
    if not p_info:
        return {"ok": False, "error": f"Producto '{pk}' no existe en _DIM_PRODUCTOS.csv"}

    fase_actual = (p_info.get("fase") or "F2").strip()
    cuenta = (p_info.get("cuenta_alias") or "*").strip()
    excluidos = angulos_probados(base_dir, pk)
    motivo_limpio = (motivo or "Fatiga de ángulo / rotación integral").strip()
    excl_str = ", ".join(excluidos) if excluidos else "ninguno"
    motivo_completo = f"{motivo_limpio}. Ángulos excluidos: {excl_str}"

    fila = {
        "fecha": datetime.date.today().isoformat(),
        "producto_key": pk,
        "cuenta_alias": cuenta,
        "campana_clave": "*",
        "conjunto_meta": "*",
        "evento": "REINGRESO_F1",
        "valor_antes": fase_actual,
        "valor_despues": "F1",
        "motivo": motivo_completo,
        "fuente_decision": "operador (app)"
    }

    if not dry_run:
        anexar_evento(base_dir, fila)

    return {
        "ok": True,
        "producto_key": pk,
        "evento": "REINGRESO_F1",
        "fase_origen": fase_actual,
        "fase_destino": "F1",
        "angulos_excluidos": excluidos,
        "motivo": motivo_completo,
        "fila_evento": fila,
        "dry_run": dry_run
    }


def main():
    ap = argparse.ArgumentParser(description="Registra retorno a F1 por fatiga excluyendo ángulos probados")
    ap.add_argument("--producto", required=True, help="producto_key a retornar a F1")
    ap.add_argument("--motivo", default="Ángulo fatigado / rotación", help="Motivo de la fatiga o decisión")
    ap.add_argument("--base", default=None, help="Ruta base para pruebas o fixtures")
    ap.add_argument("--dry-run", action="store_true", help="No escribe cambios en disco")
    ap.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = ap.parse_args()

    res = ejecutar_reingreso(args.producto.strip(), args.motivo, args.base, args.dry_run)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if not res.get("ok"):
            print("ERROR:", res.get("error"))
            return 1
        print(f"REINGRESO A F1 REGISTRADO para {res['producto_key']}:")
        print(f"  Fase anterior: {res['fase_origen']} -> Fase nueva: {res['fase_destino']}")
        print(f"  Ángulos excluidos ({len(res['angulos_excluidos'])}): {', '.join(res['angulos_excluidos'])}")
        print(f"  Motivo: {res['motivo']}")
        if res.get("dry_run"):
            print("  [dry-run: sin escrituras en disco]")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
