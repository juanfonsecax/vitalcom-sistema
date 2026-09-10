#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decidir_operativo.py — Wrapper de compatibilidad hacia decidir.py.

La doctrina y la ejecución están unificadas en Ads/_TOOLS/decidir.py (Motor de Decisión Unificado).
Este archivo redirige transparentemente cualquier invocación hacia el motor unificado.
"""
import sys
import os

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decidir import main

if __name__ == "__main__":
    sys.exit(main())
