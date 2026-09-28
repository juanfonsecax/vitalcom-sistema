"""test_fase2_prompt.py — el prompt REAL de FASE 2 (join contra armar_prompts_fase2.py) y el
endpoint de imágenes de swipe (Ads/_SWIPE/).

Corre sobre un sistema mínimo de mentira (no el real): solo necesita `DOCTRINA/FLUJO.json`
(la marca de `config._es_base`) + las carpetas que el join lee. `flujo()`/`decisiones()` se
mockean: son subprocess sobre `flujo.py`/`decidir.py`, fuera del alcance de este join.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROMPT_REAL = (
    "Actúa como Director de Arte Senior y diseñador de anuncios de alta conversión "
    "para Meta Ads en Guatemala.\nTe he adjuntado 2 imágenes..."
)


def _escribir_paquete_clearstem(base: Path) -> None:
    """Reproduce el defecto real: `_DIM_CREATIVOS.csv` usa `RESISTENCIA_INSULINA_SOP`, la
    carpeta del paquete (la arma `armar_prompts_fase2.py` con el ángulo que detectó ANTES de
    que se le agregara el sufijo `_SOP`) es `FASE2_RESISTENCIA_INSULINA`."""
    carpeta = base / "Ads" / "MEDIA_CLEARSTEM" / "FASE2_RESISTENCIA_INSULINA"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagen_dir = base / "Ads" / "_SWIPE" / "_IMG" / "Camila_Recomienda"
    imagen_dir.mkdir(parents=True, exist_ok=True)
    (imagen_dir / "15_foto.jpg").write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
    paquete = {
        "producto": "CLEARSTEM",
        "angulo": "RESISTENCIA_INSULINA",
        "conceptos": [
            {
                "slot": 1,
                "canonico_id": "CN05_LISTA_BENEFICIOS",
                "nombre_blueprint": "Lista de beneficios con icono",
                "archivo_salida": "CLEARSTEM_F2_CN05_RESISTENCIA_.png",
                "foto_base_competidor": "Ads/_SWIPE/_IMG/Camila_Recomienda/15_foto.jpg",
                "foto_producto_propio": "Ads/MEDIA_CLEARSTEM/producto.png",
                "variables_json": {},
                "prompt_director_de_arte": PROMPT_REAL,
            }
        ],
    }
    (carpeta / "PAQUETE_CREATIVO_RESISTENCIA_INSULINA.json").write_text(
        json.dumps(paquete, ensure_ascii=False), encoding="utf-8"
    )


@pytest.fixture()
def sistema_min(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Un sistema mínimo: solo la marca de `config._es_base` + las carpetas que el join lee."""
    from vitalcom_app import config

    (tmp_path / "DOCTRINA").mkdir()
    (tmp_path / "DOCTRINA" / "FLUJO.json").write_text("{}", encoding="utf-8")
    _escribir_paquete_clearstem(tmp_path)
    monkeypatch.setenv("VITALCOM_BASE", str(tmp_path))
    config.base.cache_clear()
    try:
        yield tmp_path
    finally:
        config.base.cache_clear()


def test_resolver_prompt_fase2_resuelve_pese_al_sufijo_sop(sistema_min: Path):
    from vitalcom_app import contratos

    resultado = contratos.resolver_prompt_fase2(
        "CLEARSTEM", "MEDIA_CLEARSTEM", "RESISTENCIA_INSULINA_SOP", "CN05_LISTA_BENEFICIOS"
    )
    assert resultado["prompt_origen"] == "paquete"
    assert resultado["prompt"] == PROMPT_REAL
    assert resultado["referencia_url"] == "/api/swipe/_IMG/Camila_Recomienda/15_foto.jpg"
    assert resultado["comando_generar"] is None


def test_resolver_prompt_fase2_pendiente_sin_match(sistema_min: Path):
    from vitalcom_app import contratos

    resultado = contratos.resolver_prompt_fase2(
        "CLEARSTEM", "MEDIA_CLEARSTEM", "RESISTENCIA_INSULINA_SOP", "CN99_NO_EXISTE"
    )
    assert resultado["prompt_origen"] == "pendiente"
    assert resultado["prompt"] is None
    assert resultado["referencia_url"] is None
    assert resultado["comando_generar"] == (
        "python Ads/_TOOLS/armar_prompts_fase2.py CLEARSTEM RESISTENCIA_INSULINA_SOP"
    )


def test_resolver_prompt_fase2_pendiente_sin_carpeta(sistema_min: Path):
    from vitalcom_app import contratos

    resultado = contratos.resolver_prompt_fase2(
        "OTROPRODUCTO", "MEDIA_OTROPRODUCTO", "ALGUN_ANGULO", "CN01"
    )
    assert resultado["prompt_origen"] == "pendiente"
    assert resultado["prompt"] is None
    assert resultado["comando_generar"] == "python Ads/_TOOLS/armar_prompts_fase2.py OTROPRODUCTO ALGUN_ANGULO"


def test_fase2_detalle_produce_el_prompt_real_para_clearstem(sistema_min: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    (sistema_min / "PRODUCTOS").mkdir(exist_ok=True)
    with open(sistema_min / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write("producto_key,carpeta_media\nCLEARSTEM,MEDIA_CLEARSTEM\n")
    with open(sistema_min / "PRODUCTOS" / "_DIM_CREATIVOS.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(
            "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas\n"
            "CLEARSTEM,CLEARSTEM_F2_CN05_RESISTENCIA_,CLEARSTEM_F2_CN05_RESISTENCIA_.png,"
            "RESISTENCIA_INSULINA_SOP,CN05_LISTA_BENEFICIOS,MOFU,GENERADO,,\n"
        )

    monkeypatch.setattr(contratos, "flujo", lambda pk, hoy=None: {"fase": "F2", "nodo_actual": "F2.etapa-9", "entradas": []})
    monkeypatch.setattr(contratos, "decisiones", lambda: {"productos": []})

    detalle = contratos.fase2_detalle("CLEARSTEM")
    conceptos = {c["canonico_id"]: c for c in detalle["conceptos"]}
    real = conceptos["CN05_LISTA_BENEFICIOS"]
    assert real["prompt_origen"] == "paquete"
    assert real["prompt"] == PROMPT_REAL
    assert real["referencia_url"] == "/api/swipe/_IMG/Camila_Recomienda/15_foto.jpg"


def test_ruta_de_swipe_rechaza_traversal_y_fuera_de_raiz(sistema_min: Path, tmp_path_factory: pytest.TempPathFactory):
    from vitalcom_app import contratos

    assert contratos.ruta_de_swipe("../../DOCTRINA/FLUJO.json") is None
    assert contratos.ruta_de_swipe("..\\..\\DOCTRINA\\FLUJO.json") is None
    otro = tmp_path_factory.mktemp("fuera")
    assert contratos.ruta_de_swipe(str(otro / "algo.jpg")) is None


def test_ruta_de_swipe_rechaza_extension_no_permitida(sistema_min: Path):
    from vitalcom_app import contratos

    (sistema_min / "Ads" / "_SWIPE" / "_IMG" / "Camila_Recomienda" / "notas.txt").write_text("x", encoding="utf-8")
    assert contratos.ruta_de_swipe("_IMG/Camila_Recomienda/notas.txt") is None


def test_ruta_de_swipe_sirve_una_imagen_valida(sistema_min: Path):
    from vitalcom_app import contratos

    encontrado = contratos.ruta_de_swipe("_IMG/Camila_Recomienda/15_foto.jpg")
    assert encontrado is not None
    assert encontrado.is_file()


def test_endpoint_swipe_sirve_la_imagen(sistema_min: Path):
    from vitalcom_app.main import app

    cliente = TestClient(app)
    res = cliente.get("/api/swipe/_IMG/Camila_Recomienda/15_foto.jpg")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"


def test_endpoint_swipe_404_extension_no_permitida(sistema_min: Path):
    from vitalcom_app.main import app

    (sistema_min / "Ads" / "_SWIPE" / "secreto.txt").write_text("x", encoding="utf-8")
    cliente = TestClient(app)
    res = cliente.get("/api/swipe/secreto.txt")
    assert res.status_code == 404


def test_endpoint_swipe_404_archivo_inexistente(sistema_min: Path):
    from vitalcom_app.main import app

    cliente = TestClient(app)
    res = cliente.get("/api/swipe/_IMG/no_existe.jpg")
    assert res.status_code == 404
