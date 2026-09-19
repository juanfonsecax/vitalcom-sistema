"""El contrato de `GET/POST /api/acciones` (diseño Hito 3, §2.5), sobre el sistema de juguete.

El manifiesto y el FLUJO son los reales de este repositorio; los scripts son falsos. Ninguna
prueba ejecuta nada de verdad: acá se prueba la puerta, no el motor.
"""

from __future__ import annotations

import sistema_de_juguete as juguete

from vitalcom_app import acciones

JOB = "a" * 32


def _pedir(cliente, accion_id, parametros=None, confirmado=False, **extra):
    return cliente.post(
        f"/api/acciones/{accion_id}",
        json={"parametros": parametros or {}, "confirmado": confirmado, **extra},
    )


def _v6(base):
    manifiesto = juguete.manifiesto_real()
    manifiesto["version"] = 6
    manifiesto.pop("acciones")
    juguete.escribir_manifiesto(base, manifiesto)
    acciones.olvidar_cache()


# ── GET ───────────────────────────────────────────────────────────────────────

def test_get_lista_solo_las_acciones_con_boton(cliente_juguete):
    respuesta = cliente_juguete.get("/api/acciones")
    assert respuesta.status_code == 200, respuesta.text
    ids = {a["id"] for a in respuesta.json()}
    assert "nodo.F1.paquete" in ids and "nodo.ciclo.motor" in ids and "producto.transcribir" in ids
    assert "producto.alta" not in ids, "producto.alta es interna: solo la usa el runner"
    assert "sistema.gen_app" not in ids
    assert all("comando" not in a for a in respuesta.json()), "el argv no se le muestra a la pantalla"


def test_get_con_producto_dice_si_esta_disponible_y_por_que(cliente_juguete):
    respuesta = cliente_juguete.get("/api/acciones", params={"producto_key": "TINNIDROP"})
    assert respuesta.status_code == 200, respuesta.text
    por_id = {a["id"]: a for a in respuesta.json()}
    assert por_id["nodo.F2.etapa-11"]["disponible"] is True, "flujo.py dice que está listo"
    assert por_id["nodo.F1.paquete"]["disponible"] is False
    assert por_id["nodo.F1.paquete"]["por_que"]["nodo_actual"] == "F2.etapa-11"
    assert por_id["nodo.F1.activar"]["disponible"] is False
    assert por_id["nodo.F1.activar"]["por_que"]["motivo"], "una deshabilitada dice su motivo"


def test_get_filtra_por_nodo_y_el_ciclo_ignora_el_prefijo_de_fase(cliente_juguete):
    directo = cliente_juguete.get("/api/acciones", params={"nodo": "F2.plan"}).json()
    assert [a["id"] for a in directo] == ["nodo.F2.plan"]
    ciclo = cliente_juguete.get("/api/acciones", params={"nodo": "F2.ciclo.motor"}).json()
    assert [a["id"] for a in ciclo] == ["nodo.ciclo.motor"]


def test_manifiesto_v6_no_ofrece_acciones(cliente_juguete, sistema_de_juguete):
    _v6(sistema_de_juguete)
    assert cliente_juguete.get("/api/acciones").json() == []


def test_get_con_manifiesto_invalido_es_503(cliente_juguete, sistema_de_juguete):
    manifiesto = juguete.manifiesto_real()
    manifiesto["acciones"]["lista"][0]["ejecutor_tipo"] = "inventado"
    juguete.escribir_manifiesto(sistema_de_juguete, manifiesto)
    acciones.olvidar_cache()
    respuesta = cliente_juguete.get("/api/acciones")
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "MANIFIESTO_INVALIDO"
    assert respuesta.json()["problemas"]


# ── POST: el orden de la tabla ────────────────────────────────────────────────

def test_accion_no_declarada_403(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.no.existe")
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "ACCION_NO_DECLARADA"


def test_accion_interna_403(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "producto.alta")
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "ACCION_INTERNA"


def test_manifiesto_v6_todo_403(cliente_juguete, sistema_de_juguete):
    _v6(sistema_de_juguete)
    respuesta = _pedir(cliente_juguete, "nodo.ciclo.motor")
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "ACCION_NO_DECLARADA"


def test_deshabilitada_409_con_motivo(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.F1.activar", {"producto_key": "TINNIDROP"},
                       confirmado=True)
    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "ACCION_DESHABILITADA" and cuerpo["motivo"]


def test_operador_409_con_escritores(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.F1.congelar_inputs", {"producto_key": "TINNIDROP"})
    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "ES_DEL_OPERADOR"
    assert {d["accion"] for d in cuerpo["datos_del_operador"]} >= {"producto.alta", "producto.transcribir"}


def test_parametro_invalido_422(cliente_juguete):
    for parametros, campo in (
        ({}, "producto_key"),                                               # falta
        ({"producto_key": "NO_EXISTE"}, "producto_key"),                    # no tiene fila
        ({"producto_key": "TINNIDROP", "sobrante": "x"}, "sobrante"),       # sobra
        ({"producto_key": "--dry-run"}, "producto_key"),                    # parece una bandera
    ):
        respuesta = _pedir(cliente_juguete, "nodo.F2.plan", parametros, confirmado=True)
        assert respuesta.status_code == 422, (parametros, respuesta.text)
        assert respuesta.json()["codigo"] == "PARAMETRO_INVALIDO"
        assert respuesta.json()["campo"] == campo


def test_parametro_enum_se_valida_contra_el_manifiesto(cliente_juguete):
    malo = _pedir(cliente_juguete, "producto.transcribir", {"producto_key": "TINNIDROP", "modelo": "gigante"})
    assert malo.status_code == 422
    assert malo.json()["campo"] == "modelo"


def test_falta_confirmacion_428(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.F2.etapa-11", {"producto_key": "TINNIDROP"})
    assert respuesta.status_code == 428
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FALTA_CONFIRMACION"
    assert cuerpo["escribe"] and cuerpo["tiempo_max_s"] and cuerpo["toca_meta"] is False


def test_nodo_no_listo_409(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.F2.plan", {"producto_key": "TINNIDROP"}, confirmado=True)
    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "NODO_NO_LISTO"
    assert cuerpo["nodo_actual"] == "F2.etapa-11" and cuerpo["estado"] == "LISTO_PARA_EJECUTAR"


def test_un_pedido_valido_queda_encolado_y_repetirlo_no_duplica(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB)
    assert respuesta.status_code == 202, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["job_id"] == JOB and cuerpo["estado"] == "ENCOLADO" and cuerpo["repetido"] is False
    assert cuerpo["url_estado"] == f"/api/trabajos/{JOB}"
    de_nuevo = _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB)
    assert de_nuevo.status_code == 202 and de_nuevo.json()["repetido"] is True


def test_un_job_id_mal_formado_se_rechaza(cliente_juguete):
    respuesta = _pedir(cliente_juguete, "nodo.ciclo.motor", {}, job_id="no-es-hex")
    assert respuesta.status_code == 422 and respuesta.json()["campo"] == "job_id"


# ── el argv sale del manifiesto, sin shell ────────────────────────────────────

def test_el_argv_se_arma_por_tokens_con_banderas_opcionales(sistema_de_juguete):
    accion = acciones.por_id_para_el_runner("producto.alta")
    valores = {"nombre": "Crema; rm -rf /", "costo": "60", "descripcion": "/tmp/d.txt",
               "imagen": "/tmp/i.png", "marca": "ACME", "dry_run": True}
    argv = acciones.resolver(accion, valores)
    assert argv[1] == "Ads/_TOOLS/alta_producto.py"
    assert "Crema; rm -rf /" in argv, "el valor viaja entero en UN token: sin shell no puede partirse"
    assert argv[-3:] == ["--marca", "ACME", "--dry-run"]
    assert "--clave" not in argv, "un opcional sin valor no agrega su bandera"


def test_un_marcador_sin_valor_no_arma_una_orden_a_medias(sistema_de_juguete):
    accion = acciones.por_id_para_el_runner("publicacion.paquete")
    try:
        acciones.resolver(accion, {"producto_key": "TINNIDROP"}, {})
    except acciones.ArgvIncompleto as error:
        assert "falta el valor" in str(error)
    else:
        raise AssertionError("tenía que negarse a armar el comando")


def test_los_reservados_completan_el_argv(sistema_de_juguete):
    accion = acciones.por_id_para_el_runner("publicacion.paquete")
    valores = {"producto_key": "TINNIDROP", "fase": "2", "brazo": "A", "cuenta": "GTR7"}
    argv = acciones.resolver(accion, valores, {"run_dir": "RUN"})
    assert argv[argv.index("--salida") + 1] == "RUN/paquete.json"
    assert argv[argv.index("--snapshot") + 1] == "Ads/_INGESTA/META/snapshot_GTR7.json"
