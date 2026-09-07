#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_fase2_lean.py — PROTOCOLO LEAN DE FASE 2 (TESTEO RÁPIDO DE CONCEPTOS).

OBJETIVO:
Elimina la trampa de 3 campañas en 2 cuentas publicitarias que congeló a TINNIDROP
por 13 días. Permite a un solo operador validar qué concepto visual vende el ángulo
ganador en 72 horas con 1 sola campaña ABO en su cuenta principal.

ESTRUCTURA:
  - 1 Campaña ABO en la cuenta activa.
  - 4 a 5 conjuntos (1 por concepto).
  - Presupuesto: $5.00 a $6.00 por conjunto.
  - Ángulo, copy y bot FIJOS en el ganador (constante de control).
  - Lo único que varía es el DISPOSITIVO VISUAL (concepto).

USO:
    python Ads/_TOOLS/gen_fase2_lean.py TINNIDROP ACCESIBILIDAD_MEDICO
    python Ads/_TOOLS/gen_fase2_lean.py CLEARSTEM ANTI_FALSIFICACION
"""

import os
import sys
import io
import json
import csv
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DIM_PROD = os.path.join(PROD, "_DIM_PRODUCTOS.csv")

CONCEPTOS_CANONICOS = [
    {
        "concepto_key": "C1_TESTIMONIO_RADICAL",
        "canonico_id": "CN02_TESTIMONIO_CHAT",
        "rol_embudo": "MOFU",
        "dispositivo": "Captura de chat de WhatsApp con clienta agradecida y foto del producto real en mano.",
        "estructura_visual": "Fondo cálido, captura de mensaje legible con hora y fecha, producto en esquina inferior con badge '100% Original'."
    },
    {
        "concepto_key": "C2_LISTA_BENEFICIOS",
        "canonico_id": "CN05_LISTA_BENEFICIOS",
        "rol_embudo": "MOFU",
        "dispositivo": "Producto al centro con 3 checks verdes gigantes de beneficios clave directos al dolor.",
        "estructura_visual": "Fondo editorial limpio, frasco protagonista con iluminación de estudio, badges 'Envío Gratis' y 'Pagás al recibir'."
    },
    {
        "concepto_key": "C3_COMPARATIVA_VS_OTROS",
        "canonico_id": "CN08_TABLA_COMPARATIVA",
        "rol_embudo": "MOFU",
        "dispositivo": "Tabla comparativa dividida en 2: 'Pastillas comunes / Tratamientos caros' (❌) vs 'Este producto' (✅).",
        "estructura_visual": "División visual vertical clara, cruces rojas vs checks verdes, precio accesible destacado al pie."
    },
    {
        "concepto_key": "C4_OFERTA_IRRESISTIBLE",
        "canonico_id": "CN11_BODEGA_OFERTA",
        "rol_embudo": "BOFU",
        "dispositivo": "Foto en bodega o despacho con etiqueta 'SOLO POR HOY 2X1' o 'PAGÁS AL RECIBIR'.",
        "estructura_visual": "Sensación de urgencia y autenticidad física, sticker de oferta contrastante, llamada a pedir antes de que se agote."
    },
    {
        "concepto_key": "C5_ANTI_FALSIFICACION",
        "canonico_id": "CN10_SELLO_SEGURIDAD",
        "rol_embudo": "BOFU",
        "dispositivo": "Primer plano del sello de seguridad y código de autenticidad para despejar desconfianza.",
        "estructura_visual": "Estilo de alerta informativa: 'Exigí el producto original sellado', frasco nítido, badge oficial."
    }
]


def leer_productos():
    prods = {}
    with io.open(DIM_PROD, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pk = r.get("producto_key", "").strip()
            if pk:
                prods[pk] = r
    return prods


def generar_fase2(producto_key, angulo_ganador=None):
    prods = leer_productos()
    if producto_key not in prods:
        print(f"Error: Producto '{producto_key}' no existe en _DIM_PRODUCTOS.csv.")
        return 1

    prod = prods[producto_key]
    cuenta = prod.get("cuenta_alias") or "GTR0"
    page_id = prod.get("page_id") or ""
    be_q = float(prod.get("cpa_be_q") or 90.0)
    obj_q = float(prod.get("cpa_base_q") or 30.8)
    slug = prod.get("slug_carpeta") or producto_key

    # Si no se indica ángulo ganador, buscar el mejor en _DECISIONES.json
    if not angulo_ganador:
        dec_file = os.path.join(PROD, "_DECISIONES.json")
        if os.path.exists(dec_file):
            try:
                data = json.load(io.open(dec_file, encoding="utf-8"))
                for pr in data.get("productos", []):
                    if pr.get("producto_key") == producto_key:
                        for c in pr.get("celdas", []):
                            if c.get("estado") == "ESCALAR":
                                angulo_ganador = c.get("celda")
                                break
            except Exception:
                pass

    if not angulo_ganador:
        angulo_ganador = "ANGULO_GANADOR"

    hoy_str = datetime.date.today().strftime("%Y%m%d")
    manana_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    nombre_campana = f"{cuenta}_{producto_key}_F2-CONCEPTOS_{hoy_str}"
    presupuesto_conjunto = 5.00

    plan_f2 = {
        "schema": "fase2_lean/1",
        "producto_key": producto_key,
        "fase": 2,
        "angulo_ganador": angulo_ganador,
        "fecha_creacion": datetime.date.today().isoformat(),
        "fecha_lanzamiento": f"{manana_str} 04:00 AM",
        "cuenta": cuenta,
        "page_id": page_id,
        "campana": {
            "nombre": nombre_campana,
            "objetivo": "OUTCOME_TRAFFIC (Conversaciones WhatsApp)",
            "tipo_presupuesto": "ABO (Presupuesto a nivel de conjunto)",
            "presupuesto_total_dia_usd": round(presupuesto_conjunto * len(CONCEPTOS_CANONICOS), 2),
        },
        "conjuntos": []
    }

    print("=" * 85)
    print(f" 🎯 PLAN FASE 2 LEAN — VALIDACIÓN RÁPIDA DE CONCEPTOS: {producto_key}")
    print(f" Ángulo Ganador Fijo: {angulo_ganador} | Cuenta: {cuenta} | Campaña: 1 Campaña ABO")
    print(f" Programación: Mañana {manana_str} a las 04:00 AM")
    print("=" * 85)
    print(f"\nCAMPAÑA: {nombre_campana}")
    print(f"Tipo: ABO | Presupuesto: ${presupuesto_conjunto:.2f}/día por conjunto (${presupuesto_conjunto*len(CONCEPTOS_CANONICOS):.2f}/día total)\n")

    for i, conc in enumerate(CONCEPTOS_CANONICOS, 1):
        nombre_conjunto = f"{cuenta}_{producto_key}_{angulo_ganador}_C{i}_{conc['concepto_key'].split('_')[1]}"
        nombre_anuncio = f"{angulo_ganador}_IMG_C{i} ~ {producto_key}|{angulo_ganador}|{conc['concepto_key']}.{conc['canonico_id']}|NC2|2X1|BOTv1"

        conj_data = {
            "posicion": i,
            "nombre_conjunto": nombre_conjunto,
            "presupuesto_usd": presupuesto_conjunto,
            "concepto_key": conc["concepto_key"],
            "canonico_id": conc["canonico_id"],
            "rol_embudo": conc["rol_embudo"],
            "nombre_anuncio": nombre_anuncio,
            "dispositivo_visual": conc["dispositivo"],
            "prompt_sugerido": f"Creativo 1080x1080 px para Meta Ads, producto {producto_key}. Ángulo '{angulo_ganador}'. Dispositivo: {conc['dispositivo']} Estructura: {conc['estructura_visual']} Look profesional, sin parecer IA, badges de 'Envío Gratis' y 'Pagás al recibir'."
        }
        plan_f2["conjuntos"].append(conj_data)

        print(f"CONJUNTO {i}: {nombre_conjunto} (${presupuesto_conjunto:.2f}/día)")
        print(f"  Concepto:  {conc['concepto_key']} ({conc['canonico_id']}) — Rol: {conc['rol_embudo']}")
        print(f"  Idea visual: {conc['dispositivo']}")
        print(f"  Anuncio:   {nombre_anuncio}")
        print(f"  Prompt:    {conj_data['prompt_sugerido'][:110]}...")
        print("-" * 85)

    # Guardar en JSON en la carpeta del producto
    ruta_salida = os.path.join(PROD, slug, "_PLAN_FASE2.json")
    with io.open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(plan_f2, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Plan de Fase 2 guardado en: {ruta_salida}")
    print("REGLA DE DECISIÓN A 72H:")
    print("  - Cualquier concepto con CPA <= CPA Objetivo (Q%.2f) -> GANADOR -> Escalar a Fase 3 (CBO)." % obj_q)
    print("  - Cualquier concepto que gaste 1x Break-Even (Q%.2f) con 0 ventas -> APAGAR." % be_q)
    print("=" * 85)
    return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: python Ads/_TOOLS/gen_fase2_lean.py <PRODUCTO_KEY> [<ANGULO_GANADOR>]")
        print("Ejemplo: python Ads/_TOOLS/gen_fase2_lean.py TINNIDROP ACCESIBILIDAD_MEDICO")
        return 1
    pk = sys.argv[1]
    ang = sys.argv[2] if len(sys.argv) > 2 else None
    return generar_fase2(pk, ang)


if __name__ == "__main__":
    sys.exit(main())
