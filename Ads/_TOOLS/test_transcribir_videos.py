#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_transcribir_videos.py — GATE DEL TRANSCRIPTOR LOCAL.

No prueba a whisper (eso es del spike E, medido el 17-sep-2026): prueba las reglas que el
sistema necesita alrededor de el, con un transcriptor de mentira. Congela:
  · la carpeta sale de _DIM_PRODUCTOS.csv, nunca del nombre del producto (invariante 10);
  · cada TXT dice que es SOLO AUDIO, para que nadie lo confunda con el analisis de 8
    bloques de Gemini, que ademas describe lo que se ve;
  · un video casi sin voz se avisa en vez de dejar un TXT vacio que etapa-0 leeria como
    "sin dolor definido";
  · no se rehace lo ya transcrito salvo que se pida;
  · --dry-run no escribe.

USO:  python Ads/_TOOLS/test_transcribir_videos.py     (exit 0 = pasa, 1 = falla)
"""

import csv
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transcribir_videos as tv  # noqa: E402

COLUMNAS = ["producto_key", "nombre_display", "carpeta_videos", "carpeta_transcripciones"]


def _fixture(base):
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "w",
                 encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(COLUMNAS)
        # La carpeta de videos se llama distinto que el producto: es el caso real de
        # OVULOS_PURITY, cuyos videos viven en "HERNATURA".
        escritor.writerow(["OVULOS_PURITY", "Óvulos Purity", "HERNATURA", "OVULOS PURITY HERNATURA"])
    carpeta_videos = os.path.join(base, tv.CARPETA_VIDEOS, "HERNATURA")
    os.makedirs(carpeta_videos)
    for nombre in ("uno.mp4", "dos.mp4", "ignorar.txt"):
        io.open(os.path.join(carpeta_videos, nombre), "w", encoding="utf-8").write("x")
    return carpeta_videos


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    fallas = []
    base = tempfile.mkdtemp(prefix="transcribir_test_")
    try:
        carpeta_videos = _fixture(base)
        videos = tv.videos_en(carpeta_videos)
        habla = lambda ruta: (  # noqa: E731
            "Si sufres de un zumbido en el oido que no te deja dormir, esto es para vos. "
            "Un cientifico descubrio como apagarlo en dos minutos con un audio."
        )
        salida = os.path.join(tv.CARPETA_TRANSCRIPCIONES, "OVULOS PURITY HERNATURA")

        def solo_toma_videos():
            assert [os.path.basename(v) for v in videos] == ["dos.mp4", "uno.mp4"], videos

        def la_carpeta_sale_del_csv():
            carpeta_v, carpeta_t = tv.carpeta_del_producto(base, "OVULOS_PURITY")
            assert carpeta_v == "HERNATURA", carpeta_v
            assert carpeta_t == "OVULOS PURITY HERNATURA", carpeta_t

        def producto_sin_fila_se_rechaza():
            try:
                tv.carpeta_del_producto(base, "NO_EXISTE")
                raise AssertionError("tenia que rechazar")
            except tv.Rechazo as rechazo:
                assert "_DIM_PRODUCTOS.csv" in str(rechazo)

        def dry_run_no_escribe():
            resumen = tv.transcribir(base, videos, salida, dry_run=True, transcriptor=habla)
            assert not os.path.isdir(os.path.join(base, salida)), "no se crea la carpeta"
            assert {a["estado"] for a in resumen["archivos"]} == {"SE_HARIA"}

        def transcribe_y_marca_que_es_audio():
            resumen = tv.transcribir(base, videos, salida, transcriptor=habla, hoy="2026-09-17")
            assert len(resumen["archivos"]) == 2
            ruta = os.path.join(base, salida, "uno.txt")
            assert os.path.isfile(ruta), "falta uno.txt"
            texto = io.open(ruta, encoding="utf-8").read()
            assert "solo lo que se ESCUCHA" in texto, "el TXT tiene que decir que es solo audio"
            assert "zumbido en el oido" in texto, "tiene que traer el texto transcrito"
            assert "uno.mp4" in texto and "2026-09-17" in texto

        def no_rehace_lo_hecho():
            resumen = tv.transcribir(base, videos, salida, transcriptor=habla)
            assert {a["estado"] for a in resumen["archivos"]} == {"YA_EXISTIA"}, resumen

        def rehacer_lo_pide_explicito():
            resumen = tv.transcribir(base, videos, salida, transcriptor=habla, rehacer=True)
            assert {a["estado"] for a in resumen["archivos"]} == {"TRANSCRITO"}

        def video_sin_voz_se_avisa():
            mudo = lambda ruta: "  "  # noqa: E731
            otra = os.path.join(tv.CARPETA_TRANSCRIPCIONES, "MUDOS")
            resumen = tv.transcribir(base, videos[:1], otra, transcriptor=mudo)
            assert resumen["sin_voz"], "un video sin voz tiene que avisarse"
            texto = io.open(os.path.join(base, otra, "dos.txt"), encoding="utf-8").read()
            assert "casi no hay voz" in texto, "el aviso va dentro del TXT, donde etapa-0 lo lee"

        def sin_whisper_dice_como_instalarlo():
            """El mensaje tiene que traer el comando, no un ImportError pelado."""
            import builtins
            real = builtins.__import__

            def sin_faster(nombre, *args, **kwargs):
                if nombre.startswith("faster_whisper"):
                    raise ImportError("no esta")
                return real(nombre, *args, **kwargs)

            builtins.__import__ = sin_faster
            try:
                tv.cargar_modelo("small")
                raise AssertionError("tenia que rechazar")
            except tv.Rechazo as rechazo:
                assert "pip install" in str(rechazo), rechazo
            finally:
                builtins.__import__ = real

        print("GATE DEL TRANSCRIPTOR LOCAL")
        for nombre, funcion in (
            ("solo toma archivos de video", solo_toma_videos),
            ("la carpeta sale del CSV, no del nombre", la_carpeta_sale_del_csv),
            ("un producto sin fila se rechaza", producto_sin_fila_se_rechaza),
            ("--dry-run no escribe", dry_run_no_escribe),
            ("transcribe y marca que es solo audio", transcribe_y_marca_que_es_audio),
            ("no rehace lo ya transcrito", no_rehace_lo_hecho),
            ("--rehacer lo vuelve a hacer", rehacer_lo_pide_explicito),
            ("un video sin voz se avisa", video_sin_voz_se_avisa),
            ("sin whisper dice como instalarlo", sin_whisper_dice_como_instalarlo),
        ):
            caso(nombre, funcion, fallas)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if fallas:
        print(f"\n{len(fallas)} falla(s): " + ", ".join(fallas))
        return 1
    print("\nTodo en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
