# -*- coding: utf-8 -*-
"""ETAPA-9 PASO 4 (registro) - CLEARSTEM / ANTI_FALSIFICACION.

Anexa 10 filas a PRODUCTOS/_DIM_CREATIVOS.csv con un escritor CSV real
(invariante 11). NO toca ninguna fila existente: lee todo, reescribe tal cual
y anexa al final.

Los 10 canonicos vienen DADOS (ya los eligio armar_prompts_fase2.py); este
script no selecciona nada.
"""
import csv, json, os, sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_CREATIVOS = os.path.join(RAIZ, "PRODUCTOS", "_DIM_CREATIVOS.csv")
PAQUETE = os.path.join(RAIZ, "Ads", "MEDIA_CLEARSTEM", "FASE2_ANTI_FALSIFICACION",
                       "PAQUETE_CREATIVO_ANTI_FALSIFICACION.json")
CANONICOS = os.path.join(RAIZ, "Ads", "_SWIPE", "_BLUEPRINTS", "CANONICOS")

PRODUCTO = "CLEARSTEM"
ANGULO = "ANTI_FALSIFICACION"
CUENTA = "GTR13"
ID_TANDA = "CLEARSTEM-T01"
FECHA_ALTA = "2026-10-09"
# del conjunto del angulo en _DIM_CONJUNTOS.csv (fila plantilla 'Anti-Falsificacion')
AVATAR_EDAD = "25-35"
AVATAR_GENERO = "MIXTO"
# el prompt del paquete instruye MSPAS NS02026-GT3147 + FDA
BADGE = "MSPAS_VIGENTE"

# orden exacto entregado por armar_prompts_fase2.py
ORDEN = [
    "CN05_LISTA_BENEFICIOS",
    "CN01_ANTES_DESPUES",
    "CN02_TIMELINE_PROGRESION",
    "CN10_PRUEBA_SOCIAL",
    "CN14_COMPARACION_DOS_COLUMNAS",
    "CN04_ESCALERA_PRECIOS",
    "CN06_CHECKLIST_SINTOMAS",
    "CN13_ANATOMIA_MECANISMO",
    "CN17_TITULAR_DOMINANTE",
    "CN15_INGREDIENTES_ACTIVO",
]
# avisados por el script como repetidores de concepto_key (ya no quedaban sin usar)
REPITEN = {"CN04_ESCALERA_PRECIOS", "CN06_CHECKLIST_SINTOMAS", "CN13_ANATOMIA_MECANISMO",
           "CN17_TITULAR_DOMINANTE", "CN15_INGREDIENTES_ACTIVO"}
# el dispositivo de testimonio solo existe en la familia de prueba social
CON_TESTIMONIO = {"CN10_PRUEBA_SOCIAL"}


def dominante(hist):
    """Misma regla que seleccionar_canonicos.concepto_dominante: argmax, desempate
    por orden de insercion del JSON."""
    return max(hist.items(), key=lambda kv: kv[1])[0]


def main():
    paquete = json.load(open(PAQUETE, encoding="utf-8"))
    assert paquete["producto"] == PRODUCTO and paquete["angulo"] == ANGULO
    por_cid = {c["canonico_id"]: c for c in paquete["conceptos"]}
    faltan = [c for c in ORDEN if c not in por_cid]
    if faltan:
        sys.exit("canonicos de la lista que no estan en el paquete: %s" % faltan)

    with open(CSV_CREATIVOS, encoding="utf-8", newline="") as fh:
        rdr = csv.DictReader(fh)
        cols = list(rdr.fieldnames)
        previas = list(rdr)

    ya = {(r["producto_key"], r["angulo_key"], r["canonico_id"]) for r in previas}

    nuevas = []
    for cid in ORDEN:
        c = por_cid[cid]
        bp = json.load(open(os.path.join(CANONICOS, cid + ".json"), encoding="utf-8"))
        perfil = bp["perfil"]
        ck = dominante(perfil["concepto_key"])
        archivo = c["archivo_salida"]
        creativo_id = os.path.splitext(archivo)[0]
        if (PRODUCTO, ANGULO, cid) in ya:
            sys.exit("YA REGISTRADO, abortando para no duplicar: %s" % cid)

        notas = (
            "FASE 2 del angulo ganador ANTI_FALSIFICACION. Slot %d del paquete. "
            "Blueprint: %s (%s), ref %s. Prompt ya armado por armar_prompts_fase2.py en "
            "Ads/MEDIA_CLEARSTEM/FASE2_ANTI_FALSIFICACION/. "
            "concepto_key %s%s. "
            "PENDIENTE a definir en render/etapa-6: estilo_visual, tipo_sello, color_dominante, brazo."
        ) % (
            c["slot"], cid, bp["nombre"], bp.get("ficha_referencia", "?"), ck,
            " (REPITE: ya no quedaban concepto_key sin usar, decidido por el script)"
            if cid in REPITEN else "",
        )

        fila = {k: "" for k in cols}
        fila.update({
            "producto_key": PRODUCTO,
            "creativo_id": creativo_id,
            "archivo": archivo,
            "cuenta_destino": CUENTA,
            "angulo_key": ANGULO,
            "concepto_key": ck,
            "canonico_id": cid,
            "rol_embudo": dominante(perfil["rol_embudo"]),
            "densidad": dominante(perfil["densidad"]),
            "estetica": dominante(perfil["estetica"]),
            "id_tanda": ID_TANDA,
            "formato": "IMAGEN",
            "tipo_hook": "ANTI_FALSIFICACION",
            "lleva_precio": "SI",          # los 10 prompts llevan la escalera de precios
            "tiene_testimonio": "SI" if cid in CON_TESTIMONIO else "NO",
            "avatar_edad": AVATAR_EDAD,
            "avatar_genero": AVATAR_GENERO,
            "badge_regulatorio": BADGE,
            "fecha_alta": FECHA_ALTA,
            "estado": "PENDIENTE_GENERAR",
            "notas": notas,
        })
        nuevas.append(fila)

    # Append puro: no se reescribe ni un byte de las filas existentes (CRLF, UTF-8).
    with open(CSV_CREATIVOS, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, quoting=csv.QUOTE_MINIMAL,
                           lineterminator="\r\n")
        for r in nuevas:
            w.writerow(r)

    print("filas previas: %d | filas nuevas: %d" % (len(previas), len(nuevas)))
    for r in nuevas:
        print("  %-30s %-30s %-16s %-5s %s" % (r["creativo_id"], r["canonico_id"],
                                               r["concepto_key"], r["rol_embudo"],
                                               r["estado"]))


if __name__ == "__main__":
    main()
