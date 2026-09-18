#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_perfilar_angulos.py — GATE DEL PERFIL DE ÁNGULO.

Congela las reglas del ciclo de vida y la aritmética del riesgo. Mismo rol que
`test_decidir.py` para el motor: si este archivo pasa, las cinco cosas que el perfil
NO puede volver a hacer no vuelven a pasar.

Las cinco:
  1. Un ganador fatigado no puede recibir APAGADO. `EN_DECLIVE` gana sobre todo lo que
     no sea abandono o una pausa ya ordenada por el motor — es la regla congelada de
     `test_decidir.py` vista desde el ciclo de vida.
  2. Un ángulo sin gasto no es un ángulo que rinde mal: es DORMIDO. Confundirlos fue lo
     que tuvo a VARICOSE 21 días proponiendo reactivación (03-sep-2026).
  3. La pérdida esperada nunca puede ser negativa ni superar 1 Q por Q: es una
     esperanza truncada sobre una cola, no un margen.
  4. `neto_por_q` tiene que coincidir con el CPA puntual en el signo — si el posterior
     dice que gana plata, el CPA observado no puede estar sobre el break-even.
  5. Las ventanas CONTROL nunca entran al acumulado (DATA_PLAYBOOK / APR-020).

USO:  python Ads/_TOOLS/test_perfilar_angulos.py     (exit 0 = pasa, 1 = falla)
"""

import os
import io
import sys
import csv
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfilar_angulos as PA  # noqa: E402

BE = 93.41


def _perfil(**kw):
    """Perfil mínimo con los campos que clasificar() mira."""
    p = {"estado_motor": "SEGUIR_MIDIENDO", "accion_codigo": "MANTENER_Y_MEDIR",
         "dias_sin_gasto": 0, "ganador_historico": False, "renovado_hace": None,
         "gasto_acum_q": 500.0, "ventas_acum": 10, "cpa_acum_q": 50.0, "be_q": BE}
    p.update(kw)
    return p


PAR = {"ventana_dias": 14}
OPT = {"dias_sin_gasto_dormido": 3, "dias_sin_gasto_apagado": 14, "min_angulos_vivos": 2}

# (nombre, perfil, estado esperado, por qué importa)
CASOS = [
    ("Ganador fatigado: el motor dice RENOVAR",
     _perfil(estado_motor="RENOVAR", ganador_historico=True, ventas_acum=38, cpa_acum_q=69.9),
     "EN_DECLIVE",
     "Un ángulo con historia rentable NUNCA se apaga por una mala racha: se le renueva el "
     "concepto. Es la regla que test_decidir.py congela, leída desde el ciclo de vida."),

    ("Ganador histórico sin orden vigente",
     _perfil(ganador_historico=True, ventas_acum=69, cpa_acum_q=58.1),
     "SOSTENIDO",
     "Rentable acumulado y sin orden del motor no es 'midiendo': es un activo sostenido."),

    ("Sin gasto hace 6 días, con historia",
     _perfil(dias_sin_gasto=6, ganador_historico=True, ventas_acum=12, cpa_acum_q=57.1),
     "DORMIDO",
     "No está rindiendo mal, no está corriendo. Confundirlo mete un CPA viejo en el "
     "promedio del portafolio (el caso VARICOSE del 03-sep-2026)."),

    ("Sin gasto hace 25 días",
     _perfil(dias_sin_gasto=25, ganador_historico=True),
     "APAGADO_ABANDONO",
     "Pasada la ventana de evaluación ninguna data lo respalda: sostenerlo vivo es "
     "declarar un estado que nadie puede verificar."),

    ("El motor ordena PAUSAR",
     _perfil(estado_motor="PAUSAR", accion_codigo="PAUSAR_TOLERANCIA_AGOTADA"),
     "APAGADO",
     "El diagnóstico es del motor (invariante 13). El perfil lo refleja, no lo discute."),

    ("PAUSAR gana sobre DORMIDO cuando las dos aplican",
     _perfil(estado_motor="PAUSAR", accion_codigo="PAUSAR_HOOK_MUERTO", dias_sin_gasto=5),
     "APAGADO",
     "Una pausa ORDENADA no es lo mismo que una celda que dejó de correr sola."),

    ("El motor ordena ESCALAR",
     _perfil(estado_motor="ESCALAR", accion_codigo="ESCALAR_SURFING", ganador_historico=True),
     "ESCALANDO",
     "ESCALANDO manda sobre SOSTENIDO: hay una orden vigente, no solo historia."),

    ("Creativo renovado hace 4 días, sin veredicto todavía",
     _perfil(renovado_hace=4, ventas_acum=3, cpa_acum_q=110.0, gasto_acum_q=330.0),
     "RENOVADO",
     "Tras un CAMBIO_CREATIVO el perfil espera veredicto; no se lee como si nada "
     "hubiera cambiado."),

    ("Todavía no gastó su presupuesto de decisión",
     _perfil(gasto_acum_q=40.0, ventas_acum=0, cpa_acum_q=None),
     "EN_PRUEBA",
     "Debajo de 1×BE, cero ventas es estadísticamente esperable hasta en un ganador: "
     "no se lee (ESCALADO_PLAYBOOK §1.5)."),

    ("PD consumido y sin veredicto",
     _perfil(gasto_acum_q=400.0, ventas_acum=4, cpa_acum_q=100.0),
     "MIDIENDO",
     "Gastó su presupuesto de decisión y sigue sin resolver: ni prueba ni ganador."),
]


def test_riesgo():
    """La aritmética del quetzal incremental. Tres invariantes que no dependen de la data."""
    fallas = 0

    # 3. la pérdida es una esperanza truncada: 0 <= perdida <= 1
    for v, g in [(0, 100.0), (1, 50.0), (6, 131.2), (36, 2305.6), (97, 6080.0)]:
        neto, perd, pr = PA.riesgo(v, g, BE)
        if not (0.0 <= perd <= 1.0):
            print("  FALLA  pérdida fuera de [0,1] con %d ventas y Q%.1f: %.3f" % (v, g, perd))
            fallas += 1
        if not (0.0 <= pr <= 1.0):
            print("  FALLA  P(rentable) fuera de [0,1] con %d ventas: %.3f" % (v, pr))
            fallas += 1
    if not fallas:
        print("  OK     la pérdida esperada y P(rentable) se quedan en [0,1] en 5 celdas reales")

    # 4. coherencia de signo contra el CPA puntual, con muestra suficiente
    v, g = 36, 36 * 64.0            # CPA Q64.0 < BE Q93.41
    neto, _, pr = PA.riesgo(v, g, BE)
    if neto <= 0 or pr < 0.5:
        print("  FALLA  CPA Q64 bajo BE Q93 debería dar neto>0 y P>0.5; dio %.3f / %.2f" % (neto, pr))
        fallas += 1
    else:
        print("  OK     CPA bajo break-even ⇒ neto positivo (%.2f Q/Q) y P(rentable) %.0f%%"
              % (neto, pr * 100))

    v, g = 10, 10 * 140.0           # CPA Q140 > BE
    neto, perd, pr = PA.riesgo(v, g, BE)
    if neto >= 0 or pr > 0.5:
        print("  FALLA  CPA Q140 sobre BE debería dar neto<0; dio %.3f / %.2f" % (neto, pr))
        fallas += 1
    else:
        print("  OK     CPA sobre break-even ⇒ neto negativo (%.2f Q/Q) y P(rentable) %.0f%%"
              % (neto, pr * 100))

    # más evidencia con el mismo CPA ⇒ la cola mala se encoge
    _, p_poco, _ = PA.riesgo(3, 3 * 64.0, BE)
    _, p_mucho, _ = PA.riesgo(60, 60 * 64.0, BE)
    if not (p_mucho < p_poco):
        print("  FALLA  con el mismo CPA, 60 ventas no reducen la cola frente a 3 (%.3f vs %.3f)"
              % (p_mucho, p_poco))
        fallas += 1
    else:
        print("  OK     a igual CPA, más ventas encogen la cola mala (%.3f → %.3f)"
              % (p_poco, p_mucho))

    # una celda sin gasto no tiene riesgo computable — y lo dice, no devuelve 0
    if PA.riesgo(0, 0.0, BE) != (None, None, None):
        print("  FALLA  una celda sin gasto debería devolver None, no un número")
        fallas += 1
    else:
        print("  OK     celda sin gasto ⇒ None (no se inventa un riesgo donde no hay data)")
    return fallas


def test_control_no_suma():
    """5. Las ventanas CONTROL no entran al acumulado, y su descarte queda declarado."""
    tmp = tempfile.mkdtemp()
    cols = ["ventana_ini", "ventana_fin", "dias", "rol_ventana", "producto_key", "conjunto",
            "spend_usd", "ventas", "mensajes"]
    filas = [
        dict(zip(cols, ["2026-09-01", "2026-09-01", "1", "BASE", "PX", "CJ", "10", "5", "50"])),
        dict(zip(cols, ["2026-09-01", "2026-09-01", "1", "CONTROL", "PX", "CJ", "10", "5", "50"])),
    ]
    prod_dir = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod_dir)
    with io.open(os.path.join(prod_dir, "_FACT_VENTAS.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    with io.open(os.path.join(prod_dir, "_DIM_CONJUNTOS.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["producto_key", "conjunto_meta", "angulo_key"])
        w.writeheader()
        w.writerow({"producto_key": "PX", "conjunto_meta": "CJ", "angulo_key": "ANG"})

    viejo = PA.PROD
    PA.PROD = prod_dir
    try:
        serie, control, _ = PA.serie_por_angulo()
        ventas = sum(v[1] for v in serie[("PX", "ANG")].values())
        if abs(ventas - 5.0) > 1e-9:
            print("  FALLA  el acumulado debería tener 5 ventas (solo BASE) y tiene %.1f" % ventas)
            return 1
        if control.get(("PX", "ANG")) != 5:
            print("  FALLA  las 5 ventas CONTROL descartadas deberían quedar declaradas")
            return 1
    finally:
        PA.PROD = viejo
    print("  OK     CONTROL no suma al acumulado y su descarte queda declarado (APR-020)")
    return 0


def main():
    print("=" * 84)
    print(" GATE DEL PERFIL DE ÁNGULO - Ads/_TOOLS/perfilar_angulos.py")
    print("=" * 84)
    fallas = 0
    for nombre, perfil, esperado, porque in CASOS:
        estado, _ = PA.clasificar(perfil, PAR, OPT)
        if estado == esperado:
            print("  OK     %s" % nombre)
        else:
            fallas += 1
            print("  FALLA  %s\n         esperado=%s  obtenido=%s\n         %s"
                  % (nombre, esperado, estado, porque))

    # todo estado que clasificar() puede emitir tiene que estar declarado en ESTADOS
    emitidos = {PA.clasificar(p, PAR, OPT)[0] for _, p, _, _ in CASOS}
    if not emitidos <= set(PA.ESTADOS):
        print("  FALLA  estados emitidos fuera del vocabulario: %s" % (emitidos - set(PA.ESTADOS)))
        fallas += 1
    else:
        print("  OK     el vocabulario de estados es cerrado (%d estados)" % len(PA.ESTADOS))

    fallas += test_riesgo()
    fallas += test_control_no_suma()

    total = len(CASOS) + 7
    print("\n%d de %d comprobaciones pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
