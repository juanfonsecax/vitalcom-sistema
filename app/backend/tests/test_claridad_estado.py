"""test_claridad_estado.py — el estado corto que lee el operador: paso, bloqueante y dueño.

La app no inventa prosa: el bloqueante sale de `falta_para_cumplir`/`bloqueantes` de `flujo.py`
(vía `_FLUJO.json` en el portafolio) y los faltantes de conceptos son resta del contrato.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FALTA = {
    "dato": "conceptos GENERADOS (10 = A 5 + B 5, de _PARAMETROS_PUBLICACION.csv)",
    "ok": False,
    "observado": "5 fila(s) · esperado ≥ 10",
    "dueno": "etapa-9 (filas) + etapa-render (PNG)",
    "regla": "R3F-13",
}
FALTA_CON_TEXTO = {**FALTA, "falta": "faltan 5 conceptos"}
NODOS = [
    {"id": "F2.conceptos", "titulo": "Fabricar los 10 conceptos", "ejecutor": "", "ejecutor_tipo": "", "como": ""},
]


def test_situacion_toma_el_primer_pendiente_con_su_dueno():
    from vitalcom_app import contratos

    s = contratos.situacion_de_flujo(
        {"nodo_actual": "F2.conceptos", "nodos": NODOS, "bloqueantes": [], "falta_para_cumplir": [FALTA],
         "fase_titulo": "FASE 2 · TESTEO DE CONCEPTOS"}
    )
    assert s["paso_titulo"] == "Fabricar los 10 conceptos"
    assert s["bloqueante_principal"] == "conceptos GENERADOS: 5 fila(s) · esperado ≥ 10"
    assert s["dueno_bloqueante"] == "etapa-9 (filas) + etapa-render (PNG)"
    assert s["fase_titulo"] == "FASE 2 · TESTEO DE CONCEPTOS"


def test_situacion_usa_el_falta_del_operador_y_sin_el_cae_al_texto_tecnico():
    from vitalcom_app import contratos

    con = contratos.situacion_de_flujo({"falta_para_cumplir": [FALTA_CON_TEXTO]})
    assert con["bloqueante_principal"] == "faltan 5 conceptos"
    sin = contratos.situacion_de_flujo({"falta_para_cumplir": [FALTA]})
    assert sin["bloqueante_principal"] == "conceptos GENERADOS: 5 fila(s) · esperado ≥ 10"


def test_situacion_prefiere_bloqueantes_y_sin_nada_queda_vacia():
    from vitalcom_app import contratos

    duro = {"dato": "ángulo ganador", "observado": "ninguno", "dueno": "operador"}
    s = contratos.situacion_de_flujo({"bloqueantes": [duro], "falta_para_cumplir": [FALTA]})
    assert s["bloqueante_principal"] == "ángulo ganador: ninguno"
    vacia = contratos.situacion_de_flujo({})
    assert vacia["bloqueante_principal"] is None and vacia["dueno_bloqueante"] is None


def test_portafolio_sirve_el_bloqueante_sin_una_llamada_por_producto(cliente, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    productos = contratos.productos_con_mercado()
    clave = productos[0]["producto_key"]
    monkeypatch.setattr(
        contratos, "flujo_global",
        lambda: {"productos": [{"producto_key": clave, "nodo_actual": "F2.conceptos", "nodos": NODOS,
                                "bloqueantes": [], "falta_para_cumplir": [FALTA_CON_TEXTO],
                                "fase_titulo": "FASE 2 · TESTEO DE CONCEPTOS"}]},
    )

    def _no_subproceso(*a, **k):
        raise AssertionError("el portafolio no puede correr flujo.py por producto")

    monkeypatch.setattr(contratos, "flujo", _no_subproceso)
    servido = {p["producto_key"]: p for p in cliente.get("/api/productos").json()}[clave]
    assert servido["bloqueante_principal"] == "faltan 5 conceptos"
    assert servido["dueno_bloqueante"] == "etapa-9 (filas) + etapa-render (PNG)"
    assert servido["paso_titulo"] == "Fabricar los 10 conceptos"
    assert servido["fase_titulo"] == "FASE 2 · TESTEO DE CONCEPTOS"


def test_portafolio_sin_flujo_global_sigue_funcionando(cliente, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    def _ausente():
        raise contratos.ContratoAusente("no hay _FLUJO.json")

    monkeypatch.setattr(contratos, "flujo_global", _ausente)
    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 200
    assert all(p["bloqueante_principal"] is None for p in respuesta.json())


@pytest.fixture()
def sistema_f2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import config, contratos

    (tmp_path / "DOCTRINA").mkdir()
    (tmp_path / "DOCTRINA" / "FLUJO.json").write_text("{}", encoding="utf-8")
    (tmp_path / "PRODUCTOS").mkdir()
    (tmp_path / "PRODUCTOS" / "_DIM_PRODUCTOS.csv").write_text(
        "producto_key,carpeta_media\nPX,MEDIA_PX\n", encoding="utf-8"
    )
    (tmp_path / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(
        "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas\n"
        "PX,PX_F2_1,PX_F2_1.png,,CN01,MOFU,GENERADO,,\n"
        "PX,PX_F2_2,PX_F2_2.png,,CN02,MOFU,PENDIENTE_GENERAR,,\n",
        encoding="utf-8",
    )
    (tmp_path / "PRODUCTOS" / "_PARAMETROS_PUBLICACION.csv").write_text(
        "fase,brazo,anuncios_por_conjunto\n2,A,5\n2,B,5\n", encoding="utf-8"
    )
    monkeypatch.setenv("VITALCOM_BASE", str(tmp_path))
    config.base.cache_clear()
    monkeypatch.setattr(
        contratos, "flujo",
        lambda pk, hoy=None: {
            "fase": "F2", "fase_titulo": "FASE 2 · TESTEO DE CONCEPTOS", "nodo_actual": "F2.conceptos",
            "nodos": NODOS, "ejecutor": "subagente `etapa-9` (Task, subagent_type=etapa-9)",
            "angulos_ganadores": [], "bloqueantes": [], "falta_para_cumplir": [FALTA_CON_TEXTO],
            "avance": {"a": "F3", "ok": False, "observado": "0 campañas", "regla": ""},
        },
    )
    monkeypatch.setattr(contratos, "decisiones", lambda: {"productos": []})
    try:
        yield tmp_path
    finally:
        config.base.cache_clear()


def test_fase2_dice_cuantos_conceptos_faltan_y_quien_los_hace(sistema_f2: Path):
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    d = contratos.fase2_detalle("PX")
    assert d["conceptos_generados"] == 1
    assert d["conceptos_requeridos"] == 10
    assert d["conceptos_faltan"] == 9
    assert d["fase_validada"] is False
    assert d["paso_titulo"] == "Fabricar los 10 conceptos"
    assert d["bloqueante_principal"] == "faltan 5 conceptos"
    assert d["dueno_bloqueante"] == "etapa-9 (filas) + etapa-render (PNG)"
    assert d["ejecutor"].startswith("subagente `etapa-9`")
    assert d["fase_titulo"] == "FASE 2 · TESTEO DE CONCEPTOS"
    Fase2Detalle(**d)
