#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exportar.py — Postgres -> CSV (P1-cimientos T5/T6/T5b).

Dos exportadores, para dos propósitos distintos:

  - `exportar_raw_todo()`  — reconstruye TODOS los CSV de PRODUCTOS/ desde el espejo verbatim
    `raw.*` (T5). Sirve para auditoría/staging: columna por columna, byte por byte salvo el orden
    de escritura de csv.writer, es el mismo archivo. NO es lo que usa el gate de paridad desde
    T5b.

  - `exportar_core_decidir()` — reconstruye SOLO las 9 CSV que `Ads/_TOOLS/decidir.py` (vía
    `gasto.py`/`alias.py`) lee directamente, desde el modelo NORMALIZADO `core.*` (T5b). Es la que
    usa el gate de paridad (T6): si `decidir.py` corre igual sobre esto que sobre el repo real,
    `core` sostiene lo que el motor de decisión necesita — no solo el round-trip de `raw`.

USO:
    "<venv>/python.exe" db/exportar.py --out DIR                  # exporta raw -> CSV completos
    "<venv>/python.exe" db/exportar.py --out DIR --modo core      # exporta core -> los 9 CSV de decidir.py
"""
import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402
from cargar import cargar_env, conectar  # noqa: E402


def _v(x):
    """None -> "" (nunca la palabra "None"); todo lo demás, str() tal cual (fechas ISO,
    Decimal sin exponente, texto verbatim)."""
    return "" if x is None else str(x)


def _escribir_csv(out_path, header, filas):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for fila in filas:
            w.writerow([_v(v) for v in fila])
    return len(filas)


# ── exportador RAW (T5, audit/staging — espejo verbatim completo) ──────────────────────────────

def exportar_tabla_raw(cur, tenant_id, tabla, archivo, opcional, out_dir):
    """Reconstruye el CSV original desde `raw.<tabla>`: header con los nombres CSV reales,
    valores leídos de las columnas SQL (pueden estar renombradas — ver tables.COLUMN_RENAMES)."""
    pares = T.columnas_csv_y_sql(tabla, archivo, opcional)
    out_path = os.path.join(out_dir, archivo)
    if not pares:
        # Tabla opcional sin CSV fuente (hoy: voz_cliente): no se puede reconstruir un header
        # que nunca existió. No se escribe archivo — igual que hoy no existe en PRODUCTOS/.
        return 0

    header_csv = [csv_col for csv_col, _ in pares]
    header_sql = [sql_col for _, sql_col in pares]
    col_list = ", ".join(['"%s"' % c for c in header_sql])
    cur.execute(
        "SELECT %s FROM raw.%s WHERE tenant_id = %%s ORDER BY id" % (col_list, tabla),
        (tenant_id,),
    )
    return _escribir_csv(out_path, header_csv, cur.fetchall())


def exportar_raw_todo(out_dir, decisiones_json=None, tenant_id="vitalcom", env=None):
    """Exporta TODAS las tablas espejo de `raw` a `out_dir` (misma estructura plana que
    PRODUCTOS/). Devuelve {tabla: n_filas}. `_DECISIONES.json` se reconstruye desde `core.decision`
    (no tiene CSV/tabla `raw` propia: nunca vino de un CSV)."""
    os.makedirs(out_dir, exist_ok=True)
    conteos = {}
    con = conectar(env)
    try:
        with con.cursor() as cur:
            for tabla, archivo, opcional in T.TABLE_SPECS:
                conteos[tabla] = exportar_tabla_raw(cur, tenant_id, tabla, archivo, opcional, out_dir)
            decisiones_json = decisiones_json or os.path.join(out_dir, "_DECISIONES.json")
            conteos["decision"] = 1 if exportar_decision(cur, tenant_id, decisiones_json) else 0
    finally:
        con.close()
    return conteos


def exportar_decision(cur, tenant_id, out_path):
    cur.execute(
        "SELECT payload FROM core.decision WHERE tenant_id = %s ORDER BY id DESC LIMIT 1",
        (tenant_id,),
    )
    r = cur.fetchone()
    if not r:
        return False
    payload = r[0]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return True


# ── exportador CORE (T5b — solo lo que decidir.py lee, reconstruido desde el modelo normalizado) ─

# {archivo: (header_csv_original, sql_select)} — un SELECT por archivo, columnas en el MISMO
# orden que el header (para que decidir.py, que lee por csv.DictReader, vea las mismas claves).
_CORE_DECIDIR_SPECS = {
    "_PARAMETROS_DECISION.csv": (
        ["parametro", "valor", "unidad", "dueno", "por_que"],
        "SELECT parametro, valor, unidad, dueno, por_que "
        "FROM core.parametro_decision WHERE tenant_id = %s ORDER BY id",
    ),
    "_DIM_PRODUCTOS.csv": (
        ["producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
         "cuenta_id", "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q",
         "cpa_base_q", "cpa_be_q", "cpa_be_anterior_q", "notas", "carpeta_videos",
         "carpeta_transcripciones", "carpeta_media", "carpetas_extra", "clave_campana",
         "campaign_id"],
        "SELECT producto_key, nombre_display, slug_carpeta, estado, fase, cuenta_alias, "
        "cuenta_id_meta, page_id, moneda, tasa, costo_q, fila_costeo_q, precio_base_q, "
        "cpa_base_q, cpa_be_q, cpa_be_anterior_q, notas, carpeta_videos, "
        "carpeta_transcripciones, carpeta_media, carpetas_extra, clave_campana, campaign_id "
        "FROM core.producto WHERE tenant_id = %s ORDER BY id",
    ),
    "_DIM_CONJUNTOS.csv": (
        ["producto_key", "conjunto_meta", "cuenta_alias", "campana_clave", "fase", "angulo_key",
         "angulo_nombre", "avatar", "dolor_nucleo", "emocion_dominante", "avatar_edad",
         "avatar_genero", "formato", "concepto_key", "tipo_hook", "nivel_conciencia",
         "rol_embudo", "rol_embudo_origen", "lleva_precio", "creativo_id", "origen_angulo",
         "estado", "verificado_en_csv", "fecha_alta", "notas"],
        "SELECT producto_key, conjunto_meta, cuenta_alias, campana_clave, fase, angulo_key, "
        "angulo_nombre, avatar, dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero, "
        "formato, concepto_key, tipo_hook, nivel_conciencia, rol_embudo, rol_embudo_origen, "
        "lleva_precio, creativo_id, origen_angulo, estado, verificado_en_csv, fecha_alta, notas "
        "FROM core.conjunto WHERE tenant_id = %s ORDER BY id",
    ),
    "_DIM_BANDAS.csv": (
        ["cuenta_alias", "conjunto_meta", "producto_key", "angulo_key", "banda_configurada",
         "avatar_edad_doctrina", "coincide", "desde", "hasta", "fuente", "notas"],
        "SELECT cuenta_alias, conjunto_meta, producto_key, angulo_key, banda_configurada, "
        "avatar_edad_doctrina, coincide, desde, hasta, fuente, notas "
        "FROM core.banda WHERE tenant_id = %s ORDER BY id",
    ),
    "_ALIAS_CONJUNTOS.csv": (
        ["nombre_viejo", "nombre_nuevo", "cuenta_alias", "producto_key", "desde", "motivo"],
        "SELECT alias_nombre, nombre_canonico, cuenta_alias, producto_key, valid_from, motivo "
        "FROM core.conjunto_nombre_hist WHERE tenant_id = %s ORDER BY id",
    ),
    "_FACT_VENTAS.csv": (
        ["ventana_ini", "ventana_fin", "dias", "rol_ventana", "producto_key", "producto",
         "cuenta_id", "cuenta_alias", "campana", "conjunto", "anuncio", "mensajes", "clicks",
         "impresiones", "spend_usd", "ventas", "total_q", "moneda_origen", "fuente", "ad_id"],
        # ad_id: SIEMPRE la columna original verbatim, NUNCA ad_id_resuelto (ver nucleo.py).
        "SELECT ventana_ini, ventana_fin, dias, rol_ventana, producto_key, producto_nombre, "
        "cuenta_id_meta, cuenta_alias, campana, conjunto_nombre, anuncio_nombre, mensajes, "
        "clicks, impresiones, spend_usd, ventas, total_q, moneda_origen, fuente, ad_id "
        "FROM core.venta WHERE tenant_id = %s ORDER BY id",
    ),
    "_FACT_ENTREGA.csv": (
        ["ventana_ini", "ventana_fin", "dias", "producto_key", "cuenta_id", "cuenta_alias",
         "campana", "conjunto", "mensajes", "clicks_totales", "link_clicks", "impresiones",
         "spend_usd", "pct_conv_clic_enlace", "fuente"],
        "SELECT ventana_ini, ventana_fin, dias, producto_key, cuenta_id_meta, cuenta_alias, "
        "campana, conjunto_nombre, mensajes, clicks_totales, link_clicks, impresiones, "
        "spend_usd, pct_conv_clic_enlace, fuente "
        "FROM core.entrega_conjunto_dia WHERE tenant_id = %s ORDER BY id",
    ),
    "_FACT_ENTREGA_ANUNCIO.csv": (
        ["ventana_ini", "ventana_fin", "dias", "producto_key", "cuenta_id", "cuenta_alias",
         "campana", "conjunto", "anuncio", "ad_id", "firma", "angulo_key", "concepto_key",
         "canonico_id", "nivel_conciencia", "oferta_key", "destino_key", "mensajes",
         "clicks_totales", "link_clicks", "impresiones", "spend_usd", "pct_conv_clic_enlace",
         "fuente"],
        "SELECT ventana_ini, ventana_fin, dias, producto_key, cuenta_id_meta, cuenta_alias, "
        "campana, conjunto_nombre, anuncio_nombre, ad_id, firma, angulo_key, concepto_key, "
        "canonico_id, nivel_conciencia, oferta_key, destino_key, mensajes, clicks_totales, "
        "link_clicks, impresiones, spend_usd, pct_conv_clic_enlace, fuente "
        "FROM core.entrega_anuncio_dia WHERE tenant_id = %s ORDER BY id",
    ),
    "_ESTADO_FLUJO.csv": (
        ["producto_key", "fase", "nodo_actual", "estado", "desde", "bloqueantes",
         "siguiente_ejecutor", "evaluado_el"],
        "SELECT producto_key, fase, nodo_actual, estado, desde, bloqueantes, "
        "siguiente_ejecutor, evaluado_el FROM core.estado_flujo WHERE tenant_id = %s ORDER BY id",
    ),
}


def exportar_core_decidir(out_dir, tenant_id="vitalcom", env=None):
    """Reconstruye, desde `core.*`, exactamente los 9 CSV que `Ads/_TOOLS/decidir.py` (y lo que
    importa: `gasto.py`, `alias.py`) lee directamente. Es lo que usa el gate de paridad (T6) desde
    T5b — NUNCA cae de vuelta a exportar desde `raw` si algo no resuelve: una diferencia acá es el
    hallazgo, no algo para enmascarar. Devuelve {archivo: n_filas}."""
    os.makedirs(out_dir, exist_ok=True)
    conteos = {}
    con = conectar(env)
    try:
        with con.cursor() as cur:
            for archivo, (header, sql) in _CORE_DECIDIR_SPECS.items():
                cur.execute(sql, (tenant_id,))
                conteos[archivo] = _escribir_csv(
                    os.path.join(out_dir, archivo), header, cur.fetchall())
    finally:
        con.close()
    return conteos


def main():
    ap = argparse.ArgumentParser(description="Exporta Postgres -> CSV (raw completo o core/decidir)")
    ap.add_argument("--out", required=True, help="directorio de salida")
    ap.add_argument("--modo", choices=["raw", "core"], default="raw")
    ap.add_argument("--decisiones-json", default=None)
    ap.add_argument("--tenant", default="vitalcom")
    args = ap.parse_args()

    if args.modo == "core":
        conteos = exportar_core_decidir(args.out, args.tenant)
    else:
        conteos = exportar_raw_todo(args.out, args.decisiones_json, args.tenant)
    total = sum(conteos.values())
    for tabla, n in sorted(conteos.items()):
        print("%-32s %6d" % (tabla, n))
    print("-" * 40)
    print("%-32s %6d" % ("TOTAL", total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
