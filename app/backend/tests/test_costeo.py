"""La tabla de precios que muestra la app es, carácter por carácter, la de `costear.py`.

Criterio de aceptación del Hito 2. La app no redondea, no convierte moneda y no rellena.
Si el costo no tiene fila propia en `_DIM_COSTEO.csv`, la app repite el criterio que informa
el script (hoy: la más cercana, y en empate la superior), sin reemplazarlo por otro.
"""

from __future__ import annotations

import json
import subprocess


def _costear(base, costo: str) -> dict:
    return json.loads(
        subprocess.run(
            ["python", str(base / "Ads" / "_TOOLS" / "costear.py"), costo, "--json"],
            cwd=str(base), capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
    )


def test_la_tabla_servida_es_la_del_script(cliente, base_declarada):
    for costo in ("40", "60", "90"):
        servido = cliente.get(f"/api/costeo/{costo}").json()
        directo = _costear(base_declarada, costo)
        for campo, valor in directo.items():
            assert servido[campo] == valor, f"{campo} con costo {costo}"


def test_un_costo_sin_fila_propia_trae_el_criterio_del_script(cliente, base_declarada):
    """Q41 es el caso real de TINNIDROP: el script usa la fila Q40, la más cercana."""
    servido = cliente.get("/api/costeo/41").json()
    directo = _costear(base_declarada, "41")
    assert servido["fila_usada"] == directo["fila_usada"]
    assert servido["criterio_de_fila"] == directo["criterio_de_fila"]
    assert servido["cpa_break_even"] == directo["cpa_break_even"]


def test_un_costo_que_no_es_numero_se_rechaza(cliente):
    assert cliente.get("/api/costeo/sesenta").status_code == 422
