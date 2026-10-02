#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cambiar_costo.py — GATE DEL CAMBIO DE COSTO.

Congela lo que cambiar_costo.py no puede romper nunca:
  · cambia el costo en el CSV y en la linea «costo del pedido» del 2_DATA_PRODUCTO.txt que dejo
    el alta, y en nada mas: ni precio, ni CPA, ni break-even (los calcula costear.py y los
    guarda etapa-guardar-producto: un dato, un dueno);
  · una vez armado el paquete de FASE 1 (cifras de costeo, 1_HACER_MANUAL.txt o un 2_DATA con
    encabezado de paquete) BLOQUEA: cambiar el costo ahi es rerun completo (invariante 5), no
    un parche que deje el costo contradiciendose entre archivos;
  · rechaza costos que no son un numero positivo; acepta la coma decimal;
  · el resto del CSV queda intacto, --dry-run no toca nada, volver a correr no cambia nada y
    una falla a mitad no deja restos.

P3 T4 (continuación parte 2) — `editar_producto.aplicar_escrituras()` escribe la fila de
_DIM_PRODUCTOS.csv por Postgres (db/escribir.py): la VERDAD pasa a raw.producto/core.producto.
Aislamiento CRÍTICO (mismo patrón que test_registrar_evento.py/test_alta_producto.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su
PROPIO tenant único para esta corrida (el fixture usa `alta_producto.py` de verdad, que también
escribe por Postgres bajo el mismo tenant) y nunca toca `vitalcom` real. Se salta con aviso si
`vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_cambiar_costo.py     (exit 0 = pasa/salta, 1 = falla)
"""

import csv
import io
import json
import os
import shutil
import sys
import tempfile
import uuid

# Aislamiento CRÍTICO: forzar vitalcom_test ANTES de conectar.
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alta_producto  # noqa: E402
import cambiar_costo  # noqa: E402

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db")
sys.path.insert(0, DB_DIR)
import cargar as db_cargar  # noqa: E402
import nucleo as db_nucleo  # noqa: E402


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
            "test_cambiar_costo.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
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


def _tenant_unico():
    return "test_costo_%s" % uuid.uuid4().hex[:8]


def _bootstrap_producto(prod_dir, tenant):
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant, "producto", "_DIM_PRODUCTOS.csv",
                                                 False, prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_DIM_PRODUCTOS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()

COLUMNAS_PRODUCTOS = [
    "producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
    "cuenta_id", "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q",
    "cpa_base_q", "cpa_be_q", "cpa_be_anterior_q", "notas", "carpeta_videos",
    "carpeta_transcripciones", "carpeta_media", "carpetas_extra", "clave_campana", "campaign_id",
    "mercado",
]
COLUMNAS_ENVASE = [
    "producto_key", "packshot", "color_envase", "color_hex", "marca_impresa",
    "formato_envase", "verificado_el", "fuente", "notas",
]
DESCRIPCION = ("Serum facial con vitamina C al 20% y acido hialuronico, frasco de 30 ml con gotero. "
               "Uso: 3 gotas por la noche sobre rostro limpio. Registro MSPAS en tramite. "
               "Proveedor local con entrega en 48 horas y garantia de 30 dias contra defectos.")


def _p(slug, nombre):
    """Ruta relativa de un archivo de producto del fixture (armada por partes: no es una ruta del repo)."""
    return "/".join(("PRODUCTOS", slug, nombre))


def _fila_producto(**campos):
    base = {c: "" for c in COLUMNAS_PRODUCTOS}
    base["mercado"] = "GT"  # el mercado es obligatorio: los productos del fixture venden en Guatemala
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
    """El producto REAL de un alta (hecho por alta_producto.py, no a mano) + otros que ya tienen paquete."""
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    os.makedirs(os.path.join(base, "Ads"))
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), COLUMNAS_PRODUCTOS, [
        _fila_producto(producto_key="OTRO", slug_carpeta="OTRO", estado="VIVO", costo_q="50",
                       cpa_be_q="92.64", notas="una, con coma"),
        _fila_producto(producto_key="CON_COSTEO", slug_carpeta="CON_COSTEO", estado="NUEVO",
                       costo_q="60", cpa_be_q="80.10"),
        _fila_producto(producto_key="CON_MANUAL", slug_carpeta="CON_MANUAL", estado="NUEVO", costo_q="60"),
        _fila_producto(producto_key="CON_ENCABEZADO", slug_carpeta="CON_ENCABEZADO", estado="NUEVO", costo_q="60"),
    ])
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv"), COLUMNAS_ENVASE, [])
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_MERCADOS.csv"),
                  ["mercado", "pais", "moneda", "simbolo", "persona", "registro_sanitario"],
                  [["GT", "Guatemala", "GTQ", "Q", "voseo", "registro MSPAS"]])
    imagen = os.path.join(base, "foto.png")
    with io.open(imagen, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    descripcion = os.path.join(base, "desc.txt")
    with io.open(descripcion, "w", encoding="utf-8") as fh:
        fh.write(DESCRIPCION)

    # P3 T4 continuación parte 2: raw.producto (tenant único, nunca `vitalcom` real) tiene que
    # estar sincronizado con el CSV de arriba ANTES del primer alta real.
    tenant = _tenant_unico()
    alta_producto.TENANT_ID = tenant
    cambiar_costo.ep.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(base, "PRODUCTOS"), tenant)

    codigo = alta_producto.main(["--nombre", "Serum Vitamina C", "--costo", "60",
                                 "--descripcion-archivo", descripcion, "--imagen", imagen,
                                 "--base", base, "--hoy", "2026-09-17", "--mercado", "GT",
                                 "--moneda", "GTQ"])
    assert codigo == 0, "el fixture necesita un alta real"
    _escribir(base, _p("CON_MANUAL", "1_HACER_MANUAL.txt"), "TODO A MANO\r\n")
    _escribir(base, _p("CON_ENCABEZADO", "2_DATA_PRODUCTO.txt"),
              "═══ X · VERSION v1 · 2026-09-17 · COSTO Q60 · DOSIS 3 · page_id PENDIENTE ═══\r\n")


def _fila(base, clave):
    filas = list(csv.reader(io.StringIO(_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), newline="")))
    return dict(zip(filas[0], next(f for f in filas[1:] if f and f[0] == clave)))


def _correr(base, producto, costo, *extra):
    return cambiar_costo.main(["--producto", producto, "--costo", costo, "--base", base, *extra])


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
    if not DB_DISPONIBLE:
        print("GATE DEL CAMBIO DE COSTO")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="costo_test_")
    datos = _p("SERUM_VITAMINA_C", "2_DATA_PRODUCTO.txt")
    try:
        _fixture(base)

        def cambia_el_csv_y_la_linea_del_alta():
            antes = _leer(base, datos)
            assert "costo del pedido . Q60" in antes, "el fixture tiene que traer la linea del alta"
            assert _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "52.50"))[0] == 0
            assert _fila(base, "SERUM_VITAMINA_C")["costo_q"] == "52.50"
            assert _leer(base, datos) == antes.replace("costo del pedido . Q60", "costo del pedido . Q52.50", 1), \
                "del TXT solo cambia la linea del costo"

        def no_escribe_cifras_de_costeo():
            fila = _fila(base, "SERUM_VITAMINA_C")
            for columna in ("fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q", "fase"):
                assert fila[columna] == "", (f"{columna} lo calcula costear.py y lo escribe "
                                              f"etapa-guardar-producto; llego «{fila[columna]}»")

        def solo_toca_la_fila_del_producto():
            assert _fila(base, "OTRO")["notas"] == "una, con coma"
            assert _fila(base, "OTRO")["costo_q"] == "50"

        def acepta_la_coma_decimal():
            assert _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "48,5"))[0] == 0
            assert _fila(base, "SERUM_VITAMINA_C")["costo_q"] == "48.5"

        def rechaza_costos_que_no_son_numero_positivo():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            for malo in ("sesenta", "0", "-5", "", "12.", "1,2,3", "Q60"):
                assert _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", malo))[0] == 1, repr(malo)
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def bloquea_si_el_paquete_tiene_cifras_de_costeo():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(lambda: _correr(base, "CON_COSTEO", "70", "--json"))
            assert codigo == 1 and "invariante 5" in json.loads(salida)["detalle"], salida
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def bloquea_si_ya_existe_1_hacer_manual():
            assert _en_silencio(lambda: _correr(base, "CON_MANUAL", "70"))[0] == 1
            assert _fila(base, "CON_MANUAL")["costo_q"] == "60"

        def bloquea_si_el_2_data_ya_trae_encabezado_de_paquete():
            assert _en_silencio(lambda: _correr(base, "CON_ENCABEZADO", "70"))[0] == 1
            assert _fila(base, "CON_ENCABEZADO")["costo_q"] == "60"

        def bloquea_un_producto_ya_vivo_con_costeo():
            assert _en_silencio(lambda: _correr(base, "OTRO", "70"))[0] == 1

        def rechaza_producto_sin_fila():
            assert _en_silencio(lambda: _correr(base, "NO_EXISTE", "70"))[0] == 1

        def volver_a_correr_no_cambia_nada():
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos))
            codigo, salida = _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "48.50", "--json"))
            resultado = json.loads(salida)
            assert codigo == 0 and resultado["sin_cambios"] is True and resultado["aplicado"] is False, resultado
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos))

        def dry_run_no_toca_nada():
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos))
            codigo, salida = _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "99", "--dry-run", "--json"))
            assert codigo == 0 and json.loads(salida)["aplicado"] is False
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos))

        def una_falla_ANTES_de_postgres_deja_todo_como_estaba():
            """P3 T4 continuación parte 2: si el TXT no se puede STAGEAR (fase 1, antes de tocar
            Postgres), nada cambia -- ni el CSV (Postgres nunca se toca) ni el TXT."""
            antes = (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos))
            ruta_datos_abs = os.path.join(base, *datos.split("/"))
            ruta_tmp = ruta_datos_abs + ".tmp"
            os.makedirs(ruta_tmp)  # una carpeta en el lugar del .tmp: escribirlo ahi falla siempre
            try:
                try:
                    _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "77"))
                    raise AssertionError("tenia que fallar")
                except OSError:
                    pass
            finally:
                os.rmdir(ruta_tmp)
            assert antes == (_leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv"), _leer(base, datos)), \
                "el CSV y el TXT tienen que quedar como estaban"

        def una_falla_DESPUES_de_postgres_es_recuperable():
            """P3 T4 continuación parte 2: si Postgres YA comiteó el nuevo costo y el
            os.replace() final del TXT falla, NO se deshace (el CSV mirror YA trae el costo
            nuevo): sale con exit 1 y deja el .tmp del TXT para terminar a mano."""
            datos_antes = _leer(base, datos)
            original = cambiar_costo.ep.os.replace

            def replace_que_falla_para_el_resto(origen, destino):
                # Filtra por el sufijo ".tmp" de editar_producto.py (nunca el ".tmp-escribir" de
                # db/escribir.py, que corre ANTES, dentro del commit).
                if str(origen).endswith(".tmp"):
                    raise OSError("disco lleno (simulado)")
                return original(origen, destino)

            cambiar_costo.ep.os.replace = replace_que_falla_para_el_resto
            try:
                codigo, salida = _en_silencio(lambda: _correr(base, "SERUM_VITAMINA_C", "81", "--json"))
            finally:
                cambiar_costo.ep.os.replace = original
            assert codigo == 1, salida
            assert "Postgres ya qued" in json.loads(salida)["detalle"], salida
            assert _fila(base, "SERUM_VITAMINA_C")["costo_q"] == "81", \
                "Postgres (y su espejo) SI tenian que quedar con el costo nuevo"
            assert _leer(base, datos) == datos_antes, \
                "el TXT NO se reemplazo (se quedo con el costo de la corrida anterior)"
            tmp_restantes = [os.path.join(r, n) for r, _, fs in os.walk(base) for n in fs
                              if n.endswith(".tmp")]
            assert tmp_restantes, "tiene que quedar el .tmp del TXT para terminar a mano"
            for ruta_tmp in tmp_restantes:
                os.remove(ruta_tmp)

        print("GATE DEL CAMBIO DE COSTO")
        for nombre, funcion in (
            ("cambia el CSV y la linea del alta, nada mas", cambia_el_csv_y_la_linea_del_alta),
            ("no escribe precio, CPA ni break-even", no_escribe_cifras_de_costeo),
            ("solo toca la fila del producto", solo_toca_la_fila_del_producto),
            ("acepta la coma decimal", acepta_la_coma_decimal),
            ("rechaza un costo que no es numero positivo", rechaza_costos_que_no_son_numero_positivo),
            ("bloquea si la fila ya tiene cifras de costeo", bloquea_si_el_paquete_tiene_cifras_de_costeo),
            ("bloquea si ya existe 1_HACER_MANUAL.txt", bloquea_si_ya_existe_1_hacer_manual),
            ("bloquea si el 2_DATA ya trae encabezado de paquete", bloquea_si_el_2_data_ya_trae_encabezado_de_paquete),
            ("bloquea un producto VIVO con costeo", bloquea_un_producto_ya_vivo_con_costeo),
            ("rechaza un producto sin fila", rechaza_producto_sin_fila),
            ("volver a correr no cambia nada", volver_a_correr_no_cambia_nada),
            ("--dry-run no toca el disco", dry_run_no_toca_nada),
            ("una falla ANTES de Postgres deja todo como estaba", una_falla_ANTES_de_postgres_deja_todo_como_estaba),
            ("una falla DESPUES de Postgres es recuperable, no se deshace", una_falla_DESPUES_de_postgres_es_recuperable),
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
