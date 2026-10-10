"""test_fase2_subir_imagen.py — cargar la imagen renderizada a mano sobre la tarjeta de un concepto.

Lo que se congela:
  * `fase2_detalle` dice, por concepto, su formato, si se le puede subir imagen (IMAGEN y no
    PUBLICADO) y la versión del archivo en disco (para que la miniatura no se quede con la vieja);
  * `POST /api/productos/<pk>/conceptos/<creativo_id>/imagen` pasa por la acción del manifiesto
    con el archivo en el temporal, nunca directo al sistema;
  * un concepto inexistente es 404; un VIDEO o un PUBLICADO se rechazan antes de correr nada;
  * si el escritor rechaza el archivo, el detalle llega a la pantalla (422).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import sistema_de_juguete as juguete

from test_fase2_angulos import PARAMETROS, sistema_angulos  # noqa: F401

CABECERA = "producto_key,creativo_id,archivo,angulo_key,canonico_id,rol_embudo,estado,ad_id,notas,formato\n"
COLUMNAS_CREATIVOS = ["producto_key", "creativo_id", "archivo", "angulo_key", "estado", "formato"]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


# ── lo que dice el detalle ────────────────────────────────────────────────────

@pytest.fixture()
def habilitada(monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: True)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)


def _conceptos(base: Path, filas: list[tuple[str, str, str]], con_archivo: set[str]) -> dict:
    """filas: (creativo_id, estado, formato)."""
    from vitalcom_app import contratos

    (base / "PRODUCTOS" / "_PARAMETROS_PUBLICACION.csv").write_text(PARAMETROS, encoding="utf-8")
    cuerpo = "".join(f"PX,{c},{c}.png,ANG_RESISTENCIA,CN01_X,MOFU,{e},,,{f}\n" for c, e, f in filas)
    (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").write_text(CABECERA + cuerpo, encoding="utf-8")
    media = base / "Ads" / "MEDIA_PX"
    media.mkdir(parents=True, exist_ok=True)
    for c in con_archivo:
        (media / f"{c}.png").write_bytes(PNG)
    return {c["creativo_id"]: c for c in contratos.fase2_detalle("PX")["conceptos"]}


def test_el_detalle_dice_quien_puede_recibir_imagen(sistema_angulos: Path, habilitada):
    c = _conceptos(sistema_angulos, [("A1", "PENDIENTE_GENERAR", "IMAGEN"), ("A2", "GENERADO", "IMAGEN"),
                                     ("A3", "PUBLICADO", "IMAGEN"), ("A4", "PENDIENTE_GENERAR", "VIDEO")], set())
    assert [c[k]["puede_subir"] for k in ("A1", "A2", "A3", "A4")] == [True, True, False, False]
    assert [c[k]["formato"] for k in ("A1", "A4")] == ["IMAGEN", "VIDEO"]


def test_sin_la_accion_habilitada_no_hay_subida(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: False)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)
    c = _conceptos(sistema_angulos, [("A1", "PENDIENTE_GENERAR", "IMAGEN")], set())
    assert c["A1"]["puede_subir"] is False


def test_la_version_cambia_con_el_archivo(sistema_angulos: Path, habilitada):
    c = _conceptos(sistema_angulos, [("A1", "GENERADO", "IMAGEN"), ("A2", "PENDIENTE_GENERAR", "IMAGEN")], {"A1"})
    assert c["A2"]["archivo_version"] == "" and c["A1"]["archivo_version"].isdigit()
    antes = c["A1"]["archivo_version"]
    nuevo = int(antes) + 5_000_000_000
    os.utime(sistema_angulos / "Ads" / "MEDIA_PX" / "A1.png", ns=(nuevo, nuevo))
    from vitalcom_app import contratos

    despues = {x["creativo_id"]: x for x in contratos.fase2_detalle("PX")["conceptos"]}
    assert despues["A1"]["archivo_version"] != antes


# ── el endpoint ───────────────────────────────────────────────────────────────

@pytest.fixture()
def con_conceptos(sistema_de_juguete: Path):
    juguete._csv(sistema_de_juguete / "PRODUCTOS" / "_DIM_PRODUCTOS.csv",
                 [*juguete.COLUMNAS_PRODUCTOS, "carpeta_media"],
                 [{"producto_key": "TINNIDROP", "nombre_display": "Tinnidrop", "estado": "VIVO", "mercado": "GT",
                   "carpeta_media": "MEDIA_T"}])
    juguete._csv(sistema_de_juguete / "PRODUCTOS" / "_DIM_CREATIVOS.csv", COLUMNAS_CREATIVOS, [
        {"producto_key": "TINNIDROP", "creativo_id": "T_1", "archivo": "T_1.png", "angulo_key": "A",
         "estado": "PENDIENTE_GENERAR", "formato": "IMAGEN"},
        {"producto_key": "TINNIDROP", "creativo_id": "T_2", "archivo": "T_2.mp4", "angulo_key": "A",
         "estado": "PENDIENTE_GENERAR", "formato": "VIDEO"},
        {"producto_key": "TINNIDROP", "creativo_id": "T_3", "archivo": "T_3.png", "angulo_key": "A",
         "estado": "PUBLICADO", "formato": "IMAGEN"},
        {"producto_key": "NUSAVA", "creativo_id": "N_1", "archivo": "N_1.png", "angulo_key": "A",
         "estado": "PENDIENTE_GENERAR", "formato": "IMAGEN"},
    ])
    return sistema_de_juguete


def _subir(cliente, producto, creativo, contenido=PNG, nombre="descarga (3).png"):
    return cliente.post(f"/api/productos/{producto}/conceptos/{creativo}/imagen",
                        files={"archivo": (nombre, contenido, "image/png")})


def test_subir_pasa_por_la_accion_con_el_archivo_temporal(cliente_juguete, con_conceptos):
    respuesta = _subir(cliente_juguete, "TINNIDROP", "T_1")
    assert respuesta.status_code == 200, respuesta.text
    argv = [c for c in juguete.llamadas(con_conceptos) if c["script"] == "cargar_imagen_concepto.py"][-1]["argv"]
    assert argv[:4] == ["--producto", "TINNIDROP", "--creativo", "T_1"]
    origen = argv[argv.index("--origen") + 1]
    assert "vitalcom-subida-" in origen and not Path(origen).exists(), "el temporal se borra al terminar"


def test_concepto_o_producto_inexistente_es_404(cliente_juguete, con_conceptos):
    assert _subir(cliente_juguete, "TINNIDROP", "NO_EXISTE").status_code == 404
    assert _subir(cliente_juguete, "TINNIDROP", "N_1").status_code == 404, "el concepto es de otro producto"
    assert _subir(cliente_juguete, "NO_EXISTE", "T_1").status_code == 404


def test_video_y_publicado_se_rechazan_sin_correr_nada(cliente_juguete, con_conceptos):
    for creativo in ("T_2", "T_3"):
        assert _subir(cliente_juguete, "TINNIDROP", creativo).status_code == 422, creativo
    assert not [c for c in juguete.llamadas(con_conceptos) if c["script"] == "cargar_imagen_concepto.py"]


def test_el_rechazo_del_escritor_llega_a_la_pantalla(cliente_juguete, con_conceptos):
    juguete.escribir_script(con_conceptos, "cargar_imagen_concepto.py", (
        "import json, sys\nprint(json.dumps({'ok': False, 'detalle': 'el archivo no es una imagen PNG o JPEG'}))\n"
        "sys.exit(1)\n"))
    respuesta = _subir(cliente_juguete, "TINNIDROP", "T_1", b"<html>")
    assert respuesta.status_code == 422 and "no es una imagen" in respuesta.json()["detail"]
