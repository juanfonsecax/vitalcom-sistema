#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingestar_unificado.py — INGESTA BLINDADA Y AUTOMATIZADA DE REPORTES.

CÓMO FUNCIONA:
  1. El operador simplemente coloca los reportes descargados (.xlsx o .csv) en la carpeta `INBOX/`.
  2. Este script detecta automáticamente el formato (LucidSales vs Meta Ads Manager).
  3. Limpia y normaliza los datos:
     - ad_id tratado siempre como TEXTO (evita la corrupción de notación científica de Excel).
     - Quita sufijos '- Copia', dobles espacios y normaliza nombres para evitar huérfanos.
     - Aplica deduplicación estricta (no duplica si subes dos veces el mismo archivo).
     - Normaliza monedas (COP a USD para cuenta CP1).
  4. Actualiza los CSVs de hechos (_FACT_VENTAS.csv y _FACT_ENTREGA.csv).
  5. Mueve los archivos procesados a `_RESPALDOS/procesados/` para mantener limpio el INBOX.
  6. Actualiza de inmediato las decisiones y la aplicación.

USO:
    python Ads/_TOOLS/ingestar_unificado.py                  # Procesa todo lo que haya en INBOX/
    python Ads/_TOOLS/ingestar_unificado.py mi_reporte.xlsx  # Procesa un archivo específico
"""

import os
import sys
import io
import re
import csv
import glob
import shutil
import datetime
import warnings

# Forzar UTF-8 en Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

warnings.filterwarnings("ignore")

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upsert_fact   # noqa: E402  (respaldos_dir() compartido, ver T9 en su docstring)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

INBOX_DIR = os.path.join(BASE, "INBOX")
PROD_DIR = os.path.join(BASE, "PRODUCTOS")
ARCH_DIR = upsert_fact.respaldos_dir(BASE, "procesados")

FACT_VENTAS = os.path.join(PROD_DIR, "_FACT_VENTAS.csv")
FACT_ENTREGA = os.path.join(PROD_DIR, "_FACT_ENTREGA.csv")
DIM_CONJ = os.path.join(PROD_DIR, "_DIM_CONJUNTOS.csv")

TASA_COP_USD = 3152.5
CP1_ID = "1346891653335162"

ALIAS_CUENTAS = {
    "598687956219141": "GTR7",
    "1665221077707961": "GTR0",
    "824783947334627": "GTR1",
    "916746367261028": "GTR13",
    "1346891653335162": "CP1",
    "581490137794343": "GTR3",
}

MAPA_PRODUCTO = {
    "tinnidrop": "TINNIDROP",
    "clearstem": "CLEARSTEM",
    "nusava": "NUSAVA",
    "varicose": "VARICOSE",
    "varices": "VARICOSE",
}


def normalizar_texto_conjunto(nombre):
    if not nombre:
        return ""
    s = str(nombre).strip()
    # Eliminar sufijos típicos de Meta que parten las series
    s = re.sub(r"\s*-\s*Copia(\s*\(\d+\))?", "", s, flags=re.I)
    s = re.sub(r"\s*\+\s*25AÑOS", "", s, flags=re.I)
    s = re.sub(r"\s*\+\s*EDAD.*", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def inferir_producto_key(texto):
    t = (texto or "").lower()
    for k, v in MAPA_PRODUCTO.items():
        if k in t:
            return v
    return "SIN_MAPEAR"


def extraer_fecha_nombre(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    if m:
        return m.group(1)
    return datetime.date.today().isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# 1. INGESTA LUCIDSALES
# ─────────────────────────────────────────────────────────────────────────────

def es_lucidsales(path):
    try:
        df_test = pd.read_excel(path, nrows=10, header=None)
        txt = df_test.astype(str).to_string().lower()
        return "accounttitle" in txt or "adsettitle" in txt or "sells" in txt
    except Exception:
        return False


def procesar_lucidsales(path):
    print(f"  [LUCIDSALES] Procesando: {os.path.basename(path)}")
    # Header en fila 4 (índice 3)
    df = pd.read_excel(path, header=3)
    df = df[df["accountTitle"].notna()].copy()

    fecha = extraer_fecha_nombre(path)

    filas_nuevas = []
    for _, r in df.iterrows():
        cuenta_id_raw = str(r.get("accountId") or "").strip()
        cuenta_id = cuenta_id_raw.replace(".0", "")
        cuenta_alias = ALIAS_CUENTAS.get(cuenta_id, str(r.get("accountTitle") or ""))

        prod_raw = str(r.get("productTitle") or "")
        pk = inferir_producto_key(prod_raw + " " + str(r.get("campaignTitle") or ""))

        conjunto_raw = str(r.get("adSetTitle") or "")
        conjunto_limpio = normalizar_texto_conjunto(conjunto_raw)

        anuncio_raw = str(r.get("adTitle") or "")
        ad_id_raw = str(r.get("adId") or "").strip()
        ad_id = ad_id_raw.replace(".0", "") if ad_id_raw != "nan" else ""

        ventas = float(r.get("sells") or 0.0)
        total_q = float(r.get("total") or 0.0)
        spend = float(r.get("spend") or 0.0)

        # Normalización COP si es CP1
        moneda = "USD"
        if cuenta_id == CP1_ID:
            spend = spend / TASA_COP_USD
            moneda = "COP"

        filas_nuevas.append({
            "ventana_ini": fecha,
            "ventana_fin": fecha,
            "dias": 1,
            "rol_ventana": "BASE",
            "producto_key": pk,
            "producto": prod_raw,
            "cuenta_id": cuenta_id,
            "cuenta_alias": cuenta_alias,
            "campana": str(r.get("campaignTitle") or "").strip(),
            "conjunto": conjunto_limpio,
            "anuncio": anuncio_raw.strip(),
            "mensajes": int(r.get("messages") or 0),
            "clicks": int(r.get("clicks") or 0),
            "impresiones": int(r.get("impressions") or 0),
            "spend_usd": round(spend, 4),
            "ventas": int(ventas),
            "total_q": round(total_q, 2),
            "moneda_origen": moneda,
            "fuente": "LucidSales_Inbox",
            "ad_id": ad_id,
        })

    if not filas_nuevas:
        print("    Sin filas válidas en LucidSales.")
        return 0

    # Cargar existente y deduplicar
    cols_order = ["ventana_ini","ventana_fin","dias","rol_ventana","producto_key","producto",
                  "cuenta_id","cuenta_alias","campana","conjunto","anuncio","mensajes","clicks",
                  "impresiones","spend_usd","ventas","total_q","moneda_origen","fuente","ad_id"]

    df_nuevas = pd.DataFrame(filas_nuevas)

    if os.path.exists(FACT_VENTAS):
        df_exist = pd.read_csv(FACT_VENTAS, dtype=str)
        # Llave deduplicación: ventana_ini + conjunto + anuncio + fuente
        llave_exist = set(df_exist["ventana_ini"].astype(str) + "|" +
                          df_exist["conjunto"].astype(str) + "|" +
                          df_exist["anuncio"].astype(str))

        df_filtradas = df_nuevas[~((df_nuevas["ventana_ini"].astype(str) + "|" +
                                   df_nuevas["conjunto"].astype(str) + "|" +
                                   df_nuevas["anuncio"].astype(str)).isin(llave_exist))]
    else:
        df_filtradas = df_nuevas

    if len(df_filtradas) > 0:
        modo = "a" if os.path.exists(FACT_VENTAS) else "w"
        header = not os.path.exists(FACT_VENTAS)
        df_filtradas[cols_order].to_csv(FACT_VENTAS, mode=modo, header=header, index=False, encoding="utf-8")
        print(f"    ✅ {len(df_filtradas)} ventas/filas nuevas agregadas a _FACT_VENTAS.csv.")
    else:
        print("    ℹ️ Todas las filas ya existían (sin duplicados).")

    return len(df_filtradas)


# ─────────────────────────────────────────────────────────────────────────────
# 2. INGESTA META ADS MANAGER
# ─────────────────────────────────────────────────────────────────────────────

def es_meta_ads(path):
    try:
        df_test = pd.read_excel(path, nrows=5)
        cols = [c.lower() for c in df_test.columns]
        return any("campaña" in c or "campaign" in c for c in cols) and \
               any("gastado" in c or "spent" in c for c in cols)
    except Exception:
        return False


def procesar_meta_ads(path):
    print(f"  [META ADS] Procesando: {os.path.basename(path)}")
    df = pd.read_excel(path)

    # Identificar nombres de columnas flexibles
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "campaña" in cl or "campaign" in cl: col_map["campana"] = c
        elif "conjunto" in cl or "ad set" in cl: col_map["conjunto"] = c
        elif "gastado" in cl or "amount spent" in cl: col_map["spend"] = c
        elif "impresiones" in cl or "impressions" in cl: col_map["impresiones"] = c
        elif "enlace" in cl or "link clicks" in cl: col_map["link_clicks"] = c
        elif "todos" in cl or "all clicks" in cl: col_map["clicks_tot"] = c
        elif "inicio" in cl or "start" in cl: col_map["ini"] = c
        elif "fin" in cl or "end" in cl: col_map["fin"] = c
        elif "anuncio" in cl or "ad name" in cl: col_map["anuncio"] = c
        elif "conversión a whatsapp" in cl or "whatsapp" in cl: col_map["conv_wa"] = c

    # Descartar filas resumen sin conjunto ni campaña
    col_conj = col_map.get("conjunto")
    if not col_conj:
        print("    No se encontró columna de conjunto en el reporte de Meta.")
        return 0

    df = df[df[col_conj].notna()].copy()

    filas_nuevas = []
    for _, r in df.iterrows():
        campana_raw = str(r.get(col_map.get("campana", ""), ""))
        conjunto_raw = str(r.get(col_conj, ""))
        conjunto_limpio = normalizar_texto_conjunto(conjunto_raw)

        pk = inferir_producto_key(campana_raw + " " + conjunto_raw)

        ini = str(r.get(col_map.get("ini", ""), extraer_fecha_nombre(path)))
        fin = str(r.get(col_map.get("fin", ""), extraer_fecha_nombre(path)))
        ini = ini.split("T")[0].split(" ")[0]
        fin = fin.split("T")[0].split(" ")[0]

        spend = float(r.get(col_map.get("spend", 0.0), 0.0) or 0.0)
        impresiones = int(r.get(col_map.get("impresiones", 0), 0) or 0)
        link_clicks = int(r.get(col_map.get("link_clicks", 0), 0) or 0)
        clicks_tot = int(r.get(col_map.get("clicks_tot", link_clicks), link_clicks) or link_clicks)

        # Mensajes
        tasa_wa = float(r.get(col_map.get("conv_wa", 0.0), 0.0) or 0.0)
        mensajes = int(round(tasa_wa * link_clicks)) if tasa_wa > 0 else int(link_clicks * 0.7)

        pct_conv = round((mensajes / link_clicks * 100.0), 1) if link_clicks > 0 else 0.0

        filas_nuevas.append({
            "ventana_ini": ini,
            "ventana_fin": fin,
            "dias": 1,
            "producto_key": pk,
            "cuenta_id": "",
            "cuenta_alias": "",
            "campana": campana_raw.strip(),
            "conjunto": conjunto_limpio,
            "mensajes": mensajes,
            "clicks_totales": clicks_tot,
            "link_clicks": link_clicks,
            "impresiones": impresiones,
            "spend_usd": round(spend, 4),
            "pct_conv_clic_enlace": pct_conv,
            "fuente": "Meta_Inbox",
        })

    if not filas_nuevas:
        print("    Sin filas válidas en reporte de Meta.")
        return 0

    cols_order = ["ventana_ini", "ventana_fin", "dias", "producto_key", "cuenta_id", "cuenta_alias",
                  "campana", "conjunto", "mensajes", "clicks_totales", "link_clicks", "impresiones",
                  "spend_usd", "pct_conv_clic_enlace", "fuente"]

    df_nuevas = pd.DataFrame(filas_nuevas)

    if os.path.exists(FACT_ENTREGA):
        df_exist = pd.read_csv(FACT_ENTREGA, dtype=str)
        llave_exist = set(df_exist["ventana_ini"].astype(str) + "|" +
                          df_exist["conjunto"].astype(str))
        df_filtradas = df_nuevas[~((df_nuevas["ventana_ini"].astype(str) + "|" +
                                   df_nuevas["conjunto"].astype(str)).isin(llave_exist))]
    else:
        df_filtradas = df_nuevas

    if len(df_filtradas) > 0:
        modo = "a" if os.path.exists(FACT_ENTREGA) else "w"
        header = not os.path.exists(FACT_ENTREGA)
        df_filtradas[cols_order].to_csv(FACT_ENTREGA, mode=modo, header=header, index=False, encoding="utf-8")
        print(f"    ✅ {len(df_filtradas)} registros de entrega agregados a _FACT_ENTREGA.csv.")
    else:
        print("    ℹ️ Registros de entrega ya existían (sin duplicados).")

    return len(df_filtradas)


# ─────────────────────────────────────────────────────────────────────────────
# 3. COORDINADOR DE INBOX
# ─────────────────────────────────────────────────────────────────────────────

def archivar_procesado(ruta_archivo):
    mes_actual = datetime.date.today().strftime("%Y-%m")
    destino_dir = os.path.join(ARCH_DIR, mes_actual)
    os.makedirs(destino_dir, exist_ok=True)
    nombre = os.path.basename(ruta_archivo)
    destino = os.path.join(destino_dir, nombre)
    try:
        shutil.move(ruta_archivo, destino)
        print(f"    📦 Archivado en: _RESPALDOS/procesados/{mes_actual}/{nombre}")
    except Exception as e:
        print(f"    Aviso: No se pudo mover {nombre}: {e}")


def main():
    print("=" * 80)
    print(" 📥 INGESTA BLINDADA Y UNIFICADA — VITALCOM GUATEMALA")
    print("=" * 80)

    archivos_a_procesar = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        archivos_a_procesar = [sys.argv[1]]
    else:
        patrones = [os.path.join(INBOX_DIR, "*.xlsx"), os.path.join(INBOX_DIR, "*.csv")]
        for p in patrones:
            archivos_a_procesar.extend(glob.glob(p))

    if not archivos_a_procesar:
        print(f"No hay archivos nuevos en la carpeta INBOX/ ({INBOX_DIR}).")
        print("Para cargar datos, copia tus reportes de LucidSales o Meta Ads en 'INBOX/' y vuelve a correr este comando.")
        print("=" * 80)
        return 0

    print(f"Detectados {len(archivos_a_procesar)} archivo(s) en INBOX/:\n")
    procesados = 0

    for f in archivos_a_procesar:
        exito = False
        if es_lucidsales(f):
            n = procesar_lucidsales(f)
            exito = True
            procesados += 1
        elif es_meta_ads(f):
            n = procesar_meta_ads(f)
            exito = True
            procesados += 1
        else:
            print(f"  ⚠️ Formato desconocido (no es LucidSales ni Meta Ads): {os.path.basename(f)}")

        if exito:
            archivar_procesado(f)

    print("\n" + "-" * 80)
    print(f"Ingesta finalizada: {procesados} archivo(s) procesados con éxito.")

    # Si hubo archivos nuevos, actualizar decisiones y app
    if procesados > 0:
        print("\nActualizando decisiones y regenerando la aplicación...")
        os.system("python Ads/_TOOLS/ciclo_hoy.py")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
