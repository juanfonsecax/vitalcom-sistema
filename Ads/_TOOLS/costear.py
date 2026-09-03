#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""costear.py — la parte DETERMINISTA del costeo, sin modelo de lenguaje.

Por qué existe
──────────────
`etapa-1` tenía dos trabajos mezclados: buscar cifras en una tabla (determinista)
y elegir la arquitectura de oferta según tipo de producto y avatar (juicio). La
primera mitad no necesita un LLM y, peor, exponía al sistema a que inventara una
cifra — justo lo que el invariante 2 de CLAUDE.md prohíbe con una advertencia en
prosa. Este script la vuelve imposible: los números salen del CSV o no salen.

`etapa-1` lo ejecuta y aplica su juicio SOBRE este output, nunca en lugar de él.

Fuentes de verdad (este script no inventa ninguna cifra)
───────────────────────────────────────────────────────
  · PRODUCTOS/_DIM_COSTEO.csv ..... P1u, CPA base, CPA break-even, envío, costos
  · ETAPA-1.md Paso 2.5 ........... regla de arranque 1u vs 2x1 (tabla de múltiplos)
  · gen_dashboard.py:escalera_sugerida .. regla de la escalera (costo × 1.7)

⚠️ NOTA DE DIVERGENCIA (2026-09-02). La escalera se calcula con la regla × 1.7,
que es la que usa el código vigente (`gen_dashboard.py`) y la que cita productos
reales: costo Q60 → 199/299/399 (CLEARSTEM) y costo Q40 → 179/249/319/389
(VARICOSE). La tabla en prosa de `ETAPA-1.md` da otra escalera para esos mismos
costos (Q40 → 179/239/299). Las dos no pueden ser ciertas a la vez. Mientras el
operador no resuelva cuál manda, este script usa la del código y lo declara en su
salida.

Uso
───
    python Ads/_TOOLS/costear.py 60
    python Ads/_TOOLS/costear.py 90 --json
    python Ads/_TOOLS/costear.py 45 --unidades 3

En productos COMBO (2x1, 4x2) el costo que entra es el del PEDIDO COMPLETO, no
el de la unidad. VARICOSE vende 2 frascos de Q45 → se pasa 90, no 45.
"""

import argparse
import csv
import io
import json
import os
import sys

# La consola de Windows arranca en cp1252 y parte los acentos y los guiones
# largos de la salida. Se fuerza UTF-8 sin romper si el flujo no lo soporta.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_COSTEO = os.path.join(BASE, "PRODUCTOS", "_DIM_COSTEO.csv")

# Parámetros de la regla de arranque (ETAPA-1.md Paso 2.5). Los fijos de logística
# no bajan con el precio: es lo que dispara el múltiplo en productos baratos.
TASA_ENTREGA = 0.83          # 17 % de devoluciones, calibrado contra _TASA_ENTREGA.csv
COSTO_DEVOLUCION = 27.0
FIJOS = 40.0                 # flete Q34 + admin Q4 + otros Q2
CPA_PEOR = 63.0              # mismo default que gen_dashboard.arranque_recomendado


def cargar_tabla():
    """Filas de _DIM_COSTEO.csv ordenadas por costo. La fila Q54 del xlsx es el
    escalón Q55 (mismo criterio que gen_dashboard.py:154)."""
    if not os.path.exists(CSV_COSTEO):
        sys.exit(f"ERROR: no existe {CSV_COSTEO}. Sin la tabla no hay costeo.")
    filas = []
    with io.open(CSV_COSTEO, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                c = float(r["costo_producto"])
            except (KeyError, ValueError):
                continue
            filas.append((55.0 if c == 54.0 else c, r))
    if not filas:
        sys.exit(f"ERROR: {CSV_COSTEO} no tiene filas legibles.")
    return sorted(filas, key=lambda x: x[0])


def elegir_fila(costo, filas):
    """Regla de aproximación de ETAPA-1.md: si el costo no está en la tabla, se
    usa la fila SUPERIOR (conservador). Nunca se interpola."""
    exactas = [(c, r) for c, r in filas if c == costo]
    if exactas:
        return exactas[0][0], exactas[0][1], "exacta"
    superiores = [(c, r) for c, r in filas if c > costo]
    if superiores:
        return superiores[0][0], superiores[0][1], "superior (conservador)"
    # Por encima del techo de la tabla: se usa la última y se avisa fuerte.
    c, r = filas[-1]
    return c, r, "TECHO DE TABLA EXCEDIDO"


def escalera(costo_u, precio_1u, n=4):
    """Cada unidad extra se cobra a `costo unitario × 1.7`, redondeado a la decena.
    Regla canónica en gen_dashboard.py:escalera_sugerida."""
    inc = round(costo_u * 1.7 / 10.0) * 10
    return [{"unidades": u,
             "precio": int(precio_1u + (u - 1) * inc),
             "costo_pedido": round(costo_u * u, 2)}
            for u in range(1, n + 1)]


def arranque(costo_u):
    """¿Arrancar en 1 unidad o directo en 2x1? Lo decide el MÚLTIPLO del costo que
    habría que cobrar por una unidad, no el margen. ETAPA-1.md Paso 2.5."""
    p1u_min = (CPA_PEOR + (1 - TASA_ENTREGA) * COSTO_DEVOLUCION) / TASA_ENTREGA + costo_u + FIJOS
    mult = p1u_min / costo_u if costo_u else 0.0
    if costo_u <= 40:
        dec, nota = "2X1", "Arrancar en 2x1. No ofrecer 1u suelta como entrada."
    elif costo_u <= 55:
        dec, nota = ("CRITERIO",
                     "Zona de criterio: si la categoría tiene ancla de precio conocida "
                     "(crema, repelente, suplemento común), el 2x1 juega a favor; si no, 1u funciona.")
    else:
        dec, nota = "1U", "1 unidad viable, con 2u/3u/4u como upsell."
    return {"p1u_minimo": round(p1u_min, 2), "multiplo_necesario": round(mult, 2),
            "decision": dec, "nota": nota}


def costear(costo, n_unidades=3):
    filas = cargar_tabla()
    costo_fila, r, criterio = elegir_fila(float(costo), filas)
    g = lambda k: float(r[k]) if r.get(k) not in (None, "") else None

    p1u = int(g("precio_establecido"))
    out = {
        "costo_ingresado": float(costo),
        "fila_usada": costo_fila,
        "criterio_de_fila": criterio,
        "precio_1u": p1u,
        "cpa_objetivo": g("cpa_objetivo"),
        "cpa_base": g("cpa_base"),
        "cpa_break_even": g("cpa_break_even"),
        "valor_envio": g("valor_envio"),
        "utilidad_esperada": g("utilidad_esperada"),
        # La escalera parte de la FILA: su precio base (P1u) también sale de ahí,
        # y mezclar costo real con precio de tabla daría una escalera incoherente.
        "escalera": escalera(costo_fila, p1u, max(3, n_unidades)),
        # El arranque se evalúa sobre el costo REAL: el múltiplo es un diagnóstico
        # del producto, no de la grilla. Con costo Q35 el múltiplo es 4.4x — que es
        # el número que cita ETAPA-1.md Paso 2.5 — no el 4.0x de la fila Q40.
        "arranque": arranque(float(costo)),
        "fuente": "PRODUCTOS/_DIM_COSTEO.csv",
        "regla_escalera": "costo x 1.7 redondeado a la decena (gen_dashboard.py)",
    }
    if criterio == "TECHO DE TABLA EXCEDIDO":
        out["alerta"] = (f"El costo Q{costo} supera el techo de la tabla (Q{costo_fila:.0f}). "
                         "Las cifras NO son válidas: extender _DIM_COSTEO.csv antes de usarlas.")
    return out


def imprimir(d):
    a = d["arranque"]
    print(f"\nCOSTEO — costo de pedido Q{d['costo_ingresado']:.0f}")
    print("=" * 58)
    print(f"Fila de tabla usada .... Q{d['fila_usada']:.0f}  ({d['criterio_de_fila']})")
    print(f"Fuente ................. {d['fuente']}")
    if "alerta" in d:
        print(f"\n  *** {d['alerta']} ***")
    print("\nPRECIOS (envío gratis en todos)")
    for e in d["escalera"]:
        marca = "  <- OFERTA HÉROE" if e["unidades"] == 2 else ""
        print(f"  {e['unidades']}u ... Q{e['precio']:<6} (costo del pedido Q{e['costo_pedido']:.0f}){marca}")
    print(f"\n  regla de escalera: {d['regla_escalera']}")
    print("\nUMBRALES DE PAUTA")
    print(f"  CPA objetivo ......... Q{d['cpa_objetivo']:.2f}")
    print(f"  CPA base ............. Q{d['cpa_base']:.2f}")
    print(f"  CPA BREAK-EVEN ....... Q{d['cpa_break_even']:.2f}   <- techo, no objetivo")
    print(f"\nARRANQUE: {a['decision']}")
    print(f"  P1u mínimo Q{a['p1u_minimo']:.2f} = múltiplo {a['multiplo_necesario']:.2f}x del costo")
    print(f"  {a['nota']}")
    print("\nLo que este script NO decide (queda para etapa-1):")
    print("  la arquitectura de oferta segun tipo de producto y nivel de")
    print("  conciencia del avatar — matriz del Paso 2 de ETAPA-1.md.\n")


def main():
    ap = argparse.ArgumentParser(description="Costeo determinista desde _DIM_COSTEO.csv")
    ap.add_argument("costo", type=float,
                    help="costo del PEDIDO COMPLETO en Q (en combos, no el de la unidad)")
    ap.add_argument("--unidades", type=int, default=3, help="escalones a calcular (default 3)")
    ap.add_argument("--json", action="store_true", help="salida JSON para consumo por una etapa")
    args = ap.parse_args()

    if args.costo <= 0:
        sys.exit("ERROR: el costo debe ser mayor que 0.")

    d = costear(args.costo, args.unidades)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        imprimir(d)
    return 1 if "alerta" in d else 0


if __name__ == "__main__":
    sys.exit(main())
