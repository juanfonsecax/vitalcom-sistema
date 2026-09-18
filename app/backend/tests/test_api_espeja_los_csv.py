"""La API dice lo mismo que los CSV, sin transformar nada.

Criterio de aceptación del Hito 1: para cada producto, fase y nodo de la API = los de
`_ESTADO_FLUJO.csv`. Si alguien mete una traducción, un redondeo o un "mejor nombre" en el
camino, esto se pone rojo.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _csv(base: Path, nombre: str) -> list[dict[str, str]]:
    with (base / "PRODUCTOS" / nombre).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_lista_los_mismos_productos_que_el_csv(cliente, base_declarada):
    esperado = [fila["producto_key"] for fila in _csv(base_declarada, "_DIM_PRODUCTOS.csv")]
    servidos = [p["producto_key"] for p in cliente.get("/api/productos").json()]
    assert servidos == esperado


def test_fase_y_nodo_salen_del_estado_flujo_sin_transformar(cliente, base_declarada):
    estado = {f["producto_key"]: f for f in _csv(base_declarada, "_ESTADO_FLUJO.csv")}
    for producto in cliente.get("/api/productos").json():
        fila = estado.get(producto["producto_key"])
        if fila is None:  # producto todavía sin evaluar por flujo.py
            assert producto["fase"] is None and producto["nodo_actual"] is None
            continue
        assert producto["fase"] == fila["fase"]
        assert producto["nodo_actual"] == fila["nodo_actual"]
        assert producto["estado_flujo"] == fila["estado"]
        assert producto["siguiente_ejecutor"] == fila["siguiente_ejecutor"]
        assert producto["evaluado_el"] == fila["evaluado_el"]


def test_los_montos_viajan_tal_cual_el_csv(cliente, base_declarada):
    """Ni conversión de moneda ni redondeo: el texto del CSV, carácter por carácter."""
    filas = {f["producto_key"]: f for f in _csv(base_declarada, "_DIM_PRODUCTOS.csv")}
    for producto in cliente.get("/api/productos").json():
        fila = filas[producto["producto_key"]]
        for campo in ("costo_q", "precio_base_q", "cpa_base_q", "cpa_be_q"):
            assert producto[campo] == fila[campo], campo


def test_la_fase_vigente_no_es_la_columna_bitacora(cliente, base_declarada):
    """`_DIM_PRODUCTOS.fase` quedó como bitácora; la vigente es la derivada (CLAUDE.md)."""
    filas = {f["producto_key"]: f for f in _csv(base_declarada, "_DIM_PRODUCTOS.csv")}
    for producto in cliente.get("/api/productos").json():
        assert producto["fase_bitacora"] == filas[producto["producto_key"]]["fase"]


def test_detalle_de_producto_es_la_salida_de_flujo_py(cliente, base_declarada):
    import subprocess

    pk = _csv(base_declarada, "_ESTADO_FLUJO.csv")[0]["producto_key"]
    servido = cliente.get(f"/api/productos/{pk}").json()
    directo = json.loads(
        subprocess.run(
            ["python", str(base_declarada / "Ads" / "_TOOLS" / "flujo.py"), pk,
             "--json", "--sin-escribir", "--silencioso"],
            cwd=str(base_declarada), capture_output=True, text=True,
            encoding="utf-8", check=True,
        ).stdout
    )
    for campo in ("producto_key", "fase", "nodo_actual", "estado", "ejecutor"):
        assert servido[campo] == directo[campo], campo
    assert [n["id"] for n in servido["nodos"]] == [n["id"] for n in directo["nodos"]]


def test_producto_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/api/productos/NO_EXISTE_ESTE")
    assert respuesta.status_code == 404
    assert "_DIM_PRODUCTOS.csv" in respuesta.json()["detail"]


def test_decisiones_se_sirven_tal_cual(cliente, base_declarada):
    crudo = json.loads((base_declarada / "PRODUCTOS" / "_DECISIONES.json").read_text("utf-8"))
    servido = cliente.get("/api/decisiones").json()
    assert servido["generado"] == crudo["generado"]
    assert servido["rezago_dias"] == crudo["rezago_dias"]
    assert servido["resumen_acciones"] == crudo["resumen_acciones"]
    assert len(servido["productos"]) == len(crudo["productos"])


def test_salud_se_sirve_tal_cual(cliente, base_declarada):
    crudo = json.loads((base_declarada / "VISTAS" / "_ESTADO.json").read_text("utf-8"))
    servido = cliente.get("/api/salud").json()
    assert servido["generado"] == crudo["generado"]
    assert [v["id"] for v in servido["vistas"]] == [v["id"] for v in crudo["vistas"]]


def test_la_app_corre_sobre_la_carpeta_real(cliente, base_declarada):
    """La lección del 17-sep: en un worktree faltan las Ads/MEDIA_* y el estado sale falso."""
    assert Path(cliente.get("/api/sistema").json()["base"]) == base_declarada
