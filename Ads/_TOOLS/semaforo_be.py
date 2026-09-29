#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semaforo_be.py - color de un costo por venta contra el break-even.

Dueno unico de la regla de color de la pantalla de FASE 2 (la app no compara ni calcula).
  verde: valor < 0.8 x BE  |  ambar: 0.8 x BE <= valor <= BE  |  rojo: valor > BE  |  "" si falta dato.
Pura y sin E/S. Prueba: python Ads/_TOOLS/test_semaforo_be.py
"""

AMBAR_DESDE = 0.8


def semaforo(valor, be):
    if valor is None or be is None or be <= 0:
        return ""
    if valor > be:
        return "rojo"
    if valor >= AMBAR_DESDE * be:
        return "ambar"
    return "verde"
