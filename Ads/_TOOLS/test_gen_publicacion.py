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
  · verificar_firma() (defecto residual de la simulacion, 16-sep-2026): un anuncio salia a
    Meta con ejes de su firma en '?' y el publicador no lo miraba. En FASE 2/3 pasaba en el
    100 % de los anuncios. TINNIDROP FASE 2 tenia 0 bloqueantes con TINNIDROP|...|C2.CN04|?|?|?

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


# ── verificar_firma() — ningun anuncio sale a Meta con un eje de su firma perdido ──────────
# El 16-sep-2026 TINNIDROP FASE 2 tenia 0 bloqueantes y estaba lista para publicar 5 anuncios
# con la firma  TINNIDROP|ACCESIBILIDAD_ME|C2.CN04|?|?|?  . La firma viaja en el nombre del
# anuncio: una vez en Meta, esos tres ejes no se recuperan.

VOCAB_HOY = {"nivel_conciencia": (False, "ETAPA-2.md"), "oferta_key": (False, "ETAPA-1.md"),
             "destino_key": (True, "ETAPA-11.md")}


def _pieza_firma(**faltan):
    p = {"creativo_id": "TINNIDROP_F2_CN04", "producto_key": "TINNIDROP",
         "angulo_key": "ACCESIBILIDAD_MEDICO", "concepto_key": "C2_BENEFICIOS",
         "canonico_id": "CN04", "nivel_conciencia": "2", "oferta_key": "ESCALERA",
         "destino_key": "PARAGUAS_V2"}
    for eje in faltan:
        p[eje] = None
    return p


def _correr_gate(piezas, vocab):
    previo = gp.vocabulario_de_ejes
    gp.vocabulario_de_ejes = lambda: vocab
    try:
        pq = gp.Paquete()
        gp.verificar_firma([{"piezas": piezas}], gp.cargar_firma(), pq)
    finally:
        gp.vocabulario_de_ejes = previo
    bloq = [b for b in pq.bloqueantes if "firma" in b["falta"]]
    avis = [a for a in pq.avisos if "firma" in a]
    return bloq, avis


def test_firma_completa_no_bloquea():
    bloq, avis = _correr_gate([_pieza_firma()], VOCAB_HOY)
    ok = not bloq and not avis
    print(("  OK     " if ok else "  FALLA  ")
          + "firma con los 5 ejes: ni bloquea ni avisa"
          + ("" if ok else f"\n         bloq={bloq} avis={avis}"))
    return 0 if ok else 1


def test_firma_fase2_sin_ejes_de_oferta_bloquea_con_su_dueno():
    """El caso real: las piezas de FASE 2 salen de _DIM_CREATIVOS.csv y el plan no trae los ejes."""
    bloq, _ = _correr_gate([_pieza_firma(nivel_conciencia=1, oferta_key=1, destino_key=1)] * 5, VOCAB_HOY)
    textos = " ".join(b["falta"] for b in bloq)
    duenos = " ".join(b["lo_produce"] for b in bloq)
    ok = (len(bloq) == 2 and "nivel_conciencia" in textos and "oferta_key" in textos
          and "ETAPA-2.md" in duenos and "ETAPA-1.md" in duenos and "5 anuncio" in textos)
    print(("  OK     " if ok else "  FALLA  ")
          + "firma '?|?|?' de FASE 2: bloquea nivel_conciencia y oferta_key, cada uno con su dueno"
          + ("" if ok else f"\n         bloq={bloq}"))
    return 0 if ok else 1


def test_firma_eje_abierto_avisa_y_no_bloquea():
    """destino_key esta declarado '(abierto)' en el vocabulario: exigirlo seria inventar la regla."""
    bloq, avis = _correr_gate([_pieza_firma(destino_key=1)], VOCAB_HOY)
    ok = not bloq and len(avis) == 1 and "destino_key" in avis[0] and "ABIERTO" in avis[0]
    print(("  OK     " if ok else "  FALLA  ")
          + "destino_key vacio con vocabulario ABIERTO: avisa, no bloquea"
          + ("" if ok else f"\n         bloq={bloq} avis={avis}"))
    return 0 if ok else 1


def test_firma_eje_se_exige_cuando_su_dueno_cierra_el_vocabulario():
    """La regla sale del vocabulario, no del codigo: cuando ETAPA-11 cierre destino_key, bloquea solo."""
    vocab_cerrado = dict(VOCAB_HOY, destino_key=(False, "ETAPA-11.md"))
    bloq, avis = _correr_gate([_pieza_firma(destino_key=1)], vocab_cerrado)
    ok = len(bloq) == 1 and "destino_key" in bloq[0]["falta"] and "ETAPA-11.md" in bloq[0]["lo_produce"]
    print(("  OK     " if ok else "  FALLA  ")
          + "el mismo destino_key vacio BLOQUEA en cuanto el vocabulario deja de estar abierto"
          + ("" if ok else f"\n         bloq={bloq} avis={avis}"))
    return 0 if ok else 1


# ── ambito de los bloqueantes y --solo-paquete — el paquete que se daba por cumplido sin poder
#    lanzarse (defecto residual de la simulacion, 16-sep-2026). F1.paquete miraba 5 artefactos y
#    no la pagina, la banda, las piezas en disco, el copy ni la firma: decia OK, y el bloqueo
#    aparecia recien en F1.publicar, cargando publicar-meta para algo que se arregla en una etapa.

MSG_DE_PUBLICACION = ("cuenta", "metodo de pago", "factura en", "minimo de la cuenta", "lanzamiento")


def _bloqueos_declarados():
    """[(metodo, texto del mensaje)] de cada llamada pq.bloquear_* en gen_publicacion.py, por AST."""
    import ast
    with open(gp.__file__, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read())
    out = []
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr.startswith("bloquear") and nodo.args):
            partes = [n.value for n in ast.walk(nodo.args[0])
                      if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            nombres = [n.id for n in ast.walk(nodo.args[0]) if isinstance(n, ast.Name)]
            out.append((nodo.func.attr, " ".join(partes) + " " + " ".join(nombres)))
    return out


def test_no_hay_bloquear_generico():
    ok = not hasattr(gp.Paquete(), "bloquear")
    print(("  OK     " if ok else "  FALLA  ")
          + "Paquete no tiene bloquear() generico: un bloqueo nuevo sin ambito rompe, no cae del lado equivocado")
    return 0 if ok else 1


def test_del_ambito_separa():
    pq = gp.Paquete()
    pq.bloquear_paquete("sin copy", "etapa-4")
    pq.bloquear_publicacion("sin metodo de pago", "el operador")
    ok = ([b["falta"] for b in pq.del_ambito("paquete")] == ["sin copy"]
          and [b["falta"] for b in pq.del_ambito("publicacion")] == ["sin metodo de pago"]
          and len(pq.bloqueantes) == 2)
    print(("  OK     " if ok else "  FALLA  ")
          + "cada bloqueante queda etiquetado y del_ambito() los separa")
    return 0 if ok else 1


def test_clasificacion_de_los_bloqueos_no_se_invierte():
    """Cuenta, pago, moneda, minimo, brazo y fecha son de la PUBLICACION; todo lo demas, del PAQUETE.
    Invertirlo manda a rehacer una fase por una cuenta, o a publicar un paquete incompleto."""
    decl = _bloqueos_declarados()
    malos = []
    for metodo, texto in decl:
        es_pub = any(k in texto for k in MSG_DE_PUBLICACION) or "error_brazo" in texto
        if metodo == "bloquear_publicacion" and not es_pub:
            malos.append("publicacion pero parece del paquete: " + texto[:60])
        if metodo == "bloquear_paquete" and es_pub:
            malos.append("paquete pero parece de la publicacion: " + texto[:60])
    pub = sum(1 for m, _ in decl if m == "bloquear_publicacion")
    paq = sum(1 for m, _ in decl if m == "bloquear_paquete")
    ok = not malos and pub >= 6 and paq >= 10
    print(("  OK     " if ok else "  FALLA  ")
          + "clasificacion: %d bloqueo(s) de publicacion y %d de paquete, cada uno de su lado" % (pub, paq)
          + ("" if ok else "\n         " + "\n         ".join(malos)))
    return 0 if ok else 1


def _fixture_producto_sin_cuenta():
    """Un producto recien creado, como los 4 de FASE 1 del portafolio: cuenta PENDIENTE, sin plan."""
    import csv, io, shutil, tempfile
    tmp = tempfile.mkdtemp(prefix="genpub_paq_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    for nombre in ("_PARAMETROS_PUBLICACION.csv", "_DIM_CUENTAS.csv", "_DIM_VOCABULARIO.csv"):
        shutil.copy(gp.P(nombre), os.path.join(prod, nombre))     # los CSV de sistema, reales
    with io.open(gp.P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig", newline="") as fh:
        cols = csv.DictReader(fh).fieldnames
    with io.open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerow(dict(dict.fromkeys(cols, ""), producto_key="PX_NUEVO", cuenta_alias="PENDIENTE"))
    return tmp


def _correr_main(base, argv):
    import contextlib, io
    previo = (gp.BASE, gp.P, sys.argv)
    gp.BASE = base
    gp.P = lambda *a: os.path.join(base, "PRODUCTOS", *a)
    sys.argv = ["gen_publicacion.py"] + argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = gp.main()
        return code, buf.getvalue(), None
    except Exception as e:                      # noqa: BLE001 — el test reporta el crash, no lo esconde
        return None, buf.getvalue(), e
    finally:
        gp.BASE, gp.P, sys.argv = previo


def test_solo_paquete_juzga_un_producto_sin_cuenta():
    base = _fixture_producto_sin_cuenta()
    code, out, err = _correr_main(base, ["--producto", "PX_NUEVO", "--fase", "1", "--solo-paquete"])
    ok = (err is None and code == 1 and "NO LANZABLE" in out and "no existe _PLAN" in out
          and "no cuentan para el paquete" in out
          and not os.path.exists(os.path.join(base, "PRODUCTOS", "_PUBLICACION_F1.json")))
    print(("  OK     " if ok else "  FALLA  ")
          + "--solo-paquete con cuenta PENDIENTE: no corta ni revienta, juzga el paquete y no escribe el canonico"
          + ("" if ok else f"\n         code={code} err={err!r}\n         out={out[:300]!r}"))
    return 0 if ok else 1


def test_modo_normal_sigue_cortando_sin_cuenta():
    """Para PUBLICAR, una cuenta inexistente sigue siendo un corte inmediato: eso no cambio."""
    base = _fixture_producto_sin_cuenta()
    code, out, err = _correr_main(base, ["--producto", "PX_NUEVO", "--fase", "1"])
    ok = err is None and code == 1 and "no existe en _DIM_CUENTAS.csv" in out
    print(("  OK     " if ok else "  FALLA  ")
          + "sin --solo-paquete, la cuenta inexistente sigue cortando la publicacion"
          + ("" if ok else f"\n         code={code} err={err!r}\n         out={out[:200]!r}"))
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
    fallas += test_firma_completa_no_bloquea()
    fallas += test_firma_fase2_sin_ejes_de_oferta_bloquea_con_su_dueno()
    fallas += test_firma_eje_abierto_avisa_y_no_bloquea()
    fallas += test_firma_eje_se_exige_cuando_su_dueno_cierra_el_vocabulario()
    fallas += test_no_hay_bloquear_generico()
    fallas += test_del_ambito_separa()
    fallas += test_clasificacion_de_los_bloqueos_no_se_invierte()
    fallas += test_solo_paquete_juzga_un_producto_sin_cuenta()
    fallas += test_modo_normal_sigue_cortando_sin_cuenta()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
