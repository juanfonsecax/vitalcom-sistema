"""Ciclo nocturno (T1b, 22-sep-2026): una falla PARCIAL de `ciclo.bajar_meta` (código de salida 2 —
al menos una cuenta de Meta OK, al menos una caída) no debe tumbar la cadena completa. Un código de
salida 1 (todas las cuentas fallaron) sí debe tumbarla, igual que cualquier otro paso.

Sobre las acciones reales del manifiesto (para que `acciones.por_id_para_el_runner` no necesite un
sistema de juguete completo), pero con `encolar`/`esperar_resultado` reemplazados: ninguna prueba
corre un script real ni toca Meta.
"""

from __future__ import annotations

from vitalcom_app import workflows

JOB = "c" * 32


def _resultado_por_paso(mapa_resultados):
    """Fábrica de un `esperar_resultado` falso: uno por accion_id, en el orden que llegan."""
    llamadas = {"n": 0}

    def _falso_encolar(accion, valores, job_id, retomar_de=None):
        return job_id, False

    def _falso_esperar(job_id, tope_s):
        llamadas["n"] += 1
        return mapa_resultados[llamadas["n"] - 1]

    return _falso_encolar, _falso_esperar


def test_bajar_meta_parcial_no_detiene_la_cadena(monkeypatch):
    resultados = [
        {"codigo_salida": 0, "estado": "EXITO", "detalle": "ok"},  # nodo.ciclo.datos
        {"codigo_salida": 2, "estado": "FALLIDO",
         "detalle": "CUENTAS CON ERROR (1 de 5): GTR 13"},  # ciclo.bajar_meta, PARCIAL
        {"codigo_salida": 0, "estado": "EXITO", "detalle": "ok"},  # nodo.ciclo.motor
        {"codigo_salida": 0, "estado": "EXITO", "detalle": "ok"},  # sistema.refrescar_flujo
        {"codigo_salida": 0, "estado": "EXITO", "detalle": "ok"},  # sistema.gen_app
    ]
    falso_encolar, falso_esperar = _resultado_por_paso(resultados)
    monkeypatch.setattr(workflows, "encolar", falso_encolar)
    monkeypatch.setattr(workflows, "esperar_resultado", falso_esperar)

    salida = workflows.ejecutar_ciclo_nocturno(JOB)

    assert salida["estado"] == "EXITO", salida
    assert len(salida["pasos"]) == len(workflows.PASOS_CICLO_NOCTURNO), "la cadena debe llegar al último paso"
    assert salida["pasos"][-1]["accion_id"] == "sistema.gen_app"
    assert len(salida["avisos"]) == 1
    assert salida["avisos"][0]["accion_id"] == "ciclo.bajar_meta"
    assert "avisos" in salida["detalle"] or "aviso" in salida["detalle"].lower()


def test_bajar_meta_todas_las_cuentas_fallan_detiene_la_cadena(monkeypatch):
    resultados = [
        {"codigo_salida": 0, "estado": "EXITO", "detalle": "ok"},  # nodo.ciclo.datos
        {"codigo_salida": 1, "estado": "FALLIDO",
         "detalle": "CUENTAS CON ERROR (5 de 5): GTR7, GTR0, GTR1, GTR3, GTR13"},  # ciclo.bajar_meta, TOTAL
    ]
    falso_encolar, falso_esperar = _resultado_por_paso(resultados)
    monkeypatch.setattr(workflows, "encolar", falso_encolar)
    monkeypatch.setattr(workflows, "esperar_resultado", falso_esperar)

    salida = workflows.ejecutar_ciclo_nocturno(JOB)

    assert salida["estado"] == "FALLIDO"
    assert salida["accion_fallida"] == "ciclo.bajar_meta"
    assert len(salida["pasos"]) == 2, "no debe seguir a nodo.ciclo.motor si bajar_meta falló completo"
    assert salida["avisos"] == []
