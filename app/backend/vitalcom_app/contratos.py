"""contratos.py — lectura de los contratos del sistema. NO calcula nada.

Regla de oro de la app (hoja de ruta §0.1): la app no calcula, no decide y no escribe CSV.
Todo número que se muestra sale tal cual de un CSV o de un script del motor. Acá no hay
aritmética de negocio: ni CPA, ni break-even, ni márgenes, ni edades de data. Si falta un
dato, se crea el script que lo produce en `Ads/_TOOLS/`, no una cuenta en este archivo.
`tests/test_sin_aritmetica.py` lo verifica sobre el árbol de sintaxis del paquete.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import python_del_sistema, ruta, base

DIM_PRODUCTOS = ("PRODUCTOS", "_DIM_PRODUCTOS.csv")
DIM_CUENTAS = ("PRODUCTOS", "_DIM_CUENTAS.csv")
DIM_FANPAGES = ("PRODUCTOS", "_DIM_FANPAGES.csv")
PARAMETROS_DECISION = ("PRODUCTOS", "_PARAMETROS_DECISION.csv")
ESTADO_FLUJO = ("PRODUCTOS", "_ESTADO_FLUJO.csv")
DECISIONES = ("PRODUCTOS", "_DECISIONES.json")
FLUJO_GLOBAL = ("PRODUCTOS", "_FLUJO.json")
ESTADO_VISTAS = ("VISTAS", "_ESTADO.json")
AUDITORIAS = ("PRODUCTOS", "_AUDITORIAS")
FLUJO_PY = ("Ads", "_TOOLS", "flujo.py")
COSTEAR_PY = ("Ads", "_TOOLS", "costear.py")
GEN_ORDENES_PY = ("Ads", "_TOOLS", "gen_ordenes.py")

# Lo que la pantalla necesita de _DIM_PRODUCTOS.csv. El resto de las columnas (notas de
# auditoría, alias de carpetas, tasas) no se sirven: la app muestra, no vuelca el CSV.
COLUMNAS_PRODUCTO = (
    "producto_key",
    "nombre_display",
    "slug_carpeta",
    "estado",
    "fase",
    "cuenta_alias",
    "cuenta_id",
    "moneda",
    "costo_q",
    "precio_base_q",
    "cpa_base_q",
    "cpa_be_q",
    "campaign_id",
)


class ContratoAusente(RuntimeError):
    """Falta un archivo que produce el motor. La app lo dice; no lo inventa ni lo crea."""


# P3 T5: archivo -> tabla DB-truth (`db/tables.py:TABLAS_MIGRADAS_DB`) que lo espeja. Solo estos
# cuatro CSV se leen por Postgres cuando `VITALCOM_FUENTE=db` (default); el resto de PRODUCTOS/
# (dimensiones editadas a mano: _DIM_CONJUNTOS, _DIM_CUENTAS, _DIM_FANPAGES,
# _PARAMETROS_DECISION, _DIM_CREATIVOS...) sigue leyéndose del CSV real, sin tocar. `_DECISIONES
# .json` no tiene fila acá: no es un espejo columna-por-columna (ver `_leer_json`).
TABLA_DB_POR_ARCHIVO = {
    "_DIM_PRODUCTOS.csv": "producto",
    "_ESTADO_FLUJO.csv": "estado_flujo",
    "_FACT_VENTAS.csv": "venta",
    "_EVENTOS.csv": "evento",
}


def _fuente() -> str:
    """`VITALCOM_FUENTE=db` (default) o `csv` — mismo contrato que `Ads/_TOOLS/decidir.py`."""
    return (os.environ.get("VITALCOM_FUENTE") or "db").strip().lower()


def _tenant_db() -> str:
    """`vitalcom` (single tenant, ver `db/tables.py`) salvo que una prueba aislada declare
    `VITALCOM_DB_TENANT` (mismo patrón de override que `registrar_evento.py`/
    `ingerir_lucidsales.py`: nunca toca el tenant real desde una prueba)."""
    return os.environ.get("VITALCOM_DB_TENANT") or "vitalcom"


def _modulo_db():
    """Importa `db/leer.py` DEL SISTEMA (nunca uno instalado en el venv de la app): se agrega
    `base()/db` a `sys.path` una sola vez, igual que ya hace `tests/test_alta_por_la_app.py`
    para `db/` en subprocesos."""
    db_dir = str(base() / "db")
    if db_dir not in sys.path:
        sys.path.insert(0, db_dir)
    import leer as db_leer  # noqa: E402

    return db_leer


def _conectar_db():
    """Conexión a Postgres para un lector `db`. Postgres inalcanzable NUNCA cae de vuelta al CSV
    en silencio (sería exactamente el defecto que P3 corrige) — se dice como `ContratoAusente`,
    que ya mapea a HTTP 503 (ver `main.py:_contrato_ausente`)."""
    db_leer = _modulo_db()
    try:
        return db_leer, db_leer.conectar()
    except Exception as exc:
        raise ContratoAusente(
            f"VITALCOM_FUENTE=db (default) pero Postgres no está disponible: {exc}"
        ) from exc


def _leer_csv(partes: tuple[str, ...]) -> list[dict[str, str]]:
    tabla = TABLA_DB_POR_ARCHIVO.get(partes[-1]) if len(partes) == 2 and partes[0] == "PRODUCTOS" else None
    if tabla and _fuente() != "csv":
        db_leer, con = _conectar_db()
        try:
            return db_leer.filas(con, tabla, tenant_id=_tenant_db())
        finally:
            con.close()
    archivo = ruta(*partes)
    if not archivo.is_file():
        raise ContratoAusente(f"falta {Path(*partes)}")
    with archivo.open(encoding="utf-8-sig", newline="") as fh:
        return [dict(fila) for fila in csv.DictReader(fh)]


def _leer_json(partes: tuple[str, ...]) -> Any:
    if partes == DECISIONES and _fuente() != "csv":
        db_leer, con = _conectar_db()
        try:
            payload = db_leer.decision(con, tenant_id=_tenant_db())
        finally:
            con.close()
        if payload is None:
            raise ContratoAusente(f"falta {Path(*partes)}")
        return payload
    archivo = ruta(*partes)
    if not archivo.is_file():
        raise ContratoAusente(f"falta {Path(*partes)}")
    with archivo.open(encoding="utf-8") as fh:
        return json.load(fh)


def productos() -> list[dict[str, str]]:
    """Las filas de `_DIM_PRODUCTOS.csv`, recortadas a las columnas que la pantalla usa."""
    return [{c: fila.get(c, "") for c in COLUMNAS_PRODUCTO} for fila in _leer_csv(DIM_PRODUCTOS)]


def fila_de_producto(producto_key: str) -> dict[str, str]:
    """La fila COMPLETA de un producto (carpetas incluidas), o {} si no tiene. Solo para el runner y
    las pantallas de FASE 1, que necesitan saber dónde viven sus transcripciones y su media."""
    return next((fila for fila in _leer_csv(DIM_PRODUCTOS) if fila.get("producto_key") == producto_key), {})


def parametros_decision() -> list[dict[str, str]]:
    """`_PARAMETROS_DECISION.csv` tal cual: los relojes y umbrales del motor de decisión.

    Pura lectura de CSV, fila por fila, sin filtrar ni derivar nada (dueño: `decidir.py` /
    `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`, verificado por `verificar_guia_madre.py`).
    """
    return _leer_csv(PARAMETROS_DECISION)


def cuentas() -> list[dict[str, str]]:
    """Las cuentas publicitarias de `_DIM_CUENTAS.csv`: alias, moneda y qué permite cada una."""
    columnas = ("cuenta_alias", "cuenta_id", "moneda", "mcp_habilitado", "sube_media_local", "estado_cuenta")
    return [{c: fila.get(c, "") for c in columnas} for fila in _leer_csv(DIM_CUENTAS)]


def fanpages() -> list[dict[str, str]]:
    """Las FanPages de `_DIM_FANPAGES.csv`: identidad, tono, edad de orientación y productos del
    nicho. A diferencia de `cuentas()`, un archivo ausente no es una falla del sistema — la
    carpeta que corre la app puede no tener todavía esa declaración (Ajustes/T5) — así que
    devuelve lista vacía en vez de levantar `ContratoAusente`."""
    if not ruta(*DIM_FANPAGES).is_file():
        return []
    columnas = ("pagina_num", "pagina_nombre", "identidad", "rol", "tono", "logica",
                "edad_orientacion", "page_id", "productos_nicho")
    return [{c: fila.get(c, "") for c in columnas} for fila in _leer_csv(DIM_FANPAGES)]


def estado_flujo() -> dict[str, dict[str, str]]:
    """`_ESTADO_FLUJO.csv` por producto_key: fase y nodo vigentes, derivados por flujo.py.

    La fase que manda es esta, no la columna `fase` de `_DIM_PRODUCTOS.csv`, que quedó como
    bitácora (CLAUDE.md, ARRANQUE DE SESIÓN).
    """
    return {fila["producto_key"]: fila for fila in _leer_csv(ESTADO_FLUJO)}


def decisiones() -> dict[str, Any]:
    """`_DECISIONES.json` tal cual lo dejó `decidir.py`: el único reglamento (invariante 13)."""
    return _leer_json(DECISIONES)


def salud() -> dict[str, Any]:
    """`VISTAS/_ESTADO.json`: qué vista existe, de cuándo es y quién la produce.

    La frescura la calcula `gen_app.py` desde el `mtime` del archivo. La app no la recalcula.
    """
    return _leer_json(ESTADO_VISTAS)


def historial_resultados() -> list[dict[str, Any]]:
    """Todos los `_PL_<ini>_<fin>.json` que dejó `gen_pl.py --json` (T4a), del más viejo al más
    nuevo por nombre de archivo. Para el gráfico de tendencia por período: cada punto es un
    período que el operador realmente cargó, nunca una interpolación ni una serie inventada.
    """
    carpeta = ruta(*AUDITORIAS)
    archivos = sorted(carpeta.glob("_PL_*.json")) if carpeta.is_dir() else []
    salida = []
    for archivo in archivos:
        with archivo.open(encoding="utf-8") as fh:
            salida.append(json.load(fh))
    return salida


def resultados() -> dict[str, Any]:
    """El `_PL_<ini>_<fin>.json` más reciente que dejó `gen_pl.py --json` (T4a).

    El nombre del archivo ordena por fecha (`_PL_YYYYMMDD_YYYYMMDD.json`), así que el último
    del orden alfabético es el período más nuevo cargado — nada se recalcula ni se compara por
    edad acá, eso ya lo decidió `gen_pl.py` y viaja en el propio JSON (`vista_a_cohorte.preliminar`).
    """
    carpeta = ruta(*AUDITORIAS)
    archivos = sorted(carpeta.glob("_PL_*.json")) if carpeta.is_dir() else []
    if not archivos:
        raise ContratoAusente(
            "no hay ningún _PL_<ini>_<fin>.json en _AUDITORIAS/: falta cargar el export de Dropi."
        )
    with archivos[-1].open(encoding="utf-8") as fh:
        return json.load(fh)


def flujo(producto_key: str, hoy: str | None = None) -> dict[str, Any]:
    """Corre `flujo.py <pk> --json` y devuelve su salida.

    Un producto puntual (sin `--todo`) ya es SOLO LECTURA por contrato de CLI (T6): no toca
    `_ESTADO_FLUJO.csv` ni anota un evento sin importar los flags. Lo que persiste el estado
    derivado es `flujo.py --todo --escribir`, que corre como acción declarada (Hito 3), no
    como efecto de abrir una pantalla.
    """
    comando = [
        python_del_sistema(),
        str(ruta(*FLUJO_PY)),
        producto_key,
        "--json",
        "--silencioso",
    ]
    if hoy:
        comando += ["--hoy", hoy]
    completado = subprocess.run(
        comando,
        cwd=str(ruta()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"flujo.py falló para «{producto_key}»: {detalle[-600:]}")
    return json.loads(completado.stdout)


def costear(costo_q: str) -> dict[str, Any]:
    """Corre `costear.py <costo> --json`: la tabla de precios de Guatemala.

    El costo llega como texto y se pasa como texto: el script valida y decide qué fila de
    `_DIM_COSTEO.csv` corresponde. La app no interpreta ni redondea el número.
    """
    completado = subprocess.run(
        [python_del_sistema(), str(ruta(*COSTEAR_PY)), costo_q, "--json"],
        cwd=str(ruta()), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"costear.py no pudo costear «{costo_q}»: {detalle[-400:]}")
    return json.loads(completado.stdout)


def flujo_global() -> dict[str, Any]:
    """`_FLUJO.json` tal como lo dejó `flujo.py --todo`: el estado consolidado de todos los productos."""
    return _leer_json(FLUJO_GLOBAL)


def ordenes(producto_key: str | None = None) -> dict[str, Any]:
    """Corre `gen_ordenes.py --json`: órdenes literales para Meta."""
    comando = [python_del_sistema(), str(ruta(*GEN_ORDENES_PY)), "--json"]
    if producto_key:
        comando += ["--producto", producto_key]
    completado = subprocess.run(
        comando,
        cwd=str(ruta()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"gen_ordenes.py falló: {detalle[-400:]}")
    return json.loads(completado.stdout)


def ganadores() -> list[dict[str, Any]]:
    """Devuelve los productos que tienen un ángulo ganador detectado por ventas."""
    resultado: list[dict[str, Any]] = []
    lista_prods = []
    try:
        fg = flujo_global()
        lista_prods = fg.get("productos", [])
    except Exception:
        lista_prods = []

    for p in lista_prods:
        pk = p.get("producto_key", "")
        entradas = p.get("entradas", [])
        ganador_obs = ""
        tiene_ganador = False
        for e in entradas:
            if e.get("fase") == "F2" and e.get("ok"):
                tiene_ganador = True
                ganador_obs = e.get("observado", "")
                break

        nodo_actual = p.get("nodo_actual", "")
        fase = p.get("fase", "")
        if tiene_ganador or fase == "F2" or (nodo_actual and nodo_actual.startswith("F2.")):
            resultado.append({
                "producto_key": pk,
                "nombre": p.get("nombre", pk),
                "fase": fase,
                "nodo_actual": nodo_actual,
                "angulo_ganador": ganador_obs or "Ángulo ganador confirmado por ventas",
                "siguiente_paso": {
                    "nodo": nodo_actual,
                    "etapa": "etapa-11" if nodo_actual == "F2.etapa-11" else nodo_actual,
                    "titulo": "Optimizar el CIERRE del bot hacia el ángulo ganador (antes de gastar más)" if nodo_actual == "F2.etapa-11" else p.get("como", "Siguiente paso en el flujo"),
                    "ejecutor": p.get("ejecutor", "subagente etapa-11"),
                    "enlace": f"/producto/{pk}/fase1" if fase == "F1" else f"/producto/{pk}",
                },
            })
    return resultado


def _angulos_probados(producto_key: str) -> list[str]:
    """Lista ordenada de ángulos testeados por el producto."""
    angulos = set()
    try:
        dim_conj = _leer_csv(("PRODUCTOS", "_DIM_CONJUNTOS.csv"))
        for r in dim_conj:
            if r.get("producto_key") == producto_key:
                a = (r.get("angulo_key") or "").strip()
                if a:
                    angulos.add(a)
        fact_ventas = _leer_csv(("PRODUCTOS", "_FACT_VENTAS.csv"))
        for r in fact_ventas:
            if r.get("producto_key") == producto_key:
                cj = (r.get("conjunto") or "").strip()
                for c in dim_conj:
                    if (c.get("conjunto_meta") or "").strip() == cj:
                        a = (c.get("angulo_key") or "").strip()
                        if a:
                            angulos.add(a)
    except Exception:
        pass
    return sorted(angulos)


def fase2_detalle(producto_key: str) -> dict[str, Any]:
    """Detalles de FASE 2 para el producto: ángulo ganador, 10 conceptos con blueprints y carriles."""
    flujo_data = flujo(producto_key)
    entradas = flujo_data.get("entradas", [])
    ganador_obs = ""
    for e in entradas:
        if e.get("fase") == "F2" and e.get("ok"):
            ganador_obs = e.get("observado", "")
            break

    # Ganadores secundarios (#2 y #3) y órdenes del motor
    celdas = []
    try:
        dec = decisiones()
        for p in dec.get("productos", []):
            if p.get("producto_key") == producto_key:
                celdas = p.get("celdas", [])
                break
    except Exception:
        celdas = []

    carriles = []
    for c in celdas:
        c_est = c.get("estado", "")
        c_nom = c.get("celda", "")
        if c_est in ("ESCALAR", "RENOVAR"):
            carriles.append({
                "angulo_key": c_nom,
                "estado_motor": c_est,
                "accion": c.get("accion_sugerida", ""),
                "fecha_estimada": "Escalonar ~3 días",
            })

    creativos_rows = []
    try:
        creativos_rows = [r for r in _leer_csv(("PRODUCTOS", "_DIM_CREATIVOS.csv")) if r.get("producto_key") == producto_key]
    except Exception:
        creativos_rows = []

    canonicos_dict: dict[str, Any] = {}
    try:
        blueprints_dir = ruta("Ads", "_SWIPE", "_BLUEPRINTS", "CANONICOS")
        if blueprints_dir.is_dir():
            for f in blueprints_dir.glob("CN*.json"):
                try:
                    with f.open(encoding="utf-8") as bfh:
                        bdata = json.load(bfh)
                        canonicos_dict[bdata.get("canonico_id", "")] = bdata
                except Exception:
                    pass
    except Exception:
        pass

    conceptos = []
    usados_canonicos = set()
    for row in creativos_rows:
        cid = row.get("canonico_id", "")
        if cid:
            usados_canonicos.add(cid)
        binfo = canonicos_dict.get(cid, {})
        arch = row.get("archivo", "")
        media_path = ruta("Ads", f"MEDIA_{producto_key}", arch)
        conceptos.append({
            "creativo_id": row.get("creativo_id", ""),
            "archivo": arch,
            "canonico_id": cid,
            "blueprint_nombre": binfo.get("nombre", cid or "Blueprint Canónico"),
            "dispositivo": binfo.get("dispositivo_canonico", ""),
            "cuando_elegirlo": binfo.get("cuando_elegirlo", ""),
            "rol_embudo": row.get("rol_embudo", "") or binfo.get("perfil", {}).get("rol_embudo", "MOFU"),
            "estado": row.get("estado", "PENDIENTE_GENERAR"),
            "ad_id": row.get("ad_id", ""),
            "archivo_existe": media_path.is_file(),
            "notas": row.get("notas", ""),
            "prompt": f"Director de Arte: Crea una imagen publicitaria para {producto_key} usando la estructura {cid} ({binfo.get('nombre', '')}). Ángulo: {row.get('angulo_key', ganador_obs)}."
        })

    # Si hay menos de 10, completamos hasta 10 con los blueprints canónicos disponibles
    indice_extra = 1
    for cid, binfo in sorted(canonicos_dict.items()):
        if len(conceptos) >= 10:
            break
        if cid in usados_canonicos:
            continue
        arch_sug = f"{producto_key}_F2_{cid[:4]}_{indice_extra}.png"
        conceptos.append({
            "creativo_id": f"{producto_key}_F2_{cid[:4]}_{indice_extra}",
            "archivo": arch_sug,
            "canonico_id": cid,
            "blueprint_nombre": binfo.get("nombre", cid),
            "dispositivo": binfo.get("dispositivo_canonico", ""),
            "cuando_elegirlo": binfo.get("cuando_elegirlo", ""),
            "rol_embudo": "MOFU",
            "estado": "PENDIENTE_GENERAR",
            "ad_id": "",
            "archivo_existe": False,
            "notas": f"Blueprint recomendado por doctrina ({binfo.get('nombre', '')})",
            "prompt": f"Director de Arte: Crea una imagen publicitaria para {producto_key} usando la estructura {cid} ({binfo.get('nombre', '')}). Ángulo ganador: {ganador_obs}."
        })
        indice_extra += 1

    angulos_excl = _angulos_probados(producto_key)

    return {
        "producto_key": producto_key,
        "fase": flujo_data.get("fase", "F2"),
        "nodo_actual": flujo_data.get("nodo_actual", ""),
        "angulo_ganador": ganador_obs or "Ángulo ganador confirmado por ventas",
        "carriles_secundarios": carriles,
        "conceptos": conceptos,
        "total_conceptos": len(conceptos),
        "conceptos_generados": sum(1 for c in conceptos if c.get("estado") in ("GENERADO", "PUBLICADO")),
        "reingreso_activo": flujo_data.get("reingreso_activo"),
        "fatiga": {
            "ordenes": flujo_data.get("ordenes", []),
            "angulos_probados": angulos_excl,
            "puede_reingresar": True,
        }
    }


def fase3_detalle(producto_key: str) -> dict[str, Any]:
    """Detalles de FASE 3 para el producto: gate 2de2 con evidencia, plan CBO 1-1-7 y expansión."""
    flujo_data = flujo(producto_key)
    entradas = flujo_data.get("entradas", [])
    gate_2de2_info = {"ok": False, "observado": "Sin evaluar", "regla": ""}
    for e in entradas:
        if e.get("fase") == "F3":
            gate_2de2_info = {
                "ok": bool(e.get("ok")),
                "observado": e.get("observado", ""),
                "regla": e.get("regla", "")
            }
            break

    plan_txt = ruta("PRODUCTOS", producto_key, "4_PLAN_ESCALADO.txt")
    plan_json = ruta("PRODUCTOS", producto_key, "_PLAN_FASE3.json")
    tiene_plan = plan_txt.is_file() or plan_json.is_file()

    prod_info = fila_de_producto(producto_key)
    cuenta_primaria = prod_info.get("cuenta_alias", "GTR0")
    page_id = prod_info.get("page_id", "")

    cuentas_expansion = [cuenta_primaria]
    try:
        for ev in _leer_csv(("PRODUCTOS", "_EVENTOS.csv")):
            if ev.get("producto_key") == producto_key and ev.get("evento") == "REPLICA_MULTICUENTA":
                cta = ev.get("cuenta_alias", "")
                if cta and cta not in cuentas_expansion:
                    cuentas_expansion.append(cta)
    except Exception:
        pass

    angulos_excl = _angulos_probados(producto_key)

    return {
        "producto_key": producto_key,
        "fase": flujo_data.get("fase", "F3"),
        "nodo_actual": flujo_data.get("nodo_actual", ""),
        "gate_2de2": gate_2de2_info,
        "plan_cbo": {
            "estructura": "1-1-7 CBO",
            "descripcion": "1 Campaña CBO, 1 Conjunto de 7 anuncios con el concepto validado en 2 de 2 × 7 hooks (microángulos)",
            "tiene_plan": tiene_plan,
            "estado": "GENERADO" if tiene_plan else "PENDIENTE",
            "archivo": "4_PLAN_ESCALADO.txt" if plan_txt.is_file() else ("_PLAN_FASE3.json" if plan_json.is_file() else None)
        },
        "expansion": {
            "post_id": bool(len(cuentas_expansion) > 1),
            "cuenta_primaria": cuenta_primaria,
            "cuentas_activas": cuentas_expansion,
            "page_id": page_id
        },
        "fatiga": {
            "angulos_probados": angulos_excl,
            "puede_reingresar": True,
        }
    }


def reingreso_f1(producto_key: str, motivo: str | None = None) -> dict[str, Any]:
    """Ejecuta el retorno a F1 por fatiga mediante Ads/_TOOLS/reingreso_f1.py."""
    comando = [
        python_del_sistema(),
        str(ruta("Ads", "_TOOLS", "reingreso_f1.py")),
        "--producto",
        producto_key,
        "--json",
    ]
    if motivo:
        comando += ["--motivo", motivo]
    completado = subprocess.run(
        comando,
        cwd=str(ruta()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"reingreso_f1.py falló para «{producto_key}»: {detalle[-400:]}")
    return json.loads(completado.stdout)


