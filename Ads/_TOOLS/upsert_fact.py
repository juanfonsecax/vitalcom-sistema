#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upsert_fact.py — UPSERT idempotente sobre un CSV de hechos, por llave natural.

POR QUE EXISTE (22-sep-2026, g07-cimientos T1): `bajar_meta_insights.py` e
`ingerir_lucidsales.py` eran los dos append-only con dedupe por llave. Un día que llega
PARCIAL (LucidSales corta el gasto a mitad de día — medido en vivo el 06/14/15/16/20-sep:
cada anuncio quedó con 0.65-0.75 del gasto real de Meta ese día) queda congelado para
siempre: la corrida siguiente encuentra la misma llave y la descarta como "ya cargado",
nunca la corrige. La doctrina de SETTLEMENT WINDOW (re-pull nocturno de los últimos N días,
reemplazando por llave) necesita que una llave YA existente se REEMPLACE, no que se ignore.

Un solo helper para los dos ingestores — no una copia del mismo bucle en cada script
(regla de CLAUDE.md: "un dato, un dueño"; acá aplica a la MECÁNICA de escritura).

CONTRATO
  upsert(path, cols, key, filas_nuevas, bkdir) hace:
    1. Lee el CSV existente (si existe) y completa cada fila vieja a `cols` (ver
       `leer_migrado`): una columna nueva en el esquema (ej. `ad_id`) no rompe la
       lectura de filas escritas antes de que existiera — quedan con "" ahí, nunca
       con un valor inventado.
    2. Indexa las filas (viejas y nuevas) por su llave natural. `key` es una tupla de
       nombres de columna (igualdad literal) o una función `fila -> tupla` cuando la
       llave necesita lógica (ej. "ad_id si lo hay, si no la firma").
    3. Cada fila nueva REEMPLAZA a la existente con la misma llave; una llave que no
       estaba se agrega. Es upsert real, no "append si no está".
    4. Reescribe el archivo COMPLETO. Es la única forma de que un cambio de header
       (columna nueva) y un reemplazo de fila convivan en un CSV — un CSV no admite
       dos esquemas de columnas a la vez, así que un `open(..., "a")` con el header
       viejo ya en disco corrompería el archivo en cuanto cambia `cols`.
    5. Backup previo del archivo COMPLETO en `bkdir` (mismo patrón que los
       ingestores existentes: nunca se pisa sin copia).
  Devuelve (reemplazadas, nuevas, sin_cambio). Reescribir con el mismo contenido dos
  veces seguidas dejo `reemplazadas` en 0 y `sin_cambio` en la cuenta completa — la
  idempotencia se mide por CONTENIDO, no por que el archivo se haya vuelto a escribir.
"""
import csv
import datetime
import os
import shutil

# Ventana de liquidación (T1, 22-sep-2026): cuántos días hacia atrás se re-consultan cada
# noche, reemplazando por llave en vez de solo anexar. 3 días cubre con margen los casos
# medidos de gasto congelado a medio día (nunca más de 1 día de rezago observado) más el
# día de la corrida. Un solo lugar: bajar_meta_insights.py y bajar_lucidsales.py importan
# esta constante en vez de cablear cada uno su propio número.
SETTLEMENT_WINDOW_DIAS = 3


def _texto(v):
    """Normaliza un valor al TEXTO que terminaria escrito en el CSV (csv.writer hace
    str() de cualquier cosa que no sea ya str). Sin esto, una fila recien calculada en
    memoria (con int/float, ej. spend_usd=1.0) nunca es '==' a la misma fila releida del
    disco (que csv.DictReader entrega como str "1.0"), y el UPSERT reportaria una fila
    sin cambios como "reemplazada" en CADA corrida — reescribiendo y respaldando el
    archivo por nada, y rompiendo el check de idempotencia (T1)."""
    if v is None:
        return ""
    return v if isinstance(v, str) else str(v)


def _completar(fila, cols):
    """Fila (vieja o nueva) -> dict con EXACTAMENTE las columnas de `cols`, en texto.

    Una columna que la fila no trae (esquema viejo leído de disco, o un caller que no
    la llena) queda en "" — nunca inventada. Una columna que la fila trae de más
    (una llave temporal calculada por el caller, p.ej.) se descarta acá: el CSV
    escrito nunca lleva columnas fuera de `cols`.
    """
    return {c: _texto(fila.get(c, "")) for c in cols}


def leer_migrado(path, cols):
    """Lee un CSV de hechos y devuelve sus filas ya completadas al esquema `cols` vigente.

    Es la migración de esquema (T1): un archivo escrito antes de agregar una columna
    (ej. `ad_id` en `_FACT_ENTREGA_ANUNCIO.csv`) se lee igual, con esa columna en "".
    """
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    return [_completar(f, cols) for f in filas]


def _clave(fila, key):
    if callable(key):
        return key(fila)
    return tuple(fila.get(k, "") for k in key)


def upsert(path, cols, key, filas_nuevas, bkdir):
    """UPSERT por llave natural `key` sobre el CSV de hechos en `path`.

    `key`: tupla de nombres de columna, o función `fila(dict) -> tupla hasheable`
    cuando la llave no es una igualdad literal de columnas (ver `bajar_meta_insights.py`
    y `ingerir_lucidsales.py` para los dos casos reales).

    Devuelve (reemplazadas, nuevas, sin_cambio). No escribe nada si `filas_nuevas`
    está vacía o si ninguna fila nueva difiere de lo que ya había Y no agrega llaves —
    en ese caso el archivo en disco queda intacto (ni backup ni reescritura de más).
    """
    existentes = leer_migrado(path, cols)
    indice = {_clave(f, key): i for i, f in enumerate(existentes)}
    resultado = list(existentes)
    reemplazadas = nuevas = sin_cambio = 0

    for fila_cruda in filas_nuevas:
        fila = _completar(fila_cruda, cols)
        llave = _clave(fila, key)
        if llave in indice:
            i = indice[llave]
            if resultado[i] == fila:
                sin_cambio += 1
            else:
                reemplazadas += 1
                resultado[i] = fila
        else:
            indice[llave] = len(resultado)
            resultado.append(fila)
            nuevas += 1

    if reemplazadas or nuevas:
        os.makedirs(bkdir, exist_ok=True)
        if os.path.exists(path):
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = os.path.basename(path)
            if nombre.lower().endswith(".csv"):
                nombre = nombre[:-4]
            shutil.copy2(path, os.path.join(bkdir, f"{nombre}_{stamp}.csv"))
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in resultado:
                w.writerow(f)

    return reemplazadas, nuevas, sin_cambio
