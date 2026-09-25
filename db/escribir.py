#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""escribir.py — capa de escritura a Postgres para las tablas DB-truth (P3 T2).

POR QUÉ EXISTE. P1/T5-T5b construyeron `raw`+`core` en UNA sola dirección: CSV -> Postgres
(`cargar.py`, TRUNCATE + reinsertar completo cada corrida). P3 invierte la dirección para el
subconjunto de `PRODUCTOS/*.csv` que hoy solo escribe un PROGRAMA (nunca el operador a mano) —
ver `db/README.md` "P3 — inventario de escritores", T1: `_FACT_VENTAS.csv`, `_FACT_ENTREGA.csv`,
`_FACT_ENTREGA_ANUNCIO.csv`, `_EVENTOS.csv`, `_DECISIONES.json`, `_ESTADO_FLUJO.csv`,
`_DIM_PRODUCTOS.csv` (`tables.TABLAS_VERDAD_DB` + `_DECISIONES.json` aparte, sin CSV dueño). Para
esos siete, desde T3/T4 la VERDAD vive en `raw.*` y el CSV en `PRODUCTOS/` se vuelve un ESPEJO
regenerado, nunca la fuente.

T2 construye la capa de escritura y la prueba de punta a punta, pero NO conecta ningún llamador
real todavía (`ingerir_*`, `bajar_*`, `flujo.py`, `decidir.py`, `registrar_evento.py`,
`alta_producto.py` siguen escribiendo CSV directo) — eso es T3/T4.

DISEÑO (decidido, odd/tasks/p3-postgres-verdad.md):
  1. La verdad vive en `raw.<tabla>` (filas VERBATIM); `core` se reconstruye ENTERO desde `raw`
     por `nucleo.construir_core()`, en LA MISMA TRANSACCIÓN que la escritura — exactamente lo que
     ya hace `cargar.py`, reusado tal cual (nunca se duplica el enriquecimiento/FK de nucleo.py).
  2. La MECÁNICA de merge (reemplaza por llave, `particion` declara el ámbito completo de un
     re-pull) es la MISMA que `Ads/_TOOLS/upsert_fact.py`, extraída a `upsert_fact.fusionar()` —
     un dato, un dueño de la semántica; acá solo cambia el ALMACÉN (Postgres en vez de un CSV).
  3. Tras un COMMIT exitoso (nunca antes), se regenera el/los espejo(s) CSV/JSON del archivo
     tocado hacia `prod_dir`, ESCRITO ATÓMICO (temp file en el mismo directorio + `os.replace`).
     El formato de cada espejo es BYTE-IDÉNTICO al que ya produce el escritor real de ese archivo
     hoy (CRLF, utf-8 sin BOM, mismo orden de columnas — ver cada función abajo).
  4. Postgres no disponible, o cualquier paso de la transacción falla -> `ErrorEscritura`. NUNCA
     se cae de vuelta a escribir el CSV directo: sería exactamente el defecto que P3 corrige.

USO (todas reciben una conexión psycopg YA ABIERTA — mismo patrón que `cargar.conectar()`; esta
capa nunca abre ni cierra la conexión, esa es responsabilidad del llamador):

    con = cargar.conectar()
    try:
        reemp, nuevas, sc = escribir.upsert(
            con, "venta", filas_nuevas, key=("ventana_ini", "cuenta_alias", "conjunto", "anuncio"),
            prod_dir=PRODUCTOS_DIR)
    finally:
        con.close()
"""
import csv
import datetime
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402
import tables as T  # noqa: E402

sys.path.insert(0, os.path.join(T.BASE_DIR, "Ads", "_TOOLS"))
from upsert_fact import _completar, fusionar, respaldos_dir  # noqa: E402


class ErrorEscritura(RuntimeError):
    """Postgres no disponible, o la transacción de escritura falló (rollback ya aplicado a mano —
    ver `_en_transaccion()`: un `with conn:` de psycopg3 DEJA LA CONEXIÓN CERRADA ante una
    excepción, no solo hace rollback, lo que rompería reusar `conn` para leer el estado o escribir
    la siguiente tabla; por eso acá el rollback es explícito con `conn.rollback()`). Quien reciba
    este error NUNCA debe interpretar esto como \"entonces escribo el CSV a mano\" — ver docstring
    del módulo, punto 4."""


class DriftDetectado(ErrorEscritura):
    """P3 T3 — GUARDIA DE DRIFT: el CSV en disco no es BYTE-IDÉNTICO a lo que la base exportaría
    para esta tabla DB-truth, o esta tabla/tenant NUNCA se importó como verdad (primera corrida,
    ver `raw.raw_import`). Nunca se escribe nada — ni `raw` ni el espejo — hasta resolverlo a
    propósito con `db/cargar.py --tomar-csv <archivo>` (ver `verificar_csv_sincronizado()`)."""


def _en_transaccion(conn, cuerpo, tabla, verbo):
    """Corre `cuerpo(cur)` en una transacción explícita sobre `conn`: COMMIT si no hay error,
    ROLLBACK (con la conexión viva, ver `ErrorEscritura`) y `ErrorEscritura` si lo hay."""
    try:
        with conn.cursor() as cur:
            resultado = cuerpo(cur)
        conn.commit()
        return resultado
    except Exception as exc:
        conn.rollback()
        raise ErrorEscritura(
            "%s sobre raw.%s falló, rollback aplicado (nunca se escribió el CSV): %s"
            % (verbo, tabla, exc)
        ) from exc


def _spec_de(tabla):
    for t, archivo, opcional in T.TABLE_SPECS:
        if t == tabla:
            return archivo, opcional
    raise ValueError("tabla sin fila en tables.TABLE_SPECS: %r" % tabla)


def _cols_de(tabla):
    archivo, opcional = _spec_de(tabla)
    return T.columnas_tabla(tabla, archivo, opcional)


def _exigir_verdad_db(tabla):
    if tabla not in T.TABLAS_VERDAD_DB:
        raise ValueError(
            "%r no es una tabla DB-truth de P3 (ver tables.TABLAS_VERDAD_DB); "
            "escribirla acá pisaría un CSV que el operador sigue editando a mano." % tabla)


def _leer_raw(cur, tenant_id, tabla, cols):
    """Filas actuales de `raw.<tabla>` para `tenant_id`, en su orden real (`ORDER BY id`,
    igual que `exportar.py`), como dicts `columna -> texto`."""
    col_list = ", ".join('"%s"' % c for c in cols)
    cur.execute(
        "SELECT %s FROM raw.%s WHERE tenant_id = %%s ORDER BY id" % (col_list, tabla),
        (tenant_id,),
    )
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _reescribir_raw(cur, tenant_id, tabla, cols, filas):
    """Reemplaza TODO el contenido de `raw.<tabla>` para este tenant, en el ORDEN de `filas` — el
    `id` bigserial nuevo queda en ese mismo orden, que `exportar.py`/el espejo leen vía
    `ORDER BY id` (el espejo byte-idéntico necesita conservar el orden, no solo el contenido)."""
    cur.execute("DELETE FROM raw.%s WHERE tenant_id = %%s" % tabla, (tenant_id,))
    if not filas:
        return
    col_list = ", ".join('"%s"' % c for c in (["tenant_id"] + cols))
    placeholders = ", ".join(["%s"] * (1 + len(cols)))
    sql = "INSERT INTO raw.%s (%s) VALUES (%s)" % (tabla, col_list, placeholders)
    cur.executemany(sql, [tuple([tenant_id] + [f.get(c, "") for c in cols]) for f in filas])


def _escribir_csv_atomico(path, cols, filas):
    """Mismo formato que `upsert_fact.upsert()` / `flujo.escribir_estado()` /
    `editar_producto.py`: `csv.DictWriter` con terminador CRLF por defecto (dialecto excel),
    utf-8 SIN BOM, header + filas en el orden de `cols`. Atómico: escribe a un temp file en el
    MISMO directorio y lo reemplaza con `os.replace` — nunca deja el mirror a medio escribir."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp-escribir"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow({c: f.get(c, "") for c in cols})
    os.replace(tmp, path)


def _escribir_json_atomico(path, payload):
    """Mismo formato que `decidir.py:main()` (`--escribir`): `io.open(path, "w",
    encoding="utf-8")` SIN `newline=""` (deja la traducción de línea del modo texto — en Windows,
    `\\n` -> `\\r\\n`, igual que el archivo real) + `json.dump(..., ensure_ascii=False,
    indent=2)`. Atómico igual que el CSV."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp-escribir"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def leer_decision_actual(conn, tenant_id="vitalcom"):
    """El `payload` (dict, con el mismo orden de claves que el `_DECISIONES.json` original) de la
    última fila de `raw.decisiones_json` para `tenant_id`, o `None` si no hay ninguna.

    A PROPÓSITO lee de `raw.decisiones_json.contenido` (texto verbatim) y NO de
    `core.decision.payload`: esa columna es `JSONB`, y Postgres NO garantiza el orden de claves de
    un objeto JSONB al leerlo de vuelta (hallazgo de T2 — `test_espejo_es_byte_identico_a_los_7_
    archivos_db_truth` lo detectó comparando bytes: reconstruir el espejo desde `core.decision`
    reordenaba las claves de nivel superior). El mismo patrón que los CSV (mirror regenerado desde
    `raw`, verbatim, nunca desde `core`) aplica acá: `core.decision` sirve para que un lector
    tipado (futuro T5) consulte `_DECISIONES.json` con SQL, no para regenerar el mirror byte a
    byte — eso es trabajo de `raw`."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT contenido FROM raw.decisiones_json WHERE tenant_id = %s "
            "ORDER BY id DESC LIMIT 1",
            (tenant_id,),
        )
        fila = cur.fetchone()
    if not fila or not fila[0]:
        return None
    return json.loads(fila[0])


def _filas_espejo(conn, tenant_id, tabla):
    """(archivo, cols, filas) que el espejo de `tabla` debería tener HOY para `tenant_id`, leído
    de `raw.<tabla>` en su orden real — la pieza compartida entre regenerar el espejo de verdad
    y solo RENDERIZARLO en memoria para comparar (`verificar_csv_sincronizado`)."""
    archivo, opcional = _spec_de(tabla)
    cols = T.columnas_tabla(tabla, archivo, opcional)
    with conn.cursor() as cur:
        filas = _leer_raw(cur, tenant_id, tabla, cols)
    return archivo, cols, filas


def _render_espejo_bytes(conn, tenant_id, tabla):
    """Bytes exactos que produciría el espejo de `tabla` para `tenant_id` AHORA MISMO, sin tocar
    ningún archivo real — se escribe a un temp file (mismo formato que `_escribir_csv_atomico`) y
    se descarta. Lo usa `verificar_csv_sincronizado()` para comparar sin arriesgar el CSV real."""
    archivo, cols, filas = _filas_espejo(conn, tenant_id, tabla)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, archivo)
        _escribir_csv_atomico(path, cols, filas)
        with open(path, "rb") as f:
            return f.read()


def _respaldar_mirror(prod_dir, archivo, bkdir):
    """Copia el mirror ACTUAL (si ya existe) a `bkdir` justo ANTES de reemplazarlo — mismo patrón
    y mismo nombrado que `upsert_fact.upsert()` (T3): ningún escritor de este módulo pisa un CSV
    sin dejar copia previa. `bkdir` es explícito (nunca inferido) para que una prueba con
    `prod_dir` en un directorio temporal no termine escribiendo en el `_RESPALDOS/` real del
    repo — el mismo motivo por el que `upsert_fact.upsert()` también recibe `bkdir` como parámetro."""
    path = os.path.join(prod_dir, archivo)
    if not os.path.exists(path):
        return
    os.makedirs(bkdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = archivo[:-4] if archivo.lower().endswith(".csv") else archivo
    shutil.copy2(path, os.path.join(bkdir, "%s_%s.csv" % (nombre, stamp)))


def _regenerar_espejo_csv(conn, tenant_id, tabla, prod_dir, bkdir=None):
    archivo, cols, filas = _filas_espejo(conn, tenant_id, tabla)
    if bkdir:
        _respaldar_mirror(prod_dir, archivo, bkdir)
    _escribir_csv_atomico(os.path.join(prod_dir, archivo), cols, filas)


def verificar_csv_sincronizado(conn, tabla, prod_dir, tenant_id="vitalcom"):
    """GUARDIA DE DRIFT (P3 T3, crítico): se corre ANTES de cualquier escritura sobre una tabla
    DB-truth migrada (`tables.TABLAS_MIGRADAS_DB`). Dos formas de abortar, misma excepción
    (`DriftDetectado`, nunca se escribe nada — ni `raw` ni el espejo):

      1. Esta tabla/tenant NUNCA se importó como verdad (`raw.raw_import` no tiene ninguna fila
         para `(tenant_id, archivo)`): es la primera corrida, nadie corrió el bootstrap
         (`db/cargar.py --tomar-csv <archivo>`). Se mide por el LOG de importación, no por
         `count(*)==0` en `raw.<tabla>`: un tenant nuevo legítimo puede empezar con cero filas de
         verdad, y comparar solo el conteo bloquearía para siempre aunque ya se hubiera corrido
         `--tomar-csv` sobre un CSV vacío.
      2. El CSV en `prod_dir` no es BYTE-IDÉNTICO a lo que la base exportaría ahora para esa tabla:
         alguien lo editó a mano, o la base quedó desactualizada frente a un cambio externo.

    En ambos casos el mensaje trae la recuperación EXACTA (`--tomar-csv`), nunca una reparación
    automática — ver `db/cargar.py:tomar_csv()`."""
    _exigir_verdad_db(tabla)
    archivo, _ = _spec_de(tabla)
    comando = "python db/cargar.py --tomar-csv %s" % archivo
    # "Ya se importó al menos una vez" se mide con `raw.raw_import` (audita cada carga real,
    # `cargar_tabla()`), NO con `count(*) FROM raw.<tabla> == 0`: un producto/tenant legítimamente
    # nuevo empieza con 0 filas de verdad, y comparar solo el conteo bloquearía PARA SIEMPRE aunque
    # el operador ya hubiera corrido `--tomar-csv` sobre un CSV vacío (0 filas antes y después del
    # bootstrap son indistinguibles por conteo). `raw_import` sí distingue "nunca se importó" de
    # "se importó y trajo cero filas".
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM raw.raw_import WHERE tenant_id = %s AND archivo = %s",
            (tenant_id, archivo))
        importado = cur.fetchone()[0] > 0
    if not importado:
        raise DriftDetectado(
            "%s (raw.%s) nunca se importo como verdad para tenant %r: es la primera corrida, "
            "nadie corrio el bootstrap. Corre PRIMERO, a mano:\n  %s\nNunca se importa solo "
            "porque nadie lo hizo antes." % (archivo, tabla, tenant_id, comando))
    real_path = os.path.join(prod_dir, archivo)
    if not os.path.exists(real_path):
        raise DriftDetectado(
            "%s no existe en %s pero raw.%s SI tiene filas para tenant %r: el espejo se "
            "desincronizo. Recupera con:\n  %s" % (archivo, prod_dir, tabla, tenant_id, comando))
    esperado = _render_espejo_bytes(conn, tenant_id, tabla)
    with open(real_path, "rb") as f:
        real = f.read()
    if real != esperado:
        raise DriftDetectado(
            "%s en %s NO es byte-identico a lo que la base exportaria para raw.%s (alguien lo "
            "edito a mano, o la base quedo desactualizada). Nunca se escribe nada hasta resolver "
            "esto. Recupera con:\n  %s" % (archivo, prod_dir, tabla, comando))


def verificar_decision_sincronizada(conn, prod_dir, tenant_id="vitalcom"):
    """GUARDIA DE DRIFT para `_DECISIONES.json` (P3 T4): mismo contrato que
    `verificar_csv_sincronizado()`, pero para el blob de `raw.decisiones_json`, que no tiene fila
    en `tables.TABLE_SPECS` (no es un espejo columna por columna) — por eso no puede reusar
    `_spec_de()`/`_render_espejo_bytes()` y se prueba aparte.

    Aborta con `DriftDetectado`, nunca escribe nada, si:
      1. esta tabla/tenant NUNCA se importó como verdad (`raw.raw_import` sin fila para
         `(tenant_id, "_DECISIONES.json")` — primera corrida, falta el bootstrap
         `db/cargar.py --tomar-csv _DECISIONES.json`).
      2. el archivo en disco no es BYTE-IDÉNTICO a lo que `reemplazar_decision()` escribiría
         ahora para el payload actual de `raw.decisiones_json` (edición a mano, o base
         desactualizada)."""
    archivo = "_DECISIONES.json"
    comando = "python db/cargar.py --tomar-csv %s" % archivo
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM raw.raw_import WHERE tenant_id = %s AND archivo = %s",
            (tenant_id, archivo))
        importado = cur.fetchone()[0] > 0
    if not importado:
        raise DriftDetectado(
            "%s (raw.decisiones_json) nunca se importo como verdad para tenant %r: es la "
            "primera corrida, nadie corrio el bootstrap. Corre PRIMERO, a mano:\n  %s"
            % (archivo, tenant_id, comando))
    real_path = os.path.join(prod_dir, archivo)
    payload = leer_decision_actual(conn, tenant_id)
    if payload is None:
        if os.path.exists(real_path):
            raise DriftDetectado(
                "%s existe en %s pero raw.decisiones_json no tiene ninguna fila para tenant %r: "
                "el espejo se desincronizo. Recupera con:\n  %s"
                % (archivo, prod_dir, tenant_id, comando))
        return
    if not os.path.exists(real_path):
        raise DriftDetectado(
            "%s no existe en %s pero raw.decisiones_json SI tiene contenido para tenant %r: el "
            "espejo se desincronizo. Recupera con:\n  %s" % (archivo, prod_dir, tenant_id, comando))
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = os.path.join(tmp, archivo)
        _escribir_json_atomico(tmp_path, payload)
        with open(tmp_path, "rb") as f:
            esperado = f.read()
    with open(real_path, "rb") as f:
        real = f.read()
    if real != esperado:
        raise DriftDetectado(
            "%s en %s NO es byte-identico a lo que raw.decisiones_json exportaria (alguien lo "
            "edito a mano, o la base quedo desactualizada). Nunca se escribe nada hasta resolver "
            "esto. Recupera con:\n  %s" % (archivo, prod_dir, comando))


def upsert(conn, tabla, filas_nuevas, key, particion=None, prod_dir=None, bkdir=None,
           tenant_id="vitalcom"):
    """UPSERT (misma semántica que `upsert_fact.upsert()`, vía `fusionar()`) sobre `raw.<tabla>`,
    con reconstrucción de `core` en LA MISMA transacción. Devuelve (reemplazadas, nuevas,
    sin_cambio) sin `particion`, o +eliminadas con `particion` — igual contrato que
    `upsert_fact.upsert()`.

    Si `prod_dir` se pasa, y hubo algún cambio (alta, reemplazo o baja), regenera el espejo CSV de
    ese archivo en `prod_dir` DESPUÉS de que el commit ya haya ocurrido (nunca antes: un fallo a
    mitad de transacción nunca debe dejar un mirror que no corresponde a lo que quedó en `raw`)."""
    _exigir_verdad_db(tabla)
    cols = _cols_de(tabla)
    contador = {}

    def _cuerpo(cur):
        existentes = _leer_raw(cur, tenant_id, tabla, cols)
        resultado, reemplazadas, nuevas, sin_cambio, eliminadas = fusionar(
            existentes, filas_nuevas, cols, key, particion)
        if reemplazadas or nuevas or eliminadas:
            _reescribir_raw(cur, tenant_id, tabla, cols, resultado)
        N.construir_core(cur, tenant_id)
        contador.update(reemplazadas=reemplazadas, nuevas=nuevas, sin_cambio=sin_cambio,
                         eliminadas=eliminadas)

    _en_transaccion(conn, _cuerpo, tabla, "upsert")
    reemplazadas = contador["reemplazadas"]
    nuevas = contador["nuevas"]
    sin_cambio = contador["sin_cambio"]
    eliminadas = contador["eliminadas"]

    if prod_dir and (reemplazadas or nuevas or eliminadas):
        _regenerar_espejo_csv(conn, tenant_id, tabla, prod_dir, bkdir)

    if particion is not None:
        return reemplazadas, nuevas, sin_cambio, eliminadas
    return reemplazadas, nuevas, sin_cambio


def anexar(conn, tabla, filas, prod_dir=None, bkdir=None, tenant_id="vitalcom"):
    """APPEND puro (para `_EVENTOS.csv`: nunca se reemplaza ni se borra una fila existente, solo
    se agregan). Reconstruye `core` en la misma transacción y, si `prod_dir` se pasa y hay filas,
    regenera el espejo completo (equivalente en bytes a un `a`ppend real: mismo header, mismas
    filas viejas intactas en el mismo orden, más las nuevas al final)."""
    _exigir_verdad_db(tabla)
    cols = _cols_de(tabla)
    filas_completas = [_completar(f, cols) for f in filas]

    def _cuerpo(cur):
        if filas_completas:
            col_list = ", ".join('"%s"' % c for c in (["tenant_id"] + cols))
            placeholders = ", ".join(["%s"] * (1 + len(cols)))
            sql = "INSERT INTO raw.%s (%s) VALUES (%s)" % (tabla, col_list, placeholders)
            cur.executemany(
                sql,
                [tuple([tenant_id] + [f.get(c, "") for c in cols]) for f in filas_completas],
            )
        N.construir_core(cur, tenant_id)

    _en_transaccion(conn, _cuerpo, tabla, "anexar")

    if prod_dir and filas_completas:
        _regenerar_espejo_csv(conn, tenant_id, tabla, prod_dir, bkdir)
    return len(filas_completas)


def reemplazar(conn, tabla, filas, prod_dir=None, bkdir=None, tenant_id="vitalcom"):
    """REESCRITURA COMPLETA (para `_ESTADO_FLUJO.csv`/`_DIM_PRODUCTOS.csv`: el escritor real
    siempre vuelve a escribir el archivo entero, no hace merge por llave). Reconstruye `core` en
    la misma transacción; con `prod_dir`, regenera el espejo siempre (igual que el escritor real,
    que reescribe en cada corrida sin condicionar a si hubo cambios)."""
    _exigir_verdad_db(tabla)
    cols = _cols_de(tabla)
    filas_completas = [_completar(f, cols) for f in filas]

    def _cuerpo(cur):
        _reescribir_raw(cur, tenant_id, tabla, cols, filas_completas)
        N.construir_core(cur, tenant_id)

    _en_transaccion(conn, _cuerpo, tabla, "reemplazar")

    if prod_dir:
        _regenerar_espejo_csv(conn, tenant_id, tabla, prod_dir, bkdir)
    return len(filas_completas)


def reemplazar_decision(conn, payload, prod_dir=None, tenant_id="vitalcom"):
    """Reescribe `raw.decisiones_json` (P3 T2: la verdad de `_DECISIONES.json`, que no tiene CSV
    ni tabla `raw` en `tables.TABLE_SPECS` — ver `tables.py`) con el TEXTO de `payload` serializado
    exactamente como `decidir.py:main()` lo escribe hoy (`json.dumps(..., ensure_ascii=False,
    indent=2)`), reconstruye `core` (que arma `core.decision` desde esa fila, ver `nucleo.py`) y,
    con `prod_dir`, regenera `_DECISIONES.json` byte-idéntico al que produciría `decidir.py
    --escribir` sobre el mismo `payload`."""
    contenido = json.dumps(payload, ensure_ascii=False, indent=2)

    def _cuerpo(cur):
        cur.execute("DELETE FROM raw.decisiones_json WHERE tenant_id = %s", (tenant_id,))
        cur.execute(
            "INSERT INTO raw.decisiones_json (tenant_id, contenido) VALUES (%s, %s)",
            (tenant_id, contenido),
        )
        N.construir_core(cur, tenant_id)

    _en_transaccion(conn, _cuerpo, "decisiones_json", "reemplazar_decision")

    if prod_dir:
        _escribir_json_atomico(os.path.join(prod_dir, "_DECISIONES.json"), payload)
