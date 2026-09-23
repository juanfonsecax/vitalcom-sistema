#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_bajar_lucidsales.py — GATE de la ventana de liquidacion (g07-cimientos T1, 22-sep-2026).

No toca la red: prueba solo la MECANICA de ventanas de main() (cuantos dias pide y como),
inyectando fakes en credenciales/login/elegir_tienda/procesar_ventana. La API real (login,
tiendas, meta/metrics) ya la ejercita el uso manual — acá se congela que:
  · sin --fecha/--desde/--hasta/--dias, la corrida pide upsert_fact.SETTLEMENT_WINDOW_DIAS
    ventanas de UN dia cada una (nunca un solo rango multi-dia): la API de LucidSales agrega
    por rango y no puede corregir un dia suelto si se le pide un tramo.
  · --dias 7 sigue siendo UN solo archivo de 7 dias (el control semanal no cambia).
  · --fecha puntual sigue siendo una sola ventana de 1 dia, sin ventana de liquidacion.

USO:  python Ads/_TOOLS/test_bajar_lucidsales.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bajar_lucidsales as bl  # noqa: E402


def _correr_con_fakes(argv):
    """Corre main() con la red totalmente fake, devuelve la lista de (ini, fin, forzar)
    con las que se llamo a procesar_ventana()."""
    llamadas = []

    def procesar_ventana_fake(token, quien, tienda, ini, fin, salida, forzar):
        llamadas.append((ini, fin, forzar))
        return True

    prev_argv = sys.argv
    try:
        sys.argv = ["bajar_lucidsales.py"] + argv
        with patch.object(bl, "credenciales", return_value=("a@b.com", "x")), \
             patch.object(bl, "login", return_value=("tok", "operador")), \
             patch.object(bl, "elegir_tienda", return_value=("tok2", "TIENDA")), \
             patch.object(bl, "procesar_ventana", side_effect=procesar_ventana_fake):
            bl.main()
    finally:
        sys.argv = prev_argv
    return llamadas


def test_default_pide_N_dias_sueltos_terminando_ayer(tmp):
    llamadas = _correr_con_fakes([])
    n = bl.SETTLEMENT_WINDOW_DIAS
    ok = (len(llamadas) == n
          and all(ini == fin for ini, fin, _ in llamadas)          # cada uno, UN dia
          and len(set(ini for ini, _, _ in llamadas)) == n          # n dias distintos
          and all(forzar for _, _, forzar in llamadas))             # se re-consulta si o si
    print(("  OK     " if ok else "  FALLA  ")
          + f"sin argumentos, pide {n} ventanas de 1 dia cada una, todas forzadas"
          + ("" if ok else f"\n         llamadas={llamadas}"))
    return 0 if ok else 1


def test_dias_7_sigue_siendo_un_solo_archivo(tmp):
    """Regresion: el control semanal de los lunes (--dias 7) NO debe convertirse en 7
    pedidos sueltos — la API agrega por rango, y el control es UN archivo de 7 dias."""
    llamadas = _correr_con_fakes(["--dias", "7"])
    ok = len(llamadas) == 1 and (llamadas[0][1] - llamadas[0][0]).days == 6
    print(("  OK     " if ok else "  FALLA  ")
          + "--dias 7 sigue pidiendo UN solo tramo de 7 dias (control semanal intacto)"
          + ("" if ok else f"\n         llamadas={llamadas}"))
    return 0 if ok else 1


def test_fecha_puntual_no_activa_la_ventana_de_liquidacion(tmp):
    llamadas = _correr_con_fakes(["--fecha", "2026-09-15"])
    ok = len(llamadas) == 1 and llamadas[0][0].isoformat() == "2026-09-15" \
        and llamadas[0][0] == llamadas[0][1] and llamadas[0][2] is False
    print(("  OK     " if ok else "  FALLA  ")
          + "--fecha puntual pide UN solo dia, sin forzar (uso manual intacto)"
          + ("" if ok else f"\n         llamadas={llamadas}"))
    return 0 if ok else 1


def main():
    import tempfile
    pruebas = [
        test_default_pide_N_dias_sueltos_terminando_ayer,
        test_dias_7_sigue_siendo_un_solo_archivo,
        test_fecha_puntual_no_activa_la_ventana_de_liquidacion,
    ]
    fallas = 0
    for prueba in pruebas:
        with tempfile.TemporaryDirectory() as tmp:
            fallas += prueba(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
