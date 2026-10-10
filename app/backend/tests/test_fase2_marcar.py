"""test_fase2_marcar.py — el botón «Marcar como generadas las imágenes que ya subiste» por ángulo.

`fase2_detalle` entrega, por ángulo, cuántos conceptos IMAGEN siguen en PENDIENTE_GENERAR con su
archivo ya en disco (la cuenta es del backend) y la acción del manifiesto que los marca GENERADO.
Sin ninguno listo para marcar, el campo es None.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from test_fase2_angulos import PARAMETROS, sistema_angulos  # noqa: F401

ACCION = "producto.marcar_conceptos_generados"
CABECERA = "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas,formato\n"


def _escribir(base: Path, filas: list[tuple[str, str, str, str]], con_archivo: set[str]) -> None:
    """filas: (creativo_id, angulo_key, estado, formato). `con_archivo`: ids cuyo PNG existe."""
    (base / "PRODUCTOS" / "_PARAMETROS_PUBLICACION.csv").write_text(PARAMETROS, encoding="utf-8")
    cuerpo = "".join(f"PX,{c},{c}.png,{a},CN01_X,MOFU,{e},,,{f}\n" for c, a, e, f in filas)
    (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(CABECERA + cuerpo, encoding="utf-8")
    media = base / "Ads" / "MEDIA_PX"
    media.mkdir(parents=True, exist_ok=True)
    for c in con_archivo:
        (media / f"{c}.png").write_bytes(b"\x89PNG\r\n\x1a\n")


@pytest.fixture()
def habilitada(monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: True)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)


def _angulos(base: Path) -> dict:
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    detalle = contratos.fase2_detalle("PX")
    Fase2Detalle(**detalle)
    return {x["angulo_key"]: x for x in detalle["angulos"]}


def test_cuenta_solo_pendientes_imagen_con_archivo(sistema_angulos: Path, habilitada):
    _escribir(sistema_angulos, [
        ("A1", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "IMAGEN"),
        ("A2", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "IMAGEN"),
        ("A3", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "IMAGEN"),   # sin archivo
        ("A4", "ANG_RESISTENCIA", "GENERADO", "IMAGEN"),            # ya marcado
        ("A5", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "VIDEO"),    # el video no se marca acá
    ], {"A1", "A2", "A4", "A5"})
    m = _angulos(sistema_angulos)["ANG_RESISTENCIA"]["marcar"]
    assert m["accion_id"] == ACCION and m["listos"] == 2 and m["habilitada"] is True
    assert m["parametros"] == {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA"}


def test_sin_nada_que_marcar_no_hay_boton(sistema_angulos: Path, habilitada):
    _escribir(sistema_angulos, [("A1", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "IMAGEN")], set())
    assert _angulos(sistema_angulos)["ANG_RESISTENCIA"].get("marcar") is None


def test_cada_angulo_cuenta_lo_suyo(sistema_angulos: Path, habilitada):
    _escribir(sistema_angulos, [
        ("A1", "ANG_RESISTENCIA", "PENDIENTE_GENERAR", "IMAGEN"),
        ("B1", "ANG_FALSIFICACION", "PENDIENTE_GENERAR", "IMAGEN"),
        ("B2", "ANG_FALSIFICACION", "PENDIENTE_GENERAR", "IMAGEN"),
    ], {"B1", "B2"})
    a = _angulos(sistema_angulos)
    assert a["ANG_RESISTENCIA"].get("marcar") is None
    assert a["ANG_FALSIFICACION"]["marcar"]["listos"] == 2
