#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verificar_publicacion.py — GATE DEL CICLO DE ESTADO EN verificar_publicacion.py
(G0.5 punto 4.3, 15-sep-2026).

Antes de este arreglo, aplicar_ad_ids() (entonces inline en main()) escribia el `ad_id` en
_DIM_CREATIVOS.csv pero no tocaba `estado`: la fila se quedaba en GENERADO aunque ya
tuviera un ad_id vivo en Meta. ETAPA-9.md declara el ciclo obligatorio "sin saltos"
PENDIENTE_GENERAR -> GENERADO -> PUBLICADO -> RETIRADO y dice que "PUBLICADO exige ad_id
real: es el unico estado que cuenta como inventario vivo" — pero nadie escribia esa
transicion.

USO:  python Ads/_TOOLS/test_verificar_publicacion.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_publicacion as vp  # noqa: E402


def _fila(creativo_id, estado, ad_id=""):
    return {"creativo_id": creativo_id, "estado": estado, "ad_id": ad_id, "notas": ""}


def test_generado_con_ad_id_pasa_a_publicado():
    rows = [_fila("C1", "GENERADO")]
    ids = {"C1": {"A": "ad_111", "B": "ad_112"}}
    rows, escritas, ascendidas, conflictos = vp.aplicar_ad_ids(rows, ids, "PROD/_PUBLICACION_F2A.json")
    ok = (rows[0]["estado"] == "PUBLICADO" and rows[0]["ad_id"] == "ad_111;ad_112"
          and escritas == 1 and ascendidas == 1 and not conflictos)
    print(("  OK     " if ok else "  FALLA  ")
          + "GENERADO + ad_id real -> PUBLICADO (ciclo de vida ETAPA-9.md), no se queda en GENERADO"
          + ("" if ok else f"\n         estado={rows[0]['estado']!r} escritas={escritas} ascendidas={ascendidas}"))
    return 0 if ok else 1


def test_pendiente_generar_tambien_asciende_a_publicado():
    """Caso raro pero posible (verificar_publicacion corre antes de que alguien haya
    marcado GENERADO a mano): igual sube a PUBLICADO porque lo que manda es el ad_id real,
    no el estado previo — salvo RETIRADO."""
    rows = [_fila("C2", "PENDIENTE_GENERAR")]
    ids = {"C2": {"A": "ad_200"}}
    rows, escritas, ascendidas, conflictos = vp.aplicar_ad_ids(rows, ids, "PROD/_PUBLICACION_F1.json")
    ok = rows[0]["estado"] == "PUBLICADO"
    print(("  OK     " if ok else "  FALLA  ")
          + "un ad_id real siempre sube a PUBLICADO, sin importar el estado previo (salvo RETIRADO)"
          + ("" if ok else f"\n         estado={rows[0]['estado']!r}"))
    return 0 if ok else 1


def test_retirado_no_se_degrada():
    """Invariante del ciclo 'sin saltos': RETIRADO es terminal. Volver a correr el gate
    sobre un snapshot viejo no puede resucitar un anuncio que el operador ya apago."""
    rows = [_fila("C3", "RETIRADO", ad_id="ad_viejo")]
    ids = {"C3": {"A": "ad_viejo"}}
    rows, escritas, ascendidas, conflictos = vp.aplicar_ad_ids(rows, ids, "PROD/_PUBLICACION_F2A.json")
    ok = rows[0]["estado"] == "RETIRADO" and ascendidas == 0
    print(("  OK     " if ok else "  FALLA  ")
          + "RETIRADO es terminal: no se degrada de vuelta a PUBLICADO"
          + ("" if ok else f"\n         estado={rows[0]['estado']!r} ascendidas={ascendidas}"))
    return 0 if ok else 1


def test_ya_publicado_no_se_recuenta_como_ascenso():
    rows = [_fila("C4", "PUBLICADO", ad_id="ad_400")]
    ids = {"C4": {"A": "ad_400"}}
    rows, escritas, ascendidas, conflictos = vp.aplicar_ad_ids(rows, ids, "PROD/_PUBLICACION_F2A.json")
    ok = rows[0]["estado"] == "PUBLICADO" and ascendidas == 0 and escritas == 1
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila ya PUBLICADA no se cuenta de nuevo como ascenso (solo las que cambian de estado)"
          + ("" if ok else f"\n         ascendidas={ascendidas}"))
    return 0 if ok else 1


def test_estado_entrega_no_se_toca():
    """estado_entrega es ENTREGADO/SIN_ENTREGA segun el gasto (DATA_PLAYBOOK.md) — un campo
    de OTRO dueno. Este gate no debe escribirlo nunca, ni siquiera dejarlo en blanco a
    mano: si la fila no lo trae, no aparece en el resultado."""
    fila = _fila("C5", "GENERADO")
    fila["estado_entrega"] = "ENTREGADO"
    rows = [fila]
    ids = {"C5": {"A": "ad_500"}}
    rows, *_ = vp.aplicar_ad_ids(rows, ids, "PROD/_PUBLICACION_F2A.json")
    ok = rows[0]["estado_entrega"] == "ENTREGADO"
    print(("  OK     " if ok else "  FALLA  ")
          + "estado_entrega no se toca — sigue siendo dueno de otro proceso"
          + ("" if ok else f"\n         estado_entrega={rows[0].get('estado_entrega')!r}"))
    return 0 if ok else 1


def test_fila_sin_ad_id_declarado_no_cambia():
    rows = [_fila("C6", "GENERADO")]
    rows, escritas, ascendidas, conflictos = vp.aplicar_ad_ids(rows, {}, "PROD/_PUBLICACION_F2A.json")
    ok = rows[0]["estado"] == "GENERADO" and escritas == 0 and ascendidas == 0
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila que no aparece en ids_por_creativo (nada declarado para ella) no se toca"
          + ("" if ok else f"\n         estado={rows[0]['estado']!r} escritas={escritas}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_generado_con_ad_id_pasa_a_publicado()
    fallas += test_pendiente_generar_tambien_asciende_a_publicado()
    fallas += test_retirado_no_se_degrada()
    fallas += test_ya_publicado_no_se_recuenta_como_ascenso()
    fallas += test_estado_entrega_no_se_toca()
    fallas += test_fila_sin_ad_id_declarado_no_cambia()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
