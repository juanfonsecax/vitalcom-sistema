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
DIM_REFERENCIA_F1 = ("PRODUCTOS", "_DIM_REFERENCIA_F1.csv")
PARAMETROS_DECISION = ("PRODUCTOS", "_PARAMETROS_DECISION.csv")
ESTADO_FLUJO = ("PRODUCTOS", "_ESTADO_FLUJO.csv")
ESTADO_ANGULOS = ("PRODUCTOS", "_ESTADO_ANGULOS.csv")
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
    "mercado",
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


def _modulo_mercado():
    """Importa `Ads/_TOOLS/mercado.py` DEL SISTEMA: el resolver de mercado (mercado → moneda de venta,
    símbolo, persona, registro). Es su dueño; la app no repite su lógica (mismo patrón que `_modulo_db`)."""
    herramientas = str(base() / "Ads" / "_TOOLS")
    if herramientas not in sys.path:
        sys.path.insert(0, herramientas)
    import mercado as resolver  # noqa: E402

    return resolver


def _perfil_de_fila(fila: dict[str, str]) -> dict[str, Any]:
    """Perfil del mercado de una fila de producto. Sin mercado o con uno desconocido NO hay valor por
    defecto: se dice como `ContratoAusente` (HTTP 503), nunca se asume GT."""
    resolver = _modulo_mercado()
    try:
        return resolver.perfil_de_fila(fila, str(base()))
    except resolver.MercadoError as error:
        raise ContratoAusente(str(error)) from error


def _con_mercado(fila: dict[str, str]) -> dict[str, str]:
    perfil = _perfil_de_fila(fila)
    return {**fila, "mercado": perfil["mercado"], "moneda_local": perfil["moneda"], "simbolo": perfil["simbolo"]}


def productos_con_mercado() -> list[dict[str, str]]:
    """`productos()` más `moneda_local` y `simbolo` del mercado de cada producto. `moneda` sigue siendo
    la de la CUENTA publicitaria; `moneda_local` es en la que el producto vende."""
    return [_con_mercado(fila) for fila in productos()]


def perfil_de_producto(producto_key: str) -> dict[str, str]:
    """`mercado`, `moneda_local` y `simbolo` de UN producto (falla si no declara mercado)."""
    fila = next((f for f in _leer_csv(DIM_PRODUCTOS) if f.get("producto_key") == producto_key), None)
    if fila is None:
        raise ContratoAusente(f"«{producto_key}» no tiene fila en _DIM_PRODUCTOS.csv.")
    perfil = _con_mercado(fila)
    return {c: perfil[c] for c in ("mercado", "moneda_local", "simbolo")}


def mercados() -> list[dict[str, Any]]:
    """Los mercados de `_DIM_MERCADOS.csv` con su perfil resuelto (moneda, símbolo, persona, tasa)."""
    resolver = _modulo_mercado()
    try:
        return [resolver.perfil_mercado(clave, str(base())) for clave in resolver.leer_mercados(str(base()))]
    except resolver.MercadoError as error:
        raise ContratoAusente(str(error)) from error


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


# ── prompt REAL de FASE 2 (join contra el paquete de armar_prompts_fase2.py) ──────────────────

FASE2_PREFIJO = "FASE2_"
PAQUETE_PREFIJO = "PAQUETE_CREATIVO_"
EXTENSIONES_SWIPE = {".jpg", ".jpeg", ".png", ".webp"}


def _localizar_carpeta_fase2(carpeta_media: str, angulo_key: str) -> Path | None:
    """La carpeta `FASE2_<ángulo>` que arma `armar_prompts_fase2.py`, para este ángulo.

    Esa carpeta la nombra el ángulo que detectó el script en `_DECISIONES.json` AL MOMENTO de
    generar el paquete. El `angulo_key` de `_DIM_CREATIVOS.csv` puede llevar un sufijo agregado
    después (ej. `RESISTENCIA_INSULINA_SOP` vs. carpeta `FASE2_RESISTENCIA_INSULINA`): por eso
    primero se intenta la carpeta EXACTA y, si no existe, se cae a la única `FASE2_*` que haya
    (doctrina: FASE 2 testea un solo ángulo ganador a la vez) o, si hay varias, a la que
    comparte el ángulo con `angulo_key` hasta un límite de `_`. Nunca inventa una carpeta: si
    nada calza, devuelve None y el llamador reporta "pendiente".
    """
    if not carpeta_media or not angulo_key:
        return None
    raiz = ruta("Ads", carpeta_media)
    if not raiz.is_dir():
        return None
    candidatas = sorted(p for p in raiz.glob(f"{FASE2_PREFIJO}*") if p.is_dir())
    if not candidatas:
        return None
    exacta = raiz / f"{FASE2_PREFIJO}{angulo_key}"
    if exacta in candidatas:
        return exacta
    if len(candidatas) == 1:
        return candidatas[0]
    for candidata in candidatas:
        nombre_angulo = candidata.name[len(FASE2_PREFIJO):]
        if (angulo_key == nombre_angulo
                or angulo_key.startswith(nombre_angulo + "_")
                or nombre_angulo.startswith(angulo_key + "_")):
            return candidata
    return None


def _leer_paquete_fase2(carpeta: Path) -> dict[str, Any] | None:
    for archivo in sorted(carpeta.glob(f"{PAQUETE_PREFIJO}*.json")):
        try:
            with archivo.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _comando_armar_prompts_fase2(producto_key: str, angulo_key: str) -> str:
    return f"python Ads/_TOOLS/armar_prompts_fase2.py {producto_key} {angulo_key}"


def _url_de_swipe(ruta_relativa: str) -> str | None:
    """URL servida por `GET /api/swipe/<ruta>` para un `foto_base_competidor` relativo
    (ej. "Ads/_SWIPE/_IMG/Camila_Recomienda/15_....jpg"). None si no viene bajo Ads/_SWIPE/."""
    if not ruta_relativa:
        return None
    normalizada = ruta_relativa.replace("\\", "/").strip()
    prefijo = "Ads/_SWIPE/"
    if not normalizada.startswith(prefijo):
        return None
    from urllib.parse import quote
    return "/api/swipe/" + quote(normalizada[len(prefijo):])


def resolver_prompt_fase2(producto_key: str, carpeta_media: str, angulo_key: str, canonico_id: str) -> dict[str, Any]:
    """El prompt REAL (+ imagen de referencia) del paquete que produjo `armar_prompts_fase2.py`
    para este concepto, o el comando exacto para generarlo si todavía no existe. Nunca fabrica
    un prompt genérico (ver `Ads/MEDIA_{producto}/FASE2_{angulo}/PAQUETE_CREATIVO_{angulo}.json`)."""
    comando = _comando_armar_prompts_fase2(producto_key, angulo_key)
    pendiente = {"prompt": None, "prompt_origen": "pendiente", "referencia_url": None, "comando_generar": comando}
    carpeta = _localizar_carpeta_fase2(carpeta_media, angulo_key)
    if carpeta is None:
        return pendiente
    paquete = _leer_paquete_fase2(carpeta)
    if not paquete:
        return pendiente
    for item in paquete.get("conceptos", []):
        if item.get("canonico_id") == canonico_id:
            return {
                "prompt": item.get("prompt_director_de_arte"),
                "prompt_origen": "paquete",
                "referencia_url": _url_de_swipe(item.get("foto_base_competidor", "")),
                "comando_generar": None,
            }
    return pendiente


def _comando_elegir_referencia_f1(producto_key: str) -> str:
    return f'python Ads/_TOOLS/referencia_f1.py --elegir {producto_key} <REFERENCIA> --motivo "..."'


def referencia_f1(producto_key: str) -> dict[str, Any]:
    """La referencia `ligera` fija de FASE 1 elegida para este producto (`_DIM_REFERENCIA_F1.csv`,
    dueño único `Ads/_TOOLS/referencia_f1.py`), o `referencia: None` + el comando exacto para
    elegirla si todavía no hay fila. Nunca fabrica una referencia."""
    comando = _comando_elegir_referencia_f1(producto_key)
    if not ruta(*DIM_REFERENCIA_F1).is_file():
        return {"referencia": None, "comando_elegir": comando}
    for fila in _leer_csv(DIM_REFERENCIA_F1):
        if fila.get("producto_key") == producto_key:
            archivo = fila.get("referencia", "")
            return {
                "referencia": {
                    "archivo": archivo,
                    "url": _url_de_swipe(f"Ads/_SWIPE/_BANCO_CREATIVOS/C2_BENEFICIOS/{archivo}"),
                    "motivo": fila.get("motivo", ""),
                    "elegido_el": fila.get("elegido_el", ""),
                },
                "comando_elegir": None,
            }
    return {"referencia": None, "comando_elegir": comando}


def ruta_de_swipe(ruta_relativa: str) -> Path | None:
    """Un archivo de imagen bajo `Ads/_SWIPE/`, o None si no existe, tiene mala extensión, o
    intenta salir de esa carpeta (traversal, ruta absoluta, symlink). Nunca sirve otra cosa."""
    if not ruta_relativa or Path(ruta_relativa).is_absolute():
        return None
    raiz = ruta("Ads", "_SWIPE").resolve()
    try:
        candidato = (raiz / ruta_relativa).resolve()
        candidato.relative_to(raiz)
    except (OSError, ValueError):
        return None
    if candidato.suffix.lower() not in EXTENSIONES_SWIPE:
        return None
    return candidato if candidato.is_file() else None


# Campos del veredicto del motor (`_DECISIONES.json`, una celda = un ángulo) que se pasan tal cual.
CAMPOS_VEREDICTO = (
    "estado", "accion_codigo", "accion_sugerida", "ventas", "ventas_acum", "cpa_real_q", "ic",
    "cierre_pct", "spend_q", "spend_acum_q", "nivel_prioridad", "faltan_ventas", "ejecutable",
    "bloqueo_fase",
)


def _celdas_del_producto(producto_key: str) -> list[dict[str, Any]]:
    try:
        for p in decisiones().get("productos", []):
            if p.get("producto_key") == producto_key:
                return list(p.get("celdas", []))
    except Exception:
        pass
    return []


def _estado_angulos_del_producto(producto_key: str) -> dict[str, dict[str, str]]:
    """`_ESTADO_ANGULOS.csv` (lo escribe `perfilar_angulos.py`) por angulo_key, solo este producto.
    Archivo ausente = sin perfil todavía: la pantalla lo dice, no lo inventa."""
    try:
        filas = _leer_csv(ESTADO_ANGULOS)
    except ContratoAusente:
        return {}
    return {f.get("angulo_key", ""): f for f in filas if f.get("producto_key") == producto_key}


def _entero_o_none(texto: Any) -> int | None:
    try:
        return int(float(str(texto).strip()))
    except (TypeError, ValueError):
        return None


def _decimal_o_none(texto: Any) -> float | None:
    try:
        return float(str(texto).strip())
    except (TypeError, ValueError):
        return None


def _semaforo(valor: float | None, referencia: float | None) -> str:
    """Color del costo por venta contra el break-even. La regla (verde < 0.8 x BE <= ambar <= BE < rojo)
    es de `Ads/_TOOLS/semaforo_be.py`: la app no compara ni calcula."""
    tools = str(Path(__file__).resolve().parents[3] / "Ads" / "_TOOLS")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from semaforo_be import semaforo  # noqa: E402

    return semaforo(valor, referencia)


def _cpa_contra_be(perfil: dict[str, str]) -> dict[str, Any]:
    """CPA acumulado y de la ventana contra el break-even, tal cual salen de `_ESTADO_ANGULOS.csv`."""
    acum = _decimal_o_none(perfil.get("cpa_acum_q"))
    ventana = _decimal_o_none(perfil.get("cpa_ventana_q"))
    be = _decimal_o_none(perfil.get("cpa_be_q"))
    return {
        "cpa_acum_q": acum,
        "cpa_ventana_q": ventana,
        "cpa_be_q": be,
        "semaforo_acum": _semaforo(acum, be),
        "semaforo_ventana": _semaforo(ventana, be),
        "orden_motor": (perfil.get("accion_motor") or "").strip(),
    }


def _es_apagado(estado_angulo: str) -> bool:
    return estado_angulo.startswith("APAGADO") or estado_angulo == "DORMIDO"


def angulos_de_fase2(producto_key: str, ganadores: list[str]) -> list[dict[str, Any]]:
    """TODOS los ángulos que el producto testeó en FASE 1, cada uno con su rol y el veredicto del
    motor. La app no elige ni ordena por su cuenta: junta tres fuentes que ya decidieron.

    Universo: unión de las celdas de `_DECISIONES.json` (el veredicto vigente de `decidir.py`)
    y las filas de `_ESTADO_ANGULOS.csv` (el estado de vida de cada ángulo, `perfilar_angulos.py`).

    Ganadores y su orden: `ganadores` es `flujo.py` -> `angulos_ganadores`, la lista que sale de la
    MISMA evidencia del gate `angulo_ganador` que abre FASE 2 (`_angulo_ganador_info`), ya
    ordenada por `flujo.ranking_ganadores`: #1 es el ESCALAR con más ventas de la ventana y menor
    CPA real (el criterio de `armar_prompts_fase2.orden_ganador`, el mismo que elige el ángulo del
    paquete de prompts); del #2 en adelante, por ventas acumuladas descendente. Acá solo se
    respeta ese orden: `posicion` es el lugar en la lista.

    Roles: `ganador_activo` (posicion 1, en testeo de conceptos ahora) · `ganador_en_fila`
    (posicion 2, 3…: cada ganador tiene su propia FASE 2, escalonadas ~3 días, DOCTRINA/
    CALENDARIO_ESCALADO.md §1) · `perdedor` (ya apagado, o el motor ordena PAUSAR) · `midiendo`
    (no ganó y todavía gasta sin orden de pausa).
    """
    celdas = {c.get("celda", ""): c for c in _celdas_del_producto(producto_key)}
    perfiles = _estado_angulos_del_producto(producto_key)
    claves_ganadoras = [g for g in ganadores if g]
    resto = sorted((set(celdas) | set(perfiles)) - set(claves_ganadoras) - {""})
    salida: list[dict[str, Any]] = []
    for lugar, clave in enumerate(claves_ganadoras + resto, start=1):
        celda = celdas.get(clave, {})
        perfil = perfiles.get(clave, {})
        es_ganador = clave in claves_ganadoras
        estado_angulo = perfil.get("estado", "")
        dias_sin_gasto = _entero_o_none(perfil.get("dias_sin_gasto"))
        if es_ganador:
            rol = "ganador_activo" if lugar == 1 else "ganador_en_fila"
            etiqueta = ""
        elif _es_apagado(estado_angulo):
            rol = "perdedor"
            etiqueta = "ya apagado" if dias_sin_gasto is None else f"ya apagado ({dias_sin_gasto} días sin gastar)"
        elif celda.get("estado") == "PAUSAR":
            rol = "perdedor"
            etiqueta = "el motor ordena pausarlo"
        else:
            rol = "midiendo"
            etiqueta = "midiendo"
        fila = {
            "angulo_key": clave,
            "rol": rol,
            "posicion": lugar if es_ganador else None,
            "etiqueta": etiqueta,
            "estado_angulo": estado_angulo,
            "dias_sin_gasto": dias_sin_gasto,
            "ultimo_dia_gasto": perfil.get("ultimo_dia_gasto", ""),
            **_cpa_contra_be(perfil),
        }
        for campo in CAMPOS_VEREDICTO:
            fila[campo] = celda.get(campo)
        salida.append(fila)
    return salida


def _estructura_fase2() -> list[tuple[str, int]]:
    """Campañas de conceptos de FASE 2 en orden: (brazo, anuncios por conjunto) de los brazos A y B de
    `_PARAMETROS_PUBLICACION.csv` (el brazo C repite los mismos dos grupos, no suma conceptos)."""
    try:
        filas = _leer_csv(("PRODUCTOS", "_PARAMETROS_PUBLICACION.csv"))
    except Exception:
        return []
    salida: list[tuple[str, int]] = []
    for brazo in ("A", "B"):
        for f in filas:
            if f.get("fase") == "2" and f.get("brazo") == brazo:
                n = _entero_o_none(f.get("anuncios_por_conjunto"))
                if n:
                    salida.append((brazo, n))
                break
    return salida


def _campana_de(numero: int, estructura: list[tuple[str, int]]) -> str:
    """Campaña (A/B) del concepto nº `numero` (1-based) dentro de su ángulo."""
    tope = 0
    for brazo, n in estructura:
        tope += n
        if numero <= tope:
            return brazo
    return ""


_ESTADOS_GENERADO = ("GENERADO", "PUBLICADO")


def _lanzado_fase2(producto_key: str) -> bool:
    """Hay un LANZAMIENTO registrado en `_EVENTOS.csv` cuyo motivo dice FASE 2."""
    try:
        eventos = _leer_csv(("PRODUCTOS", "_EVENTOS.csv"))
    except Exception:
        return False
    return any(
        e.get("producto_key") == producto_key
        and e.get("evento") in ("LANZAMIENTO", "LANZAMIENTO_TEST")
        and "FASE 2" in (e.get("motivo") or "").upper()
        for e in eventos
    )


def _checklist_angulo(conceptos: list[dict[str, Any]], estructura: list[tuple[str, int]],
                      requeridos: int, lanzado: bool) -> list[dict[str, Any]]:
    """Qué falta para que el ángulo termine su FASE 2, derivado de los conceptos y eventos ya leídos."""
    generados = [c for c in conceptos if c.get("estado") in _ESTADOS_GENERADO]
    por_campana = {b: sum(1 for c in generados if c.get("campana") == b) for b, _ in estructura}
    desglose = " · ".join(f"Campaña {b}: {por_campana[b]} de {n}" for b, n in estructura)
    publicados = [c for c in conceptos if c.get("ad_id")]
    hecho_gen = requeridos > 0 and len(generados) >= requeridos
    hecho_pub = requeridos > 0 and len(publicados) >= requeridos
    return [
        {"clave": "generar", "rotulo": "Conceptos generados", "cumplido": hecho_gen,
         "detalle": f"{len(generados)} de {requeridos}" + (f" ({desglose})" if desglose else "")},
        {"clave": "publicar", "rotulo": "Publicados en Meta", "cumplido": hecho_pub,
         "detalle": f"{len(publicados)} de {requeridos} con anuncio en Meta"},
        {"clave": "lanzar", "rotulo": "Lanzado", "cumplido": hecho_pub and lanzado,
         "detalle": "LANZAMIENTO de FASE 2 registrado" if lanzado else "Sin LANZAMIENTO de FASE 2 registrado"},
    ]


ACCION_ARMAR_PROMPTS = "producto.armar_prompts_fase2"
ACCION_CONCEPTOS = "nodo.F2.conceptos"
# Los datos de `datos_producto.py` que frenan a `armar_prompts_fase2.py` (los mismos que él bloquea).
DATOS_QUE_FRENAN_PROMPTS = ("packshot", "precio", "registro_sanitario", "perfil_creativo")
MOTIVO_EN_FILA = "Se genera cuando le toque su Fase 2."


def _accion_habilitada(accion_id: str) -> bool:
    from . import acciones

    try:
        return any(a.get("id") == accion_id and a.get("habilitada") for a in acciones.cargar().lista())
    except Exception:
        return False


def _generar_prompts(producto_key: str, angulo: dict[str, Any], revisar: bool) -> dict[str, Any]:
    """El descriptor del botón de un ángulo ganador. Solo el #1 (`ganador_activo`) se puede pedir; los
    datos que le faltan salen de `datos_producto.py` (`fase1.datos_para_arrancar`), sin repetir sus chequeos.
    `revisar=False` (no hay conceptos pendientes) evita correr el script de datos."""
    descriptor: dict[str, Any] = {
        "accion_id": ACCION_ARMAR_PROMPTS,
        "parametros": {"producto_key": producto_key, "angulo_key": angulo["angulo_key"]},
        "habilitada": angulo["rol"] == "ganador_activo",
        "motivo": "",
        "listo": False,
        "faltan": [],
        "accion_perfil": None,
        "aviso": "",
    }
    if not descriptor["habilitada"]:
        descriptor["motivo"] = MOTIVO_EN_FILA
        return descriptor
    if not revisar:
        descriptor["listo"] = True
        return descriptor
    from . import fase1

    datos = fase1.datos_para_arrancar(producto_key)
    if not datos.get("ok", True):
        descriptor["listo"] = True
        descriptor["aviso"] = "; ".join(datos.get("avisos") or [])
        return descriptor
    faltan = [i for i in datos.get("items", [])
              if i.get("clave") in DATOS_QUE_FRENAN_PROMPTS and i.get("estado") == "falta"]
    faltan.sort(key=lambda i: DATOS_QUE_FRENAN_PROMPTS.index(i["clave"]))
    descriptor["faltan"] = faltan
    descriptor["listo"] = not faltan
    if any(i["clave"] == "perfil_creativo" for i in faltan) and _accion_habilitada(ACCION_CONCEPTOS):
        descriptor["accion_perfil"] = ACCION_CONCEPTOS
    return descriptor


def fase2_detalle(producto_key: str) -> dict[str, Any]:
    """Detalles de FASE 2 para el producto: ángulos con su rol, 10 conceptos y órdenes del motor."""
    flujo_data = flujo(producto_key)
    angulos = angulos_de_fase2(producto_key, list(flujo_data.get("angulos_ganadores") or []))
    principal = next((a["angulo_key"] for a in angulos if a["rol"] == "ganador_activo"), "")

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

    carpeta_media = fila_de_producto(producto_key).get("carpeta_media", "") or f"MEDIA_{producto_key}"

    conceptos = []
    for row in creativos_rows:
        cid = row.get("canonico_id", "")
        binfo = canonicos_dict.get(cid, {})
        arch = row.get("archivo", "")
        media_path = ruta("Ads", carpeta_media, arch)
        angulo_key = row.get("angulo_key", "") or principal
        paquete = resolver_prompt_fase2(producto_key, carpeta_media, angulo_key, cid)
        conceptos.append({
            "creativo_id": row.get("creativo_id", ""),
            "archivo": arch,
            "canonico_id": cid,
            "angulo_key": angulo_key,
            "blueprint_nombre": binfo.get("nombre", cid or "Blueprint Canónico"),
            "dispositivo": binfo.get("dispositivo_canonico", ""),
            "cuando_elegirlo": binfo.get("cuando_elegirlo", ""),
            "rol_embudo": row.get("rol_embudo", "") or binfo.get("perfil", {}).get("rol_embudo", "MOFU"),
            "estado": row.get("estado", "PENDIENTE_GENERAR"),
            "ad_id": row.get("ad_id", ""),
            "archivo_existe": media_path.is_file(),
            "notas": row.get("notas", ""),
            **paquete,
        })

    estructura = _estructura_fase2()
    requeridos = sum(n for _, n in estructura)
    vistos: dict[str, int] = {}
    for c in conceptos:
        vistos[c["angulo_key"]] = vistos.get(c["angulo_key"], 0) + 1
        c["numero"] = vistos[c["angulo_key"]]
        c["campana"] = _campana_de(c["numero"], estructura)
    lanzado = _lanzado_fase2(producto_key)

    for angulo in angulos:
        if angulo["rol"] in ("ganador_activo", "ganador_en_fila"):
            angulo["checklist"] = _checklist_angulo(
                [c for c in conceptos if c["angulo_key"] == angulo["angulo_key"]], estructura, requeridos, lanzado)
            hay_pendientes = any(c["angulo_key"] == angulo["angulo_key"] and c["prompt_origen"] == "pendiente"
                                 for c in conceptos)
            angulo["generar"] = _generar_prompts(producto_key, angulo, hay_pendientes)

    angulos_excl = _angulos_probados(producto_key)

    return {
        "producto_key": producto_key,
        "fase": flujo_data.get("fase", "F2"),
        "nodo_actual": flujo_data.get("nodo_actual", ""),
        "angulo_ganador": principal,
        "angulos": angulos,
        "conceptos": conceptos,
        "total_conceptos": len(conceptos),
        "conceptos_requeridos": requeridos,
        "campanas": [{"brazo": b, "conceptos": n} for b, n in estructura],
        "conceptos_generados": sum(1 for c in conceptos if c.get("estado") in ("GENERADO", "PUBLICADO")),
        "reingreso_activo": flujo_data.get("reingreso_activo"),
        "fatiga": {
            "ordenes": flujo_data.get("ordenes", []),
            "angulos_probados": angulos_excl,
            "puede_reingresar": True,
        }
    }


def fase3_detalle(producto_key: str) -> dict[str, Any]:
    """Detalles de FASE 3 (optimización de flujo LucidBot) para el producto: el gate de entrada
    (concepto 2de2, igual al de siempre), el estado de sus dos nodos (`F3.reescribir` reescribe el
    bot, `F3.medir_cierre` mide mensajes→ventas después del CAMBIO_BOT), los eventos CAMBIO_BOT/
    EXCEPCION_CAMBIO_BOT registrados, y el gate duro de salida hacia FASE 4
    (`cierre_post_cambio_bot`) EXACTAMENTE como lo calculó `flujo.py` — esta función nunca
    recalcula mensajes, ventas ni cierre %, solo lee el campo estructurado que `flujo.py --json`
    ya trae (regla de oro del archivo: la app no hace aritmética de negocio)."""
    flujo_data = flujo(producto_key)
    entradas = flujo_data.get("entradas", [])

    def _entrada(fase_id: str) -> dict[str, Any]:
        for e in entradas:
            if e.get("fase") == fase_id:
                return {
                    "ok": bool(e.get("ok")),
                    "observado": e.get("observado", ""),
                    "regla": e.get("regla", ""),
                }
        return {"ok": False, "observado": "Sin evaluar", "regla": ""}

    nodos = flujo_data.get("nodos", [])
    nodo_reescribir = next((n for n in nodos if n.get("id") == "F3.reescribir"), None)
    nodo_medir_cierre = next((n for n in nodos if n.get("id") == "F3.medir_cierre"), None)

    eventos_cambio_bot = []
    try:
        for ev in _leer_csv(("PRODUCTOS", "_EVENTOS.csv")):
            if ev.get("producto_key") == producto_key and ev.get("evento") in ("CAMBIO_BOT", "EXCEPCION_CAMBIO_BOT"):
                eventos_cambio_bot.append({
                    "evento": ev.get("evento", ""),
                    "fecha": ev.get("fecha", ""),
                    "motivo": ev.get("motivo", ""),
                })
    except Exception:
        eventos_cambio_bot = []
    eventos_cambio_bot.sort(key=lambda e: e.get("fecha", ""))

    return {
        "producto_key": producto_key,
        "fase": flujo_data.get("fase", "F3"),
        "nodo_actual": flujo_data.get("nodo_actual", ""),
        "entrada": _entrada("F3"),
        "nodo_reescribir": nodo_reescribir,
        "nodo_medir_cierre": nodo_medir_cierre,
        "eventos_cambio_bot": eventos_cambio_bot,
        # Estructurado por `medir_cierre_post_cambio_bot` (Ads/_TOOLS/flujo.py): fecha_cambio_bot,
        # mensajes, ventas, cierre_pct, min_mensajes, min_cierre_pct, cierre_meta_min_pct/max_pct
        # (benchmark 15-20%, nunca gate), ok, explicacion. None si el producto todavía no llegó a F3.
        "gate_f4": flujo_data.get("cierre_post_cambio_bot"),
        "entrada_f4": _entrada("F4"),
    }


def fase4_detalle(producto_key: str) -> dict[str, Any]:
    """Detalles de FASE 4 (escalado) para el producto: gate de entrada (concepto 2de2 + CAMBIO_BOT
    + cierre_post_cambio_bot, `flujo.py:F4.entrada`), plan CBO 1-1-7 y expansión.

    Ex-`fase3_detalle` (renombrada B3, decisión del operador 28-sep-2026: FASE 3 pasó a ser la
    optimización del flujo del bot, FASE 4 es el escalado de siempre)."""
    flujo_data = flujo(producto_key)
    entradas = flujo_data.get("entradas", [])
    gate_2de2_info = {"ok": False, "observado": "Sin evaluar", "regla": ""}
    for e in entradas:
        if e.get("fase") == "F4":
            gate_2de2_info = {
                "ok": bool(e.get("ok")),
                "observado": e.get("observado", ""),
                "regla": e.get("regla", "")
            }
            break

    plan_txt = ruta("PRODUCTOS", producto_key, "4_PLAN_ESCALADO.txt")
    plan_json = ruta("PRODUCTOS", producto_key, "_PLAN_FASE4.json")
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
        "fase": flujo_data.get("fase", "F4"),
        "nodo_actual": flujo_data.get("nodo_actual", ""),
        "gate_2de2": gate_2de2_info,
        "plan_cbo": {
            "estructura": "1-1-7 CBO",
            "descripcion": "1 Campaña CBO, 1 Conjunto de 7 anuncios con el concepto validado en 2 de 2 × 7 hooks (microángulos)",
            "tiene_plan": tiene_plan,
            "estado": "GENERADO" if tiene_plan else "PENDIENTE",
            "archivo": "4_PLAN_ESCALADO.txt" if plan_txt.is_file() else ("_PLAN_FASE4.json" if plan_json.is_file() else None)
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


