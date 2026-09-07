# -*- coding: utf-8 -*-
"""ingerir_creativos.py — Ingestor y Catalogador de Creativos tipo SaaS.

QUÉ HACE:
1. Lee las imágenes depositadas en INBOX/ (descargadas de ChatGPT/Gemini).
2. Las cruza con el paquete de Fase 2 (PAQUETE_CREATIVO_*.json).
3. Renombra cada imagen con su nomenclatura canónica oficial:
   [PRODUCTO]_F2_[CANONICO]_[ANGULO].png
4. Mueve la imagen a Ads/MEDIA_[PRODUCTO]/
5. Genera la Ficha JSON atómica del creativo (SaaS metadata):
   Ads/MEDIA_[PRODUCTO]/FICHAS/[CREATIVO_ID].json
   con rol de embudo (TOFU/MOFU/BOFU), dolor, ángulo, blueprint y precios.
6. Actualiza PRODUCTOS/_DIM_CREATIVOS.csv con estado = 'GENERADO'.
7. Deja INBOX/ limpio y listo para la siguiente tanda.

USO:
    python Ads/_TOOLS/ingerir_creativos.py TINNIDROP ACCESIBILIDAD_MEDICO
    python Ads/_TOOLS/ingerir_creativos.py --listar
"""

import os
import sys
import io
import csv
import json
import shutil
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = os.path.join(BASE, "INBOX")
PROD_DIR = os.path.join(BASE, "PRODUCTOS")
DIM_CREATIVOS = os.path.join(PROD_DIR, "_DIM_CREATIVOS.csv")


def listar_inbox():
    if not os.path.exists(INBOX_DIR):
        os.makedirs(INBOX_DIR, exist_ok=True)
    exts = (".png", ".jpg", ".jpeg", ".webp")
    return sorted([f for f in os.listdir(INBOX_DIR) if f.lower().endswith(exts) and not f.startswith(".")])


def cargar_paquete(producto_key, angulo_key):
    ruta_paquete = os.path.join(
        BASE, "Ads", f"MEDIA_{producto_key}", f"FASE2_{angulo_key}",
        f"PAQUETE_CREATIVO_{angulo_key}.json"
    )
    if not os.path.exists(ruta_paquete):
        dir_media = os.path.join(BASE, "Ads", f"MEDIA_{producto_key}")
        if os.path.exists(dir_media):
            for root, _, files in os.walk(dir_media):
                for f in files:
                    if f.startswith("PAQUETE_CREATIVO") and f.endswith(".json"):
                        return os.path.join(root, f)
        return None
    return ruta_paquete


def actualizar_dim_creativos(filas_nuevas):
    if not os.path.exists(DIM_CREATIVOS):
        return
    
    with io.open(DIM_CREATIVOS, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        filas_existentes = list(reader)

    ids_existentes = {r["creativo_id"]: i for i, r in enumerate(filas_existentes)}

    for n in filas_nuevas:
        cid = n.get("creativo_id")
        if cid in ids_existentes:
            filas_existentes[ids_existentes[cid]].update(n)
        else:
            fila_completa = {k: "" for k in fieldnames}
            fila_completa.update(n)
            filas_existentes.append(fila_completa)

    with io.open(DIM_CREATIVOS, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filas_existentes)


def ingerir(producto_key, angulo_key, mapeo_manual=None):
    archivos = listar_inbox()
    if not archivos:
        print(f"⚠️  El directorio INBOX/ ({INBOX_DIR}) está vacío.")
        print("   Por favor arrastra tus imágenes descargadas ahí y vuelve a correr el comando.")
        return 1

    print("=" * 80)
    print(f" 📥 INGESTOR SAAS DE CREATIVOS — {producto_key} | {angulo_key}")
    print(f" Imágenes encontradas en INBOX/: {len(archivos)}")
    print("=" * 80)

    paquete_path = cargar_paquete(producto_key, angulo_key)
    if not paquete_path or not os.path.exists(paquete_path):
        print(f"❌ Error: No se encontró el paquete JSON en Ads/MEDIA_{producto_key}/FASE2_{angulo_key}/")
        print("   Primero corre: python Ads/_TOOLS/armar_prompts_fase2.py " + producto_key + " " + angulo_key)
        return 1

    with io.open(paquete_path, encoding="utf-8") as fh:
        paquete = json.load(fh)

    conceptos = paquete.get("conceptos", [])
    if not conceptos:
        print("❌ Error: El paquete no tiene conceptos definidos.")
        return 1

    dir_media = os.path.join(BASE, "Ads", f"MEDIA_{producto_key}")
    dir_fichas = os.path.join(dir_media, "FICHAS")
    os.makedirs(dir_fichas, exist_ok=True)

    filas_csv = []
    hoy_str = datetime.date.today().isoformat()

    for i, ar in enumerate(archivos):
        slot_idx = i
        if mapeo_manual and ar in mapeo_manual:
            slot_idx = mapeo_manual[ar]
        elif slot_idx >= len(conceptos):
            print(f"⚠️  Archivo sobrante '{ar}' sin slot en paquete. Saltando.")
            continue

        c = conceptos[slot_idx]
        cid_base = c["canonico_id"].split("_")[0]
        nombre_salida = c.get("archivo_salida") or f"{producto_key}_F2_{cid_base}_{angulo_key[:12]}.png"
        creativo_id = os.path.splitext(nombre_salida)[0]

        ruta_origen = os.path.join(INBOX_DIR, ar)
        ruta_destino = os.path.join(dir_media, nombre_salida)

        shutil.copy2(ruta_origen, ruta_destino)
        os.remove(ruta_origen)

        v = c.get("variables_json", {})
        ficha_json = {
            "creativo_id": creativo_id,
            "archivo": nombre_salida,
            "producto_key": producto_key,
            "angulo_key": angulo_key,
            "dolor_atacado": v.get("SINTOMA_ANTES", "Accesibilidad económica y frustración médica"),
            "transformacion_prometida": v.get("RESULTADO_DESPUES", "Alivio auditivo y tranquilidad"),
            "concepto_key": "C2_BENEFICIOS" if "BENEFICIOS" in c["canonico_id"] else ("C1_TESTIMONIO" if "TESTIMONIO" in c["canonico_id"] else "C9_COMPARACION"),
            "canonico_id": c["canonico_id"],
            "nombre_blueprint": c.get("nombre_blueprint", ""),
            "rol_embudo": "BOFU" if "PRECIOS" in c["canonico_id"] or "OFERTA" in c["canonico_id"] else "MOFU",
            "nivel_conciencia": "NC2",
            "dispositivo_visual": c.get("dispositivo_visual", ""),
            "precios_gt": v.get("PRECIOS_GT", {}),
            "hook_titular": v.get("HOOK_TITULAR", ""),
            "garantias": v.get("GARANTIAS", ""),
            "cta": v.get("CTA", ""),
            "firma_meta": f"{producto_key}|{angulo_key[:15]}|{cid_base}|NC2|2X1|BOTv1",
            "blueprint_referencia": c.get("foto_base_competidor", ""),
            "fecha_creacion": hoy_str,
            "estado": "GENERADO"
        }

        ruta_ficha = os.path.join(dir_fichas, f"{creativo_id}.json")
        with io.open(ruta_ficha, "w", encoding="utf-8") as fh:
            json.dump(ficha_json, fh, ensure_ascii=False, indent=2)

        filas_csv.append({
            "producto_key": producto_key,
            "creativo_id": creativo_id,
            "archivo": nombre_salida,
            "cuenta_destino": "GTR0",
            "angulo_key": angulo_key,
            "concepto_key": ficha_json["concepto_key"],
            "canonico_id": c["canonico_id"],
            "rol_embudo": ficha_json["rol_embudo"],
            "formato": "IMAGEN",
            "tipo_hook": "EMOCIONAL",
            "lleva_precio": "SI" if v.get("PRECIOS_GT") else "NO",
            "tiene_testimonio": "SI" if "TESTIMONIO" in c["canonico_id"] or "PRUEBA" in c["canonico_id"] else "NO",
            "fecha_alta": hoy_str,
            "estado": "GENERADO",
            "notas": f"Fase 2 Lean. Blueprint: {c['canonico_id']} ({c.get('nombre_blueprint')}). Dolor: {v.get('HOOK_TITULAR')[:50]}"
        })

        print(f"  ✅ [Slot {slot_idx+1}] {ar} -> {nombre_salida}")
        print(f"     Ficha SaaS: Ads/MEDIA_{producto_key}/FICHAS/{creativo_id}.json")
        print(f"     Blueprint: {c['canonico_id']} | Rol: {ficha_json['rol_embudo']}")

    actualizar_dim_creativos(filas_csv)
    print("\n" + "=" * 80)
    print(f" 🎉 INGESTA COMPLETADA: {len(filas_csv)} creativos catalogados con éxito.")
    print(f"     Archivos en disco: Ads/MEDIA_{producto_key}/")
    print(f"     Fichas JSON:       Ads/MEDIA_{producto_key}/FICHAS/")
    print(f"     Registro Maestro:  PRODUCTOS/_DIM_CREATIVOS.csv (actualizado)")
    print("=" * 80)
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--listar":
        archivos = listar_inbox()
        print(f"Archivos en INBOX/ ({len(archivos)}):")
        for a in archivos:
            print("  ·", a)
        return 0

    pk = sys.argv[1] if len(sys.argv) > 1 else "TINNIDROP"
    ang = sys.argv[2] if len(sys.argv) > 2 else "ACCESIBILIDAD_MEDICO"
    return ingerir(pk, ang)


if __name__ == "__main__":
    sys.exit(main())
