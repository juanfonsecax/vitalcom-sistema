"""Un proceso que muere a mitad de un paso, para probar que el runner retoma o deja rastro.

Lo lanza `test_workflows.py` como subproceso (mismo patrón que el spike C): la caída es real
—`os._exit`— y el estado vive en la SQLite de DBOS. Usa `VITALCOM_BASE` y `VITALCOM_DATOS`.

  driver_caida.py arrancar <accion_id> <job_id> [parametros_json [segundos]]
      encola el trabajo. Sin `segundos`, el proceso MUERE cuando la unidad va a correr su
      comando (el comando nunca corre). Con `segundos`, muere ESA cantidad de segundos después de
      arrancar, con el comando real corriendo (queda un log parcial).
  driver_caida.py retomar <job_id>
      relanza DBOS (que retoma lo pendiente) y escribe en stdout el resultado del trabajo.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time

from vitalcom_app import acciones, workflows


def arrancar(accion_id: str, job_id: str, parametros: dict, segundos: float | None) -> None:
    workflows.iniciar()

    def morir(*_argumentos):
        os._exit(3)

    if segundos is None:
        workflows.correr_script = morir  # el comando nunca llega a correr
        workflows.correr_claude = morir
    else:
        threading.Timer(segundos, morir).start()
    accion = acciones.por_id_para_el_runner(accion_id)
    workflows.encolar(accion, parametros, job_id)
    time.sleep(60)  # si llegamos acá, nadie mató al proceso: la prueba lo detecta por el código de salida
    sys.exit(0)


def retomar(job_id: str) -> None:
    workflows.iniciar()
    resultado = workflows.esperar_resultado(job_id, 90)
    print(json.dumps(resultado, ensure_ascii=False, default=str))
    workflows.detener()


if __name__ == "__main__":
    if sys.argv[1] == "arrancar":
        arrancar(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]) if len(sys.argv) > 4 else {},
                 float(sys.argv[5]) if len(sys.argv) > 5 else None)
    else:
        retomar(sys.argv[2])
