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


# ── T8-2 (23-sep-2026): todo objeto declarado que existe en Meta tiene que estar PAUSED ────

def _filas_declaradas():
    return [("CAMPANA", "GTR7_PX_F1", "OK", "c1"),
            ("CONJUNTO", "GTR7_PX_F1_ANG1", "OK", "s1"),
            ("ANUNCIO", "GTR7_PX_F1_ANG1_A1", "OK", "a1")]


def test_todo_paused_pasa_el_gate():
    filas = _filas_declaradas()
    meta = {"GTR7_PX_F1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1_A1": {"status": "PAUSED"}}
    no_pausados = vp.objetos_no_pausados(filas, meta)
    ok = no_pausados == []
    print(("  OK     " if ok else "  FALLA  ")
          + "los 3 objetos PAUSED en Meta: el gate no reporta ninguno"
          + ("" if ok else f"\n         no_pausados={no_pausados}"))
    return 0 if ok else 1


def test_un_anuncio_active_bloquea():
    filas = _filas_declaradas()
    meta = {"GTR7_PX_F1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1_A1": {"status": "ACTIVE"}}
    no_pausados = vp.objetos_no_pausados(filas, meta)
    ok = (len(no_pausados) == 1 and no_pausados[0][0] == "ANUNCIO"
          and no_pausados[0][1] == "GTR7_PX_F1_ANG1_A1" and no_pausados[0][3] == "ACTIVE")
    print(("  OK     " if ok else "  FALLA  ")
          + "un anuncio ACTIVE se reporta solo (no los otros dos que si estan PAUSED)"
          + ("" if ok else f"\n         no_pausados={no_pausados}"))
    return 0 if ok else 1


def test_sin_effective_status_no_pasa():
    """Un objeto sin `status`/`effective_status` en el snapshot NUNCA se asume PAUSED —
    fallar en silencio seria peor que no verificar nada."""
    filas = _filas_declaradas()
    meta = {"GTR7_PX_F1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1": {"status": "PAUSED"},
            "GTR7_PX_F1_ANG1_A1": {}}
    no_pausados = vp.objetos_no_pausados(filas, meta)
    ok = (len(no_pausados) == 1 and no_pausados[0][1] == "GTR7_PX_F1_ANG1_A1"
          and no_pausados[0][3] == "SIN effective_status")
    print(("  OK     " if ok else "  FALLA  ")
          + "sin effective_status en el snapshot: se reporta, NUNCA se asume PAUSED"
          + ("" if ok else f"\n         no_pausados={no_pausados}"))
    return 0 if ok else 1


def test_objetos_faltantes_no_entran_al_chequeo_de_paused():
    """Un objeto que ni siquiera existe en Meta (estado FALTA en `filas`) ya lo bloquea el gate
    de existencia — no tiene sentido, ademas, reportarlo como 'no pausado'."""
    filas = [("ANUNCIO", "GTR7_PX_F1_ANG1_A9", "FALTA", "")]
    no_pausados = vp.objetos_no_pausados(filas, {})
    ok = no_pausados == []
    print(("  OK     " if ok else "  FALLA  ")
          + "un objeto FALTA no se reporta tambien como 'no pausado' (el gate de existencia ya lo cubre)"
          + ("" if ok else f"\n         no_pausados={no_pausados}"))
    return 0 if ok else 1


def test_no_declarados_usa_el_prefijo_de_la_campana():
    """Los no declarados salen del prefijo cuenta_token_ de la campaña, no del producto_key."""
    campana = "EXTERNA_OVULOSPURITY_TEST_20260930"
    declarados = {"EXTERNA_OVULOSPURITY_TEST_20260930"}
    meta = {"EXTERNA_OVULOSPURITY_TEST_20260930": {"id": "1"},
            "EXTERNA_OVULOSPURITY_TEST_20260929": {"id": "2"},
            "EXTERNA_OTRO_TEST_20260930": {"id": "3"},
            "GTR7_OVULOSPURITY_TEST_20260930": {"id": "4"}}
    hallados = vp.no_declarados(meta, declarados, campana)
    ok = hallados == ["EXTERNA_OVULOSPURITY_TEST_20260929"]
    print(("  OK     " if ok else "  FALLA  ")
          + "solo la no declarada con el prefijo y el token de fase de la campaña"
          + ("" if ok else f"\n         hallados={hallados}"))
    return 0 if ok else 1


def test_copia_sin_renombrar_se_detecta_solo_en_la_campana():
    meta = {
        "C2-X A ~ P|A|C2.CN05|NC3A|1U|BOT_V3": {"id": "1", "campaign_id": "C"},
        "C2-X A ~ P|A|C2.CN05|NC3A|1U|BOT_V3 - Copia": {"id": "2", "campaign_id": "C"},
        "OTRO ~ Q - Copia 2": {"id": "3", "campaign_id": "OTRA"},
    }
    hits = vp.copias_sin_renombrar(meta, "C")
    ok = hits == [("C2-X A ~ P|A|C2.CN05|NC3A|1U|BOT_V3 - Copia", "2")]
    print(("  OK     " if ok else "  FALLA  ")
          + "un anuncio '- Copia' de la campana declarada bloquea; el de otra campana no"
          + ("" if ok else f"\n         hits={hits!r}"))
    return 0 if ok else 1


def test_alta_conjuntos_hereda_de_la_fila_del_mismo_angulo():
    dim = [{"producto_key": "P", "angulo_key": "ANG", "conjunto_meta": "G13_R1", "avatar": "av",
            "fase": "FASE2_ESCALA", "estado": "ACTIVO"}]
    man = {"campana": "G7_P_CONCEPTOS-C", "conjuntos": [{"nombre": "G7_P_ANG_C1"}, {"nombre": "G13_R1"}]}
    pq = {"producto_key": "P", "angulo": "ANG", "cuenta_alias": "GTR7", "fase": 2}
    altas = vp.filas_alta_conjuntos(man, pq, dim, True, "2026-10-17")
    ok = (len(altas) == 1 and altas[0]["conjunto_meta"] == "G7_P_ANG_C1"
          and altas[0]["avatar"] == "av" and altas[0]["fase"] == "FASE2"
          and altas[0]["campana_clave"] == "G7_P_CONCEPTOS-C" and altas[0]["estado"] == "ACTIVO")
    print(("  OK     " if ok else "  FALLA  ")
          + "el alta solo crea los conjuntos que faltan, heredando atributos del mismo producto y angulo"
          + ("" if ok else f"\n         altas={altas!r}"))
    return 0 if ok else 1


def test_alta_conjuntos_sin_plantilla_no_inventa():
    man = {"campana": "C", "conjuntos": [{"nombre": "NUEVO"}]}
    pq = {"producto_key": "P", "angulo": "ANG", "cuenta_alias": "GTR7", "fase": 2}
    altas = vp.filas_alta_conjuntos(man, pq, [], False, "2026-10-17")
    ok = altas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "sin fila del mismo producto y angulo no se inventan atributos"
          + ("" if ok else f"\n         altas={altas!r}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_no_declarados_usa_el_prefijo_de_la_campana()
    fallas += test_generado_con_ad_id_pasa_a_publicado()
    fallas += test_pendiente_generar_tambien_asciende_a_publicado()
    fallas += test_retirado_no_se_degrada()
    fallas += test_ya_publicado_no_se_recuenta_como_ascenso()
    fallas += test_estado_entrega_no_se_toca()
    fallas += test_fila_sin_ad_id_declarado_no_cambia()
    fallas += test_todo_paused_pasa_el_gate()
    fallas += test_un_anuncio_active_bloquea()
    fallas += test_sin_effective_status_no_pasa()
    fallas += test_objetos_faltantes_no_entran_al_chequeo_de_paused()
    fallas += test_copia_sin_renombrar_se_detecta_solo_en_la_campana()
    fallas += test_alta_conjuntos_hereda_de_la_fila_del_mismo_angulo()
    fallas += test_alta_conjuntos_sin_plantilla_no_inventa()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
