import sys, time
from faster_whisper import WhisperModel
t0 = time.time()
m = WhisperModel("small", device="cpu", compute_type="int8")
t1 = time.time()
segs, info = m.transcribe(sys.argv[1], language="es", vad_filter=True)
texto = " ".join(s.text.strip() for s in segs)
t2 = time.time()
print(f"carga_modelo={t1-t0:.1f}s transcripcion={t2-t1:.1f}s duracion_audio={info.duration:.1f}s idioma={info.language}")
print(texto)
