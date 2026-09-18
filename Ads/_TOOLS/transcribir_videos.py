#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""transcribir_videos.py — pasa a texto los videos de la competencia, en esta maquina.

Por que existe
--------------
`etapa-0` necesita >=6 transcripciones TXT para clasificar angulos, y hasta hoy salian de
subir los videos a Gemini a mano. Eso obliga al operador a salir del sistema justo en el
primer paso. Con faster-whisper corre local: 52,6 s de video en 10,8 s sin placa de video
(medido el 17-sep-2026, spike E de la hoja de ruta).

QUE DA Y QUE NO DA (importante, no es lo mismo que hacia Gemini)
---------------------------------------------------------------
Esto transcribe el AUDIO. Los TXT que hay hoy en Ads/1.2 Transcripcion videos/ NO son
transcripciones crudas: son el "Analisis del Video" de 8 bloques del prompt de Gemini
(Ads/Prompt-Gemini.txt), que ademas describe lo que se VE y los textos en pantalla.
`etapa-0` clasifica por el hook de los primeros 5 segundos y el dolor, que estan en el
audio, asi que con esto le alcanza. Lo que se pierde: los bloques visuales y los videos
SIN VOZ, donde todo el mensaje esta en el texto en pantalla. Por eso cada TXT lleva un
encabezado que dice de donde salio, y los videos casi sin voz se avisan.

Uso
---
    python Ads/_TOOLS/transcribir_videos.py --producto OVULOS_PURITY
    python Ads/_TOOLS/transcribir_videos.py --videos "Ads/1.1 Videos/TINNIDROP" --salida-nombre TINNIDROP
    python Ads/_TOOLS/transcribir_videos.py --producto X --modelo medium --rehacer --json

La primera corrida baja el modelo (~480 MB). Se fija HF_HUB_DISABLE_XET=1: sin eso, la
descarga se colgo a los 134 MB por mas de 15 minutos; con eso tardo 11 segundos.
"""

import argparse
import csv
import io
import json
import os
import sys

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_POR_DEFECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_VIDEOS = os.path.join("Ads", "1.1 Videos")
CARPETA_TRANSCRIPCIONES = os.path.join("Ads", "1.2 Transcripcion videos")
EXTENSIONES = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")
PALABRAS_MINIMAS = 20  # menos que esto es un video sin voz: el mensaje esta en pantalla

ENCABEZADO = """\
============================================================
{archivo}
Transcripcion del AUDIO — transcribir_videos.py (faster-whisper {modelo})
{fecha}
------------------------------------------------------------
OJO: esto es solo lo que se ESCUCHA. No incluye lo que se ve ni
los textos en pantalla, que si trae el prompt de Gemini
(Ads/Prompt-Gemini.txt, 8 bloques). etapa-0 clasifica por el
hook de los primeros 5 segundos y el dolor, que estan aca.
{aviso}============================================================

{texto}
"""


class Rechazo(Exception):
    """Falta algo o no cuadra: se dice y se detiene (invariante 4)."""


def carpeta_del_producto(base, producto_key):
    """Resuelve la carpeta leyendo _DIM_PRODUCTOS.csv; nunca se adivina (invariante 10)."""
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    if not os.path.isfile(ruta):
        raise Rechazo("falta PRODUCTOS/_DIM_PRODUCTOS.csv")
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for fila in csv.DictReader(fh):
            if fila.get("producto_key", "").strip() == producto_key:
                return (fila.get("carpeta_videos") or producto_key,
                        fila.get("carpeta_transcripciones") or producto_key)
    raise Rechazo(
        f"«{producto_key}» no tiene fila en _DIM_PRODUCTOS.csv. Dalo de alta primero "
        "(Ads/_TOOLS/alta_producto.py): sin fila es invisible para el sistema (invariante 8)."
    )


def videos_en(carpeta):
    if not os.path.isdir(carpeta):
        raise Rechazo(f"no existe la carpeta de videos «{carpeta}»")
    return sorted(
        os.path.join(carpeta, nombre)
        for nombre in os.listdir(carpeta)
        if nombre.lower().endswith(EXTENSIONES)
    )


def cargar_modelo(nombre_modelo):
    """Carga faster-whisper. Si no esta instalado, lo dice con el comando exacto."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise Rechazo(
            "falta faster-whisper en este Python. Instalalo con:\n"
            "    python -m pip install --user faster-whisper"
        )
    return WhisperModel(nombre_modelo, device="cpu", compute_type="int8")


def texto_de_video(modelo, ruta_video, idioma):
    """Devuelve el texto del audio. Es la unica parte que depende de whisper."""
    segmentos, _info = modelo.transcribe(ruta_video, language=idioma, vad_filter=True)
    return " ".join(segmento.text.strip() for segmento in segmentos).strip()


def transcribir(base, entradas, carpeta_salida, nombre_modelo="small", idioma="es",
                rehacer=False, dry_run=False, transcriptor=None, hoy=None):
    """Transcribe cada video y deja un TXT por video. Devuelve el resumen, sin imprimir."""
    import datetime

    fecha = hoy or datetime.date.today().isoformat()
    destino = os.path.join(base, carpeta_salida)
    resultados = []
    pendientes = []
    for video in entradas:
        nombre = os.path.splitext(os.path.basename(video))[0] + ".txt"
        salida = os.path.join(destino, nombre)
        if os.path.isfile(salida) and not rehacer:
            resultados.append({"video": os.path.basename(video), "txt": nombre,
                               "estado": "YA_EXISTIA", "palabras": None})
            continue
        pendientes.append((video, salida, nombre))

    if dry_run:
        for _video, _salida, nombre in pendientes:
            resultados.append({"video": nombre[:-4], "txt": nombre, "estado": "SE_HARIA",
                               "palabras": None})
        return {"carpeta_salida": carpeta_salida, "modelo": nombre_modelo,
                "archivos": resultados, "sin_voz": []}

    if pendientes and transcriptor is None:
        modelo = cargar_modelo(nombre_modelo)
        transcriptor = lambda ruta: texto_de_video(modelo, ruta, idioma)  # noqa: E731

    if pendientes and not os.path.isdir(destino):
        os.makedirs(destino)

    sin_voz = []
    for video, salida, nombre in pendientes:
        texto = (transcriptor(video) or "").strip()
        palabras = len(texto.split())
        aviso = ""
        if palabras < PALABRAS_MINIMAS:
            aviso = ("AVISO: casi no hay voz en este video ({} palabra(s)). Lo que vende puede\n"
                     "estar en el texto en pantalla; convendria mirarlo o pasarlo por Gemini.\n"
                     ).format(palabras)
            sin_voz.append(os.path.basename(video))
        with io.open(salida, "w", encoding="utf-8") as fh:
            fh.write(ENCABEZADO.format(archivo=os.path.basename(video), modelo=nombre_modelo,
                                       fecha=fecha, aviso=aviso, texto=texto))
        resultados.append({"video": os.path.basename(video), "txt": nombre,
                           "estado": "TRANSCRITO", "palabras": palabras})

    return {"carpeta_salida": carpeta_salida, "modelo": nombre_modelo,
            "archivos": resultados, "sin_voz": sin_voz}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Transcribe videos a TXT, en local")
    ap.add_argument("--producto", default=None, help="producto_key de _DIM_PRODUCTOS.csv")
    ap.add_argument("--videos", default=None, help="carpeta con los videos (si no se usa --producto)")
    ap.add_argument("--salida-nombre", default=None, help="subcarpeta de Ads/1.2 Transcripcion videos/")
    ap.add_argument("--modelo", default="small", help="tiny, base, small (por defecto), medium")
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--rehacer", action="store_true", help="rehace los TXT que ya existen")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--base", default=BASE_POR_DEFECTO)
    args = ap.parse_args(argv)

    try:
        if args.producto:
            carpeta_videos, carpeta_txt = carpeta_del_producto(args.base, args.producto)
        elif args.videos:
            carpeta_videos = None
            carpeta_txt = args.salida_nombre or os.path.basename(os.path.normpath(args.videos))
        else:
            raise Rechazo("hay que pasar --producto o --videos")

        origen = (args.videos if args.videos
                  else os.path.join(args.base, CARPETA_VIDEOS, carpeta_videos))
        if not os.path.isabs(origen):
            origen = os.path.join(args.base, origen)
        entradas = videos_en(origen)
        if not entradas:
            raise Rechazo(f"no hay videos ({', '.join(EXTENSIONES)}) en «{origen}»")

        resumen = transcribir(
            args.base, entradas, os.path.join(CARPETA_TRANSCRIPCIONES, carpeta_txt),
            nombre_modelo=args.modelo, idioma=args.idioma, rehacer=args.rehacer,
            dry_run=args.dry_run,
        )
    except Rechazo as rechazo:
        if args.json:
            print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False))
        else:
            print(f"BLOQUEANTE: {rechazo}", file=sys.stderr)
        return 1

    if args.json:
        resumen["ok"] = True
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
    else:
        hechos = [a for a in resumen["archivos"] if a["estado"] == "TRANSCRITO"]
        print(f"{len(hechos)} transcripcion(es) en {resumen['carpeta_salida']}/ "
              f"(modelo {resumen['modelo']})")
        for archivo in resumen["archivos"]:
            print(f"  {archivo['estado']:11} {archivo['txt']}")
        if resumen["sin_voz"]:
            print("\nCasi sin voz (el mensaje puede estar en pantalla): "
                  + ", ".join(resumen["sin_voz"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
