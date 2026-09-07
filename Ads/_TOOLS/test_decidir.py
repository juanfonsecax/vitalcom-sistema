#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_decidir.py — GATE DEL MOTOR DE DECISIÓN.

Congela las reglas que se rompieron el 07-sep-2026 al colapsar los tres relojes del
motor en una sola ventana de 3 días. Cada caso es una orden que el sistema TIENE que
saber emitir, y una que NO tiene que emitir nunca.

El caso que da nombre a este archivo: un ángulo con historia de rentabilidad
(TINNIDROP/PERDIDA_AUDITIVA, 38 ventas a CPA Q69.9 bajo BE Q93.4) recibió la orden
APAGAR porque la ventana de 3 días solo veía su peor racha. La orden correcta es
RENOVAR el concepto. Si este archivo pasa, ese error no puede volver.

USO:  python Ads/_TOOLS/test_decidir.py     (exit 0 = pasa, 1 = falla)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decidir import evaluar_celda, cargar_parametros  # noqa: E402

BE, OBJ, TASA = 93.41, 30.80, 7.62

# (nombre, kwargs de la celda, estado esperado, por qué importa)
CASOS = [
    ("Quemando sin ventas: el acumulado supera 1x BE",
     dict(ventas=0, mensajes=20, spend_usd=4.0, ventas_3d=0, mensajes_3d=5, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=60, spend_acum_usd=13.0),
     "PAUSAR",
     "La tolerancia se mide sobre el gasto acumulado. Con ventana movil nunca se alcanzaba."),

    ("FASE 1 lento: el acumulado AUN no llega a 1x BE",
     dict(ventas=0, mensajes=8, spend_usd=4.0, ventas_3d=0, mensajes_3d=3, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=8, spend_acum_usd=4.0),
     "SEGUIR_MIDIENDO",
     "Un angulo dentro de su margen de prueba no se apaga antes de tiempo."),

    ("Enlace caido: ni un chat en toda su historia",
     dict(ventas=0, mensajes=0, spend_usd=2.0, ventas_3d=0, mensajes_3d=0, spend_3d=0.5,
          ventas_acum=0, mensajes_acum=0, spend_acum_usd=9.0),
     "PAUSAR",
     "Hook muerto se mide acumulado: si alguna vez trajo un chat, el enlace no esta caido."),

    ("Angulo nuevo con CPA desbordado y SIN historia rentable",
     dict(ventas=3, mensajes=40, spend_usd=60.0, ventas_3d=1, mensajes_3d=10, spend_3d=15.0,
          ventas_acum=3, mensajes_acum=40, spend_acum_usd=60.0),
     "PAUSAR",
     "Sin historia que lo respalde, el CPA desbordado si corta."),

    ("Ganador probado con mala racha: NO se apaga, se renueva",
     dict(ventas=3, mensajes=40, spend_usd=60.0, ventas_3d=1, mensajes_3d=10, spend_3d=15.0,
          ventas_acum=40, mensajes_acum=600, spend_acum_usd=360.0),
     "RENOVAR",
     "EL CASO PERDIDA_AUDITIVA. PAUSAR se evalua antes que FATIGA: sin la guarda de "
     "ganador_historico, un angulo con 40 ventas rentables recibe APAGAR."),

    ("Ganador limpio con IC entero bajo el BE",
     dict(ventas=26, mensajes=190, spend_usd=97.0, ventas_3d=6, mensajes_3d=40, spend_3d=20.0,
          ventas_acum=26, mensajes_acum=190, spend_acum_usd=97.0),
     "ESCALAR",
     "Con evidencia solida la orden de escalar si sale."),
]


def main():
    params = cargar_parametros()

    if int(params.get("ventana_fatiga_dias", 3)) >= int(params.get("ventana_dias", 14)):
        print("FALLA  ventana_fatiga_dias debe ser MENOR que ventana_dias: si son iguales "
              "la celda se compara consigo misma y RENOVAR nunca se emite.")
        return 1

    fallas = 0
    for nombre, kw, esperado, porque in CASOS:
        obtenido = evaluar_celda(be_q=BE, obj_q=OBJ, tasa=TASA, params=params, **kw)
        estado = obtenido["estado"]
        if estado == esperado:
            print("  OK     %s" % nombre)
        else:
            fallas += 1
            print("  FALLA  %s\n         esperado=%s  obtenido=%s (%s)\n         %s"
                  % (nombre, esperado, estado, obtenido["accion_codigo"], porque))

    print("\n%d de %d casos pasan." % (len(CASOS) - fallas, len(CASOS)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
