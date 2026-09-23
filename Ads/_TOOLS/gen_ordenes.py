#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ordenes.py — Generador de órdenes literales para Meta desde PRODUCTOS/_DECISIONES.json.

POR QUE EXISTE (Hito 5, 19-sep-2026):
------------------------------------
_DECISIONES.json trae la recomendación en prosa ("APAGAR: Gastó Q95...", "ESCALAR (Calet)...").
Este script traduce esas decisiones a órdenes LITERALES de Meta para el operador y el runner:
  - Entidad de Meta (id, nombre, nivel: adset o campaign)
  - Acción: ads_update_entity con fields: {"status": "PAUSED"} o {"daily_budget": ...}
  - Valor antes -> valor después
  - El porqué (CPA observado, IC 95%, break-even, ventas faltantes) y el rezago de la data
  - SEGUIR_MIDIENDO no genera orden a Meta (mantiene y mide).
  - RENOVAR alerta fatiga y rotación de concepto en F2 sin apagar en Meta.
  - Si falta el ID de una entidad en Meta para una orden, BLOQUEA y nombra al dueño (invariante 4).
  - Si la entidad ya está en el estado deseado en Meta, marca omitir: true (idempotencia).

USO:
    python Ads/_TOOLS/gen_ordenes.py
    python Ads/_TOOLS/gen_ordenes.py --producto TINNIDROP
    python Ads/_TOOLS/gen_ordenes.py --producto TINNIDROP --snapshot Ads/_INGESTA/META/snapshot_GTR7.json --json
    python Ads/_TOOLS/gen_ordenes.py --json
"""
import argparse
import csv
import io
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
INGESTA_META = os.path.join(BASE, "Ads", "_INGESTA", "META")

P = lambda *a: os.path.join(PROD, *a)


def cargar_json(ruta):
    if not os.path.exists(ruta):
        return None
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_snapshot(ruta):
    """Devuelve dict con objetos indexados por id y por nombre."""
    if not ruta or not os.path.exists(ruta):
        return {}
    with io.open(ruta, encoding="utf-8") as fh:
        d = json.load(fh)
    objetos = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
    if isinstance(objetos, str):
        try:
            objetos = json.loads(objetos)
        except Exception:
            objetos = []
    out = {}
    for o in objetos:
        nombre = (o.get("name") or "").strip()
        oid = (o.get("id") or "").strip()
        nivel = (o.get("nivel") or o.get("entity_type") or "").strip().lower()
        status = (o.get("status") or o.get("effective_status") or "").strip().upper()
        daily_budget = o.get("daily_budget")
        item = {
            "id": oid,
            "name": nombre,
            "nivel": nivel,
            "status": status,
            "daily_budget": daily_budget,
        }
        if nombre:
            out[nombre] = item
        if oid:
            out[oid] = item
    return out


def cargar_dim_conjuntos():
    """Mapea (producto_key, angulo_key) -> lista de filas de _DIM_CONJUNTOS.csv."""
    ruta = P("_DIM_CONJUNTOS.csv")
    if not os.path.exists(ruta):
        return {}
    resultado = {}
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            pk = (r.get("producto_key") or "").strip()
            ak = (r.get("angulo_key") or "").strip()
            if not pk or not ak:
                continue
            clave = (pk, ak)
            if clave not in resultado:
                resultado[clave] = []
            resultado[clave].append(r)
    return resultado


def cargar_dim_productos():
    ruta = P("_DIM_PRODUCTOS.csv")
    if not os.path.exists(ruta):
        return {}
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return {
            (r.get("producto_key") or "").strip(): r
            for r in csv.DictReader(fh)
            if r.get("producto_key")
        }


def cargar_pendientes_registro():
    """Anuncios NUESTROS de Meta (`producto_key` clasificado, via _DIM_CONJUNTOS.csv o via el
    patron de nombre de PROD_KEY — ver producto_de() en ingerir_meta.py) cuyo conjunto todavia
    no tiene fila de `angulo_key` en _DIM_CONJUNTOS.csv.

    NO confundir con un anuncio AJENO: la cuenta GTR7 es compartida con clientes de agencia
    (DR MELAXIN, MAG, TRULY X1 GT, OLD SCHOOL VENTAS — ver el docstring FILTRADO de
    bajar_meta_insights.py). Un ajeno no clasifica ningun producto_key (producto_de() devuelve
    SIN_CLASIFICAR) y bajar_meta_insights.py ya lo excluye antes de que llegue aca — no aparece
    en `_FACT_ENTREGA_ANUNCIO.csv` y por lo tanto tampoco en esta lista. Lo que SI aparece aca es
    NUESTRO, ya gasta plata, y solo le falta la fila de registro.

    Quien cierra el pendiente: ETAPA-6 (el planificador de lanzamiento, dueño unico de
    _DIM_CONJUNTOS.csv y de la CONVENCION DE NOMBRES) da de alta la fila que falta con un
    escritor CSV real (invariante 11) — nunca a mano.
    """
    ruta = P("_FACT_ENTREGA_ANUNCIO.csv")
    if not os.path.exists(ruta):
        return []
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ingerir_meta as im  # un solo dueño de producto_de()/leer_dim()/canonico(), no se copia

    _, con_angulo = im.leer_dim()
    agg = {}
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            pk = (r.get("producto_key") or "").strip()
            conj = (r.get("conjunto") or "").strip()
            if not pk or pk == "SIN_CLASIFICAR" or not conj:
                continue
            if conj in con_angulo or im.canonico(conj) in con_angulo:
                continue   # ya tiene angulo_key declarado en _DIM_CONJUNTOS.csv
            clave = (r.get("cuenta_alias") or "", r.get("campana") or "", conj)
            a = agg.setdefault(clave, {
                "cuenta_alias": r.get("cuenta_alias") or "",
                "campana": r.get("campana") or "",
                "conjunto": conj,
                "producto_key": pk,
                "spend_usd": 0.0,
                "anuncios": 0,
                "lo_produce": "ETAPA-6 / _DIM_CONJUNTOS.csv",
            })
            try:
                a["spend_usd"] += float(r.get("spend_usd") or 0)
            except (TypeError, ValueError):
                pass
            a["anuncios"] += 1
    salida = list(agg.values())
    for a in salida:
        a["spend_usd"] = round(a["spend_usd"], 2)
    salida.sort(key=lambda x: -x["spend_usd"])
    return salida


def cargar_parametros():
    p = {"surfing_pct": 20.0}
    ruta = P("_PARAMETROS_DECISION.csv")
    if os.path.exists(ruta):
        with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                k = (r.get("parametro") or "").strip()
                v = (r.get("valor") or "").strip()
                if k == "surfing_pct":
                    try:
                        p[k] = float(v)
                    except ValueError:
                        pass
    return p


def generar_frase_simple(estado, angulo_nombre, cpa_real, obj_q, be_q, faltan_ventas, surfing_pct):
    if estado == "ESCALAR":
        return f"Subir {surfing_pct:.0f}% al presupuesto de {angulo_nombre}"
    elif estado == "PAUSAR":
        return f"Pausar conjunto de {angulo_nombre}"
    elif estado == "RENOVAR":
        return f"Renovar creativo para {angulo_nombre} (rotar concepto en F2)"
    elif estado == "SEGUIR_MIDIENDO":
        if faltan_ventas:
            return f"Mantener presupuesto de {angulo_nombre}: faltan ~{faltan_ventas} ventas para decidir"
        return f"Mantener presupuesto de {angulo_nombre} y seguir midiendo"
    return f"Acción {estado} para {angulo_nombre}"


def generar_ordenes(producto_filtro=None, ruta_decisiones=None, ruta_snapshot=None):
    dec_path = ruta_decisiones or P("_DECISIONES.json")
    data_dec = cargar_json(dec_path)
    if not data_dec:
        return {
            "schema": "ordenes/1",
            "error": f"No existe {dec_path}",
            "llamadas": [],
            "bloqueantes": [{"falta": f"archivo {dec_path}", "lo_produce": "decidir.py / gen_decisiones.py", "ambito": "decisiones"}],
            "avisos": [],
            "pendientes_registro": [],
        }

    rezago_dias = data_dec.get("rezago_dias", 0)
    # g07-cimientos T2 (22-sep-2026): un dbt build roto quedaba solo en stdout de
    # gen_decisiones.py. Ahora viaja en _DECISIONES.json (capa_analitica) y de aca sube al
    # header de órdenes / la app, que es donde el operador de verdad mira.
    capa_analitica = data_dec.get("capa_analitica") or {"estado": "DESCONOCIDO", "detalle": ""}
    dim_conjuntos = cargar_dim_conjuntos()
    dim_productos = cargar_dim_productos()
    params = cargar_parametros()
    surfing_pct = params.get("surfing_pct", 20.0)

    # Cargar snapshot si se especificó, o buscar en INGESTA_META
    snapshot_meta = {}
    if ruta_snapshot and os.path.exists(ruta_snapshot):
        snapshot_meta = cargar_snapshot(ruta_snapshot)
    else:
        # Intentar cargar snapshots de cuentas conocidas en INGESTA_META
        if os.path.isdir(INGESTA_META):
            for arch in os.listdir(INGESTA_META):
                if arch.startswith("snapshot_") and arch.endswith(".json"):
                    sub_snap = cargar_snapshot(os.path.join(INGESTA_META, arch))
                    snapshot_meta.update(sub_snap)

    llamadas = []
    ordenes_resumen = []
    bloqueantes = []
    avisos = []
    if capa_analitica.get("estado") == "FALLO":
        avisos.append("CAPA ANALITICA (dbt) FALLO: %s — el motor esta leyendo los CSV "
                       "directamente." % capa_analitica.get("detalle", ""))
    pendientes_registro = cargar_pendientes_registro()
    if pendientes_registro:
        gasto_pend = sum(p["spend_usd"] for p in pendientes_registro)
        avisos.append(
            "%d conjunto(s) NUESTRO(S) sin registrar en _DIM_CONJUNTOS.csv ($%.2f de gasto "
            "sin angulo_key, ya contado a nivel producto): %s — lo produce ETAPA-6."
            % (len(pendientes_registro), gasto_pend,
               ", ".join(p["conjunto"] for p in pendientes_registro[:5]))
        )
    num_llamada = 1

    productos_data = data_dec.get("productos", [])
    if producto_filtro:
        productos_data = [p for p in productos_data if p.get("producto_key") == producto_filtro]

    for p in productos_data:
        pk = p.get("producto_key")
        be_q = p.get("break_even_q")
        obj_q = p.get("cpa_objetivo_q")
        fase = p.get("fase_vigente", "F1")
        info_prod = dim_productos.get(pk, {})
        campaign_id_prod = (info_prod.get("campaign_id") or "").strip()

        for celda in p.get("celdas", []):
            ak = celda.get("celda")
            estado = celda.get("estado")
            accion_codigo = celda.get("accion_codigo")
            bloqueo_fase = celda.get("bloqueo_fase")
            ejecutable = celda.get("ejecutable", True)
            cpa_real = celda.get("cpa_real_q")
            ic = celda.get("ic")
            faltan_ventas = celda.get("faltan_ventas")
            cierre_pct = celda.get("cierre_pct")
            ventas_actual = celda.get("ventas_actual")
            ventas_necesarias = celda.get("ventas_necesarias")

            # Buscar conjuntos asociados a este ángulo
            filas_conj = dim_conjuntos.get((pk, ak), [])
            nombres_conjuntos = [r.get("conjunto_meta") for r in filas_conj if r.get("conjunto_meta")]
            angulo_nombre = filas_conj[0].get("angulo_nombre") if filas_conj else ak

            frase = generar_frase_simple(estado, angulo_nombre, cpa_real, obj_q, be_q, faltan_ventas, surfing_pct)

            orden_item = {
                "producto_key": pk,
                "angulo_key": ak,
                "angulo_nombre": angulo_nombre,
                "estado": estado,
                "accion_codigo": accion_codigo,
                "frase_simple": frase,
                "por_que": {
                    "frase": frase,
                    "cpa_real_q": cpa_real,
                    "ic": ic,
                    "break_even_q": be_q,
                    "cpa_objetivo_q": obj_q,
                    "faltan_ventas": faltan_ventas,
                    "rezago_dias": rezago_dias,
                    # Cierre real (mensajes -> ventas) tal cual lo calcula decidir.py. La meta
                    # 15-20% (UMBRAL_CIERRE_MINIMO_BOT, benchmark no gate) viaja en
                    # `parametros_motor` (_PARAMETROS_DECISION.csv), no acá: un solo dato, un dueño.
                    "cierre_pct": cierre_pct,
                    # Umbral que decidir.py REALMENTE aplicó en esta celda (ventas de la ventana
                    # vs. las que hacen falta para resolver el IC). None cuando el motor no
                    # proyectó ventana en este estado — la app no dibuja la barra sin ambos.
                    "ventas_actual": ventas_actual,
                    "ventas_necesarias": ventas_necesarias,
                },
                "bloqueo_fase": bloqueo_fase,
                "ejecutable": ejecutable,
                "conjuntos": nombres_conjuntos,
            }
            ordenes_resumen.append(orden_item)

            # SEGUIR_MIDIENDO y RENOVAR no generan orden de escritura a Meta
            if estado in ("SEGUIR_MIDIENDO", "RENOVAR"):
                continue

            # Si la celda está bloqueada por fase o no es ejecutable
            if not ejecutable or bloqueo_fase:
                avisos.append(f"{pk} - {ak}: no se genera orden a Meta ({bloqueo_fase or 'bloqueado'}).")
                continue

            if estado == "PAUSAR":
                # Cada conjunto activo del ángulo se pausa
                if not nombres_conjuntos:
                    bloqueantes.append({
                        "falta": f"No hay conjuntos asociados a '{ak}' para '{pk}' en _DIM_CONJUNTOS.csv",
                        "lo_produce": "ETAPA-6 / _DIM_CONJUNTOS.csv",
                        "ambito": "ordenes",
                    })
                    continue

                for c_nombre in set(nombres_conjuntos):
                    meta_obj = snapshot_meta.get(c_nombre)
                    if not meta_obj:
                        bloqueantes.append({
                            "falta": f"no existe id de Meta para el conjunto '{c_nombre}' (ángulo '{ak}') de '{pk}'",
                            "lo_produce": "verificar_publicacion.py / snapshot Meta",
                            "ambito": "ordenes",
                        })
                        continue

                    cid = meta_obj.get("id")
                    status_actual = meta_obj.get("status", "ACTIVE")
                    ya_pausado = (status_actual == "PAUSED")

                    llamadas.append({
                        "n": num_llamada,
                        "tool": "ads_update_entity",
                        "args": {
                            "entity_id": cid,
                            "fields": {"status": "PAUSED"},
                        },
                        "entidad": {
                            "id": cid,
                            "nombre": c_nombre,
                            "nivel": meta_obj.get("nivel", "adset"),
                        },
                        "accion": "PAUSAR",
                        "antes": status_actual,
                        "despues": "PAUSED",
                        "omitir": ya_pausado,
                        "id_existente": cid if ya_pausado else None,
                        "por_que": orden_item["por_que"],
                    })
                    num_llamada += 1

            elif estado == "ESCALAR":
                # Subir daily_budget
                if not nombres_conjuntos:
                    bloqueantes.append({
                        "falta": f"No hay conjuntos asociados a '{ak}' para '{pk}' en _DIM_CONJUNTOS.csv",
                        "lo_produce": "ETAPA-6 / _DIM_CONJUNTOS.csv",
                        "ambito": "ordenes",
                    })
                    continue

                for c_nombre in set(nombres_conjuntos):
                    meta_obj = snapshot_meta.get(c_nombre)
                    if not meta_obj:
                        bloqueantes.append({
                            "falta": f"no existe id de Meta para el conjunto '{c_nombre}' (ángulo '{ak}') de '{pk}'",
                            "lo_produce": "verificar_publicacion.py / snapshot Meta",
                            "ambito": "ordenes",
                        })
                        continue

                    cid = meta_obj.get("id")
                    status_actual = meta_obj.get("status", "ACTIVE")
                    budget_actual = meta_obj.get("daily_budget")

                    # Si el snapshot no tiene daily_budget, default a 2.99 USD o su valor actual
                    try:
                        b_val = float(budget_actual) if budget_actual else 2.99
                    except (ValueError, TypeError):
                        b_val = 2.99

                    nuevo_budget = round(b_val * (1.0 + surfing_pct / 100.0), 2)
                    ya_escalado = (budget_actual is not None and abs(float(budget_actual) - nuevo_budget) < 0.01)

                    llamadas.append({
                        "n": num_llamada,
                        "tool": "ads_update_entity",
                        "args": {
                            "entity_id": cid,
                            "fields": {"daily_budget": nuevo_budget},
                        },
                        "entidad": {
                            "id": cid,
                            "nombre": c_nombre,
                            "nivel": meta_obj.get("nivel", "adset"),
                        },
                        "accion": "ESCALAR",
                        "antes": f"{b_val:.2f}",
                        "despues": f"{nuevo_budget:.2f}",
                        "omitir": ya_escalado,
                        "id_existente": cid if ya_escalado else None,
                        "por_que": orden_item["por_que"],
                    })
                    num_llamada += 1

    manifiesto = {
        "producto": producto_filtro or "TODOS",
        "total_ordenes": len(ordenes_resumen),
        "total_llamadas_meta": len(llamadas),
        "rezago_dias": rezago_dias,
    }

    resultado = {
        "schema": "ordenes/1",
        "producto": producto_filtro or "TODOS",
        "rezago_dias": rezago_dias,
        "capa_analitica": capa_analitica,
        "pendientes_registro": pendientes_registro,
        "ordenes": ordenes_resumen,
        "llamadas": llamadas,
        "manifiesto": manifiesto,
        "bloqueantes": bloqueantes,
        "avisos": avisos,
    }
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Genera órdenes literales desde _DECISIONES.json")
    parser.add_argument("--producto", help="Filtrar por producto_key")
    parser.add_argument("--decisiones", help="Ruta alternativa a _DECISIONES.json")
    parser.add_argument("--snapshot", help="Ruta al snapshot de Meta")
    parser.add_argument("--salida", help="Ruta para guardar el JSON generado")
    parser.add_argument("--json", action="store_true", help="Imprimir salida como JSON")
    args = parser.parse_args()

    res = generar_ordenes(
        producto_filtro=args.producto,
        ruta_decisiones=args.decisiones,
        ruta_snapshot=args.snapshot,
    )

    if args.salida:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 1 if res.get("bloqueantes") else 0

    print("=" * 78)
    print(f"ÓRDENES DEL MOTOR  ·  REZAGO: {res.get('rezago_dias', 0)} DÍAS")
    print("=" * 78)
    if res.get("rezago_dias", 0) > 2:
        print(f"  [!] ALERTA: Data con {res['rezago_dias']} días de rezago. Revisar antes de ejecutar.")
    print(f"  Total órdenes analizadas : {len(res.get('ordenes', []))}")
    print(f"  Total llamadas a Meta     : {len(res.get('llamadas', []))}")
    print()

    for ord_item in res.get("ordenes", []):
        print(f"  [{ord_item['estado']}] {ord_item['producto_key']} · {ord_item['frase_simple']}")
        if ord_item.get("bloqueo_fase"):
            print(f"      Bloqueo de fase: {ord_item['bloqueo_fase']}")

    if res.get("bloqueantes"):
        print()
        print(f"  BLOQUEANTES ({len(res['bloqueantes'])}):")
        for b in res["bloqueantes"]:
            print(f"    X {b['falta']}")
            print(f"      lo produce: {b['lo_produce']}")
        return 1

    if res.get("avisos"):
        print()
        print(f"  AVISOS ({len(res['avisos'])}):")
        for av in res["avisos"]:
            print(f"    ! {av}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
