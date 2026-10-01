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
import datetime
import json
import os
import sys
import uuid

# P3 T4: registrar_evento.anexar() (que usa este archivo indirectamente vía registrar_excepcion())
# escribe siempre por Postgres. Aislamiento CRÍTICO, mismo patrón que test_db_write_path.py: fuerza
# vitalcom_test ANTES de importar nada que pueda conectar, para nunca tocar `vitalcom` real.
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_publicacion as gp  # noqa: E402

MANANA = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
import registrar_evento as re_  # noqa: E402 — mismo módulo que gp.registrar_evento (cache de sys.modules)
import test_flujo as tf  # noqa: E402 — reusa su fixture del gate de F2 (ángulo ganador)

sys.path.insert(0, os.path.join(re_.BASE, "db"))
import cargar as db_cargar      # noqa: E402
import nucleo as db_nucleo      # noqa: E402


def _preparar_base_de_pruebas():
    try:
        if db_cargar.asegurar_base_de_datos("vitalcom_test"):
            db_cargar.aplicar_schema(dbname="vitalcom_test")
    except Exception:
        pass


_preparar_base_de_pruebas()


def _conectar_seguro():
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_gen_publicacion.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
            "Abortado antes de tocar nada.")
    return con


def _db_disponible():
    try:
        con = _conectar_seguro()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _db_disponible()


def _bootstrap_evento(prod_dir, tenant):
    """Bootstrap mínimo de raw.evento/raw.raw_import para que verificar_csv_sincronizado() no
    aborte por 'nunca se importó' -- mismo patrón que test_db_write_path.py::_fixture()."""
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant, "evento", "_EVENTOS.csv", False, prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_EVENTOS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()


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

MSG_DE_PUBLICACION = ("cuenta", "metodo de pago", "factura en", "minimo de la cuenta", "lanzamiento",
                        "tasa sin declarar")


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
    if "mercado" not in cols:
        cols = cols + ["mercado"]
    with io.open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerow(dict(dict.fromkeys(cols, ""), producto_key="PX_NUEVO", cuenta_alias="PENDIENTE",
                       mercado="GT"))
    return tmp


def _correr_main(base, argv, tenant=None):
    import contextlib, io
    # registrar_evento es el MISMO módulo que gp.registrar_evento (cache de sys.modules): sus
    # rutas también hay que apuntarlas al fixture, o la EXCEPCION (P5) caería en el repo real.
    # P3 T4: registrar_evento.anexar() escribe por Postgres -- TENANT_ID/BKDIR también se
    # redirigen cuando el escenario va a escribir de verdad (tenant != None).
    previo = (gp.BASE, gp.P, re_.BASE, re_.PROD, re_.EVENTOS, re_.TENANT_ID, re_.BKDIR, sys.argv)
    gp.BASE = base
    gp.P = lambda *a: os.path.join(base, "PRODUCTOS", *a)
    re_.BASE = base
    re_.PROD = os.path.join(base, "PRODUCTOS")
    re_.EVENTOS = os.path.join(re_.PROD, "_EVENTOS.csv")
    if tenant:
        re_.TENANT_ID = tenant
        re_.BKDIR = os.path.join(base, "backups_csv")
    sys.argv = ["gen_publicacion.py"] + argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = gp.main()
        return code, buf.getvalue(), None
    except Exception as e:                      # noqa: BLE001 — el test reporta el crash, no lo esconde
        return None, buf.getvalue(), e
    finally:
        (gp.BASE, gp.P, re_.BASE, re_.PROD, re_.EVENTOS, re_.TENANT_ID, re_.BKDIR,
         sys.argv) = previo


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


# ---------------------------------------------------------------- P5: el gate de fase es candado
#
# F2 mide por ANGULO GANADOR (invariante 1). El fixture reproduce el caso de test_flujo.py
# (fixture_escalar_flaco): dos angulos con el MISMO CPA bajo break-even; `con_probado=True` le da
# a ANG_PROBADO el piso de volumen (min_ventas_ganador) y el gate se cumple; `con_probado=False`
# lo deja corto y el gate no se cumple. No se necesita un _PLAN.json completo para llegar hasta el
# gate: gen_publicacion ya escribe el paquete canonico aun con bloqueantes de plan/pagina/piezas
# (invariante 4 — se declaran, no cortan la corrida), asi que el fixture se queda minimo.

def _fixture_fase2_con_gate(gate_cumplido):
    """Reusa Ads/_TOOLS/test_flujo.py::fixture_escalar_flaco — el mismo caso (dos ángulos, mismo
    CPA bajo break-even, `con_probado` decide si ANG_PROBADO llega al piso de volumen) — y le
    agrega solo lo que gen_publicacion.py necesita para no cortar antes de llegar al gate: los
    CSV reales de cuenta/publicación, la carpeta PRODUCTOS/PX y un _EVENTOS.csv con header."""
    import csv, io, shutil
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=gate_cumplido)
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(os.path.join(prod, "PX"))
    for nombre in ("_PARAMETROS_PUBLICACION.csv", "_DIM_CUENTAS.csv", "_DIM_VOCABULARIO.csv"):
        shutil.copy(gp.P(nombre), os.path.join(prod, nombre))
    with io.open(os.path.join(prod, "_EVENTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow(["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta",
                                  "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"])
    return tmp


def _leer_eventos(base):
    import csv, io
    ruta = os.path.join(base, "PRODUCTOS", "_EVENTOS.csv")
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_gate_cumplido_escribe_el_paquete():
    base = _fixture_fase2_con_gate(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--fase", "2", "--cuenta", "GTR7"])
    escrito = os.path.exists(os.path.join(base, "PRODUCTOS", "PX", "_PUBLICACION_F2A.json"))
    eventos = _leer_eventos(base)
    ok = err is None and escrito and not eventos and "gate de entrada" not in out
    return _informe(ok, "gate de F2 cumplido: el paquete se escribe y no hay fila EXCEPCION",
                    (code, err, escrito, eventos, out[:200]))


def test_gate_incumplido_sin_excepcion_no_escribe_nada():
    base = _fixture_fase2_con_gate(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--fase", "2", "--cuenta", "GTR7"])
    escrito = os.path.exists(os.path.join(base, "PRODUCTOS", "PX", "_PUBLICACION_F2A.json"))
    eventos = _leer_eventos(base)
    ok = err is None and code == 1 and not escrito and not eventos and "gate de entrada a F2" in out
    return _informe(ok, "gate de F2 incumplido sin --excepcion: refusa, no escribe el paquete ni un evento",
                    (code, err, escrito, eventos, out[:300]))


def test_gate_incumplido_excepcion_vacia_refusa_igual():
    base = _fixture_fase2_con_gate(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--fase", "2", "--cuenta", "GTR7",
                                          "--excepcion", ""])
    escrito = os.path.exists(os.path.join(base, "PRODUCTOS", "PX", "_PUBLICACION_F2A.json"))
    ok = err is None and code == 1 and not escrito
    return _informe(ok, "--excepcion \"\" (vacío) se trata como ausente: refusa igual", (code, err, escrito))


def test_gate_incumplido_con_excepcion_procede_y_registra_una_excepcion():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base = _fixture_fase2_con_gate(gate_cumplido=False)
    tenant = "test_genpub_%s" % uuid.uuid4().hex[:8]
    _bootstrap_evento(os.path.join(base, "PRODUCTOS"), tenant)
    code, out, err = _correr_main(base, ["--producto", "PX", "--fase", "2", "--cuenta", "GTR7",
                                          "--excepcion", "el operador decide seguir sin el gate"],
                                   tenant=tenant)
    escrito = os.path.exists(os.path.join(base, "PRODUCTOS", "PX", "_PUBLICACION_F2A.json"))
    eventos = _leer_eventos(base)
    exc = [e for e in eventos if e["evento"] == "EXCEPCION"]
    ok = (err is None and escrito and len(eventos) == 1 and len(exc) == 1
          and exc[0]["valor_antes"] == "F2.entrada"
          and exc[0]["valor_despues"] == "gen_publicacion --fase 2"
          and exc[0]["motivo"] == "el operador decide seguir sin el gate"
          and exc[0]["fuente_decision"] == "Ads/_TOOLS/gen_publicacion.py")
    return _informe(ok, "gate incumplido + --excepcion: escribe el paquete y anexa EXACTAMENTE una EXCEPCION",
                    (code, err, escrito, eventos))


# ---------------------------------------------------------------- --media biblioteca (18-sep-2026)
#
# El operador sube las piezas a mano a la biblioteca de la cuenta y el paquete lee cada image_hash por
# nombre. Sin pantalla, LOCAL_FILE no sirve (spike F). Lo que estas pruebas congelan: ninguna subida
# sale en el paquete, ningun nombre viejo se reusa, el nombre no cambia despues de subir, y dos
# imagenes distintas con el mismo nombre bloquean.

def _fixture_fase1_completa(clave_campana="", mercado="GT", moneda="", tasa="", cuenta="GTR 7",
                           cuenta_extra=None):
    """Un producto de FASE 1 con todo en regla (plan de 6 angulos, pagina, cuenta y las 6 imagenes)."""
    import csv, io, shutil, tempfile
    tmp = tempfile.mkdtemp(prefix="genpub_bib_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(os.path.join(prod, "PX"))
    os.makedirs(os.path.join(tmp, "Ads", "MEDIA_PX"))
    for nombre in ("_PARAMETROS_PUBLICACION.csv", "_DIM_CUENTAS.csv", "_DIM_VOCABULARIO.csv"):
        shutil.copy(gp.P(nombre), os.path.join(prod, nombre))
    if cuenta_extra is not None:
        ruta_ctas = os.path.join(prod, "_DIM_CUENTAS.csv")
        with io.open(ruta_ctas, encoding="utf-8-sig", newline="") as fh:
            lector = csv.DictReader(fh)
            cols_ctas = lector.fieldnames
            filas_ctas = list(lector)
        filas_ctas.append({c: cuenta_extra.get(c, "") for c in cols_ctas})
        with io.open(ruta_ctas, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols_ctas)
            w.writeheader()
            w.writerows(filas_ctas)
    with io.open(gp.P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig", newline="") as fh:
        cols = csv.DictReader(fh).fieldnames
    if "mercado" not in cols:
        cols = cols + ["mercado"]
    with io.open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        fila = dict(dict.fromkeys(cols, ""), producto_key="PX", cuenta_alias=cuenta, page_id="111",
                    slug_carpeta="PX", carpeta_media="MEDIA_PX", clave_campana=clave_campana,
                    mercado=mercado, moneda=moneda, tasa=tasa)
        w.writerow({c: fila.get(c, "") for c in cols})
    conjuntos = []
    for i in range(1, 7):
        archivo = "PX_%d_ANG%d.png" % (i, i)
        with open(os.path.join(tmp, "Ads", "MEDIA_PX", archivo), "wb") as fh:
            fh.write(b"imagen %d" % i)
        conjuntos.append({"angulo_key": "ANG%d" % i, "avatar_edad": "35-55", "nivel_conciencia": "1",
                          "formato": "IMAGEN", "archivo_creativo": archivo, "copy": "Copy del angulo %d" % i})
    plan = {"producto_key": "PX", "fase": 1, "destino_key": "BOT_V1", "oferta": {"oferta_key": "ESCALERA"},
            "concepto_control": {"concepto_key": "C2_BENEFICIOS", "variante": "ligera", "canonico_id": "CN05"},
            "conjuntos": conjuntos}
    with io.open(os.path.join(prod, "PX", "_PLAN.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh)
    return tmp


def _listado(base, nombre, imagenes):
    ruta = os.path.join(base, nombre)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump({"tomado_el": "2026-09-18T10:00:00-06:00", "imagenes": imagenes}, fh)
    return ruta


def _paquete_biblioteca(base, antes=None, despues=None):
    salida = os.path.join(base, "paquete.json")
    argv = ["--producto", "PX", "--fase", "1", "--cuenta", "GTR7", "--lanzamiento", MANANA,
            "--media", "biblioteca", "--salida", salida]
    if antes:
        argv += ["--imagenes-antes", antes]
    if despues:
        argv += ["--imagenes-despues", despues]
    code, _out, err = _correr_main(base, argv)
    paquete = None
    if os.path.exists(salida):
        with open(salida, encoding="utf-8") as fh:
            paquete = json.load(fh)
    return code, paquete, err


def _creativos(paquete):
    return [l["args"]["image_hash"] for l in paquete["llamadas"] if l["tool"] == "ads_create_creative"]


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         " + str(detalle)[:400]))
    return 0 if ok else 1


def test_los_bloqueos_del_operador_llevan_su_clave():
    """cuenta · page_id · piezas llevan `clave` (y las piezas, la lista COMPLETA de archivos): quien los
    muestra ofrece el campo para cargar el dato sin interpretar la frase. Los demas no llevan clave."""
    import csv, io
    base = _fixture_fase1_completa()
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    with io.open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    filas[0].update(page_id="", cuenta_alias="GTR 99")
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    for i in (2, 5):
        os.remove(os.path.join(base, "Ads", "MEDIA_PX", "PX_%d_ANG%d.png" % (i, i)))
    salida = os.path.join(base, "paquete.json")
    code, _out, err = _correr_main(base, ["--producto", "PX", "--fase", "1", "--solo-paquete", "--json",
                                          "--salida", salida])
    with open(salida, encoding="utf-8") as fh:
        bloqueos = json.load(fh)["bloqueantes"]
    por_clave = {b["clave"]: b for b in bloqueos if "clave" in b}
    ok = (err is None and code == 1 and set(por_clave) == {"cuenta", "page_id", "piezas"}
          and por_clave["piezas"]["archivos"] == ["PX_2_ANG2.png", "PX_5_ANG5.png"]
          and por_clave["page_id"]["ambito"] == "paquete" and por_clave["cuenta"]["ambito"] == "publicacion")
    return _informe(ok, "los bloqueos que resuelve el operador llevan clave (cuenta, page_id, piezas con sus archivos)",
                    (code, err, bloqueos))


def test_biblioteca_sin_listado_espera_la_lectura_y_no_sube_nada():
    base = _fixture_fase1_completa()
    code, pq, err = _paquete_biblioteca(base)
    tools = [l["tool"] for l in pq["llamadas"]] if pq else []
    ok = (err is None and code == 1 and "ads_creative_upload_media" not in tools
          and [b["ambito"] for b in pq["bloqueantes"]] == ["media"]
          and set(_creativos(pq)) == {"{{FALTA_HASH}}"})
    return _informe(ok, "--media biblioteca sin volcado: ninguna subida en el paquete, un solo bloqueo de "
                        "ambito media (falta leer la biblioteca)", (code, err, pq and pq["bloqueantes"]))


def test_biblioteca_elige_un_nombre_que_no_existe():
    base = _fixture_fase1_completa()
    antes = _listado(base, "antes.json", [{"hash": "viejo2", "name": "PX_1_ANG1_V2.png"},
                                          {"hash": "otro", "name": "OTRO_PRODUCTO_V2"}])
    code, pq, err = _paquete_biblioteca(base, antes)
    nombres = [p["nombre_en_biblioteca"] for p in pq["media"]["piezas"]] if pq else []
    ok = (err is None and code == 1 and nombres[:1] == ["PX_1_ANG1_V3"]
          and nombres[1:] == ["PX_%d_ANG%d_V2" % (i, i) for i in range(2, 7)]
          and {p["estado"] for p in pq["media"]["piezas"]} == {"POR_SUBIR"}
          and len(pq["bloqueantes"]) == 1 and "falta subir 6" in pq["bloqueantes"][0]["falta"])
    return _informe(ok, "el nombre de cada pieza es el primer _V2, _V3... libre: PX_1_ANG1_V2 ya existia -> _V3",
                    (code, err, nombres))


def test_biblioteca_con_todo_subido_arma_el_paquete_sin_bloqueos():
    base = _fixture_fase1_completa()
    antes = _listado(base, "antes.json", [{"hash": "viejo2", "name": "PX_1_ANG1_V2.png"}])
    subidas = [{"hash": "h%d" % i, "name": "PX_%d_ANG%d_V%d.png" % (i, i, 3 if i == 1 else 2)} for i in range(1, 7)]
    despues = _listado(base, "despues.json", [{"hash": "viejo2", "name": "PX_1_ANG1_V2.png"}] + subidas)
    code, pq, err = _paquete_biblioteca(base, antes, despues)
    ok = (err is None and code == 0 and pq["bloqueantes"] == []
          and _creativos(pq) == ["h%d" % i for i in range(1, 7)]
          and "ads_creative_upload_media" not in [l["tool"] for l in pq["llamadas"]]
          and pq["media"]["piezas"][0]["nombre_en_biblioteca"] == "PX_1_ANG1_V3")
    return _informe(ok, "con todo subido: exit 0, cada creativo lleva SU hash literal y el nombre no se "
                        "corrio a _V4 por estar ya en la biblioteca", (code, err, pq and pq["bloqueantes"]))


def test_biblioteca_dos_imagenes_con_el_mismo_nombre_bloquean():
    base = _fixture_fase1_completa()
    antes = _listado(base, "antes.json", [])
    subidas = [{"hash": "h%d" % i, "name": "PX_%d_ANG%d_V2" % (i, i)} for i in range(1, 7)]
    subidas.append({"hash": "otra", "name": "PX_3_ANG3_V2.png"})
    despues = _listado(base, "despues.json", subidas)
    code, pq, err = _paquete_biblioteca(base, antes, despues)
    repetida = [b for b in (pq or {}).get("bloqueantes", []) if "PX_3_ANG3_V2" in b["falta"]]
    ok = (err is None and code == 1 and len(pq["bloqueantes"]) == 1 and repetida
          and repetida[0]["ambito"] == "media" and "{{FALTA_HASH}}" in _creativos(pq))
    return _informe(ok, "dos imagenes distintas con el mismo nombre: bloquea y no elige ninguna",
                    (code, err, pq and pq["bloqueantes"]))


def test_subida_local_sigue_igual_para_la_skill():
    base = _fixture_fase1_completa()
    salida = os.path.join(base, "p.json")
    code, _out, err = _correr_main(base, ["--producto", "PX", "--fase", "1", "--cuenta", "GTR7",
                                          "--lanzamiento", MANANA, "--salida", salida])
    with open(salida, encoding="utf-8") as fh:
        pq = json.load(fh)
    subidas = [l for l in pq["llamadas"] if l["tool"] == "ads_creative_upload_media"]
    ok = (err is None and code == 0 and len(subidas) == 6 and "media" not in pq
          and _creativos(pq)[0] == "{{image_hash_1}}")
    return _informe(ok, "sin --media, el paquete de la skill interactiva sigue con sus 6 subidas LOCAL_FILE",
                    (code, err, len(subidas), pq["bloqueantes"]))


def test_media_invalida_no_arranca():
    base = _fixture_fase1_completa()
    code, _out, err = _correr_main(base, ["--producto", "PX", "--fase", "1", "--media", "url"])
    return _informe(err is None and code == 2, "--media con un valor desconocido sale con 2", (code, err))


# ── T8-3 (23-sep-2026): invariante 7 exige EXACTAMENTE el dia siguiente ────────────────────

def test_fecha_hoy_bloquea():
    hoy = datetime.date(2026, 9, 23)
    ok = gp.fecha_lanzamiento_invalida(hoy, hoy) is True
    print(("  OK     " if ok else "  FALLA  ") + "lanzamiento el mismo dia de hoy bloquea")
    return 0 if ok else 1


def test_fecha_manana_no_bloquea():
    hoy = datetime.date(2026, 9, 23)
    ok = gp.fecha_lanzamiento_invalida(hoy + datetime.timedelta(days=1), hoy) is False
    print(("  OK     " if ok else "  FALLA  ") + "lanzamiento manana (exactamente el dia siguiente) no bloquea")
    return 0 if ok else 1


def test_fecha_pasado_manana_bloquea():
    """Antes de este arreglo, `fecha <= hoy` dejaba pasar cualquier fecha 2+ dias en el futuro
    sin avisar — invariante 7 exige el dia siguiente, no 'en algun momento futuro'."""
    hoy = datetime.date(2026, 9, 23)
    ok = gp.fecha_lanzamiento_invalida(hoy + datetime.timedelta(days=2), hoy) is True
    print(("  OK     " if ok else "  FALLA  ")
          + "lanzamiento pasado manana (2 dias en el futuro) bloquea, no solo el mismo dia o antes")
    return 0 if ok else 1


def test_fecha_ayer_bloquea():
    hoy = datetime.date(2026, 9, 23)
    ok = gp.fecha_lanzamiento_invalida(hoy - datetime.timedelta(days=1), hoy) is True
    print(("  OK     " if ok else "  FALLA  ") + "una fecha en el pasado sigue bloqueando")
    return 0 if ok else 1


# ---------------------------------------------------------------- P12/T12: F4.exploracion
#
# El mini-F1 de ángulos nuevos que corre en paralelo al escalado. Dos gates distintos:
#   1. el de ENTRADA a F4 (concepto 2/2 + CAMBIO_BOT posterior + cierre) — ya lo cubre el bloque de arriba.
#   2. el PROPIO de F4.exploracion (flujo.gate_nodo: F4 rentable según decidir.py) — nuevo aquí.
# Y una regla mecánica: el presupuesto/estructura salen de _PARAMETROS_PUBLICACION.csv
# (fase=4 brazo=EXPLORACION), nunca hardcodeados.

def _fixture_f3_exploracion_base(con_fila_parametros=True, presupuesto="2.99"):
    """Producto en F4 (2/2 + CAMBIO_BOT posterior + cierre, mismo caso que _fixture_fase2_con_gate pero
    para F4) con los CSV reales de cuenta/vocabulario y, salvo que se pida lo contrario, una fila
    fase=4 brazo=EXPLORACION en _PARAMETROS_PUBLICACION.csv (una copia, nunca el CSV real)."""
    import csv, io, shutil
    tmp = tf.fixture_conceptos_al_filo()
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(os.path.join(prod, "TURMERIC"))
    with io.open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "nombre_display", "estado", "fase"])
        w.writerow(["TURMERIC", "TURMERIC", "VIVO", "F4"])
    eventos_cols = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta",
                     "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"]
    with io.open(os.path.join(prod, "_EVENTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(eventos_cols)
        w.writerow(["2026-09-28", "TURMERIC", "GTR7", "*", "*", "CAMBIO_BOT", "", "",
                    "reescritura hacia C2.CN06 tras 2 de 2", "test"])
    # F4.entrada exige además cierre_post_cambio_bot (b: mensajes, c: cierre %) — se agrega
    # `ventana_ini` a las filas del fixture (vacía: no filtra nada, quedan bajo el piso de
    # replicación de concepto_2de2) y se SUMA una fila con ventana_ini POSTERIOR al CAMBIO_BOT,
    # nunca se sobrescribe la data del concepto ganador.
    with io.open(os.path.join(prod, "_FACT_VENTAS.csv"), encoding="utf-8-sig", newline="") as fh:
        filas_ventas = list(csv.reader(fh))
    header_ventas, filas_ventas = filas_ventas[0], filas_ventas[1:]
    header_ventas_ini = ["ventana_ini"] + header_ventas
    filas_ventas = [[""] + r for r in filas_ventas]
    filas_ventas.append(["2026-09-29", "2026-10-06", "BASE", "TURMERIC", "GTR7_TURMERIC_ANG_R1",
                          "GTR7_TURMERIC_F3-BOT_20261006", "ad", "5", "40", "80"])
    with io.open(os.path.join(prod, "_FACT_VENTAS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header_ventas_ini)
        w.writerows(filas_ventas)
    for nombre in ("_DIM_CUENTAS.csv", "_DIM_VOCABULARIO.csv"):
        shutil.copy(gp.P(nombre), os.path.join(prod, nombre))
    with io.open(gp.P("_PARAMETROS_PUBLICACION.csv"), encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        filas = [f for f in r if not (f["fase"] == "4" and f["brazo"] == "EXPLORACION")]
        cols = r.fieldnames
    with io.open(os.path.join(prod, "_PARAMETROS_PUBLICACION.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
        if con_fila_parametros:
            fila = dict(dict.fromkeys(cols, ""), fase="4", brazo="EXPLORACION", estructura="3-1-1",
                        conjuntos="3", anuncios_por_conjunto="1", daily_budget_usd=presupuesto,
                        presupuesto_nivel="ADSET", objetivo="OUTCOME_TRAFFIC",
                        optimization_goal="CONVERSATIONS", destination_type="WHATSAPP",
                        billing_event="IMPRESSIONS", buying_type="AUCTION", advantage_audience="0",
                        hora_lanzamiento="04:00", tz_offset="-06:00", estado="VIGENTE",
                        fuente_doctrina="test P12", notas="fixture de test")
            w.writerow(fila)
    plan = {"schema": "plan/1", "producto_key": "TURMERIC", "fase": "EXPLORACION",
            "conjuntos": [
                {"n": 1, "angulo_key": "ANG_NUEVO_UNO", "formato": "IMAGEN", "avatar_edad": None,
                 "archivo_creativo": "", "copy": "copy 1"},
                {"n": 2, "angulo_key": "ANG_NUEVO_DOS", "formato": "IMAGEN", "avatar_edad": None,
                 "archivo_creativo": "", "copy": "copy 2"},
                {"n": 3, "angulo_key": "ANG_NUEVO_TRES", "formato": "IMAGEN", "avatar_edad": None,
                 "archivo_creativo": "", "copy": "copy 3"},
            ]}
    with io.open(os.path.join(prod, "TURMERIC", "_PLAN_EXPLORACION.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh)
    return tmp


def test_exploracion_sin_fila_de_parametros_bloquea_nombrando_fase_y_brazo():
    base = _fixture_f3_exploracion_base(con_fila_parametros=False)
    code, out, err = _correr_main(base, ["--producto", "TURMERIC", "--fase", "4", "--brazo",
                                          "EXPLORACION", "--solo-paquete"])
    ok = (err is None and code == 1
          and "no hay fila VIGENTE en _PARAMETROS_PUBLICACION.csv para fase=4 brazo=EXPLORACION" in out)
    return _informe(ok, "sin fila fase=4 brazo=EXPLORACION en _PARAMETROS_PUBLICACION.csv: BLOQUEANTE nombrando fase y brazo",
                    (code, err, out[:300]))


def _correr_con_gate_propio_forzado(base, argv):
    """El gate propio de F4.exploracion (flujo.gate_nodo) se prueba aparte (ver los tests
    dedicados más abajo); acá se fuerza a True para poder mirar el PAQUETE que arma
    gen_publicacion.py sin repetir la construcción de un fixture de decidir.py completo."""
    original = gp.flujo.gate_nodo
    gp.flujo.gate_nodo = lambda pk, nid, env=None: (True, "test: F4 rentable")
    try:
        return _correr_main(base, argv)
    finally:
        gp.flujo.gate_nodo = original


def test_exploracion_presupuesto_sale_del_csv_no_hardcodeado():
    base299 = _fixture_f3_exploracion_base(presupuesto="2.99")
    code, out, err = _correr_con_gate_propio_forzado(
        base299, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION", "--cuenta", "GTR7", "--json"])
    paquete = json.loads(out) if err is None and out.strip() else {}
    ok299 = (err is None and paquete.get("daily_budget_usd_por_conjunto") == 2.99
             and paquete.get("presupuesto_nivel") == "ADSET" and "EXPLORA" in paquete.get("manifiesto", {}).get("campana", ""))

    base555 = _fixture_f3_exploracion_base(presupuesto="5.55")
    code2, out2, err2 = _correr_con_gate_propio_forzado(
        base555, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION", "--cuenta", "GTR7", "--json"])
    paquete2 = json.loads(out2) if err2 is None and out2.strip() else {}
    ok555 = err2 is None and paquete2.get("daily_budget_usd_por_conjunto") == 5.55

    ok = ok299 and ok555
    return _informe(ok, "el presupuesto de F4.exploracion sale de _PARAMETROS_PUBLICACION.csv "
                    "(2.99 y 5.55, no un valor fijo en el código) y la campaña nace EXPLORA",
                    (code, err, paquete.get("daily_budget_usd_por_conjunto"),
                     code2, err2, paquete2.get("daily_budget_usd_por_conjunto")))


def test_exploracion_arma_tres_conjuntos_con_angulos_distintos():
    base = _fixture_f3_exploracion_base()
    code, out, err = _correr_con_gate_propio_forzado(
        base, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION", "--cuenta", "GTR7", "--json"])
    paquete = json.loads(out) if err is None and out.strip() else {}
    conj = paquete.get("manifiesto", {}).get("conjuntos", [])
    angulos = {c.get("angulo") for c in conj}
    ok = (err is None and len(conj) == 3 and angulos == {"ANG_NUEVO_UNO", "ANG_NUEVO_DOS", "ANG_NUEVO_TRES"}
          and paquete.get("angulo", "").startswith("VARIOS"))
    return _informe(ok, "F4.exploracion arma UN CONJUNTO POR ÁNGULO (como FASE 1), no un ángulo fijo ×N",
                    (code, err, conj, paquete.get("angulo")))


def test_exploracion_gate_propio_incumplido_bloquea_sin_excepcion():
    """Este fixture no tiene ninguna celda ESCALAR para TURMERIC (decidir.py sin _DIM_CONJUNTOS.csv
    ni _PARAMETROS_DECISION.csv no corona nada): el gate propio de F4.exploracion está cerrado
    aunque el gate de ENTRADA a F3 (2/2 + CAMBIO_BOT) esté cumplido — son gates DISTINTOS."""
    base = _fixture_f3_exploracion_base()
    ok_natural, _ = gp.flujo.gate_nodo("TURMERIC", "F4.exploracion", gp.flujo.Entorno(base=base))
    code, out, err = _correr_main(base, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION",
                                          "--cuenta", "GTR7"])
    eventos = _leer_eventos(base)   # solo el CAMBIO_BOT que ya trae el fixture (F4.entrada) — cero EXCEPCION
    ok = (ok_natural is False and err is None and code == 1
          and "el gate de F4.exploracion no esta cumplido" in out
          and len(eventos) == 1 and all(e["evento"] != "EXCEPCION" for e in eventos))
    return _informe(ok, "gate propio de F4.exploracion incumplido (F4 no rentable) sin --excepcion: refusa, no escribe nada",
                    (ok_natural, code, err, out[:300], eventos))


def test_exploracion_gate_propio_con_excepcion_registra_F3_exploracion():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base = _fixture_f3_exploracion_base()
    tenant = "test_genpub_expl_%s" % uuid.uuid4().hex[:8]
    _bootstrap_evento(os.path.join(base, "PRODUCTOS"), tenant)
    code, out, err = _correr_main(base, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION",
                                          "--cuenta", "GTR7", "--excepcion", "el operador arranca antes"],
                                   tenant=tenant)
    eventos = _leer_eventos(base)
    exc = [e for e in eventos if e["evento"] == "EXCEPCION"]
    ok = (err is None and len(exc) == 1 and exc[0]["valor_antes"] == "F4.exploracion"
          and exc[0]["valor_despues"] == "gen_publicacion --fase 4 --brazo EXPLORACION")
    return _informe(ok, "gate propio de F4.exploracion incumplido + --excepcion: procede y registra "
                    "EXACTAMENTE una EXCEPCION contra 'F4.exploracion' (no 'F4.entrada')",
                    (code, err, eventos))


def test_exploracion_gate_propio_cumplido_no_pide_excepcion():
    """Cuando decidir.py SÍ ve el escalado rentable (gate_nodo True), F4.exploracion publica
    sin necesitar --excepcion — se verifica inyectando el resultado ya probado en
    test_flujo.py::gate_nodo, sin repetir la construcción de un fixture de decidir.py completo."""
    base = _fixture_f3_exploracion_base()
    code, out, err = _correr_con_gate_propio_forzado(
        base, ["--producto", "TURMERIC", "--fase", "4", "--brazo", "EXPLORACION", "--cuenta", "GTR7"])
    eventos = _leer_eventos(base)
    ok = (err is None and len(eventos) == 1 and all(e["evento"] != "EXCEPCION" for e in eventos)
          and "F4.exploracion" not in out)
    return _informe(ok, "gate propio de F4.exploracion cumplido: publica sin pedir --excepcion ni EXCEPCION",
                    (code, err, out[:200], eventos))


# ---------------------------------------------------------------- 2C-2: pais del mercado y presupuesto en moneda de la cuenta
#
# El targeting va al pais del mercado del producto (GT/CO: el codigo de mercado es el codigo
# de pais ISO que usa Meta) y una cuenta que no factura en USD recibe el presupuesto
# convertido a su moneda (COP en pesos enteros) en vez de bloquear. Sin mercado, el paquete
# bloquea.

_CUENTA_COP_TEST = {"cuenta_alias": "CO TEST", "cuenta_id": "999", "moneda": "COP",
                    "min_daily_budget_cents": "3154", "mcp_habilitado": "SI",
                    "tiene_metodo_pago": "SI", "sube_media_local": "NO", "estado_cuenta": "ACTIVE"}


def _paquete_solo(base, argv_extra):
    salida = os.path.join(base, "paquete.json")
    code, _out, err = _correr_main(base, ["--producto", "PX", "--fase", "1", "--solo-paquete",
                                          "--lanzamiento", MANANA, "--salida", salida] + argv_extra)
    with open(salida, encoding="utf-8") as fh:
        return code, json.load(fh), err


def test_targeting_usa_el_pais_del_mercado():
    base = _fixture_fase1_completa(mercado="CO")
    code, pq, err = _paquete_solo(base, [])
    paises = {tuple(json.loads(l["args"]["targeting"])["geo_locations"]["countries"])
              for l in pq["llamadas"] if l["tool"] == "ads_create_ad_set"}
    ok = err is None and paises == {("CO",)} and pq.get("pais") == "CO"
    return _informe(ok, 'mercado="CO": cada conjunto targetea ["CO"] y paquete["pais"] == "CO"',
                    (code, err, paises, pq.get("pais")))


def test_sin_mercado_bloquea_el_paquete():
    base = _fixture_fase1_completa(mercado="")
    code, pq, err = _paquete_solo(base, [])
    hit = [b for b in pq["bloqueantes"]
           if b["ambito"] == "paquete" and "columna mercado" in b["lo_produce"]]
    ok = err is None and code == 1 and bool(hit)
    return _informe(ok, 'mercado="": un bloqueante de ambito paquete nombra la columna mercado',
                    (code, err, pq["bloqueantes"]))


def test_cuenta_en_cop_presupuesta_en_pesos():
    base = _fixture_fase1_completa(cuenta_extra=dict(_CUENTA_COP_TEST), cuenta="CO TEST",
                                   mercado="CO", moneda="COP", tasa="3152.5")
    code, pq, err = _paquete_solo(base, ["--cuenta", "CO TEST"])
    sin_factura = not any("factura en" in b["falta"] for b in pq["bloqueantes"])
    ok = err is None and pq.get("daily_budget_cents") == 9426 and sin_factura
    return _informe(ok, "cuenta COP: 2.99 USD x 3152.5 = 9426 pesos, sin bloqueante de factura",
                    (code, err, pq.get("daily_budget_cents"), pq["bloqueantes"]))


def test_moneda_del_producto_distinta_a_la_cuenta_bloquea():
    base = _fixture_fase1_completa(cuenta_extra=dict(_CUENTA_COP_TEST), cuenta="CO TEST",
                                   mercado="CO", moneda="USD", tasa="3152.5")
    code, pq, err = _paquete_solo(base, ["--cuenta", "CO TEST"])
    hit = [b for b in pq["bloqueantes"]
           if b["ambito"] == "publicacion" and "factura en COP" in b["falta"]]
    ok = err is None and bool(hit)
    return _informe(ok, "producto en USD contra cuenta COP: bloquea la publicacion con factura en COP",
                    (code, err, pq["bloqueantes"]))


def test_cuenta_usd_sigue_en_centavos():
    base = _fixture_fase1_completa()
    code, pq, err = _paquete_solo(base, [])
    ok = err is None and pq.get("daily_budget_cents") == 299
    return _informe(ok, "cuenta USD: 2.99 sigue siendo 299 centavos, igual que antes",
                    (code, err, pq.get("daily_budget_cents")))


def test_token_producto_sale_de_clave_campana():
    """El token de los nombres sale de clave_campana (dueño: gen_lanzador.corto)."""
    casos = [
        ({"producto_key": "OVULOS_PURITY", "clave_campana": "OVULOSPURITY"}, "OVULOSPURITY"),
        ({"producto_key": "OVULOS_PURITY", "clave_campana": ""}, "OVULOS-PURITY"),
        ({"producto_key": "NUSAVA", "clave_campana": "NUSAVAB12"}, "NUSAVAB12"),
    ]
    mal = [(f, gp.token_producto(f)) for f, esperado in casos if gp.token_producto(f) != esperado]
    return _informe(not mal, "el token sale de clave_campana, o del producto_key si esta vacia", mal)


def test_paquete_nombra_con_el_token_de_clave_campana():
    """Con clave_campana=PXDOS, campana y conjuntos usan PXDOS y el paquete lo declara."""
    base = _fixture_fase1_completa(clave_campana="PXDOS")
    antes = _listado(base, "antes.json", [{"hash": "viejo2", "name": "PX_1_ANG1_V2.png"}])
    subidas = [{"hash": "h%d" % i, "name": "PX_%d_ANG%d_V%d.png" % (i, i, 3 if i == 1 else 2)} for i in range(1, 7)]
    despues = _listado(base, "despues.json", [{"hash": "viejo2", "name": "PX_1_ANG1_V2.png"}] + subidas)
    code, pq, err = _paquete_biblioteca(base, antes, despues)
    man = (pq or {}).get("manifiesto", {})
    ok = (err is None and code == 0
          and man.get("campana", "").startswith("GTR7_PXDOS_TEST_")
          and all(c["nombre"].startswith("GTR7_PXDOS_") for c in man.get("conjuntos", []))
          and man.get("conjuntos")
          and pq.get("token_producto") == "PXDOS")
    return _informe(ok, "el paquete nombra campana y conjuntos con el token de clave_campana",
                    (code, err, man.get("campana"), pq and pq.get("token_producto")))


def main():
    fallas = 0
    fallas += test_token_producto_sale_de_clave_campana()
    fallas += test_paquete_nombra_con_el_token_de_clave_campana()
    fallas += test_targeting_usa_el_pais_del_mercado()
    fallas += test_sin_mercado_bloquea_el_paquete()
    fallas += test_cuenta_en_cop_presupuesta_en_pesos()
    fallas += test_moneda_del_producto_distinta_a_la_cuenta_bloquea()
    fallas += test_cuenta_usd_sigue_en_centavos()
    fallas += test_fecha_hoy_bloquea()
    fallas += test_fecha_manana_no_bloquea()
    fallas += test_fecha_pasado_manana_bloquea()
    fallas += test_fecha_ayer_bloquea()
    fallas += test_biblioteca_sin_listado_espera_la_lectura_y_no_sube_nada()
    fallas += test_biblioteca_elige_un_nombre_que_no_existe()
    fallas += test_biblioteca_con_todo_subido_arma_el_paquete_sin_bloqueos()
    fallas += test_biblioteca_dos_imagenes_con_el_mismo_nombre_bloquean()
    fallas += test_subida_local_sigue_igual_para_la_skill()
    fallas += test_media_invalida_no_arranca()
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
    fallas += test_gate_cumplido_escribe_el_paquete()
    fallas += test_gate_incumplido_sin_excepcion_no_escribe_nada()
    fallas += test_gate_incumplido_excepcion_vacia_refusa_igual()
    fallas += test_gate_incumplido_con_excepcion_procede_y_registra_una_excepcion()
    fallas += test_los_bloqueos_del_operador_llevan_su_clave()
    fallas += test_exploracion_sin_fila_de_parametros_bloquea_nombrando_fase_y_brazo()
    fallas += test_exploracion_presupuesto_sale_del_csv_no_hardcodeado()
    fallas += test_exploracion_arma_tres_conjuntos_con_angulos_distintos()
    fallas += test_exploracion_gate_propio_incumplido_bloquea_sin_excepcion()
    fallas += test_exploracion_gate_propio_con_excepcion_registra_F3_exploracion()
    fallas += test_exploracion_gate_propio_cumplido_no_pide_excepcion()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
