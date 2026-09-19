# -*- coding: utf-8 -*-
"""gen_orden_activacion.py — ORDEN DE ACTIVACION FASE 1 EN META (4 AM, Invariante 7).

POR QUE EXISTE (2026-09-18)
--------------------------
La activación de campañas a las 4:00 AM es el paso que pone en marcha los anuncios en Meta
tras haber sido creados en PAUSA por `publicar-meta` (`gen_publicacion.py`).

QUE HACE Y QUE NO HACE
----------------------
NO llama a Meta. NO gasta. NO activa directamente.
Lee el plan, `_DIM_PRODUCTOS.csv`, `_DIM_CREATIVOS.csv` y el snapshot fresco de Meta,
y emite la orden LITERAL para el operador y el runner (`wf_meta`):

    llamadas[]    la llamada literal `ads_activate_entity` con `args: {"entity_id": campaign_id}`
    manifiesto{}  el estado esperado en Meta (la campaña en estado ACTIVE)

Si la campaña ya está ACTIVE en Meta (según el snapshot), la llamada se marca `omitir: true`
con `id_existente` para garantizar IDEMPOTENCIA.

Si falta un dato (campaign_id, ad_ids de creativos, cuenta), emite un BLOQUEANTE
nombrando a su dueño doctrinal y sale con exit 1 (Invariante 4 de CLAUDE.md).

INVARIANTE 7
------------
La activación se programa para las 04:00 AM del día SIGUIENTE (nunca hoy).
La hora sale de `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` (CALENDARIO_ESCALADO.md 1.7.2).

USO
    python Ads/_TOOLS/gen_orden_activacion.py --producto TINNIDROP --fase 1
    python Ads/_TOOLS/gen_orden_activacion.py --producto TINNIDROP --fase 1 --cuenta GTR7
    python Ads/_TOOLS/gen_orden_activacion.py --producto TINNIDROP --fase 1 --snapshot Ads/_INGESTA/META/snapshot_GTR7.json --json
"""
import csv
import datetime
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
P = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def flag(f):
    return f in sys.argv


def cargar_snapshot(ruta):
    """Devuelve dict con objetos indexados por nombre y por id."""
    with io.open(ruta, encoding="utf-8") as fh:
        d = json.load(fh)
    objetos = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
    if isinstance(objetos, str):
        objetos = json.loads(objetos)
    out = {}
    for o in objetos:
        nombre = (o.get("name") or "").strip()
        oid = (o.get("id") or "").strip()
        nivel = o.get("nivel") or o.get("entity_type") or ""
        status = o.get("status") or o.get("effective_status") or ""
        item = {"id": oid, "name": nombre, "nivel": nivel, "status": status}
        if nombre:
            out[nombre] = item
        if oid:
            out[oid] = item
    return out


def main():
    pk = arg("--producto")
    fase_str = arg("--fase", "1")
    cuenta_arg = arg("--cuenta")
    snap = arg("--snapshot")
    ruta_pl = arg("--plan")
    salida = arg("--salida")
    como_json = flag("--json")

    if not pk or not fase_str:
        print(__doc__)
        return 2

    try:
        fase = int(fase_str)
    except ValueError:
        print("ERROR: --fase debe ser un número entero.")
        return 2

    bloqueantes = []
    avisos = []

    # 1. Producto en _DIM_PRODUCTOS.csv
    dim_prod_path = P("_DIM_PRODUCTOS.csv")
    productos = {}
    if os.path.exists(dim_prod_path):
        with io.open(dim_prod_path, encoding="utf-8-sig", newline="") as fh:
            productos = {r["producto_key"]: r for r in csv.DictReader(fh) if r.get("producto_key")}
    else:
        bloqueantes.append({
            "falta": f"no existe {dim_prod_path}",
            "lo_produce": "alta_producto.py",
            "ambito": "paquete",
        })

    fila_prod = productos.get(pk)
    if not fila_prod:
        bloqueantes.append({
            "falta": f"'{pk}' no tiene fila en _DIM_PRODUCTOS.csv",
            "lo_produce": "alta_producto.py",
            "ambito": "paquete",
        })

    # 2. Cuenta publicitaria
    cuenta = (cuenta_arg or (fila_prod.get("cuenta_alias") if fila_prod else "") or "").strip()
    if not cuenta:
        bloqueantes.append({
            "falta": f"'{pk}' no tiene cuenta asignada en _DIM_PRODUCTOS.csv",
            "lo_produce": "producto.cargar_cuenta",
            "ambito": "publicacion",
            "clave": "cuenta",
        })

    # 3. Campaign ID
    campaign_id = (fila_prod.get("campaign_id") if fila_prod else "") or ""
    campaign_id = campaign_id.strip()

    # Si no está en _DIM_PRODUCTOS.csv, intentar ubicarla en el snapshot
    if (not campaign_id or campaign_id.upper() == "PENDIENTE") and snap and os.path.exists(snap):
        meta_objs = cargar_snapshot(snap)
        for _, info in meta_objs.items():
            if info.get("nivel") == "campaign" and pk in info.get("name", "") and f"F{fase}" in info.get("name", ""):
                campaign_id = info.get("id", "")
                break

    if not campaign_id or campaign_id.upper() == "PENDIENTE":
        bloqueantes.append({
            "falta": f"falta campaign_id para '{pk}' en _DIM_PRODUCTOS.csv",
            "lo_produce": "verificar_publicacion.py / alta_producto.py",
            "ambito": "paquete",
        })

    # 4. Creativos y ad_ids
    dim_creativos_path = P("_DIM_CREATIVOS.csv")
    creativos = []
    if os.path.exists(dim_creativos_path):
        with io.open(dim_creativos_path, encoding="utf-8-sig", newline="") as fh:
            creativos = [r for r in csv.DictReader(fh) if r.get("producto_key") == pk]

    if not creativos:
        bloqueantes.append({
            "falta": f"el producto '{pk}' no tiene creativos en _DIM_CREATIVOS.csv",
            "lo_produce": "etapa-9 / gen_piezas",
            "ambito": "paquete",
        })
    else:
        con_ad_id = [
            r for r in creativos
            if (r.get("ad_id") or "").strip() and (r.get("ad_id") or "").strip().upper() != "PENDIENTE"
        ]
        if not con_ad_id:
            bloqueantes.append({
                "falta": f"no hay creativos con ad_id para '{pk}' en _DIM_CREATIVOS.csv",
                "lo_produce": "verificar_publicacion.py",
                "ambito": "publicacion",
            })

    # 5. Snapshot e idempotencia
    ya_activa = False
    if snap and os.path.exists(snap):
        meta_objs = cargar_snapshot(snap)
        hit = None
        if campaign_id:
            hit = meta_objs.get(campaign_id)
        if not hit and pk:
            for _, info in meta_objs.items():
                if info.get("nivel") == "campaign" and pk in info.get("name", "") and f"F{fase}" in info.get("name", ""):
                    hit = info
                    break
        if hit:
            status = (hit.get("status") or "").upper()
            if status == "ACTIVE":
                ya_activa = True
        elif campaign_id:
            bloqueantes.append({
                "falta": f"la campaña '{campaign_id}' no existe en el snapshot de Meta",
                "lo_produce": "publicacion.paquete / publicar-meta",
                "ambito": "publicacion",
            })
    elif snap:
        avisos.append(f"--snapshot apunta a un archivo que no existe: {snap}. Sin snapshot no hay chequeo de idempotencia.")

    # 6. Invariante 7: Activación a las 4 AM del día siguiente
    hoy = datetime.date.today()
    fecha = hoy + datetime.timedelta(days=1)
    if ruta_pl and os.path.exists(ruta_pl):
        try:
            with io.open(ruta_pl, encoding="utf-8") as fh:
                pld = json.load(fh)
            f_plan_str = pld.get("fecha_lanzamiento") or pld.get("lanzamiento")
            if f_plan_str:
                d_plan = datetime.datetime.strptime(f_plan_str, "%Y-%m-%d").date()
                if d_plan > hoy:
                    fecha = d_plan
        except Exception:
            pass

    hora_lanz = "04:00"
    tz_offset = "-06:00"
    params_path = P("_PARAMETROS_PUBLICACION.csv")
    if os.path.exists(params_path):
        with io.open(params_path, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("fase") or "").strip() == str(fase):
                    hora_lanz = (r.get("hora_lanzamiento") or "04:00").strip()
                    tz_offset = (r.get("tz_offset") or "-06:00").strip()
                    break

    if fecha <= hoy:
        bloqueantes.append({
            "falta": f"lanzamiento {fecha} no es posterior a hoy ({hoy}). Invariante 7: siempre 4 AM del día SIGUIENTE, nunca el mismo día.",
            "lo_produce": "CLAUDE.md invariante 7",
            "ambito": "publicacion",
        })

    start_time = f"{fecha.isoformat()}T{hora_lanz}:00{tz_offset}"

    # 7. Construcción de llamadas y manifiesto
    llamadas = [
        {
            "n": 1,
            "tool": "ads_activate_entity",
            "args": {"entity_id": campaign_id},
            "omitir": ya_activa,
            "id_existente": campaign_id if ya_activa else None,
            "nota": "Activar campaña en Meta a las 4 AM (Invariante 7)."
                    + (" (Ya está ACTIVE)" if ya_activa else ""),
        }
    ]

    manifiesto = {
        "campana_id": campaign_id,
        "cuenta_alias": cuenta,
        "producto_key": pk,
        "fase": fase,
        "hora_lanzamiento": start_time,
        "evento": "LANZAMIENTO",
    }

    resultado = {
        "schema": "activacion/1",
        "producto": pk,
        "fase": fase,
        "cuenta_alias": cuenta,
        "campaign_id": campaign_id,
        "hora_activacion": start_time,
        "evento": "LANZAMIENTO",
        "llamadas": llamadas,
        "manifiesto": manifiesto,
        "bloqueantes": bloqueantes,
        "avisos": avisos,
    }

    if salida:
        os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
        with io.open(salida, "w", encoding="utf-8") as fh:
            json.dump(resultado, fh, ensure_ascii=False, indent=1)

    if como_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=1))
        return 1 if bloqueantes else 0

    print("=" * 78)
    print(f"ORDEN DE ACTIVACIÓN  ·  {pk}  ·  FASE {fase}  ·  {cuenta}")
    print("=" * 78)
    print(f"  campaña ID      {campaign_id}")
    print(f"  activación      {start_time} (Invariante 7: 4 AM)")
    print(f"  evento          LANZAMIENTO")
    print(f"  estado previo   {'ACTIVE (omitir llamada)' if ya_activa else 'PAUSED -> ACTIVE'}")
    print()
    if avisos:
        print("  AVISOS:")
        for a in avisos:
            print(f"    · {a}")
        print()
    if bloqueantes:
        print(f"  BLOQUEANTES ({len(bloqueantes)}) — NO ACTIVAR:")
        for b in bloqueantes:
            print(f"    X {b['falta']}")
            print(f"      lo produce: {b['lo_produce']}")
        print()
        return 1

    print("  Sin bloqueantes. Lista para aprobación del operador.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
