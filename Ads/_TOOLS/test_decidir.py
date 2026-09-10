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

    ("Conversacion floja por clic-ENLACE con 0 ventas: se mata SIN esperar el PD",
     dict(ventas=0, mensajes=10, spend_usd=6.0, ventas_3d=0, mensajes_3d=3, spend_3d=2.0,
          ventas_acum=0, mensajes_acum=10, spend_acum_usd=6.0,
          link_clicks_acum=60, mensajes_enlace_acum=10, dias_activo=2),
     "PAUSAR",
     "17% de conversacion por clic-enlace (<35%) es problema anuncio->bot (Joaquin, clases 7 y 15). "
     "Hasta el 09-sep-2026 esta regla vivia solo en prosa."),

    ("Conversacion floja pero SIN el piso de clics de enlace: no se juzga",
     dict(ventas=0, mensajes=2, spend_usd=2.0, ventas_3d=0, mensajes_3d=1, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=2, spend_acum_usd=2.0,
          link_clicks_acum=8, mensajes_enlace_acum=1, dias_activo=1),
     "SEGUIR_MIDIENDO",
     "Con 8 clics la proporcion es ruido binomial: matar por conversacion seria matar por azar."),

    ("PD agotado sin ventas pero con 1 solo dia con data: esperar la maduracion COD",
     dict(ventas=0, mensajes=20, spend_usd=13.0, ventas_3d=0, mensajes_3d=20, spend_3d=13.0,
          ventas_acum=0, mensajes_acum=20, spend_acum_usd=13.0, dias_activo=1),
     "SEGUIR_MIDIENDO",
     "El 0 ventas de un conjunto de 1 dia no es veredicto (ESCALADO_PLAYBOOK 1.5: ~3 dias COD)."),

    ("PD agotado sin ventas y la maduracion COD cumplida: ahora si se apaga",
     dict(ventas=0, mensajes=20, spend_usd=13.0, ventas_3d=0, mensajes_3d=5, spend_3d=3.0,
          ventas_acum=0, mensajes_acum=40, spend_acum_usd=13.0, dias_activo=4),
     "PAUSAR",
     "Mismo caso, 4 dias con data: el veredicto ya vale."),
]


def test_tope_pausas(params):
    """max_pausas_por_dia: se difieren las pausas que sobran, de menor gasto; el hook muerto nunca."""
    from decidir import aplicar_tope_pausas
    celdas = [
        {"celda": "A", "estado": "PAUSAR", "accion_codigo": "PAUSAR_CPA_DESBORDADO", "spend_q": 300.0, "accion_sugerida": "x"},
        {"celda": "B", "estado": "PAUSAR", "accion_codigo": "PAUSAR_TOLERANCIA_AGOTADA", "spend_q": 200.0, "accion_sugerida": "x"},
        {"celda": "C", "estado": "PAUSAR", "accion_codigo": "PAUSAR_CONVERSACION_FLOJA", "spend_q": 100.0, "accion_sugerida": "x"},
        {"celda": "D", "estado": "PAUSAR", "accion_codigo": "PAUSAR_HOOK_MUERTO", "spend_q": 5.0, "accion_sugerida": "x"},
        {"celda": "E", "estado": "ESCALAR", "accion_codigo": "ESCALAR_SURFING", "spend_q": 50.0, "accion_sugerida": "x"},
    ]
    diferidas = aplicar_tope_pausas(celdas, dict(params, max_pausas_por_dia=2))
    est = {c["celda"]: (c["estado"], c["accion_codigo"]) for c in celdas}
    ok = (diferidas == 1 and est["A"][0] == "PAUSAR" and est["B"][0] == "PAUSAR"
          and est["C"] == ("SEGUIR_MIDIENDO", "PAUSAR_DIFERIDA")
          and est["D"] == ("PAUSAR", "PAUSAR_HOOK_MUERTO") and est["E"][0] == "ESCALAR")
    print(("  OK     " if ok else "  FALLA  ") + "Tope de pausas por dia: 2 de mayor gasto + el hook muerto; la tercera queda diferida")
    return 0 if ok else 1


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

    fallas += test_tope_pausas(params)
    print("\n%d de %d casos pasan." % (len(CASOS) + 1 - fallas, len(CASOS) + 1))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
