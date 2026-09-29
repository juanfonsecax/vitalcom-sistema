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
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armar_prompts_fase2 as ap  # noqa: E402


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

def _entorno_json(con_packshot=True, con_precio=True, con_perfil=True, angulo="ANG"):
    """BASE/PROD_DIR temporales con un producto PX. Devuelve (base, restaurar)."""
    import json
    base = tempfile.mkdtemp(prefix="ap_json_")
    prod = os.path.join(base, "PRODUCTOS")
    os.makedirs(os.path.join(prod, "PX_CARPETA"))
    with open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "slug_carpeta"])
        w.writerow(["PX", "PX_CARPETA"])
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
            json.dump({"schema": "perfil_creativo/1", "angulo_key": angulo, "perfil": {}, "textos": textos}, fh)
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
                   test_json_exito_lista_lo_que_escribio_y_solo_bajo_su_carpeta):
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
