#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_page_id.py — GATE DE LA CARGA DEL page_id.

Congela lo que cargar_page_id.py no puede romper nunca:
  · el page_id tiene que ser un id de Meta (solo digitos); «PENDIENTE» se rechaza;
  · se escribe en el CSV Y en el encabezado de los TXT del producto, y despues de escribirlo
    verificar_producto.py pasa: un encabezado que dice «page_id PENDIENTE» con el CSV ya cargado
    es exactamente el fallo que ese gate declara (invariante 9);
  · del encabezado se reemplaza SOLO el valor del campo: el resto del archivo queda byte a byte;
  · un page_id ya cargado no se cambia sin --reemplazar;
  · un _PLAN.json con otro page_id se AVISA (gen_publicacion.py le da prioridad);
  · el resto del CSV queda intacto, --dry-run no toca nada y una falla a mitad no deja restos.

USO:  python Ads/_TOOLS/test_cargar_page_id.py     (exit 0 = pasa, 1 = falla)
"""

import csv
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_page_id  # noqa: E402
import verificar_producto  # noqa: E402

COLUMNAS_PRODUCTOS = [
    "producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
    "cuenta_id", "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q",
    "cpa_base_q", "cpa_be_q", "cpa_be_anterior_q", "notas", "carpeta_videos",
    "carpeta_transcripciones", "carpeta_media", "carpetas_extra", "clave_campana", "campaign_id",
]
NUEVA = "1279576438561754"
OTRA = "823825257480758"

CUERPO = "\r\nPRODUCTO: lo que sigue del archivo, con acentos: ñ á é\r\npage_id PENDIENTE (en el cuerpo NO se toca)\r\n"


def _p(slug, nombre):
    """Ruta relativa de un archivo de producto del fixture (armada por partes: no es una ruta del repo)."""
    return "/".join(("PRODUCTOS", slug, nombre))


def _encabezado(page_id, costo="60"):
    return (f"═══ SERUM UNO · VERSION v1 · 2026-09-17 · COSTO Q{costo} · DOSIS 3 gotas · "
            f"page_id {page_id} · campaign_id PENDIENTE ═══")


def _fila_producto(**campos):
    base = {c: "" for c in COLUMNAS_PRODUCTOS}
    base.update(campos)
    return [base[c] for c in COLUMNAS_PRODUCTOS]


def _escribir_csv(ruta, columnas, filas):
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(columnas)
        escritor.writerows(filas)


def _escribir(base, relativa, texto):
    ruta = os.path.join(base, *relativa.split("/"))
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with io.open(ruta, "wb") as fh:
        fh.write(texto.encode("utf-8"))


def _leer(base, relativa):
    with io.open(os.path.join(base, *relativa.split("/")), "rb") as fh:
        return fh.read().decode("utf-8")


def _fixture(base):
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), COLUMNAS_PRODUCTOS, [
        _fila_producto(producto_key="OTRO", slug_carpeta="OTRO", estado="VIVO", costo_q="50",
                       page_id="111111111111111", notas="una, con coma"),
        _fila_producto(producto_key="SERUM_UNO", slug_carpeta="SERUM_UNO", estado="NUEVO",
                       costo_q="60", page_id="PENDIENTE"),
        _fila_producto(producto_key="SOLO_ALTA", slug_carpeta="SOLO_ALTA", estado="NUEVO",
                       costo_q="60", page_id=""),
        _fila_producto(producto_key="CON_PAGINA", slug_carpeta="CON_PAGINA", estado="NUEVO",
                       costo_q="60", page_id=OTRA),
    ])
    for nombre in ("1_HACER_MANUAL.txt", "2_DATA_PRODUCTO.txt"):
        _escribir(base, _p("SERUM_UNO", nombre), _encabezado("PENDIENTE (externa)") + CUERPO)
    _escribir(base, _p("SOLO_ALTA", "2_DATA_PRODUCTO.txt"), "ALTA\r\nsin encabezado de paquete\r\n")
    _escribir(base, _p("CON_PAGINA", "1_HACER_MANUAL.txt"), _encabezado(f"{OTRA} (Astrid García)") + CUERPO)


def _fila(base, clave):
    filas = list(csv.reader(io.StringIO(_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), newline="")))
    return dict(zip(filas[0], next(f for f in filas[1:] if f and f[0] == clave)))


def _correr(base, producto, page_id, *extra):
    return cargar_page_id.main(["--producto", producto, "--page-id", page_id, "--base", base, *extra])


def _en_silencio(funcion):
    salida = io.StringIO()
    real, sys.stdout = sys.stdout, salida
    try:
        codigo = funcion()
    finally:
        sys.stdout = real
    return codigo, salida.getvalue()


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    fallas = []
    base = tempfile.mkdtemp(prefix="page_test_")
    try:
        _fixture(base)

        def carga_en_csv_y_en_los_encabezados():
            antes = {n: _leer(base, _p("SERUM_UNO", n)) for n in ("1_HACER_MANUAL.txt", "2_DATA_PRODUCTO.txt")}
            assert _en_silencio(lambda: _correr(base, "SERUM_UNO", NUEVA))[0] == 0
            assert _fila(base, "SERUM_UNO")["page_id"] == NUEVA
            for nombre, viejo in antes.items():
                nuevo = _leer(base, _p("SERUM_UNO", nombre))
                assert nuevo == viejo.replace("page_id PENDIENTE (externa) ·", f"page_id {NUEVA} ·", 1), \
                    f"{nombre}: se toco algo mas que el valor del campo"
                assert nuevo.split("\r\n", 1)[1] == viejo.split("\r\n", 1)[1], "el cuerpo tiene que quedar igual"
                assert "═══" in nuevo.split("\r\n", 1)[0] and nuevo.endswith("\r\n"), "conserva la forma"

        def el_gate_de_reconciliacion_pasa():
            fila = {"producto_key": "SERUM_UNO", "slug_carpeta": "SERUM_UNO", "estado": "NUEVO",
                    "costo_q": "60", "page_id": NUEVA, "cuenta_alias": "", "campaign_id": ""}
            real = verificar_producto.PROD
            verificar_producto.PROD = os.path.join(base, "PRODUCTOS")
            try:
                discrepancias, _, _ = verificar_producto.verificar("SERUM_UNO", {"SERUM_UNO": fila})
            finally:
                verificar_producto.PROD = real
            assert not [d for d in discrepancias if "page_id" in d], discrepancias

        def el_cuerpo_del_archivo_no_se_toca():
            assert "page_id PENDIENTE (en el cuerpo NO se toca)" in _leer(base, _p("SERUM_UNO", "1_HACER_MANUAL.txt"))

        def completa_un_producto_sin_encabezado_solo_en_el_csv():
            texto = _leer(base, _p("SOLO_ALTA", "2_DATA_PRODUCTO.txt"))
            assert _en_silencio(lambda: _correr(base, "SOLO_ALTA", NUEVA))[0] == 0
            assert _fila(base, "SOLO_ALTA")["page_id"] == NUEVA
            assert _leer(base, _p("SOLO_ALTA", "2_DATA_PRODUCTO.txt")) == texto

        def solo_toca_la_fila_del_producto():
            assert _fila(base, "OTRO")["page_id"] == "111111111111111"
            assert _fila(base, "OTRO")["notas"] == "una, con coma"
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv").count("\r\n") == 5

        def rechaza_lo_que_no_es_un_id():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            for malo in ("PENDIENTE", "12345", "1279 5764 3856 1754", "https://facebook.com/x", "12345678901234567890123"):
                assert _en_silencio(lambda: _correr(base, "CON_PAGINA", malo, "--reemplazar"))[0] == 1, malo
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def rechaza_producto_sin_fila():
            assert _en_silencio(lambda: _correr(base, "NO_EXISTE", NUEVA))[0] == 1

        def el_mismo_id_con_nombre_de_pagina_no_se_toca():
            """El encabezado real de CLEARSTEM dice «823... (Astrid García)»: el nombre no se pierde."""
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("CON_PAGINA", "1_HACER_MANUAL.txt")))
            codigo, salida = _en_silencio(lambda: _correr(base, "CON_PAGINA", OTRA, "--json"))
            assert codigo == 0 and json.loads(salida)["sin_cambios"] is True, salida
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("CON_PAGINA", "1_HACER_MANUAL.txt")))

        def no_cambia_un_page_id_cargado_sin_reemplazar():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            assert _en_silencio(lambda: _correr(base, "CON_PAGINA", NUEVA))[0] == 1
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes
            assert OTRA in _leer(base, _p("CON_PAGINA", "1_HACER_MANUAL.txt"))

        def reemplaza_con_bandera_y_corrige_el_encabezado():
            assert _en_silencio(lambda: _correr(base, "CON_PAGINA", NUEVA, "--reemplazar"))[0] == 0
            assert _fila(base, "CON_PAGINA")["page_id"] == NUEVA
            cabeza = _leer(base, _p("CON_PAGINA", "1_HACER_MANUAL.txt")).split("\r\n", 1)[0]
            assert f"page_id {NUEVA} · campaign_id" in cabeza and OTRA not in cabeza, cabeza

        def volver_a_correr_no_cambia_nada():
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("SERUM_UNO", "1_HACER_MANUAL.txt")))
            codigo, salida = _en_silencio(lambda: _correr(base, "SERUM_UNO", NUEVA, "--json"))
            resultado = json.loads(salida)
            assert codigo == 0 and resultado["sin_cambios"] is True and resultado["aplicado"] is False, resultado
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("SERUM_UNO", "1_HACER_MANUAL.txt")))

        def avisa_si_el_plan_trae_otra_pagina():
            _escribir(base, _p("OTRO", "_PLAN.json"), json.dumps({"page_id": "999999999999999"}))
            codigo, salida = _en_silencio(lambda: _correr(base, "OTRO", NUEVA, "--reemplazar", "--json"))
            assert codigo == 0
            assert any("_PLAN.json" in a for a in json.loads(salida)["avisos"]), salida

        def dry_run_no_toca_nada():
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("SOLO_ALTA", "2_DATA_PRODUCTO.txt")))
            assert _en_silencio(lambda: _correr(base, "CON_PAGINA", OTRA, "--reemplazar", "--dry-run"))[0] == 0
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, _p("SOLO_ALTA", "2_DATA_PRODUCTO.txt")))

        def una_falla_a_mitad_deja_todo_como_estaba():
            _escribir(base, _p("CON_PAGINA", "2_DATA_PRODUCTO.txt"), _encabezado(f"{NUEVA}") + CUERPO)
            archivos = ("PRODUCTOS/_DIM_PRODUCTOS.csv", _p("CON_PAGINA", "1_HACER_MANUAL.txt"),
                        _p("CON_PAGINA", "2_DATA_PRODUCTO.txt"))
            antes = [_leer(base, a) for a in archivos]
            original = cargar_page_id.ep.os.replace
            llamadas = {"n": 0}

            def replace_que_falla_a_la_segunda(origen, destino):
                llamadas["n"] += 1
                if llamadas["n"] == 2:
                    raise OSError("disco lleno (simulado)")
                return original(origen, destino)

            cargar_page_id.ep.os.replace = replace_que_falla_a_la_segunda
            try:
                try:
                    _en_silencio(lambda: _correr(base, "CON_PAGINA", "222222222222222", "--reemplazar"))
                    raise AssertionError("tenia que fallar")
                except OSError:
                    pass
            finally:
                cargar_page_id.ep.os.replace = original
            assert [_leer(base, a) for a in archivos] == antes, "todo tiene que volver a como estaba"
            assert llamadas["n"] >= 2, "la falla tenia que ocurrir con un archivo ya escrito"
            assert not [n for r, _, fs in os.walk(base) for n in fs if n.endswith(".tmp")], "no puede quedar un temporal"

        print("GATE DE LA CARGA DEL page_id")
        for nombre, funcion in (
            ("carga en el CSV y en los encabezados, sin tocar mas", carga_en_csv_y_en_los_encabezados),
            ("despues de cargarlo verificar_producto no marca page_id", el_gate_de_reconciliacion_pasa),
            ("el cuerpo del archivo no se toca", el_cuerpo_del_archivo_no_se_toca),
            ("un producto sin encabezado se completa solo en el CSV", completa_un_producto_sin_encabezado_solo_en_el_csv),
            ("solo toca la fila del producto", solo_toca_la_fila_del_producto),
            ("rechaza lo que no es un id de Meta", rechaza_lo_que_no_es_un_id),
            ("rechaza un producto sin fila", rechaza_producto_sin_fila),
            ("el mismo id con nombre de pagina en el encabezado no se toca", el_mismo_id_con_nombre_de_pagina_no_se_toca),
            ("no cambia un page_id cargado sin --reemplazar", no_cambia_un_page_id_cargado_sin_reemplazar),
            ("--reemplazar lo cambia y corrige el encabezado", reemplaza_con_bandera_y_corrige_el_encabezado),
            ("volver a correr no cambia nada", volver_a_correr_no_cambia_nada),
            ("avisa si el _PLAN.json trae otra pagina", avisa_si_el_plan_trae_otra_pagina),
            ("--dry-run no toca el disco", dry_run_no_toca_nada),
            ("una falla a mitad deja todo como estaba", una_falla_a_mitad_deja_todo_como_estaba),
        ):
            caso(nombre, funcion, fallas)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if fallas:
        print(f"\n{len(fallas)} falla(s): " + ", ".join(fallas))
        return 1
    print("\nTodo en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
