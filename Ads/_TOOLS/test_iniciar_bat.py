#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_iniciar_bat.py -- GATE de iniciar.bat (g07-cimientos T8-1, 23-sep-2026).

iniciar.bat corre SOBRE la carpeta donde vive: si esa carpeta es un WORKTREE
VINCULADO de git (ej. SISTEMA-app, donde se desarrolla) en vez de la carpeta
PRINCIPAL (SISTEMA, la dueña de PRODUCTOS/, Ads/MEDIA_* y los CSV reales), el
doble clic levantaria la app sobre datos viejos SIN AVISAR -- exactamente el
error de worktree del 17-sep-2026 que el propio archivo ya documenta en un
comentario, pero que antes de este cambio no comprobaba en codigo.

Este test es ESTATICO: comprueba que el .bat contiene la deteccion (git
rev-parse --git-dir vs --git-common-dir, la comparacion y el `exit /b 1`) y
el segundo chequeo de PRODUCTOS/_DIM_PRODUCTOS.csv, sin ejecutar cmd.exe.

Por que no hay prueba de comportamiento (invocando cmd.exe de verdad): en esta
maquina, el usuario sandbox bajo el que corre esta sesion (grupo
`CodexSandboxUsers`) no puede ejecutar NINGUN .bat -- ni uno trivial de una
sola linea ("not recognized as an internal or external command", el mismo
mensaje generico que da Windows cuando una politica de restriccion de
software bloquea el lanzamiento) -- mientras que invocar un .exe (git.exe,
cmd.exe con un builtin) funciona sin problema. Confirmado probando un
`q.bat` con una sola linea `echo hi` fuera de este archivo: mismo error.
Por eso, si algun dia se corre en una maquina donde `cmd.exe //c` sobre un
.bat SI funciona, vale la pena agregar la prueba de comportamiento descrita
en odd/tasks/g07-cimientos.md (T8-1): copiar iniciar.bat a un worktree git
temporal y confirmar que se niega con exit distinto de 0, y que en la carpeta
principal (o una carpeta suelta sin worktrees) sigue de largo.

USO:  python Ads/_TOOLS/test_iniciar_bat.py     (exit 0 = pasa, 1 = falla)
"""
import io
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(TOOLS))
RUTA_BAT = os.path.join(BASE, "iniciar.bat")


def _leer():
    with io.open(RUTA_BAT, encoding="utf-8") as fh:
        return fh.read()


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         " + str(detalle)[:400]))
    return 0 if ok else 1


def test_detecta_worktree_vinculado_por_git_dir():
    """La deteccion compara --git-dir contra --git-common-dir (distintos SOLO en un worktree
    vinculado) en vez de adivinar por el nombre de la carpeta."""
    txt = _leer()
    ok = ("--git-dir" in txt and "--git-common-dir" in txt
          and "worktree list --porcelain" in txt)
    return _informe(ok, "compara --git-dir vs --git-common-dir y lista los worktrees para nombrar el principal")


def test_se_niega_sin_adivinar():
    """Ante una base ambigua, el script tiene que salir con error, no seguir con VITALCOM_BASE
    apuntando al worktree vinculado."""
    txt = _leer()
    ok = "exit /b 1" in txt and "worktree vinculado" in txt.lower()
    return _informe(ok, "se niega (exit /b 1) y nombra el motivo (worktree vinculado) en vez de redirigir en silencio")


def test_respeta_vitalcom_base_explicito():
    """Si el operador ya declaro VITALCOM_BASE a mano, el chequeo de worktree no debe correr
    (ese es el escape declarado en el propio archivo: 'set VITALCOM_BASE antes de correr esto')."""
    txt = _leer()
    ok = 'if "%VITALCOM_BASE%"=="" (' in txt
    return _informe(ok, "el chequeo de worktree solo corre cuando VITALCOM_BASE no fue declarado a mano")


def test_bloquea_sin_dim_productos():
    """Ademas de DOCTRINA/FLUJO.json (ya existia), ahora tambien exige PRODUCTOS/_DIM_PRODUCTOS.csv:
    un worktree vinculado SI tiene FLUJO.json (es doctrina versionada) pero no los CSV de datos
    reales del operador si estos estan fuera del control de versiones esperado."""
    txt = _leer()
    ok = "PRODUCTOS\\_DIM_PRODUCTOS.csv" in txt or "PRODUCTOS\\\\_DIM_PRODUCTOS.csv" in txt
    return _informe(ok, "exige ademas PRODUCTOS\\_DIM_PRODUCTOS.csv antes de arrancar")


def main():
    pruebas = [
        test_detecta_worktree_vinculado_por_git_dir,
        test_se_niega_sin_adivinar,
        test_respeta_vitalcom_base_explicito,
        test_bloquea_sin_dim_productos,
    ]
    fallas = sum(p() for p in pruebas)
    print("\n%s." % ("0 fallas" if not fallas else "%d falla(s)" % fallas))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
