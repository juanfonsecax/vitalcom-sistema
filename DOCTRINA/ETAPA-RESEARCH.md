# ETAPA-RESEARCH — INVESTIGACIÓN EXTERNA DEL PRODUCTO

## Rol
Módulo **opcional y profundo** que se activa entre ETAPA-1B y ETAPA-2 cuando el operador lo solicita. Hace dos cosas independientes que pueden correrse juntas o por separado:

- **Módulo A:** Investigación web profunda de los ingredientes (vía API con web_search), para enriquecer ETAPA-1B con beneficios/dolores adicionales.
- **Módulo B:** Busca anuncios activos en Meta Ads Library (APIFY) sobre el problema que resuelve el producto — y de paso es la **única vía para leer la capa de Facebook/Instagram** (comentarios y copies de competencia que WebSearch no alcanza). Da datos reales de saturación a ETAPA-2.

> **Importante (división de trabajo):** el **minado base de la VOZ DEL CLIENTE ya es permanente en ETAPA-1B** (Paso 0: WebSearch en Reddit/foros/reseñas/blogs) y la búsqueda web por ingrediente también vive en ETAPA-1B. Estos módulos NO los reemplazan: son la versión **más profunda y opcional** para cuando el operador quiere ir más a fondo (Módulo A) o necesita la capa FB/IG + saturación real de competencia (Módulo B, requiere APIFY_TOKEN). Si el operador no los pide, ETAPA-1B ya cubre el piso de voz real + ingredientes; el flujo continúa normal.

Ambos módulos usan llamadas externas desde Claude Code. No son parte del flujo automático — el operador decide si activarlos.

---

## MÓDULO A — Investigación de ingredientes en internet

### Cómo funciona
Claude Code llama la API de Anthropic con web_search habilitado y hace las siguientes búsquedas por cada ingrediente principal del producto:
- "[nombre ingrediente] beneficios científicos"
- "[nombre ingrediente] para qué sirve estudios"
- "[nombre ingrediente] efectos secundarios contraindicaciones"

### Output del Módulo A
Para cada ingrediente:
INGREDIENTE: [nombre]
Beneficios encontrados en web: [lista]
Dolores que resuelve (traducidos a primera persona del avatar): [lista]
Contraindicaciones relevantes: [lista]
Fuentes consultadas: [URLs]
Ángulos nuevos identificados que no estaban en los componentes del operador: [lista]

### Instrucción para Claude Code
```python
import anthropic

client = anthropic.Anthropic()

def investigar_ingrediente(ingrediente, producto):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"""Busca información sobre el ingrediente '{ingrediente}' 
            del producto '{producto}'. Necesito:
            1. Para qué sirve específicamente (mecanismo de acción)
            2. Qué dolores o síntomas resuelve (escríbelos en primera persona como los diría alguien que los sufre)
            3. Contraindicaciones importantes
            Sé específico y concreto. Sin información genérica."""
        }]
    )
    return response

# Llamar por cada ingrediente de la lista
```

---

## MÓDULO B — Análisis de competencia en Meta Ads Library

### Lógica del módulo
1. Busca en Meta Ads Library el NOMBRE EXACTO DEL PRODUCTO
2. Trae máximo 50 anuncios activos (costo: ~$0.04 USD de los $5 del free tier)
3. Extrae los dolores/ángulos que atacan los copies de competidores
4. Cruza esos ángulos con los ángulos candidatos de ETAPA-1B
5. Clasifica en VALIDADOS y VÍRGENES
6. Entrega SOLO el resumen clasificado a ETAPA-2 — nunca los datos crudos

### Por qué buscar por nombre del producto y no por problema
Buscar por nombre del producto encuentra a competidores directos que venden
exactamente lo mismo. Sus copies revelan qué ángulos ya están validados en el
mercado real. Buscar por problema trae demasiado ruido de productos distintos.

### Requiere
- Cuenta Apify con free tier ($5/mes gratuitos)
- APIFY_TOKEN como variable de entorno en Claude Code
- Output completo de ETAPA-1B (lista de ángulos candidatos)

### Código para Claude Code

```python
import requests
import os
import time
import anthropic

def buscar_ads_competencia(nombre_producto, max_ads=50):
    """Busca anuncios activos del producto en Meta Ads Library"""
    
    APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
    if not APIFY_TOKEN:
        return {"error": "APIFY_TOKEN no configurado. Saltar este módulo."}
    
    actor_id = "apify/facebook-ads-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"
    
    payload = {
        "searchTerms": [nombre_producto],
        "country": "ALL",
        "maxItems": max_ads,
        "activeStatus": "ACTIVE",
        "adType": "ALL"
    }
    
    # Iniciar run
    response = requests.post(run_url, json=payload)
    run_id = response.json()["data"]["id"]
    
    # Esperar resultado (máximo 3 minutos)
    status_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={APIFY_TOKEN}"
    intentos = 0
    while intentos < 36:
        status = requests.get(status_url).json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        if status == "FAILED":
            return {"error": "El run de Apify falló. Verificar token y cuota."}
        time.sleep(5)
        intentos += 1
    
    # Obtener copies
    dataset_id = requests.get(status_url).json()["data"]["defaultDatasetId"]
    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    ads = requests.get(items_url).json()
    
    # Extraer solo los copies de texto
    copies = []
    for ad in ads:
        cuerpos = ad.get("ad_creative_bodies", [])
        if cuerpos:
            copies.append(cuerpos[0][:300])  # primeros 300 chars por copy
    
    return {
        "total_encontrados": len(ads),
        "copies": copies
    }


def clasificar_angulos(copies_competencia, angulos_etapa_1b, nombre_producto):
    """Claude analiza los copies y clasifica los ángulos"""
    
    client = anthropic.Anthropic()
    
    copies_texto = "\n---\n".join(copies_competencia[:30])  # máximo 30 copies al análisis
    angulos_texto = "\n".join([f"- {a}" for a in angulos_etapa_1b])
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""Analiza estos copies de anuncios de competidores que venden '{nombre_producto}'.

COPIES DE COMPETIDORES:
{copies_texto}

ÁNGULOS CANDIDATOS (desde ingredientes del producto):
{angulos_texto}

Tu tarea:
1. Identifica qué dolores específicos están atacando los competidores en sus copies
2. Para cada ángulo candidato, determina si algún competidor lo está usando o no
3. Clasifica cada ángulo candidato en:
   - VALIDADO: al menos 1 competidor lo usa (mercado probado, más competencia)
   - VIRGEN: ningún competidor lo usa (oportunidad, potencial ganador)

Responde SOLO con este formato, sin explicaciones extra:

ÁNGULOS USADOS POR COMPETIDORES (extracto):
- [dolor 1 que atacan]
- [dolor 2 que atacan]
- [dolor 3 que atacan]

CLASIFICACIÓN DE ÁNGULOS CANDIDATOS:
VALIDADOS (competidores ya los usan):
- [ángulo]: [qué tan frecuente aparece en copies]

VÍRGENES (nadie los usa — oportunidad):
- [ángulo]: [por qué puede funcionar]

RECOMENDACIÓN PARA TESTEO:
Ángulo más prometedor para testear primero: [nombre del ángulo virgen más fuerte]
Razón: [1 oración]"""
        }]
    )
    
    return response.content[0].text


def ejecutar_modulo_b(nombre_producto, angulos_etapa_1b):
    """Función principal del Módulo B"""
    
    print(f"Buscando anuncios de '{nombre_producto}' en Meta Ads Library...")
    resultado_ads = buscar_ads_competencia(nombre_producto, max_ads=50)
    
    if "error" in resultado_ads:
        return f"MÓDULO B OMITIDO: {resultado_ads['error']}"
    
    total = resultado_ads["total_encontrados"]
    copies = resultado_ads["copies"]
    
    if total == 0:
        return f"""MÓDULO B — RESULTADO:
Producto buscado: {nombre_producto}
Anuncios encontrados: 0
Conclusión: NINGÚN competidor está pautando este producto actualmente.
Todos los ángulos de ETAPA-1B son VÍRGENES por defecto.
Saturación: MUY BAJA — gran oportunidad."""
    
    print(f"Encontrados {total} anuncios. Analizando ángulos...")
    clasificacion = clasificar_angulos(copies, angulos_etapa_1b, nombre_producto)
    
    return f"""MÓDULO B — ANÁLISIS META ADS LIBRARY
Producto buscado: {nombre_producto}
Anuncios activos encontrados: {total}
Saturación general: {"ALTA" if total > 20 else "MEDIA" if total > 5 else "BAJA"}

{clasificacion}

→ Este análisis va directo al campo <datos_saturacion> de ETAPA-2."""
```

### Output que recibe ETAPA-2
Solo el resumen clasificado. Nunca los 50 copies crudos.
El campo `<datos_saturacion>` en ETAPA-2 recibe exactamente esto:

---

## Refinamiento — leer la SITUACIÓN validada, no solo el ángulo

> La meta-jugada: no copiar el PRODUCTO del competidor escalado, sino la **situación validada** de su avatar (dolor + deseo + estructura de oferta que ya probó que convierte), y servirla con un producto/ángulo diferenciado. Aterrizado a NUESTRO modelo (salud / COD / el mercado del producto), sin cambiar el flujo — es una lectura extra sobre lo que el Módulo B (o la búsqueda manual del operador en la Ad Library) ya trae.

Cuando se detecte un competidor **escalado** (varios anuncios activos con recorrido, la MISMA situación de avatar repetida en varios copies), extraer y pasar a ETAPA-2 —además de la saturación— estos tres elementos:

- **SITUACIÓN VALIDADA:** el avatar + el dolor + el deseo + la estructura de oferta que la competencia ya probó que convierte. Es "trabajo ya hecho por el mercado": no hay que adivinar el dolor, ya está validado.
- **HUECO / ÁNGULO VIRGEN dentro de esa situación:** el sub-dolor o encuadre que NINGÚN competidor ataca (regla del 10%: entrar solo si hay un ángulo que nadie usa, o si nadie lo vende por WhatsApp/COD → público distinto al de landing). Ese hueco es el candidato a ganador y **rankea arriba** en ETAPA-2.
- **CHEQUEO DE COHERENCIA DE PRODUCTO:** validar que NUESTRO producto (ya aprobado en ETAPA-PRODUCTO) puede servir de **vehículo** a esa situación. Si calza → priorizar el ángulo virgen sobre los ángulos puramente teóricos del ingrediente. Si NO calza → descartar la situación, **nunca forzar el producto** a un mercado que no le corresponde.

**Formato de salida hacia ETAPA-2** (se suma al bloque `<datos_saturacion>`):
```
SITUACIÓN VALIDADA DETECTADA (competencia escalada):
- Avatar + dolor validado: [...]
- Deseo / promesa que usa la competencia: [...]
- Estructura de oferta validada: [...]
ÁNGULO VIRGEN dentro de esa situación (hueco que nadie ataca): [...]  → candidato a testear primero
¿Nuestro producto calza como vehículo de esta situación?: [sí/no + por qué en 1 línea]
```

> Nota de disciplina (regla del sistema): esto NO reemplaza a ETAPA-PRODUCTO ni invierte el orden del flujo — el producto sigue validándose primero. Es una señal adicional de priorización de ÁNGULO para ETAPA-2, no una licencia para elegir producto por "el mercado del competidor".

---

## Cuándo activar cada módulo

| Situación | Módulo A | Módulo B |
|-----------|----------|----------|
| Producto nuevo sin información | ✅ Sí | ✅ Sí |
| Producto conocido, solo necesita saturación | ❌ No | ✅ Sí |
| El operador ya tiene toda la info del producto | ❌ No | ✅ Sí |
| Sin cuenta Apify | ✅ Sí | ❌ No |

---

## Conexión
Output Módulo A → enriquece ETAPA-1B antes de pasar a ETAPA-2
Output Módulo B → va como `<datos_saturacion>` en el input de ETAPA-2
