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

RESUELTO 2026-09-02 — una sola escalera
──────────────────────────────────────
Habia dos escaleras en circulacion: la tabla de ETAPA-1.md y la regla `costo x
1.7` del codigo. `_DIM_PRECIOS.csv` desempato con datos de Dropi: TINNIDROP en
la fila Q40 vende a 179/239/299 con n=102/42/18 ordenes reales, que es la tabla,
no la regla (habria dado 179/249/319). Ahora la escalera vive SOLO en
`_DIM_COSTEO.csv` (columnas precio_2u, precio_3u, origen_escalera) y la regla
x1.7 se usa unicamente para extrapolar los costos Q85-Q130 que el operador
nunca fijo, marcados como EXTRAPOLADO.

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
# Costing table per market. GT is the default and keeps CSV_COSTEO; other markets have
# their own table with the same columns, in their own currency.
TABLAS_POR_MERCADO = {"CO": os.path.join(BASE, "PRODUCTOS", "_DIM_COSTEO_CO.csv")}

# Parámetros de la regla de arranque (ETAPA-1.md Paso 2.5). Los fijos de logística
# no bajan con el precio: es lo que dispara el múltiplo en productos baratos.
TASA_ENTREGA = 0.83          # 17 % de devoluciones, calibrado contra _TASA_ENTREGA.csv
COSTO_DEVOLUCION = 27.0
FIJOS = 40.0                 # flete Q34 + admin Q4 + otros Q2
CPA_PEOR = 63.0              # mismo default que gen_dashboard.arranque_recomendado


def cargar_tabla(ruta=None):
    """Filas de _DIM_COSTEO.csv ordenadas por costo, con su valor REAL.

    `gen_dashboard.py` lee la fila Q54 como el escalón Q55 para que su grilla
    quede en múltiplos de 5; eso es cosmético del dashboard y NO debe usarse
    acá: con Q55 la distancia a un costo de Q57 sale 2 y elige esa fila,
    mientras que con el valor real Q54 sale 3 y empata con Q60 — que es la fila
    que el operador usa de verdad para CLEARSTEM.
    """
    ruta = ruta or CSV_COSTEO
    if not os.path.exists(ruta):
        sys.exit(f"ERROR: no existe {ruta}. Sin la tabla no hay costeo.")
    filas = []
    with io.open(ruta, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                c = float(r["costo_producto"])
            except (KeyError, ValueError):
                continue
            filas.append((c, r))
    if not filas:
        sys.exit(f"ERROR: {ruta} no tiene filas legibles.")
    return sorted(filas, key=lambda x: x[0])


def elegir_fila(costo, filas):
    """La fila MÁS CERCANA; en empate, la superior (conservador).

    ETAPA-1.md dice las dos cosas —"la fila con el valor más cercano" y "si está
    entre dos valores, usar el superior"— y la práctica real desempata:
      · TINNIDROP costo Q41 usa fila Q40 (más cercano), no Q45. Sus precios
        desplegados son 179/239/299, los de la fila Q40, con n=102 órdenes.
      · NUSAVA costo Q55 usa fila Q54 (más cercano), no Q60.
      · CLEARSTEM costo Q57 empata entre Q54 y Q60 → Q60, el superior.
    Nunca se interpola: siempre cae en una fila existente.
    """
    exactas = [(c, r) for c, r in filas if c == costo]
    if exactas:
        return exactas[0][0], exactas[0][1], "exacta"
    if costo > filas[-1][0]:
        c, r = filas[-1]
        return c, r, "TECHO DE TABLA EXCEDIDO"
    # Ordena por distancia; a igual distancia gana el costo mayor (conservador).
    c, r = min(filas, key=lambda x: (abs(x[0] - costo), -x[0]))
    crit = "más cercana" + (" (empate → superior)" if any(
        abs(o - costo) == abs(c - costo) and o != c for o, _ in filas) else "")
    return c, r, crit


def escalera(costo_u, fila, n=3):
    """La escalera sale del CSV, no de una fórmula.

    `precio_2u` y `precio_3u` de _DIM_COSTEO.csv son los precios que fijó el
    operador, y son los que Dropi confirma: TINNIDROP en la fila Q40 vende a
    179/239/299 con n=102/42/18 órdenes reales. La regla `costo × 1.7` que se
    usaba antes daba 179/249/319 para esa misma fila — aproximaba la escalera
    sin reproducirla. Ahora solo se usa para EXTRAPOLAR los costos que el
    operador nunca fijó (Q85-Q130), y esas filas van marcadas como tales en
    `origen_escalera`.
    """
    p1 = int(float(fila["precio_establecido"]))
    precios = [p1]
    for k in ("precio_2u", "precio_3u"):
        v = fila.get(k)
        precios.append(int(float(v)) if v not in (None, "") else None)
    # Escalones por encima del 3u: se extienden con el último salto conocido.
    if n > 3 and precios[2] and precios[1]:
        salto = precios[2] - precios[1]
        precios += [precios[2] + salto * i for i in range(1, n - 2)]
    return [{"unidades": u, "precio": p, "costo_pedido": round(costo_u * u, 2)}
            for u, p in enumerate(precios[:n], start=1) if p is not None]


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


def costear(costo, n_unidades=3, mercado="GT"):
    if mercado == "GT":
        ruta = CSV_COSTEO
    elif mercado in TABLAS_POR_MERCADO:
        ruta = TABLAS_POR_MERCADO[mercado]
    else:
        sys.exit(f"ERROR: no hay tabla de costeo para el mercado {mercado}.")
    filas = cargar_tabla(ruta)
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
        "escalera": escalera(costo_fila, r, max(3, n_unidades)),
        # El arranque se evalúa sobre el costo REAL: el múltiplo es un diagnóstico
        # del producto, no de la grilla. Con costo Q35 el múltiplo es 4.4x — que es
        # el número que cita ETAPA-1.md Paso 2.5 — no el 4.0x de la fila Q40.
        # The start-up rule (1u vs 2x1) is calibrated on Guatemala logistics in quetzales.
        "arranque": arranque(float(costo)) if mercado == "GT" else None,
        "fuente": "PRODUCTOS/" + os.path.basename(ruta),
        "origen_escalera": r.get("origen_escalera", "OPERADOR"),
    }
    if mercado != "GT":
        out["mercado"] = mercado
    if criterio == "TECHO DE TABLA EXCEDIDO":
        out["alerta"] = (f"El costo Q{costo} supera el techo de la tabla (Q{costo_fila:.0f}). "
                         "Las cifras NO son válidas: extender _DIM_COSTEO.csv antes de usarlas.")
    return out


def imprimir(d, Q="Q"):
    """`Q` is the market currency symbol (GT quetzal by default)."""
    a = d["arranque"]
    print(f"\nCOSTEO — costo de pedido {Q}{d['costo_ingresado']:.0f}")
    print("=" * 58)
    print(f"Fila de tabla usada .... {Q}{d['fila_usada']:.0f}  ({d['criterio_de_fila']})")
    print(f"Fuente ................. {d['fuente']}")
    if "alerta" in d:
        print(f"\n  *** {d['alerta']} ***")
    print("\nPRECIOS (envío gratis en todos)")
    for e in d["escalera"]:
        marca = "  <- OFERTA HÉROE" if e["unidades"] == 2 else ""
        print(f"  {e['unidades']}u ... {Q}{e['precio']:<6} (costo del pedido {Q}{e['costo_pedido']:.0f}){marca}")
    if d["origen_escalera"] == "EXTRAPOLADO":
        print("\n  *** escalera EXTRAPOLADA: el operador nunca fijó precio para este costo.")
        print("      Confirmar con él antes de publicarla. ***")
    elif d["origen_escalera"] == "PENDIENTE":
        print("\n  *** escalera 2u/3u PENDIENTE: el operador no la fijó para este costo. ***")
    elif "mercado" in d:
        print(f"\n  escalera fijada por el operador en {d['fuente']}, aún sin ventas que la confirmen")
    else:
        print("\n  escalera fijada por el operador en _DIM_COSTEO.csv, confirmada contra Dropi")
    print("\nUMBRALES DE PAUTA")
    print(f"  CPA objetivo ......... {Q}{d['cpa_objetivo']:.2f}")
    print(f"  CPA base ............. {Q}{d['cpa_base']:.2f}")
    print(f"  CPA BREAK-EVEN ....... {Q}{d['cpa_break_even']:.2f}   <- techo, no objetivo")
    if a:
        print(f"\nARRANQUE: {a['decision']}")
        print(f"  P1u mínimo Q{a['p1u_minimo']:.2f} = múltiplo {a['multiplo_necesario']:.2f}x del costo")
        print(f"  {a['nota']}")
    else:
        print("\nARRANQUE: la regla 1u vs 2x1 está calibrada para Guatemala; no aplica a este mercado.")
    print("\nLo que este script NO decide (queda para etapa-1):")
    print("  la arquitectura de oferta segun tipo de producto y nivel de")
    print("  conciencia del avatar — matriz del Paso 2 de ETAPA-1.md.\n")


def main():
    ap = argparse.ArgumentParser(description="Costeo determinista desde _DIM_COSTEO.csv")
    ap.add_argument("costo", type=float,
                    help="costo del PEDIDO COMPLETO en Q (en combos, no el de la unidad)")
    ap.add_argument("--unidades", type=int, default=3, help="escalones a calcular (default 3)")
    ap.add_argument("--json", action="store_true", help="salida JSON para consumo por una etapa")
    ap.add_argument("--mercado", default="GT",
                    help="mercado del producto (default GT); CO lee _DIM_COSTEO_CO.csv, en pesos")
    args = ap.parse_args()

    if args.costo <= 0:
        sys.exit("ERROR: el costo debe ser mayor que 0.")

    mercado = args.mercado.strip().upper()
    d = costear(args.costo, args.unidades, mercado)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    elif mercado == "GT":
        imprimir(d)
    else:
        import mercado as mc
        imprimir(d, mc.perfil_mercado(mercado, BASE)["simbolo"])
    return 1 if "alerta" in d else 0


if __name__ == "__main__":
    sys.exit(main())
