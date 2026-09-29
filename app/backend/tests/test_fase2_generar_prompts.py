"""test_fase2_generar_prompts.py — el botón «Generar los prompts de este ángulo» (C3).

`fase2_detalle` entrega, por cada ganador, el descriptor de la acción `producto.armar_prompts_fase2`
(id + parámetros) y qué dato lo frena, derivado de `datos_producto.py` (`fase1.datos_para_arrancar`,
que aquí se mockea: es un subprocess). Reusa el sistema de mentira de `test_fase2_angulos.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from test_fase2_angulos import GANADORES, sistema_angulos  # noqa: F401

FALTA_PACKSHOT = {"clave": "packshot", "rotulo": "Foto del producto (packshot)", "estado": "falta",
                  "detalle": "No hay foto declarada.", "como_resolver": "Subí la foto.",
                  "accion": "producto.cargar_packshot"}
FALTA_PERFIL = {"clave": "perfil_creativo", "rotulo": "Perfil creativo del ángulo #1", "estado": "falta",
                "detalle": "No hay perfil creativo del ángulo ANG_RESISTENCIA.",
                "como_resolver": "Claude lo prepara.", "accion": None}
OK_PRECIO = {"clave": "precio", "rotulo": "Precio de venta", "estado": "ok", "detalle": "1x Q150",
             "como_resolver": "", "accion": None}
OTRO_FALTANTE = {"clave": "page_id", "rotulo": "Página de Facebook", "estado": "falta", "detalle": "Falta.",
                 "como_resolver": "Pegá el page_id.", "accion": "producto.cargar_page_id"}


def _datos(monkeypatch: pytest.MonkeyPatch, items: list[dict], ok: bool = True) -> list[str]:
    from vitalcom_app import fase1

    llamadas: list[str] = []

    def falso(pk: str) -> dict:
        llamadas.append(pk)
        return {"producto_key": pk, "ok": ok, "items": items, "avisos": [] if ok else ["No pude revisar."]}

    monkeypatch.setattr(fase1, "datos_para_arrancar", falso)
    return llamadas


def _generar(detalle: dict) -> dict:
    return {a["angulo_key"]: a.get("generar") for a in detalle["angulos"]}


def test_el_numero_1_lleva_la_accion_y_sus_parametros(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    _datos(monkeypatch, [OK_PRECIO])
    g = _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]
    assert g["accion_id"] == "producto.armar_prompts_fase2"
    assert g["parametros"] == {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA"}
    assert g["habilitada"] is True and g["listo"] is True and g["faltan"] == []


def test_la_accion_del_descriptor_existe_en_el_manifiesto_real():
    import json

    from vitalcom_app import config, contratos

    manifiesto = json.loads(Path(__file__).resolve().parents[3].joinpath("VISTAS", "_MANIFIESTO.json").read_text("utf-8"))
    accion = next(a for a in manifiesto["acciones"]["lista"] if a["id"] == contratos.ACCION_ARMAR_PROMPTS)
    assert accion["ejecutor_tipo"] == "script" and accion["visibilidad"] == "boton" and accion["habilitada"]
    assert set(accion["parametros"]) == {"producto_key", "angulo_key"}
    assert config  # el módulo carga sin base de prueba


def test_los_ganadores_en_fila_no_se_pueden_pedir_y_no_corren_el_chequeo(
    sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch
):
    from vitalcom_app import contratos

    llamadas = _datos(monkeypatch, [FALTA_PACKSHOT])
    g = _generar(contratos.fase2_detalle("PX"))
    for clave in GANADORES[1:]:
        assert g[clave]["habilitada"] is False
        assert g[clave]["motivo"] == "Se genera cuando le toque su Fase 2."
        assert g[clave]["faltan"] == []
        assert g[clave]["parametros"]["angulo_key"] == clave
    assert llamadas == ["PX"]  # una sola revisión, la del #1


def test_perdedores_y_midiendo_no_tienen_boton(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    _datos(monkeypatch, [])
    g = _generar(contratos.fase2_detalle("PX"))
    for clave in ("ANG_APAGADO", "ANG_PERDEDOR_PAUSAR", "ANG_MIDIENDO"):
        assert g[clave] is None


def test_si_falta_un_dato_dice_cual_y_como_arreglarlo(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    _datos(monkeypatch, [FALTA_PERFIL, OK_PRECIO, OTRO_FALTANTE, FALTA_PACKSHOT])
    g = _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]
    assert g["listo"] is False and g["habilitada"] is True
    # solo los datos que frenan a armar_prompts_fase2 (page_id no), en el orden del script
    assert [i["clave"] for i in g["faltan"]] == ["packshot", "perfil_creativo"]
    assert g["faltan"][0]["accion"] == "producto.cargar_packshot"
    assert g["faltan"][0]["como_resolver"] == "Subí la foto."
    assert g["faltan"][1]["accion"] is None


def test_perfil_creativo_sin_accion_habilitada_queda_para_claude(
    sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch
):
    from vitalcom_app import contratos

    _datos(monkeypatch, [FALTA_PERFIL])
    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: False)
    assert _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]["accion_perfil"] is None
    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: accion_id == "nodo.F2.conceptos")
    assert _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]["accion_perfil"] == "nodo.F2.conceptos"
    # y si lo que falta es otra cosa, no se ofrece
    _datos(monkeypatch, [FALTA_PACKSHOT])
    assert _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]["accion_perfil"] is None


def test_si_datos_producto_no_responde_no_se_inventa_un_bloqueo(
    sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch
):
    from vitalcom_app import contratos

    _datos(monkeypatch, [], ok=False)
    g = _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]
    assert g["listo"] is True and g["faltan"] == [] and "No pude revisar" in g["aviso"]


def test_sin_conceptos_pendientes_no_corre_el_chequeo(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    llamadas = _datos(monkeypatch, [FALTA_PACKSHOT])
    monkeypatch.setattr(
        contratos, "resolver_prompt_fase2",
        lambda pk, carpeta, angulo, cid: {"prompt": "p", "prompt_origen": "paquete", "referencia_url": None,
                                          "comando_generar": None},
    )
    g = _generar(contratos.fase2_detalle("PX"))["ANG_RESISTENCIA"]
    assert llamadas == [] and g["listo"] is True


def test_el_contrato_valida_contra_el_modelo_con_el_descriptor(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    _datos(monkeypatch, [FALTA_PACKSHOT])
    modelo = Fase2Detalle(**contratos.fase2_detalle("PX"))
    primero = modelo.angulos[0].generar
    assert primero is not None and primero.faltan[0].clave == "packshot"
    assert modelo.angulos[1].generar.habilitada is False
    assert modelo.angulos[-1].generar is None
