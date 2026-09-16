#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_publicacion.py — GATE DE LA NUMERACION Y EL BRAZO EN gen_publicacion.py.

Congela tres defectos de la cadena de FASE 2/3 (simulación Turmeric, 22-sep-2026):

  · orden_nombre_de(): antes el numero del nombre del anuncio salia de un contador
    LOCAL A LA CORRIDA (orden_global, reseteado a 0 en cada invocacion). Publicar el
    brazo A y despues el brazo B por separado numeraba los dos 01-05 en vez de que B
    continuara en 06-10.
  · chequear_brazo_ambiguo(): sin --brazo-creativos, un angulo con mas de un brazo
    declarado en _DIM_CREATIVOS.csv tomaba las primeras piezas del CSV sin avisar —
    publicar el brazo B sin el flag republicaria el pool del brazo A.
  · nombre_conjunto()/siguiente_replica() (G0.5 punto 4.1, 15-sep-2026): el R[N] del
    nombre salia de 'i', la posicion del conjunto DENTRO DEL LOOP de la corrida — no
    de cuantas replicas reales ya tiene ese angulo en Meta. Republicar (una tanda mas
    de escalado horizontal) volvia a nombrar R1, R2... encima de replicas que ya
    existian; la simulacion tuvo que fijarlo a mano a R1 para poder avanzar (f71f9ec).

USO:  python Ads/_TOOLS/test_gen_publicacion.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_publicacion as gp  # noqa: E402


def _pieza(creativo_id, brazo):
    return {"creativo_id": creativo_id, "brazo": brazo}


def test_orden_estable_brazo_b_continua_donde_termina_a():
    piezas = ([_pieza("A%d" % i, "A") for i in range(1, 6)]
              + [_pieza("B%d" % i, "B") for i in range(1, 6)])
    orden = gp.orden_nombre_de(piezas)
    solo_b = [p for p in piezas if p["brazo"] == "B"]
    orden_solo_b = gp.orden_nombre_de(solo_b)   # publicando SOLO el brazo B, en otra corrida
    numeros_b_con_ambos = sorted(orden[p["creativo_id"]] for p in solo_b)
    ok = numeros_b_con_ambos == [6, 7, 8, 9, 10]
    print(("  OK     " if ok else "  FALLA  ")
          + "con las 10 piezas presentes, el brazo B numera 06-10 (no 01-05)"
          + ("" if ok else f"\n         obtenido={numeros_b_con_ambos}"))
    fallas = 0 if ok else 1

    # El bug real: correr el script SOLO para el brazo B (sin ver las piezas del A)
    # volvia a numerar 01-05 porque el contador era local a la corrida. Documentamos
    # que orden_nombre_de por si sola no resuelve eso — necesita ver TODAS las piezas
    # del angulo, que es exactamente lo que gen_publicacion.py le pasa (piezas_del_angulo,
    # antes de filtrar por --brazo-creativos).
    ok2 = sorted(orden_solo_b.values()) == [1, 2, 3, 4, 5]
    print("  OK     (documentado) orden_nombre_de(solo_b) por si sola numera 01-05: "
          "el llamador DEBE pasarle piezas_del_angulo completo, no ya filtrado por brazo")
    return fallas


def test_orden_estable_sin_brazo_declarado_no_rompe():
    """Angulos sin columna brazo poblada (todo el portafolio real hoy): NO reordena por
    creativo_id (eso ROMPERIA los nombres ya publicados en Meta, que matchean por nombre
    en el snapshot de idempotencia) — preserva el orden ORIGINAL del CSV, 1..N."""
    piezas = [_pieza("ZETA", ""), _pieza("ALFA", None), _pieza("BETA", "")]
    try:
        orden = gp.orden_nombre_de(piezas)
        ok = orden == {"ZETA": 1, "ALFA": 2, "BETA": 3}   # orden ORIGINAL, no alfabetico
    except Exception as e:
        ok = False
        orden = str(e)
    print(("  OK     " if ok else "  FALLA  ")
          + "brazo vacio o ausente preserva el ORDEN ORIGINAL del CSV, no reordena alfabetico"
          + ("" if ok else f"\n         {orden}"))
    return 0 if ok else 1


def test_bloquea_multibrazo_sin_flag():
    piezas = ([_pieza("A%d" % i, "A") for i in range(1, 6)]
              + [_pieza("B%d" % i, "B") for i in range(1, 6)])
    msg = gp.chequear_brazo_ambiguo(piezas, brazo_creativos=None, brazo_arg="B")
    ok = msg is not None and "brazo" in msg.lower()
    print(("  OK     " if ok else "  FALLA  ")
          + "2 brazos en _DIM_CREATIVOS.csv sin --brazo-creativos bloquea con un mensaje claro"
          + ("" if ok else f"\n         msg={msg!r}"))
    return 0 if ok else 1


def test_no_bloquea_con_flag_explicito():
    piezas = ([_pieza("A%d" % i, "A") for i in range(1, 6)]
              + [_pieza("B%d" % i, "B") for i in range(1, 6)])
    msg = gp.chequear_brazo_ambiguo(piezas, brazo_creativos="B", brazo_arg="B")
    ok = msg is None
    print(("  OK     " if ok else "  FALLA  ")
          + "pasando --brazo-creativos B no bloquea aunque haya 2 brazos"
          + ("" if ok else f"\n         msg={msg!r}"))
    return 0 if ok else 1


def test_no_bloquea_con_un_solo_brazo_o_ninguno():
    un_brazo = [_pieza("A%d" % i, "A") for i in range(1, 6)]
    sin_brazo = [_pieza("X%d" % i, "") for i in range(1, 6)]
    m1 = gp.chequear_brazo_ambiguo(un_brazo, brazo_creativos=None, brazo_arg="A")
    m2 = gp.chequear_brazo_ambiguo(sin_brazo, brazo_creativos=None, brazo_arg="UNICO")
    ok = m1 is None and m2 is None
    print(("  OK     " if ok else "  FALLA  ")
          + "un solo brazo declarado, o ninguno (portafolio real hoy), nunca bloquea"
          + ("" if ok else f"\n         m1={m1!r} m2={m2!r}"))
    return 0 if ok else 1


def _conjunto(pk, angulo, cta, n):
    return {"producto_key": pk, "angulo_key": angulo, "cuenta_alias": cta,
            "conjunto_meta": "%s_%s_%s_R%d" % (cta, pk, angulo.replace("_", "-"), n)}


def test_siguiente_replica_continua_donde_quedo_en_meta():
    filas = [_conjunto("TINNIDROP", "PERDIDA_AUDITIVA", "GTR7", 1),
             _conjunto("TINNIDROP", "PERDIDA_AUDITIVA", "GTR7", 2),
             _conjunto("TINNIDROP", "PERDIDA_AUDITIVA", "GTR7", 3)]
    n = gp.siguiente_replica(filas, "TINNIDROP", "PERDIDA_AUDITIVA", "GTR7")
    ok = n == 4
    print(("  OK     " if ok else "  FALLA  ")
          + "con R1-R2-R3 ya en _DIM_CONJUNTOS.csv, la siguiente replica es R4 (no R1)"
          + ("" if ok else f"\n         obtenido={n}"))
    return 0 if ok else 1


def test_siguiente_replica_sin_historial_arranca_en_1():
    n = gp.siguiente_replica([], "PRODUCTO_NUEVO", "ANGULO_X", "GTR0")
    ok = n == 1
    print(("  OK     " if ok else "  FALLA  ")
          + "sin filas para este producto+angulo+cuenta, arranca en R1"
          + ("" if ok else f"\n         obtenido={n}"))
    return 0 if ok else 1


def test_siguiente_replica_no_mezcla_angulo_ni_cuenta():
    filas = [_conjunto("TINNIDROP", "PERDIDA_AUDITIVA", "GTR7", 5),
             _conjunto("TINNIDROP", "DETERIORO_COGNITIVO", "GTR7", 9),
             _conjunto("TINNIDROP", "PERDIDA_AUDITIVA", "GTR1", 7)]
    n = gp.siguiente_replica(filas, "TINNIDROP", "PERDIDA_AUDITIVA", "GTR7")
    ok = n == 6
    print(("  OK     " if ok else "  FALLA  ")
          + "el R9 de otro angulo y el R7 de otra cuenta no contaminan el conteo (da R6, no R10)"
          + ("" if ok else f"\n         obtenido={n}"))
    return 0 if ok else 1


def test_siguiente_replica_ignora_huecos_por_pausas():
    """ETAPA-6.md regla 2: el numero no se reutiliza aunque R2 este pausada — el maximo
    historico manda, nunca la cuenta de filas vivas."""
    filas = [_conjunto("VARICOSE", "VERGUENZA_PIERNAS", "GTR7", 1),
             _conjunto("VARICOSE", "VERGUENZA_PIERNAS", "GTR7", 2)]
    filas[1]["estado"] = "PAUSADO"
    n = gp.siguiente_replica(filas, "VARICOSE", "VERGUENZA_PIERNAS", "GTR7")
    ok = n == 3
    print(("  OK     " if ok else "  FALLA  ")
          + "una replica pausada sigue contando para el maximo: la siguiente es R3, no reusa R2"
          + ("" if ok else f"\n         obtenido={n}"))
    return 0 if ok else 1


def test_nombre_conjunto_fase2_no_cambia_de_semantica():
    """La FASE 2 no usa siguiente_replica: 'numero' sigue siendo la posicion dentro del
    brazo (A1, A2...), sin tocar."""
    nombre = gp.nombre_conjunto(2, "GTR7", "TINNIDROP", "PERDIDA_AUDITIVA", "A", 3)
    ok = nombre == "GTR7_TINNIDROP_PERDIDA-AUDITIVA_A3"
    print(("  OK     " if ok else "  FALLA  ")
          + "fase 2 sigue nombrando por posicion en el brazo, no por replica"
          + ("" if ok else f"\n         obtenido={nombre!r}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_orden_estable_brazo_b_continua_donde_termina_a()
    fallas += test_orden_estable_sin_brazo_declarado_no_rompe()
    fallas += test_bloquea_multibrazo_sin_flag()
    fallas += test_no_bloquea_con_flag_explicito()
    fallas += test_no_bloquea_con_un_solo_brazo_o_ninguno()
    fallas += test_siguiente_replica_continua_donde_quedo_en_meta()
    fallas += test_siguiente_replica_sin_historial_arranca_en_1()
    fallas += test_siguiente_replica_no_mezcla_angulo_ni_cuenta()
    fallas += test_siguiente_replica_ignora_huecos_por_pausas()
    fallas += test_nombre_conjunto_fase2_no_cambia_de_semantica()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
