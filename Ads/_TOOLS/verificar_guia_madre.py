#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verificar_guia_madre.py — GATE DEL TEXTO MADRE.

DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md declara, variable por variable, que valor rige el
sistema y que archivo lo ejecuta. Sin un verificador eso es prosa: puede desincronizarse
del codigo en silencio y nadie se entera hasta que una orden sale mal.

Ya paso. El 07-sep-2026 la Guia Madre declaraba VENTANA = 3 DIAS, el CSV decia 3, y el
docstring de decidir.py seguia diciendo 14. Tres fuentes, tres respuestas, cero alarmas.

Este gate hace TRES cosas, y no adivina ninguna:

  A. PUNTEROS    Cada archivo citado en la columna "Archivo Ejecutor" existe en disco.
                 Un texto madre que apunta a un archivo borrado miente por omision.

  B. VALORES     Para cada variable con verificador registrado, extrae el numero que la
                 GUIA declara (de su propia fila, no de este script) y lo compara con el
                 valor REAL que usa el ejecutor. Si este archivo hardcodeara los valores,
                 solo moveria el problema de lugar.

  C. COHERENCIA  Invariantes entre variables, y el drift inverso: un parametro que vive
                 en el codigo pero que la Guia Madre no declara en ninguna fila.

Lo que NO puede verificar lo DICE, no lo aprueba en silencio: las variables cualitativas
(psicografia, niveles de conciencia, DOFA, objeciones) se cuentan como "sin verificador".

USO:  python Ads/_TOOLS/verificar_guia_madre.py            (exit 0 = pasa, 1 = falla)
      python Ads/_TOOLS/verificar_guia_madre.py --listar   (que se verifica y que no)
"""

import io
import os
import re
import sys
import csv

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUIA = os.path.join(BASE, "DOCTRINA", "GUIA_MADRE_PARAMETRIZADA.md")
PARAMS = os.path.join(BASE, "PRODUCTOS", "_PARAMETROS_DECISION.csv")
DECIDIR = os.path.join(BASE, "Ads", "_TOOLS", "decidir.py")

RE_VAR = re.compile(r"^`([A-Z][A-Z0-9_]{3,})`$")
RE_TOKEN = re.compile(r"`([^`]+)`")
RE_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
EXT = (".md", ".py", ".csv", ".json", ".txt", ".html")


# ------------------------------------------------------------- lectura de fuentes

def leer_filas_guia():
    """Devuelve [(variable, celda_valor, celda_ejecutor, n_linea)] de las tablas markdown."""
    filas = []
    for n, linea in enumerate(io.open(GUIA, encoding="utf-8"), 1):
        if not linea.lstrip().startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 3:
            continue
        m = RE_VAR.match(celdas[0])
        if m:
            filas.append((m.group(1), celdas[1], celdas[-1], n))
    return filas


def params_csv():
    d = {}
    with io.open(PARAMS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            k = (r.get("parametro") or "").strip()
            if k:
                d[k] = (r.get("valor") or "").strip()
    return d


def params_efectivos():
    """Los parametros TAL COMO los ve el motor: defaults de decidir.py + overrides del CSV."""
    if os.path.dirname(DECIDIR) not in sys.path:
        sys.path.insert(0, os.path.dirname(DECIDIR))
    from decidir import cargar_parametros
    return cargar_parametros()


def fuente_decidir():
    return io.open(DECIDIR, encoding="utf-8").read()


def num(texto):
    """Primer numero de una celda. '**`14 DIAS`**' -> 14.0 ; '$5.00 USD' -> 5.0"""
    m = RE_NUM.search(texto or "")
    return float(m.group(0).replace(",", ".")) if m else None


def buscar_por_nombre(nombre):
    """Resuelve un puntero suelto (sin ruta) a su ubicacion real, o None."""
    for dp, dirs, archivos in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in (".git", "_ARCHIVO", "node_modules")]
        if nombre in archivos:
            return os.path.relpath(os.path.join(dp, nombre), BASE).replace("\\", "/")
    return None


# ------------------------------------------------------------- A. punteros

def verificar_punteros(filas):
    fallas, avisos, vistos = [], [], set()
    for var, _valor, ejecutor, ln in filas:
        for tok in RE_TOKEN.findall(ejecutor):
            tok = tok.strip().rstrip("/")
            # Un token sin extension y sin barra es un nombre de parametro, no una ruta
            # (ej. "PRODUCTOS/_PARAMETROS_DECISION.csv -> duracion_testeo_fase2_dias").
            if not tok.endswith(EXT) and "/" not in tok:
                continue
            if (var, tok) in vistos:
                continue
            vistos.add((var, tok))

            if os.path.exists(os.path.join(BASE, tok)):
                continue

            if "/" not in tok:
                real = buscar_por_nombre(tok)
                if real:
                    avisos.append("linea %d  %-28s puntero suelto `%s` -> resuelve a %s "
                                  "(conviene escribir la ruta completa)" % (ln, var, tok, real))
                    continue
            fallas.append("linea %d  %-28s apunta a `%s`, que NO existe" % (ln, var, tok))
    return fallas, avisos


# ------------------------------------------------------------- B. valores

def _csv_num(clave):
    def f():
        v = params_csv().get(clave)
        return (None if v is None else float(v)), "_PARAMETROS_DECISION.csv:%s" % clave
    f.csv_key = clave   # lo lee verificar_coherencia() para saber que claves ya estan cubiertas
    return f


def _csv_txt(clave):
    def f():
        return params_csv().get(clave), "_PARAMETROS_DECISION.csv:%s" % clave
    f.csv_key = clave
    return f


def _param_efectivo(clave):
    def f():
        v = params_efectivos().get(clave)
        return (None if v is None else float(v)), "decidir.py:cargar_parametros()[%s]" % clave
    return f


def _literal_fuente(patron, etiqueta):
    """Extrae un umbral hardcodeado del codigo de decidir.py."""
    def f():
        m = re.search(patron, fuente_decidir())
        return (float(m.group(1)) if m else None), "decidir.py (%s)" % etiqueta
    return f


# variable de la Guia -> (como leer el valor REAL, modo de comparacion).
# El valor DECLARADO siempre sale de la fila de la Guia, nunca de aca: si este archivo
# hardcodeara los numeros, solo moveria el problema de lugar.
VERIFICADORES = {
    "VENTANA_EVALUACION_DIAS":     (_csv_num("ventana_dias"), "num"),
    "VENTANA_FATIGA_DIAS":         (_csv_num("ventana_fatiga_dias"), "num"),
    "DURACION_TESTEO_FASE2_DIAS":  (_csv_num("duracion_testeo_fase2_dias"), "num"),
    "FASE2_DURACION_TESTEO":       (_csv_num("duracion_testeo_fase2_dias"), "num"),
    "MADURACION_ENTREGA_COD":      (_csv_num("maduracion_dias"), "num_en_rango"),
    "NIVEL_CONFIANZA_ESTADISTICA": (_csv_num("nivel_confianza"), "num"),
    "ALPHA_CIERRE":                (_csv_num("alpha_cierre"), "num"),
    "MINIMO_MENSAJES_COMPARAR_CIERRE": (_csv_num("min_mensajes_cierre"), "num"),
    "HORIZONTE_VENTAS_PROYECCION": (_csv_num("horizonte_ventas"), "num"),
    "TOLERANCIA_BASE":             (_csv_txt("tolerancia_base"), "txt"),
    "TOLERANCIA_MAXIMA_TESTEO":    (_param_efectivo("factor_tolerancia_pd"), "num"),
    "UMBRAL_HOOK_MUERTO_USD":      (_param_efectivo("umbral_gasto_sin_chat_usd"), "num"),
    "UMBRAL_CPA_DESBORDADO":       (_param_efectivo("factor_cpa_desbordado"), "num"),
    "MINIMO_VENTAS_PARA_ESCALAR":  (_literal_fuente(
        r"ventas >= (\d+) and cpa_real_q and cpa_real_q <= obj_q", "regla 5, ESCALAR_SURFING"), "num"),
    "GUARDA_GANADOR_HISTORICO":    (_literal_fuente(
        r"ventas_acum >= (\d+) and cpa_acum_q is not None", "guarda ganador_historico"), "num"),
}


def verificar_valores(filas):
    fallas, ok = [], []
    for var, valor, _ejec, ln in filas:
        if var not in VERIFICADORES:
            continue
        leer, modo = VERIFICADORES[var]
        real, origen = leer()

        if real is None:
            fallas.append("linea %d  %-28s la Guia lo declara, pero %s NO EXISTE"
                          % (ln, var, origen))
            continue

        if modo == "txt":
            decl = (RE_TOKEN.findall(valor) or [valor])[0].strip("* `")
            bien = decl.lower() == str(real).strip().lower()
        elif modo == "num_en_rango":
            # celda con rango ("3 a 10 DIAS"): el valor real tiene que caer adentro
            ns = [float(x.replace(",", ".")) for x in RE_NUM.findall(valor)]
            decl = ("%g a %g" % (min(ns), max(ns))) if len(ns) > 1 else (ns[0] if ns else None)
            bien = bool(ns) and min(ns) <= real <= max(ns)
        else:
            decl = num(valor)
            bien = decl is not None and abs(decl - real) < 1e-9

        if bien:
            ok.append("%-28s declara %-10s == %s" % (var, decl, origen))
        else:
            fallas.append("linea %d  %-28s la GUIA declara %s, pero %s vale %s"
                          % (ln, var, decl, origen, real))
    return fallas, ok


# ------------------------------------------------------------- C. coherencia

# Parametros del CSV que no necesitan fila propia en la Guia Madre.
EXENTOS = {"agrega_por"}


def verificar_coherencia(filas):
    fallas = []
    p = params_efectivos()

    # El invariante que se rompio el 07-sep: la ventana de fatiga tiene que ser un
    # subconjunto PROPIO de la de evaluacion, o el detector se compara consigo mismo.
    if int(p["ventana_fatiga_dias"]) >= int(p["ventana_dias"]):
        fallas.append("ventana_fatiga_dias (%s) NO es menor que ventana_dias (%s): el detector "
                      "de fatiga se compara consigo mismo y RENOVAR no se emite nunca"
                      % (p["ventana_fatiga_dias"], p["ventana_dias"]))

    # Drift inverso: un parametro que el motor lee y que el texto madre no declara.
    # Una clave esta cubierta si alguna variable de la Guia la verifica (el vinculo real vive
    # en VERIFICADORES) o si alguna fila la nombra explicitamente.
    declaradas = {v for v, _, _ in [(v, val, ej) for v, val, ej, _ in filas]}
    cubiertas = {getattr(leer, "csv_key", None)
                 for var, (leer, _modo) in VERIFICADORES.items()
                 if var in declaradas}
    texto = " ".join("%s %s %s" % (v, val, ej) for v, val, ej, _ in filas)
    for clave in params_csv():
        if clave in EXENTOS or clave in cubiertas or clave in texto:
            continue
        fallas.append("el parametro `%s` vive en _PARAMETROS_DECISION.csv, pero la Guia "
                      "Madre no lo declara en ninguna fila" % clave)
    return fallas


# ------------------------------------------------------------- salida

def main():
    if not os.path.exists(GUIA):
        print("FALLA  no existe %s" % GUIA)
        return 1

    filas = leer_filas_guia()
    f_punt, a_punt = verificar_punteros(filas)
    f_val, ok_val = verificar_valores(filas)
    f_coh = verificar_coherencia(filas)
    sin_verificador = [v for v, _, _, _ in filas if v not in VERIFICADORES]

    print("=" * 84)
    print(" GATE DEL TEXTO MADRE - DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md")
    print("=" * 84)
    print(" %d variables declaradas | %d verificadas contra su ejecutor | %d cualitativas"
          % (len(filas), len(filas) - len(sin_verificador), len(sin_verificador)))

    if "--listar" in sys.argv:
        print("\n VALORES VERIFICADOS CONTRA SU EJECUTOR")
        for l in ok_val:
            print("   ok   " + l)
        print("\n SIN VERIFICADOR (cualitativas: no son un numero que un script pueda leer)")
        for v in sin_verificador:
            print("   --   " + v)

    if a_punt:
        print("\n AVISOS (no bloquean)")
        for a in a_punt:
            print("   ~    " + a)

    fallas = f_punt + f_val + f_coh
    if fallas:
        print("\n FALLAS")
        for f in fallas:
            print("   X    " + f)
        print("\n %d falla(s). El texto madre NO coincide con lo que corre." % len(fallas))
        return 1

    print("\n Sin fallas: cada valor declarado coincide con su ejecutor y todo puntero existe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
