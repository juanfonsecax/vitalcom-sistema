#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decidir.py — MOTOR DE DECISIÓN UNIFICADO (VITALCOM GUATEMALA).

SÍNTESIS DOCTRINARIA Y OPERATIVA:
Combina el rigor estadístico de los Intervalos de Credibilidad Bayesiana (IC 95%)
con la Gestión de Riesgo Asimétrico (Bankroll, Tolerancia 1x BE y Detector Temprano de Fatiga).

PRINCIPIOS:
  1. TRES RELOJES DISTINTOS, NUNCA UNO SOLO (_PARAMETROS_DECISION.csv):
       - ventana_dias (14)              -> sobre cuántos días se calcula CPA e IC.
       - ventana_fatiga_dias (3)        -> días recientes que se comparan CONTRA esa ventana.
       - duracion_testeo_fase2_dias (3) -> cuánto rueda la 1-1-5 antes de coronar (Calet 22-ago).
       - tolerancia_base = acumulado    -> la regla 1x BE se mide sobre el gasto DESDE EL LANZAMIENTO.
     Los 3 días de Calet son una DURACIÓN DE CAMPAÑA, no una ventana de cálculo: él decide en 3 días
     porque corre a $15-18 USD/día y esos 3 días le traen 20-30 ventas. A $3-6 USD/día traen 1-3.
     Lo que Calet fija es VOLUMEN DE EVIDENCIA, no tiempo. La ventana es fija y no se corta después
     de ver el dato, para evitar p-hacking.
  2. AGREGACIÓN POR ANGULO_KEY (Invariante 1 y 12): Las réplicas R[N] se SUMAN.
  3. CERO PARÁLISIS OPERATIVA:
     Si el intervalo cruza el Break-Even por escasez de muestra o cercanía al BE,
     el sistema NO se congela en parálisis: emite la acción de menor riesgo
     (MANTENER PRESUPUESTO / SEGUIR MIDIENDO) y calcula cuántas ventas faltan
     para resolver la incertidumbre al CPA observado.
  4. BLOQUEO DE ACCIONES IRREVERSIBLES:
     Las decisiones irreversibles (apagar definitivamente un ángulo o escalar fuerte)
     requieren evidencia rigurosa o transgresión de tolerancia máxima (1x BE sin ventas).
  5. DETECTOR TEMPRANO DE FATIGA:
     Si un ángulo con historia rentable decae en los últimos `ventana_fatiga_dias`, la
     acción es RENOVAR el concepto en Fase 2, NUNCA apagar el ángulo. La guarda
     `ganador_historico` hace que esta regla gane sobre PAUSAR, que se evalúa antes.

ESTADOS:
  [ESCALAR]         CPA bajo objetivo o bajo BE con respaldo -> Subir +surfing_pct (una vez, en la mañana)
  [PAUSAR]          Gasto ACUMULADO sin chats · conversación por clic-enlace floja con 0 ventas ·
                    tolerancia acumulada de 1x BE agotada (tras la maduración COD) · CPA desbordado
  [RENOVAR]         Ganador de la ventana con fatiga en los últimos días recientes (Brief Fase 2)
  [SEGUIR_MIDIENDO] Cruza BE en zona de prueba/maduración (Acción: Mantener presupuesto). También
                    PAUSAR_DIFERIDA: una pausa que excede max_pausas_por_dia y espera a mañana.

REGLAMENTO ÚNICO (09-sep-2026):
  Hasta esa fecha el 35 % de conversación por clic-enlace, el presupuesto de decisión con sus ~3
  días COD, el máximo de 2 pausas por día y el +20 % de surfing vivían SOLO en prosa (ETAPA-7.md,
  ESCALADO_PLAYBOOK.md) y este motor no los conocía: dos reglamentos. Hoy todos son filas de
  _PARAMETROS_DECISION.csv, este motor los ejecuta y verificar_guia_madre.py los vigila. ETAPA-7
  consume _DECISIONES.json; no recalcula nada.

USO:
    python Ads/_TOOLS/decidir.py                      # Portafolio completo, SOLO LECTURA
    python Ads/_TOOLS/decidir.py CLEARSTEM            # Un solo producto
    python Ads/_TOOLS/decidir.py --grano conjunto     # Desglose por conjunto
    python Ads/_TOOLS/decidir.py --dias 7             # Ventana de evaluacion personalizada
    python Ads/_TOOLS/decidir.py --json               # Salida JSON por stdout
    python Ads/_TOOLS/decidir.py --escribir           # Ademas, guarda _DECISIONES.json

Contrato de CLI (T6, parejo con flujo.py y gen_grafo.py): un "mirar" nunca
escribe. Por defecto este comando calcula e imprime (consola o `--json`) sin
tocar disco. `--escribir` es el unico flag que persiste `_DECISIONES.json`; lo
usa la cadena nocturna (`gen_decisiones.py`) y ningun otro caller: `flujo.py`,
`perfilar_angulos.py` y `backtest_politica.py` llaman a `analizar_portafolio()`
como función de Python, nunca a este `main()`, así que nunca escriben.
"""

import os
import sys
import io
import csv
import json
import argparse
import datetime
import math
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from scipy.stats import gamma as _gamma, fisher_exact

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alias import mapa_de as _alias_de  # noqa: E402
import gasto as _gasto  # noqa: E402 -- fuente unica del spend_usd (g07-cimientos T2)
import mercado  # noqa: E402 -- moneda del mercado para presentar montos

# Cobertura de la ultima corrida de cargar_datos_duckdb(): {fuente_gasto: n_celdas}, una celda =
# una llave (producto,cuenta,ventana,conjunto), no una fila de venta original. La lee
# analizar_portafolio() para reportarla en el JSON (ver gasto.py: nunca se debe usar el
# spend_usd de _FACT_VENTAS.csv sin decir de donde salio de verdad).
COBERTURA_GASTO = {}

# DECIDIR_PROD_DIR (P1-cimientos T6, 23-sep-2026): override MÍNIMO y retro-compatible del
# directorio PRODUCTOS/ que lee este módulo. Sin variable de entorno, el comportamiento es
# EXACTAMENTE el de siempre (BASE/PRODUCTOS del repo real). flujo.py ya monkey-parchea estas
# mismas constantes de módulo para correr el motor sobre un fixture (ver Entorno.motor()); esta
# variable existe para el caso donde no hay un proceso Python vivo para monkey-parchear —
# el gate de paridad de db/test_db.py corre decidir.py en un subproceso aparte (con scipy y
# duckdb, que no viven en el venv de psycopg) y necesita apuntarlo a una base exportada.
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.environ.get("DECIDIR_PROD_DIR") or os.path.join(BASE, "PRODUCTOS")
DB_PATH = os.path.join(BASE, "warehouse", "vitalcom.duckdb")
PARAMS_PATH = os.path.join(PROD, "_PARAMETROS_DECISION.csv")
DIM_PROD_PATH = os.path.join(PROD, "_DIM_PRODUCTOS.csv")
DIM_CONJ_PATH = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
DIM_BANDAS_PATH = os.path.join(PROD, "_DIM_BANDAS.csv")
ALIAS_PATH = os.path.join(PROD, "_ALIAS_CONJUNTOS.csv")
FACT_VENTAS_PATH = os.path.join(PROD, "_FACT_VENTAS.csv")
FACT_ENTREGA_PATH = os.path.join(PROD, "_FACT_ENTREGA.csv")
FACT_ENTREGA_ANUNCIO_PATH = os.path.join(PROD, "_FACT_ENTREGA_ANUNCIO.csv")  # link_clicks: la conversacion por clic-ENLACE vive aca
# La FASE VIGENTE de cada producto. Derivada por flujo.py, nunca escrita a mano (CLAUDE.md:
# _DIM_PRODUCTOS.fase quedo como bitacora). Se lee como CSV, no importando flujo.py: flujo.py
# ya importa este modulo y hacerlo al reves cerraria el ciclo.
ESTADO_FLUJO_PATH = os.path.join(PROD, "_ESTADO_FLUJO.csv")
SALIDA_JSON = os.path.join(PROD, "_DECISIONES.json")
# No hay SALIDA_HTML: este motor escribe JSON y nada mas. Lo dibuja VISTAS/APP.html.

# P3 T4: `--escribir` ahora escribe PRIMERO en Postgres (`raw.decisiones_json`, vía
# `db/escribir.reemplazar_decision()`) y regenera `_DECISIONES.json` como ESPEJO recién después
# del commit -- nunca al revés (ver db/escribir.py, punto 4 de su docstring). TENANT_ID es el
# único punto de override para pruebas aisladas (mismo patrón que registrar_evento.py/
# ingerir_lucidsales.py) -- nunca toca `vitalcom` real desde una prueba. El import de `db/` es
# LOCAL a `main()` (nunca al tope del módulo): el gate de paridad (`db/test_db.py`) corre este
# archivo en un subproceso con scipy+duckdb que NO tiene psycopg, y ese camino nunca pasa por
# `--escribir` -- mantenerlo así evita que decidir.py deje de ser importable ahí.
# DECIDIR_TENANT_ID (P3 T5): mismo override, pero por VARIABLE DE ENTORNO -- una prueba que
# monkey-parcha `decidir.TENANT_ID` en proceso (test_cli_solo_lectura.py) no alcanza a un
# subproceso (el gate de paridad de db/test_db.py corre este archivo en uno aparte, con
# scipy+duckdb); sin esto, la lectura en modo "db" (ver _activar_fuente_db_si_corresponde) de un
# subproceso siempre caería sobre el tenant real "vitalcom". Default idéntico a siempre.
TENANT_ID = os.environ.get("DECIDIR_TENANT_ID") or "vitalcom"

# P3 T5: `VITALCOM_FUENTE` decide de dónde LEE este motor las 5 tablas DB-truth que ya escribe
# Postgres (`tables.TABLAS_MIGRADAS_DB`: producto/estado_flujo/venta/entrega_conjunto_dia/
# entrega_anuncio_dia) -- "db" (default) o "csv". El resto de PRODUCTOS/ (dimensiones editadas a
# mano: _DIM_CONJUNTOS, _DIM_BANDAS, _ALIAS_CONJUNTOS, _PARAMETROS_DECISION) NUNCA pasa por acá:
# sigue viniendo del CSV real, tal como hoy. `DECIDIR_PROD_DIR` (T6, fixtures/gate de paridad)
# sigue ganando SIEMPRE: si alguien ya redirigió `PROD` a mano (la variable de entorno, o el
# monkeypatch de módulo que hace `flujo.py:Entorno.motor()` sobre un fixture), este motor nunca
# se mete a buscar Postgres -- leería una base que no tiene nada que ver con el fixture. Por eso
# `analizar_portafolio()` compara `PROD` contra la ruta real ANTES de activar el modo DB: si ya
# no coincide, alguien más decidió de dónde se lee y este motor lo respeta tal cual.
# NUNCA cae de vuelta a CSV en silencio si Postgres no responde en modo "db": revienta con un
# mensaje claro (mismo criterio que `--escribir`, ver el comentario de arriba).
FUENTE_DB_ENV = "VITALCOM_FUENTE"
TABLAS_FUENTE_DB = ("producto", "estado_flujo", "venta", "entrega_conjunto_dia",
                     "entrega_anuncio_dia")
_FUENTE_DB_ACTIVADA = False
_TMP_FUENTE_DB = None  # referencia viva del TemporaryDirectory -- se borra solo al salir del proceso


def _fuente_efectiva():
    return (os.environ.get(FUENTE_DB_ENV) or "db").strip().lower()


def _activar_fuente_db_si_corresponde():
    """Si `VITALCOM_FUENTE` (o su default) pide "db" y nadie redirigió `PROD` a mano todavía,
    materializa las 5 tablas DB-truth desde Postgres a un directorio temporal y rebinda SOLO esas
    5 rutas de módulo -- el resto (`PARAMS_PATH`, `DIM_CONJ_PATH`, `DIM_BANDAS_PATH`,
    `ALIAS_PATH`) sigue leyendo el CSV real de `PROD`, sin tocar. Se corre una sola vez por
    proceso (`_FUENTE_DB_ACTIVADA`); `analizar_portafolio()` la llama al principio."""
    global _FUENTE_DB_ACTIVADA, _TMP_FUENTE_DB
    global DIM_PROD_PATH, ESTADO_FLUJO_PATH, FACT_VENTAS_PATH, FACT_ENTREGA_PATH
    global FACT_ENTREGA_ANUNCIO_PATH
    if _FUENTE_DB_ACTIVADA:
        return
    if _fuente_efectiva() == "csv":
        return
    if PROD != os.path.join(BASE, "PRODUCTOS"):
        # DECIDIR_PROD_DIR explícito, o flujo.py corriendo sobre un fixture: CSV siempre.
        return
    db_dir = os.path.join(BASE, "db")
    if db_dir not in sys.path:
        sys.path.insert(0, db_dir)
    import leer as _leer  # noqa: E402

    try:
        con = _leer.conectar()
    except Exception as exc:
        raise SystemExit(
            "\n⛔ VITALCOM_FUENTE=db (default) pero Postgres no está disponible: no se pudo leer "
            "producto/estado_flujo/venta/entrega. Corré con VITALCOM_FUENTE=csv para leer los "
            "espejos CSV en su lugar, o revisá la conexión. Detalle: %s" % exc)
    try:
        _TMP_FUENTE_DB = tempfile.TemporaryDirectory(prefix="decidir_fuente_db_")
        rutas = _leer.materializar(con, TABLAS_FUENTE_DB, _TMP_FUENTE_DB.name, tenant_id=TENANT_ID)
    finally:
        con.close()

    DIM_PROD_PATH = rutas["producto"]
    ESTADO_FLUJO_PATH = rutas["estado_flujo"]
    FACT_VENTAS_PATH = rutas["venta"]
    FACT_ENTREGA_PATH = rutas["entrega_conjunto_dia"]
    FACT_ENTREGA_ANUNCIO_PATH = rutas["entrega_anuncio_dia"]
    _FUENTE_DB_ACTIVADA = True


# No hay tasa USD->moneda local por defecto: cada producto declara la suya en _DIM_PRODUCTOS.csv
# (`tasa`). Un producto sin tasa se OMITE con un aviso (ver `evaluar`); nunca se asume la de GT.


def cargar_parametros():
    p = {
        "ventana_dias": 14,
        "ventana_fatiga_dias": 3,
        "duracion_testeo_fase2_dias": 3,
        "tolerancia_base": "acumulado",
        "maduracion_dias": 10,
        "nivel_confianza": 0.95,
        "alpha_cierre": 0.05,
        "horizonte_ventas": 60,
        "min_mensajes_cierre": 30,
        "agrega_por": "angulo_key",
        "umbral_gasto_sin_chat_usd": 5.0,
        "factor_tolerancia_pd": 1.0,
        "factor_cpa_desbordado": 1.4,
        # reglamento único (09-sep-2026): antes vivían en prosa o como literales
        "min_ventas_ganador": 5,
        "min_ventas_escalar": 2,
        "rezago_max_dias": 2,
        "umbral_conv_clic_enlace_pct": 35.0,
        "min_link_clicks_conv": 30,
        "max_pausas_por_dia": 2,
        "surfing_pct": 20.0,
        "dias_min_cod_pausa_ventas": 3,
        # Lo usa flujo.py (concepto_2de2), no este motor, pero vive acá porque los parámetros
        # del sistema tienen un solo CSV y flujo.py los lee por esta misma puerta. El default
        # repite el del CSV a propósito: si la fila se borra, el gate de FASE 3 no puede volver
        # a quedar en winner-take-all sin que nadie lo note.
        "margen_empate_cpa_pct": 10.0,
        # Benchmark de cierre (UMBRAL_CIERRE_MINIMO_BOT, Clases 16 y 22-ago, Calet). NO es un gate:
        # ningún caso de este archivo lo usa para decidir un ESTADO. Vive acá solo para que la app
        # muestre "cierre actual vs meta" sin inventar el rango (T3 auditoría 21-sep-2026).
        "cierre_meta_min_pct": 15.0,
        "cierre_meta_max_pct": 20.0,
        # Gate duro de FASE 3 -> FASE 4 (PROHIBIDO_ESCALAR_CIERRE_BAJO, Clase 22-ago Calet):
        # a diferencia de cierre_meta_min_pct/max_pct (benchmark, nunca bloquea), este SÍ es un
        # gate — flujo.py lo usa en el predicado `cierre_post_cambio_bot` de F4.entrada.
        "cierre_min_escalar_pct": 10.0,
    }
    if os.path.exists(PARAMS_PATH):
        try:
            with io.open(PARAMS_PATH, encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    k = r.get("parametro", "").strip()
                    v = r.get("valor", "").strip()
                    if k in p:
                        try:
                            p[k] = float(v) if "." in v else int(v)
                        except ValueError:
                            p[k] = v
        except Exception:
            pass
    return p


def ic_cpa(ventas, gasto_usd, conf=0.95, tasa=None):
    """Intervalo de credibilidad Bayesiano del CPA en Quetzales.

    Ventas ~ Poisson(lambda); posterior Jeffreys lambda|k ~ Gamma(k+0.5, 1);
    CPA = gasto_q / lambda. Devuelve (bajo, punto, alto).
    """
    if not tasa or tasa <= 0:
        raise ValueError("ic_cpa necesita la tasa del producto (moneda local por USD); no hay tasa por defecto.")
    gq = gasto_usd * tasa
    if ventas <= 0:
        a = (1.0 - conf) / 2.0
        hi_lam = _gamma.ppf(1 - a, 0.5)
        bajo = round(gq / hi_lam, 1) if hi_lam > 0 else 0.0
        return bajo, None, None

    a = (1.0 - conf) / 2.0
    hi_lam = _gamma.ppf(1 - a, ventas + 0.5)
    lo_lam = _gamma.ppf(a, ventas + 0.5)
    bajo = round(gq / hi_lam, 1) if hi_lam > 0 else 0.0
    alto = round(gq / lo_lam, 1) if lo_lam > 0 else None
    punto = round(gq / ventas, 1)
    return bajo, punto, alto


def calcular_ventas_faltantes(ventas, gasto_usd, be_q, conf, horizonte, tasa):
    """Calcula cuántas ventas faltan para que el IC se resuelva bajo el BE al CPA observado."""
    if ventas <= 0 or not be_q:
        return None
    cpa_actual = (gasto_usd * tasa) / ventas
    if cpa_actual >= be_q:
        return None
    for n in range(int(ventas) + 1, horizonte + 1):
        g_proj = (gasto_usd / ventas) * n
        b_n, _, a_n = ic_cpa(n, g_proj, conf, tasa)
        if a_n is not None and a_n < be_q:
            return n - int(ventas)
    return None


def _progreso_ventas(ventas, faltan):
    """Deriva (ventas_actual, ventas_necesarias) del mismo `faltan` que ya decidió la celda.

    El umbral es el que el motor REALMENTE aplicó ahí, no uno inventado: si `faltan` es None
    (el motor no proyectó ventana) el progreso también es None — nunca un cero disfrazado.
    """
    if faltan is None:
        return None, None
    return int(ventas), int(ventas) + int(faltan)


def comparar_cierre(a_v, a_m, b_v, b_m, alpha):
    """Fisher exacto entre dos tasas de cierre. Corta, nunca corona."""
    if min(a_m, b_m) <= 0:
        return None
    try:
        _, p = fisher_exact([[int(a_v), int(a_m - a_v)], [int(b_v), int(b_m - b_v)]])
        return {
            "p": round(float(p), 4),
            "significativo": bool(p < alpha),
            "cierre_a": round(a_v / a_m * 100, 1),
            "cierre_b": round(b_v / b_m * 100, 1),
        }
    except Exception:
        return None


def _num_o_none(v):
    """float o None (NaN de pandas incluido): el motor no inventa un cero donde no hay data."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _dias_entre(desde, hasta):
    """Días con data de una celda, ambos extremos incluidos. None si falta alguno."""
    try:
        d = getattr(desde, "date", lambda: desde)()
        h = getattr(hasta, "date", lambda: hasta)()
        if d is None or h is None or d != d or h != h:
            return None
        return (h - d).days + 1
    except (TypeError, AttributeError):
        return None


def cargar_productos():
    prods = {}
    if not os.path.exists(DIM_PROD_PATH):
        return prods
    with io.open(DIM_PROD_PATH, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pk = r.get("producto_key", "").strip()
            if not pk:
                continue

            def _flt(val, default=0.0):
                try:
                    return float(val) if val else default
                except ValueError:
                    return default

            prods[pk] = {
                "producto_key": pk,
                "nombre": r.get("nombre_display", pk),
                "estado": r.get("estado", "DESCONOCIDO"),
                "fase": r.get("fase", ""),
                "cpa_base_q": _flt(r.get("cpa_base_q")),
                "cpa_be_q": _flt(r.get("cpa_be_q")),
                "tasa": _flt(r.get("tasa"), None),
            }
    return prods


def cargar_datos_duckdb(dias=14, grano="angulo", dias_fatiga=3):
    """Carga cada celda con TRES cortes temporales distintos sobre la misma serie.

    - Columnas de VENTANA  (ventas/mensajes/spend_usd): últimos `dias`. Miden CPA e IC.
    - Columnas de FATIGA   (*_3d): últimos `dias_fatiga`. Se comparan CONTRA la ventana.
    - Columnas ACUMULADAS  (*_acum): toda la serie. Miden la tolerancia 1x BE, que no se
      olvida cada ciclo porque la pérdida se acumula.
    """
    import duckdb

    con = duckdb.connect()

    # Un conjunto renombrado en Meta es el mismo objeto: hechos y dimensiones (conjuntos, bandas,
    # entrega) se resuelven a su nombre canónico, de los dos lados del JOIN. Sin esto el nombre
    # nuevo no cruza con la dimensión, pierde su ángulo y compite como un ángulo aparte.
    con.execute("create temp table alias_map (viejo varchar, nuevo varchar)")
    filas_alias = []
    if os.path.exists(ALIAS_PATH):
        with io.open(ALIAS_PATH, encoding="utf-8-sig", newline="") as fh:
            filas_alias = list(csv.DictReader(fh))
    mapa_alias = _alias_de(filas_alias)
    if mapa_alias:
        con.executemany("insert into alias_map values (?, ?)", list(mapa_alias.items()))

    # spend_usd deja de ser el de _FACT_VENTAS.csv (LucidSales) tal cual: gasto.py agrega el gasto
    # de Meta y las ventas de LucidSales POR SEPARADO a grano (producto,cuenta,ventana,conjunto) y
    # los cruza con un FULL OUTER JOIN -- una fila por celda, nunca una por venta original (eso
    # duplicaba el gasto en un conjunto con varios anuncios sin match individual). Ver
    # Ads/_TOOLS/gasto.py para la regla completa y por que. El CSV temporal se limpia al final de
    # esta funcion (variable _ruta_ventas_gasto).
    global COBERTURA_GASTO
    # Rutas del MODULO (no las constantes de gasto.py) y el MISMO mapa de alias ya cargado arriba
    # (no el de gasto.canonico() sobre el repo real): flujo.py monkey-parchea estas rutas para
    # correr el motor sobre un fixture de test (Entorno.motor()); sin esto un fixture leería el
    # gasto/alias de Meta del repo real y contaminaría el resultado del test.
    _ruta_ventas_gasto, COBERTURA_GASTO = _gasto.escribir_conjunto_ventana_csv(
        ruta_ventas=FACT_VENTAS_PATH,
        ruta_entrega=FACT_ENTREGA_PATH,
        alias_fn=lambda n: mapa_alias.get(n, n),
    )

    f_ventas = _ruta_ventas_gasto.replace("\\", "/")
    f_conj = DIM_CONJ_PATH.replace("\\", "/")
    f_bandas = DIM_BANDAS_PATH.replace("\\", "/")

    # La banda REAL vive en _DIM_BANDAS.csv (su dueno). Si el archivo no existe todavia
    # la bandera queda en true, en vez de mentir con un false.
    if os.path.exists(DIM_BANDAS_PATH):
        # Una fila por conjunto canónico: dos grafías del mismo conjunto no pueden duplicar sus
        # ventas en el JOIN. Basta una fila NO para que la banda no coincida.
        cte_bandas = ("bandas as (select coalesce(am.nuevo, trim(b.conjunto_meta)) as conjunto, "
                      "bool_and(upper(trim(b.coincide)) = 'SI') as coincide "
                      "from read_csv('%s', header=true, all_varchar=true) b "
                      "left join alias_map am on am.viejo = trim(b.conjunto_meta) "
                      "group by 1),") % f_bandas
        join_bandas = "left join bandas b on b.conjunto = v.conjunto"
        col_banda = "coalesce(b.coincide, true)"
    else:
        cte_bandas, join_bandas, col_banda = "", "", "true"

    col_agrup = "coalesce(v.angulo_key, v.conjunto)" if grano == "angulo" else "v.conjunto"

    # La conversación por clic-ENLACE vive en _FACT_ENTREGA_ANUNCIO.csv (export de Meta por
    # anuncio). Se agrega por la misma celda; si el archivo no existe, las columnas quedan nulas
    # y la regla de conversación calla en vez de mentir con los clics totales de LucidSales.
    f_ent = FACT_ENTREGA_ANUNCIO_PATH.replace("\\", "/")
    if os.path.exists(FACT_ENTREGA_ANUNCIO_PATH):
        col_agrup_e = "coalesce(d.angulo_key, e.conjunto)" if grano == "angulo" else "e.conjunto"
        cte_entrega = f""",
    entrega_celda as (
        select e.producto_key, {col_agrup_e} as celda,
               sum(try_cast(e.link_clicks as double)) as link_clicks_acum,
               sum(try_cast(e.mensajes as double)) as mensajes_enlace_acum
        from (select trim(x.producto_key) as producto_key,
                     coalesce(am.nuevo, trim(x.conjunto)) as conjunto,
                     x.link_clicks, x.mensajes
              from read_csv('{f_ent}', header=true, all_varchar=true) x
              left join alias_map am on am.viejo = trim(x.conjunto)) e
        left join dim_conj d on d.producto_key = e.producto_key and d.conjunto_meta = e.conjunto
        group by 1, 2
    )"""
        col_entrega = "e.link_clicks_acum, e.mensajes_enlace_acum"
        join_entrega = " left join entrega_celda e on e.producto_key = c.producto_key and e.celda = c.celda"
    else:
        cte_entrega = ""
        col_entrega = "null as link_clicks_acum, null as mensajes_enlace_acum"
        join_entrega = ""

    # Los dos cortes se cuentan desde el ULTIMO DIA CON DATA e incluyen ese dia (>=, no >):
    # con `>` la ventana entregaba dias-1 dias y mentia en el encabezado. El corte de arriba
    # (`<= ult`) es NUEVO (g07-cimientos T2, encontrado en review 22-sep-2026): `ult` ahora se
    # calcula SOLO sobre dias con una fila real de LucidSales (ver la CTE `ult`), pero gasto.py
    # puede agregar celdas de dias MAS RECIENTES que `ult` cuando Meta gasto y LucidSales todavia
    # no escribio nada ese dia. Sin el `<=` esas celdas colaban sin limite superior y la ventana
    # terminaba siendo mas ancha que `dias` (contaminando el CPA con un dia de mas).
    dias = max(int(dias), 1)
    dias_fatiga = max(min(int(dias_fatiga), dias - 1), 1) if dias > 1 else 1
    win = f"v.fecha >= (select f from ult) - interval {dias - 1} day and v.fecha <= (select f from ult)"
    fat = f"v.fecha >= (select f from ult) - interval {dias_fatiga - 1} day and v.fecha <= (select f from ult)"

    sql = f"""
    with {cte_bandas}
    ventas_raw as (
        select
            try_cast(v.ventana_fin as date) as fecha,
            trim(v.producto_key) as producto_key,
            coalesce(am.nuevo, trim(v.conjunto)) as conjunto,
            try_cast(v.spend_usd as double) as spend_usd,
            try_cast(v.ventas as integer) as ventas,
            try_cast(v.mensajes as integer) as mensajes,
            -- gasto.py agrega una celda por Meta aunque LucidSales no haya escrito ninguna fila
            -- ese dia (full outer join, para no perder gasto real). "el ultimo dia CON DATA" que
            -- corta la ventana de evaluacion tiene que seguir significando lo que significaba
            -- antes de gasto.py -- un dia con una fila de LucidSales -- y no correrse por un dia
            -- donde solo Meta gasto y nadie vendio (encontrado en review, 22-sep-2026).
            coalesce(nullif(trim(v.tiene_fila_ventas), ''), '1') = '1' as tiene_fila_ventas
        from read_csv('{f_ventas}', header=true, all_varchar=true) v
        left join alias_map am on am.viejo = trim(v.conjunto)
        where v.ventana_fin is not null and v.ventana_fin != ''
          -- BASE suma; CONTROL solapa a propósito para auditar y nunca suma (DATA_PLAYBOOK).
          and upper(coalesce(nullif(trim(v.rol_ventana), ''), 'BASE')) = 'BASE'
    ),
    ult as (
        select max(fecha) as f from ventas_raw where tiene_fila_ventas
    ),
    dim_conj as (
        select
            trim(c.producto_key) as producto_key,
            coalesce(am.nuevo, trim(c.conjunto_meta)) as conjunto_meta,
            max(trim(c.angulo_key)) as angulo_key
        from read_csv('{f_conj}', header=true, all_varchar=true) c
        left join alias_map am on am.viejo = trim(c.conjunto_meta)
        group by 1, 2
    ),
    unidos as (
        select
            v.fecha,
            v.producto_key,
            v.conjunto,
            coalesce(d.angulo_key, v.conjunto) as angulo_key,
            v.ventas,
            v.mensajes,
            v.spend_usd,
            {col_banda} as banda_coincide,
            (regexp_extract(v.conjunto, '^[A-Z0-9]+_[A-Z0-9]+_([-A-Z0-9]+)_R[0-9]+$', 1) <> '') as en_convencion
        from ventas_raw v
        left join dim_conj d
          on d.producto_key = v.producto_key and d.conjunto_meta = v.conjunto
        {join_bandas}
    ),
    celdas as (
    select
        producto_key,
        {col_agrup} as celda,
        count(distinct case when {win} then v.conjunto end) as conjuntos,
        sum(case when {win} then ventas     else 0 end) as ventas,
        sum(case when {win} then mensajes   else 0 end) as mensajes,
        sum(case when {win} then spend_usd  else 0 end) as spend_usd,
        sum(case when {fat} then ventas     else 0 end) as ventas_3d,
        sum(case when {fat} then mensajes   else 0 end) as mensajes_3d,
        sum(case when {fat} then spend_usd  else 0 end) as spend_3d,
        sum(ventas)    as ventas_acum,
        sum(mensajes)  as mensajes_acum,
        sum(spend_usd) as spend_acum,
        min(case when {win} then v.fecha end) as desde,
        max(case when {win} then v.fecha end) as hasta,
        min(v.fecha) as desde_acum,
        max(v.fecha) as hasta_acum,
        bool_and(case when {win} then banda_coincide else true end) as banda_ok,
        bool_and(case when {win} then en_convencion  else true end) as nombres_ok
    from unidos v
    group by 1, 2
    having sum(case when {win} then spend_usd else 0 end) > 0
    ){cte_entrega}
    select c.*, {col_entrega}
    from celdas c{join_entrega}
    order by 1, 4 desc
    """
    df = con.execute(sql).fetchdf()
    con.close()
    try:
        os.remove(_ruta_ventas_gasto)
    except OSError:
        pass
    return df


def _monto(valor, decimales, producto_key):
    """Monto en la moneda del mercado del producto (solo presentacion).

    Sin producto_key, o si el producto no resuelve mercado (fixtures de tests,
    backtest), se formatea en Q como antes: la presentacion nunca tumba al motor."""
    if decimales is None:
        q = "Q%s" % valor
    else:
        q = "Q%.*f" % (decimales, float(valor))
    if not producto_key:
        return q
    try:
        return mercado.monto_producto(valor, producto_key, decimales)
    except mercado.MercadoError:
        return q


def evaluar_celda(ventas, mensajes, spend_usd, ventas_3d, mensajes_3d, spend_3d,
                  be_q, obj_q, tasa, params,
                  ventas_acum=None, mensajes_acum=None, spend_acum_usd=None,
                  link_clicks_acum=None, mensajes_enlace_acum=None, dias_activo=None,
                  producto_key=None):
    """Evalúa una celda combinando Intervalos de Credibilidad con Reglas Operativas.

    Las métricas de rendimiento (CPA, IC, escalado) se miden sobre la VENTANA.
    Las reglas de corte de pérdida (hook muerto, tolerancia 1x BE) se miden sobre el
    ACUMULADO desde el lanzamiento: la plata quemada no se olvida al pasar la ventana.

    link_clicks_acum / mensajes_enlace_acum vienen de _FACT_ENTREGA_ANUNCIO.csv (export de Meta):
    la conversación por clic-ENLACE. Sin ellos la regla de conversación calla — nunca se usa la
    columna `clicks` de _FACT_VENTAS.csv, que son clics totales y dan 5-13 % hasta en ganadores.
    dias_activo = días entre el primer y el último día con data de la celda (maduración COD).
    """
    if ventas_acum is None:
        ventas_acum = ventas
    if mensajes_acum is None:
        mensajes_acum = mensajes
    if spend_acum_usd is None:
        spend_acum_usd = spend_usd

    gasto_q = spend_usd * tasa
    gasto_acum_q = spend_acum_usd * tasa
    gasto_3d_q = spend_3d * tasa
    cpa_real_q = (gasto_q / ventas) if ventas > 0 else None
    cpa_acum_q = (gasto_acum_q / ventas_acum) if ventas_acum > 0 else None
    cierre_pct = (ventas / mensajes * 100.0) if mensajes > 0 else None

    # Un ángulo con historia de rentabilidad no se APAGA por una mala racha: se le RENUEVA
    # el concepto. Sin esta guarda, PAUSAR (regla 3) se evalúa antes que FATIGA (regla 4) y
    # un ganador probado recibe "apagar" en vez de "rotar creativo" — el error del 06-sep-2026.
    min_gan = int(params.get("min_ventas_ganador", 5))
    ganador_historico = (ventas_acum >= min_gan and cpa_acum_q is not None and cpa_acum_q <= be_q)

    # Intervalo de credibilidad Bayesiano
    conf = float(params.get("nivel_confianza", 0.95))
    horizonte = int(params.get("horizonte_ventas", 60))
    dias_fat = int(params.get("ventana_fatiga_dias", 3))
    bajo_ic, punto_ic, alto_ic = ic_cpa(ventas, spend_usd, conf, tasa)
    ic_res = [bajo_ic, punto_ic, alto_ic]

    # PD = Presupuesto de Decisión (1x Break-Even de tolerancia para testeo).
    # Se consume sobre el gasto ACUMULADO: con ventana móvil la regla era inalcanzable
    # (Q22.80/día x 3 días = Q68.40 nunca llega al BE Q93.41) y no cortaba nunca.
    pd_q = be_q * params.get("factor_tolerancia_pd", 1.0)
    pct_pd_consumido = (gasto_acum_q / pd_q * 100.0) if pd_q > 0 else 0.0

    # 1. REGLA: HOOK MUERTO / ENLACE CAÍDO (sobre el acumulado: si alguna vez trajo un
    #    chat, el enlace no está caído — no importa que esta ventana venga en cero)
    if spend_acum_usd >= params["umbral_gasto_sin_chat_usd"] and mensajes_acum == 0:
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_HOOK_MUERTO",
            "accion_sugerida": f"APAGAR INMEDIATO: Gastó ${spend_acum_usd:.2f} acumulados sin un solo chat. Hook sin atracción o WhatsApp caído.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 1,
        }

    # 1b. REGLA: MATAR POR CONVERSACIÓN (Joaquín, clases 7 y 15 · ESCALADO_PLAYBOOK 1.5).
    #     Con 0 ventas acumuladas y clics de enlace suficientes, una conversación por clic-enlace
    #     bajo el umbral es un problema anuncio→bot y se corta SIN esperar el presupuesto de
    #     decisión. Solo con link_clicks reales (export de Meta); sin ellos, la regla calla.
    umb_conv = float(params.get("umbral_conv_clic_enlace_pct", 35.0))
    piso_lc = int(params.get("min_link_clicks_conv", 30))
    conv_enlace_pct = None
    if link_clicks_acum and link_clicks_acum > 0:
        conv_enlace_pct = (mensajes_enlace_acum or 0.0) / link_clicks_acum * 100.0
    if (ventas_acum == 0 and not ganador_historico and conv_enlace_pct is not None
            and link_clicks_acum >= piso_lc and conv_enlace_pct < umb_conv):
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_CONVERSACION_FLOJA",
            "accion_sugerida": f"APAGAR (matar por conversación): {conv_enlace_pct:.0f}% de conversación por clic-enlace ({(mensajes_enlace_acum or 0):.0f} chats / {link_clicks_acum:.0f} clics) bajo el {umb_conv:.0f}% con 0 ventas. Problema anuncio→bot: no esperar el PD.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 1,
        }

    # 2. REGLA: TOLERANCIA DE DECISIÓN AGOTADA (0 ventas ACUMULADAS tras 1x BE acumulado
    #    Y la maduración COD cumplida: el "0 ventas" de un conjunto de 2 días no es veredicto)
    dias_min_cod = int(params.get("dias_min_cod_pausa_ventas", 3))
    cod_cumplido = (dias_activo is None) or (dias_activo >= dias_min_cod)
    if ventas_acum == 0 and gasto_acum_q >= pd_q and cod_cumplido:
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_TOLERANCIA_AGOTADA",
            "accion_sugerida": f"APAGAR: Gastó {_monto(gasto_acum_q, 1, producto_key)} acumulados (100% de tolerancia BE {_monto(be_q, 1, producto_key)}) sin una sola venta. Cortar pérdida.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 1,
        }

    # 3. REGLA: CPA DESBORDADO (Destrucción de margen confirmada)
    umbral_desborde = be_q * params.get("factor_cpa_desbordado", 1.4)
    desbordado = (ventas >= 2 and cpa_real_q and cpa_real_q > umbral_desborde) or (bajo_ic and bajo_ic > be_q)
    if desbordado and not ganador_historico:
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_CPA_DESBORDADO",
            "accion_sugerida": f"APAGAR: CPA {_monto(cpa_real_q, 1, producto_key)} desbordado sobre BE {_monto(be_q, 1, producto_key)} (IC mín {_monto(bajo_ic, 0, producto_key)}). Margen destruido.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 2,
        }

    # 4. REGLA: DETECTOR TEMPRANO DE FATIGA (últimos `ventana_fatiga_dias` CONTRA la ventana).
    #    Exige que la ventana de fatiga sea un subconjunto propio de la de evaluación: si son
    #    iguales, la celda se compara consigo misma y RENOVAR no se emite nunca.
    if (ventas >= 5 or ganador_historico) and gasto_3d_q >= (0.6 * be_q) and spend_3d < spend_usd:
        cpa_3d = (gasto_3d_q / ventas_3d) if ventas_3d > 0 else None
        if ventas_3d == 0 or (cpa_3d and cpa_3d > 1.3 * be_q) or desbordado:
            return {
                "estado": "RENOVAR",
                "accion_codigo": "FATIGA_CREATIVO",
                "accion_sugerida": f"RENOVAR CREATIVO (FASE 2): Ángulo probado ({ventas_acum:.0f} vts acumuladas a CPA {_monto(cpa_acum_q, 1, producto_key)} bajo BE {_monto(be_q, 1, producto_key)}) pero los últimos {dias_fat}d sangran ({_monto(gasto_3d_q, 0, producto_key)} con {ventas_3d:.0f} vts). Mantener ángulo y rotar concepto — NO apagar.",
                "cpa_real_q": round(cpa_real_q, 1) if cpa_real_q else None,
                "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
                "pct_pd": round(pct_pd_consumido, 1),
                "ic": ic_res,
                "faltan_ventas": None,
                "ventas_actual": None,
                "ventas_necesarias": None,
                "nivel_prioridad": 3,
            }

    # 5. REGLA: ESCALAR SURFING (Ganador sólido con CPA <= Objetivo)
    ic_bajo_be = alto_ic is not None and alto_ic <= be_q
    min_esc = int(params.get("min_ventas_escalar", 2))
    surf = float(params.get("surfing_pct", 20.0))
    if ventas >= min_esc and cpa_real_q and cpa_real_q <= obj_q and ic_bajo_be:
        return {
            "estado": "ESCALAR",
            "accion_codigo": "ESCALAR_SURFING",
            "accion_sugerida": f"ESCALAR (Calet): CPA {_monto(cpa_real_q, 1, producto_key)} (Obj {_monto(obj_q, 1, producto_key)}) con {ventas:.0f} ventas, IC entero bajo BE. Opciones: (A) Duplicar campaña al ppto inicial, o (B) Pasar a CBO 1-1-7 a Q120 ($15 USD) con Surfing +{surf:.0f}% una vez al día.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 4,
        }

    # 6. REGLA: ESCALA LEVE / MANTENER (Rentable bajo Break-Even)
    if ventas >= min_esc and cpa_real_q and (obj_q < cpa_real_q <= be_q) and ic_bajo_be:
        return {
            "estado": "ESCALAR",
            "accion_codigo": "ESCALAR_MODERADO",
            "accion_sugerida": f"MANTENER / ESCALA LEVE: CPA rentable {_monto(cpa_real_q, 1, producto_key)} bajo BE {_monto(be_q, 1, producto_key)}. Opciones: duplicar o subir hasta +{surf:.0f}% (una vez, en la mañana) si el CPA se mantiene bajo.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 3,
        }

    # 7. REGLA: TESTEO ACTIVO / SEGUIR MIDIENDO (El IC cruza BE pero está en tolerancia)
    faltan = calcular_ventas_faltantes(ventas, spend_usd, be_q, conf, horizonte, tasa)
    if ventas == 0:
        disponible_q = pd_q - gasto_acum_q
        if gasto_acum_q >= pd_q and not cod_cumplido:
            return {
                "estado": "SEGUIR_MIDIENDO",
                "accion_codigo": "TESTEO_ESPERA_COD",
                "accion_sugerida": f"MANTENER (esperar COD): PD agotado ({pct_pd_consumido:.0f}%) pero solo {dias_activo} día(s) con data, menos que los {dias_min_cod} de maduración. Un 0 ventas tan temprano no es veredicto.",
                "cpa_real_q": None,
                "cierre_pct": 0.0,
                "pct_pd": round(pct_pd_consumido, 1),
                "ic": ic_res,
                "faltan_ventas": None,
                "ventas_actual": None,
                "ventas_necesarias": None,
                "nivel_prioridad": 2,
            }
        return {
            "estado": "SEGUIR_MIDIENDO",
            "accion_codigo": "TESTEO_EN_TOLERANCIA",
            "accion_sugerida": f"MANTENER / MEDIR: Gastó {_monto(gasto_acum_q, 1, producto_key)} acumulados de {_monto(pd_q, 1, producto_key)} ({pct_pd_consumido:.0f}% PD). Margen disponible: {_monto(disponible_q, 1, producto_key)}.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "ventas_actual": None,
            "ventas_necesarias": None,
            "nivel_prioridad": 2,
        }

    if ventas == 1:
        txt_faltan = f" Faltan ~{faltan} ventas para resolver IC." if faltan else ""
        v_actual, v_necesarias = _progreso_ventas(ventas, faltan)
        return {
            "estado": "SEGUIR_MIDIENDO",
            "accion_codigo": "TESTEO_PRIMERA_VENTA",
            "accion_sugerida": f"MANTENER / MEDIR: 1 venta a CPA {_monto(cpa_real_q, 1, producto_key)} (IC [{bajo_ic:.0f}-{alto_ic if alto_ic else 'inf'}]).{txt_faltan} Mantener presupuesto.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": faltan,
            "ventas_actual": v_actual,
            "ventas_necesarias": v_necesarias,
            "nivel_prioridad": 2,
        }

    # Muestra moderada cruzando BE: acción conservadora de bajo riesgo
    txt_f = f" Faltan ~{faltan} ventas al CPA actual para resolver IC." if faltan else " El CPA observado está cerca del BE."
    rentable_pero_sin_evidencia = cpa_real_q is not None and cpa_real_q <= be_q
    if rentable_pero_sin_evidencia:
        txt_accion = (f"MANTENER PRESUPUESTO (no subir): CPA {_monto(cpa_real_q, 1, producto_key)} bajo BE {_monto(be_q, 1, producto_key)}, "
                      f"pero el IC [{bajo_ic:.0f}-{alto_ic if alto_ic else 'inf'}] lo cruza.{txt_f}")
    else:
        txt_accion = (f"MANTENER PRESUPUESTO: IC [{bajo_ic:.0f} - {alto_ic if alto_ic else 'inf'}] "
                      f"cruza BE {_monto(be_q, 1, producto_key)}.{txt_f}")
    v_actual, v_necesarias = _progreso_ventas(ventas, faltan)
    return {
        "estado": "SEGUIR_MIDIENDO",
        "accion_codigo": "MANTENER_Y_MEDIR",
        "accion_sugerida": txt_accion,
        "cpa_real_q": round(cpa_real_q, 1) if cpa_real_q else None,
        "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
        "pct_pd": round(pct_pd_consumido, 1),
        "ic": ic_res,
        "faltan_ventas": faltan,
        "ventas_actual": v_actual,
        "ventas_necesarias": v_necesarias,
        "nivel_prioridad": 2,
    }


FASES_EN_TESTEO = ("F1", "F2", "F3")


def cargar_fases():
    """{producto_key: fase vigente} de _ESTADO_FLUJO.csv. Vacio si el archivo no existe."""
    fases = {}
    if not os.path.exists(ESTADO_FLUJO_PATH):
        return fases
    try:
        with io.open(ESTADO_FLUJO_PATH, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                pk = (r.get("producto_key") or "").strip()
                if pk:
                    fases[pk] = (r.get("fase") or "").strip().upper()
    except (IOError, OSError, csv.Error):
        pass
    return fases


def aplicar_gate_fase(celdas, fase, pk, params=None):
    """GATE #2: una orden de ESCALAR no es EJECUTABLE mientras el producto este en gate de testeo.

    POR QUE NO SE DEGRADA EL ESTADO. Lo obvio seria convertir el ESCALAR en SEGUIR_MIDIENDO, y
    seria un error: flujo.py corona el angulo ganador PRECISAMENTE por el ESCALAR del motor
    (_ev_angulo_ganador). Si el motor se lo calla mientras el producto esta en F1, el producto
    no puede salir de F1 por esa rama y el gate se muerde la cola. El ESCALAR es EVIDENCIA de
    que la celda vende barato, y esa evidencia es valida en cualquier fase.

    LO QUE SI SE BLOQUEA ES LA ACCION. El invariante 6 pide mismo presupuesto en todos los
    conjuntos dentro de cada etapa, para no sesgar que gana por dinero: subirle el presupuesto
    a un conjunto en pleno testeo hace ganar al que recibio mas plata, no al mejor. Y el
    invariante 13 ya nombra mover plata como LA accion irreversible. Asi que el estado queda y
    lo que se marca es `ejecutable`, que es lo que miran etapa-7, el operador y el runner MCP.

    En la simulacion de TURMERIC el motor ordeno escalar un conjunto el dia 1, en plena FASE 1.

    Con las 4 fases (decisión 28-sep-2026): F3 (optimización del flujo del bot) tambien testea —
    escalar ahi compraria volumen antes de confirmar que el bot reescrito cierra, y por eso queda
    en FASES_EN_TESTEO junto a F1/F2. Solo F4 (escalado) ejecuta.

    TRES VALORES, nunca dos: True (F4 o fuera de testeo) · False (F1/F2/F3) · None cuando la fase
    no esta derivada (sin fila, o sin _ESTADO_FLUJO.csv). None NO es permiso: es 'no pude
    evaluarlo', y lo dice. Inventar un permiso donde no hay dato es lo que este sistema no hace.
    """
    params = params or {}
    min_msj = params.get("min_mensajes_cierre", 30)
    min_cierre = params.get("cierre_min_escalar_pct", 10)
    for c in celdas:
        if c.get("estado") != "ESCALAR":
            c["ejecutable"] = True
            c["bloqueo_fase"] = None
            continue
        if not fase:
            c["ejecutable"] = None
            c["bloqueo_fase"] = ("No sabemos en qué fase está %s todavía: corré "
                                 "`python Ads/_TOOLS/flujo.py %s` para saberlo antes de tocar "
                                 "presupuesto" % (pk, pk))
            c["accion_sugerida"] = "⚠ FASE SIN DERIVAR — " + c["accion_sugerida"]
        elif fase in FASES_EN_TESTEO:
            c["ejecutable"] = False
            if fase == "F3":
                c["bloqueo_fase"] = (
                    "%s ya es ganador (rentable, evidencia confirmada), pero está en FASE 3 "
                    "optimizando el flujo del bot hacia el concepto ganador: si le subís "
                    "presupuesto ahora, escalás antes de confirmar que el bot reescrito cierra. "
                    "Para desbloquearlo: aplicá el CAMBIO_BOT (o registrá la EXCEPCION_CAMBIO_BOT) "
                    "y esperá ≥%s mensajes con cierre ≥%s%% para pasar a FASE 4 (escalado)."
                    % (pk, min_msj, min_cierre))
            elif fase == "F2":
                c["bloqueo_fase"] = (
                    "%s ya es ganador (rentable, evidencia confirmada), pero está en FASE 2 "
                    "testeando conceptos: si le subís presupuesto ahora, gana el conjunto que "
                    "recibió más plata, no el mejor concepto. Para desbloquearlo: terminá el "
                    "testeo hasta que un concepto gane 2 de 2, lo que pasa el producto a FASE 3 "
                    "(optimización del flujo del bot)."
                    % pk)
            else:
                c["bloqueo_fase"] = (
                    "%s ya es ganador (rentable, evidencia confirmada), pero está en FASE 1 "
                    "testeando ángulos: si le subís presupuesto ahora, gana el conjunto que "
                    "recibió más plata, no el mejor ángulo. Para desbloquearlo: terminá FASE 1 "
                    "y pasá a FASE 2 con el ángulo ganador." % pk)
            c["accion_sugerida"] = (
                "NO SUBIR PRESUPUESTO todavía: %s. Mantené el presupuesto que ya tiene hasta "
                "entonces. Orden original del motor: %s"
                % (c["bloqueo_fase"].rstrip("."), c["accion_sugerida"]))
        else:
            c["ejecutable"] = True
            c["bloqueo_fase"] = None
    return celdas


def aplicar_tope_pausas(celdas, params):
    """GATE #1 (ESCALADO_PLAYBOOK 1.5): como máximo `max_pausas_por_dia` pausas por producto por
    corrida, las de mayor gasto primero. Las demás quedan PAUSAR_DIFERIDA (SEGUIR_MIDIENDO con la
    orden anotada) hasta mañana. Un enlace caído (hook muerto) nunca se difiere: no es una
    decisión de rendimiento. Devuelve cuántas se difirieron."""
    tope = int(params.get("max_pausas_por_dia", 2))
    cand = [c for c in celdas if c.get("estado") == "PAUSAR" and c.get("accion_codigo") != "PAUSAR_HOOK_MUERTO"]
    cand.sort(key=lambda c: -float(c.get("spend_q") or c.get("spend_usd") or 0.0))
    for c in cand[tope:]:
        c["estado"] = "SEGUIR_MIDIENDO"
        c["accion_codigo"] = "PAUSAR_DIFERIDA"
        c["accion_sugerida"] = ("DIFERIDA (máx %d pausas/día, Calet: no apagar todo en un día malo): %s"
                                % (tope, c.get("accion_sugerida", "")))
        c["nivel_prioridad"] = 2
    return max(0, len(cand) - tope)


def analizar_portafolio(producto_filtro=None, grano="angulo", dias=None):
    _activar_fuente_db_si_corresponde()
    params = cargar_parametros()
    if dias:
        params["ventana_dias"] = dias
    dias_v = int(params["ventana_dias"])
    dias_f = int(params.get("ventana_fatiga_dias", 3))
    if dias_f >= dias_v:
        # Invariante del detector de fatiga: si la ventana reciente no es un subconjunto
        # propio de la de evaluación, la celda se compara consigo misma y RENOVAR muere.
        dias_f = max(dias_v - 1, 1)
        params["ventana_fatiga_dias"] = dias_f

    prods = cargar_productos()
    fases = cargar_fases()          # la fase VIGENTE la deriva flujo.py, no la declara el CSV
    df_celdas = cargar_datos_duckdb(dias=dias_v, grano=grano, dias_fatiga=dias_f)

    # FRESCURA. La ventana de evaluacion se cuenta desde el ULTIMO DIA CON DATA, no desde hoy.
    # Si la data trae rezago, la orden se calcula sobre un pasado que la fecha "generado" oculta:
    # es el mismo error de ventana que produjo la orden equivocada del 06-sep-2026.
    hoy = datetime.date.today()
    datos_hasta = datos_desde = None
    rezago = None
    if not df_celdas.empty:
        try:
            datos_hasta = max(df_celdas["hasta"])
            datos_desde = min(df_celdas["desde"])
            datos_hasta = getattr(datos_hasta, "date", lambda: datos_hasta)()
            datos_desde = getattr(datos_desde, "date", lambda: datos_desde)()
            rezago = (hoy - datos_hasta).days
        except (KeyError, TypeError, ValueError):
            pass

    resultado = {
        "generado": hoy.isoformat(),
        "datos_desde": datos_desde.isoformat() if datos_desde else None,
        "datos_hasta": datos_hasta.isoformat() if datos_hasta else None,
        "rezago_dias": rezago,
        "motor": "decidir v4 (IC Bayesiana + Riesgo Asimétrico + tres relojes separados)",
        "grano": grano,
        "ventana_dias": dias_v,
        "ventana_fatiga_dias": dias_f,
        "tolerancia_base": "acumulado",
        "nivel_confianza": float(params.get("nivel_confianza", 0.95)),
        # Benchmark de cierre (GUIA_MADRE_PARAMETRIZADA.md, UMBRAL_CIERRE_MINIMO_BOT): referencia,
        # no gate. Se expone acá para que la app muestre "cierre actual vs meta" sin hardcodearlo.
        "cierre_meta_min_pct": float(params.get("cierre_meta_min_pct", 15.0)),
        "cierre_meta_max_pct": float(params.get("cierre_meta_max_pct", 20.0)),
        # De donde salio el spend_usd de cada celda producto+conjunto+ventana (g07-cimientos T2,
        # Ads/_TOOLS/gasto.py): MetaAPI-conjunto = Meta Graph API; LucidSales-fallback = celdas sin
        # cobertura de Meta para esa cuenta+ventana.
        "cobertura_gasto": dict(COBERTURA_GASTO),
        "resumen_acciones": {
            "PAUSAR": 0,
            "RENOVAR": 0,
            "ESCALAR": 0,
            "SEGUIR_MIDIENDO": 0,
        },
        "productos": [],
    }

    if df_celdas.empty:
        return resultado

    if producto_filtro:
        df_celdas = df_celdas[df_celdas["producto_key"] == producto_filtro]

    for pk, g in df_celdas.groupby("producto_key"):
        info = prods.get(pk, {})
        be_q = info.get("cpa_be_q", 90.0)
        obj_q = info.get("cpa_base_q", 30.0)
        tasa = info.get("tasa")
        if not tasa or tasa <= 0:
            motivo = ("«%s» no declara `tasa` (moneda local por USD) en _DIM_PRODUCTOS.csv%s: se OMITE "
                      "de las decisiones; no hay tasa por defecto." % (pk, "" if info else " (ni tiene fila)"))
            print("AVISO decidir: " + motivo, file=sys.stderr)
            resultado.setdefault("omitidos", []).append({"producto_key": pk, "motivo": motivo})
            continue
        estado_prod = info.get("estado", "DESCONOCIDO")

        celdas_eval = []
        for r in g.itertuples():
            eval_res = evaluar_celda(
                ventas=float(r.ventas),
                mensajes=float(r.mensajes),
                spend_usd=float(r.spend_usd),
                ventas_3d=float(r.ventas_3d),
                mensajes_3d=float(r.mensajes_3d),
                spend_3d=float(r.spend_3d),
                be_q=be_q,
                obj_q=obj_q,
                tasa=tasa,
                params=params,
                ventas_acum=float(r.ventas_acum),
                mensajes_acum=float(r.mensajes_acum),
                spend_acum_usd=float(r.spend_acum),
                link_clicks_acum=_num_o_none(r.link_clicks_acum),
                mensajes_enlace_acum=_num_o_none(r.mensajes_enlace_acum),
                dias_activo=_dias_entre(r.desde_acum, r.hasta_acum),
                producto_key=pk,
            )
            eval_res.update({
                "celda": str(r.celda),
                "conjuntos": int(r.conjuntos),
                "ventas": float(r.ventas),
                "mensajes": float(r.mensajes),
                "spend_usd": round(float(r.spend_usd), 2),
                "spend_q": round(float(r.spend_usd) * tasa, 1),
                "ventas_acum": float(r.ventas_acum),
                "spend_acum_q": round(float(r.spend_acum) * tasa, 1),
                "banda_ok": bool(r.banda_ok),
                "nombres_ok": bool(r.nombres_ok),
            })
            celdas_eval.append(eval_res)

        # GATE #1: máximo de pausas por producto por corrida (las demás quedan diferidas)
        aplicar_tope_pausas(celdas_eval, params)
        # GATE #2: en fase de testeo, un ESCALAR sigue siendo evidencia pero NO es ejecutable
        fase_vigente = fases.get(pk, "")
        aplicar_gate_fase(celdas_eval, fase_vigente, pk, params)
        for c in celdas_eval:
            estado_cat = c["estado"]
            resultado["resumen_acciones"][estado_cat] = resultado["resumen_acciones"].get(estado_cat, 0) + 1

        # Comparación de cierre (Fisher) si aplica
        min_msj = int(params.get("min_mensajes_cierre", 30))
        alpha = float(params.get("alpha_cierre", 0.05))
        elegibles = [f for f in celdas_eval if f["mensajes"] >= min_msj]
        mejor = max(elegibles, key=lambda f: f["cierre_pct"] or 0, default=None)
        if mejor:
            for f in celdas_eval:
                if f is not mejor and f["mensajes"] >= min_msj:
                    cf = comparar_cierre(f["ventas"], f["mensajes"], mejor["ventas"], mejor["mensajes"], alpha)
                    if cf and cf["significativo"]:
                        f["cierre_vs_mejor"] = dict(cf, contra=mejor["celda"])

        # Ordenar: PAUSAR -> RENOVAR -> ESCALAR -> SEGUIR_MIDIENDO
        orden_prio = {"PAUSAR": 0, "RENOVAR": 1, "ESCALAR": 2, "SEGUIR_MIDIENDO": 3}
        celdas_eval.sort(key=lambda x: (orden_prio.get(x["estado"], 9), -x["spend_q"]))

        resultado["productos"].append({
            "producto_key": pk,
            "nombre": info.get("nombre", pk),
            "estado_producto": estado_prod,
            "fase_vigente": fase_vigente or None,   # de _ESTADO_FLUJO.csv (derivada por flujo.py)
            "cpa_objetivo_q": obj_q,
            "break_even_q": be_q,
            "celdas": celdas_eval,
        })

    return resultado


def imprimir_consola(res):
    print("=" * 115)
    print(f" MOTOR DE DECISIÓN UNIFICADO — VITALCOM GUATEMALA (Evaluación: {res['ventana_dias']}d | Fatiga: {res.get('ventana_fatiga_dias', 3)}d | Tolerancia: acumulada | IC 95% | Grano: {res['grano']})")
    if res.get("datos_hasta"):
        rez = res.get("rezago_dias")
        print(f" Data: {res.get('datos_desde')} → {res['datos_hasta']}  (generado {res['generado']})")
        if rez is not None and rez > 2:
            print(f" ⚠️  LA DATA ARRASTRA {rez} DÍAS DE REZAGO. Estas órdenes NO describen lo que pasó "
                  f"después del {res['datos_hasta']}: cargá el export antes de ejecutarlas.")
    print(f" Resumen:  🔴 PAUSAR: {res['resumen_acciones'].get('PAUSAR', 0)}  |  "
          f"🔵 RENOVAR (FATIGA): {res['resumen_acciones'].get('RENOVAR', 0)}  |  "
          f"🟢 ESCALAR: {res['resumen_acciones'].get('ESCALAR', 0)}  |  "
          f"🟡 SEGUIR MIDIENDO: {res['resumen_acciones'].get('SEGUIR_MIDIENDO', 0)}")
    print("=" * 115)

    for p in res["productos"]:
        fv = p.get("fase_vigente")
        print(f"\n[{p['producto_key']}]  Estado: {p['estado_producto']} | Fase: {fv or '(sin derivar)'} | Break-Even: {_monto(p['break_even_q'], 2, p['producto_key'])} | CPA Objetivo: {_monto(p['cpa_objetivo_q'], 2, p['producto_key'])}")
        frenadas = [c for c in p["celdas"] if c.get("ejecutable") is False]
        sin_fase = [c for c in p["celdas"] if c.get("ejecutable") is None]
        if frenadas:
            print(f"  ⛔ {len(frenadas)} orden(es) de ESCALAR NO EJECUTABLES: {p['producto_key']} está en {fv}, "
                  f"gate de testeo. Valen como EVIDENCIA de ganador; mover plata ahora sesga la medición "
                  f"(invariante 6). Mantener presupuesto hasta cerrar la fase.")
        if sin_fase:
            print(f"  ⚠️  {len(sin_fase)} orden(es) de ESCALAR sin fase derivada: corré "
                  f"`python Ads/_TOOLS/flujo.py {p['producto_key']}` antes de mover presupuesto.")
        print("-" * 115)
        print(f"  {'ESTADO':<16} {'CELDA / ÁNGULO':<28} {'VTS':>4} {'MSJ':>5} {'GASTO Q':>8} {'CPA REAL':>8} {'IC 95% Q':<15} ACCIÓN INMEDIATA")
        print("-" * 115)

        for c in p["celdas"]:
            est = f"[{c['estado']}]"
            cpa_str = _monto(c['cpa_real_q'], 1, p['producto_key']) if c['cpa_real_q'] else "-"
            ic = c.get("ic", [0, 0, 0])
            ic_str = f"[{ic[0]:.0f}-{ic[2]:.0f}]" if (ic and ic[2]) else f"[≥{ic[0]:.0f}]" if ic else "-"
            print(f"  {est:<16} {c['celda'][:26]:<28} {c['ventas']:>4.0f} {c['mensajes']:>5.0f} {c['spend_q']:>8.1f} {cpa_str:>8} {ic_str:<15} {c['accion_sugerida']}")

    print("\n" + "=" * 115)
    print(" SÍNTESIS COMPLETA: Cero parálisis por falta de muestra · Cero decisiones irreversibles sin evidencia.")
    print("=" * 115)


def main():
    ap = argparse.ArgumentParser(description="Motor de Decisión Unificado (VitalCom)")
    ap.add_argument("producto", nargs="?", help="producto_key opcional")
    ap.add_argument("--grano", choices=["angulo", "conjunto"], default="angulo", help="Agrupación (angulo por defecto)")
    ap.add_argument("--dias", type=int, default=None, help="Días de la ventana de EVALUACION (no cambia la tolerancia acumulada)")
    ap.add_argument("--json", action="store_true", help="Emitir solo JSON por stdout")
    ap.add_argument("--escribir", action="store_true",
                    help="guarda _DECISIONES.json (por defecto solo lee/calcula)")
    args = ap.parse_args()

    res = analizar_portafolio(producto_filtro=args.producto, grano=args.grano, dias=args.dias)

    if args.escribir:
        # P3 T4: escribe SIEMPRE por Postgres (db/escribir.py) -- la verdad vive en
        # raw.decisiones_json, _DECISIONES.json es el ESPEJO regenerado tras el commit. Import
        # LOCAL (nunca al tope del módulo, ver el comentario junto a TENANT_ID más arriba).
        db_dir = os.path.join(BASE, "db")
        if db_dir not in sys.path:
            sys.path.insert(0, db_dir)
        import cargar as db_cargar  # noqa: E402
        import escribir as db_escribir  # noqa: E402

        prod_dir = os.path.dirname(SALIDA_JSON)
        try:
            con = db_cargar.conectar()
        except Exception as exc:
            raise SystemExit(
                "\n⛔ Postgres no disponible: no se pudo escribir _DECISIONES.json (nunca se "
                "escribe el CSV directo). Detalle: %s" % exc)
        try:
            db_escribir.verificar_decision_sincronizada(con, prod_dir, tenant_id=TENANT_ID)
            db_escribir.reemplazar_decision(con, res, prod_dir=prod_dir, tenant_id=TENANT_ID)
        except db_escribir.ErrorEscritura as exc:
            raise SystemExit("\n⛔ %s" % exc)
        finally:
            con.close()

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        imprimir_consola(res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
