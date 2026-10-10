# -*- coding: utf-8 -*-
"""armar_prompts_fase2.py — Generador Automático de Lotes Creativos Multimodales para Fase 2.

QUE HACE:
1. Detecta automáticamente el ÁNGULO GANADOR desde PRODUCTOS/_DECISIONES.json (sin que el operador adivine).
2. Selecciona los 5 Blueprints Canónicos idóneos (vía seleccionar_canonicos.py).
3. Vincula para cada concepto:
   - La Imagen Base del competidor (Layout/Composición) desde Ads/_SWIPE/_IMG/
   - La Foto Real del producto desde Ads/MEDIA_[PRODUCTO]/
   - El JSON parametrizado con variables de dolor, precios en la moneda del mercado e ingredientes reales.
   - El Prompt Multimodal "Director de Arte" listo para pegar en ChatGPT / Gemini Pro.
4. NO escribe texto de bot: ese flujo es de etapa-5 (PRODUCTOS/[carpeta]/1_HACER_MANUAL.txt).

DE DONDE SALE CADA DATO (un dato, un dueno — este script ya no nombra ningun producto)
    precios                   PRODUCTOS/_DIM_PRECIOS.csv                       (nunca se inventan)
    packshot / envase         PRODUCTOS/_DIM_ENVASE.csv
    perfil y textos           PRODUCTOS/[carpeta]/_PERFIL_CREATIVO.json        (lo escribe la skill
                              generar-conceptos desde la investigacion del producto; el perfil es del
                              producto, los textos son por angulo en `textos_por_angulo`)
    mercado                   _DIM_PRODUCTOS.mercado -> _DIM_MERCADOS.csv, via mercado.py: pais, moneda,
                              simbolo y persona (voseo/tuteo) del prompt
    registro sanitario        DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md ([REG_MSPAS]/[REG_FDA] en GT,
                              [REG_INVIMA] en CO), leido por mercado.registro_de_perfil(). Sin numero
                              (INVIMA pendiente) BLOQUEA con dato=registro_sanitario: nunca se inventa ni
                              se cae al MSPAS.
Si falta cualquiera, BLOQUEA con el nombre de quien lo produce (invariante 4).

DUENO DE «QUE CANONICOS» (tandas): este script. Elige, con seleccionar_canonicos.py, los canonicos de
cada tanda EXCLUYENDO los que ya estan registrados en PRODUCTOS/_DIM_CREATIVOS.csv para ese
producto+angulo (lectura; jamas lo escribe), y respeta «un concepto_key no se repite mientras queden
sin usar» a traves de todas las tandas. etapa-9 registra EXACTAMENTE los canonicos que este script
devuelve (`canonicos` en el JSON / PAQUETE_CREATIVO_*.json); no elige otros. Cuantos faltan: la
estructura de FASE 2 (_PARAMETROS_PUBLICACION.csv: brazos A y B, como flujo.publicacion_num) menos las
filas del angulo en _DIM_CREATIVOS.csv. `--n` (default = lo que falta) nunca pasa de eso; con 0
faltantes sale en limpio sin escribir. Los archivos del angulo ACUMULAN las tandas (se fusionan por
canonico_id): el paquete que lee la app nunca pierde el prompt de una tanda anterior.
"""

import argparse
import contextlib
import os
import sys
import io
import csv
import json

for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))

import mercado as mc
import seleccionar_canonicos as sc

PROD_DIR = os.path.join(BASE, "PRODUCTOS")
SWIPE_DIR = os.path.join(BASE, "Ads", "_SWIPE")
DECISIONES_JSON = os.path.join(PROD_DIR, "_DECISIONES.json")


class Bloqueado(SystemExit):
    """Un BLOQUEANTE con el dato que lo causa. Sigue siendo un `SystemExit` con el mismo texto (la
    CLI sin `--json` se comporta igual); `dato` deja que el llamador diga QUE falta sin leer prosa:
    packshot | precio | perfil_creativo | producto | angulo | mercado | registro_sanitario."""

    def __init__(self, mensaje, dato):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.dato = dato


DIM_CREATIVOS = "_DIM_CREATIVOS.csv"
PARAMETROS_PUBLICACION = "_PARAMETROS_PUBLICACION.csv"
N_POR_DEFECTO = 5  # sin estructura de FASE 2 declarada: la tanda historica de este script


def _filas_csv(nombre):
    ruta = os.path.join(PROD_DIR, nombre)
    if not os.path.isfile(ruta):
        return None
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def conceptos_requeridos():
    """Cuantos conceptos pide la estructura de FASE 2, o None si no esta declarada. Misma cuenta que
    flujo.publicacion_num(env, "conceptos_fase2"): conjuntos x anuncios de los brazos A y B (C repite)."""
    filas = _filas_csv(PARAMETROS_PUBLICACION)
    if filas is None:
        return None
    total = 0
    for r in filas:
        if (r.get("estado") or "") != "VIGENTE" or (r.get("fase") or "") != "2":
            continue
        if (r.get("brazo") or "").upper() == "C":
            continue
        try:
            total += int(float(r.get("conjuntos") or 0)) * int(float(r.get("anuncios_por_conjunto") or 0))
        except ValueError:
            continue
    return total or None


def registrados_del_angulo(producto_key, angulo):
    """(filas, canonicos) de _DIM_CREATIVOS.csv para este producto+angulo, solo lectura. `filas` son TODAS
    las piezas registradas (cuentan para lo que falta); `canonicos` los que ya tienen canonico_id (no se repiten)."""
    filas = [r for r in (_filas_csv(DIM_CREATIVOS) or [])
             if (r.get("producto_key") or "").strip() == producto_key and (r.get("angulo_key") or "").strip() == angulo]
    canonicos = [r["canonico_id"].strip() for r in filas if (r.get("canonico_id") or "").strip()]
    return len(filas), canonicos


def cuantos_pedir(n_pedido, requeridos, n_registradas):
    """(n efectivo, aviso de tope). Default = lo que falta; --n nunca pasa de lo que falta."""
    if requeridos is None:
        return (N_POR_DEFECTO if n_pedido is None else n_pedido), ""
    faltan = max(0, requeridos - n_registradas)
    if n_pedido is None:
        return faltan, ""
    if n_pedido > faltan:
        return faltan, (f"Tope: se pidieron {n_pedido} pero la estructura de FASE 2 pide {requeridos} y el angulo "
                        f"ya tiene {n_registradas}: solo faltan {faltan}.")
    return n_pedido, ""


def orden_ganador(celda):
    """Llave de orden del ángulo que va PRIMERO a FASE 2: más ventas, y a igualdad, CPA real más
    bajo. Dueño único del criterio: lo usa `detectar_angulo_ganador` y `flujo.ranking_ganadores`
    (la cola de ganadores que muestra la pantalla de FASE 2)."""
    return (-(celda.get("ventas") or 0), celda.get("cpa_real_q") or 999)


def detectar_angulo_ganador(producto_key):
    """Lee _DECISIONES.json y extrae el ángulo con mejor volumen y CPA en estado ESCALAR."""
    if not os.path.exists(DECISIONES_JSON):
        return None, "No existe _DECISIONES.json"
    
    with io.open(DECISIONES_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
        
    prods = data.get("productos", [])
    p_data = next((p for p in prods if p["producto_key"].upper() == producto_key.upper()), None)
    if not p_data:
        return None, f"Producto {producto_key} no encontrado en decisiones"
        
    celdas = p_data.get("celdas", [])
    # Filtrar por ESCALAR
    escalables = [c for c in celdas if c.get("estado") == "ESCALAR"]
    if not escalables:
        # Fallback al que tenga más ventas
        escalables = sorted(celdas, key=lambda x: x.get("ventas", 0), reverse=True)
        if not escalables:
            return None, "No hay celdas registradas"
            
    # Ordenar por ventas descendente y CPA real ascendente
    ganador = sorted(escalables, key=orden_ganador)[0]
    return ganador["celda"], ganador


def leer_envase(producto_key):
    """Lee la identidad FISICA declarada del producto desde PRODUCTOS/_DIM_ENVASE.csv.

    POR QUE EXISTE (07-sep-2026): esta funcion antes se llamaba buscar_foto_producto() y
    devolvia el PRIMER archivo alfabetico de Ads/MEDIA_[PK]/, llamandolo "la foto limpia del
    producto". En MEDIA_TINNIDROP el primero alfabetico era TINNIDROP_R1_VIVIRCONESO.png, que
    NO es un packshot: es un ANUNCIO entero con el frasco VERDE y la marca SOUTH MOON. El
    prompt le ordenaba al modelo copiar "este envase real respetando su forma y etiqueta", asi
    que las 5 piezas de FASE 2 salieron verdes y de otra marca. El packshot se DECLARA, no se
    adivina: un dato, un dueno.
    """
    ruta = os.path.join(PROD_DIR, "_DIM_ENVASE.csv")
    if not os.path.isfile(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila.get("producto_key", "").strip() == producto_key:
                return fila
    return None


def leer_escalera(producto_key, perfil=None):
    """Arma los tiers con ANTES y AHORA desde PRODUCTOS/_DIM_PRECIOS.csv.

    POR QUE EXISTE (08-sep-2026): los precios estaban hardcodeados por producto dentro de este
    script, contra la regla 'un dato, un dueno'. Y el precio ANCLA ('antes Q...') no existia en
    ningun lado del sistema, asi que el modelo lo completaba solo: en TINNIDROP_F2_CN05 escribio
    'PRECIO NORMAL: Q299.00', que es nuestro precio de TRES frascos presentado como el precio
    normal de UNO. La oferta se declara, no se improvisa.
    """
    ruta = os.path.join(PROD_DIR, "_DIM_PRECIOS.csv")
    if not os.path.isfile(ruta):
        return None
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for x in csv.DictReader(f):
            if x.get("producto_key") == producto_key and x.get("estado") == "ACTIVO":
                filas.append(x)
    if not filas:
        return None
    filas.sort(key=lambda x: int(x["unidades"]))

    monto = (lambda v: mc.formatear_monto(v, perfil)) if perfil else (lambda v: f"Q{float(v):.0f}")
    tiers, etiquetas = {}, {1: "", 2: " (OFERTA MÁS ELEGIDA ⭐)", 3: " (Tratamiento Completo)"}
    for i, x in enumerate(filas[:3], start=1):
        u = int(x["unidades"])
        ahora = monto(x['precio_q'])
        antes = x.get("precio_antes_q", "").strip()
        txt = f"{u} Frasco{'s' if u > 1 else ''} por {ahora}"
        if antes:
            txt += f" (antes {monto(antes)})"
        tiers[f"TIER_{i}"] = txt + etiquetas.get(u, "")
    return tiers or None


def requerir_precios_reales(producto_key, perfil=None):
    """La escalera de precios REAL o BLOQUEO — nunca los precios de otro producto.

    Misma clase de bug que buscar_foto_producto() (07-sep): leer_escalera() ya existia
    desde el 08-sep para leer PRODUCTOS/_DIM_PRECIOS.csv, pero cuando devolvia None (sin
    fila ACTIVA para este producto) el llamador caia en silencio a un PRECIOS_GT
    hardcodeado — Q179/Q239/Q299 de TINNIDROP para cualquier producto sin fila propia, o
    Q199/Q299/Q399 de CLEARSTEM en la adaptacion de LucidBot. Invariante 4: si falta un
    input requerido, se detiene con el nombre de quien lo produce — nunca se asume."""
    precios = leer_escalera(producto_key, perfil)
    if not precios:
        raise Bloqueado(
            f"BLOQUEANTE: {producto_key} no tiene fila ACTIVA en PRODUCTOS/_DIM_PRECIOS.csv.\n"
            f"  Sin la escalera de precios real, no se generan los prompts: caer a los precios "
            f"de otro producto (TINNIDROP Q179/Q239/Q299) fue exactamente el bug que "
            f"leer_escalera() vino a cerrar el 08-sep-2026 — no se reintroduce por la puerta "
            f"de atras con un fallback hardcodeado.\n"
            f"  Agrega la fila de {producto_key} en PRODUCTOS/_DIM_PRECIOS.csv (unidades, "
            f"precio_q, precio_antes_q, estado=ACTIVO) antes de generar.",
            "precio",
        )
    return precios


def requerir_mercado(producto_key):
    """El perfil del MERCADO del producto (pais, moneda, simbolo, persona, registro) o BLOQUEO.

    Un producto sin `mercado` declarado no tiene un default GT: se detiene y se pide (invariante 4)."""
    try:
        return mc.perfil_de_producto(producto_key, BASE)
    except mc.MercadoError as e:
        raise Bloqueado(
            f"BLOQUEANTE: {producto_key} no tiene un mercado utilizable: {e}\n"
            f"  El mercado (GT o CO) lo declara el operador en la columna `mercado` de "
            f"PRODUCTOS/_DIM_PRODUCTOS.csv; sin el no se sabe el pais, la moneda ni el tono del prompt.",
            "mercado")


def requerir_registro(producto_key, perfil):
    """Los numeros de registro sanitario DEL MERCADO del producto o BLOQUEO. Nunca los de otro mercado."""
    try:
        return mc.registro_de_perfil(perfil, BASE)
    except mc.RegistroFaltante as e:
        nombre = ", ".join(e.claves) or e.regulador or "?"
        raise Bloqueado(
            f"BLOQUEANTE: falta el numero de registro sanitario {nombre} de {producto_key} "
            f"(mercado {perfil['pais']}).\n"
            f"  Pasale a Claude el numero de registro {nombre} y él lo deja cargado en "
            f"DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md. Sin ese numero no se generan los prompts: "
            f"no se inventa uno ni se usa el de otro mercado.\n"
            f"  ({e})",
            "registro_sanitario")
    except mc.MercadoError as e:
        raise Bloqueado(f"BLOQUEANTE: no se pudo leer el registro sanitario de {producto_key}: {e}",
                        "registro_sanitario")


def buscar_foto_producto(producto_key):
    """Devuelve la ruta absoluta del packshot DECLARADO. Falla ruidoso si no lo hay."""
    envase = leer_envase(producto_key)
    if not envase or not envase.get("packshot", "").strip():
        raise Bloqueado(
            f"BLOQUEANTE: {producto_key} no tiene packshot declarado en "
            f"PRODUCTOS/_DIM_ENVASE.csv.\n"
            f"  Agregale su fila (packshot, color_envase, marca_impresa) antes de generar.\n"
            f"  No se adivina agarrando un archivo de Ads/MEDIA_{producto_key}/: asi fue como "
            f"TINNIDROP heredo un frasco verde de otra marca.",
            "packshot",
        )
    ruta = os.path.join(BASE, envase["packshot"].replace("/", os.sep))
    if not os.path.isfile(ruta):
        raise Bloqueado(
            f"BLOQUEANTE: {producto_key} declara el packshot '{envase['packshot']}' "
            f"pero el archivo no existe en el disco.\n"
            f"  Ponelo ahi o corregi la fila de PRODUCTOS/_DIM_ENVASE.csv.",
            "packshot",
        )
    return ruta


PERFIL_CREATIVO = "_PERFIL_CREATIVO.json"
PRODUCTOR_PERFIL = "la skill generar-conceptos (PASO 1 arma el perfil, PASO 3 agrega los textos del angulo)"
# Los textos que el prompt usa si o si. PRODUCTO, DESCRIPTOR, SINTOMA_ANTES y RESULTADO_DESPUES
# viajan en variables_json pero el prompt no los pide: no se exigen.
TEXTOS_REQUERIDOS = ("HOOK_TITULAR", "SUB_HOOK", "ACTIVOS_CLAVE", "GARANTIAS", "CTA")


def carpeta_de(producto_key):
    """slug_carpeta desde _DIM_PRODUCTOS.csv. Invariante 10: la carpeta nunca se adivina por el nombre."""
    ruta = os.path.join(PROD_DIR, "_DIM_PRODUCTOS.csv")
    if os.path.exists(ruta):
        with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("producto_key") or "").strip() == producto_key:
                    return (r.get("slug_carpeta") or "").strip() or None
    return None


def cargar_perfil_creativo(producto_key):
    """PRODUCTOS/[carpeta]/_PERFIL_CREATIVO.json, o BLOQUEO con el nombre de quien lo produce.

    POR QUE EXISTE (16-sep-2026, defecto residual de la simulacion TURMERIC). Este script tenia
    el perfil de cada producto, el texto de sus creativos y el guion del bot ESCRITOS A MANO en
    el codigo: `if producto_key == "CLEARSTEM"`. Tres consecuencias medidas:
      · un producto nuevo caia en un `else` que le inventaba los INGREDIENTES ("Extractos
        botanicos certificados", "Absorcion rapida") en vez de leer la investigacion;
      · el mismo `else` asumia `resultado_visible_en_el_cuerpo = True`, lo contrario de la regla
        de su dueno (seleccionar_canonicos.py: lo no declarado es FALSO), y elegia mal las
        plantillas de creativo;
      · el guion de LucidBot estaba escrito para CLEARSTEM y se aplicaba a TODOS: el paquete real
        de TINNIDROP (un spray para el oido) saluda con "Vi que te interesó Clearstem para el
        acné hormonal".

    El dato ya tenia productor: la skill generar-conceptos lee 2_DATA_PRODUCTO.txt y arma el
    perfil (PASO 1) y los textos (PASO 3), pero los dejaba en un archivo temporal. Ahora los
    persiste aca y este script solo los LEE: el codigo no vuelve a nombrar un producto, y un
    producto nuevo no necesita que nadie toque Python. Es el camino a un sistema autonomo."""
    carpeta = carpeta_de(producto_key)
    if not carpeta:
        raise Bloqueado(
            f"BLOQUEANTE: {producto_key} no tiene slug_carpeta en PRODUCTOS/_DIM_PRODUCTOS.csv.\n"
            f"  La carpeta del producto se resuelve por el CSV, nunca por el nombre (invariante 10).",
            "producto")
    ruta = os.path.join(PROD_DIR, carpeta, PERFIL_CREATIVO)
    if not os.path.exists(ruta):
        raise Bloqueado(
            f"BLOQUEANTE: falta PRODUCTOS/{carpeta}/{PERFIL_CREATIVO}.\n"
            f"  Lo produce {PRODUCTOR_PERFIL}, leyendo la investigacion del producto.\n"
            f"  Sin el no se generan creativos: el codigo ya no inventa el perfil ni los textos.",
            "perfil_creativo")
    with io.open(ruta, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc.get("perfil"), dict):
        raise Bloqueado(
            f"BLOQUEANTE: PRODUCTOS/{carpeta}/{PERFIL_CREATIVO} no trae el bloque 'perfil'.\n"
            f"  Lo produce {PRODUCTOR_PERFIL}.",
            "perfil_creativo")
    return doc


def requerir_textos(perfil_creativo, producto_key, angulo):
    """Los textos del creativo PARA ESTE ANGULO, o BLOQUEO. Nunca un texto generico ni de otro angulo.

    El perfil (si el resultado se ve, si hay curva...) es del PRODUCTO. Los textos son de UN ANGULO:
    el hook de TINNIDROP ("¿cansado de gastar en consultas...?") es de ACCESIBILIDAD_MEDICO.
    Esquema `perfil_creativo/2`: los textos viven en `textos_por_angulo[ANGULO]["textos"]` y cada
    angulo tiene su entrada; generar para uno nunca lee ni toca la de otro. Si el angulo no tiene
    entrada, bloquea nombrando los angulos que si existen.
    Archivo de un solo angulo (sin `textos_por_angulo`): `angulo_key` + `textos` de primer nivel;
    si el angulo ganador es otro, bloquea."""
    por_angulo = perfil_creativo.get("textos_por_angulo")
    if isinstance(por_angulo, dict):
        entrada = por_angulo.get(angulo)
        if not isinstance(entrada, dict):
            existentes = ", ".join(sorted(por_angulo)) or "(ninguno)"
            raise Bloqueado(
                f"BLOQUEANTE: el {PERFIL_CREATIVO} de {producto_key} no trae textos para el angulo '{angulo}'.\n"
                f"  Angulos con textos: {existentes}. Los textos de un angulo no sirven para otro.\n"
                f"  Los produce {PRODUCTOR_PERFIL}, para '{angulo}' (agrega su entrada en "
                f"textos_por_angulo sin tocar las demas).",
                "perfil_creativo")
        textos = entrada.get("textos") or {}
    else:
        declarado = (perfil_creativo.get("angulo_key") or "").strip()
        if declarado != angulo:
            raise Bloqueado(
                f"BLOQUEANTE: los textos del {PERFIL_CREATIVO} de {producto_key} son del angulo "
                f"'{declarado or '(sin declarar)'}' y se esta generando para '{angulo}'.\n"
                f"  Los textos de un angulo no sirven para otro. Los produce {PRODUCTOR_PERFIL}, para '{angulo}'.",
                "perfil_creativo")
        textos = perfil_creativo.get("textos") or {}
    faltan = [k for k in TEXTOS_REQUERIDOS if not textos.get(k)]
    if faltan:
        raise Bloqueado(
            f"BLOQUEANTE: el {PERFIL_CREATIVO} de {producto_key} no trae los textos: {', '.join(faltan)}.\n"
            f"  Los produce {PRODUCTOR_PERFIL}. No se rellenan con un texto generico: los "
            f"ingredientes salen de la investigacion, no de una plantilla.",
            "perfil_creativo")
    return textos


def obtener_perfil_producto(producto_key, angulo_ganador, perfil_creativo=None):
    """Construye el perfil para seleccionar_canonicos.py desde el perfil DECLARADO del producto.

    Parte de PLANTILLA_PERFIL, asi que lo que el archivo no declara queda en su valor por defecto
    (falso / 0): la regla de seleccionar_canonicos.py, en vez del optimismo que tenia el codigo."""
    doc = perfil_creativo or cargar_perfil_creativo(producto_key)
    p = dict(sc.PLANTILLA_PERFIL)
    p.update(doc["perfil"])
    p["producto"] = producto_key
    p["angulo_ganador"] = angulo_ganador
    return p


def _armar(producto_key, angulo_manual=None, n_pedido=None):
    # 0. Mercado del producto: pais, moneda, persona y registro salen de mercado.py, no del codigo.
    perfil_mercado = requerir_mercado(producto_key)
    tuteo = perfil_mercado["persona"] == "tuteo"

    # 1. Determinar ángulo ganador por data
    if angulo_manual:
        angulo = angulo_manual
        info_angulo = {"celda": angulo, "ventas": "manual", "cpa_real_q": 0}
    else:
        angulo, info_angulo = detectar_angulo_ganador(producto_key)
        if not angulo:
            raise Bloqueado(f"BLOQUEANTE: no se pudo detectar el ángulo ganador de {producto_key}: {info_angulo}",
                            "angulo")

    print("=" * 80)
    print(f" 🚀 FÁBRICA CREATIVA MULTIMODAL — FASE 2 LEAN")
    print(f" Producto: {producto_key}")
    print(f" Ángulo Ganador Coronado por Data: {angulo}")
    if isinstance(info_angulo, dict) and "ventas" in info_angulo:
        print(f" Desempeño Histórico: {info_angulo.get('ventas')} ventas | CPA Real: {mc.formatear_monto(info_angulo.get('cpa_real_q', 0), perfil_mercado, 2)}")
    print("=" * 80)

    # 1b. Cuantos faltan: la estructura de FASE 2 menos lo ya registrado. 0 = no hay nada que armar (no
    # se exigen precios ni perfil para decir eso, y no se escribe nada).
    requeridos = conceptos_requeridos()
    n_filas, ya = registrados_del_angulo(producto_key, angulo)
    n, aviso_tope = cuantos_pedir(n_pedido, requeridos, n_filas)
    if n <= 0:
        aviso = (f"No falta ningun concepto de {angulo}: la estructura de FASE 2 pide {requeridos} y ya hay "
                 f"{n_filas} registrados. No se armo nada.")
        print(aviso)
        return {"nada_que_hacer": True, "aviso": aviso, "angulo": angulo, "paquetes": [], "requeridos": requeridos,
                "registradas": n_filas, "solicitados": 0, "salida_txt": None, "salida_json": None,
                "adaptacion_bot": None, "descartados": [], "faltantes_de_aptos": 0, "repiten_concepto_key": []}

    # 2. Foto del producto
    foto_prod_path = buscar_foto_producto(producto_key)
    foto_prod_rel = os.path.relpath(foto_prod_path, BASE).replace("\\", "/")

    # 2b. Precios REALES — se bloquea ANTES de armar un solo paquete, no se descubre a
    # medio prompt ni se cae a los de otro producto (ver requerir_precios_reales).
    precios_reales = requerir_precios_reales(producto_key, perfil_mercado)
    registro = requerir_registro(producto_key, perfil_mercado)

    # 2c. Perfil y textos DECLARADOS del producto — mismo criterio que los precios: se bloquea
    # antes de escribir un solo archivo, nunca se cae a un texto generico ni al de otro producto.
    perfil_creativo = cargar_perfil_creativo(producto_key)
    textos = requerir_textos(perfil_creativo, producto_key, angulo)

    # 3. Selección de los 5 blueprints canónicos
    perfil = obtener_perfil_producto(producto_key, angulo, perfil_creativo)
    sel_res = sc.seleccionar(perfil, n=n, ya=ya)
    elegidos = sel_res["seleccion"]
    faltantes_de_aptos = n - len(elegidos)
    descartados = [{"canonico_id": d["canonico_id"], "motivo": d["motivo_descarte"]} for d in sel_res["descartados"]]
    avisos = [aviso_tope] if aviso_tope else []
    if faltantes_de_aptos > 0:
        avisos.append(
            f"Se pidieron {n} conceptos pero solo hay {len(elegidos)} canonicos aptos sin usar para {angulo}; "
            f"faltan {faltantes_de_aptos} y NO se repite ninguno ya registrado. Descartados por sus gates: "
            + "; ".join(f"{d['canonico_id']} ({d['motivo']})" for d in descartados) + ".")
    if sel_res["repiten_concepto_key"]:
        avisos.append("Repiten concepto_key (ya no quedaban sin usar): " + ", ".join(sel_res["repiten_concepto_key"]) + ".")
    for a in avisos:
        print("⚠️  " + a)

    # 4. Construir los 5 paquetes
    out_dir = os.path.join(BASE, "Ads", f"MEDIA_{producto_key}", f"FASE2_{angulo}")
    os.makedirs(out_dir, exist_ok=True)

    paquetes = []
    prompts_texto = []

    prompts_texto.append(f"══════════════════════════════════════════════════════════════════════════════")
    prompts_texto.append(f" PAQUETE CREATIVO MULTIMODAL — FASE 2 LEAN ({producto_key})")
    prompts_texto.append(f" ÁNGULO GANADOR CORONADO POR DATA: {angulo}")
    prompts_texto.append(f" FOTO DE TU PRODUCTO: {foto_prod_rel}")
    prompts_texto.append(f"══════════════════════════════════════════════════════════════════════════════\n")

    for idx, bp in enumerate(elegidos, 1):
        cid = bp["canonico_id"]
        ref_ficha = bp["ficha_referencia"]
        ficha_path = os.path.join(SWIPE_DIR, "_BLUEPRINTS", "FICHAS", f"{ref_ficha}.json")

        foto_base_rel = "No disponible"
        # El dispositivo es del CANONICO (neutro de producto). El de la ficha describe un anuncio de
        # otro nicho: solo es respaldo si el canonico no declara el suyo.
        dispositivo_txt = bp.get("dispositivo", "")
        if os.path.exists(ficha_path):
            with io.open(ficha_path, encoding="utf-8") as fh:
                f_data = json.load(fh)
                orig_file = f_data.get("origen", {}).get("archivo", "")
                foto_base_rel = os.path.join("Ads", "_SWIPE", orig_file).replace("\\", "/")
                if not dispositivo_txt:
                    dispositivo_txt = f_data.get("dispositivo_dominante", "")

        # Los textos DECLARADOS del producto (requerir_textos, validados al arrancar). Copia por
        # concepto: abajo se le agrega PRECIOS_GT y no debe filtrarse al siguiente.
        variables_adaptadas = dict(textos)

        # La escalera de precios es SIEMPRE la real (precios_reales, validada al arrancar
        # generar_paquete_multimodal): sale de _DIM_PRECIOS.csv y trae el precio ancla, para
        # que el modelo no invente el "antes". Ningun bloque de arriba la hardcodea ya.
        variables_adaptadas["PRECIOS_GT"] = precios_reales

        nombre_archivo = f"{producto_key}_F2_{cid.split('_')[0]}_{angulo[:12]}.png"

        # Prompt Multimodal listo para copiar en Gemini / ChatGPT
        prompt_ia = (
            f"Actúa como Director de Arte Senior y diseñador de anuncios de alta conversión para Meta Ads en {perfil_mercado['pais']}.\n"
            f"Te he adjuntado 2 imágenes:\n"
            f"  • IMAGEN 1 (Referencia visual): {foto_base_rel} -> Mantén EXACTAMENTE su distribución espacial, composición geométrica, encuadre de cámara y jerarquía de elementos.\n"
            f"  • IMAGEN 2 (Mi producto real): {foto_prod_rel} -> Coloca este envase/frasco real en la posición del producto hero, respetando su forma y etiqueta.\n\n"
            f"INSTRUCCIONES DE REEMPLAZO Y DISEÑO:\n"
            f"- Dispositivo Canónico: {dispositivo_txt}\n"
            f"- Titular Principal (Top, grande y legible): \"{variables_adaptadas['HOOK_TITULAR']}\"\n"
            f"- Subtitular: \"{variables_adaptadas['SUB_HOOK']}\"\n"
            f"- Beneficios en viñetas/cards: {', '.join(variables_adaptadas['ACTIVOS_CLAVE'])}\n"
            f"- Escalera de Precios: Tier 1: {variables_adaptadas['PRECIOS_GT']['TIER_1']} | Tier 2: {variables_adaptadas['PRECIOS_GT']['TIER_2']} | Tier 3: {variables_adaptadas['PRECIOS_GT']['TIER_3']}\n"
            f"- Franja inferior: Botón verde WhatsApp con texto: \"{variables_adaptadas['CTA']}\"\n"
            f"- Garantías en micro-badges: {variables_adaptadas['GARANTIAS']} · Garantía de 30 días\n"
            f"- Registro sanitario (si la IMAGEN 1 muestra un sello regulatorio, va ESTE): "
            f"{registro['texto']}. Somos de {perfil_mercado['pais']}: nunca "
            f"{' ni '.join(registro['ajenos'])} ni "
            f"ningún otro regulador extranjero.\n"
            f"- Formato: 4:5 vertical (1080x1350 px), fotorrealista, iluminación comercial de estudio, colores nítidos, texto 100% legible y sin errores ortográficos.\n\n"
            f"REGLA DE PRECEDENCIA — MANDA LA IMAGEN 1:\n"
            f"La IMAGEN 1 es un anuncio que YA está validado en este mercado. Su estructura no es "
            f"una sugerencia: es el concepto que se está replicando. Qué bloques existen, cuántos "
            f"elementos tiene cada bloque y —sobre todo— qué NO aparece, lo decide la IMAGEN 1.\n"
            f"- Si algo de la lista de arriba NO está en la IMAGEN 1, {'OMÍTELO' if tuteo else 'OMITILO'}. Ejemplo: si la "
            f"IMAGEN 1 muestra un solo precio, va un solo precio, no la escalera de tres.\n"
            f"- Si la IMAGEN 1 tiene un elemento que la lista de arriba no menciona, {'RÉPLICALO' if tuteo else 'REPLICALO'} "
            f"igual, PERO con nuestro dato — nunca con el de la IMAGEN 1.\n"
            f"- Ante cualquier duda entre la lista y la IMAGEN 1, se hace lo que muestra la IMAGEN 1.\n"
            f"La IMAGEN 1 dicta la FORMA. La lista de arriba dicta QUÉ DICE cada parte.\n"
            f"NUNCA se copia de la IMAGEN 1 ningún dato que identifique a SU producto: marca, "
            f"nombre, ingredientes, precios, entidad reguladora, números de registro, nombres o "
            f"ciudades de los testimonios. Todo eso va con NUESTRO dato, que está en la lista de "
            f"arriba. El elemento se replica siempre — lo que cambia es el dato que lleva adentro."
        )

        item = {
            "slot": idx,
            "canonico_id": cid,
            "nombre_blueprint": bp["nombre"],
            "archivo_salida": nombre_archivo,
            "foto_base_competidor": foto_base_rel,
            "foto_producto_propio": foto_prod_rel,
            "variables_json": variables_adaptadas,
            "prompt_director_de_arte": prompt_ia
        }
        paquetes.append(item)

        prompts_texto.append(f"──────────────────────────────────────────────────────────────────────────────")
        prompts_texto.append(f" CONCEPTO #{idx} · {bp['nombre']} ({cid})")
        prompts_texto.append(f" Guardar archivo generado como: {nombre_archivo}")
        prompts_texto.append(f" [1] FOTO BASE REFERENCIA: {foto_base_rel}")
        prompts_texto.append(f" [2] FOTO TU PRODUCTO:     {foto_prod_rel}")
        prompts_texto.append(f"──────────────────────────────────────────────────────────────────────────────")
        prompts_texto.append(f"{prompt_ia}\n\n")

    # 5. El bot NO se escribe aca. El texto del flujo de LucidBot tiene un solo dueno, etapa-5, y su
    # doctrina contradice lo que este script generaba: ETAPA-5.md manda el saludo FIJO, "SIN dolor
    # del angulo (el saludo no cambia por angulo)", y "NO se hace la pregunta de opciones". Este
    # script armaba "¡Hola! Vi que te interesó [producto] para [dolor]" + una pregunta de calificacion:
    # quien lo copiara a LucidBot rompia el saludo fijo. Ademas estaba escrito para CLEARSTEM y se
    # aplicaba a todos (16-sep-2026). Se deja solo el puntero a donde vive el flujo real.
    carpeta = carpeta_de(producto_key)
    adaptacion_bot = {
        "angulo_ganador": angulo,
        "dueno": "etapa-5 (dueno unico del texto del flujo de LucidBot)",
        "flujo": f"PRODUCTOS/{carpeta}/1_HACER_MANUAL.txt",
        "regla": "saludo FIJO sin dolor del angulo · sin pregunta de opciones · el dolor va en el anuncio",
    }

    # Guardar archivos: ACUMULAN las tandas (se fusionan por canonico_id; la tanda nueva pisa solo sus
    # propios canonicos). El paquete que lee la app nunca pierde el prompt de una tanda anterior.
    salida_txt = os.path.join(out_dir, f"PROMPTS_FASE2_{angulo}.txt")
    salida_json = os.path.join(out_dir, f"PAQUETE_CREATIVO_{angulo}.json")
    previos = []
    if os.path.isfile(salida_json):
        try:
            with io.open(salida_json, encoding="utf-8") as fh:
                previos = (json.load(fh).get("conceptos") or [])
        except (OSError, ValueError):
            previos = []
    nuevos = {p["canonico_id"]: p for p in paquetes}
    acumulados = [nuevos.pop(p["canonico_id"], p) for p in previos] + list(nuevos.values())
    for slot, p in enumerate(acumulados, 1):
        p["slot"] = slot

    cabecera = prompts_texto[:5]
    cuerpo_txt = []
    for p in acumulados:
        cuerpo_txt += [
            "──────────────────────────────────────────────────────────────────────────────",
            f" CONCEPTO #{p['slot']} · {p['nombre_blueprint']} ({p['canonico_id']})",
            f" Guardar archivo generado como: {p['archivo_salida']}",
            f" [1] FOTO BASE REFERENCIA: {p['foto_base_competidor']}",
            f" [2] FOTO TU PRODUCTO:     {p['foto_producto_propio']}",
            "──────────────────────────────────────────────────────────────────────────────",
            f"{p['prompt_director_de_arte']}\n\n",
        ]
    with io.open(salida_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(cabecera + cuerpo_txt))
    with io.open(salida_json, "w", encoding="utf-8") as f:
        json.dump({"producto": producto_key, "angulo": angulo, "conceptos": acumulados, "lucidbot_flujo": adaptacion_bot},
                  f, ensure_ascii=False, indent=2)

    print(f"✅ Armados {len(paquetes)} paquetes creativos multimodales ({len(acumulados)} acumulados en el angulo):")
    print(f"   📄 {salida_txt}")
    print(f"   📄 {salida_json}")
    print(f"\n🤖 El texto del bot no se genera aca: es de etapa-5, en {adaptacion_bot['flujo']}.")
    return {"nada_que_hacer": False, "aviso": " ".join(avisos), "angulo": angulo, "paquetes": paquetes,
            "requeridos": requeridos, "registradas": n_filas, "solicitados": n, "salida_txt": salida_txt,
            "salida_json": salida_json, "adaptacion_bot": adaptacion_bot, "descartados": descartados,
            "faltantes_de_aptos": faltantes_de_aptos, "repiten_concepto_key": sel_res["repiten_concepto_key"]}


def generar_paquete_multimodal(producto_key, angulo_manual=None, n=None):
    """(salida_txt, salida_json, paquetes de ESTA tanda, adaptacion_bot). Con nada que armar: (None, None, [], None)."""
    r = _armar(producto_key, angulo_manual, n)
    return r["salida_txt"], r["salida_json"], r["paquetes"], r["adaptacion_bot"]


def _json_de_bloqueo(e):
    """El BLOQUEANTE como dato: `motivo` es la primera linea (la frase), `detalle` el mensaje completo
    (el runner de la app lo muestra si el trabajo falla) y `dato` que falta."""
    completo = str(e.mensaje).strip()
    primera = completo.splitlines()[0].replace("BLOQUEANTE:", "").strip()
    return {"ok": False, "bloqueado": True, "motivo": primera, "dato": e.dato, "detalle": completo}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Arma los prompts multimodales de FASE 2 de un producto")
    ap.add_argument("producto", help="producto_key")
    ap.add_argument("angulo", nargs="?", help="angulo_key; sin él, el ganador que fija _DECISIONES.json")
    ap.add_argument("--n", type=int, default=None,
                    help="cuantos conceptos armar en esta tanda; default = los que faltan del angulo, y nunca mas que eso")
    ap.add_argument("--json", action="store_true",
                    help="stdout = un solo JSON (el bloqueo trae `dato`); el resto va a stderr")
    args = ap.parse_args(argv)
    if args.n is not None and args.n < 0:
        ap.error("--n no puede ser negativo")
    if not args.json:
        _armar(args.producto, args.angulo, args.n)
        return 0
    try:
        with contextlib.redirect_stdout(sys.stderr):
            r = _armar(args.producto, args.angulo, args.n)
    except Bloqueado as e:
        print(json.dumps(_json_de_bloqueo(e), ensure_ascii=False))
        return 1
    rel = lambda ruta: os.path.relpath(ruta, BASE).replace("\\", "/")  # noqa: E731
    cuerpo = {"ok": True, "bloqueado": False, "producto_key": args.producto, "angulo_key": r["angulo"],
              "nada_que_hacer": r["nada_que_hacer"], "conceptos": len(r["paquetes"]),
              "canonicos": [p["canonico_id"] for p in r["paquetes"]], "solicitados": r["solicitados"],
              "faltantes_de_aptos": r["faltantes_de_aptos"], "repiten_concepto_key": r["repiten_concepto_key"],
              "descartados": r["descartados"], "aviso": r["aviso"],
              "archivos": [rel(r["salida_txt"]), rel(r["salida_json"])] if r["salida_json"] else []}
    print(json.dumps(cuerpo, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
