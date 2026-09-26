#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""leer.py — API pública de LECTURA de las tablas DB-truth (P3 T5).

POR QUÉ EXISTE. `db/escribir.py` (P3 T2-T4) hizo que la VERDAD de seis tablas viva en
`raw.*`, con el CSV en `PRODUCTOS/` como espejo regenerado — pero hasta T4 los únicos
lectores en producción seguían siendo `Ads/_TOOLS/decidir.py` y el backend de la app
(`app/backend/vitalcom_app/contratos.py`), y ambos leían el ESPEJO CSV directo del disco, no
la base. T5 conecta esos dos lectores a Postgres.

Este módulo NO abre ni cierra la conexión (mismo patrón que `db/escribir.py`): la recibe ya
abierta del llamador. Devuelve exactamente lo que un `csv.DictReader` sobre el espejo daría
hoy — reusa `db/escribir.py:_filas_espejo()` (la misma pieza que ya usa
`verificar_csv_sincronizado()` para comparar sin tocar disco), así que nunca hay una segunda
implementación del mapeo columna-por-columna.

USO:
    con = leer.conectar()
    try:
        filas = leer.filas(con, "producto")                  # list[dict[str, str]]
        payload = leer.decision(con)                          # dict | None
        rutas = leer.materializar(con, ["producto", "venta"], tmp_dir)  # {tabla: ruta_csv}
    finally:
        con.close()
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar as C  # noqa: E402
import escribir as W  # noqa: E402


def conectar(env=None):
    """Misma conexión que `cargar.conectar()` (mismas credenciales, mismo `connect_timeout=10`):
    este módulo no inventa una segunda forma de conectarse a Postgres, solo lee con ella."""
    return C.conectar(env)


def filas(conn, tabla, tenant_id="vitalcom"):
    """Filas de `tabla` para `tenant_id`, EXACTAMENTE como las devolvería `csv.DictReader` sobre
    el espejo CSV de esa tabla hoy (mismas claves, mismo orden de filas) — ver
    `escribir._filas_espejo()`, la pieza compartida con el guardia de drift."""
    _, _, filas_ = W._filas_espejo(conn, tenant_id, tabla)
    return filas_


def decision(conn, tenant_id="vitalcom"):
    """El payload de `_DECISIONES.json` tal cual lo dejó la última corrida de `decidir.py
    --escribir` (orden de claves original), o `None` si nunca se escribió. Delega en
    `escribir.leer_decision_actual()` — ver su docstring sobre por qué lee `raw` verbatim y
    nunca `core.decision` (orden de claves de un JSONB no es determinista)."""
    return W.leer_decision_actual(conn, tenant_id)


def materializar(conn, tablas, out_dir, tenant_id="vitalcom"):
    """Escribe en `out_dir` el espejo CSV de cada tabla de `tablas` (mismo formato byte a byte
    que `escribir._escribir_csv_atomico()`: CRLF, utf-8 sin BOM, header + filas en orden).
    Pensado para lectores que necesitan un ARCHIVO real en disco (p. ej. `decidir.py`, que lee
    con DuckDB `read_csv`), no un dict en memoria — a diferencia de `filas()`.

    Devuelve {tabla: ruta_absoluta_del_csv}."""
    os.makedirs(out_dir, exist_ok=True)
    rutas = {}
    for tabla in tablas:
        archivo, cols, filas_ = W._filas_espejo(conn, tenant_id, tabla)
        destino = os.path.join(out_dir, archivo)
        W._escribir_csv_atomico(destino, cols, filas_)
        rutas[tabla] = destino
    return rutas
