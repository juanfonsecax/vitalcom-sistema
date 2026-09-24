#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""venta_identidad.py — identidad estable de una fila de _FACT_VENTAS.csv (P1-cimientos T2b).

Dueño único de `asignar_venta_uids()`. Vive en su propio módulo, SIN dependencias más allá de la
librería estándar, a propósito: `Ads/_TOOLS/mapear_ad_id_hist.py` (que escribe
`_MAPA_AD_ID_HIST.csv`) y `db/cargar.py` (que lo lee, corriendo en el venv de `psycopg`, que no
tiene `pandas`) necesitan la MISMA función sin arrastrar la cadena de imports de
`mapear_ad_id_hist.py` -> `bajar_meta_insights.py` -> `ingerir_meta.py` -> `pandas` (ausente en
ese venv). Separarla acá es lo que evita esa cadena, no una copia paralela.

POR QUÉ EXISTE. El JOIN histórico original entre `_MAPA_AD_ID_HIST.csv` y `_FACT_VENTAS.csv` usaba
(ventana_ini, cuenta_alias, conjunto, anuncio) + orden de aparición (FIFO): esa llave se repite en
150 grupos del mapa real, así que la correspondencia dependía de que el ORDEN de _FACT_VENTAS.csv
no cambiara nunca entre la corrida que generó el mapa y la corrida que lo consume. `venta_uid`
reemplaza esa dependencia posicional con un hash del CONTENIDO completo de la fila (todas sus
columnas, en el orden real del CSV): sobrevive a un reordenamiento del archivo porque no depende
de la posición.

Único caso que un hash de contenido no puede distinguir por sí solo: duplicados EXACTOS
byte-a-byte (mismas 20 columnas). Se comprobó sobre `_FACT_VENTAS.csv` real: existen 9 grupos así
(22 filas en total, de 3407). Para esos casos se agrega un contador de ocurrencia (0, 1, 2...)
según el orden de aparición en el archivo que se está procesando. Como el contenido es idéntico,
la fila y su(s) gemela(s) exactas resuelven al MISMO ad_id/método de todos modos (el emparejamiento
de `mapear_ad_id_hist.mapear_fila()` depende solo de esas mismas columnas), así que el orden en que
se reparte el sufijo de ocurrencia entre las copias físicas no cambia la atribución resultante —
es lo que prueba `test_asignar_venta_uids_estable_ante_reordenamiento` en
`Ads/_TOOLS/test_mapear_ad_id_hist.py` y `db/test_db.py`.
"""
import hashlib


def asignar_venta_uids(filas):
    """[venta_uid, ...] en el mismo orden que `filas` (lista de dicts homogéneos, p.ej. de
    csv.DictReader sobre _FACT_VENTAS.csv: todas las filas con las mismas columnas). Determinista:
    mismo contenido -> mismo hash, sin importar el orden de `filas` (salvo el sufijo de ocurrencia
    entre duplicados byte-a-byte, ver el docstring del módulo)."""
    if not filas:
        return []
    columnas = list(filas[0].keys())
    contador = {}
    uids = []
    for fila in filas:
        base = "\x1f".join((fila.get(c) or "") for c in columnas)
        h = hashlib.sha256(base.encode("utf-8")).hexdigest()
        n = contador.get(h, 0)
        contador[h] = n + 1
        uids.append(h if n == 0 else "%s-%d" % (h, n))
    return uids
