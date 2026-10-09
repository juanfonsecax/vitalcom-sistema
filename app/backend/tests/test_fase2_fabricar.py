"""test_fase2_fabricar.py — el botón «Generar los conceptos que faltan (N)» por ángulo ganador.

`fase2_detalle` entrega, por cada ángulo GANADOR (#1 y en fila), cuántos conceptos le faltan
(`requeridos − registrados`, la cuenta es del backend), la acción del manifiesto que los fabrica
y si ya hay un trabajo corriendo para ese producto+ángulo. La acción nueva
(`producto.fabricar_conceptos_fase2`) fabrica SOLO (etapa-9), sin render ni Meta; su prompt sale
del bloque `acciones.claude` del manifiesto, no de prosa en Python.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_fase2_angulos import GANADORES, PARAMETROS, sistema_angulos  # noqa: F401

ACCION = "producto.fabricar_conceptos_fase2"
RAIZ = Path(__file__).resolve().parents[3]


def _manifiesto() -> dict:
    return json.loads((RAIZ / "VISTAS" / "_MANIFIESTO.json").read_text("utf-8"))


def _accion(accion_id: str) -> dict:
    return next(a for a in _manifiesto()["acciones"]["lista"] if a["id"] == accion_id)


def _escribir_creativos(base: Path, n_resistencia: int, n_falsificacion: int = 0) -> None:
    (base / "PRODUCTOS" / "_PARAMETROS_PUBLICACION.csv").write_text(PARAMETROS, encoding="utf-8")
    filas = [
        f"PX,PX_R{i},PX_R{i}.png,ANG_RESISTENCIA,CN{i:02d}_X,MOFU,GENERADO,,\n" for i in range(1, n_resistencia + 1)
    ] + [
        f"PX,PX_F{i},PX_F{i}.png,ANG_FALSIFICACION,CN{i + 20:02d}_Y,MOFU,PENDIENTE_GENERAR,,\n"
        for i in range(1, n_falsificacion + 1)
    ]
    (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(
        "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas\n" + "".join(filas),
        encoding="utf-8",
    )


@pytest.fixture()
def habilitada(monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: True)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)


def test_cada_ganador_dice_cuantos_conceptos_le_faltan(sistema_angulos: Path, habilitada):
    from vitalcom_app import contratos

    _escribir_creativos(sistema_angulos, 5, 2)
    a = {x["angulo_key"]: x for x in contratos.fase2_detalle("PX")["angulos"]}
    f = a["ANG_RESISTENCIA"]["fabricar"]
    assert f["accion_id"] == ACCION and f["faltan"] == 5 and f["habilitada"] is True
    assert f["parametros"] == {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA", "n": "5"}
    assert f["trabajo_en_curso"] is None
    # un concepto registrado (aunque falte renderizarlo) cuenta como existente: no se duplica
    assert a["ANG_FALSIFICACION"]["fabricar"]["faltan"] == 8
    assert a["ANG_FALSIFICACION"]["fabricar"]["parametros"]["n"] == "8"
    # sin ningún concepto: faltan los 10
    assert a["ANG_MEDICOS"]["fabricar"]["faltan"] == 10


def test_los_perdedores_no_llevan_boton(sistema_angulos: Path, habilitada):
    from vitalcom_app import contratos

    _escribir_creativos(sistema_angulos, 1)
    a = {x["angulo_key"]: x for x in contratos.fase2_detalle("PX")["angulos"]}
    for perdedor in ("ANG_PERDEDOR_PAUSAR", "ANG_MIDIENDO", "ANG_APAGADO"):
        assert a[perdedor].get("fabricar") is None


def test_con_todos_los_conceptos_no_falta_nada(sistema_angulos: Path, habilitada):
    from vitalcom_app import contratos

    _escribir_creativos(sistema_angulos, 10)
    f = {x["angulo_key"]: x for x in contratos.fase2_detalle("PX")["angulos"]}["ANG_RESISTENCIA"]["fabricar"]
    assert f["faltan"] == 0


def test_un_trabajo_en_curso_se_informa_y_la_accion_deshabilitada_tambien(
    sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch,
):
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    _escribir_creativos(sistema_angulos, 5)
    visto: list[tuple] = []

    def en_curso(accion_id, pk, angulo):
        visto.append((accion_id, pk, angulo))
        return "abc123" if angulo == "ANG_RESISTENCIA" else None

    monkeypatch.setattr(contratos, "_trabajo_en_curso", en_curso)
    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: False)
    detalle = contratos.fase2_detalle("PX")
    a = {x["angulo_key"]: x for x in detalle["angulos"]}
    assert a["ANG_RESISTENCIA"]["fabricar"]["trabajo_en_curso"] == "abc123"
    assert a["ANG_FALSIFICACION"]["fabricar"]["trabajo_en_curso"] is None
    assert a["ANG_RESISTENCIA"]["fabricar"]["habilitada"] is False
    assert (ACCION, "PX", "ANG_RESISTENCIA") in visto
    Fase2Detalle(**detalle)


def test_si_no_se_puede_consultar_los_trabajos_el_detalle_no_se_cae(
    sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch,
):
    from vitalcom_app import contratos, trabajos

    _escribir_creativos(sistema_angulos, 5)
    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: True)

    def roto(*a, **k):
        raise RuntimeError("DBOS no está lanzado")

    monkeypatch.setattr(trabajos, "listar", roto)
    f = {x["angulo_key"]: x for x in contratos.fase2_detalle("PX")["angulos"]}["ANG_RESISTENCIA"]["fabricar"]
    assert f["trabajo_en_curso"] is None


def test_trabajo_en_curso_mira_accion_producto_y_angulo(monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos, trabajos

    filas = [
        {"job_id": "viejo", "accion_id": ACCION, "producto_key": "PX", "angulo_key": "A", "estado": "EXITO"},
        {"job_id": "otro-angulo", "accion_id": ACCION, "producto_key": "PX", "angulo_key": "B", "estado": "CORRIENDO"},
        {"job_id": "otra-accion", "accion_id": "producto.armar_prompts_fase2", "producto_key": "PX",
         "angulo_key": "A", "estado": "CORRIENDO"},
        {"job_id": "vivo", "accion_id": ACCION, "producto_key": "PX", "angulo_key": "A", "estado": "ESPERA_RESPUESTA"},
    ]
    monkeypatch.setattr(trabajos, "listar", lambda **k: filas)
    assert contratos._trabajo_en_curso(ACCION, "PX", "A") == "vivo"
    assert contratos._trabajo_en_curso(ACCION, "PX", "C") is None


# ── la acción del manifiesto y su prompt ──────────────────────────────────────────────────────

def test_la_accion_esta_declarada_para_fabricar_sin_render_ni_meta():
    a = _accion(ACCION)
    assert (a["ejecutor_tipo"], a["name"]) == ("subagente", "etapa-9")
    assert a["requiere_confirmacion"] is True and a["toca_meta"] is False and a["habilitada"] is True
    assert set(a["escribe"]) == {"PRODUCTOS/", "Ads/"}
    assert set(a["parametros"]) == {"producto_key", "angulo_key", "n"}
    assert a["parametros"]["angulo_key"]["patron"] == _accion("producto.armar_prompts_fase2")["parametros"]["angulo_key"]["patron"]
    import re

    patron = a["parametros"]["n"]["patron"]
    assert all(re.fullmatch(patron, str(n)) for n in range(1, 11))
    assert not any(re.fullmatch(patron, x) for x in ("0", "11", "-1", "5.5", "", "x"))
    plan = _accion("nodo.F2.plan")
    assert a["tiempo_max_s"] == plan["tiempo_max_s"] and a["presupuesto_usd"] == plan["presupuesto_usd"]


def test_el_nodo_que_hacia_todo_sigue_deshabilitado_y_apunta_a_la_accion_nueva():
    a = _accion("nodo.F2.conceptos")
    assert a["habilitada"] is False
    assert ACCION in a["motivo"]


def test_el_prompt_sale_del_bloque_claude_del_manifiesto(sistema_angulos: Path):
    from vitalcom_app import contratos, workflows

    (sistema_angulos / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(
        "producto_key,creativo_id,archivo,angulo_key,concepto_key,canonico_id,rol_embudo,estado,ad_id,notas\n"
        "PX,PX_1,PX_1.png,ANG_RESISTENCIA,C2_BENEFICIOS,CN05_LISTA_BENEFICIOS,MOFU,GENERADO,,\n"
        "PX,PX_2,PX_2.png,ANG_RESISTENCIA,C5_PRUEBA,CN10_PRUEBA_SOCIAL,BOFU,PENDIENTE_GENERAR,,\n"
        "PX,PX_3,PX_3.png,OTRO_ANGULO,C4_TRANSFORMACION,CN01_ANTES_DESPUES,TOFU,GENERADO,,\n",
        encoding="utf-8",
    )
    registrados = contratos.conceptos_registrados("PX", "ANG_RESISTENCIA")
    assert [(r["canonico_id"], r["concepto_key"]) for r in registrados] == [
        ("CN05_LISTA_BENEFICIOS", "C2_BENEFICIOS"), ("CN10_PRUEBA_SOCIAL", "C5_PRUEBA")]

    accion = _accion(ACCION)
    contexto = workflows.contexto_de_prompt(accion, {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA", "n": "5"})
    sello = {"job_id": "j" * 32, "accion": accion, "claude": _manifiesto()["acciones"]["claude"],
             "parametros": {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA", "n": "5"},
             "ejecutor": "subagente `etapa-9`", "contexto": contexto}
    prompt = workflows.prompt_del_nodo(sello)
    assert "{" not in prompt, "ningún marcador sin llenar"
    assert "PX" in prompt and "ANG_RESISTENCIA" in prompt and "exactamente 5" in prompt
    assert "CN05_LISTA_BENEFICIOS" in prompt and "CN10_PRUEBA_SOCIAL" in prompt
    assert "CN01_ANTES_DESPUES" not in prompt, "solo los registrados de ESE ángulo"
    # UN dueno de «que canonicos»: el script elige (con --n) y etapa-9 registra EXACTAMENTE esos
    assert "python Ads/_TOOLS/armar_prompts_fase2.py PX ANG_RESISTENCIA --n 5 --json" in prompt
    assert "QUIÉN ELIGE LOS CANÓNICOS: el script" in prompt
    assert "EXACTAMENTE los canónicos de `canonicos`" in prompt
    assert prompt.index("armar_prompts_fase2.py") < prompt.index("generar-conceptos"), "primero el script, despues el registro"
    assert "NO vuelvas a correr armar_prompts_fase2.py" in prompt
    assert "etapa-render" in prompt and "Meta" in prompt  # lo prohíbe explícitamente
    assert "PREGUNTA_OPERADOR:" in prompt


def test_sin_registrados_el_prompt_lo_dice(sistema_angulos: Path):
    from vitalcom_app import contratos, workflows

    accion = _accion(ACCION)
    contexto = workflows.contexto_de_prompt(accion, {"producto_key": "PX", "angulo_key": "ANG_RESISTENCIA", "n": "10"})
    assert "ninguno" in contexto["ya_registrados"].lower()
    assert contratos.conceptos_registrados("PX", "ANG_RESISTENCIA") == []
