#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_semaforo_be.py - congela la regla de color contra el break-even. exit 0 = pasa."""
import sys

from semaforo_be import semaforo

CASOS = [(50.0, 100.0, "verde"), (79.9, 100.0, "verde"), (80.0, 100.0, "ambar"), (100.0, 100.0, "ambar"),
         (100.1, 100.0, "rojo"), (None, 100.0, ""), (50.0, None, ""), (50.0, 0, "")]
malos = [(c, semaforo(c[0], c[1])) for c in CASOS if semaforo(c[0], c[1]) != c[2]]
if malos:
    print("FALLA", malos)
    sys.exit(1)
print("OK semaforo_be")
