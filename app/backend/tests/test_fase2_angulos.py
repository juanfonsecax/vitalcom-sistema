"""test_fase2_angulos.py — FASE 2 por ÁNGULO: roles, orden de la fila y etiquetas por dato.

Sistema mínimo de mentira con 6 ángulos: 3 ganadores (el orden lo dicta `flujo.py`, que ya lo
rankeó con `ranking_ganadores`) y 3 perdedores con estados distintos. `flujo()` y `decisiones()`
se mockean (son subprocess); `_ESTADO_ANGULOS.csv` se escribe de verdad.
"""

from __future__ import annotations

from pathlib import Path

import pytest

GANADORES = ["ANG_RESISTENCIA", "ANG_FALSIFICACION", "ANG_MEDICOS"]


def _celda(nombre: str, estado: str, ventas_acum: float, accion: str = "") -> dict:
    return {
        "celda": nombre, "estado": estado, "accion_codigo": estado, "accion_sugerida": accion,
        "ventas": 5.0, "ventas_acum": ventas_acum, "cpa_real_q": 50.0, "ic": [30.0, 50.0, 90.0],
        "cierre_pct": 12.5, "spend_q": 800.0, "spend_acum_q": 3000.0, "bloqueo_fase": None,
    }


CELDAS = [
    _celda("ANG_RESISTENCIA", "ESCALAR", 102),
    _celda("ANG_FALSIFICACION", "RENOVAR", 65, "RENOVAR CREATIVO: rotá el concepto"),
    _celda("ANG_MEDICOS", "RENOVAR", 41),
    _celda("ANG_PERDEDOR_PAUSAR", "PAUSAR", 3, "PAUSAR: CPA sobre break-even"),
    _celda("ANG_MIDIENDO", "SEGUIR_MIDIENDO", 4),
]

ESTADO_ANGULOS = (
    "producto_key,angulo_key,estado,ultimo_dia_gasto,dias_sin_gasto\n"
    "PX,ANG_RESISTENCIA,ESCALANDO,2026-09-25,0\n"
    "PX,ANG_FALSIFICACION,ESCALANDO,2026-09-25,0\n"
    "PX,ANG_MEDICOS,EN_DECLIVE,2026-09-25,0\n"
    "PX,ANG_APAGADO,APAGADO_ABANDONO,2026-08-16,40\n"
    "PX,ANG_PERDEDOR_PAUSAR,SOSTENIDO,2026-09-25,0\n"
    "OTRO,ANG_AJENO,ESCALANDO,2026-09-25,0\n"
)

CONCATENADO = ("ANG_RESISTENCIA (ESCALAR 25v CPA Q50.6); ANG_FALSIFICACION (histórico 65v CPA Q43.7 ≤ BE Q105.9)")


@pytest.fixture()
def sistema_angulos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import config, contratos

    (tmp_path / "DOCTRINA").mkdir()
    (tmp_path / "DOCTRINA" / "FLUJO.json").write_text("{}", encoding="utf-8")
    (tmp_path / "PRODUCTOS").mkdir()
    (tmp_path / "PRODUCTOS" / "_ESTADO_ANGULOS.csv").write_text(ESTADO_ANGULOS, encoding="utf-8")
    (tmp_path / "PRODUCTOS" / "_DIM_PRODUCTOS.csv").write_text(
        "producto_key,carpeta_media\nPX,MEDIA_PX\n", encoding="utf-8"
    )
    (tmp_path / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(
        "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas\n"
        "PX,PX_F2_1,PX_F2_1.png,,CN01,MOFU,PENDIENTE_GENERAR,,\n"
        "PX,PX_F2_2,PX_F2_2.png,ANG_FALSIFICACION,CN02,MOFU,PENDIENTE_GENERAR,,\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("VITALCOM_BASE", str(tmp_path))
    config.base.cache_clear()
    monkeypatch.setattr(
        contratos, "flujo",
        lambda pk, hoy=None: {
            "fase": "F2", "nodo_actual": "F2.conceptos", "angulos_ganadores": GANADORES,
            "entradas": [{"fase": "F2", "ok": True, "observado": CONCATENADO}],
            "ordenes": [{"celda": "ANG_FALSIFICACION", "estado": "RENOVAR", "accion": "rotá"}],
        },
    )
    monkeypatch.setattr(contratos, "decisiones", lambda: {"productos": [{"producto_key": "PX", "celdas": CELDAS}]})
    try:
        yield tmp_path
    finally:
        config.base.cache_clear()


def _por_clave(detalle: dict) -> dict:
    return {a["angulo_key"]: a for a in detalle["angulos"]}


def test_cubre_todos_los_angulos_del_producto_y_solo_los_suyos(sistema_angulos: Path):
    from vitalcom_app import contratos

    detalle = contratos.fase2_detalle("PX")
    claves = [a["angulo_key"] for a in detalle["angulos"]]
    assert set(claves) == set(GANADORES) | {"ANG_PERDEDOR_PAUSAR", "ANG_MIDIENDO", "ANG_APAGADO"}
    assert len(claves) == 6
    assert "ANG_AJENO" not in claves


def test_los_ganadores_respetan_el_orden_de_flujo_y_tienen_posicion(sistema_angulos: Path):
    from vitalcom_app import contratos

    detalle = contratos.fase2_detalle("PX")
    ganadores = [a for a in detalle["angulos"] if a["posicion"] is not None]
    assert [a["angulo_key"] for a in ganadores] == GANADORES
    assert [a["posicion"] for a in ganadores] == [1, 2, 3]
    assert [a["rol"] for a in ganadores] == ["ganador_activo", "ganador_en_fila", "ganador_en_fila"]
    # los ganadores van primero en la lista
    assert [a["angulo_key"] for a in detalle["angulos"][:3]] == GANADORES


def test_los_perdedores_se_etiquetan_por_dato(sistema_angulos: Path):
    from vitalcom_app import contratos

    a = _por_clave(contratos.fase2_detalle("PX"))
    assert a["ANG_APAGADO"]["rol"] == "perdedor"
    assert a["ANG_APAGADO"]["etiqueta"] == "ya apagado (40 días sin gastar)"
    assert a["ANG_APAGADO"]["dias_sin_gasto"] == 40
    assert a["ANG_APAGADO"]["ultimo_dia_gasto"] == "2026-08-16"
    # sigue gastando y el motor ordena PAUSAR: se muestra la orden, no se decide acá
    assert a["ANG_PERDEDOR_PAUSAR"]["rol"] == "perdedor"
    assert a["ANG_PERDEDOR_PAUSAR"]["estado"] == "PAUSAR"
    assert a["ANG_PERDEDOR_PAUSAR"]["accion_sugerida"].startswith("PAUSAR")
    # ni ganó ni tiene orden de pausa: sigue midiéndose
    assert a["ANG_MIDIENDO"]["rol"] == "midiendo"
    assert a["ANG_MIDIENDO"]["etiqueta"] == "midiendo"


def test_pasa_el_veredicto_del_motor_sin_tocarlo(sistema_angulos: Path):
    from vitalcom_app import contratos

    a = _por_clave(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]
    assert a["estado"] == "ESCALAR"
    assert a["ventas_acum"] == 102
    assert a["cpa_real_q"] == 50.0
    assert a["ic"] == [30.0, 50.0, 90.0]
    assert a["cierre_pct"] == 12.5
    assert a["spend_q"] == 800.0
    assert a["estado_angulo"] == "ESCALANDO"


def test_el_angulo_de_respaldo_es_el_numero_1_y_nunca_el_texto_concatenado(sistema_angulos: Path):
    from vitalcom_app import contratos

    detalle = contratos.fase2_detalle("PX")
    assert detalle["angulo_ganador"] == "ANG_RESISTENCIA"
    por_id = {c["creativo_id"]: c for c in detalle["conceptos"]}
    # la fila sin angulo_key cae al #1; la que lo trae conserva el suyo
    assert por_id["PX_F2_1"]["angulo_key"] == "ANG_RESISTENCIA"
    assert por_id["PX_F2_2"]["angulo_key"] == "ANG_FALSIFICACION"
    assert "ANG_RESISTENCIA" in por_id["PX_F2_1"]["comando_generar"]
    for c in detalle["conceptos"]:
        assert "(" not in c["angulo_key"] and ";" not in c["angulo_key"]
        assert CONCATENADO not in (c.get("comando_generar") or "")
    assert CONCATENADO not in str(detalle["angulo_ganador"])


def test_sin_ganadores_no_hay_numero_1_y_nadie_se_inventa(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(
        contratos, "flujo", lambda pk, hoy=None: {"fase": "F1", "nodo_actual": "F1.x", "entradas": []}
    )
    detalle = contratos.fase2_detalle("PX")
    assert detalle["angulo_ganador"] == ""
    assert all(a["posicion"] is None for a in detalle["angulos"])
    assert not any(a["rol"].startswith("ganador") for a in detalle["angulos"])


def test_el_contrato_valida_contra_el_modelo(sistema_angulos: Path):
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    modelo = Fase2Detalle(**contratos.fase2_detalle("PX"))
    assert len(modelo.angulos) == 6
    assert modelo.angulos[0].rol == "ganador_activo"


def test_no_se_rellenan_conceptos_que_nadie_va_a_generar(sistema_angulos: Path):
    from vitalcom_app import contratos

    detalle = contratos.fase2_detalle("PX")
    # solo las filas reales de _DIM_CREATIVOS.csv; ningun relleno hasta 10
    assert [c["creativo_id"] for c in detalle["conceptos"]] == ["PX_F2_1", "PX_F2_2"]
    assert detalle["total_conceptos"] == 2
