#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_costear.py — GATE del costeo determinista (invariante 2 de CLAUDE.md).

Congela la regla: "las cifras salen de _DIM_COSTEO.csv, nunca de memoria" — la fila más CERCANA
al costo del pedido, y en caso de empate la fila SUPERIOR (conservador). Usa una tabla de costeo
propia en un directorio temporal (nunca la real de PRODUCTOS/): `costear.CSV_COSTEO` se
monkeypatchea igual que `decidir.PARAMS_PATH` en test_decidir.py.

USO:  python Ads/_TOOLS/test_costear.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import costear as c  # noqa: E402

COLS = ["costo_producto", "valor_envio", "costos_admin", "costo_devolucion", "total_gastos",
        "cpa_objetivo", "cpa_minimo", "cpa_real_calc", "suma_costos", "utilidad", "precio_sugerido",
        "precio_establecido", "cpa_base", "utilidad_esperada", "cpa_break_even", "pct_ingreso",
        "pct_ingreso_utilidad", "cpa_base_usd", "precio_2u", "precio_3u", "origen_escalera"]

# Tres filas separadas por Q10: 40 (empate candidato con 50 a los 45), 50 (exacta), 60 (techo).
# Los valores no vienen de la tabla real: son un fixture de control con numeros redondos, para que
# cada aserción compare contra un valor que el test mismo fijó, no contra una cifra que puede
# cambiar si el operador edita _DIM_COSTEO.csv.
FILAS = [
    dict(costo_producto="40", valor_envio="40.96", costos_admin="4.0", costo_devolucion="4.59",
         total_gastos="10.67", cpa_objetivo="22.91", cpa_minimo="30.8", cpa_real_calc="38.26",
         suma_costos="129.89", utilidad="40.33", precio_sugerido="170.22", precio_establecido="179",
         cpa_base="30.8", utilidad_esperada="40.76", cpa_break_even="71.56", pct_ingreso="0.56",
         pct_ingreso_utilidad="0.23", cpa_base_usd="4.03", precio_2u="239", precio_3u="299",
         origen_escalera="OPERADOR"),
    dict(costo_producto="50", valor_envio="42.17", costos_admin="4.0", costo_devolucion="4.59",
         total_gastos="10.67", cpa_objetivo="25.71", cpa_minimo="30.8", cpa_real_calc="38.26",
         suma_costos="141.09", utilidad="43.81", precio_sugerido="184.91", precio_establecido="189",
         cpa_base="30.8", utilidad_esperada="39.76", cpa_break_even="70.56", pct_ingreso="0.53",
         pct_ingreso_utilidad="0.21", cpa_base_usd="4.03", precio_2u="269", precio_3u="349",
         origen_escalera="OPERADOR"),
    dict(costo_producto="60", valor_envio="43.00", costos_admin="4.0", costo_devolucion="4.59",
         total_gastos="10.67", cpa_objetivo="27.00", cpa_minimo="30.8", cpa_real_calc="38.26",
         suma_costos="150.00", utilidad="45.00", precio_sugerido="190.00", precio_establecido="199",
         cpa_base="30.8", utilidad_esperada="45.00", cpa_break_even="75.00", pct_ingreso="0.52",
         pct_ingreso_utilidad="0.22", cpa_base_usd="4.03", precio_2u="289", precio_3u="369",
         origen_escalera="OPERADOR"),
]


def _tabla_temporal():
    tmp = tempfile.mkdtemp(prefix="costeo_")
    ruta = os.path.join(tmp, "_DIM_COSTEO.csv")
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(FILAS)
    return ruta


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


def _con_tabla(fn):
    """Corre `fn(ruta)` con costear.CSV_COSTEO apuntando al fixture, y lo restaura después."""
    previo = c.CSV_COSTEO
    ruta = _tabla_temporal()
    c.CSV_COSTEO = ruta
    try:
        return fn(ruta)
    finally:
        c.CSV_COSTEO = previo


def test_match_exacto():
    def correr(_ruta):
        d = c.costear(50)
        ok = (d["fila_usada"] == 50.0 and d["criterio_de_fila"] == "exacta"
              and d["precio_1u"] == 189 and d["cpa_objetivo"] == 25.71
              and d["cpa_break_even"] == 70.56 and "alerta" not in d)
        return _informe(ok, "costo Q50 == fila Q50: match exacto, cifras iguales a la fila", d)
    return _con_tabla(correr)


def test_nearest_por_debajo():
    def correr(_ruta):
        # 44 dista 4 de 40 y 6 de 50: la fila más cercana es la de ABAJO.
        d = c.costear(44)
        ok = (d["fila_usada"] == 40.0 and d["criterio_de_fila"] == "más cercana"
              and d["precio_1u"] == 179 and "alerta" not in d)
        return _informe(ok, "costo Q44: la fila más cercana es Q40 (dist 4) sobre Q50 (dist 6)", d)
    return _con_tabla(correr)


def test_nearest_por_encima():
    def correr(_ruta):
        # 47 dista 7 de 40 y 3 de 50: la fila más cercana es la de ARRIBA.
        d = c.costear(47)
        ok = (d["fila_usada"] == 50.0 and d["criterio_de_fila"] == "más cercana"
              and d["precio_1u"] == 189 and "alerta" not in d)
        return _informe(ok, "costo Q47: la fila más cercana es Q50 (dist 3) sobre Q40 (dist 7)", d)
    return _con_tabla(correr)


def test_empate_exacto_elige_la_superior():
    def correr(_ruta):
        # 45 equidista de 40 y 50 (5 cada una): ETAPA-1.md manda usar la SUPERIOR (conservador).
        d = c.costear(45)
        ok = (d["fila_usada"] == 50.0 and "empate" in d["criterio_de_fila"]
              and d["precio_1u"] == 189 and "alerta" not in d)
        return _informe(ok, "costo Q45: empate técnico Q40/Q50 -> gana la SUPERIOR (Q50), conservador", d)
    return _con_tabla(correr)


def test_techo_de_tabla_excedido():
    def correr(_ruta):
        # 100 supera la fila más alta (60): el script NO extrapola una fila nueva, usa el techo
        # y levanta una alerta explícita — main() debe devolver 1 en este caso (ver test_json_cli).
        d = c.costear(100)
        ok = (d["fila_usada"] == 60.0 and d["criterio_de_fila"] == "TECHO DE TABLA EXCEDIDO"
              and "alerta" in d and "Q100" in d["alerta"] and "Q60" in d["alerta"])
        return _informe(ok, "costo Q100 > techo Q60: usa el techo, marca alerta, NO extrapola una fila", d)
    return _con_tabla(correr)


def test_debajo_del_piso_de_tabla_sin_alerta():
    """HALLAZGO (no se corrige aquí, solo se documenta con el test — la regla del código no
    distingue "por debajo del piso" de "empate/nearest normal"): un costo MENOR que la fila más
    baja de _DIM_COSTEO.csv no dispara ninguna alerta, a diferencia de excederse por ARRIBA
    (TECHO DE TABLA EXCEDIDO). `elegir_fila()` solo chequea `costo > filas[-1][0]` para el techo;
    no existe un chequeo simétrico contra `filas[0][0]` para el piso. El costo Q10 (por debajo de
    la fila más barata, Q40) cae calladamente en la fila Q40 con criterio "más cercana", como si
    fuera un costo normal dentro de rango. Si nunca ocurre en la práctica (todo producto cuesta
    más que la fila más barata) esto es inofensivo; si algún día se ingresa un costo por error muy
    por debajo del piso, el script no lo va a señalar."""
    def correr(_ruta):
        d = c.costear(10)
        ok = d["fila_usada"] == 40.0 and d["criterio_de_fila"] == "más cercana" and "alerta" not in d
        return _informe(ok, "HALLAZGO: costo Q10 (bajo el piso Q40) NO levanta alerta, usa Q40 en silencio", d)
    return _con_tabla(correr)


def test_escalera_sale_de_la_fila():
    def correr(_ruta):
        d = c.costear(50)
        esc = {e["unidades"]: e["precio"] for e in d["escalera"]}
        ok = esc.get(1) == 189 and esc.get(2) == 269 and esc.get(3) == 349
        return _informe(ok, "escalera(costo Q50): 1u/2u/3u == precio_establecido/precio_2u/precio_3u de la fila", (d["escalera"],))
    return _con_tabla(correr)


def test_json_cli_devuelve_1_con_alerta():
    """`main()` (el CLI) devuelve 1 cuando hay alerta y 0 cuando no — es la señal que consume un
    caller de shell (nunca se parsea el texto del stdout para saber si el costeo es válido)."""
    def correr(_ruta):
        prev_argv = sys.argv
        try:
            sys.argv = ["costear.py", "100", "--json"]
            cod_alerta = c.main()
            sys.argv = ["costear.py", "50", "--json"]
            cod_ok = c.main()
        finally:
            sys.argv = prev_argv
        ok = cod_alerta == 1 and cod_ok == 0
        return _informe(ok, "main(): exit 1 con TECHO DE TABLA EXCEDIDO, exit 0 en un match limpio",
                         (cod_alerta, cod_ok))
    return _con_tabla(correr)


def test_mercado_lee_su_propia_tabla():
    """--mercado CO reads its own table (same columns, its currency) and leaves GT untouched;
    the GT start-up rule is not applied to another market."""
    def correr(ruta_gt):
        previo = dict(c.TABLAS_POR_MERCADO)
        ruta_co = _tabla_temporal()
        c.TABLAS_POR_MERCADO["CO"] = ruta_co
        try:
            co = c.costear(50, mercado="CO")
            gt = c.costear(50)
        finally:
            c.TABLAS_POR_MERCADO.clear()
            c.TABLAS_POR_MERCADO.update(previo)
        ok = (co["fuente"] == "PRODUCTOS/" + os.path.basename(ruta_co)
              and co["arranque"] is None and co.get("mercado") == "CO"
              and gt["arranque"] is not None and "mercado" not in gt
              and gt["fuente"] == "PRODUCTOS/" + os.path.basename(ruta_gt))
        return _informe(ok, "costear(mercado=CO) lee TABLAS_POR_MERCADO['CO'], sin regla de arranque GT; GT intacto",
                        (co["fuente"], co["arranque"], gt["fuente"]))
    return _con_tabla(correr)


def main():
    pruebas = [
        test_match_exacto,
        test_nearest_por_debajo,
        test_nearest_por_encima,
        test_empate_exacto_elige_la_superior,
        test_techo_de_tabla_excedido,
        test_debajo_del_piso_de_tabla_sin_alerta,
        test_escalera_sale_de_la_fila,
        test_json_cli_devuelve_1_con_alerta,
        test_mercado_lee_su_propia_tabla,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
