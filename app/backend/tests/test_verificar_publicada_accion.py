"""El botón «Ya publiqué la campaña: verificar» (`publicacion.verificar_publicada`).

Se prueba la puerta, no el motor: el manifiesto es el real y los scripts son falsos (sistema de
juguete). La acción se ofrece como botón, valida sus parámetros contra el manifiesto y arma el argv
por tokens apuntando a `verificar_campana_publicada.py`.
"""

from __future__ import annotations

import pytest

from vitalcom_app import acciones

ACCION = "publicacion.verificar_publicada"
JOB = "b" * 32
BUENOS = {"producto_key": "TINNIDROP", "fase": "2", "brazo": "C"}


def _pedir(cliente, parametros, **extra):
    return cliente.post(f"/api/acciones/{ACCION}",
                        json={"parametros": parametros, "confirmado": False, **extra})


def test_se_ofrece_como_boton(cliente_juguete):
    ids = {a["id"] for a in cliente_juguete.get("/api/acciones").json()}
    assert ACCION in ids


def test_un_pedido_valido_se_encola_sin_pedir_confirmacion(cliente_juguete):
    respuesta = _pedir(cliente_juguete, BUENOS, job_id=JOB)
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["estado"] == "ENCOLADO"


@pytest.mark.parametrize("parametros,campo", [
    ({"producto_key": "TINNIDROP", "fase": "2"}, "brazo"),                       # falta
    ({**BUENOS, "fase": "3"}, "fase"),                                           # fuera del enum
    ({**BUENOS, "brazo": "c"}, "brazo"),                                         # minúscula
    ({**BUENOS, "brazo": "A;rm -rf"}, "brazo"),                                  # fuera del patrón
    ({**BUENOS, "brazo": "--escribir"}, "brazo"),                                # parece bandera
    ({**BUENOS, "producto_key": "NO_EXISTE"}, "producto_key"),                   # sin fila
    ({**BUENOS, "sobrante": "x"}, "sobrante"),                                   # sobra
])
def test_parametros_invalidos_422(cliente_juguete, parametros, campo):
    respuesta = _pedir(cliente_juguete, parametros)
    assert respuesta.status_code == 422, (parametros, respuesta.text)
    assert respuesta.json()["codigo"] == "PARAMETRO_INVALIDO"
    assert respuesta.json()["campo"] == campo


def test_el_argv_sale_del_manifiesto(sistema_de_juguete):
    accion = acciones.por_id_para_el_runner(ACCION)
    argv = acciones.resolver(accion, {"producto_key": "TINNIDROP", "fase": "2", "brazo": "C"})
    assert argv[1] == "Ads/_TOOLS/verificar_campana_publicada.py"
    assert argv[2:] == ["--producto", "TINNIDROP", "--fase", "2", "--brazo", "C", "--json"]
