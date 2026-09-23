#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flujo.py — EL FLUJO DECLARADO: dónde está cada producto, qué lo bloquea y qué sigue.

QUÉ ES
------
El grafo de pasos del sistema vive en DOCTRINA/FLUJO.json: fases, nodos, ejecutores y GATES.
Este script lo recorre para cada producto y responde, con la data del disco y nada más:

    · en qué FASE está (por el gate de entrada de cada fase, evaluado sobre los CSV),
    · cuál es el NODO ACTUAL (el primer paso cuyos artefactos aún no existen),
    · qué lo BLOQUEA (cada `requiere` que falla, con el nombre de quien lo produce),
    · qué se EJECUTA a continuación (subagente, skill, script u operador),
    · qué le falta para AVANZAR a la fase siguiente,
    · y los AVISOS: cosas que no bloquean pero contradicen la doctrina.

POR QUÉ EXISTE (2026-09-09)
---------------------------
Los números del sistema ya no varían: costeo, break-even, decisión y publicación salen de
scripts y CSV. Lo que variaba eran las TRANSICIONES entre pasos y sus gates, que vivían en
prosa dentro de las skills y un modelo las interpretaba cada vez. El 08-sep-2026 cuatro gates
escritos en doctrina no se dispararon (10 conceptos o no arranca · estructura 1-1-5 · plan
igual a lo publicado · preguntarle a Meta antes de publicar) y se gastaron $23.46 sirviendo la
pieza equivocada. Con esos cuatro predicados en código, este script los canta antes de gastar.
Ads/_TOOLS/test_flujo.py congela ese caso.

EL PRINCIPIO
------------
    DOCTRINA/FLUJO.json   EL SISTEMA    qué pasos hay, quién ejecuta cada uno, qué gate lo cierra
    los CSV / _PLAN.json  LOS HECHOS    lo que existe en disco
    este script           EL RECORRIDO  evalúa predicados; no decide, no ejecuta, no inventa
    flujo_html.py         EL DIBUJO     VISTAS/FLUJO.html

Un gate que no se pueda escribir con el vocabulario cerrado de predicados de abajo NO es un
gate: es criterio, y vive en el subagente que lo ejerce. Este script dicta; la sesión ejecuta
(por Task, por skill o por MCP con confirmación del operador) y este script lo comprueba
después por los artefactos que el nodo declara en `produce`.

VOCABULARIO DE PREDICADOS (cerrado — ver `evaluar`)
---------------------------------------------------
    csv            filas de un CSV de PRODUCTOS/ que cumplen `where` (min/max/eq/distinct/sum)
    csv_campo      un valor de una fila (no_vacio / eq / in / not_in / num_min)
    archivo        existe un archivo o carpeta (opcional: edad_max_dias, contiene)
    glob           N archivos que cumplen un patrón
    json           un campo de un JSON (existe / eq / in / min_len / no_vacio)
    script         un verificador existente devuelve el exit esperado (lista de args, sin shell)
    decision       el motor decidir.py, corrido EN MEMORIA sobre la data actual
    decisiones_json  frescura de PRODUCTOS/_DECISIONES.json (generado hoy / rezago)
    data_fresca    rezago de la última fecha de un CSV
    eventos        filas de _EVENTOS.csv del producto (evento, hoy, desde_dias, campana_contiene)
    angulo_ganador ángulo ganador POR VENTA agregando por angulo_key (invariante 1)
    concepto_2de2  concepto que gana en 2 de 2 campañas de conceptos (regla de replicación)
    estructura_publicada  conjuntos observados en Meta vs los de _PARAMETROS_PUBLICACION.csv
    todos / alguno / no   composición

DE DÓNDE SALE CADA DATO (un dato, un dueño)
-------------------------------------------
    productos, carpetas, cuenta, página    PRODUCTOS/_DIM_PRODUCTOS.csv
    ángulo por conjunto                    PRODUCTOS/_DIM_CONJUNTOS.csv
    creativos y sus ad_id                  PRODUCTOS/_DIM_CREATIVOS.csv
    ventas y gasto                         PRODUCTOS/_FACT_VENTAS.csv
    eventos                                PRODUCTOS/_EVENTOS.csv
    estados de decisión                    Ads/_TOOLS/decidir.py (importado, no reimplementado)
    parámetros                             PRODUCTOS/_PARAMETROS_DECISION.csv (@param:clave)
    estructura por fase                    PRODUCTOS/_PARAMETROS_PUBLICACION.csv (@publicacion:…)

QUÉ ESCRIBE (solo con --todo --escribir — ver CONTRATO DE CLI)
-----------
    PRODUCTOS/_FLUJO.json          el estado de todos los productos (lo dibuja la app)
    PRODUCTOS/_ESTADO_FLUJO.csv    una fila por producto: fase, nodo, desde cuándo
    PRODUCTOS/_EVENTOS.csv         una fila TRANSICION_FLUJO cada vez que un producto cambia de nodo
    VISTAS/FLUJO.html              la vista, vía flujo_html.py

CONTRATO DE CLI (T6, parejo con decidir.py y gen_grafo.py)
------------------------------------------------------------
Un "mirar" nunca escribe. `flujo.py PRODUCTO`, `--json`, `--validar` y `--grafo`
ya eran solo lectura. `--todo` (el único modo que antes escribía por defecto)
ahora también es solo lectura salvo que se pida `--escribir` explícitamente —
ese es el único flag que toca `_ESTADO_FLUJO.csv`/`_EVENTOS.csv`/`_FLUJO.json`/
`FLUJO.html`. `gate_entrada()` (usada por gen_publicacion.py y
registrar_evento.py como función de Python, no CLI) sigue siendo SOLO LECTURA
sin excepción.

USO
---
    python Ads/_TOOLS/flujo.py TINNIDROP              # un producto: dónde está, qué bloquea, qué sigue
    python Ads/_TOOLS/flujo.py --todo                 # los 8 productos, SOLO LECTURA (no escribe nada)
    python Ads/_TOOLS/flujo.py --todo --escribir      # ademas, persiste _FLUJO.json y la vista
    python Ads/_TOOLS/flujo.py TINNIDROP --json       # solo el JSON del producto
    python Ads/_TOOLS/flujo.py --validar              # el JSON declarado contra el disco (nunca escribe)
    python Ads/_TOOLS/flujo.py --grafo                # el grafo en mermaid (lo usa la vista)
    python Ads/_TOOLS/flujo.py --base DIR --hoy 2026-09-08 --sin-scripts   # replay sobre un fixture
"""
import argparse
import csv
import datetime
import fnmatch
import glob as _glob
import io
import json
import os
import re
import subprocess
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BASE_REAL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(BASE_REAL, "Ads", "_TOOLS")
FLUJO_DECLARADO = os.path.join("DOCTRINA", "FLUJO.json")

EVENTO_TRANSICION = "TRANSICION_FLUJO"
CAMPOS_ESTADO = ["producto_key", "fase", "nodo_actual", "estado", "desde", "bloqueantes",
                 "siguiente_ejecutor", "evaluado_el"]


# ─────────────────────────────────────────────────────────────────────────────
# 0 · ENTORNO: base, fecha y caches
# ─────────────────────────────────────────────────────────────────────────────

class Entorno(object):
    """Todo lo que el evaluador necesita saber del mundo: dónde está la data y qué día es.

    `base` puede ser un fixture (test_flujo.py) — por eso nada usa rutas absolutas del repo
    real salvo los scripts, que se desactivan con `sin_scripts` cuando se corre sobre un fixture.
    """

    def __init__(self, base=None, hoy=None, sin_scripts=False):
        self.base = os.path.abspath(base or BASE_REAL)
        self.hoy = hoy or datetime.date.today()
        self.sin_scripts = sin_scripts
        self._csv = {}
        self._json = {}
        self._motor = None
        self._params = None
        self._alias = None

    # -- rutas --------------------------------------------------------------
    def ruta(self, *partes):
        return os.path.join(self.base, *partes)

    def prod(self, nombre):
        return self.ruta("PRODUCTOS", nombre)

    # -- lectores con cache -------------------------------------------------
    def csv(self, nombre):
        if nombre not in self._csv:
            ruta = self.prod(nombre) if not os.path.isabs(nombre) else nombre
            filas = []
            if os.path.exists(ruta):
                with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
                    filas = list(csv.DictReader(fh))
            self._csv[nombre] = filas
        return self._csv[nombre]

    def alias(self):
        """{nombre_viejo: nombre_canónico} del _ALIAS_CONJUNTOS.csv de ESTA base (fixture o real)."""
        if self._alias is None:
            if TOOLS not in sys.path:
                sys.path.insert(0, TOOLS)
            from alias import mapa_de
            self._alias = mapa_de(self.csv("_ALIAS_CONJUNTOS.csv"))
        return self._alias

    def json(self, ruta_rel):
        ruta = self.ruta(ruta_rel)
        if ruta not in self._json:
            d = None
            if os.path.exists(ruta):
                try:
                    with io.open(ruta, encoding="utf-8") as fh:
                        d = json.load(fh)
                except ValueError:
                    d = None
            self._json[ruta] = d
        return self._json[ruta]

    # -- el motor de decisión, importado y corrido una sola vez ---------------
    def motor(self):
        """decidir.analizar_portafolio() sobre la data de `base`. Nunca escribe nada."""
        if self._motor is None:
            if TOOLS not in sys.path:
                sys.path.insert(0, TOOLS)
            import decidir
            if self.base != BASE_REAL:
                # apuntar el motor al fixture: sus rutas son globales de módulo
                P = os.path.join(self.base, "PRODUCTOS")
                decidir.PROD = P
                decidir.PARAMS_PATH = os.path.join(P, "_PARAMETROS_DECISION.csv")
                decidir.DIM_PROD_PATH = os.path.join(P, "_DIM_PRODUCTOS.csv")
                decidir.DIM_CONJ_PATH = os.path.join(P, "_DIM_CONJUNTOS.csv")
                decidir.DIM_BANDAS_PATH = os.path.join(P, "_DIM_BANDAS.csv")
                decidir.FACT_VENTAS_PATH = os.path.join(P, "_FACT_VENTAS.csv")
                decidir.FACT_ENTREGA_PATH = os.path.join(P, "_FACT_ENTREGA.csv")
                decidir.FACT_ENTREGA_ANUNCIO_PATH = os.path.join(P, "_FACT_ENTREGA_ANUNCIO.csv")
                decidir.ALIAS_PATH = os.path.join(P, "_ALIAS_CONJUNTOS.csv")
                # Sin esto, un fixture leería la fase vigente del repo REAL y el gate de fase
                # del motor juzgaría al producto del fixture con la fase de otro producto.
                decidir.ESTADO_FLUJO_PATH = os.path.join(P, "_ESTADO_FLUJO.csv")
            try:
                self._motor = decidir.analizar_portafolio()
            except Exception as e:      # el motor caído no frena el flujo: se dice
                self._motor = {"error": str(e), "productos": []}
        return self._motor

    def celdas(self, pk):
        for p in self.motor().get("productos", []):
            if p.get("producto_key") == pk:
                return p.get("celdas", []), p
        return [], {}

    def params(self):
        if self._params is None:
            if TOOLS not in sys.path:
                sys.path.insert(0, TOOLS)
            import decidir
            if self.base != BASE_REAL:
                decidir.PARAMS_PATH = os.path.join(self.base, "PRODUCTOS", "_PARAMETROS_DECISION.csv")
            self._params = decidir.cargar_parametros()
        return self._params


# ─────────────────────────────────────────────────────────────────────────────
# 1 · UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

class _Ctx(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def fmt(v, ctx):
    if isinstance(v, str):
        return v.format_map(ctx)
    if isinstance(v, list):
        return [fmt(x, ctx) for x in v]
    if isinstance(v, dict):
        return {k: fmt(x, ctx) for k, x in v.items()}
    return v


def norm(s):
    return re.sub(r"\s+", "", (s or "")).upper()


def num(v, default=None):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default


def fecha(s):
    s = (s or "").strip()[:10]
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def resolver_num(v, env):
    """Un número, o una referencia '@param:clave' / '@publicacion:clave' a su dueño."""
    if isinstance(v, str) and v.startswith("@param:"):
        return num(env.params().get(v[7:]))
    if isinstance(v, str) and v.startswith("@publicacion:"):
        return publicacion_num(env, v[13:])
    return num(v)


def publicacion_num(env, clave):
    """Números derivados de _PARAMETROS_PUBLICACION.csv (dueño de la estructura por fase)."""
    filas = [r for r in env.csv("_PARAMETROS_PUBLICACION.csv") if (r.get("estado") or "") == "VIGENTE"]
    m = re.match(r"^(conceptos|conjuntos)_fase(\d)$", clave)
    if not m:
        return None
    que, fase = m.group(1), m.group(2)
    de_fase = [r for r in filas if (r.get("fase") or "") == fase]
    if que == "conjuntos":
        return float(sum(int(num(r.get("conjuntos"), 0)) for r in de_fase))
    # conceptos = anuncios distintos de los brazos que NO replican (C repite los de A y B)
    total = 0
    for r in de_fase:
        if (r.get("brazo") or "").upper() == "C":
            continue
        total += int(num(r.get("conjuntos"), 0)) * int(num(r.get("anuncios_por_conjunto"), 0))
    return float(total)


def coincide(row, where, ctx):
    """¿La fila cumple `where`? Cada condición es str (igual), lista (in) o dict de operador."""
    for col, cond in (where or {}).items():
        v = (row.get(col) or "").strip()
        cond = fmt(cond, ctx)
        if isinstance(cond, str):
            if v != cond:
                return False
        elif isinstance(cond, list):
            if v not in cond:
                return False
        elif isinstance(cond, dict):
            for op, arg in cond.items():
                if op == "contiene" and arg.lower() not in v.lower():
                    return False
                if op == "empieza" and not v.startswith(arg):
                    return False
                if op == "no_vacio" and arg and not v:
                    return False
                if op == "vacio" and arg and v:
                    return False
                if op == "in" and v not in arg:
                    return False
                if op == "not_in" and v in arg:
                    return False
                if op == "norm" and norm(v) != norm(arg):
                    return False
        else:
            return False
    return True


def _campo(d, ruta):
    """Campo anidado 'a.b.c' de un dict; None si no existe."""
    cur = d
    for parte in ruta.split("."):
        if isinstance(cur, dict) and parte in cur:
            cur = cur[parte]
        else:
            return None
    return cur


# ─────────────────────────────────────────────────────────────────────────────
# 2 · EL EVALUADOR: un predicado → (ok, observado)
# ─────────────────────────────────────────────────────────────────────────────

TIPOS = ("csv", "csv_campo", "archivo", "glob", "json", "script", "decision", "decisiones_json",
         "data_fresca", "eventos", "angulo_ganador", "concepto_2de2", "estructura_publicada",
         "todos", "alguno", "no")


def evaluar(pred, ctx, env):
    """Devuelve (ok: bool|None, observado: str). None = no se pudo evaluar (se dice, no se aprueba)."""
    t = pred.get("tipo")
    f = _EVALUADORES.get(t)
    if not f:
        return None, "predicado desconocido: %s" % t
    try:
        return f(pred, ctx, env)
    except Exception as e:      # un predicado roto no frena el recorrido: se reporta
        return None, "error evaluando %s: %s" % (t, e)


def _ev_csv(p, ctx, env):
    filas = [r for r in env.csv(p["csv"]) if coincide(r, p.get("where"), ctx)]
    if p.get("distinct"):
        n = len({(r.get(p["distinct"]) or "").strip() for r in filas if (r.get(p["distinct"]) or "").strip()})
        que = "%d %s distintos" % (n, p["distinct"])
    elif p.get("sum"):
        n = sum(num(r.get(p["sum"]), 0.0) for r in filas)
        que = "suma %s = %.2f (%d filas)" % (p["sum"], n, len(filas))
    else:
        n = len(filas)
        que = "%d fila(s)" % n
    ok = True
    for op in ("min", "max", "eq", "sum_min", "sum_max"):
        if op in p:
            lim = resolver_num(p[op], env)
            if lim is None:
                return None, "%s: límite %s no resuelto" % (que, p[op])
            if op in ("min", "sum_min") and n < lim: ok = False
            if op in ("max", "sum_max") and n > lim: ok = False
            if op == "eq" and n != lim: ok = False
            que += " · esperado %s %g" % ({"min": "≥", "sum_min": "≥", "max": "≤", "sum_max": "≤", "eq": "="}[op], lim)
    return ok, que


def _ev_csv_campo(p, ctx, env):
    fila = next((r for r in env.csv(p["csv"]) if coincide(r, p.get("where"), ctx)), None)
    if fila is None:
        return False, "sin fila en %s" % p["csv"]
    v = (fila.get(p["campo"]) or "").strip()
    que = "%s=«%s»" % (p["campo"], v or "vacío")
    if p.get("no_vacio") and not v:
        return False, que
    if "eq" in p and v != fmt(p["eq"], ctx):
        return False, que
    if "in" in p and v not in fmt(p["in"], ctx):
        return False, que
    if "not_in" in p and v in fmt(p["not_in"], ctx):
        return False, que
    if "num_min" in p and (num(v) is None or num(v) < resolver_num(p["num_min"], env)):
        return False, que
    return True, que


def _ev_archivo(p, ctx, env):
    ruta = env.ruta(fmt(p["ruta"], ctx))
    if not os.path.exists(ruta):
        return False, "no existe %s" % fmt(p["ruta"], ctx)
    dias = (env.hoy - datetime.date.fromtimestamp(os.path.getmtime(ruta))).days
    if "edad_max_dias" in p and dias > resolver_num(p["edad_max_dias"], env):
        return False, "existe pero tiene %d días (máx %g)" % (dias, resolver_num(p["edad_max_dias"], env))
    if "contiene" in p:
        buscado = fmt(p["contiene"], ctx)
        try:
            with io.open(ruta, encoding="utf-8", errors="replace") as f:
                texto = f.read()
        except OSError as e:
            return False, "no se pudo leer %s: %s" % (fmt(p["ruta"], ctx), e)
        if buscado.lower() not in texto.lower():
            return False, "existe pero no contiene «%s»" % buscado
        return True, "existe y contiene «%s» (hace %d día%s)" % (buscado, dias, "" if dias == 1 else "s")
    return True, "existe (hace %d día%s)" % (dias, "" if dias == 1 else "s")


def _ev_glob(p, ctx, env):
    patron = env.ruta(fmt(p["patron"], ctx))
    # glob no escapa corchetes ni '+' raros de las carpetas del repo: se recorre a mano
    carpeta, mascara = os.path.split(patron)
    n = 0
    if os.path.isdir(carpeta):
        n = sum(1 for x in os.listdir(carpeta) if fnmatch.fnmatch(x.lower(), mascara.lower()))
    lim = resolver_num(p.get("min", 1), env)
    return n >= lim, "%d archivo(s) · esperado ≥ %g" % (n, lim)


def _ev_json(p, ctx, env):
    d = env.json(fmt(p["ruta"], ctx))
    if d is None:
        return False, "no existe o no es JSON: %s" % fmt(p["ruta"], ctx)
    v = _campo(d, p["campo"]) if p.get("campo") else d
    que = "%s=%s" % (p.get("campo", "(raíz)"), json.dumps(v, ensure_ascii=False)[:60] if v is not None else "ausente")
    if p.get("existe") and v is None:
        return False, que
    if p.get("no_vacio") and not v:
        return False, que
    if "eq" in p and v != fmt(p["eq"], ctx):
        return False, que
    if "in" in p and v not in fmt(p["in"], ctx):
        return False, que
    if "min_len" in p:
        n = len(v) if isinstance(v, (list, dict, str)) else 0
        lim = resolver_num(p["min_len"], env)
        if n < lim:
            return False, "%s tiene %d elemento(s) · esperado ≥ %g" % (p["campo"], n, lim)
        que = "%s: %d elemento(s)" % (p["campo"], n)
    return True, que


def _ev_script(p, ctx, env):
    if env.sin_scripts:
        return None, "script no evaluado (--sin-scripts)"
    args = fmt(p["cmd"], ctx)
    if not isinstance(args, list):
        return None, "cmd debe ser una lista de argumentos"
    tmp = None
    if any("{tmp}" in a for a in p["cmd"]):
        fd, tmp = tempfile.mkstemp(suffix=".json", prefix="flujo_")
        os.close(fd)
        args = [a.replace("{tmp}", tmp) for a in args]
    args = [sys.executable if a == "python" else a for a in args]
    try:
        r = subprocess.run(args, cwd=env.base, capture_output=True, timeout=int(p.get("timeout", 120)))
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, "no corrió: %s" % e
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    salida = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
    lineas = [l.strip() for l in salida.splitlines() if l.strip()]
    ultima = ""
    for l in lineas:
        if "BLOQUEANTE" in l or l.startswith("[x]") or "FALLA" in l:
            ultima = l
            break
    if not ultima and lineas:
        ultima = lineas[-1]
    esperado = int(p.get("exit", 0))
    return r.returncode == esperado, "exit %d · %s" % (r.returncode, ultima[:110])


def _ev_decision(p, ctx, env):
    celdas, _ = env.celdas(ctx["pk"])
    estados = p.get("estados") or ([p["estado"]] if "estado" in p else [])
    if isinstance(estados, str):
        estados = [estados]
    mv = resolver_num(p.get("min_ventas", 0), env) or 0
    hit = [c for c in celdas if c.get("estado") in estados and num(c.get("ventas"), 0) >= mv]
    que = ", ".join("%s (%s %.0fv CPA Q%s)" % (c["celda"], c["estado"], num(c.get("ventas"), 0),
                                                c.get("cpa_real_q") if c.get("cpa_real_q") is not None else "-")
                    for c in hit) or "ninguna celda en %s" % "/".join(estados)
    n = len(hit)
    if "min" in p and n < resolver_num(p["min"], env):
        return False, que
    if "max" in p and n > resolver_num(p["max"], env):
        return False, que
    return True, que


def _ev_decisiones_json(p, ctx, env):
    d = env.json(os.path.join("PRODUCTOS", "_DECISIONES.json"))
    if not d:
        return False, "no existe PRODUCTOS/_DECISIONES.json"
    gen = fecha(d.get("generado"))
    rez = d.get("rezago_dias")
    que = "generado %s · rezago %s día(s)" % (gen, rez)
    if p.get("generado_hoy") and gen != env.hoy:
        return False, que + " · no es de hoy (%s)" % env.hoy
    if "rezago_max_dias" in p and (rez is None or rez > resolver_num(p["rezago_max_dias"], env)):
        return False, que
    return True, que


def _ev_data_fresca(p, ctx, env):
    filas = [r for r in env.csv(p["csv"]) if coincide(r, p.get("where"), ctx)]
    fechas = [fecha(r.get(p["col"])) for r in filas]
    fechas = [f for f in fechas if f]
    if not fechas:
        return False, "sin fechas en %s" % p["csv"]
    ult = max(fechas)
    rez = (env.hoy - ult).days
    lim = resolver_num(p.get("max_rezago_dias", 2), env)
    return rez <= lim, "última data %s · rezago %d día(s) · máx %g" % (ult, rez, lim)


def _ev_eventos(p, ctx, env):
    ev = p.get("evento")
    evs = [ev] if isinstance(ev, str) else (ev or [])
    # `posterior_a` filtra a eventos con fecha ESTRICTAMENTE posterior a una fecha de referencia
    # que resuelve otra parte del sistema — nunca una fecha escrita a mano acá.
    # `{"tipo": "<clave de RESOLVEDORES_FECHA>"}`; sin fecha de referencia resoluble (p.ej. sin
    # ganador todavía) el gate no pasa, no se interpreta como "sin límite".
    fecha_ref = None
    posterior_a = p.get("posterior_a")
    if posterior_a:
        tipo_fecha = posterior_a.get("tipo") if isinstance(posterior_a, dict) else posterior_a
        resolver = RESOLVEDORES_FECHA.get(tipo_fecha)
        if resolver is None:
            return False, "posterior_a: resolvedor de fecha desconocido '%s'" % tipo_fecha
        fecha_ref = resolver(ctx, env)
        if fecha_ref is None:
            return False, "posterior_a:%s sin fecha de referencia resoluble todavía" % tipo_fecha
    filas = []
    for r in env.csv("_EVENTOS.csv"):
        if (r.get("producto_key") or "").strip() != ctx["pk"]:
            continue
        if evs and (r.get("evento") or "").strip() not in evs:
            continue
        f = fecha(r.get("fecha"))
        if p.get("hoy") and f != env.hoy:
            continue
        if "desde_dias" in p and (f is None or (env.hoy - f).days > resolver_num(p["desde_dias"], env)):
            continue
        if fecha_ref is not None and (f is None or f <= fecha_ref):
            continue
        cc = p.get("campana_contiene")
        if cc and fmt(cc, ctx).lower() not in (r.get("campana_clave") or "").lower():
            continue
        filas.append(r)
    n = len(filas)
    ult = max((fecha(r.get("fecha")) for r in filas if fecha(r.get("fecha"))), default=None)
    que = "%d evento(s) %s%s" % (n, "/".join(evs) or "(cualquiera)", (" · último %s" % ult) if ult else "")
    if fecha_ref is not None:
        que += " · posterior a %s" % fecha_ref
    lim = resolver_num(p.get("min", 1), env)
    if "max" in p:
        return n <= resolver_num(p["max"], env), que
    return n >= lim, que


def _modulo_gasto():
    if TOOLS not in sys.path:
        sys.path.insert(0, TOOLS)
    import gasto
    return gasto


def _celdas_conjunto_gasto(env, pk):
    """gasto.gasto_por_conjunto_ventana() cacheado en `env`, sobre los FACT de la MISMA base
    (real o fixture) que `env` ya resuelve. Una fila por (producto,cuenta,ventana,conjunto) —
    el gasto de Meta de esa celda se agrega UNA vez, nunca se copia por cada venta que cae ahí
    (g07-cimientos T2, defecto de conteo múltiple encontrado en review 22-sep-2026)."""
    if getattr(env, "_celdas_conjunto_gasto", None) is None:
        gasto = _modulo_gasto()
        am = env.alias()
        env._celdas_conjunto_gasto = gasto.gasto_por_conjunto_ventana(
            filas_venta=env.csv("_FACT_VENTAS.csv"),
            filas_entrega_conjunto=env.csv("_FACT_ENTREGA.csv"),
            alias_fn=lambda n: am.get(n, n),
        )
    return env._celdas_conjunto_gasto


def _celdas_anuncio_gasto(env, pk):
    """gasto.gasto_por_anuncio_ventana() cacheado en `env`, mismo criterio que la de arriba pero
    a grano ANUNCIO (para el análisis de CONCEPTO, que vive en el anuncio, no en el conjunto)."""
    if getattr(env, "_celdas_anuncio_gasto", None) is None:
        gasto = _modulo_gasto()
        am = env.alias()
        env._celdas_anuncio_gasto = gasto.gasto_por_anuncio_ventana(
            filas_venta=env.csv("_FACT_VENTAS.csv"),
            filas_entrega_anuncio=env.csv("_FACT_ENTREGA_ANUNCIO.csv"),
            alias_fn=lambda n: am.get(n, n),
        )
    return env._celdas_anuncio_gasto


def _ventas_base(env, pk):
    """(fila, conjunto canónico) de las filas CRUDAS de _FACT_VENTAS.csv del producto que SUMAN.

    BASE suma; CONTROL solapa a propósito para auditar y nunca suma (DATA_PLAYBOOK). El conjunto
    se resuelve con _ALIAS_CONJUNTOS.csv para que un renombrado en Meta cruce con su dimensión.

    `spend_usd` acá es el de LucidSales SIN corregir por gasto.py -- a propósito: los únicos usos
    que quedan de este generador (_ev_estructura_publicada) solo preguntan "¿hay gasto > 0?", un
    booleano donde LucidSales y Meta casi siempre coinciden en el signo. Un CPA de verdad usa
    _celdas_conjunto_gasto()/_celdas_anuncio_gasto(), que agregan por separado y cruzan (full
    outer join) en vez de resolver fila por fila -- resolver fila por fila fue el defecto de
    conteo múltiple encontrado en review (22-sep-2026): copiar el gasto de un conjunto en cada
    venta que cae en él, sin match individual, lo multiplicaba por cada anuncio sin match."""
    am = env.alias()
    for r in env.csv("_FACT_VENTAS.csv"):
        if (r.get("producto_key") or "").strip() != pk:
            continue
        if (r.get("rol_ventana") or "BASE").strip().upper() != "BASE":
            continue
        cj = (r.get("conjunto") or "").strip()
        yield r, am.get(cj, cj)


def _angulos_acumulados(env, pk):
    """VENTA y gasto acumulados por angulo_key, uniendo el gasto ya agregado por conjunto+ventana
    (gasto.gasto_por_conjunto_ventana, g07-cimientos T2) con _DIM_CONJUNTOS. Es la definición
    literal del invariante 1: el ganador se declara por VENTA agregando por angulo_key. Un
    conjunto sin dimensión agrega por su propio nombre (no se descarta data)."""
    am = env.alias()
    ang = {}
    for r in env.csv("_DIM_CONJUNTOS.csv"):
        if (r.get("producto_key") or "").strip() == pk:
            cm = (r.get("conjunto_meta") or "").strip()
            ang[am.get(cm, cm)] = (r.get("angulo_key") or "").strip()
    acc = {}
    for c in _celdas_conjunto_gasto(env, pk):
        if c["producto_key"] != pk:
            continue
        cj = c["conjunto"]
        k = ang.get(cj) or cj
        a = acc.setdefault(k, [0.0, 0.0])
        a[0] += c["ventas"]
        a[1] += c["spend_usd"]
    return acc


def _angulos_probados(env, pk):
    """Ángulos que el producto ya probó en el pasado (para no repetirlos al volver a F1)."""
    angulos = set()
    for row in env.csv("_DIM_CONJUNTOS.csv"):
        if (row.get("producto_key") or "").strip() == pk:
            a = (row.get("angulo_key") or "").strip()
            if a:
                angulos.add(a)
    for c in env.csv("_FACT_VENTAS.csv"):
        if (c.get("producto_key") or "").strip() == pk:
            conj = (c.get("conjunto") or "").strip()
            for row in env.csv("_DIM_CONJUNTOS.csv"):
                if (row.get("conjunto_meta") or "").strip() == conj:
                    a = (row.get("angulo_key") or "").strip()
                    if a:
                        angulos.add(a)
    return sorted(angulos)


def _angulo_ganador_info(p, ctx, env):
    """Cálculo compartido de "quién ganó el ángulo", para que _fecha_angulo_ganador() derive su
    fecha de la MISMA evidencia que corona al ganador, nunca de un cálculo aparte.

    Devuelve {"gana": bool, "claves": [angulo_key,...], "que": str} — `claves` son las llaves
    de angulo_key (o el nombre del conjunto, si el ángulo ganó por la rama histórica sin
    angulo_key asignado todavía) que calificaron como ganadoras."""
    pk = ctx["pk"]
    mv = resolver_num(p.get("min_ventas", "@param:min_ventas_ganador"), env) or 5
    prod = next((r for r in env.csv("_DIM_PRODUCTOS.csv") if (r.get("producto_key") or "").strip() == pk), {})
    be = num(prod.get("cpa_be_q"))
    tasa = num(prod.get("tasa"), 7.62) or 7.62
    ganadores, claves = [], []
    cortos = []                       # ESCALAR que aún no llega al piso: se dice, no se esconde
    celdas, _ = env.celdas(pk)
    for c in celdas:
        if c.get("estado") != "ESCALAR":
            continue
        v = num(c.get("ventas"), 0) or 0
        if v >= mv:
            ganadores.append("%s (ESCALAR %.0fv CPA Q%s)" % (c["celda"], v, c.get("cpa_real_q")))
            claves.append(c["celda"])
        else:
            cortos.append("%s (ESCALAR pero %.0fv < %g)" % (c["celda"], v, mv))
    if be:
        for k, (v, s) in sorted(_angulos_acumulados(env, pk).items(), key=lambda kv: -kv[1][0]):
            if v >= mv and s > 0 and (s * tasa / v) <= be:
                et = "%s (histórico %.0fv CPA Q%.1f ≤ BE Q%.1f)" % (k, v, s * tasa / v, be)
                if not any(k in g for g in ganadores):
                    ganadores.append(et)
                    claves.append(k)
    if not ganadores:
        que = "ningún ángulo con ≥%g ventas a CPA ≤ BE ni ESCALAR vigente con ≥%g ventas" % (mv, mv)
        if cortos:
            que += " · descartado por volumen: " + "; ".join(cortos[:3])
        return {"gana": False, "claves": [], "que": que}
    return {"gana": True, "claves": claves, "que": "; ".join(ganadores[:4])}


def _ev_angulo_ganador(p, ctx, env):
    """Ganador = ESCALAR del motor en la ventana vigente, O historia rentable acumulada.
    Las dos cosas son VENTA por angulo_key, y LAS DOS exigen el mismo piso de volumen
    (min_ventas_ganador). Cada rama se autocontiene y trae su propia prueba de rentabilidad:

      · vigente   ventas de la VENTANA ≥ mv  +  ESCALAR (reglas 5/6 de decidir.py, que ya
                  exigen el IC 95% ENTERO bajo break-even — evidencia más fuerte que un CPA
                  puntual, así que no se le pide además el CPA acumulado: un ángulo que
                  quemó plata antes de arreglar el bot es costo hundido, y eso lo contabiliza
                  CONTABILIDAD.md, no este gate).
      · histórica ventas ACUMULADAS ≥ mv  +  CPA acumulado ≤ BE (sin IC: es un promedio, y
                  por eso necesita toda la serie para sostenerse).

    Hasta el 15-sep-2026 la rama vigente NO pedía piso de volumen: bastaba un ESCALAR. Como
    la regla 5 corona desde min_ventas_escalar (2), un ángulo con 3 ventas de UN SOLO DÍA
    coronaba y el producto saltaba de fase esa misma noche — medido en la simulación de
    TURMERIC. min_ventas_ganador es literalmente «cuántas ventas hacen a un ganador»: que
    una rama lo aplicara y la otra no era un reglamento partido en dos."""
    info = _angulo_ganador_info(p, ctx, env)
    return info["gana"], info["que"]


def _fecha_angulo_ganador(ctx, env):
    """Fecha ESTABLE en la que el ángulo ganador (gate angulo_ganador) quedó confirmado: el
    primer día en que las ventas ACUMULADAS de los conjuntos de ese ángulo alcanzaron el piso
    del ganador (min_ventas_ganador). Es una fecha de PRIMER CRUCE, no "el último día con venta":
    las campañas del ángulo siguen vendiendo después de coronarlo, y un "último día" se movería
    hacia adelante con cada venta nueva, haciendo que un CAMBIO_BOT que hoy es "posterior al
    ganador" deje de serlo mañana sin que nada haya cambiado en el ganador mismo. Con el primer
    cruce, una venta posterior nunca mueve la fecha ya confirmada.

    Usada por F2.etapa-11 para fechar el diagnóstico de congruencia DESPUÉS del ganador — nunca
    antes, que sería diagnosticar un ángulo que todavía no ganó."""
    pk = ctx["pk"]
    info = _angulo_ganador_info({}, ctx, env)
    if not info["gana"] or not info["claves"]:
        return None
    claves = set(info["claves"])
    mv = resolver_num("@param:min_ventas_ganador", env) or 5
    am = env.alias()
    ang = {}
    for r in env.csv("_DIM_CONJUNTOS.csv"):
        if (r.get("producto_key") or "").strip() == pk:
            cm = (r.get("conjunto_meta") or "").strip()
            ang[am.get(cm, cm)] = (r.get("angulo_key") or "").strip()
    filas = []
    for r, cj in _ventas_base(env, pk):
        v = num(r.get("ventas"), 0) or 0
        if v <= 0:
            continue
        k = ang.get(cj) or cj
        if k not in claves:
            continue
        f = fecha(r.get("ventana_fin")) or fecha(r.get("ventana_ini"))
        if f:
            filas.append((f, v))
    filas.sort(key=lambda t: t[0])
    acc = 0.0
    for f, v in filas:
        acc += v
        if acc >= mv:
            return f
    return None


def _concepto_de(anuncio, conjunto):
    """El concepto viaja en el NOMBRE (firma.py): '… ~ PK|ANG|C1.CN03|NC2|…' o en el conjunto
    '…_C1-CN05_R1'. Sin ninguno de los dos, la fila no puede medir concepto."""
    if "~" in (anuncio or ""):
        partes = anuncio.split("~", 1)[1].strip().split("|")
        if len(partes) >= 3 and partes[2].strip():
            return partes[2].strip()
    m = re.search(r"_(C\d+[-.]CN\d+[A-Z_]*)_R\d+", conjunto or "")
    if m:
        return m.group(1)
    return None


def _concepto_ganador_info(p, ctx, env):
    """Cálculo compartido de la regla de replicación, para que la FECHA de confirmación del
    ganador —que necesita el gate «CAMBIO_BOT posterior al ganador» de F3— se derive EXACTAMENTE
    de la misma evidencia que corona al concepto, nunca de un cálculo aparte que podría discrepar.

    Devuelve un dict: {"gana": bool, "concepto": str|None, "n": int, "total_campanas": int,
    "que": str, "empates": [...]}. Un concepto solo "gana" con n >= 2."""
    pk = ctx["pk"]
    mv = resolver_num(p.get("min_ventas", "@param:min_ventas_escalar"), env) or 2
    margen = resolver_num(p.get("margen_empate_pct", "@param:margen_empate_cpa_pct"), env)
    margen = 0.0 if margen is None else margen      # sin parámetro declarado: winner-take-all
    # Grano ANUNCIO ya agregado por gasto.py (g07-cimientos T2): una fila por anuncio, con su
    # gasto de Meta contado una sola vez -- nunca la copia del total del conjunto en cada anuncio
    # sin match individual (ese fue el defecto de conteo múltiple que rompía este mismo gate).
    por_camp = {}
    for c in _celdas_anuncio_gasto(env, pk):
        if c["producto_key"] != pk:
            continue
        camp = c["campana"]
        if "CONCEPTOS" not in camp.upper():
            continue
        cpt = _concepto_de(c["anuncio"], c["conjunto"])
        if not cpt:
            continue
        a = por_camp.setdefault(camp, {}).setdefault(cpt, [0.0, 0.0])
        a[0] += c["ventas"]
        a[1] += c["spend_usd"]
    if len(por_camp) < 2:
        return {"gana": False, "concepto": None, "n": 0, "total_campanas": len(por_camp),
                "empates": [],
                "que": "%d campaña(s) de conceptos con data · se necesitan 2 para replicar" % len(por_camp)}
    conteo = {}
    empates = []
    for camp, cs in sorted(por_camp.items()):
        cand = sorted((s / v, c) for c, (v, s) in cs.items() if v >= mv and s > 0)
        if not cand:
            continue
        techo = cand[0][0] * (1.0 + margen / 100.0)
        ganan = [c for cpa, c in cand if cpa <= techo + 1e-9]
        for c in ganan:
            conteo[c] = conteo.get(c, 0) + 1
        if len(ganan) > 1:
            empates.append("%s en «%s»" % (" = ".join(ganan), camp))
    if not conteo:
        return {"gana": False, "concepto": None, "n": 0, "total_campanas": len(por_camp),
                "empates": empates, "que": "ningún concepto con ≥%g ventas en ninguna campaña" % mv}
    # Desempate determinista: más campañas primero y, a igualdad, el mejor CPA AGREGADO — que
    # junta la evidencia de todas las campañas en vez de fiarse del número de una sola. El
    # nombre entra solo como último recurso, para no depender del orden de lectura del CSV.
    glob = {}
    for cs in por_camp.values():
        for c, (v, s) in cs.items():
            a = glob.setdefault(c, [0.0, 0.0])
            a[0] += v
            a[1] += s

    def _cpa_glob(c):
        v, s = glob.get(c, [0.0, 0.0])
        return (s / v) if v > 0 else float("inf")

    c = min(conteo, key=lambda k: (-conteo[k], _cpa_glob(k), k))
    n = conteo[c]
    que = "%s replica en %d de las %d campañas con data (hacen falta 2)" % (c, n, len(por_camp))
    if empates:
        que += " · empate técnico dentro del %g%%: %s" % (margen, "; ".join(empates[:2]))
    return {"gana": n >= 2, "concepto": c, "n": n, "total_campanas": len(por_camp),
            "empates": empates, "que": que}


def _ev_concepto_2de2(p, ctx, env):
    """Regla de replicación: el mismo concepto gana (≥ min_ventas ventas) en al menos 2 campañas
    de conceptos distintas. Fuente: _FACT_VENTAS.csv, campañas con 'CONCEPTOS' en el nombre.
    Sin dos campañas no hay replicación posible.

    EL UMBRAL ES 2, SIEMPRE. El denominador es cuántas campañas de conceptos tienen data, y la
    doctrina de FASE 2 son TRES (1-1-5 + 1-1-5 + 1-2-5), así que el rótulo natural de este gate
    es «2 de 3»: es la regla 2-de-2 de siempre contada sobre tres campañas, no una variante. El
    mensaje lo dice explícito («… de las 3 campañas con data · hacen falta 2») porque el texto
    viejo —«gana en 2 de 3 campañas»— se leyó como si el umbral hubiera cambiado.

    EMPATE TÉCNICO (15-sep-2026). Hasta hoy cada campaña coronaba UN concepto por CPA puntual
    (`min(cand)`). Con 2-3 ventas por concepto esa diferencia es ruido, y el gate oscilaba día a
    día — medido sobre la simulación de TURMERIC: 25-sep ✗ · 26-sep ✓ · 27-sep ✗ · 28-sep ✓. El
    26 dos conceptos empataban EXACTO (1.75 y 1.75) y desempataba el orden alfabético; el 27 se
    dieron vuelta por Q0.04 (1.7 %) y el producto volvió de FASE 3 a FASE 2. Un 1.7 % con 3
    ventas no prueba replicación: es la misma razón por la que decidir.py no mueve plata con un
    CPA puntual si el IC lo cruza (invariante 13), y entrar a FASE 3 —comprar volumen en CBO— es
    igual de irreversible. Ahora cuenta como ganador de una campaña todo concepto dentro de
    `margen_empate_cpa_pct` del mejor.

    No se usa el IC acá, y es deliberado: con 2 ventas el intervalo de un concepto es tan ancho
    que TODOS se solaparían con todos y el gate se volvería trivial. El margen acota el empate a
    una banda declarada en vez de a una incertidumbre que con n chico no discrimina."""
    info = _concepto_ganador_info(p, ctx, env)
    return info["gana"], info["que"]


def _fecha_concepto_ganador(ctx, env):
    """Fecha ESTABLE en la que el concepto ganador (gate concepto_2de2) quedó confirmado. No
    existe un evento reservado tipo GANADOR_CONCEPTO en _EVENTOS.csv (el vocabulario de evento
    es libre, ver registrar_evento.py) — se DERIVA determinísticamente de la misma evidencia que
    _concepto_ganador_info() ya usa para coronarlo, pero como PRIMER CRUCE, no como "el último
    día con venta": las campañas de CONCEPTOS siguen vendiendo después de que el concepto ya
    replicó, y un "último día" se movería hacia adelante con cada venta nueva, haciendo que un
    CAMBIO_BOT que hoy es "posterior al ganador" deje de serlo mañana. Por campaña, se ordenan
    sus ventas del concepto ganador por fecha y se marca el día en que la suma ACUMULADA alcanzó
    el piso de replicación (min_ventas_escalar); la fecha de confirmación es el día en que la
    SEGUNDA campaña cruzó ese piso — la misma campaña que hace ganar al gate (≥2 campañas).

    Sin ganador, None (el gate `posterior_a` de F3 no puede resolver una fecha de referencia y
    por lo tanto no pasa — correcto: sin concepto ganador tampoco se puede entrar a FASE 3,
    invariante 1)."""
    pk = ctx["pk"]
    info = _concepto_ganador_info({}, ctx, env)
    if not info["gana"] or not info["concepto"]:
        return None
    ganador = info["concepto"]
    mv = resolver_num("@param:min_ventas_escalar", env) or 2
    por_campana = {}
    for r, cj in _ventas_base(env, pk):
        camp = (r.get("campana") or "").strip()
        if "CONCEPTOS" not in camp.upper():
            continue
        v = num(r.get("ventas"), 0) or 0
        if v <= 0:
            continue
        if _concepto_de(r.get("anuncio"), cj) != ganador:
            continue
        f = fecha(r.get("ventana_fin")) or fecha(r.get("ventana_ini"))
        if f:
            por_campana.setdefault(camp, []).append((f, v))
    cruces = []
    for camp, filas in por_campana.items():
        filas.sort(key=lambda t: t[0])
        acc = 0.0
        for f, v in filas:
            acc += v
            if acc >= mv:
                cruces.append(f)
                break
    if len(cruces) < 2:
        return None
    cruces.sort()
    return cruces[1]


RESOLVEDORES_FECHA = {
    "concepto_ganador": _fecha_concepto_ganador,
    "angulo_ganador": _fecha_angulo_ganador,
}


TOKEN_FASE = {"1": "TEST", "2": "CONCEPTOS", "3": "ESCALA"}


def _ev_estructura_publicada(p, ctx, env):
    """Conjuntos con gasto en las campañas de la fase vs los que declara _PARAMETROS_PUBLICACION.
    Si hay MÁS conjuntos que los de la doctrina, la estructura publicada no es la doctrinal
    (el 08-sep: 5 conjuntos × 1 concepto donde la doctrina pide 1-1-5 + 1-1-5 + 1-2-5)."""
    fase = str(p.get("fase", 2))
    esperado = publicacion_num(env, "conjuntos_fase%s" % fase)
    tok = TOKEN_FASE.get(fase, "")
    vistos = {}
    for r, cj in _ventas_base(env, ctx["pk"]):
        camp = (r.get("campana") or "").strip()
        if tok not in camp.upper() or num(r.get("spend_usd"), 0) <= 0:
            continue
        vistos.setdefault(camp, set()).add(cj)
    if not vistos:
        return True, "sin campañas de fase %s con gasto" % fase
    total = sum(len(v) for v in vistos.values())
    que = "%d conjunto(s) en %d campaña(s) · doctrina: %g conjuntos (%s)" % (
        total, len(vistos), esperado or 0,
        " + ".join(r.get("estructura", "") for r in env.csv("_PARAMETROS_PUBLICACION.csv")
                   if r.get("fase") == fase and r.get("estado") == "VIGENTE"))
    return (esperado is None) or total <= esperado, que


def _ev_todos(p, ctx, env):
    obs = []
    ok_total = True
    for sub in p.get("de", []):
        ok, o = evaluar(sub, ctx, env)
        obs.append(("✓" if ok else "✗" if ok is False else "?") + " " + o)
        if ok is not True:
            ok_total = False if ok is False else (ok_total if ok_total is False else None)
    return ok_total, " | ".join(obs)


def _ev_alguno(p, ctx, env):
    obs = []
    for sub in p.get("de", []):
        ok, o = evaluar(sub, ctx, env)
        if ok:
            return True, o
        obs.append(o)
    return False, " | ".join(obs)


def _ev_no(p, ctx, env):
    ok, o = evaluar(p["de"], ctx, env)
    return (None if ok is None else (not ok)), o


_EVALUADORES = {
    "csv": _ev_csv, "csv_campo": _ev_csv_campo, "archivo": _ev_archivo, "glob": _ev_glob,
    "json": _ev_json, "script": _ev_script, "decision": _ev_decision,
    "decisiones_json": _ev_decisiones_json, "data_fresca": _ev_data_fresca, "eventos": _ev_eventos,
    "angulo_ganador": _ev_angulo_ganador, "concepto_2de2": _ev_concepto_2de2,
    "estructura_publicada": _ev_estructura_publicada,
    "todos": _ev_todos, "alguno": _ev_alguno, "no": _ev_no,
}


# ─────────────────────────────────────────────────────────────────────────────
# 3 · EL RECORRIDO: fase → nodos → nodo actual
# ─────────────────────────────────────────────────────────────────────────────

def cargar_flujo(env):
    ruta = env.ruta(FLUJO_DECLARADO)
    if not os.path.exists(ruta):
        ruta = os.path.join(BASE_REAL, FLUJO_DECLARADO)   # el fixture no necesita copiar el grafo
    with io.open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def contexto(prod, env):
    cuenta_raw = (prod.get("cuenta_alias") or "").strip()
    return _Ctx({
        "pk": prod["producto_key"],
        "slug": prod.get("slug_carpeta") or prod["producto_key"],
        "carpeta_transcripciones": prod.get("carpeta_transcripciones") or prod["producto_key"],
        "carpeta_media": prod.get("carpeta_media") or ("MEDIA_" + prod["producto_key"]),
        "cuenta": norm(cuenta_raw),
        "cuenta_alias": cuenta_raw,
        "page_id": (prod.get("page_id") or "").strip(),
        "hoy": env.hoy.isoformat(),
    })


def _lista(pred_list, ctx, env, con_dueno=True):
    out = []
    for req in pred_list or []:
        ok, obs = evaluar(req["predicado"], ctx, env)
        item = {"dato": fmt(req.get("dato", ""), ctx), "ok": ok, "observado": obs}
        if con_dueno:
            item["dueno"] = req.get("dueno", "")
            item["regla"] = req.get("regla", "")
        out.append(item)
    return out


def _ejecutor_texto(ej, ctx):
    t = ej.get("tipo")
    if t == "subagente":
        return "subagente `%s` (Task, subagent_type=%s)" % (ej["name"], ej["name"])
    if t == "skill":
        return "skill `%s`" % ej["name"]
    if t == "script":
        return "`" + " ".join(fmt(ej["cmd"], ctx)) + "`"
    if t == "operador":
        return "operador"
    if t == "mcp":
        return "MCP con confirmación del operador por orden"
    return t or "?"


def nodos_de_fase(flujo, fase):
    """Los nodos propios de la fase + el ciclo post-lanzamiento, con ids prefijados."""
    nodos = list(fase.get("nodos", []))
    if fase.get("ciclo", True):
        for n in flujo.get("ciclo", []):
            m = dict(n)
            m["id"] = "%s.%s" % (fase["id"], n["id"])
            m["ciclo"] = True
            nodos.append(m)
    return nodos


def situar(prod, flujo, env):
    """El corazón: dónde está el producto, evaluado sobre la data y nada más."""
    ctx = contexto(prod, env)
    pk = ctx["pk"]
    res = {"producto_key": pk, "nombre": prod.get("nombre_display") or pk,
           "estado_producto": (prod.get("estado") or "").strip(), "cuenta": ctx["cuenta_alias"],
           "fase_csv": (prod.get("fase") or "").strip(), "evaluado_el": env.hoy.isoformat()}

    # -- excepciones declaradas (PAUSADO, etc.) -------------------------------
    for ex in flujo.get("excepciones", []):
        ok, obs = evaluar(ex["si"], ctx, env)
        if ok:
            res.update({"fase": ex["nodo"], "fase_titulo": ex.get("titulo", ex["nodo"]),
                        "nodo_actual": ex["nodo"], "estado": "EXCEPCION",
                        "mensaje": fmt(ex.get("mensaje", ""), ctx), "observado": obs,
                        "ejecutor": "operador", "bloqueantes": [], "nodos": [], "avisos": [],
                        "avance": None, "ordenes": []})
            return res

    # -- la fase: la más alta cuyo gate de ENTRADA pasa, en orden ------------
    fases = flujo["fases"]
    fase_actual = fases[0]
    entradas = []
    for f in fases[1:]:
        ok, obs = evaluar(f["entrada"]["gate"], ctx, env)
        entradas.append({"fase": f["id"], "ok": ok, "observado": obs,
                         "regla": f["entrada"].get("regla", "")})
        if ok:
            fase_actual = f
        else:
            break

    # Si la fase alcanzada tiene declarado reingreso y hay un evento REINGRESO_F1 activo:
    reingreso_activo = None
    if fase_actual.get("reingreso") and fase_actual["id"] != "F1":
        evs_reingreso = [e for e in env.csv("_EVENTOS.csv")
                         if (e.get("producto_key") or "").strip() == pk
                         and (e.get("evento") or "").strip() in ("REINGRESO_F1", "FATIGA_ANGULO")]
        if evs_reingreso:
            evs_reingreso.sort(key=lambda x: str(x.get("fecha") or ""), reverse=True)
            ult_reingreso = evs_reingreso[0]
            fecha_reingreso = str(ult_reingreso.get("fecha") or "")
            lanzamientos_post = [e for e in env.csv("_EVENTOS.csv")
                                 if (e.get("producto_key") or "").strip() == pk
                                 and (e.get("evento") or "").strip() in ("LANZAMIENTO", "LANZAMIENTO_TEST")
                                 and str(e.get("fecha") or "") > fecha_reingreso]
            if not lanzamientos_post:
                dest_id = fase_actual["reingreso"].get("a", "F1")
                reingreso_activo = {
                    "desde": fase_actual["id"],
                    "a": dest_id,
                    "fecha": fecha_reingreso,
                    "motivo": ult_reingreso.get("motivo", ""),
                    "regla": fase_actual["reingreso"].get("regla", ""),
                    "angulos_excluidos": _angulos_probados(env, pk)
                }
                fase_actual = next((f for f in fases if f["id"] == dest_id), fases[0])

    res["fase"] = fase_actual["id"]
    res["fase_titulo"] = fase_actual.get("titulo", fase_actual["id"])
    res["entradas"] = entradas
    res["reingreso_activo"] = reingreso_activo

    # -- los nodos de la fase: cumplido / pendiente ---------------------------
    nodos_out, actual = [], None
    for n in nodos_de_fase(flujo, fase_actual):
        if n.get("ciclo") and actual is not None:
            # el ciclo diario recién aplica cuando la fase está lanzada: antes no hay nada que
            # recolectar ni decidir para este producto, y evaluarlo mentiría con un ✓ vacío
            nodos_out.append({"id": n["id"], "titulo": fmt(n.get("titulo", n["id"]), ctx), "ciclo": True,
                              "ejecutor": _ejecutor_texto(n.get("ejecutor", {}), ctx),
                              "ejecutor_tipo": (n.get("ejecutor") or {}).get("tipo"), "como": "",
                              "secuencia": [], "produce": [], "cumplido": False, "estado": "NO_APLICA",
                              "avisos": []})
            continue
        produce = _lista(n.get("produce") or n.get("requiere"), ctx, env, con_dueno=True)
        cumplido = bool(produce) and all(x["ok"] for x in produce)
        item = {"id": n["id"], "titulo": fmt(n.get("titulo", n["id"]), ctx), "ciclo": n.get("ciclo", False),
                "ejecutor": _ejecutor_texto(n.get("ejecutor", {}), ctx),
                "ejecutor_tipo": (n.get("ejecutor") or {}).get("tipo"),
                "como": fmt(n.get("como", ""), ctx), "secuencia": n.get("secuencia", []),
                "produce": produce, "cumplido": cumplido, "estado": "CUMPLIDO" if cumplido else "PENDIENTE"}
        if not cumplido and actual is None:
            actual = item
            if n.get("produce"):
                item["requiere"] = _lista(n.get("requiere"), ctx, env)
            else:
                # nodo de operador sin `produce`: lo que se le pide es lo mismo que lo cumple
                item["requiere"] = produce
                item["requiere_es_produce"] = True
            bloq = [r for r in item["requiere"] if r["ok"] is False]
            item["estado"] = "BLOQUEADO" if bloq else "LISTO_PARA_EJECUTAR"
        elif cumplido and actual is not None and not n.get("ciclo"):
            item["fuera_de_orden"] = True
        avisos = _lista(n.get("avisos"), ctx, env)
        item["avisos"] = [a for a in avisos if a["ok"]]
        nodos_out.append(item)
    res["nodos"] = nodos_out

    if actual is None:      # todo cumplido: el producto está en ciclo y al día
        ultimo = nodos_out[-1] if nodos_out else None
        res.update({"nodo_actual": ultimo["id"] if ultimo else None, "estado": "AL_DIA",
                    "ejecutor": "—", "bloqueantes": []})
    else:
        res.update({"nodo_actual": actual["id"], "estado": actual["estado"],
                    "ejecutor": actual["ejecutor"], "como": actual["como"],
                    "bloqueantes": [r for r in actual.get("requiere", []) if r["ok"] is False],
                    "falta_para_cumplir": [x for x in actual["produce"] if not x["ok"]]})

    # -- avance a la fase siguiente -------------------------------------------
    salida = fase_actual.get("salida")
    if salida:
        ok, obs = evaluar(salida["gate"], ctx, env)
        res["avance"] = {"a": salida["a"], "ok": ok, "observado": obs, "regla": salida.get("regla", "")}
    else:
        res["avance"] = None

    # -- reingreso por fatiga -------------------------------------------------
    reingreso = fase_actual.get("reingreso")
    if reingreso:
        ok_r, obs_r = evaluar(reingreso["gate"], ctx, env)
        res["reingreso"] = {"a": reingreso["a"], "ok": ok_r, "observado": obs_r,
                            "regla": reingreso.get("regla", ""),
                            "angulos_excluidos": _angulos_probados(env, pk)}
    else:
        res["reingreso"] = None

    # -- avisos globales: objetos de fases posteriores sin gate, etc. ----------
    avisos = []
    for n in nodos_out:
        for a in n["avisos"]:
            avisos.append("%s: %s — %s" % (n["id"], a["dato"], a["observado"]))
    idx = [f["id"] for f in fases].index(fase_actual["id"])
    for f in fases[idx + 1:]:
        for n in f.get("nodos", []):
            for x in _lista(n.get("produce"), ctx, env):
                if x["ok"]:
                    avisos.append("%s: existe «%s» (%s) sin haber pasado el gate de entrada a %s"
                                  % (n["id"], x["dato"], x["observado"], f["id"]))
    res["avisos"] = avisos

    # -- las órdenes del motor, para que la vista las muestre junto al nodo ----
    celdas, _ = env.celdas(pk)
    res["ordenes"] = [{"celda": c["celda"], "estado": c["estado"], "accion": c.get("accion_sugerida", ""),
                       "ventas": c.get("ventas"), "cpa_real_q": c.get("cpa_real_q")}
                      for c in celdas if c.get("estado") != "SEGUIR_MIDIENDO"]
    res["motor"] = {"generado": env.motor().get("generado"), "datos_hasta": env.motor().get("datos_hasta"),
                    "rezago_dias": env.motor().get("rezago_dias"),
                    "seguir_midiendo": sum(1 for c in celdas if c.get("estado") == "SEGUIR_MIDIENDO")}
    return res


def gate_entrada(producto_key, fase, env=None):
    """¿Está cumplido el gate de ENTRADA a `fase` (1/2/3 o "F1"/"F2"/"F3") para `producto_key`?

    EL DUEÑO ÚNICO de esta pregunta: la evalúa exactamente como `situar()` evalúa `entradas`,
    sobre el mismo `evaluar()`/`Entorno`, pero sin recorrer nodos ni escribir nada — a
    diferencia de `correr()`/`escribir_estado()`, que sí tocan `_ESTADO_FLUJO.csv` y
    `_EVENTOS.csv`, esta función es SOLO LECTURA. La usan gen_publicacion.py y
    registrar_evento.py para negar (o exigir `--excepcion`) una acción cuyo gate de fase no
    se cumplió: las fases se abren por el gate declarado en DOCTRINA/FLUJO.json, nunca por
    decisión del operador o del modelo.

    Una fase sin gate de entrada (F1, la primera) está siempre cumplida.
    Devuelve (ok: bool, observado: str)."""
    env = env or Entorno()
    flujo = cargar_flujo(env)
    fase_id = str(fase) if str(fase).upper().startswith("F") else "F%s" % fase
    f = next((x for x in flujo["fases"] if x["id"] == fase_id), None)
    if f is None:
        return False, "'%s' no es una fase de %s" % (fase_id, FLUJO_DECLARADO)
    entrada = f.get("entrada") or {}
    gate = entrada.get("gate")
    if not gate:
        return True, "%s no declara gate de entrada" % fase_id
    prod = next((p for p in env.csv("_DIM_PRODUCTOS.csv")
                 if (p.get("producto_key") or "").strip() == producto_key), None)
    if prod is None:
        return False, "'%s' no tiene fila en _DIM_PRODUCTOS.csv (invariante 10)" % producto_key
    ctx = contexto(prod, env)
    ok, obs = evaluar(gate, ctx, env)
    return bool(ok), obs


# ─────────────────────────────────────────────────────────────────────────────
# 4 · ESTADO EN DISCO: _ESTADO_FLUJO.csv + evento de transición
# ─────────────────────────────────────────────────────────────────────────────

def escribir_estado(resultados, env, registrar_eventos=True):
    ruta = env.prod("_ESTADO_FLUJO.csv")
    previo = {r["producto_key"]: r for r in env.csv("_ESTADO_FLUJO.csv")}
    filas, transiciones = [], []
    for r in resultados:
        pk = r["producto_key"]
        ant = previo.get(pk)
        misma = ant and ant.get("fase") == r["fase"] and ant.get("nodo_actual") == (r.get("nodo_actual") or "")
        desde = ant["desde"] if misma and ant.get("desde") else env.hoy.isoformat()
        filas.append({
            "producto_key": pk, "fase": r["fase"], "nodo_actual": r.get("nodo_actual") or "",
            "estado": r.get("estado", ""), "desde": desde,
            "bloqueantes": len(r.get("bloqueantes") or []),
            "siguiente_ejecutor": (r.get("ejecutor") or "").replace("`", "")[:60],
            "evaluado_el": env.hoy.isoformat(),
        })
        if ant and not misma:
            transiciones.append((pk, ant, r))
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_ESTADO)
        w.writeheader()
        w.writerows(filas)
    env._csv.pop("_ESTADO_FLUJO.csv", None)

    if registrar_eventos and transiciones:
        ruta_ev = env.prod("_EVENTOS.csv")
        campos = None
        with io.open(ruta_ev, encoding="utf-8-sig", newline="") as fh:
            campos = next(csv.reader(fh))
        with io.open(ruta_ev, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            for pk, ant, r in transiciones:
                w.writerow({
                    "fecha": env.hoy.isoformat(), "producto_key": pk,
                    "cuenta_alias": r.get("cuenta") or "", "campana_clave": "*", "conjunto_meta": "*",
                    "evento": EVENTO_TRANSICION,
                    "valor_antes": "%s / %s" % (ant.get("fase"), ant.get("nodo_actual")),
                    "valor_despues": "%s / %s" % (r["fase"], r.get("nodo_actual")),
                    "motivo": "flujo.py: el nodo actual cambió al evaluar la data del %s" % env.hoy.isoformat(),
                    "fuente_decision": "Ads/_TOOLS/flujo.py",
                })
    return transiciones


# ─────────────────────────────────────────────────────────────────────────────
# 5 · VALIDACIÓN DEL GRAFO DECLARADO
# ─────────────────────────────────────────────────────────────────────────────

def _nombres_agentes():
    nombres = set()
    for ruta in _glob.glob(os.path.join(BASE_REAL, ".claude", "agents", "*.md")):
        with io.open(ruta, encoding="utf-8") as fh:
            for linea in fh:
                m = re.match(r"^name:\s*(\S+)", linea)
                if m:
                    nombres.add(m.group(1))
                    break
    return nombres


def _validar_predicado(p, donde, problemas, env):
    if not isinstance(p, dict) or "tipo" not in p:
        problemas.append("%s: predicado sin `tipo`" % donde)
        return
    t = p["tipo"]
    if t not in TIPOS:
        problemas.append("%s: tipo `%s` no está en el vocabulario" % (donde, t))
        return
    if t in ("csv", "csv_campo", "data_fresca"):
        if not os.path.exists(env.prod(p.get("csv", ""))):
            problemas.append("%s: el CSV `%s` no existe" % (donde, p.get("csv")))
    if t == "script":
        cmd = p.get("cmd")
        if not isinstance(cmd, list) or not cmd:
            problemas.append("%s: `cmd` debe ser una lista" % donde)
        else:
            rutas = [a for a in cmd if a.endswith(".py")]
            for r in rutas:
                if not os.path.exists(env.ruta(r)):
                    problemas.append("%s: el script `%s` no existe" % (donde, r))
    for k, v in p.items():
        if isinstance(v, str) and v.startswith("@param:") and v[7:] not in env.params():
            problemas.append("%s: `%s` no existe en _PARAMETROS_DECISION.csv" % (donde, v))
        if isinstance(v, str) and v.startswith("@publicacion:") and publicacion_num(env, v[13:]) is None:
            problemas.append("%s: `%s` no se puede derivar de _PARAMETROS_PUBLICACION.csv" % (donde, v))
    if t in ("todos", "alguno"):
        for i, s in enumerate(p.get("de", [])):
            _validar_predicado(s, "%s.de[%d]" % (donde, i), problemas, env)
    if t == "no":
        _validar_predicado(p.get("de"), donde + ".de", problemas, env)


def validar(flujo, env):
    problemas = []
    if flujo.get("schema") != "flujo/1":
        problemas.append("schema debe ser flujo/1")
    agentes = _nombres_agentes()
    skills = {d for d in os.listdir(os.path.join(BASE_REAL, ".claude", "skills"))}
    ids = set()

    def val_nodo(n, donde):
        nid = n.get("id")
        if not nid:
            problemas.append("%s: nodo sin id" % donde)
            return
        if nid in ids:
            problemas.append("%s: id `%s` repetido" % (donde, nid))
        ids.add(nid)
        ej = n.get("ejecutor") or {}
        t = ej.get("tipo")
        if t not in ("subagente", "skill", "script", "operador", "mcp"):
            problemas.append("%s: ejecutor.tipo `%s` inválido" % (nid, t))
        if t == "subagente" and ej.get("name") not in agentes:
            problemas.append("%s: el subagente `%s` no existe en .claude/agents/" % (nid, ej.get("name")))
        if t == "skill" and ej.get("name") not in skills:
            problemas.append("%s: la skill `%s` no existe en .claude/skills/" % (nid, ej.get("name")))
        if t == "script":
            for a in ej.get("cmd", []):
                if a.endswith(".py") and not os.path.exists(env.ruta(a)):
                    problemas.append("%s: el script `%s` no existe" % (nid, a))
        if not n.get("produce") and not n.get("requiere"):
            problemas.append("%s: sin `produce` ni `requiere` — nunca se podría dar por cumplido" % nid)
        for lista in ("requiere", "produce", "avisos"):
            for i, req in enumerate(n.get(lista) or []):
                if "predicado" not in req:
                    problemas.append("%s.%s[%d]: sin `predicado`" % (nid, lista, i))
                else:
                    _validar_predicado(req["predicado"], "%s.%s[%d]" % (nid, lista, i), problemas, env)
        for s in n.get("secuencia", []):
            if s not in agentes and s not in skills and not s.startswith("operador") and not s.startswith("Ads/"):
                problemas.append("%s: la secuencia cita `%s`, que no es agente ni skill" % (nid, s))

    for f in flujo.get("fases", []):
        if f is not flujo["fases"][0]:
            if not (f.get("entrada") or {}).get("gate"):
                problemas.append("fase %s: sin gate de entrada" % f.get("id"))
            else:
                _validar_predicado(f["entrada"]["gate"], "fase %s.entrada" % f["id"], problemas, env)
        if f.get("salida"):
            _validar_predicado(f["salida"]["gate"], "fase %s.salida" % f["id"], problemas, env)
            if f["salida"].get("a") not in [x["id"] for x in flujo["fases"]]:
                problemas.append("fase %s: salida apunta a `%s`, que no existe" % (f["id"], f["salida"].get("a")))
        if f.get("reingreso"):
            _validar_predicado(f["reingreso"]["gate"], "fase %s.reingreso" % f["id"], problemas, env)
            if f["reingreso"].get("a") not in [x["id"] for x in flujo["fases"]]:
                problemas.append("fase %s: reingreso apunta a `%s`, que no existe" % (f["id"], f["reingreso"].get("a")))
        for n in f.get("nodos", []):
            val_nodo(n, "fase %s" % f["id"])
    for n in flujo.get("ciclo", []):
        val_nodo(n, "ciclo")
    for ex in flujo.get("excepciones", []):
        _validar_predicado(ex.get("si"), "excepcion %s" % ex.get("nodo"), problemas, env)
    return problemas


# ─────────────────────────────────────────────────────────────────────────────
# 6 · SALIDAS: consola, JSON, mermaid
# ─────────────────────────────────────────────────────────────────────────────

MARCA = {"CUMPLIDO": "✓", "PENDIENTE": "·", "BLOQUEADO": "✗", "LISTO_PARA_EJECUTAR": "▶", "NO_APLICA": "—"}


def imprimir(r):
    print("=" * 96)
    print(" %s · %s · %s · %s" % (r["producto_key"], r["nombre"], r["estado_producto"], r.get("cuenta") or "sin cuenta"))
    if r["estado"] == "EXCEPCION":
        print("   %s — %s" % (r["nodo_actual"], r.get("mensaje")))
        print("   observado: %s" % r.get("observado"))
        return
    print(" FASE %s — %s" % (r["fase"], r["fase_titulo"]))
    for e in r.get("entradas", []):
        print("   entrada a %s: %s %s" % (e["fase"], "✓" if e["ok"] else "✗", e["observado"][:120]))
    print("-" * 96)
    for n in r["nodos"]:
        m = MARCA.get(n["estado"], "·")
        actual = " ← NODO ACTUAL" if n["id"] == r["nodo_actual"] and r["estado"] != "AL_DIA" else ""
        extra = "  (fuera de orden: ya existe)" if n.get("fuera_de_orden") else ""
        print("  %s %-24s %s%s%s" % (m, n["id"], n["titulo"][:60], actual, extra))
        if n["id"] == r["nodo_actual"] and r["estado"] != "AL_DIA":
            for x in ([] if n.get("requiere_es_produce") else n["produce"]):
                if not x["ok"]:
                    print("        falta  %-34s %s" % (x["dato"][:34], x["observado"][:90]))
                    if x.get("dueno"):
                        print("               lo produce: %s%s" % (x["dueno"], ("  (%s)" % x["regla"]) if x.get("regla") else ""))
            for x in n.get("requiere", []):
                if x["ok"] is False:
                    print("        BLOQUEA %-33s %s" % (x["dato"][:33], x["observado"][:90]))
                    print("               lo produce: %s%s" % (x["dueno"], ("  (%s)" % x["regla"]) if x.get("regla") else ""))
            print("        ejecutar: %s" % n["ejecutor"])
            if n.get("como"):
                print("        cómo: %s" % n["como"][:140])
            if n.get("secuencia"):
                print("        secuencia: %s" % " → ".join(n["secuencia"]))
        elif n["estado"] == "PENDIENTE" and not n.get("ciclo"):
            for x in n["produce"]:
                if not x["ok"]:
                    print("        falta  %-34s %s" % (x["dato"][:34], x["observado"][:90]))
        for a in n["avisos"]:
            print("        ⚠ %s — %s" % (a["dato"], a["observado"][:100]))
    if r["estado"] == "AL_DIA":
        print("  ▶ todo cumplido: el producto está en ciclo y al día")
    if r.get("avance"):
        a = r["avance"]
        print("-" * 96)
        print("  PARA PASAR A %s: %s %s" % (a["a"], "✓ LISTO" if a["ok"] else "✗", a["observado"][:110]))
        if a.get("regla"):
            print("     regla: %s" % a["regla"])
    if r.get("ordenes"):
        print("-" * 96)
        m = r.get("motor", {})
        print("  ÓRDENES DEL MOTOR (data hasta %s, rezago %s d · %d en SEGUIR_MIDIENDO):"
              % (m.get("datos_hasta"), m.get("rezago_dias"), m.get("seguir_midiendo", 0)))
        for o in r["ordenes"]:
            print("     [%s] %-28s %s" % (o["estado"], o["celda"][:28], (o["accion"] or "")[:80]))
    if r["avisos"]:
        print("-" * 96)
        for a in r["avisos"]:
            print("  ⚠ %s" % a[:160])


def mermaid(flujo):
    L = ["flowchart TD"]
    for f in flujo["fases"]:
        L.append("  subgraph %s[\"%s\"]" % (f["id"], f.get("titulo", f["id"])))
        prev = None
        for n in nodos_de_fase(flujo, f):
            nid = n["id"].replace(".", "_")
            L.append("    %s[\"%s\"]" % (nid, n.get("titulo", n["id"]).replace('"', "'")[:38]))
            if prev:
                L.append("    %s --> %s" % (prev, nid))
            prev = nid
        if f.get("ciclo", True) and flujo.get("ciclo"):
            primero = ("%s.%s" % (f["id"], flujo["ciclo"][0]["id"])).replace(".", "_")
            L.append("    %s -. cada día .-> %s" % (prev, primero))
        L.append("  end")
    for f in flujo["fases"]:
        s = f.get("salida")
        if s:
            L.append("  %s -- \"%s\" --> %s" % (f["id"], s.get("regla", "gate").replace('"', "'")[:40], s["a"]))
        r = f.get("reingreso")
        if r:
            L.append("  %s -. \"%s\" .-> %s" % (f["id"], r.get("regla", "reingreso").replace('"', "'")[:35], r["a"]))
    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
# 7 · MAIN
# ─────────────────────────────────────────────────────────────────────────────

def correr(env, productos=None):
    flujo = cargar_flujo(env)
    dim = env.csv("_DIM_PRODUCTOS.csv")
    if productos:
        dim = [p for p in dim if p["producto_key"] in productos]
    return flujo, [situar(p, flujo, env) for p in dim if (p.get("producto_key") or "").strip()]


def main():
    ap = argparse.ArgumentParser(description="El flujo declarado del sistema")
    ap.add_argument("producto", nargs="?", help="producto_key de _DIM_PRODUCTOS.csv")
    ap.add_argument("--todo", action="store_true", help="todos los productos (solo lectura salvo --escribir)")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    ap.add_argument("--validar", action="store_true", help="valida DOCTRINA/FLUJO.json contra el disco")
    ap.add_argument("--grafo", action="store_true", help="imprime el grafo en mermaid")
    ap.add_argument("--base", help="raíz alternativa (fixture de test)")
    ap.add_argument("--hoy", help="fecha de evaluación YYYY-MM-DD (replay)")
    ap.add_argument("--sin-scripts", action="store_true", help="no corre predicados `script`")
    ap.add_argument("--escribir", action="store_true",
                    help="con --todo, persiste _ESTADO_FLUJO.csv/_EVENTOS.csv/_FLUJO.json/FLUJO.html "
                         "(por defecto --todo tambien solo lee)")
    ap.add_argument("--silencioso", action="store_true")
    a = ap.parse_args()

    env = Entorno(base=a.base, hoy=fecha(a.hoy) if a.hoy else None, sin_scripts=a.sin_scripts)

    if a.validar:
        flujo = cargar_flujo(env)
        problemas = validar(flujo, env)
        n = sum(len(nodos_de_fase(flujo, f)) for f in flujo["fases"])
        if problemas:
            print("FLUJO INVÁLIDO — %s\n  · %s" % (FLUJO_DECLARADO, "\n  · ".join(problemas)))
            return 1
        print("%s válido: %d fases, %d nodos, %d excepciones. Cada ejecutor y cada archivo citado existen."
              % (FLUJO_DECLARADO, len(flujo["fases"]), n, len(flujo.get("excepciones", []))))
        return 0

    if a.grafo:
        print(mermaid(cargar_flujo(env)))
        return 0

    if not a.producto and not a.todo:
        ap.print_help()
        return 2

    flujo, resultados = correr(env, [a.producto] if a.producto else None)
    if a.producto and not resultados:
        print("'%s' no tiene fila en _DIM_PRODUCTOS.csv (invariante 10: la llave es producto_key)." % a.producto)
        return 1

    if a.json and not a.todo:
        print(json.dumps(resultados[0] if a.producto else resultados, ensure_ascii=False, indent=2))
        return 0

    if not a.silencioso:
        for r in resultados:
            imprimir(r)
        print("=" * 96)

    if a.todo:
        transiciones = escribir_estado(resultados, env) if a.escribir else []
        salida = {"generado": env.hoy.isoformat(), "flujo_version": flujo.get("version"),
                  "grafo_mermaid": mermaid(flujo),
                  "fases": [{"id": f["id"], "titulo": f.get("titulo", f["id"]), "mide": f.get("mide", "")}
                            for f in flujo["fases"]],
                  "productos": resultados}
        if a.escribir:
            with io.open(env.prod("_FLUJO.json"), "w", encoding="utf-8") as fh:
                json.dump(salida, fh, ensure_ascii=False, indent=2)
            try:
                if TOOLS not in sys.path:
                    sys.path.insert(0, TOOLS)
                from flujo_html import HTML
                vistas = env.ruta("VISTAS")
                if not os.path.isdir(vistas):
                    os.makedirs(vistas)
                with io.open(os.path.join(vistas, "FLUJO.html"), "w", encoding="utf-8") as fh:
                    fh.write(HTML(salida))
                vista = "VISTAS/FLUJO.html"
            except Exception as e:      # la vista caída no frena el estado: se dice
                vista = "(vista no escrita: %s)" % e
            print("escrito PRODUCTOS/_FLUJO.json · PRODUCTOS/_ESTADO_FLUJO.csv · %s · %d transición(es) registradas"
                  % (vista, len(transiciones)))
        if a.json:
            print(json.dumps(salida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
