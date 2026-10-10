#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_armar_prompts_fase2.py — GATE DE LOS PRECIOS REALES EN armar_prompts_fase2.py
(G0.5 punto 4.5, 15-sep-2026).

leer_escalera() ya leia PRODUCTOS/_DIM_PRECIOS.csv desde el 08-sep-2026 (arreglo previo),
pero cuando devolvia None (sin fila ACTIVA para el producto) el llamador caia en SILENCIO
a un PRECIOS_GT hardcodeado en el codigo — los precios de TINNIDROP (Q179/Q239/Q299) para
CUALQUIER producto sin fila propia, y los de CLEARSTEM (Q199/Q299/Q399) en la adaptacion
de LucidBot, sin condicionar siquiera por producto. Misma clase de bug que
buscar_foto_producto()/leer_envase() (07-sep): sin el dato real, se bloquea, nunca se
asumen los precios de otro producto (invariante 4, CLAUDE.md).

USO:  python Ads/_TOOLS/test_armar_prompts_fase2.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armar_prompts_fase2 as ap  # noqa: E402
import seleccionar_canonicos as sc  # noqa: E402


def _dim_precios(tmp, filas):
    ruta = os.path.join(tmp, "_DIM_PRECIOS.csv")
    cols = ["producto_key", "unidades", "etiqueta", "precio_q", "precio_antes_q", "estado"]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow({**{c: "" for c in cols}, **f})
    return ruta


def test_producto_sin_fila_bloquea_no_hereda_precios_de_otro():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [{"producto_key": "TINNIDROP", "unidades": "1",
                            "precio_q": "179", "estado": "ACTIVO"}])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            ap.requerir_precios_reales("PRODUCTO_SIN_FILA")
            ok, msg = False, None
        except SystemExit as e:
            msg = str(e)
            ok = "PRODUCTO_SIN_FILA" in msg and "_DIM_PRECIOS.csv" in msg
        finally:
            ap.PROD_DIR = viejo
    print(("  OK     " if ok else "  FALLA  ")
          + "producto sin fila en _DIM_PRECIOS.csv BLOQUEA (nunca hereda los Q179 de TINNIDROP)"
          + ("" if ok else f"\n         msg={msg!r}"))
    return 0 if ok else 1


def test_producto_solo_inactivo_bloquea_igual():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [{"producto_key": "VIEJO", "unidades": "1",
                            "precio_q": "99", "estado": "RETIRADO"}])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            ap.requerir_precios_reales("VIEJO")
            ok = False
        except SystemExit:
            ok = True
        finally:
            ap.PROD_DIR = viejo
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila que existe pero no esta ACTIVA cuenta como 'sin precio real' — bloquea igual")
    return 0 if ok else 1


def test_producto_con_fila_activa_arma_la_escalera_real():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [
            {"producto_key": "CLEARSTEM", "unidades": "1", "precio_q": "198.00", "estado": "ACTIVO"},
            {"producto_key": "CLEARSTEM", "unidades": "2", "precio_q": "289.00", "estado": "ACTIVO"},
            {"producto_key": "CLEARSTEM", "unidades": "3", "precio_q": "389.01", "estado": "ACTIVO"},
        ])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            precios = ap.requerir_precios_reales("CLEARSTEM")
        finally:
            ap.PROD_DIR = viejo
    ok = ("Q198" in precios["TIER_1"] and "Q289" in precios["TIER_2"] and "Q389" in precios["TIER_3"])
    print(("  OK     " if ok else "  FALLA  ")
          + "con fila ACTIVA arma la escalera REAL (Q198/Q289/Q389, no Q199/Q299/Q399 hardcodeados)"
          + ("" if ok else f"\n         obtenido={precios!r}"))
    return 0 if ok else 1


def test_no_quedan_diccionarios_precios_gt_hardcodeados():
    """Regresion literal: los tres bloques PRECIOS_GT viejos (CLEARSTEM, TINNIDROP, el
    fallback generico) escribian el TIER directo como string con un Q de por medio —
    p.ej. '"TIER_1": "1 Frasco (1 Mes) por Q199"'. Ninguna linea del modulo debe volver
    a declarar un TIER_1/2/3 así: la escalera SIEMPRE debe salir de precios_reales."""
    with open(ap.__file__, encoding="utf-8") as fh:
        lineas = fh.readlines()
    ofensivas = [l.strip() for l in lineas if ("TIER_1" in l or "TIER_2" in l or "TIER_3" in l)
                 and "por Q" in l]
    ok = not ofensivas
    print(("  OK     " if ok else "  FALLA  ")
          + "ningun TIER_1/2/3 queda declarado como string literal con precio adentro"
          + ("" if ok else f"\n         lineas: {ofensivas}"))
    return 0 if ok else 1


# ── _PERFIL_CREATIVO.json — el codigo ya no nombra productos (defecto residual de la simulacion,
#    16-sep-2026). Tenia el perfil, los textos del creativo y el guion del bot escritos a mano:
#    `if producto_key == "CLEARSTEM"`. Un producto nuevo caia en un `else` que inventaba sus
#    ingredientes, y el guion de CLEARSTEM se aplicaba a TODOS — el paquete real de TINNIDROP
#    saluda "Vi que te interesó Clearstem para el acné hormonal".

def _con_producto(perfil_creativo=None):
    """PROD_DIR temporal con un producto PX (carpeta PX_CARPETA) y, opcional, su perfil creativo."""
    import json
    tmp = tempfile.mkdtemp(prefix="ap_perfil_")
    with open(os.path.join(tmp, "_DIM_PRODUCTOS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "slug_carpeta"])
        w.writerow(["PX", "PX_CARPETA"])
    os.makedirs(os.path.join(tmp, "PX_CARPETA"))
    if perfil_creativo is not None:
        with open(os.path.join(tmp, "PX_CARPETA", ap.PERFIL_CREATIVO), "w", encoding="utf-8") as fh:
            json.dump(perfil_creativo, fh)
    return tmp


def _bajo(tmp, fn):
    viejo = ap.PROD_DIR
    ap.PROD_DIR = tmp
    try:
        return fn(), None
    except SystemExit as e:
        return None, str(e)
    finally:
        ap.PROD_DIR = viejo


def test_el_codigo_no_decide_por_nombre_de_producto():
    """Ninguna comparacion del modulo contra un producto_key real: el dato vive en su archivo."""
    import ast
    with open(os.path.join(ap.PROD_DIR, "_DIM_PRODUCTOS.csv"), encoding="utf-8-sig") as fh:
        claves = {r["producto_key"].upper() for r in csv.DictReader(fh)}
    with open(ap.__file__, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read())
    ofensivas = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Compare):
            for c in [n.left] + n.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value.upper() in claves:
                    ofensivas.append("linea %d: %r" % (n.lineno, c.value))
    ok = not ofensivas
    print(("  OK     " if ok else "  FALLA  ")
          + "ninguna rama del codigo compara contra el nombre de un producto"
          + ("" if ok else "\n         " + "; ".join(ofensivas)))
    return 0 if ok else 1


def test_el_script_no_genera_ni_lee_texto_de_bot():
    """El flujo de LucidBot es de etapa-5. Este script armaba "¡Hola! Vi que te interesó [producto]
    para [dolor]" + una pregunta de calificacion, contra ETAPA-5.md (saludo FIJO sin dolor, sin
    pregunta de opciones), escrito para CLEARSTEM y aplicado a todos. No debe volver: ni como string
    del modulo ni leido de un archivo."""
    import ast
    with open(ap.__file__, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read())
    claves_bot = ("saludo_inicial_hook", "pregunta_calificacion", "presentacion_solucion", "lucidbot_adaptacion")
    docstrings = {id(n.body[0].value) for n in ast.walk(arbol)
                  if isinstance(n, (ast.Module, ast.FunctionDef)) and n.body
                  and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    ofensivas = sorted({n.lineno for n in ast.walk(arbol)
                        if isinstance(n, ast.Constant) and isinstance(n.value, str)
                        and id(n) not in docstrings and any(k in n.value for k in claves_bot)})
    ok = not ofensivas
    print(("  OK     " if ok else "  FALLA  ")
          + "el script no genera ni lee texto de bot (es de etapa-5: saludo fijo, sin pregunta de opciones)"
          + ("" if ok else f"\n         lineas: {ofensivas}"))
    return 0 if ok else 1


def test_producto_sin_perfil_creativo_bloquea_nombrando_al_productor():
    _, err = _bajo(_con_producto(), lambda: ap.cargar_perfil_creativo("PX"))
    ok = bool(err) and "BLOQUEANTE" in err and "_PERFIL_CREATIVO.json" in err and "generar-conceptos" in err
    print(("  OK     " if ok else "  FALLA  ")
          + "producto sin _PERFIL_CREATIVO.json: bloquea y nombra a generar-conceptos, no inventa"
          + ("" if ok else f"\n         err={err!r}"))
    return 0 if ok else 1


def test_perfil_sin_textos_bloquea_y_lista_los_que_faltan():
    doc = {"schema": "perfil_creativo/1", "angulo_key": "ANG", "perfil": {}, "textos": {"HOOK_TITULAR": "x", "CTA": "y"}}
    _, err = _bajo(_con_producto(doc), lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG"))
    ok = (bool(err) and "SUB_HOOK" in err and "ACTIVOS_CLAVE" in err and "GARANTIAS" in err
          and "HOOK_TITULAR" not in err.split("textos:")[1].split(".")[0])
    print(("  OK     " if ok else "  FALLA  ")
          + "textos incompletos: bloquea y nombra exactamente los que faltan (nunca un texto generico)"
          + ("" if ok else f"\n         err={err!r}"))
    return 0 if ok else 1


def test_textos_de_otro_angulo_bloquean():
    """Los textos son de UN angulo: si el ganador cambia, no se usan los del angulo anterior."""
    completos = {k: ("x" if k != "ACTIVOS_CLAVE" else ["x"]) for k in ap.TEXTOS_REQUERIDOS}
    doc = {"schema": "perfil_creativo/1", "angulo_key": "ACCESIBILIDAD_MEDICO", "perfil": {}, "textos": completos}
    base = _con_producto(doc)
    t, err_ok = _bajo(base, lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ACCESIBILIDAD_MEDICO"))
    _, err_otro = _bajo(base, lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "PERDIDA_AUDITIVA"))
    sin = dict(doc); sin.pop("angulo_key")
    _, err_sin = _bajo(_con_producto(sin), lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ACCESIBILIDAD_MEDICO"))
    ok = (err_ok is None and t == completos
          and bool(err_otro) and "ACCESIBILIDAD_MEDICO" in err_otro and "PERDIDA_AUDITIVA" in err_otro
          and bool(err_sin) and "sin declarar" in err_sin)
    return _check_simple(ok, "textos de un angulo: sirven para ese, bloquean para otro y sin angulo declarado",
                         "ok=%r otro=%r sin=%r" % (err_ok, err_otro, err_sin))


def _check_simple(ok, nombre, detalle):
    print(("  OK     " if ok else "  FALLA  ") + nombre + ("" if ok else "\n         " + detalle))
    return 0 if ok else 1


def test_lo_no_declarado_del_perfil_queda_falso_no_optimista():
    """El `else` viejo asumia resultado_visible_en_el_cuerpo=True para todo producto nuevo."""
    doc = {"schema": "perfil_creativo/1", "perfil": {"categoria": "dolor"}, "textos": {}}
    p, err = _bajo(_con_producto(doc), lambda: ap.obtener_perfil_producto("PX", "ANG"))
    ok = (err is None and p["categoria"] == "dolor" and p["resultado_visible_en_el_cuerpo"] is False
          and p["producto"] == "PX" and p["angulo_ganador"] == "ANG")
    print(("  OK     " if ok else "  FALLA  ")
          + "perfil: lo declarado manda y lo no declarado queda falso (regla de seleccionar_canonicos)"
          + ("" if ok else f"\n         p={p} err={err!r}"))
    return 0 if ok else 1


# ── --json: el bloqueo como dato (C3, la app lanza este script con un boton) ───────────────

REAL_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doctrina_registros(base, invima=None):
    """DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md de la doctrina real; con `invima` reemplaza el PENDIENTE."""
    import re
    with open(os.path.join(REAL_BASE, "DOCTRINA", "PLANTILLAS_DEFAULTS_OPERADOR.md"), encoding="utf-8") as fh:
        texto = fh.read()
    if invima:
        texto, n = re.subn(r"(\| `\[REG_INVIMA\]` \| )\*\*PENDIENTE del operador\*\* — no hay valor",
                           lambda m: m.group(1) + "**`%s`** — valor de prueba" % invima, texto)
        assert n == 1
    os.makedirs(os.path.join(base, "DOCTRINA"), exist_ok=True)
    with open(os.path.join(base, "DOCTRINA", "PLANTILLAS_DEFAULTS_OPERADOR.md"), "w", encoding="utf-8") as fh:
        fh.write(texto)


def _entorno_json(con_packshot=True, con_precio=True, con_perfil=True, angulo="ANG", mercado="GT", invima=None,
                  perfil=None, con_parametros=False):
    """BASE/PROD_DIR temporales con un producto PX del `mercado`. Devuelve (base, restaurar)."""
    import json
    base = tempfile.mkdtemp(prefix="ap_json_")
    prod = os.path.join(base, "PRODUCTOS")
    os.makedirs(os.path.join(prod, "PX_CARPETA"))
    with open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "slug_carpeta", "mercado"])
        w.writerow(["PX", "PX_CARPETA", mercado])
    for nombre in ("_DIM_MERCADOS.csv", "_PARAMETROS_FINANZAS.csv"):
        shutil.copy(os.path.join(REAL_BASE, "PRODUCTOS", nombre), os.path.join(prod, nombre))
    _doctrina_registros(base, invima)
    with open(os.path.join(prod, "_DIM_ENVASE.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "packshot"])
        if con_packshot:
            w.writerow(["PX", "Ads/MEDIA_PX/PX_PACKSHOT.png"])
    os.makedirs(os.path.join(base, "Ads", "MEDIA_PX"))
    if con_packshot:
        with open(os.path.join(base, "Ads", "MEDIA_PX", "PX_PACKSHOT.png"), "wb") as fh:
            fh.write(b"PNG")
    _dim_precios(prod, [{"producto_key": "PX", "unidades": str(u), "precio_q": str(100 + u * 50),
                         "estado": "ACTIVO"} for u in (1, 2, 3)] if con_precio else [])
    if con_perfil:
        textos = {k: ("x" if k != "ACTIVOS_CLAVE" else ["x"]) for k in ap.TEXTOS_REQUERIDOS}
        with open(os.path.join(prod, "PX_CARPETA", ap.PERFIL_CREATIVO), "w", encoding="utf-8") as fh:
            json.dump({"schema": "perfil_creativo/1", "angulo_key": angulo, "perfil": perfil or {}, "textos": textos}, fh)
    if con_parametros:  # la estructura de FASE 2: A (1x5) + B (1x5) = 10 conceptos; C repite los mismos
        with open(os.path.join(prod, "_PARAMETROS_PUBLICACION.csv"), "w", newline="", encoding="utf-8") as fh:
            fh.write("fase,brazo,conjuntos,anuncios_por_conjunto,estado" + chr(10)
                     + "2,A,1,5,VIGENTE" + chr(10) + "2,B,1,5,VIGENTE" + chr(10) + "2,C,2,5,VIGENTE" + chr(10))
    viejo = (ap.BASE, ap.PROD_DIR, ap.DECISIONES_JSON)
    ap.BASE, ap.PROD_DIR, ap.DECISIONES_JSON = base, prod, os.path.join(prod, "_DECISIONES.json")

    def restaurar():
        ap.BASE, ap.PROD_DIR, ap.DECISIONES_JSON = viejo
    return base, restaurar


def _correr_main(argv):
    import contextlib
    import json
    salida, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(err):
        codigo = ap.main(argv)
    return codigo, json.loads(salida.getvalue()), err.getvalue()


def test_json_bloqueo_por_packshot_dice_el_dato_y_sale_con_1():
    _, restaurar = _entorno_json(con_packshot=False)
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert codigo == 1
    assert cuerpo["ok"] is False and cuerpo["bloqueado"] is True and cuerpo["dato"] == "packshot"
    assert "packshot" in cuerpo["motivo"] and chr(10) not in cuerpo["motivo"] and not cuerpo["motivo"].startswith("BLOQUEANTE")
    assert cuerpo["detalle"].startswith("BLOQUEANTE")


def test_json_bloqueo_por_precio_y_por_perfil_creativo():
    _, restaurar = _entorno_json(con_precio=False)
    try:
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert cuerpo["dato"] == "precio"
    _, restaurar = _entorno_json(con_perfil=False)
    try:
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert cuerpo["dato"] == "perfil_creativo"
    _, restaurar = _entorno_json(angulo="OTRO")
    try:
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert cuerpo["dato"] == "perfil_creativo" and "OTRO" in cuerpo["detalle"]


def test_sin_json_el_bloqueo_sigue_siendo_systemexit_con_el_mismo_texto():
    _, restaurar = _entorno_json(con_packshot=False)
    try:
        try:
            ap.main(["PX", "ANG"])
            msg = None
        except SystemExit as e:
            msg = str(e)
    finally:
        restaurar()
    assert msg and msg.startswith("BLOQUEANTE: PX no tiene packshot declarado")
    assert isinstance(ap.Bloqueado("x", "packshot"), SystemExit)


def test_json_exito_lista_lo_que_escribio_y_solo_bajo_su_carpeta():
    base, restaurar = _entorno_json()
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert codigo == 0 and cuerpo["ok"] is True and cuerpo["bloqueado"] is False
    assert cuerpo["producto_key"] == "PX" and cuerpo["angulo_key"] == "ANG" and cuerpo["conceptos"] >= 1
    assert cuerpo["archivos"] == ["Ads/MEDIA_PX/FASE2_ANG/PROMPTS_FASE2_ANG.txt",
                                  "Ads/MEDIA_PX/FASE2_ANG/PAQUETE_CREATIVO_ANG.json"]
    for rel in cuerpo["archivos"]:
        assert os.path.isfile(os.path.join(base, *rel.split("/")))
    escritos = sorted(os.path.relpath(os.path.join(d, f), base).replace("\\", "/")
                      for d, _, fs in os.walk(os.path.join(base, "Ads")) for f in fs)
    assert all(e.startswith("Ads/MEDIA_PX/") for e in escritos)



# ── segunda tanda: el script es el DUEÑO de «qué canónicos» y no repite los ya registrados ──────────

def _perfil_rico():
    """Un perfil que deja pasar casi todos los gates (>=10 canonicos aptos)."""
    perfil = dict(sc.PLANTILLA_PERFIL)
    for k, v in perfil.items():
        if isinstance(v, bool):
            perfil[k] = True
        elif isinstance(v, int) and k != "nivel_conciencia_objetivo":
            perfil[k] = 5
    perfil.update(categoria="dolor", tiers_de_oferta=3, testimonios_reales_disponibles=5,
                  prueba_social_clientes=500, alternativa_conocida="")
    perfil.pop("producto", None)
    perfil.pop("angulo_ganador", None)
    return perfil


def _registrar(prod, canonicos, angulo="ANG", pk="PX", estado="GENERADO", extra_filas=0):
    """Escribe _DIM_CREATIVOS.csv como lo deja etapa-9 (esta prueba SI escribe: es un sandbox)."""
    with open(os.path.join(prod, "_DIM_CREATIVOS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "creativo_id", "angulo_key", "canonico_id", "concepto_key", "estado"])
        for c in canonicos:
            w.writerow([pk, f"{pk}_F2_{c}", angulo, c, "", estado])
        for i in range(extra_filas):  # piezas viejas del angulo, sin canonico
            w.writerow([pk, f"{pk}_R{i}", angulo, "", "SIN_CLASIFICAR", "PENDIENTE_GENERAR"])


def _ids(cuerpo):
    return cuerpo["canonicos"]


def _paquete(base, angulo="ANG"):
    import json
    ruta = os.path.join(base, "Ads", "MEDIA_PX", f"FASE2_{angulo}", f"PAQUETE_CREATIVO_{angulo}.json")
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def test_selector_excluye_los_ya_registrados_y_sigue_la_regla_del_concepto_key():
    perfil = dict(_perfil_rico(), producto="PX", angulo_ganador="ANG")
    uno = sc.seleccionar(perfil, 5)
    ya = [i["canonico_id"] for i in uno["seleccion"]]
    dos = sc.seleccionar(perfil, 5, ya=ya)
    ids2 = [i["canonico_id"] for i in dos["seleccion"]]
    assert len(ids2) == 5 and not set(ids2) & set(ya), "5 canonicos DISTINTOS de los ya registrados"
    docs = sc.cargar_canonicos()
    ck = lambda cid: sc.concepto_dominante(docs[cid])  # noqa: E731
    usados = {ck(c) for c in ya}
    sin_usar = [c for c in ids2 if ck(c) not in usados]
    # un concepto_key sin usar entra antes que uno repetido: mientras queden, no se repite
    assert sin_usar and ids2[:len(sin_usar)] == sin_usar
    assert dos["ya_registrados"] == sorted(ya)
    assert set(dos["repiten_concepto_key"]) == set(ids2) - set(sin_usar)
    assert not set(i["canonico_id"] for i in dos["aptos_no_elegidos"]) & set(ya)


def test_al_repetir_se_reparte_entre_los_concepto_key_menos_usados():
    """Agotados los concepto_key sin usar, el relleno va al menos usado, no siempre al primero de la rotacion."""
    perfil = dict(_perfil_rico(), producto="PX", angulo_ganador="ANG")
    aptos, _ = sc.evaluar(perfil, sc.cargar_canonicos())
    disponibles = {}
    for it in aptos:
        disponibles[it["concepto_key"]] = disponibles.get(it["concepto_key"], 0) + 1
    distintos = len(disponibles)
    assert len(aptos) > distintos + 2, "el perfil de prueba tiene que obligar a repetir"
    res = sc.seleccionar(perfil, distintos + 3)
    conteo = {}
    for it in res["seleccion"]:
        conteo[it["concepto_key"]] = conteo.get(it["concepto_key"], 0) + 1
    assert set(conteo) == set(disponibles), "primero entra un canonico de cada concepto_key"
    # ningun concepto_key lleva 2+ piezas mas que otro al que todavia le quedaban aptos sin elegir
    for ck, veces in conteo.items():
        for otro, veces_otro in conteo.items():
            if veces_otro < disponibles[otro]:
                assert veces - veces_otro <= 1, (ck, veces, otro, veces_otro)


def test_segunda_tanda_elige_otros_5_y_no_pisa_la_primera():
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    prod = os.path.join(base, "PRODUCTOS")
    try:
        c1, uno, _ = _correr_main(["PX", "ANG", "--json", "--n", "5"])
        assert c1 == 0 and uno["conceptos"] == 5 and len(_ids(uno)) == 5
        primera = {x["canonico_id"]: x["prompt_director_de_arte"] for x in _paquete(base)["conceptos"]}
        _registrar(prod, _ids(uno))
        c2, dos, _ = _correr_main(["PX", "ANG", "--json"])  # sin --n: faltan 10 - 5 = 5
        assert c2 == 0 and dos["conceptos"] == 5
        assert not set(_ids(dos)) & set(_ids(uno)), "ningun canonico de la tanda 1 se repite"
        paquete = _paquete(base)
        todos = {x["canonico_id"]: x for x in paquete["conceptos"]}
        assert set(todos) == set(_ids(uno)) | set(_ids(dos)), "el paquete acumula las dos tandas"
        for cid, prompt in primera.items():  # la tanda 1 quedo intacta, byte a byte
            assert todos[cid]["prompt_director_de_arte"] == prompt
        assert [x["slot"] for x in paquete["conceptos"]] == list(range(1, 11))
        # lo que lee la app: cada concepto trae su prompt y su imagen de referencia
        assert all(x["prompt_director_de_arte"] and "foto_base_competidor" in x for x in todos.values())
        ruta_txt = os.path.join(base, "Ads", "MEDIA_PX", "FASE2_ANG", "PROMPTS_FASE2_ANG.txt")
        with open(ruta_txt, encoding="utf-8") as fh:
            txt = fh.read()
        assert all(cid in txt for cid in todos), "el .txt lista las dos tandas"
        assert dos["archivos"] == uno["archivos"], "mismos archivos, acumulados (no uno por tanda que se pise)"
    finally:
        restaurar()


def test_repetir_la_misma_tanda_es_idempotente():
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    prod = os.path.join(base, "PRODUCTOS")
    try:
        _, uno, _ = _correr_main(["PX", "ANG", "--json", "--n", "5"])
        _registrar(prod, _ids(uno))
        _, dos, _ = _correr_main(["PX", "ANG", "--json"])
        _, tres, _ = _correr_main(["PX", "ANG", "--json"])  # la tanda 2 nunca se registro: se rehace igual
        assert _ids(tres) == _ids(dos)
        assert len(_paquete(base)["conceptos"]) == 10
    finally:
        restaurar()


def test_nada_que_hacer_cuando_no_falta_ningun_concepto():
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    prod = os.path.join(base, "PRODUCTOS")
    try:
        _, uno, _ = _correr_main(["PX", "ANG", "--json", "--n", "10"])
        assert uno["conceptos"] == 10
        _registrar(prod, _ids(uno))
        ruta = os.path.join(base, "Ads", "MEDIA_PX", "FASE2_ANG", "PAQUETE_CREATIVO_ANG.json")
        with open(ruta, "rb") as fh:
            antes = fh.read()
        codigo, nada, _ = _correr_main(["PX", "ANG", "--json"])
        assert codigo == 0 and nada["ok"] is True and nada["nada_que_hacer"] is True and nada["conceptos"] == 0
        assert "no falta" in nada["aviso"].lower()
        with open(ruta, "rb") as fh:
            assert fh.read() == antes, "no escribe nada"
    finally:
        restaurar()


def test_n_se_topa_con_lo_que_falta_para_la_estructura():
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    prod = os.path.join(base, "PRODUCTOS")
    try:
        _registrar(prod, ["CN01_ANTES_DESPUES", "CN02_TIMELINE_PROGRESION", "CN10_PRUEBA_SOCIAL",
                          "CN04_ESCALERA_PRECIOS", "CN05_LISTA_BENEFICIOS", "CN03_OFERTA_MULTIPLICADOR",
                          "CN07_DOLOR_A_PLENO", "CN06_CHECKLIST_SINTOMAS"])
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json", "--n", "9"])  # faltan 2 de 10
        assert cuerpo["conceptos"] == 2 and "tope" in cuerpo["aviso"].lower()
    finally:
        restaurar()


def test_si_quedan_menos_aptos_que_los_pedidos_lo_dice_y_no_repite():
    base, restaurar = _entorno_json(con_parametros=True)  # perfil vacio: solo 4 canonicos aptos
    prod = os.path.join(base, "PRODUCTOS")
    try:
        _registrar(prod, ["CN20_PRECIO_ANCLA"])
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json", "--n", "5"])
        assert codigo == 0 and cuerpo["ok"] is True
        assert cuerpo["conceptos"] == 3 and cuerpo["solicitados"] == 5 and cuerpo["faltantes_de_aptos"] == 2
        assert "CN20_PRECIO_ANCLA" not in _ids(cuerpo)
        assert "3" in cuerpo["aviso"] and "descartad" in cuerpo["aviso"].lower()
        assert cuerpo["descartados"] and {"canonico_id", "motivo"} <= set(cuerpo["descartados"][0])
    finally:
        restaurar()


def test_piezas_viejas_sin_canonico_cuentan_como_registradas_pero_no_excluyen_nada():
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    prod = os.path.join(base, "PRODUCTOS")
    try:
        _registrar(prod, [], extra_filas=4)  # 4 piezas R1..R4 del angulo, sin canonico
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
        assert cuerpo["conceptos"] == 6, "10 requeridos - 4 registradas"
    finally:
        restaurar()


def test_sin_estructura_declarada_el_default_sigue_siendo_5():
    _, restaurar = _entorno_json(perfil=_perfil_rico())  # sin _PARAMETROS_PUBLICACION.csv
    try:
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
        assert cuerpo["conceptos"] == 5
    finally:
        restaurar()


# ── multi-mercado (D6): el prompt sale del mercado del producto, no de Guatemala hardcodeada ──────────

def _prompt_de(mercado, invima=None):
    _, restaurar = _entorno_json(mercado=mercado, invima=invima)
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
        assert codigo == 0, cuerpo
        with open(os.path.join(ap.BASE, cuerpo["archivos"][0].replace("/", os.sep)), encoding="utf-8") as fh:
            return fh.read()
    finally:
        restaurar()


def test_gt_conserva_el_registro_el_pais_el_voseo_y_la_moneda():
    t = _prompt_de("GT")
    assert ("MSPAS NS02026-GT3147 · FDA 30045469041. Somos de Guatemala: nunca INVIMA ni "
            "ningún otro regulador extranjero.") in t
    assert "Meta Ads en Guatemala." in t and "OMITILO" in t and "REPLICALO" in t
    linea_precios = next(l for l in t.splitlines() if "Escalera de Precios" in l)
    assert "Tier 1: 1 Frasco por Q150" in linea_precios and "$" not in linea_precios


def test_co_usa_tuteo_invima_y_pesos():
    t = _prompt_de("CO", invima="INVIMA 2026M-0012345")
    assert "Meta Ads en Colombia." in t
    assert "INVIMA 2026M-0012345. Somos de Colombia: nunca MSPAS ni ningún otro regulador extranjero." in t
    assert "OMÍTELO" in t and "RÉPLICALO" in t and "OMITILO" not in t and "REPLICALO" not in t
    assert "Tier 1: 1 Frasco por $ 150" in t
    for ajeno in ("NS02026", "30045469041", "Guatemala", "Q150"):
        assert ajeno not in t


def test_co_sin_numero_invima_bloquea_con_dato_registro_sanitario():
    base, restaurar = _entorno_json(mercado="CO")
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert codigo == 1 and cuerpo["bloqueado"] is True and cuerpo["dato"] == "registro_sanitario"
    assert "INVIMA" in cuerpo["motivo"] and "PX" in cuerpo["motivo"]
    assert "MSPAS" not in cuerpo["motivo"]
    assert not os.path.exists(os.path.join(base, "Ads", "MEDIA_PX", "FASE2_ANG")), "no escribio nada"


def test_producto_sin_mercado_bloquea_no_asume_gt():
    _, restaurar = _entorno_json(mercado="")
    try:
        _, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
    finally:
        restaurar()
    assert cuerpo["dato"] == "mercado" and "GT o CO" in cuerpo["detalle"]


# ── textos por angulo (perfil_creativo/2) ────────────────────────────────────────────────────────────

def _textos(marca):
    return {k: (marca if k != "ACTIVOS_CLAVE" else [marca]) for k in ap.TEXTOS_REQUERIDOS}


def _doc_dos_angulos():
    return {"schema": "perfil_creativo/2", "producto_key": "PX", "perfil": {},
            "textos_por_angulo": {"ANG_A": {"textos": _textos("a"), "textos_notas": {"n": "a"}},
                                  "ANG_B": {"textos": _textos("b")}}}


def test_textos_por_angulo_devuelve_los_del_angulo_pedido():
    base = _con_producto(_doc_dos_angulos())
    ta, ea = _bajo(base, lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG_A"))
    tb, eb = _bajo(base, lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG_B"))
    assert ea is None and eb is None
    assert ta == _textos("a") and tb == _textos("b")


def test_angulo_ausente_en_textos_por_angulo_bloquea_con_dato_perfil_creativo():
    base = _con_producto(_doc_dos_angulos())
    viejo = ap.PROD_DIR
    ap.PROD_DIR = base
    try:
        try:
            ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG_C")
            raise AssertionError("debio bloquear")
        except ap.Bloqueado as e:
            assert e.dato == "perfil_creativo"
            msg = str(e)
            assert "ANG_C" in msg and "ANG_A" in msg and "ANG_B" in msg and "generar-conceptos" in msg
    finally:
        ap.PROD_DIR = viejo


def test_textos_por_angulo_sigue_exigiendo_los_textos_requeridos():
    doc = _doc_dos_angulos()
    doc["textos_por_angulo"]["ANG_B"]["textos"].pop("CTA")
    _, err = _bajo(_con_producto(doc), lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG_B"))
    assert err and "CTA" in err


def test_perfil_viejo_de_un_solo_angulo_sigue_funcionando():
    doc = {"schema": "perfil_creativo/1", "angulo_key": "ANG_A", "perfil": {}, "textos": _textos("a")}
    t, err = _bajo(_con_producto(doc), lambda: ap.requerir_textos(ap.cargar_perfil_creativo("PX"), "PX", "ANG_A"))
    assert err is None and t == _textos("a")


def test_generar_para_un_angulo_no_toca_los_textos_del_otro():
    import json
    base, restaurar = _entorno_json(angulo="ANG_A")
    try:
        ruta = os.path.join(ap.PROD_DIR, "PX_CARPETA", ap.PERFIL_CREATIVO)
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(_doc_dos_angulos(), fh)
        with open(ruta, "rb") as fh:
            antes = fh.read()
        codigo, cuerpo, _ = _correr_main(["PX", "ANG_B", "--json"])
        assert codigo == 0, cuerpo
        with open(ruta, "rb") as fh:
            assert fh.read() == antes
        with open(os.path.join(ap.BASE, cuerpo["archivos"][0].replace("/", os.sep)), encoding="utf-8") as fh:
            assert '"b"' in fh.read()
    finally:
        restaurar()


# ── dispositivo neutro por canonico (T4): el prompt usa el del canonico, no el de la ficha de otro nicho ──

# Palabras de nicho que un dispositivo neutro no puede nombrar: son zonas del cuerpo o dolencias de los
# anuncios de referencia; el dispositivo describe la composicion, no el producto del anuncio original.
PALABRAS_DE_NICHO = ("pie", "pies", "oido", "oído", "acne", "acné", "varice", "várice", "hongo", "cabello",
                     "rodilla", "ovulo", "óvulo")


def test_todo_canonico_declara_un_dispositivo_neutro():
    import re
    docs = sc.cargar_canonicos()
    assert len(docs) == 22
    for cid, doc in docs.items():
        d = (doc.get("dispositivo") or "").strip()
        assert d, f"{cid} no declara `dispositivo`"
        for palabra in PALABRAS_DE_NICHO:
            assert not re.search(r"" + palabra + r"", d, re.IGNORECASE), f"{cid}: «{palabra}» en su dispositivo"


def test_el_prompt_usa_el_dispositivo_del_canonico_y_no_el_de_la_ficha():
    import json
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
        assert codigo == 0, cuerpo
        docs = sc.cargar_canonicos()
        paquete = _paquete(base)
        assert paquete["conceptos"]
        for c in paquete["conceptos"]:
            doc = docs[c["canonico_id"]]
            ruta = os.path.join(ap.SWIPE_DIR, "_BLUEPRINTS", "FICHAS", doc["ficha_referencia"] + ".json")
            with open(ruta, encoding="utf-8") as fh:
                ficha = json.load(fh)["dispositivo_dominante"]
            linea = "- Dispositivo Canónico: " + doc["dispositivo"]
            assert linea in c["prompt_director_de_arte"], c["canonico_id"]
            if ficha != doc["dispositivo"]:  # algunas fichas ya son neutras y coinciden con el canonico
                assert ficha not in c["prompt_director_de_arte"], c["canonico_id"]
    finally:
        restaurar()


def test_sin_dispositivo_en_el_canonico_cae_al_de_la_ficha():
    import json
    base, restaurar = _entorno_json(perfil=_perfil_rico(), con_parametros=True)
    docs = sc.cargar_canonicos()
    viejo = sc.cargar_canonicos
    sc.cargar_canonicos = lambda: {k: {kk: vv for kk, vv in v.items() if kk != "dispositivo"} for k, v in docs.items()}
    try:
        codigo, cuerpo, _ = _correr_main(["PX", "ANG", "--json"])
        assert codigo == 0, cuerpo
        for c in _paquete(base)["conceptos"]:
            ruta = os.path.join(ap.SWIPE_DIR, "_BLUEPRINTS", "FICHAS", docs[c["canonico_id"]]["ficha_referencia"] + ".json")
            with open(ruta, encoding="utf-8") as fh:
                assert json.load(fh)["dispositivo_dominante"] in c["prompt_director_de_arte"]
    finally:
        sc.cargar_canonicos = viejo
        restaurar()


def main():
    fallas = 0
    fallas += test_producto_sin_fila_bloquea_no_hereda_precios_de_otro()
    fallas += test_producto_solo_inactivo_bloquea_igual()
    fallas += test_producto_con_fila_activa_arma_la_escalera_real()
    fallas += test_no_quedan_diccionarios_precios_gt_hardcodeados()
    fallas += test_el_codigo_no_decide_por_nombre_de_producto()
    fallas += test_el_script_no_genera_ni_lee_texto_de_bot()
    fallas += test_producto_sin_perfil_creativo_bloquea_nombrando_al_productor()
    fallas += test_perfil_sin_textos_bloquea_y_lista_los_que_faltan()
    fallas += test_textos_de_otro_angulo_bloquean()
    fallas += test_lo_no_declarado_del_perfil_queda_falso_no_optimista()
    for prueba in (test_json_bloqueo_por_packshot_dice_el_dato_y_sale_con_1,
                   test_json_bloqueo_por_precio_y_por_perfil_creativo,
                   test_sin_json_el_bloqueo_sigue_siendo_systemexit_con_el_mismo_texto,
                   test_json_exito_lista_lo_que_escribio_y_solo_bajo_su_carpeta,
                   test_selector_excluye_los_ya_registrados_y_sigue_la_regla_del_concepto_key,
                   test_segunda_tanda_elige_otros_5_y_no_pisa_la_primera,
                   test_repetir_la_misma_tanda_es_idempotente,
                   test_nada_que_hacer_cuando_no_falta_ningun_concepto,
                   test_n_se_topa_con_lo_que_falta_para_la_estructura,
                   test_si_quedan_menos_aptos_que_los_pedidos_lo_dice_y_no_repite,
                   test_piezas_viejas_sin_canonico_cuentan_como_registradas_pero_no_excluyen_nada,
                   test_sin_estructura_declarada_el_default_sigue_siendo_5,
                   test_gt_conserva_el_registro_el_pais_el_voseo_y_la_moneda,
                   test_co_usa_tuteo_invima_y_pesos,
                   test_co_sin_numero_invima_bloquea_con_dato_registro_sanitario,
                   test_producto_sin_mercado_bloquea_no_asume_gt,
                   test_textos_por_angulo_devuelve_los_del_angulo_pedido,
                   test_angulo_ausente_en_textos_por_angulo_bloquea_con_dato_perfil_creativo,
                   test_textos_por_angulo_sigue_exigiendo_los_textos_requeridos,
                   test_perfil_viejo_de_un_solo_angulo_sigue_funcionando,
                   test_generar_para_un_angulo_no_toca_los_textos_del_otro,
                   test_todo_canonico_declara_un_dispositivo_neutro,
                   test_el_prompt_usa_el_dispositivo_del_canonico_y_no_el_de_la_ficha,
                   test_sin_dispositivo_en_el_canonico_cae_al_de_la_ficha):
        try:
            prueba()
            print("  OK     " + prueba.__name__)
        except AssertionError as e:
            fallas += 1
            print("  FALLA  " + prueba.__name__ + chr(10) + "         " + repr(e))
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
