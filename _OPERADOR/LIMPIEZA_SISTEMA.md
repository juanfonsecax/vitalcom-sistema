# LIMPIEZA DEL SISTEMA — HOJA DE RUTA

Estado: PARTE 2 cerrada (2A, 2B, 2B-FIX); PARTE 3A, 3B-1 y 3B-2 cerradas; PARTE 3B cerrada completa (3B-3A, 3B-3B, 3B-3C); PARTE 2C en curso: 2C-1 y 2C-2 cerradas, 2C-3 por diseñar · creada 2026-09-29 · actualizada 2026-09-30.

## Objetivo

Que cualquier producto, en cualquier mercado (GT o CO), salga igual por el mismo camino. Hoy el
sistema "varía" porque, cuando un gate bloquea, el trabajo se desvía a un camino manual en prosa y
ese camino pierde lo que el código garantizaba. Ejemplo real del 29-sep: el flujo LucidBot de
OVULOS_PURITY salió sin las REGLAS porque `gen_flujo_bot.py` bloqueaba el flujo entero por un dato
que solo va en el título.

## Decisión de arquitectura

Un solo sistema con **un núcleo** y **dos talleres**, no dos sistemas separados:

| Pieza | Qué hace | Ejemplos |
|---|---|---|
| NÚCLEO | La verdad: datos, estado del producto, reglas numéricas | CSV/Postgres, `FLUJO.json`, `flujo.py`, `decidir.py`, `costear.py`, `mercado.py` |
| FÁBRICA | Produce contenido: ángulos, copies, imágenes, bot, plan, publicación | etapa-producto, 0, 1, 1b, 2, 3, 4, 5, 6, 9, render, guardar-producto |
| OPERACIÓN | Mide y decide: ingesta, métricas, pausar/escalar, cierre | etapa-7, 10, 11, `ciclo-diario`, `recopilar-lucidsales` |
| PANTALLA | Lo que ve el operador | `app/` (y `VISTAS/` como respaldo) |

Por qué no dos sistemas: la relación no es una línea, es un ciclo. Operación le pide trabajo a
Fábrica (RENOVAR un concepto, 10 conceptos para FASE 2, microángulos para FASE 4). Dos sistemas con
dos copias de los datos se desincronizan, que es justo el problema que queremos quitar. Los talleres
se comunican por una ORDEN escrita en el núcleo, nunca por prosa.

Regla guía de toda la limpieza: **un solo camino**. Un gate nunca manda a un desvío manual: dice
qué dato falta y por dónde entra.

## Partes

| Parte | Qué | Quién | Estado |
|---|---|---|---|
| 1 | Inventario: cada archivo clasificado por taller y estado, más la lista de desvíos | IA ejecutora | HECHA 30-sep (`_OPERADOR/LIMPIEZA/`) |
| 2A | El flujo LucidBot sale completo e igual en GT y CO (4 arreglos en `gen_flujo_bot.py`) | IA ejecutora | HECHA 30-sep (commit `b9ffd51`, verificada) |
| 2B | Moneda por mercado en el MOTOR (`decidir`, `flujo`, `perfilar_angulos`) | IA ejecutora | HECHA 30-sep (commit `f6f923d`, verificada) |
| 2B-FIX | Un solo envoltorio de monto y sin `Q` silencioso para un producto real | IA ejecutora | HECHA 30-sep (commit `fe0bde1`, verificada) |
| 2B-2 | Reportes y pantallas | — | NO APLICA: `gen_pl.py` y `gen_dashboard.py` ya se declaran de un solo mercado (GT) y excluyen CO; su `Q` es correcto. Lo que falta es un reporte de Colombia: es una función nueva, se decide cuando CO tenga ventas |
| 2C-1 | Un solo token de producto en los nombres de Meta (paquete, gate y orden de activación usan `clave_campana`, como el lanzador) | IA ejecutora, guía de Claude | HECHA 30-sep (commit `16355ee`, verificada) |
| 2C-2 | El paquete segmenta al país del mercado y presupuesta en la moneda de la cuenta | IA ejecutora, guía de Claude | HECHA 30-sep (commit `bc4d3fe`, verificada) |
| 2C-3A | La moneda de la cuenta de OVULOS pasa a USD con un escritor sancionado (si no, el gasto de CO entra dividido por 3152,5) | IA ejecutora, guía de Claude | HECHA 30-sep (commits `7fe5e58`, `7b16d33`, verificada) |
| 2C-3B | Un solo dueño del nombre de anuncio (formato, destino) y de la réplica `R[N]` | IA ejecutora, guía de Claude | Va como T4 del PAQUETE 4 |
| P4 | PAQUETE 4: borrar código muerto (T1), punteros viejos a CLAUDE.md en etapas (T2), skill publicar-meta con biblioteca (T3), 2C-3B (T4) | IA ejecutora, guía de Claude | HECHO 30-sep (4 commits, verificado) |
| P5 | PAQUETE 5: últimos punteros, restos en disco y todo el trabajo pendiente guardado en commits | IA ejecutora, guía de Claude | SIGUIENTE — guía lista; cierra la limpieza |
| 3A | Los subagentes dejan de heredar los CLAUDE.md (global y del proyecto); reciben solo constantes e invariantes | IA ejecutora + prueba del operador | HECHA 30-sep (commit `2d3ebab`; prueba de contexto superada: la etapa no ve los CLAUDE.md y cita el invariante 4 y la definición de ÁNGULO) |
| 3B-1 | Los bloques de juicio del bot viven en `BLOQUES_BOT.md` y `gen_flujo_bot.py` los inserta: el flujo sale completo | IA ejecutora | HECHA 30-sep (commit `9814298`, verificada) |
| 3B-2 | Los prompts de infografías viven en `INFOGRAFIAS.md` y `gen_manual.py` arma el manual completo (sin reemplazar nada todavía) | IA ejecutora | HECHA 30-sep (commit `0a1d647`, verificada) |
| 3B-3A | El manual generado queda completo (encabezado único, config fija de Meta, mensaje prellenado, imágenes de referencia, monto en moneda de la cuenta) y el presupuesto de fase y la fecha de lanzamiento tienen un solo dueño | IA ejecutora, guía de Claude | HECHA 30-sep (commits `0cea30c` y `7380de1`, verificada) |
| 3B-3B | `etapa-4` y `etapa-5` escriben `INFOGRAFIAS.md` y `BLOQUES_BOT.md`; en FASE 1 `etapa-guardar-producto` corre `gen_manual.py` en vez de tipear | IA ejecutora, guía de Claude | HECHA 30-sep (commit `4e5eb60`, verificada) |
| 3B-3C | Los dueños nuevos (`BLOQUES_BOT.md`, `INFOGRAFIAS.md`, `gen_manual.py`) entran al MAPA DE ARCHIVOS de `CLAUDE.md` | IA ejecutora, guía de Claude | HECHA 30-sep (commit `9c15c29`, verificada) |
| 4 | Borrar muerto y duplicado con los tests como red | IA ejecutora | Pendiente |
| 5 | Un solo manual por producto generado por el sistema, y una sola pantalla | IA ejecutora | Pendiente |

Cada parte termina con los tests pasando: `python -m pytest Ads/_TOOLS -q`.

---

## Lectura de la Parte 1

- 260 filas: 257 VIVO, 3 MUERTO. No hay grasa de archivos; la grasa es peso de contexto y desvíos.
- De los 3 MUERTO, solo `Ads/_TOOLS/gen_sistema.py` es candidato real. Los dos tests
  (`test_cargar_packshot.py`, `test_referencia_f1.py`) no tienen lectores porque los corre pytest:
  están vivos.
- Los desvíos graves quedaron en `_OPERADOR/LIMPIEZA/DESVIOS.md`. La Parte 2 los ataca por orden de
  daño: primero el bot (2A), después la moneda (2B), después la publicación (2C).

---

## PARTE 2A — EL FLUJO LUCIDBOT SALE COMPLETO E IGUAL EN GT Y CO

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: 4 arreglos en el generador del flujo LucidBot. Cada arreglo lleva su test.
Archivos que puedes modificar (SOLO estos 3):
  Ads/_TOOLS/gen_flujo_bot.py
  Ads/_TOOLS/mercado.py
  Ads/_TOOLS/test_gen_flujo_bot.py
Prohibido: tocar DOCTRINA/, cualquier CSV o JSON de PRODUCTOS/, y cualquier carpeta de producto.
Prohibido: correr `gen_flujo_bot.py OVULOS_PURITY` SIN `--copy`. Sin ese flag sobrescribe
  PRODUCTOS/OVULOS_PURITY/FLUJO_LUCIDBOT.md, que está editado a mano y en producción.

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS/gen_flujo_bot.py Ads/_TOOLS/mercado.py Ads/_TOOLS/test_gen_flujo_bot.py
     Debe salir vacío. Si sale algo, DETENTE y avisa.
  2. python Ads/_TOOLS/test_gen_flujo_bot.py   → debe terminar en "TODO PASA".
  3. Lee completos gen_flujo_bot.py y test_gen_flujo_bot.py. Los tests nuevos se escriben con el
     mismo estilo (función `check`, fixture `_con_datos`) y se REGISTRAN en la tupla de `main()`
     al final del archivo de tests; un test sin registrar no corre.

ARREGLO 1 — Un producto sin ventas ni ángulo no bloquea el flujo
  Hoy: en `resolver()`, si no hay ángulo de FASE 2 ni filas en _ESTADO_ANGULOS.csv,
    `angulo_nombre` queda "" y el flujo ENTERO se bloquea. Ese dato solo va en el título.
  Cambio: en la rama `else` (sin angulo_f2 y sin razon_f2), cuando `cand` está vacío,
    `v["angulo_nombre"] = "PARAGUAS F1"`.
  NO cambiar: la rama `elif razon_f2` (ángulo ambiguo en FASE 2) sigue bloqueando.
  Test nuevo `test_producto_sin_ventas_no_bloquea_por_titulo`: con
    `_con_datos({"_ESTADO_ANGULOS.csv": [], "_DIM_CREATIVOS.csv": [], "_DIM_CONJUNTOS.csv": []},
    lambda: G.resolver("CLEARSTEM"))` comprobar que `v["angulo_nombre"] == "PARAGUAS F1"` y que
    "angulo_nombre" no está en `faltan`.

ARREGLO 2 — El filtro de verbos médicos no calza dentro de otra palabra
  Hoy: `(r"(?:cura|curar|elimina el|erradica)\b", ...)` rechaza "frescura" y "procurar".
  Cambio: `r"\b(?:cura|curar|elimina el|erradica)\b"`.
  Test nuevo `test_verbo_medico_no_calza_dentro_de_palabra`:
    `G.prohibiciones("la frescura se mantiene y hay que procurar descanso")` NO contiene
    "VERBO MEDICO PROHIBIDO."; `G.prohibiciones("esto cura la infección")` SÍ lo contiene.

ARREGLO 3 — El precio usa el separador de miles de la moneda del mercado
  Hoy: `escalera()` usa `format(..., ",")` siempre → en Colombia sale "$84,900".
  Cambio: `escalera(pk, fila, simbolo, moneda="GTQ")`. Separador de miles "." si
    `moneda == "COP"`, "," en cualquier otro caso (GT queda idéntico a hoy). En `resolver()`,
    leer `moneda` de la MISMA fila de _DIM_MERCADOS.csv de donde ya salen `simbolo` y `persona`,
    y pasarla a `escalera()`.
  Test nuevo `test_escalera_co_usa_punto_de_miles`: con `_con_datos` y 3 filas ACTIVO de un
    producto ficticio en "_DIM_PRECIOS.csv" (precio_q 84900, 129900, 169900; unidades 1, 2, 3;
    etiqueta 1x, 2x, 3x), `G.escalera("PROD_X", {"envase": "paquete", "duracion_1u": ""}, "$", "COP")`
    contiene "$84.900" y NO contiene "84,900". Con moneda "GTQ" y precio 1299 contiene "Q1,299".

ARREGLO 4 — La persona del texto sale del mercado (GT voseo, CO tuteo)
  Hoy: el texto fijo de la plantilla y de `escalera()` está en voseo; en Colombia sale en voseo.
  Cambio en mercado.py — agregar:
    VOSEO_A_TUTEO = [   # pares (voseo, tuteo); frases específicas donde la palabra sola es ambigua
      ("con vos", "contigo"), ("por vos", "por ti"), ("Contame", "Cuéntame"),
      ("escribís", "escribes"), ("Deseás", "Deseas"), ("sabés", "sabes"), ("pagás", "pagas"),
      ("¿Confirmame", "¿Me confirmas"), ("Confirmame", "Confírmame"), ("arriesgás", "arriesgas"),
      ("llevás", "llevas"), ("asegurate", "asegúrate"), ("podés", "puedes"),
      ("indicame", "indícame"), ("o escribí OFICINA", "o escribe OFICINA"),
      ("reclamás", "reclamas"), ("preferís", "prefieres"), ("Confirmás", "Confirmas"),
      ("Recordá", "Recuerda"), ("tenés", "tienes"), ("disfrutés", "disfrutes"),
      ("escribás", "escribas"), ("hacé ", "haz "), ("Indicale", "Indícale"),
      ("corregila", "corrígela"), ("Hacelo", "Hazlo"), ("CAMBIÁ", "CAMBIA"), ("Decime", "Dime"),
      ("persuadilo", "persuádelo"), ("Respondé", "Responde"), ("respondé", "responde"),
      ("No continuás", "No continúes"),
    ]
    def aplicar_persona(texto, persona):
        """Devuelve el texto en la persona del mercado. Solo 'tuteo' transforma."""
        → si persona != "tuteo" devuelve el texto igual; si es "tuteo" aplica los pares en orden.
    RE_VOSEO = re.compile(r"\b(vos|sabés|pagás|podés|tenés|querés|llevás|arriesgás|reclamás|"
        r"preferís|escribís|deseás|confirmás|contame|decime|confirmame|indicame|asegurate|"
        r"recordá|respondé|hacelo|indicale|corregila|persuadilo|cambiá|disfrutés|escribás|"
        r"continuás)\b", re.I)
    def voseo_restante(texto):
        """Lista ordenada y sin repetir de las formas de voseo que quedan en el texto."""
  Cambio en gen_flujo_bot.py:
    a. Al final de `render(v)`: `txt = mercado.aplicar_persona(txt, v.get("persona", ""))`
       antes del return (importar `mercado` como lo hacen los demás scripts de Ads/_TOOLS).
    b. `prohibiciones(txt, persona="")`: si `persona == "tuteo"` y `mercado.voseo_restante(copy)`
       no está vacío, agregar el hallazgo
       "VOSEO EN MERCADO DE TUTEO: <palabras separadas por coma>".
    c. En `una()` y `una_json()`, pasar `v.get("persona", "")` a `prohibiciones`.
  Si al renderizar OVULOS_PURITY el gate encuentra una forma de voseo que no está en la tabla,
    AGREGA el par a VOSEO_A_TUTEO (no aflojes el gate) y vuelve a correr.
  Tests nuevos:
    `test_persona_tuteo_transforma_y_voseo_no`: `mercado.aplicar_persona("Contame, ¿pagás con vos?", "tuteo")`
      no contiene "Contame", "pagás" ni "vos"; con "voseo" devuelve el texto idéntico.
    `test_voseo_en_mercado_de_tuteo_se_rechaza`: `G.prohibiciones("Ya sabés que pagás al recibir", "tuteo")`
      contiene un hallazgo que empieza por "VOSEO EN MERCADO DE TUTEO"; con persona "voseo" no.
    `test_flujo_co_renderiza_sin_voseo`: `v, faltan, _ = G.resolver("OVULOS_PURITY")`,
      `faltan == []`, y `mercado.voseo_restante(G.solo_copy(G.render(v))) == []`.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python Ads/_TOOLS/test_gen_flujo_bot.py        → "TODO PASA"
  2. python -m pytest Ads/_TOOLS -q                 → 54 passed (o más), 0 failed
  3. python Ads/_TOOLS/gen_flujo_bot.py OVULOS_PURITY --copy
       → NO dice BLOQUEADO ni RECHAZADO; el texto incluye "REGLAS CONVERSACIONALES",
         precios con punto ("$84.900") y ninguna forma de voseo.
  4. python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --copy
       → sigue en voseo ("Contame", "pagás") y con sus precios en Q como antes.
  5. git status --short → tuyos SOLO los 3 archivos permitidos. En particular,
     PRODUCTOS/OVULOS_PURITY/FLUJO_LUCIDBOT.md no debe cambiar.
  6. Commit en la rama actual, solo esos 3 archivos, sin push:
     git add Ads/_TOOLS/gen_flujo_bot.py Ads/_TOOLS/mercado.py Ads/_TOOLS/test_gen_flujo_bot.py
     git commit -m "fix(flujo-bot): render a complete flow for unlaunched products and per-market persona and price format"
     Sin "Co-Authored-By" ni ninguna línea de atribución.

SI ALGO NO CUADRA (un test viejo falla, una función no existe como se describe, el chequeo 4
  cambia el texto de CLEARSTEM): DETENTE, no improvises, y reporta qué encontraste.

ENTREGA: salida de los chequeos 1, 2, 3 (solo las primeras 15 líneas y el bloque de REGLAS) y 4
  (primeras 15 líneas), el hash del commit y los pares que agregaste a VOSEO_A_TUTEO.
```

---

## PARTE 2B — EL MOTOR HABLA EN LA MONEDA DEL PRODUCTO

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: el motor de decisión escribe "Q" fijo en sus textos. Un producto de Colombia (valores en
COP) sale como "CPA Q9426.0". Debe salir en la moneda de su mercado. Es un cambio SOLO de
presentación: ningún número, umbral, estado ni cálculo cambia.

Archivos que puedes modificar (SOLO estos 5):
  Ads/_TOOLS/mercado.py
  Ads/_TOOLS/test_mercado.py
  Ads/_TOOLS/decidir.py
  Ads/_TOOLS/flujo.py
  Ads/_TOOLS/perfilar_angulos.py
Prohibido: tocar CSV/JSON de PRODUCTOS/, DOCTRINA/, carpetas de producto.
Prohibido: correr con --escribir. Prohibido correr `perfilar_angulos.py` por CLI (escribe un CSV
  por defecto): se verifica solo con sus tests.

ANTES DE EMPEZAR
  1. git status --short de los 5 archivos → vacío. Si no, DETENTE y avisa.
  2. python -m pytest Ads/_TOOLS -q → 54 passed.
  3. Guardar la salida actual (la "foto de antes"):
       python Ads/_TOOLS/decidir.py > _OPERADOR/LIMPIEZA/2B_antes_decidir.txt
       python Ads/_TOOLS/flujo.py --todo > _OPERADOR/LIMPIEZA/2B_antes_flujo.txt
     (en PowerShell usar `| Out-File -Encoding utf8 <ruta>`; definir antes $env:PYTHONIOENCODING="utf-8")
  4. Buscar si algún código LEE esos textos con un patrón:
       rg -n "CPA Q|BE Q|Obj Q" --glob "*.py" --glob "*.js" --glob "*.ts" --glob "*.tsx" --glob "*.sql"
     Si fuera de decidir.py, flujo.py, perfilar_angulos.py y los test_*.py aparece código que
     PARSEA ese texto (re.search, split, startswith, regex en JS), DETENTE y reporta dónde.

PASO 1 — Un solo formateador, en mercado.py
  Agregar (con caché para no releer el CSV en cada llamada):
    def monto_producto(valor, producto_key, decimales=None, base=None):
        """Un monto en la moneda del mercado del producto.
        COP: formatear_monto(valor, perfil, 0)            → "$ 28.031"
        resto, decimales=None: simbolo + "%s" % valor     → "Q50.1" (el valor tal cual venía)
        resto, decimales=N:    simbolo + "%.*f"           → "Q50.10" con N=2
        """
  El perfil sale de `perfil_de_producto(producto_key, base)`. Si el producto no resuelve
  mercado, se deja propagar el error: no hay default (así funciona ya mercado.py).
  La caché se indexa por (producto_key, base) y no debe romper los tests que usan `base` temporal.

PASO 2 — Reemplazar cada "Q" fijo de estas líneas por monto_producto(...)
  decidir.py: 656, 674, 694, 713, 729, 761, 778, 793, 797, 1092, 1108
  flujo.py: 505, 709, 718
  perfilar_angulos.py: 307, 312, 482, 493, 494, 579, 580, 585
  (los números de línea son de referencia: ubica cada uno con rg -n "Q\{|Q%" <archivo>)
  Reglas:
   a. `decimales` = los mismos que imprime hoy esa línea (`:.1f` → 1, `:.0f` → 0, `%.2f` → 2,
      `%s` → None). Para un producto de GT el texto debe quedar IDÉNTICO byte a byte.
   b. El `producto_key` sale de la variable que ya esté en el alcance de esa función. Si no hay,
      se agrega como parámetro y se pasa desde quien la llama. No leer variables globales ni
      adivinar el producto por el nombre del conjunto.
   c. No tocar nada más de esas líneas: ni el texto, ni los números, ni las condiciones.
   d. Los nombres de campos y columnas que terminan en `_q` NO se renombran.

PASO 3 — Tests en test_mercado.py (mismo estilo que los que ya hay, con `_sistema`)
  test_monto_producto_gt_queda_como_hoy: producto GT → monto_producto(50.123, pk, 1) == "Q50.1",
    monto_producto("50.1", pk) == "Q50.1", monto_producto(93, pk, 2) == "Q93.00".
  test_monto_producto_co_usa_pesos_sin_decimales: producto CO → monto_producto(28031.11, pk, 2)
    == "$ 28.031" y monto_producto(9426, pk) == "$ 9.426".
  test_monto_producto_sin_mercado_falla: producto inexistente → lanza el mismo error que mercado_de.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python -m pytest Ads/_TOOLS -q → 54 passed (o más), 0 failed.
  2. Foto de después y comparación:
       python Ads/_TOOLS/decidir.py > _OPERADOR/LIMPIEZA/2B_despues_decidir.txt
       python Ads/_TOOLS/flujo.py --todo > _OPERADOR/LIMPIEZA/2B_despues_flujo.txt
       git diff --no-index _OPERADOR/LIMPIEZA/2B_antes_decidir.txt _OPERADOR/LIMPIEZA/2B_despues_decidir.txt
       git diff --no-index _OPERADOR/LIMPIEZA/2B_antes_flujo.txt _OPERADOR/LIMPIEZA/2B_despues_flujo.txt
     Las ÚNICAS líneas distintas permitidas son las de productos con mercado CO (hoy:
     OVULOS_PURITY). Si cambia una sola línea de un producto de GT, está mal: corrige y repite.
     Si no hay ninguna diferencia, también es válido (el producto CO aún no tiene data).
  3. rg -n "Q\{|Q%" Ads/_TOOLS/decidir.py Ads/_TOOLS/flujo.py Ads/_TOOLS/perfilar_angulos.py
     → no queda ningún "Q" fijo delante de un monto (si queda alguno, explica por qué no aplica).
  4. git status --short → tuyos solo los 5 archivos permitidos (más los 4 .txt de la foto).
  5. Commit en la rama actual, solo los 5 archivos, sin push:
     git commit -m "fix(motor): print amounts in the product market currency"
     Sin "Co-Authored-By" ni ninguna línea de atribución.

SI ALGO NO CUADRA: DETENTE, no improvises, y reporta qué encontraste.

ENTREGA: resultado de los chequeos 1, 2 (el diff completo, o "sin diferencias") y 3, el hash del
  commit, y la lista de funciones a las que tuviste que agregarles el parámetro producto_key.
```

---

## PARTE 2B-FIX — UN SOLO ENVOLTORIO DE MONTO

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: la Parte 2B dejó la función `_monto` copiada 3 veces (decidir.py, flujo.py,
perfilar_angulos.py), y las 3 caen a "Q" en silencio ante CUALQUIER error de mercado. Queda
una sola función, en mercado.py, y el "Q" silencioso solo vale para productos que no existen
(fixtures de tests), nunca para un producto real mal declarado.

Archivos que puedes modificar (SOLO estos 5):
  Ads/_TOOLS/mercado.py · Ads/_TOOLS/test_mercado.py
  Ads/_TOOLS/decidir.py · Ads/_TOOLS/flujo.py · Ads/_TOOLS/perfilar_angulos.py
Prohibido: --escribir, correr perfilar_angulos.py por CLI, tocar CSV/JSON/DOCTRINA.

ANTES: git status --short de los 5 → vacío · python -m pytest Ads/_TOOLS -q → 54 passed.
  Contar las llamadas actuales y anotar el número N:
    rg -o "_monto\(" Ads/_TOOLS/decidir.py Ads/_TOOLS/flujo.py Ads/_TOOLS/perfilar_angulos.py
    N = total de coincidencias menos 3 (las 3 líneas `def _monto(`).

PASO 1 — mercado.py: agregar
    def monto_o_q(valor, decimales, producto_key, base=None):
        """El monto en la moneda del producto, para textos del motor.
        Sin producto_key, o si el producto NO tiene fila en _DIM_PRODUCTOS (fixtures de tests,
        backtest): formato Q de siempre. Si el producto SÍ tiene fila pero su mercado no
        resuelve: se propaga MercadoError (un producto real nunca sale en Q por descarte)."""
  Cómo distinguir los dos casos: llamar `_fila_producto(producto_key, base)` dentro de un
  try/except MercadoError → si falla, devolver el formato Q; si devuelve fila, llamar
  `monto_producto(valor, producto_key, decimales, base)` SIN try (que propague).
  Formato Q: "Q%s" % valor si decimales is None; si no, "Q%.*f" % (decimales, float(valor)).

PASO 2 — En decidir.py, flujo.py y perfilar_angulos.py: BORRAR la función local `_monto` y
  reemplazar cada llamada `_monto(a, b, c)` por `mercado.monto_o_q(a, b, c)` (mismos
  argumentos, mismo orden). No cambiar nada más.

PASO 3 — Tests en test_mercado.py:
  test_monto_o_q_producto_inexistente_sale_en_q: monto_o_q(50.123, 1, "NO_EXISTE", base) == "Q50.1"
    y monto_o_q(50.1, None, None, base) == "Q50.1".
  test_monto_o_q_producto_real_sin_mercado_falla: producto con fila pero `mercado` vacío →
    lanza MercadoError.
  test_monto_o_q_producto_co: producto CO → monto_o_q(28031.11, 2, pk, base) == "$ 28.031".

CHEQUEOS FINALES
  1. python -m pytest Ads/_TOOLS -q → 54 passed (o más), 0 failed.
  2. rg -n "def _monto" Ads/_TOOLS → 0 resultados.
  3. rg -o "mercado\.monto_o_q\(" Ads/_TOOLS/decidir.py Ads/_TOOLS/flujo.py Ads/_TOOLS/perfilar_angulos.py
     → el total de coincidencias es exactamente N.
  4. Foto de después, contra la foto "antes" de la 2B (ya está en _OPERADOR/LIMPIEZA/):
       python Ads/_TOOLS/decidir.py > _OPERADOR/LIMPIEZA/2BFIX_decidir.txt
       python Ads/_TOOLS/flujo.py --todo > _OPERADOR/LIMPIEZA/2BFIX_flujo.txt
       git diff --no-index _OPERADOR/LIMPIEZA/2B_antes_decidir.txt _OPERADOR/LIMPIEZA/2BFIX_decidir.txt
       git diff --no-index _OPERADOR/LIMPIEZA/2B_antes_flujo.txt _OPERADOR/LIMPIEZA/2BFIX_flujo.txt
     Solo pueden diferir líneas de productos CO. Si el motor ahora FALLA con MercadoError en un
     producto real, NO lo tapes: DETENTE y reporta qué producto es y qué le falta.
  5. Commit en la rama actual, solo los 5 archivos, sin push, sin atribución:
     git commit -m "refactor(motor): single market-aware amount formatter"

ENTREGA: chequeos 1 a 4 y el hash del commit.
```

---

## PARTE 2C — LA PUBLICACIÓN SALE IGUAL PARA CUALQUIER PRODUCTO Y MERCADO

Qué encontró Claude el 30-sep leyendo `gen_publicacion.py`, `verificar_publicacion.py`,
`gen_orden_activacion.py` y la skill `publicar-meta`:

| Hallazgo | Consecuencia |
|---|---|
| El token de producto en los nombres de Meta tiene dos dueños: `gen_lanzador.py` usa `clave_campana` (`corto()`), `gen_publicacion.py` usa `producto_key` | OVULOS se lanzó como `EXTERNA_OVULOSPURITY_TEST_20260930`; el paquete lo llamaría `EXTERNA_OVULOS_PURITY_TEST_…` (con un `_` dentro del campo, que rompe la convención). NUSAVA vive en Meta como `NUSAVAB12`; el paquete diría `NUSAVA`. El snapshot compara por nombre: la idempotencia no ve lo que ya existe y el gate da FALTA |
| `verificar_publicacion.py` arma el prefijo de «no declarados» con `producto_key` y `gen_orden_activacion.py` busca la campaña con `pk in nombre` y `"F1" in nombre` | Ningún nombre real de FASE 1 contiene «F1» (el token es TEST): ese respaldo nunca encuentra la campaña |
| `countries: ["GT"]` fijo en el conjunto | Un producto de Colombia saldría segmentado a Guatemala |
| Cuenta que no factura en USD → bloqueo, sin conversión | Ningún producto de CO puede tener paquete aunque su cuenta tenga MCP |
| La cuenta EXTERNA no está en `_DIM_CUENTAS.csv` | OVULOS no tiene paquete, ni verificación, ni `ad_id` en `_DIM_CREATIVOS.csv` (0 filas) |

Va en tres entregas: **2C-1** (un solo token de producto), **2C-2** (país y moneda por mercado) y
**2C-3** (publicación manual verificada para cuentas sin MCP; se diseña cuando el operador
responda si la cuenta EXTERNA es suya). Cada una se pasa cuando Claude verificó la anterior.

#### PARTE 2C-1 — UN SOLO TOKEN DE PRODUCTO EN LOS NOMBRES DE META

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: que el paquete de publicación, el gate de publicación y la orden de activación usen el
mismo token de producto que ya usa gen_lanzador.py (función `corto`, sale de clave_campana).

Archivos que puedes modificar (SOLO estos 6):
  Ads/_TOOLS/gen_publicacion.py
  Ads/_TOOLS/test_gen_publicacion.py
  Ads/_TOOLS/verificar_publicacion.py
  Ads/_TOOLS/test_verificar_publicacion.py
  Ads/_TOOLS/gen_orden_activacion.py
  Ads/_TOOLS/test_gen_orden_activacion.py
PROHIBIDO: tocar PRODUCTOS/, DOCTRINA/, .claude/, gen_lanzador.py, flujo.py.
PROHIBIDO: correr gen_publicacion.py sin --solo-paquete (escribe _PUBLICACION_F*.json y puede
  registrar eventos), correr verificar_publicacion.py con --escribir, y llamar a Meta.
Comandos desde la raíz del repo, de a uno. En PowerShell: $env:PYTHONIOENCODING="utf-8" y
  `| Out-File -Encoding utf8 <archivo>` en vez de `>`.
Docstrings y comentarios nuevos: la regla vigente, sin fechas ni historia.

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.
  3. Comprueba que `import gen_lanzador` no imprime, no escribe y no cambia de carpeta (su
     código suelto está bajo `if __name__ == "__main__":`). Si hace algo de eso, DETENTE.
  4. Fotos de antes, una por producto, en _OPERADOR/LIMPIEZA/2C1_antes_<PK>.json:
       python Ads/_TOOLS/gen_publicacion.py --producto OVULOS_PURITY --fase 1 --solo-paquete --json
       python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 1 --solo-paquete --json
       python Ads/_TOOLS/gen_publicacion.py --producto CLEARSTEM --fase 1 --solo-paquete --json
     (Pueden salir con exit 1 por bloqueantes: no importa, se guarda la salida igual.)

PASO 1 — gen_publicacion.py
  a. Arriba, junto a los demás imports del módulo:
         from gen_lanzador import corto as token_producto  # dueño del token de producto en los nombres
  b. En main(), justo después de `prod = productos[pk]`:
         tok = token_producto(prod)
  c. En las dos llamadas que arman nombres, cambia el argumento `pk` por `tok`:
         camp = nombre_campana(fase, cta, tok, brazo, angulo, fecha)
         cj = nombre_conjunto(fase, cta, tok, ang_u, brazo, numero_conj)
     NO cambies `siguiente_replica(...)` (filtra por producto_key, está bien), ni la firma, ni
     los nombres de media, ni `nombre_anuncio`.
  d. En el dict `paquete`, justo después de `"producto_key": pk,` agrega `"token_producto": tok,`.

PASO 2 — verificar_publicacion.py
  a. Agrega una función pura:
         def no_declarados(meta, declarados, campana):
             """Nombres del snapshot que empiezan con cuenta_token_ de la campaña declarada, no
             están en el manifiesto y llevan el token de fase de la campaña. Se reportan, nunca
             se borran."""
             prefijo = "_".join(campana.split("_")[:2]) + "_"
             token_fase = campana.split("_")[2]
             return [n for n in meta
                     if n.startswith(prefijo) and n not in declarados and token_fase in n]
  b. En main(), reemplaza el bloque que arma `prefijo` y `no_declarados` por:
         no_declarados_ = no_declarados(meta, declarados, man["campana"])
     y usa `no_declarados_` donde hoy se usa `no_declarados` (el `if` y el `for` del reporte).

PASO 3 — gen_orden_activacion.py
  a. Agrega:
         def es_campana_de_fase(nombre, token, fase):
             """True si `nombre` es una campaña de ese producto y esa fase: su segundo campo es
             el token del producto y contiene un token de flujo.TOKEN_FASE para la fase."""
     (import de gen_lanzador y de flujo DENTRO de las funciones que los usan, o arriba si
     ninguno tiene efectos al importarse; la comparación del token es exacta, sobre
     nombre.split("_")[1]; la de fase, sobre el nombre en mayúsculas.)
  b. En las DOS condiciones que hoy dicen
         pk in info.get("name", "") and f"F{fase}" in info.get("name", "")
     usa en su lugar
         es_campana_de_fase(info.get("name", ""), tok, fase)
     con `tok = token_producto(fila_prod)` calculado una vez; si fila_prod es None, tok = None
     y la función devuelve False.

PASO 4 — tests
  test_gen_publicacion.py:
    - `test_token_producto_sale_de_clave_campana` (función pura):
        {"producto_key": "OVULOS_PURITY", "clave_campana": "OVULOSPURITY"} → "OVULOSPURITY"
        {"producto_key": "OVULOS_PURITY", "clave_campana": ""}             → "OVULOS-PURITY"
        {"producto_key": "NUSAVA", "clave_campana": "NUSAVAB12"}          → "NUSAVAB12"
    - Agrega a `_fixture_fase1_completa` un parámetro opcional `clave_campana=""` que se escribe
      en la fila de PX (el valor por defecto deja todo como hoy). Test
      `test_paquete_nombra_con_el_token_de_clave_campana`: con clave_campana="PXDOS", arma el
      paquete con el mismo helper que ya usan los tests de biblioteca/fase 1 y comprueba que
      manifiesto["campana"] empieza con "GTR7_PXDOS_TEST_", que cada conjunto del manifiesto
      empieza con "GTR7_PXDOS_" y que paquete["token_producto"] == "PXDOS".
  test_verificar_publicacion.py — `test_no_declarados_usa_el_prefijo_de_la_campana`:
      campana "EXTERNA_OVULOSPURITY_TEST_20260930"; meta con
        "EXTERNA_OVULOSPURITY_TEST_20260930" (declarada),
        "EXTERNA_OVULOSPURITY_TEST_20260929" (no declarada),
        "EXTERNA_OTRO_TEST_20260930", "GTR7_OVULOSPURITY_TEST_20260930"
      → devuelve solo ["EXTERNA_OVULOSPURITY_TEST_20260929"].
  test_gen_orden_activacion.py — `test_es_campana_de_fase`:
      ("EXTERNA_OVULOSPURITY_TEST_20260930", "OVULOSPURITY", 1) → True
      ("EXTERNA_OVULOSPURITY_TEST_20260930", "OVULOSPURITY", 2) → False
      ("GTR7_OVULOSPURITY-X_TEST_20260930", "OVULOSPURITY", 1)  → False
      ("GTR0_TINNIDROP_CONCEPTOS-A_20260907", "TINNIDROP", 2)   → True
      (cualquier nombre, None, 1)                               → False
  Registra cada test nuevo en el main() de su archivo.

CHEQUEOS FINALES
  1. python Ads/_TOOLS/test_gen_publicacion.py, test_verificar_publicacion.py y
     test_gen_orden_activacion.py → sin fallas.
  2. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  3. Fotos de después (mismos 3 comandos) en _OPERADOR/LIMPIEZA/2C1_despues_<PK>.json y
       git diff --no-index --stat _OPERADOR/LIMPIEZA/2C1_antes_<PK>.json _OPERADOR/LIMPIEZA/2C1_despues_<PK>.json
     Esperado:
       OVULOS_PURITY → los nombres pasan de EXTERNA_OVULOS_PURITY_… a EXTERNA_OVULOSPURITY_…,
                       aparece "token_producto", y cambia "generado_el".
       TINNIDROP y CLEARSTEM → solo "token_producto" nuevo y "generado_el" (su clave_campana
                       es igual a su producto_key).
     Si cambia cualquier otra cosa, DETENTE y reporta.
  4. git status --short → tuyos solo los 6 archivos (más los .json de _OPERADOR/LIMPIEZA/).
     No debe aparecer ningún _PUBLICACION_F*.json nuevo ni cambios en PRODUCTOS/.
  5. Commit en la rama actual, solo esos 6 archivos, sin push, sin atribución:
     git commit -m "fix(publicacion): one product token for Meta names across package, gate and activation"

SI ALGO NO CUADRA (importar gen_lanzador tiene efectos, un test viejo compara nombres armados
  con producto_key, la foto de TINNIDROP o CLEARSTEM cambia nombres): DETENTE y reporta.

ENTREGA: chequeos 1 a 4, el hash del commit, y de las fotos de OVULOS_PURITY: la línea de
  "manifiesto" → "campana" de antes y de después.
```

#### PARTE 2C-2 — EL PAQUETE SEGMENTA AL PAÍS DEL MERCADO Y PRESUPUESTA EN LA MONEDA DE LA CUENTA

No pasar hasta que Claude verifique la 2C-1. Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: en gen_publicacion.py, que el país del conjunto salga del mercado del producto y que una
cuenta que no factura en USD reciba el presupuesto convertido a su moneda, en vez de bloquear.

Archivos que puedes modificar (SOLO estos 3):
  Ads/_TOOLS/gen_publicacion.py
  Ads/_TOOLS/test_gen_publicacion.py
  Ads/_TOOLS/test_flujo.py        (SOLO el fixture `fixture_escalar_flaco`: ver PASO 3)
PROHIBIDO: tocar PRODUCTOS/, DOCTRINA/, .claude/, gen_lanzador.py, mercado.py, flujo.py.
Mismas prohibiciones de ejecución que la 2C-1 (siempre --solo-paquete; nada de Meta).

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.
  3. Fotos de antes: los mismos 3 comandos de la 2C-1, en _OPERADOR/LIMPIEZA/2C2_antes_<PK>.json.

PASO 1 — país
  a. Import de mercado.py (mismo patrón que el resto de imports locales del archivo).
  b. En main(), después de `tok = token_producto(prod)`:
         try:
             pais = mercado.mercado_de_fila(prod)
         except mercado.MercadoError as e:
             pq.bloquear_paquete(str(e), "operador · _DIM_PRODUCTOS.csv columna mercado")
             pais = None
     Si `pq` todavía no existe en ese punto, ubica este bloque inmediatamente después de que se
     cree `pq`.
  c. En `targeting`: "geo_locations": {"countries": [pais or "{{FALTA_PAIS}}"]}.
     Comentario de una línea: el código de mercado (GT, CO) es el código de país ISO que usa Meta.
  d. En el dict `paquete`, después de "token_producto", agrega "pais": pais.
  NO agregues ningún valor por defecto: un producto sin mercado bloquea el paquete.

PASO 2 — moneda de la cuenta
  a. Constante de módulo:
         # Unidades menores por unidad de moneda en el daily_budget de Meta. COP va en pesos
         # enteros: el mínimo diario medido de las cuentas COP es 3154 (~1 USD) en
         # _DIM_CUENTAS.csv.min_daily_budget_cents.
         UNIDAD_MENOR = {"USD": 100, "COP": 1}
  b. Reemplaza el bloque que hoy bloquea `if moneda != "USD":` (y su `else`) por esta lógica,
     conservando el chequeo del mínimo:
       - moneda_prod = _DIM_PRODUCTOS.moneda del producto, sin espacios y en mayúsculas.
         Si no está vacía y es distinta de la moneda de la cuenta → bloquear_publicacion(
           "la cuenta %s factura en %s y _DIM_PRODUCTOS.moneda de %s dice %s",
           "operador · _DIM_PRODUCTOS.csv columna moneda o la cuenta asignada").
       - Si la moneda de la cuenta no está en UNIDAD_MENOR → bloquear_publicacion(
           "la moneda %s de la cuenta %s no tiene unidad menor declarada",
           "Ads/_TOOLS/gen_publicacion.py UNIDAD_MENOR") y presu_cents = None.
       - Si no: valor, _ = gen_lanzador.monto_cuenta(presu_usd, moneda, tasa_del_producto)
         (tasa_del_producto = la columna `tasa` de _DIM_PRODUCTOS como número, None si vacía).
         valor None → bloquear_publicacion("tasa sin declarar: no se puede convertir el
           presupuesto a %s", "operador · _DIM_PRODUCTOS.csv columna tasa") y presu_cents = None.
         Si no → presu_cents = int(round(valor * UNIDAD_MENOR[moneda])).
       - Con presu_cents calculado, el chequeo `presu_cents < minimo` queda igual que hoy.
     Para una cuenta USD el resultado tiene que ser idéntico al de hoy (2.99 → 299).

PASO 3 — fixtures sin mercado
  Los fixtures de test_gen_publicacion.py (`_fixture_producto_sin_cuenta`,
  `_fixture_fase1_completa`) y `fixture_escalar_flaco` de test_flujo.py escriben el producto con
  las columnas vacías: con el PASO 1 bloquearían. Agrega `mercado="GT"` a la fila del producto
  en cada uno (si el encabezado del fixture no tiene la columna `mercado`, agrégala). Nada más en
  test_flujo.py.

PASO 4 — tests nuevos en test_gen_publicacion.py (regístralos en main())
  - Agrega a `_fixture_fase1_completa` parámetros opcionales `mercado="GT"`, `moneda=""`,
    `tasa=""`, `cuenta="GTR 7"` que se escriben en la fila de PX, y uno `cuenta_extra=None`
    que, si viene un dict, se agrega como fila a la copia de _DIM_CUENTAS.csv del fixture
    (escritor CSV real, mismas columnas).
  - test_targeting_usa_el_pais_del_mercado: mercado="CO" → en cada llamada ads_create_ad_set,
    json.loads(args["targeting"])["geo_locations"]["countries"] == ["CO"] y paquete["pais"] == "CO".
  - test_sin_mercado_bloquea_el_paquete: mercado="" → hay un bloqueante de ámbito "paquete" cuyo
    `lo_produce` menciona "columna mercado".
  - test_cuenta_en_cop_presupuesta_en_pesos: cuenta_extra = {"cuenta_alias": "CO TEST",
    "cuenta_id": "999", "moneda": "COP", "min_daily_budget_cents": "3154", "mcp_habilitado": "SI",
    "tiene_metodo_pago": "SI", "sube_media_local": "NO", "estado_cuenta": "ACTIVE"} (resto vacío),
    cuenta="CO TEST", mercado="CO", moneda="COP", tasa="3152.5" → paquete["daily_budget_cents"]
    == 9426 y ningún bloqueante contiene "factura en".
  - test_moneda_del_producto_distinta_a_la_cuenta_bloquea: misma cuenta COP pero moneda="USD"
    → hay un bloqueante de ámbito "publicacion" que contiene "factura en COP".
  - test_cuenta_usd_sigue_en_centavos: el fixture por defecto → daily_budget_cents == 299.

CHEQUEOS FINALES
  1. python Ads/_TOOLS/test_gen_publicacion.py y python Ads/_TOOLS/test_flujo.py → sin fallas.
  2. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  3. Fotos de después en _OPERADOR/LIMPIEZA/2C2_despues_<PK>.json y diff contra las de antes.
     Esperado: aparece "pais" (OVULOS_PURITY "CO"; TINNIDROP y CLEARSTEM "GT"); en OVULOS el
     targeting pasa de ["GT"] a ["CO"]; cambia "generado_el". TINNIDROP y CLEARSTEM conservan
     "daily_budget_cents" igual que antes. Cualquier otro cambio: DETENTE y reporta.
  4. git status --short → tuyos solo los 3 archivos (más los .json de _OPERADOR/LIMPIEZA/).
  5. Commit, solo esos 3 archivos, sin push, sin atribución:
     git commit -m "feat(publicacion): target the product market and budget in the account currency"

SI ALGO NO CUADRA (mercado_de_fila falla para un producto real, un test viejo de otro archivo
  depende de "GT" fijo, la conversión de USD cambia un valor): DETENTE y reporta.

ENTREGA: chequeos 1 a 4, el hash del commit y el diff de la foto de OVULOS_PURITY.
```

2C-1 HECHA (commit `16355ee`) y 2C-2 HECHA (commit `bc4d3fe`), verificadas por Claude: pytest 56;
el paquete de OVULOS sale `EXTERNA_OVULOSPURITY_TEST_…`, conjuntos `EXTERNA_OVULOSPURITY_<ÁNGULO>_R2`
(R2 porque la R1 ya existe), país CO, 299 centavos con la cuenta en USD.

#### PARTE 2C-3 — REDISEÑO CON LOS EXPORTS (30-sep)

Con los dos exports con identificadores, Claude midió qué aporta cada pieza y cambió el plan:

| Pieza | Decisión | Por qué |
|---|---|---|
| Moneda de la cuenta de OVULOS (COP → USD) | **2C-3A, urgente** | `ingerir_meta.py` toma la divisa de `_DIM_PRODUCTOS.moneda` cuando el export no trae columna «Divisa» (el de EXTERNA no la trae: dice «Importe gastado (USD)»), e `ingerir_lucidsales.py` hace lo mismo con el gasto de una cuenta EXTERNA. Con COP, el gasto real en dólares se dividiría por 3152,5: el CPA de OVULOS saldría casi en cero en la primera carga. Hoy OVULOS tiene 0 filas cargadas: todavía no hizo daño |
| Registrar EXTERNA en `_DIM_CUENTAS.csv` | **No se hace** | `bajar_meta_insights.py` descarga cada noche toda cuenta ACTIVE con método de pago: la intentaría sin id y sin acceso. El modo manual de CO ya está diseñado sin esa fila (skill `recopilar-lucidsales`, «MERCADO CO (MANUAL)») |
| Un solo dueño del nombre de anuncio y de la réplica | **2C-3B** (se diseña tras verificar la 2C-3A) | Formato `IMG`/`IMA` y destino `BOT_Vn`/`?` difieren entre lanzador y paquete; `siguiente_replica` cuenta las filas que `etapa-guardar-producto` escribe ANTES de publicar, así que la primera publicación de un producto sale `_R2` y el lanzador dice `_R1` |
| Verificar una publicación manual y guardar sus `ad_id` | **Pendiente, sin valor hoy** | Ningún producto tiene filas de FASE 1 en `_DIM_CREATIVOS.csv`: aun por MCP, `verificar_publicacion.py --escribir` no tiene dónde guardar un `ad_id` de FASE 1. La medición de CO va por nombre (`ingerir_meta.py`) y eso ya funciona |

#### PARTE 2C-3A — LA MONEDA DE LA CUENTA DE OVULOS PASA A USD

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: crear el escritor que corrige la columna `moneda` (moneda de la CUENTA publicitaria) de
un producto que ya tiene fila, y usarlo para pasar OVULOS_PURITY de COP a USD.
Evidencia: el export de Ads Manager de su cuenta dice «Importe gastado (USD)».

Archivos que puedes crear o modificar (SOLO estos):
  Ads/_TOOLS/cargar_moneda_cuenta.py         (nuevo)
  Ads/_TOOLS/test_cargar_moneda_cuenta.py    (nuevo)
  Ads/_TOOLS/editar_producto.py              (solo la lista de escritores del docstring)
  Ads/_TOOLS/cargar_cuenta.py                (solo el aviso de la línea ~73, ver PASO 3)
  Ads/_TOOLS/test_gen_lanzador.py            (solo test_plan_real_de_ovulos, ver PASO 5)
  y, a través del escritor nuevo (nunca a mano), la fila de OVULOS_PURITY en
  PRODUCTOS/_DIM_PRODUCTOS.csv y su espejo en Postgres.
PROHIBIDO: editar _DIM_PRODUCTOS.csv con un editor o con csv.DictWriter directo (es espejo de
  Postgres: el próximo escritor legítimo lo rechaza por drift). Tocar _DIM_CUENTAS.csv,
  `tasa`, cualquier otra columna u otro producto. Tocar DOCTRINA/, .claude/.
Comandos desde la raíz, de a uno. En PowerShell: $env:PYTHONIOENCODING="utf-8".

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.
  3. python Ads/_TOOLS/test_gen_lanzador.py → "0 fallas."
  4. Lee completos Ads/_TOOLS/cargar_page_id.py, Ads/_TOOLS/test_cargar_page_id.py y las
     funciones de editar_producto.py que usan (buscar_producto, fila_dict, csv_con_cambios,
     es_pendiente, argumentos_comunes, ejecutar, lineas_de_cambios, lineas_de_avisos).
     El escritor nuevo es una copia de ese patrón para UNA columna.

PASO 1 — Ads/_TOOLS/cargar_moneda_cuenta.py (mismo patrón que cargar_page_id.py)
  Docstring: qué escribe (SOLO la columna `moneda` de la fila del producto en
  _DIM_PRODUCTOS.csv; no hay encabezados de TXT que la lleven), qué bloquea, qué avisa, uso.
  Regla vigente, sin historia. Debe decir que `moneda` es la moneda con que Meta COBRA la cuenta
  publicitaria (no la de venta, que es del mercado).
  planear(args):
    - moneda = args.moneda sin espacios y en MAYÚSCULAS.
    - Rechazo si no es un código conocido: el conjunto de valores de la columna `moneda` de
      PRODUCTOS/_DIM_CUENTAS.csv unido al de PRODUCTOS/_DIM_MERCADOS.csv (léelos, no los
      escribas fijos). Mensaje: qué valores valen.
    - Rechazo si la cuenta del producto (cuenta_alias, comparada sin espacios y en mayúsculas)
      ESTÁ en _DIM_CUENTAS.csv y su moneda es otra: «la moneda la dicta la cuenta <alias>
      (<moneda>); si cambió de cuenta, eso es cargar_cuenta.py».
    - Rechazo si el producto ya tiene una moneda distinta y no vino --reemplazar.
    - Aviso (no bloquea) si moneda != "USD" y la columna `tasa` del producto está vacía.
    - Escritura: ep.csv_con_cambios(encabezado, filas, indice, {"moneda": moneda}) sobre
      PRODUCTOS/_DIM_PRODUCTOS.csv. Sin cambios si ya tiene esa moneda.
  CLI: --producto, --moneda (requerido), --reemplazar, más ep.argumentos_comunes
  (--dry-run, --json, --base). main() con ep.ejecutar(...), igual que cargar_page_id.
  Siguiente paso que imprime: python Ads/_TOOLS/gen_manual.py <PK> --validar

PASO 2 — editar_producto.py
  En la lista de escritores del docstring agrega una línea:
      cargar_moneda_cuenta.py   moneda (de la cuenta publicitaria)

PASO 3 — cargar_cuenta.py
  El aviso «<alias> factura en <moneda>: gen_publicacion.py bloquea la publicacion hasta que el
  presupuesto se derive en esa moneda» ya no es cierto. Reemplázalo por:
      f"{alias} factura en {cuenta['moneda']}: el presupuesto se convierte con la tasa del producto (columna tasa)."
  No cambies nada más de ese archivo.

PASO 4 — Ads/_TOOLS/test_cargar_moneda_cuenta.py
  Mismo estilo y mismos fixtures temporales que test_cargar_page_id.py (base temporal, Postgres
  de pruebas como allí). Tests:
    - una moneda desconocida («ABC») se rechaza;
    - producto con cuenta en _DIM_CUENTAS en USD y pedido COP → rechazo que nombra la cuenta;
    - producto con cuenta que NO está en _DIM_CUENTAS (alias EXTERNA), moneda COP, pedido USD
      sin --reemplazar → rechazo; con --reemplazar → la fila queda en USD y ninguna otra
      columna ni fila cambia;
    - pedir la misma moneda que ya tiene → «sin cambios», no escribe;
    - --dry-run no toca el disco.
  Si los fixtures de test_cargar_page_id.py dependen de Postgres y se saltan sin él, haz lo mismo.

PASO 5 — aplicar a OVULOS_PURITY (es el único cambio de datos de la tarea)
  a. python Ads/_TOOLS/cargar_moneda_cuenta.py --producto OVULOS_PURITY --moneda USD --reemplazar --dry-run
     Debe listar UN cambio: moneda COP → USD. Si lista otra cosa, DETENTE.
  b. El mismo comando sin --dry-run. Debe terminar con exit 0.
  c. git diff PRODUCTOS/_DIM_PRODUCTOS.csv → cambia SOLO el valor COP→USD en la fila de
     OVULOS_PURITY (puede variar el fin de línea si el escritor normaliza: repórtalo).
  d. En test_gen_lanzador.py, test_plan_real_de_ovulos: la expectativa "COP" pasa a "USD" y la de
     textos que terminan en " COP" pasa a textos que empiezan con "US$". Nada más.

CHEQUEOS FINALES
  1. python Ads/_TOOLS/test_cargar_moneda_cuenta.py → sin fallas.
  2. python Ads/_TOOLS/test_gen_lanzador.py → "0 fallas."
  3. python -m pytest Ads/_TOOLS -q → 57 passed, 0 failed (un archivo de test nuevo).
  4. python Ads/_TOOLS/gen_publicacion.py --producto OVULOS_PURITY --fase 1 --solo-paquete --json
     → ningún bloqueante contiene «factura en».
  5. python Ads/_TOOLS/gen_manual.py OVULOS_PURITY → exit 0; contiene «US$2.99/día» y
     «Total del día: US$17.94»; no contiene «COP/día».
  6. python Ads/_TOOLS/verificar_producto.py OVULOS_PURITY → PASA.
  7. git status --short → tuyos: los 5 archivos de código y PRODUCTOS/_DIM_PRODUCTOS.csv.
  8. Dos commits en la rama actual, sin push, sin atribución:
     git add Ads/_TOOLS/cargar_moneda_cuenta.py Ads/_TOOLS/test_cargar_moneda_cuenta.py Ads/_TOOLS/editar_producto.py Ads/_TOOLS/cargar_cuenta.py
     git commit -m "feat(producto): writer for the ad account currency of an existing product"
     git add PRODUCTOS/_DIM_PRODUCTOS.csv Ads/_TOOLS/test_gen_lanzador.py
     git commit -m "fix(ovulos): its ad account bills in USD, not COP"
     ATENCIÓN: _DIM_PRODUCTOS.csv ya tenía cambios del operador sin commitear antes de esta
     tarea. Si `git diff PRODUCTOS/_DIM_PRODUCTOS.csv` muestra más líneas que la tuya, NO hagas
     el segundo commit con ese archivo: haz el commit solo con test_gen_lanzador.py y repórtalo.

SI ALGO NO CUADRA (el escritor rechaza por drift de Postgres, Postgres no está disponible, el
  dry-run lista más de un cambio, un test viejo fija COP para OVULOS en otro archivo): DETENTE,
  no edites el CSV a mano, y reporta.

ENTREGA: chequeos 1 a 7, los hashes y la salida del dry-run del PASO 5a.
```

#### 2C-3A — CONTINUACIÓN TRAS EL BLOQUEO POR DRIFT (30-sep)

La ejecutora se detuvo bien en el PASO 5b: Postgres tenía la fila v1 de OVULOS (sin page_id ni
precios) y el CSV la v2 vigente, cargada sin escritor. Claude verificó con `git diff` que la única
diferencia es esa fila y que la v2 es la correcta. Decisión: el CSV es la verdad.

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: sincronizar Postgres con el CSV de productos y terminar la 2C-3A desde el PASO 5b.

1. git diff --stat PRODUCTOS/_DIM_PRODUCTOS.csv → 1 archivo, 1 inserción, 1 borrado (la fila v2
   de OVULOS_PURITY). Si hay más, DETENTE.
2. Con el python del entorno de la app (el mismo que usan los escritores):
     "..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py --tomar-csv _DIM_PRODUCTOS.csv
   Si esa ruta no existe, usa el python con el que corriste test_cargar_moneda_cuenta.py y dilo.
   Debe terminar sin error. No toca el CSV: solo la base.
3. Sigue la guía de la 2C-3A desde el PASO 5b (el comando sin --dry-run), luego 5c, 5d, los
   chequeos finales 1 a 7 y los dos commits.
   En el PASO 5c el diff de _DIM_PRODUCTOS.csv contra HEAD va a mostrar la fila v2 completa con
   moneda USD (la v2 nunca se commiteó): eso es lo esperado. El segundo commit lleva
   _DIM_PRODUCTOS.csv y test_gen_lanzador.py, con este mensaje en lugar del de la guía:
     git commit -m "fix(ovulos): record the v2 product row and its USD ad account currency"

SI ALGO NO CUADRA (tomar-csv falla, el escritor vuelve a rechazar por drift, el diff trae otros
  productos): DETENTE y reporta.

ENTREGA: la salida del paso 2, los chequeos 1 a 7 de la 2C-3A y los hashes.
```

2C-3A HECHA (commits `7fe5e58` y `7b16d33`, verificada: la fila de OVULOS queda v2 con moneda USD,
Postgres sincronizado, pytest 57).

## PAQUETE 4 — BORRAR LO MUERTO, QUITAR PUNTEROS VIEJOS Y UN SOLO DUEÑO DE LOS NOMBRES

Medición de Claude (30-sep, auditoría de solo lectura + `gen_grafo.py`): el repo casi no tiene
archivos muertos (3 scripts y 1 informe). Lo que pesa es lo que lee cada fase: FASE 2 ~343k
tokens, FASE 1 ~260k. Por eso este paquete junta cuatro tareas independientes, cada una con su
commit: si una se detiene, las anteriores quedan hechas.

Copiar el bloque COMPLETO y pasárselo a la IA ejecutora.

```
TAREA: cuatro tareas en orden (T1 → T4). Cada una termina con su propio commit. Si una tarea
se detiene por su condición de parada, NO sigas con las siguientes: reporta lo hecho hasta ahí.
Reglas comunes: comandos desde la raíz, de a uno; en PowerShell $env:PYTHONIOENCODING="utf-8";
para guardar salidas con tildes usa python con subprocess y encoding utf-8 (como ya hiciste).
Nunca push, nunca atribución en los commits, nunca tocar PRODUCTOS/ ni llamar a Meta.
Antes de T1: git status --short Ads/_TOOLS .claude → vacío; python -m pytest Ads/_TOOLS -q → 57 passed.

═══ T1 — BORRAR CÓDIGO MUERTO ═══
Archivos: borrar Ads/_TOOLS/gen_sistema.py, Ads/_TOOLS/check_huella.py,
  Ads/_TOOLS/escribir_fichas.py, Ads/_SWIPE/_AUDITORIA_2026-08-18.md; quitar de .gitignore
  la línea que menciona gen_sistema o su salida _SISTEMA.html.
1. Para cada uno: rg -n "<nombre sin extensión>" Ads .claude DOCTRINA app db evals warehouse CLAUDE.md
   Se permiten menciones solo en documentos de handoff (_HANDOFF*.md) y en
   Ads/_SWIPE/_BLUEPRINTS/_datos/tanda01.py. Si tanda01.py o cualquier .py lo IMPORTA (import /
   from ... import / subprocess que lo ejecute), DETENTE: no es muerto.
2. git rm de los 4 archivos y la edición de .gitignore.
3. python -m pytest Ads/_TOOLS -q → 57 passed.
4. git commit -m "chore(limpieza): remove dead scripts and a stale dated report"

═══ T2 — PUNTEROS VIEJOS A CLAUDE.md DENTRO DE LAS ETAPAS ═══
Por qué: las etapas ya no cargan CLAUDE.md (traen la skill reglas-sistema). Un puntero
«regla 6 de CLAUDE.md» las manda a leer un archivo de ~6k tokens, y además esas «reglas N» ya no
existen con ese número. Reemplazos LITERALES (busca el texto ANTES exacto; si no aparece tal
cual, DETENTE y reporta cuál):
  .claude/agents/ETAPA-6.md
    ANTES: (la crea el orquestador justo después de ETAPA-0 — ver CLAUDE.md PASO 1.5, independiente del MCP)
    DESPUÉS: (la crea el orquestador justo después de ETAPA-0, independiente del MCP)
    ANTES: "amplio 18-65+" de `CLAUDE.md`.
    DESPUÉS: "amplio 18-65+" de `reglas-sistema` (SEGMENTACIÓN).
    ANTES: (regla 6 de `CLAUDE.md`)
    DESPUÉS: (invariante 1 de `reglas-sistema`)
    ANTES: esta regla y la de CLAUDE.md nº 9.
    DESPUÉS: esta regla.
  .claude/agents/ETAPA-11.md
    ANTES: (`CLAUDE.md` → PRINCIPIO DE ALCANCE DEL COMPLIANCE)
    DESPUÉS: (`reglas-sistema` → ALCANCE DEL COMPLIANCE)
    ANTES: (regla 6 de `CLAUDE.md`).
    DESPUÉS: (invariante 1 de `reglas-sistema`).
  .claude/agents/ETAPA-10.md
    ANTES: regla 6 de `CLAUDE.md` (agregar por
    DESPUÉS: invariante 1 de `reglas-sistema` (agregar por
  .claude/agents/ETAPA-9.md
    ANTES: (regla 22 de `CLAUDE.md`: campos de texto libre con comas entre comillas dobles)
    DESPUÉS: (invariante 11 de `reglas-sistema`: campos de texto libre con comas entre comillas dobles)
  .claude/agents/ETAPA-3.md
    ANTES: (CLAUDE.md regla lite de barreras #10; Clase 22 "no reducir fricciones mata la venta")
    DESPUÉS: (Clase 22: "no reducir fricciones mata la venta")
    ANTES: = avatar ultra-específico (CLAUDE.md).
    DESPUÉS: = avatar ultra-específico (`reglas-sistema`, DEFINICIONES CLAVE).
  .claude/agents/ETAPA-1.md
    ANTES: Vale para TODO producto nuevo. Movida desde `CLAUDE.md` — **este archivo es el dueño.**
    DESPUÉS: Vale para TODO producto nuevo. **Este archivo es el dueño.**
  .claude/agents/ETAPA-RENDER.md
    ANTES: (invariante 4 de `CLAUDE.md`)
    DESPUÉS: (invariante 4 de `reglas-sistema`)
  .claude/agents/ETAPA-GUARDAR-PRODUCTO.md
    ANTES: ## Entrega de ejecución en el chat (default — CLAUDE.md regla 19)
    DESPUÉS: ## Entrega de ejecución en el chat (default — preferencia del operador)
  .claude/skills/generar-conceptos/SKILL.md
    ANTES: que es exactamente lo que `CLAUDE.md` prohíbe
    DESPUÉS: que es exactamente lo que `reglas-sistema` prohíbe
    ANTES: Ver `CLAUDE.md` →
    DESPUÉS: Ver `reglas-sistema` →
  .claude/skills/generar-imagenes-chatgpt/SKILL.md
    ANTES: (invariante 8 de `CLAUDE.md`)
    DESPUÉS: (invariante 8 de `reglas-sistema`)
  NO toques .claude/skills/fase-3-flujo/SKILL.md ni .claude/skills/reglas-sistema/ (la primera la
  lee el orquestador, que sí tiene CLAUDE.md; la segunda es generada).
  ATENCIÓN: .claude/skills/generar-imagenes-chatgpt/SKILL.md ya tenía cambios del operador sin
  commitear. Si `git diff` de ese archivo muestra más que tu línea, NO lo incluyas en el commit:
  deja tu cambio en disco y repórtalo.
Chequeos:
  a. rg -n "CLAUDE\.md" .claude/agents → solo puede quedar ETAPA-RENDER/otros si mencionan
     CLAUDE.md sin número de regla; pega lo que quede.
  b. rg -n "regla (6|9|19|22) de|regla lite|PASO 1\.5" .claude → 0 resultados.
  c. python -m pytest Ads/_TOOLS -q → 57 passed. python evals/run_baseline.py → TOTAL=28 PASS=27
     FALLO-CONOCIDO=1 FAIL=0.
  d. git commit (solo los archivos de .claude que tocaste) -m "docs(etapas): point stage rules to reglas-sistema instead of stale CLAUDE.md numbers"

═══ T3 — LA SKILL publicar-meta DOCUMENTA LA SUBIDA POR BIBLIOTECA ═══
Archivo: .claude/skills/publicar-meta/SKILL.md. Inserta, inmediatamente ANTES de la línea que
empieza con «Si una llamada falla, **parar ahí**.», este bloque (con una línea en blanco antes
y otra después):

#### Cuenta sin subida local: `--media biblioteca`

En toda cuenta con `sube_media_local=NO` la media va por la biblioteca de la cuenta, nunca con
`LOCAL_FILE`:

1. `ads_get_ad_images` de la cuenta → guardar `{"imagenes":[{"hash","name"}]}` en
   `Ads/_INGESTA/META/imagenes_antes_[ALIAS].json`.
2. Regenerar con `--media biblioteca --imagenes-antes Ads/_INGESTA/META/imagenes_antes_[ALIAS].json`:
   el bloqueante de ámbito `media` lista los nombres EXACTOS con que el operador sube cada pieza.
3. El operador sube a la biblioteca con esos nombres y avisa.
4. `ads_get_ad_images` otra vez → `Ads/_INGESTA/META/imagenes_despues_[ALIAS].json`, y regenerar
   con `--imagenes-antes` y `--imagenes-despues`: sin bloqueantes de `media`, cada creativo lleva
   su `image_hash` literal y no hay llamadas `ads_creative_upload_media`.

Chequeo: python -m pytest Ads/_TOOLS -q → 57 passed.
git commit -m "docs(publicar-meta): document the media library path for accounts without local upload"

═══ T4 — UN SOLO DUEÑO DEL NOMBRE DE ANUNCIO Y DE LA RÉPLICA (2C-3B) ═══
Problema medido: gen_lanzador.py (el manual) y gen_publicacion.py (el paquete) nombran distinto:
  formato  `IMG` (lanzador) vs `IMA` (paquete: formato[:3]);
  destino  `destino_actual()` (lanzador) vs `plan["destino_key"]` o `?` (paquete);
  réplica  `_R1` fijo (lanzador) vs `siguiente_replica()` (paquete), que cuenta también las
           filas que etapa-guardar-producto escribe en _DIM_CONJUNTOS ANTES de publicar: la
           primera publicación de un producto sale `_R2`.
Archivos (SOLO estos 4): Ads/_TOOLS/gen_lanzador.py, Ads/_TOOLS/test_gen_lanzador.py,
  Ads/_TOOLS/gen_publicacion.py, Ads/_TOOLS/test_gen_publicacion.py.
PROHIBIDO correr gen_lanzador.py por CLI o gen_publicacion.py sin --solo-paquete.

Antes: fotos read-only en _OPERADOR/LIMPIEZA/:
  T4_antes_lanzador.json  = json.dumps(gen_lanzador.construir(), sort_keys=True, indent=1)
  T4_antes_<PK>.json      = gen_publicacion.py --producto <PK> --fase 1 --solo-paquete --json
                            para OVULOS_PURITY, TINNIDROP y CLEARSTEM.

PASO 1 — gen_lanzador.py es el dueño. Agrega (docstrings con la regla vigente, sin historia):
  def token_formato(formato):
      """Token de formato del nombre del anuncio: IMG para IMAGEN (o vacío), VID para el resto."""
      → "IMG" if (formato or "IMAGEN").strip().upper() == "IMAGEN" else "VID"
  def destino_de(plan):
      """El eje destino de la firma: el que el plan declara (FASE 2 fija uno por brazo del A/B);
      si el plan no declara, la versión vigente del bot (destino_actual())."""
      → (plan.get("destino_key") or "").strip() or destino_actual()
  PATRON_REPLICA = re.compile(r"_R(\d+)$")
  def siguiente_replica(filas_conjuntos, pk, angulo, cta, nombres_meta=()):
      """El próximo R[N] para producto+ángulo+cuenta. Cuenta solo lo que consta publicado: las
      filas de _DIM_CONJUNTOS.csv con verificado_en_csv == "SI" y los nombres de un snapshot de
      Meta (nombres_meta). Una fila de diseño (verificado_en_csv NO) no ocupa número. Sin nada
      publicado, R1. La publicación siempre corre con snapshot, así que lo vivo nunca se reusa."""
      Reglas: filas con producto_key == pk, angulo_key == angulo, cuenta (sin espacios, mayúsculas)
      == cta y verificado_en_csv == "SI" → máximo R de su conjunto_meta. nombres_meta → para cada
      nombre que empiece con "%s_%s_%s_" % (cta, <token>, guion(angulo)) — usa el token del
      producto que recibas como parámetro extra `token` (agrega `token=None` a la firma; si es
      None no se cuentan nombres_meta) — máximo R. Devuelve máximo + 1.
  En derivar():
    - fmt = token_formato(c.get("formato"))
    - la firma usa destino_de(plan) en lugar de destino_actual()
    - el nombre del conjunto usa siguiente_replica(filas de _DIM_CONJUNTOS.csv, pk, ak, cta,
      token=prod_corto) en lugar del "_R1" fijo (lee _DIM_CONJUNTOS.csv una sola vez en
      construir() y pásalo a derivar como parámetro nuevo; ajusta la única llamada).

PASO 2 — gen_publicacion.py usa al dueño
  - Borra su PATRON_REPLICA y su siguiente_replica y en su lugar:
        from gen_lanzador import PATRON_REPLICA, siguiente_replica, token_formato, destino_de
    (los tests que llaman gp.siguiente_replica siguen funcionando por el import).
  - La llamada a siguiente_replica pasa además nombres_meta=list(existentes) y token=tok.
  - `fmt = (cre.get("formato") or "IMG")[:3].upper()` → `fmt = token_formato(cre.get("formato"))`.
  - Las dos asignaciones "destino_key": plan.get("destino_key") → "destino_key": destino_de(plan).

PASO 3 — tests
  test_gen_publicacion.py: los tests test_siguiente_replica_* arman filas sin
  verificado_en_csv; agrega "verificado_en_csv": "SI" a cada fila de esos fixtures (es la
  semántica nueva: solo cuenta lo publicado). No cambies sus expectativas. Si alguno sigue
  fallando, DETENTE. Tests nuevos:
    - test_fila_de_diseno_no_ocupa_numero: una fila verificado_en_csv "NO" con _R1 → devuelve 1.
    - test_snapshot_ocupa_numero: sin filas, nombres_meta=["GTR7_PX_ANG1_R3"], token="PX",
      angulo "ANG1", cta "GTR7" → devuelve 4.
  test_gen_lanzador.py:
    - test_token_formato: "IMAGEN"→"IMG", ""→"IMG", None→"IMG", "VIDEO"→"VID".
    - test_destino_de: {"destino_key": "BOT_V9"}→"BOT_V9"; {}→ lo mismo que destino_actual().
    - en test_plan_real_de_ovulos agrega: el primer conjunto termina en "_R1" y su primer
      anuncio contiene "_IMG_A ~ ".
  Registra los tests nuevos en el main() de cada archivo.

Chequeos de T4:
  a. python Ads/_TOOLS/test_gen_lanzador.py → 0 fallas; python Ads/_TOOLS/test_gen_publicacion.py → 0 fallas.
  b. python -m pytest Ads/_TOOLS -q → 57 passed.
  c. Fotos de después (mismos comandos) y diff contra las de antes. Esperado:
     paquete OVULOS_PURITY: conjuntos _R2 → _R1; anuncios _IMA_ → _IMG_ y destino ? → BOT_V3.
     paquetes TINNIDROP y CLEARSTEM: _IMA_ → _IMG_ en anuncios; destino ? → BOT_V3 SOLO si su
       plan no declaraba destino_key; la réplica puede cambiar SOLO si había filas de diseño
       (verificado_en_csv NO) de ese ángulo y cuenta — lista cada cambio de réplica con la fila
       de _DIM_CONJUNTOS que lo explica.
     lanzador: los nombres de conjunto pasan de _R1 fijo a la réplica calculada; lista CADA
       producto/ángulo donde ya no es _R1 con la fila verificada que lo explica.
     Cualquier otro cambio: DETENTE y reporta.
  d. git commit (los 4 archivos) -m "refactor(nombres): one owner for ad name format, bot destination and replica numbering"

ENTREGA FINAL: por cada tarea, sus chequeos y su hash; de T2 la salida del chequeo a; de T4 el
  resumen del diff de fotos (c) con cada cambio de réplica explicado.
```

PAQUETE 4 HECHO (commits `83213d0`, `ed79673`, `f8d57fa`, `31b2732`), verificado por Claude:
pytest 57; el paquete de OVULOS nombra `EXTERNA_OVULOSPURITY_<ÁNGULO>_R1` y
`<ÁNGULO>_IMG_A ~ …|BOT_V3`; `siguiente_replica`, `token_formato` y `destino_de` viven solo en
`gen_lanzador.py`; 680 líneas muertas fuera.

## PAQUETE 5 — CIERRE: ÚLTIMOS RESTOS Y GUARDAR TODO EL TRABAJO EN GIT

Hay trabajo real del operador sin commitear (el paquete v2 de OVULOS, sus bloques del bot,
infografías, data del sistema, informes de LucidSales). Una sesión que cambie de rama en este
mismo checkout puede borrarlo. Este paquete lo deja guardado en commits locales (sin push).

Copiar el bloque COMPLETO y pasárselo a la IA ejecutora.

```
TAREA: tres tareas en orden. Mismas reglas comunes del PAQUETE 4 (cada tarea su commit, sin
push, sin atribución, si una se detiene no sigas).

═══ T1 — ÚLTIMOS PUNTEROS VIEJOS ═══
.claude/skills/generar-conceptos/SKILL.md, reemplazos literales:
  ANTES: (regla 22 del orquestador)   DESPUÉS: (invariante 11 de `reglas-sistema`)
  ANTES: (regla 6 del orquestador)    DESPUÉS: (invariante 1 de `reglas-sistema`)
  ANTES: (regla 19 del orquestador)   DESPUÉS: (preferencia del operador)
Chequeo: rg -n "regla [0-9]+ del orquestador" .claude → 0. pytest Ads/_TOOLS -q → 57 passed.
git commit -m "docs(conceptos): point the last stale rule numbers to reglas-sistema"

═══ T2 — RESTOS EN DISCO ═══
  a. Ads/_SWIPE/_SISTEMA.html (sin seguimiento) es la salida de gen_sistema.py, que ya no existe:
     bórralo.
  b. backups_csv/ en la raíz (sin seguimiento): lista su contenido y busca quién lo crea
     (rg -n "backups_csv" Ads/_TOOLS db app). Muévelo entero a _RESPALDOS/backups_csv_raiz/
     (_RESPALDOS/ está en .gitignore). No lo borres. Si un script del sistema escribe en la raíz
     backups_csv/ en vez de _RESPALDOS/, NO lo corrijas: anota archivo y línea en la entrega.
  Sin commit (nada de esto está en git).

═══ T3 — GUARDAR EL TRABAJO PENDIENTE EN COMMITS ═══
NUNCA agregues: .agents/, .codex/, .claude/launch.json, .claude/settings.local.json.
Para cada grupo: git add <rutas del grupo>; git diff --cached --stat → solo deben aparecer
rutas del grupo (si aparece otra, git restore --staged y DETENTE); git commit.
  a. git add PRODUCTOS/OVULOS_PURITY
     git commit -m "docs(ovulos): v2 product package with bot blocks, infographics and flow"
  b. git add -A PRODUCTOS/_AUDITORIAS
     git commit -m "chore(auditorias): archive August daily audits by month"
  c. git add Ads/_INGESTA/LUCIDSALES
     git commit -m "chore(data): LucidSales reports up to 28-sep"
  d. PRODUCTOS/_VOZ_CLIENTE.csv y PRODUCTOS/_CORRIDAS_DIARIAS.csv están sin seguimiento: para
     cada uno, rg -n "<nombre>" Ads/_TOOLS. Inclúyelo en este grupo SOLO si un script del
     sistema lo lee o lo escribe; si no, déjalo fuera y repórtalo.
     git add PRODUCTOS/*.csv PRODUCTOS/*.json VISTAS (más los de d que correspondan)
     git commit -m "chore(data): system data and generated views as of 30-sep"
  e. git add .claude/skills/generar-imagenes-chatgpt/SKILL.md
     git commit -m "docs(render): market registration values and reglas-sistema pointer"
  f. git add _OPERADOR odd/tasks
     git commit -m "docs(operador): cleanup roadmap, executor guides and task notes"
Chequeo final: git status --short → solo pueden quedar .agents/, .codex/,
  .claude/launch.json y .claude/settings.local.json (y lo que d dejó fuera).

ENTREGA: hash de T1, qué contenía backups_csv/ y quién lo escribe, los hashes de T3 a–f y el
  git status final.
```

#### PARTE 2C-3 (anterior) — PUBLICACIÓN MANUAL VERIFICADA

Para cuentas sin MCP (hoy EXTERNA): que el paquete exista igual como manifiesto, que el operador
publique a mano contra él y que el gate compare contra un volcado de Ads Manager y escriba los
`ad_id`. También: la skill `publicar-meta` no documenta `--media biblioteca`; `cargar_cuenta.py:73`
todavía avisa que una cuenta no-USD se bloquea.

Datos que ya hay (exports de Ads Manager del operador, 30-sep, cuenta «4 CUENTA DE VERDA»):

- La cuenta EXTERNA **factura en USD** (columna «Importe gastado (USD)», presupuesto 3 por
  conjunto). `_DIM_PRODUCTOS.moneda` de OVULOS dice COP: el bloqueante que dio la 2C-2 contra la
  fila provisoria era correcto, y el «$9.426 COP» del manual generado está mal (es US$2.99). Hay
  que registrar EXTERNA en `_DIM_CUENTAS.csv` (moneda USD, `mcp_habilitado` NO) y corregir
  `moneda` del producto, revisando antes qué otros lectores usan esa columna.
- El export trae «Identificador de la campaña» pero no el del conjunto ni el del anuncio: para el
  gate hacen falta los tres (se agregan como columnas en Ads Manager).
- El nombre del ANUNCIO tiene dos dueños, igual que tenía el producto: `gen_lanzador.py` arma
  `_IMG_` y el destino `BOT_V2` (de los `CAMBIO_BOT`); `gen_publicacion.py` arma `_IMA_`
  (`formato[:3]`) y el destino `?` (de `_PLAN.json`). En Meta quedó lo del lanzador.
- En Meta hay 4 anuncios terminados en « - Copia» y 4 en « (copia exacta)», en vez del par A/B
  (invariante 12).

## PARTE 3A — LOS SUBAGENTES DEJAN DE HEREDAR LOS CLAUDE.md

Hechos verificados en la documentación de Claude Code (30-sep-2026):
- Cada subagente carga TODA la jerarquía de CLAUDE.md: el global (`~/.claude/CLAUDE.md`, ~18.300
  tokens, instrucciones de orquestador que a una etapa no le aplican) y el del proyecto (~6.300).
  Son ~24.600 tokens por subagente; una FASE 2 lanza unos 12.
- `omitClaudeMd: true` en el frontmatter del agente evita esa carga (Claude Code ≥ 2.1.271;
  instalado 2.1.278).
- `skills:` en el frontmatter precarga el contenido completo de una skill al arrancar el subagente.

Diseño: `CLAUDE.md` NO se toca (la sesión principal queda igual). Las CONSTANTES y los INVARIANTES
se copian con un generador a una skill derivada que se precarga en las 15 etapas. `CLAUDE.md` sigue
siendo el dueño; un test falla si la copia se desincroniza.

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: que los 15 subagentes de etapa dejen de cargar los CLAUDE.md y reciban solo las
CONSTANTES y los INVARIANTES del sistema, por una skill generada.

Archivos que puedes crear o modificar (SOLO estos):
  Ads/_TOOLS/gen_reglas_etapas.py            (nuevo)
  Ads/_TOOLS/test_gen_reglas_etapas.py       (nuevo)
  .claude/skills/reglas-sistema/SKILL.md     (nuevo; lo ESCRIBE el generador, no tú a mano)
  .claude/agents/ETAPA-*.md                  (los 15; SOLO el frontmatter, 3 líneas nuevas)
  Ads/_TOOLS/gen_grafo.py                    (2 cambios puntuales)
PROHIBIDO tocar: CLAUDE.md, ~/.claude/CLAUDE.md, .claude/settings*.json, el CUERPO de cualquier
  agente (todo lo que va después del segundo `---`), DOCTRINA/, PRODUCTOS/.

ANTES DE EMPEZAR
  1. git status --short .claude/agents Ads/_TOOLS/gen_grafo.py → vacío. Si no, DETENTE y avisa.
  2. python -m pytest Ads/_TOOLS -q → 54 passed.
  3. Foto de antes: python Ads/_TOOLS/gen_grafo.py > _OPERADOR/LIMPIEZA/3A_antes_grafo.txt

PASO 1 — Ads/_TOOLS/gen_reglas_etapas.py
  Lee CLAUDE.md (raíz del repo, utf-8) y extrae DOS tramos, en este orden:
    A. desde la línea que empieza por "## CONSTANTES DEL SISTEMA" hasta la línea ANTERIOR a la
       que empieza por "## ARRANQUE DE SESIÓN"
    B. desde la línea que empieza por "## INVARIANTES DEL ORQUESTADOR" hasta el final del archivo
  Quita las líneas que sean solo "---" al final de cada tramo. No cambia ni una palabra del texto.
  Si falta cualquiera de los 3 encabezados: imprime cuál falta y exit 1 (nunca escribe a medias).
  Contenido que produce (exacto):
    ---
    name: reglas-sistema
    description: "Constantes e invariantes del SISTEMA VITALCOM que aplican a toda etapa. Se precarga en los subagentes de etapa; no se invoca a mano."
    ---

    # REGLAS DEL SISTEMA PARA TODA ETAPA

    > GENERADO desde `CLAUDE.md` por `Ads/_TOOLS/gen_reglas_etapas.py`. No editar: se edita
    > `CLAUDE.md` y se regenera con `--escribir`.

    <tramo A>

    <tramo B>
  CLI (un "mirar" nunca escribe):
    python Ads/_TOOLS/gen_reglas_etapas.py
        compara con el archivo en disco; imprime "EN SINCRONIA" y exit 0, o "DESINCRONIZADO"
        (o "NO EXISTE") y exit 1. No escribe.
    python Ads/_TOOLS/gen_reglas_etapas.py --escribir
        escribe .claude/skills/reglas-sistema/SKILL.md (utf-8, saltos "\n") e imprime la ruta.
  Expone una función `contenido()` que devuelve el texto completo, para que el test la use.

PASO 2 — Generar la skill
  python Ads/_TOOLS/gen_reglas_etapas.py --escribir
  python Ads/_TOOLS/gen_reglas_etapas.py        → "EN SINCRONIA"

PASO 3 — Frontmatter de los 15 agentes (.claude/agents/ETAPA-*.md)
  En cada archivo, inmediatamente ANTES de la línea `---` que cierra el frontmatter, agregar
  exactamente estas 3 líneas:
    omitClaudeMd: true
    skills:
      - reglas-sistema
  No cambiar name, description, tools ni model. No tocar el cuerpo.
  Verificar: git diff --stat .claude/agents → 15 archivos, 3 inserciones cada uno, 0 borrados.

PASO 4 — gen_grafo.py (2 cambios)
  a. En `frontmatter()`: el patrón `^([a-z_]+):\s*(.*)$` no reconoce claves con mayúsculas
     (`omitClaudeMd`) y las pega al valor de la clave anterior. Cambiar a `^([A-Za-z_]+):\s*(.*)$`.
  b. En `construir()`, a cada agente agregarle:
       "omite_claude": fm.get("omitClaudeMd", "").strip() == "true",
       "skills": re.findall(r"[\w-]+", fm.get("skills", "")),
     y en `costo_fase()` de `analizar()`, reemplazar el `claude` que se suma por agente por:
       (sum(skills[k]["tokens"] for k in a["skills"] if k in skills) if a["omite_claude"] else claude)
     Actualizar el docstring de `costo_fase` para que diga lo que ahora hace.
  Comprobar que `model` se sigue leyendo bien: la sección HALLAZGOS debe seguir diciendo
  "agentes sin model:inherit  etapa-render" y nada más.

PASO 5 — Ads/_TOOLS/test_gen_reglas_etapas.py
  Mismo estilo que los demás test_*.py (script que sale con código 0 si todo pasa y distinto de 0
  si algo falla; conftest.py lo corre como subproceso). Comprueba:
    1. La skill en disco es idéntica a `gen_reglas_etapas.contenido()`. Si alguien edita
       CLAUDE.md sin regenerar, este test falla y el mensaje dice cómo regenerar.
    2. El contenido incluye "ÁNGULO = por qué duele" y los invariantes numerados del 1 al 13
       (líneas que empiezan por "1. " hasta "13. ").
    3. El contenido NO incluye "MAPA DE ARCHIVOS" ni "ARRANQUE DE SESIÓN".
    4. Los 15 archivos de .claude/agents/ tienen en su frontmatter `omitClaudeMd: true` y
       `reglas-sistema` dentro de `skills:`.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python -m pytest Ads/_TOOLS -q → 55 passed, 0 failed.
  2. python Ads/_TOOLS/gen_grafo.py > _OPERADOR/LIMPIEZA/3A_despues_grafo.txt
     git diff --no-index _OPERADOR/LIMPIEZA/3A_antes_grafo.txt _OPERADOR/LIMPIEZA/3A_despues_grafo.txt
     Esperado: bajan los tokens de las 5 fases; "skills 10" pasa a "skills 11"; HALLAZGOS igual
     que antes. Si aparece un hallazgo nuevo, repórtalo sin arreglarlo.
  3. python Ads/_TOOLS/gen_app.py --todo no debe fallar por la skill nueva ni por el frontmatter.
     OJO: ese comando regenera VISTAS/ (es su función). Los archivos de VISTAS NO van en tu
     commit. Si falla por algo relacionado con tu cambio, DETENTE y reporta el error textual.
  4. git status --short → tuyos solo: los 2 .py nuevos, la skill, los 15 agentes y gen_grafo.py
     (más los .txt de la foto).
  5. Commit en la rama actual, solo esos archivos, sin push, sin atribución:
     git add Ads/_TOOLS/gen_reglas_etapas.py Ads/_TOOLS/test_gen_reglas_etapas.py Ads/_TOOLS/gen_grafo.py .claude/skills/reglas-sistema .claude/agents
     git commit -m "perf(agents): stage subagents skip CLAUDE.md and preload system rules skill"

SI ALGO NO CUADRA (un test viejo falla, otro script lee el frontmatter de los agentes y se rompe,
  un agente no tiene el frontmatter que se describe): DETENTE, no improvises, y reporta.

ENTREGA: chequeos 1 a 4, el diff del grafo (antes/después) completo, el hash del commit, y el
  número de líneas y de tokens (bytes/3.6) de la skill generada.
```

### Prueba del operador (después del commit, 2 minutos)

Los agentes se cargan al abrir la sesión: la prueba va en una sesión NUEVA de Claude Code en la
carpeta SISTEMA. Pegar esto tal cual y traer la respuesta:

```
Lanza el subagente etapa-producto con exactamente este mensaje y pégame su respuesta sin cambiar nada:
"PRUEBA DE CONTEXTO. No ejecutes tu tarea ni leas archivos. Responde solo estas 3 cosas mirando lo que ya tienes en contexto: (1) ¿Aparece el texto 'Agent Teams Lite' o 'MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ'? Responde SI o NO. (2) Copia textual el invariante número 4. (3) Copia textual la definición de ÁNGULO."
```

Lectura del resultado:
- (1) NO, y (2) y (3) con el texto → funciona.
- (1) SI → esta app no aplica `omitClaudeMd`; no hay daño (todo queda como antes). Avisar a Claude.
- (2) o (3) sin texto → la skill no se precargó y las etapas quedaron sin reglas: revertir ya con
  `git revert <hash del commit>` y avisar a Claude.

Red adicional: en la primera corrida real de una fase después de este cambio, comparar el paquete
contra uno anterior. Si baja la calidad, se revierte con el mismo `git revert`.

---

## PARTE 3B — EL MANUAL DEL PRODUCTO LO ARMA EL CÓDIGO

Hallazgo (30-sep): `1_HACER_MANUAL.txt` (1.298 líneas en OVULOS) lo escribe un modelo a mano, pero
casi todo su contenido ya existe como dato y el código ya lo sabe derivar:

| Sección del manual | Ya existe en | Quién lo deriva |
|---|---|---|
| Prompts de los ads, copies, nombres, presupuesto, bandas, fechas | `_PLAN.json` | `gen_lanzador.py` |
| Texto fijo del bot y REGLAS | `PLANTILLAS_FLUJO_BOT.md` + CSV | `gen_flujo_bot.py` |
| Bloques de juicio del bot (catálogo, testimonios, audio, M2, FAQ) | solo en el manual, tipeados | nadie → 3B-1 |
| Prompts de infografías | solo en el manual, tipeados | nadie → 3B-2 |

Volver a tipear lo que ya es dato es donde se pierde contenido (OVULOS salió sin las REGLAS) y
donde se gasta la salida más cara. Las infografías NO se renderizan por código: adaptar la plantilla
a un envase que no es frasco exige criterio; lo que se arregla es dónde queda guardado el resultado.

- 3B-1: los bloques de juicio del bot viven en un archivo y `gen_flujo_bot.py` los inserta.
- 3B-2: los prompts de infografías viven como dato.
- 3B-3: `gen_manual.py` arma `1_HACER_MANUAL.txt`; `etapa-guardar-producto` deja de tipearlo.

### PARTE 3B-1 — LOS BLOQUES DE JUICIO DEL BOT, COMO DATO

Ya creado por Claude: `PRODUCTOS/OVULOS_PURITY/BLOQUES_BOT.md` (9 bloques, caso real de prueba).

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: que gen_flujo_bot.py llene los marcadores <<BLOQUE:nombre>> con el texto guardado en
PRODUCTOS/<carpeta del producto>/BLOQUES_BOT.md, para que el flujo salga completo y pegable.

Archivos que puedes modificar (SOLO estos 2):
  Ads/_TOOLS/gen_flujo_bot.py
  Ads/_TOOLS/test_gen_flujo_bot.py
PROHIBIDO: tocar PRODUCTOS/ (incluido BLOQUES_BOT.md de OVULOS_PURITY, que ya existe y es tu
  caso de prueba), DOCTRINA/, .claude/. PROHIBIDO correr `gen_flujo_bot.py OVULOS_PURITY` sin
  `--copy` (sobrescribe un archivo editado a mano que está en producción).

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS/gen_flujo_bot.py Ads/_TOOLS/test_gen_flujo_bot.py → vacío.
  2. python Ads/_TOOLS/test_gen_flujo_bot.py → "TODO PASA".
  3. Foto de antes (en PowerShell definir primero $env:PYTHONIOENCODING="utf-8"):
       python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --copy > _OPERADOR/LIMPIEZA/3B1_antes_CLEARSTEM.txt
       python Ads/_TOOLS/gen_flujo_bot.py TINNIDROP --copy > _OPERADOR/LIMPIEZA/3B1_antes_TINNIDROP.txt

FORMATO de BLOQUES_BOT.md (ya definido, no lo cambies)
  Una línea que es exactamente `<<BLOQUE:nombre>>` abre un bloque; su texto es todo lo que sigue
  hasta la próxima línea `<<BLOQUE:...>>` o el fin del archivo.
  Nombres válidos: descripcion, modo_de_uso, caracteristicas, contenido, testimonios, audio, m2,
  faq_venta, faq_postventa.
  `propuestas_valor` NO va en este archivo: sigue saliendo de 2_DATA_PRODUCTO.txt como hoy.

PASO 1 — gen_flujo_bot.py: agregar
  BLOQUES_DE_JUICIO = ("descripcion", "modo_de_uso", "caracteristicas", "contenido",
                       "testimonios", "audio", "m2", "faq_venta", "faq_postventa")

  def parsear_bloques(texto):
      """{nombre: texto} de un BLOQUES_BOT.md. Quita líneas vacías al inicio y al final de cada
      bloque. ValueError si un nombre se repite o no está en BLOQUES_DE_JUICIO."""

  def bloques_persistidos(pk):
      """Los bloques de PRODUCTOS/<slug_carpeta>/BLOQUES_BOT.md. {} si no hay carpeta o no existe
      el archivo (nunca bloquea). Usa carpeta_de(pk), igual que propuestas_persistidas()."""

  def insertar_bloques(txt, bloques):
      """(texto, pendientes). Reemplaza cada LÍNEA que sea exactamente `<<BLOQUE:nombre>>` (con
      nombre en BLOQUES_DE_JUICIO) por el texto del bloque, si existe y no está vacío. Si no, deja
      el marcador como está y agrega el nombre a `pendientes` (en el orden de BLOQUES_DE_JUICIO).
      No toca `<<BLOQUE:propuestas_valor>>` ni un marcador que aparezca en medio de una línea."""

PASO 2 — Dónde se llama
  En `una()` y en `una_json()`: inmediatamente después de `txt = render(v)` y ANTES de
  `prohibiciones(...)`:
      txt, pendientes = insertar_bloques(txt, bloques_persistidos(pk))
  Así las prohibiciones también revisan los bloques (es lo que declara la sección 4 de
  DOCTRINA/PLANTILLAS_FLUJO_BOT.md).
  Los bloques NO pasan por `mercado.aplicar_persona`: ya vienen escritos en la persona del mercado.
  Un ValueError de parsear_bloques se muestra como "BLOQUEADO — BLOQUES_BOT.md: <mensaje>" y
  devuelve False (en una_json: va en la lista de bloqueos que ya use esa función).
  Salida:
    - `una()`: si el producto TIENE BLOQUES_BOT.md y quedan pendientes, imprimir una línea
      "  aviso: bloques pendientes en BLOQUES_BOT.md: <nombres>" junto a los demás avisos.
      Si el producto NO tiene el archivo, no imprimir nada nuevo.
    - `una_json()`: agregar la clave "bloques_pendientes": [nombres] SOLO si el producto tiene
      el archivo (para no cambiar el JSON de los productos que no lo tienen).

PASO 3 — Tests nuevos en test_gen_flujo_bot.py (registrarlos en la tupla de `main()`)
  test_parsear_bloques_lee_y_limpia: dos bloques con líneas vacías alrededor → dict con el texto
    sin esas líneas vacías; un nombre repetido lanza ValueError; un nombre desconocido también.
  test_insertar_bloques_reemplaza_solo_la_linea_exacta: el marcador en línea propia se reemplaza;
    el mismo marcador en medio de una línea no; `<<BLOQUE:propuestas_valor>>` queda igual;
    un bloque ausente queda como marcador y aparece en `pendientes`.
  test_producto_sin_archivo_de_bloques_queda_igual: `G.bloques_persistidos("CLEARSTEM") == {}` y
    `G.insertar_bloques(txt, {})` devuelve el mismo texto con los 9 nombres en `pendientes`.
  test_ovulos_sale_completo_con_sus_bloques: con `v, faltan, _ = G.resolver("OVULOS_PURITY")`,
    `txt, pend = G.insertar_bloques(G.render(v), G.bloques_persistidos("OVULOS_PURITY"))`:
    `faltan == []`, `pend == []`, el único marcador `<<BLOQUE:` que queda en txt es
    propuestas_valor, y `G.prohibiciones(txt, v["persona"]) == []`.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python Ads/_TOOLS/test_gen_flujo_bot.py → "TODO PASA".
  2. python -m pytest Ads/_TOOLS -q → 55 passed, 0 failed.
  3. Foto de después y comparación (deben ser IDÉNTICAS: esos productos no tienen el archivo):
       python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --copy > _OPERADOR/LIMPIEZA/3B1_despues_CLEARSTEM.txt
       python Ads/_TOOLS/gen_flujo_bot.py TINNIDROP --copy > _OPERADOR/LIMPIEZA/3B1_despues_TINNIDROP.txt
       git diff --no-index _OPERADOR/LIMPIEZA/3B1_antes_CLEARSTEM.txt _OPERADOR/LIMPIEZA/3B1_despues_CLEARSTEM.txt
       git diff --no-index _OPERADOR/LIMPIEZA/3B1_antes_TINNIDROP.txt _OPERADOR/LIMPIEZA/3B1_despues_TINNIDROP.txt
  4. python Ads/_TOOLS/gen_flujo_bot.py OVULOS_PURITY --copy > _OPERADOR/LIMPIEZA/3B1_OVULOS.txt
     El archivo NO contiene "BLOQUEADO" ni "RECHAZADO"; contiene "REGLAS CONVERSACIONALES",
     "Holaa, buenas" (audio testimonio de M2) y "FAQ POSTVENTA"; y no le queda ningún
     `<<BLOQUE:` de los 9 nombres.
  5. git status --short → tuyos solo los 2 archivos (más los .txt de la foto).
     PRODUCTOS/OVULOS_PURITY/FLUJO_LUCIDBOT.md y BLOQUES_BOT.md no deben cambiar.
  6. Commit en la rama actual, solo los 2 archivos, sin push, sin atribución:
     git commit -m "feat(flujo-bot): fill judgment blocks from the product's BLOQUES_BOT.md"

SI ALGO NO CUADRA (un gate rechaza a OVULOS por el contenido de un bloque, `estructura()` o
  `para_pegar()` se rompen con el texto insertado, un test viejo falla): DETENTE, no aflojes el
  gate ni edites el bloque, y reporta qué encontraste.

ENTREGA: chequeos 1 a 5, el hash del commit, y las líneas de _OPERADOR/LIMPIEZA/3B1_OVULOS.txt
  que van desde "MENSAJES DE INACTIVIDAD" hasta el final de la FAQ.
```

---

### PARTE 3B-2 — `gen_manual.py`: EL MANUAL ARMADO POR CÓDIGO

Ya creado por Claude: `PRODUCTOS/OVULOS_PURITY/INFOGRAFIAS.md` (4 prompts, caso real de prueba).
Esta parte solo CREA el generador y lo prueba. No reemplaza el manual de ningún producto ni toca
las etapas: eso es la 3B-3, después de comparar el resultado contra el manual tipeado.

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: crear Ads/_TOOLS/gen_manual.py, que arma 1_HACER_MANUAL.txt de un producto a partir de
datos que ya existen. No tipea contenido: lo copia textual de sus dueños.

Archivos que puedes crear o modificar (SOLO estos):
  Ads/_TOOLS/gen_manual.py                      (nuevo)
  Ads/_TOOLS/test_gen_manual.py                 (nuevo)
  evals/asserts/etapa-guardar-producto.py       (agregar 2 nombres a PERMITIDOS_EXACTOS)
PROHIBIDO: tocar PRODUCTOS/, DOCTRINA/, .claude/, gen_lanzador.py, gen_flujo_bot.py.
PROHIBIDO: correr gen_manual.py con --escribir sobre un producto real, y correr
  gen_lanzador.py o gen_flujo_bot.py por CLI sin --copy / --json (escriben archivos).

ANTES DE EMPEZAR
  1. python -m pytest Ads/_TOOLS -q → 55 passed.
  2. Lee completos: Ads/_TOOLS/gen_lanzador.py (funciones `construir` y `derivar`) y
     Ads/_TOOLS/gen_flujo_bot.py (funciones `resolver`, `render`, `insertar_bloques`,
     `bloques_persistidos`, `prohibiciones`, `para_pegar`, `carpeta_de`, `una`).
  3. Comprueba que `gen_lanzador.construir()` NO escribe archivos (solo devuelve el dict).
     Si escribe, DETENTE y reporta.

DE DÓNDE SALE CADA COSA (un dato, un dueño; gen_manual no calcula nada)
  Plan derivado del producto  → gen_lanzador.construir()["productos"], el elemento con ese
                                producto_key, clave "plan" (nombres, presupuesto, bandas,
                                fechas, prompts, copies, calendario, bloqueantes, faltantes)
  Flujo del bot               → gen_flujo_bot: resolver → render → insertar_bloques(txt,
                                bloques_persistidos(pk)) → prohibiciones → para_pegar
  Prompts de infografías      → PRODUCTOS/<carpeta>/INFOGRAFIAS.md
  Carpeta del producto        → gen_flujo_bot.carpeta_de(pk)

FORMATO de INFOGRAFIAS.md (ya definido)
  Una línea que es exactamente `<<INFOGRAFIA:n>>` (n de 1 a 6) abre un bloque; su texto es todo
  lo que sigue hasta la próxima línea `<<INFOGRAFIA:...>>` o el fin del archivo.
  Las infografías 1, 2 y 3 son obligatorias; 4, 5 y 6 son opcionales.

PASO 1 — gen_manual.py, funciones
  def parsear_infografias(texto)
      {n (str): texto} sin líneas vacías al inicio ni al final. ValueError si un n se repite o
      no está entre 1 y 6.
  def reunir(pk)
      Junta las fuentes. Devuelve (datos, bloqueos): `datos` es un dict con "plan", "flujo"
      (texto pegable) e "infografias"; `bloqueos` es una lista de textos. Agrega un bloqueo,
      nombrando QUÉ falta y QUIÉN lo produce, en cada uno de estos casos:
        - el producto no existe en el lanzador o no tiene plan   → "_PLAN.json — etapa-6"
        - plan["bloqueantes"] no está vacío                       → cada bloqueante tal cual
        - resolver() devuelve `faltan`                            → cada dato y su dueño
        - quedan bloques pendientes tras insertar_bloques         → "BLOQUES_BOT.md: <nombres> — etapa-5"
        - prohibiciones() devuelve hallazgos                      → cada hallazgo tal cual
        - falta INFOGRAFIAS.md o falta la 1, la 2 o la 3          → "INFOGRAFIAS.md: <cuáles> — etapa-4"
      Nunca rellena ni inventa: si falta, bloquea.
  def render_manual(datos)
      Función PURA (no lee disco): devuelve el texto completo del manual. Secciones, en orden:

      ENCABEZADO
        HACER MANUAL — <plan.nombre> | <plan.fase_nombre>
        FanPage: <plan.pagina> (page_id <plan.page_id>) · Cuenta: <plan.cuenta>
        GENERADO por Ads/_TOOLS/gen_manual.py — no editar a mano: se corrige el dato de origen
        y se vuelve a generar.
      A. CHECKLIST (en este orden)
        [ ] 1. Generar las imágenes de los anuncios (sección B)
        [ ] 2. Generar las infografías del bot (sección C)
        [ ] 3. Armar el flujo en LucidBot (sección D) y probarlo desde otro WhatsApp
        [ ] 4. Crear la campaña en Meta (sección E)
        [ ] 5. Registrar en el sistema (sección F)
      B. CREATIVOS DE LOS ANUNCIOS
        Por cada conjunto, en orden de `n`:
          AD <n> — <angulo_titulo> · formato: <formato> · archivo: <archivo_creativo> · precio en el ad: SI/NO
          y debajo, si tiene `prompt_imagen`, el prompt TEXTUAL completo.
      C. INFOGRAFÍAS DEL BOT (van dentro del flujo, no en Meta)
        Por cada infografía presente, en orden: el bloque TEXTUAL completo.
      D. FLUJO LUCIDBOT (copiar cada parte en su campo)
        El texto pegable del flujo, TEXTUAL completo.
      E. ESTRUCTURA EN META
        Por cada campaña de plan["campanas"]: nombre, objetivo, presupuesto.
        Lanzamiento: <plan.lanzamiento.legible> a las <plan.lanzamiento.hora>.
        Por cada conjunto: nombre · presupuesto US$<presupuesto_usd>/día · edad <banda_edad> ·
          género <genero> · formato · archivo · precio en el ad SI/NO; los nombres de sus anuncios;
          y su copy TEXTUAL: cada texto de copy["textos"] rotulado TEXTO PRINCIPAL 1..n, cada
          título de copy["titulos"] rotulado TÍTULO 1..n, y copy["descripcion"] rotulada DESCRIPCIÓN.
        PENDIENTES QUE DECLARA EL LANZADOR: cada elemento de plan["faltantes"], tal cual.
      F. CALENDARIO Y REGISTRO
        Cada fila de plan["calendario"]: <dia> (<fecha>) — <que> · hacer: <hace> · traer: <manda>.
        Y los dos comandos, con los datos del plan:
          python Ads/_TOOLS/registrar_evento.py --producto <pk> --evento CAMBIO_BOT --motivo "bot cargado en LucidBot" --fuente "operador"
          python Ads/_TOOLS/registrar_evento.py --producto <pk> --evento LANZAMIENTO --fase <fase> --fecha <lanzamiento.fecha> --cuenta <cuenta> --campana <nombre de la primera campaña> --motivo "lanzamiento" --fuente "operador"
      Reglas del render: un separador visible entre secciones; ningún texto de origen se
      resume, recorta ni reescribe; una clave ausente u opcional vacía no rompe el render
      (se omite esa línea).

  CLI (un "mirar" nunca escribe)
    python Ads/_TOOLS/gen_manual.py <PK>             → si hay bloqueos: imprime "BLOQUEADO — falta:"
                                                       y la lista, exit 1. Si no: imprime el manual, exit 0.
    python Ads/_TOOLS/gen_manual.py <PK> --escribir  → igual, y si no hay bloqueos escribe
                                                       PRODUCTOS/<carpeta>/1_HACER_MANUAL.txt (utf-8, "\n").
    python Ads/_TOOLS/gen_manual.py <PK> --validar   → imprime solo "LISTO" o la lista de bloqueos.
  La salida por consola debe imprimir bien tildes y emojis en Windows
  (sys.stdout.reconfigure(encoding="utf-8") si existe reconfigure).

PASO 2 — evals/asserts/etapa-guardar-producto.py
  Agregar "BLOQUES_BOT.md" e "INFOGRAFIAS.md" al conjunto PERMITIDOS_EXACTOS. Nada más.

PASO 3 — test_gen_manual.py (mismo estilo de script que los demás tests: sale 0 si todo pasa)
  Con datos FALSOS en memoria (sin leer productos reales):
    1. render_manual con un plan de 2 conjuntos: cada prompt_imagen, cada texto, título y
       descripción del copy, el flujo y cada infografía aparecen TEXTUALES en la salida, y las
       secciones A..F aparecen en ese orden.
    2. parsear_infografias: lee 3 bloques; repetido o fuera de 1..6 lanza ValueError.
    3. render_manual no falla si un conjunto no tiene prompt_imagen ni si `manda` es None.
  Con el producto real OVULOS_PURITY (solo lectura):
    4. `datos, bloqueos = reunir("OVULOS_PURITY")` → `bloqueos == []`.
    5. El manual contiene "REGLAS CONVERSACIONALES", las 4 infografías textuales (compararlas
       contra parsear_infografias del archivo) y, por cada conjunto del plan, su `nombre` y su
       `prompt_imagen` textual.
  Con un producto real SIN archivos nuevos (CLEARSTEM):
    6. `reunir("CLEARSTEM")` devuelve bloqueos que nombran INFOGRAFIAS.md y BLOQUES_BOT.md
       (no lanza excepción).

CHEQUEOS FINALES (todos deben cumplirse)
  1. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  2. python evals/run_baseline.py → mismo resultado que antes de tu cambio (córrelo antes y después).
  3. python Ads/_TOOLS/gen_manual.py OVULOS_PURITY > _OPERADOR/LIMPIEZA/3B2_OVULOS_manual.txt
     (en PowerShell: $env:PYTHONIOENCODING="utf-8" y `| Out-File -Encoding utf8`). exit 0.
  4. python Ads/_TOOLS/gen_manual.py CLEARSTEM --validar → lista de bloqueos, exit 1.
  5. git status --short → tuyos solo los 2 .py nuevos y el assert de evals (más el .txt).
     PRODUCTOS/OVULOS_PURITY/1_HACER_MANUAL.txt NO debe cambiar.
  6. Commit en la rama actual, solo esos 3 archivos, sin push, sin atribución:
     git commit -m "feat(manual): assemble the operator manual from plan, bot flow and infographics data"

SI ALGO NO CUADRA (construir() escribe archivos, la estructura del plan no es la descrita,
  reunir("OVULOS_PURITY") da bloqueos): DETENTE, no improvises, y reporta.

ENTREGA: chequeos 1 a 5, el hash del commit, y de _OPERADOR/LIMPIEZA/3B2_OVULOS_manual.txt:
  el número de líneas, las primeras 20 líneas y la sección E del conjunto 1 completa.
```

---

### PARTE 3B-3 — EL MANUAL GENERADO REEMPLAZA AL TIPEADO

Va en dos entregas, en este orden. La B no se pasa a la ejecutora hasta que Claude verifique la A.

- **3B-3A (solo código):** el manual generado queda completo y cada dato con un solo dueño.
- **3B-3B (prosa de etapas):** `etapa-4` y `etapa-5` escriben sus archivos de datos y
  `etapa-guardar-producto` corre `gen_manual.py` en FASE 1 en vez de tipear.

Decisiones de diseño (propuestas por Claude, aceptadas por el operador el 30-sep-2026):

| Tema | Decisión | Por qué |
|---|---|---|
| Presupuesto de FASE 1 | Dueño único: `_PARAMETROS_PUBLICACION.csv` (2.99). `gen_lanzador.py` deja la fórmula 7 × $/conversación | Es lo que publica `gen_publicacion.py`, lo que dicen `ETAPA-6.md` y la Guía Madre, y lo que se lanzó en OVULOS. La fórmula se alimentaba del costo por conversación del portafolio GT aun para un producto de CO. La pantalla mostraba un número y Meta recibía otro |
| `anuncios_por_conjunto` = 1 en el CSV | No se toca el dato | La columna cuenta PIEZAS por conjunto (la usa `gen_publicacion.py` para repartir creativos y `flujo.py` para contar). El duplicado A/B es una regla aparte que `gen_lanzador.py` y `gen_publicacion.py` ya aplican. No había contradicción |
| Fecha y nombre de campaña | Si hay un `LANZAMIENTO` de esa fase en `_EVENTOS.csv`, manda su fecha | El plan dejaba de coincidir con Meta al día siguiente de lanzar |
| Monto en moneda de la cuenta | `presupuesto USD × tasa` de `_DIM_PRODUCTOS.csv`, solo si `moneda` ≠ USD | `moneda` ya es la moneda con que Meta cobra la cuenta |
| Primera línea del manual | Se copia de `2_DATA_PRODUCTO.txt` | `verificar_producto.py` exige el encabezado único en la línea 1; sin él, el manual generado no pasa el gate |
| Quién escribe `BLOQUES_BOT.md` e `INFOGRAFIAS.md` | La etapa que los redacta, con `Write` | Se tipean una sola vez. Pasarlos por el orquestador a `etapa-guardar-producto` es volver a tipearlos |
| Alcance de la 3B-3B | Solo FASE 1 | `gen_lanzador.py` lee `_PLAN.json`; el manual de FASE 2 y FASE 4 no está probado con el generador |

#### PARTE 3B-3A — MANUAL COMPLETO Y UN SOLO DUEÑO POR DATO

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: completar el plan que deriva gen_lanzador.py y el manual que arma gen_manual.py, sin
tipear contenido y sin cambiar ningún dato de PRODUCTOS/.

Archivos que puedes modificar (SOLO estos 4):
  Ads/_TOOLS/gen_lanzador.py
  Ads/_TOOLS/test_gen_lanzador.py
  Ads/_TOOLS/gen_manual.py
  Ads/_TOOLS/test_gen_manual.py
PROHIBIDO: tocar PRODUCTOS/, DOCTRINA/, .claude/, VISTAS/, lanzador_html.py, gen_publicacion.py,
  gen_flujo_bot.py, flujo.py, mercado.py, referencia_f1.py, verificar_producto.py.
PROHIBIDO: correr gen_lanzador.py o gen_flujo_bot.py por línea de comandos (escriben archivos)
  y correr gen_manual.py con --escribir.
Todos los comandos se corren desde la raíz del repo, de a uno. En PowerShell define primero
  $env:PYTHONIOENCODING="utf-8" y usa `| Out-File -Encoding utf8 <archivo>` en vez de `>`.
Docstrings y comentarios nuevos: describen la regla vigente, sin fechas ni historia del cambio.

ANTES DE EMPEZAR
  1. git status --short Ads/_TOOLS → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.
  3. Foto de antes (archivo _OPERADOR/LIMPIEZA/3B3A_antes.json):
       python -c "import sys,json; sys.path.insert(0,'Ads/_TOOLS'); import gen_lanzador as g; print(json.dumps(g.construir(), ensure_ascii=False, indent=1, sort_keys=True))"
  4. Lee completos gen_lanzador.py y gen_manual.py. Lee en flujo.py la definición de TOKEN_FASE,
     en mercado.py `perfil_de_fila` y `MercadoError`, en referencia_f1.py `fila_de` y `BANCO_DIR`,
     y en verificar_producto.py `parsear_encabezado`.
  5. Comprueba que importar flujo, mercado, referencia_f1 y verificar_producto NO escribe
     archivos ni imprime nada (todo su código suelto está bajo `if __name__ == "__main__":`).
     Si alguno escribe o imprime al importarse, DETENTE y reporta.

───────── gen_lanzador.py ─────────

PASO 1 — El presupuesto de TODAS las fases sale de _PARAMETROS_PUBLICACION.csv
  `presupuesto_por_fase(fase, usd_conv, brazo="A")` queda así (misma firma; `usd_conv` ya no
  se usa):
      fase 2          → presupuesto_fase_csv(2, brazo)
      cualquier otra  → presupuesto_fase_csv(fase, "UNICO")
  Borra la función `presupuesto_conjunto` y la constante MULT_CONVERSACIONES.
  NO borres PISO_PRESUPUESTO, TECHO_PRESUPUESTO ni la clave "constantes" de construir().
  Reescribe los docstrings de presupuesto_fase_csv y presupuesto_por_fase para que digan solo
  la regla: todas las fases leen su fila VIGENTE; sin fila, devuelve None y no inventa.

PASO 2 — Un lanzamiento ya registrado fija la fecha
  Agrega:
      def lanzamiento_registrado(pk, fase):
          """(fecha "YYYY-MM-DD", campana_clave) del ÚLTIMO evento LANZAMIENTO del producto
          para esa fase en _EVENTOS.csv, o None. Un evento es de la fase si su campana_clave,
          en mayúsculas, contiene alguno de los tokens de flujo.TOKEN_FASE para esa fase."""
  Reglas: compara producto_key exacto y evento == "LANZAMIENTO"; ignora las filas cuya fecha
  no sea YYYY-MM-DD; «último» = fecha mayor. Importa flujo DENTRO de la función (mismo patrón
  que `banda_edad` con bandas_edad). Adapta la comparación al tipo real de las llaves de
  TOKEN_FASE (texto o número).
  En `derivar`:
      reg = lanzamiento_registrado(pk, fase)
      lanzamiento = la fecha de reg si existe; si no, HOY + 1 día (como hoy)
  Los nombres de campaña y el calendario siguen saliendo de `lanzamiento`, sin más cambios.
  En el dict "lanzamiento" del plan agrega:
      "registrado": True/False
      "campana_registrada": el campana_clave de reg, o None

PASO 3 — El presupuesto también en la moneda con que Meta cobra la cuenta
  Agrega:
      def monto_cuenta(usd, moneda, tasa):
          """(valor, texto) de un monto en USD expresado en la moneda de la cuenta
          publicitaria (_DIM_PRODUCTOS.moneda).
          USD   → (usd, "US$2.99")            dos decimales
          otra  → (round(usd * tasa), "$9.426 COP")   entero, punto de miles, código de moneda
          (None, None) si falta la moneda, o si no es USD y falta la tasa."""
  En `derivar`: moneda = prod["moneda"] sin espacios y en mayúsculas.
    - moneda vacía → bloqueante {"que": "moneda de la cuenta publicitaria sin declarar",
                                 "quien": "operador · _DIM_PRODUCTOS.csv columna moneda"}
    - moneda distinta de USD y sin tasa → bloqueante
          {"que": "tasa sin declarar: no se puede dar el presupuesto en <moneda>",
           "quien": "operador · _DIM_PRODUCTOS.csv columna tasa"}
  Claves nuevas:
    en cada conjunto:        "presupuesto_cuenta" (valor) y "presupuesto_cuenta_texto"
    en plan["presupuesto"]:  "moneda_cuenta", "por_conjunto_cuenta_texto" y
                             "total_dia_cuenta_texto" (valor del conjunto × número de
                             conjuntos, con el mismo formato)
  No cambies ninguna clave existente (presupuesto_usd, presupuesto_centavos, total_dia_usd…).

PASO 4 — La configuración fija de Meta, como dato del plan
  Agrega la constante (textos exactos):
      CONFIG_META_FIJA = (
          "Ubicación: %(pais)s · Sin intereses",
          "Advantage+ Audience: OFF (si no, Meta ignora la banda de edad)",
          "Optimización: Maximizar CONVERSACIONES — revisarlo justo antes de publicar: Meta lo revierte a clics con cada duplicado",
          "Destino: WhatsApp (el número conectado a la FanPage, nunca Messenger) · CTA: Enviar mensaje",
          "DESMARCAR «anuncios multianunciantes»",
          "DESMARCAR «incluir personas de WhatsApp cuya edad se desconoce»",
          "Anuncios A y B de una misma pieza: el B es copia exacta del A (misma imagen, mismo copy)",
          "Texto principal: cargar todos los TEXTOS como opciones · Títulos: todos · Descripción: la indicada",
          "Cero «- Copia» en ningún nombre: renombrar antes de publicar",
          "NO aceptar recomendaciones de Meta",
      )
  En `derivar`: pais = mercado.perfil_de_fila(prod)["pais"] (import dentro de la función).
    Si lanza mercado.MercadoError → bloqueante
        {"que": "mercado del producto sin declarar o inexistente",
         "quien": "operador · _DIM_PRODUCTOS.csv columna mercado"}
    y pais = "[PAÍS]".
  Clave nueva del plan: "config_meta": [linea % {"pais": pais} for linea in CONFIG_META_FIJA]

PASO 5 — test_gen_lanzador.py
  - Borra `test_fase1_sigue_usando_la_formula_autoajustable` y pon en su lugar
    `test_fase1_lee_el_valor_fijo_del_csv`: con el CSV temporal del archivo,
    presupuesto_por_fase(1, 0.1)[0] == 2.99 y presupuesto_por_fase(1, 0.9)[0] == 2.99.
  - `test_fase2_ya_no_dicta_la_mitad`: quita la llamada a presupuesto_conjunto; la condición
    queda `presup_fase2 == 6.0`. Ajusta su texto impreso y el docstring del módulo a la regla
    vigente (todas las fases leen el CSV).
  - `test_monto_cuenta`: (2.99, "USD", 7.62) → (2.99, "US$2.99");
    (2.99, "COP", 3152.5) → (9426, "$9.426 COP"); (2.99, "COP", None) → (None, None);
    (2.99, "", 7.62) → (None, None).
  - `test_lanzamiento_registrado`: con un _EVENTOS.csv temporal (cambia gl.EVENTOS igual que
    los tests cambian gl.PARAMETROS_PUBLICACION) con estas filas del producto "P":
      2026-09-28 LANZAMIENTO campana_clave "X_P_TEST_20260928"
      2026-09-30 LANZAMIENTO campana_clave "X_P_TEST_20260930"
      2026-09-30 CAMBIO_BOT  campana_clave "*"
    → fase 1 devuelve ("2026-09-30", "X_P_TEST_20260930"); fase 2 devuelve None; el producto
    "OTRO" devuelve None.
  - `test_plan_real_de_ovulos` (solo lectura, producto real OVULOS_PURITY vía construir()):
    bloqueantes == []; presupuesto["por_conjunto_usd"] == 2.99;
    presupuesto["moneda_cuenta"] == "COP"; cada conjunto tiene presupuesto_cuenta_texto que
    termina en " COP"; lanzamiento["registrado"] is True y lanzamiento["fecha"] == "2026-09-30";
    campanas[0]["nombre"] == "EXTERNA_OVULOSPURITY_TEST_20260930";
    config_meta[0] == "Ubicación: Colombia · Sin intereses".
  Registra los tests nuevos en `main()`.

  PRODUCTOS FICTICIOS EN TESTS VIEJOS: si un test de OTRO archivo falla porque su producto
  inventado no trae `moneda` o `mercado`, NO agregues un valor por defecto en gen_lanzador.py.
  DETENTE y reporta el nombre del test y del archivo.

CHEQUEO INTERMEDIO (antes de tocar gen_manual.py)
  a. python Ads/_TOOLS/test_gen_lanzador.py → "0 fallas."
  b. python -m pytest Ads/_TOOLS -q → 56 passed.
  c. Foto de después (mismo comando del punto 3) en _OPERADOR/LIMPIEZA/3B3A_despues.json y
       git diff --no-index --stat _OPERADOR/LIMPIEZA/3B3A_antes.json _OPERADOR/LIMPIEZA/3B3A_despues.json
     Lo esperado: claves NUEVAS en todos los planes; valores que CAMBIAN solo en el presupuesto
     de planes de fase 1 y en fecha / nombre de campaña / calendario de OVULOS_PURITY.
     Si cambia el valor de cualquier otra clave existente, DETENTE y reporta.
  d. Commit 1 (solo gen_lanzador.py y test_gen_lanzador.py, sin push, sin atribución):
     git commit -m "feat(lanzador): single owner for phase budget and launch date, account-currency amounts and fixed Meta config"

───────── gen_manual.py ─────────

PASO 6 — `reunir(pk)` junta cuatro datos más (mismo patrón: si falta, bloquea con su dueño)
  a. datos["encabezado"]: la primera línea de PRODUCTOS/<carpeta>/2_DATA_PRODUCTO.txt, tal
     cual (sin el salto de línea), SOLO si verificar_producto.parsear_encabezado(ruta) no es
     None. Si el archivo no existe o devuelve None → bloqueo:
       "2_DATA_PRODUCTO.txt: falta o su primera línea no es el encabezado único — etapa-guardar-producto"
  b. datos["mensaje_prellenado"]: v["mensaje_prellenado_anuncio"] del `resolver(pk)` que ya se
     llama (no bloquea por sí mismo: si falta, `resolver` ya lo reporta en `faltan`).
  c. datos["packshot"]: la columna `packshot` de la fila del producto en
     PRODUCTOS/_DIM_ENVASE.csv, leída con gen_lanzador.leer_csv. Sin fila o con la columna
     vacía → bloqueo:
       "_DIM_ENVASE.csv: sin packshot declarado — operador (Ads/_TOOLS/cargar_packshot.py)"
  d. datos["referencia"]: solo si plan["fase"] == 1. Con fila = referencia_f1.fila_de(pk):
     la ruta relativa al repo, con "/", de os.path.join(referencia_f1.BANCO_DIR,
     fila["referencia"]). Si fila es None → bloqueo:
       "_DIM_REFERENCIA_F1.csv: sin referencia elegida — etapa-2 (Ads/_TOOLS/referencia_f1.py --elegir)"

PASO 7 — `render_manual(datos)` (sigue siendo PURA; una clave ausente omite su línea)
  - PRIMERA línea del manual: datos["encabezado"]. Después, las líneas de encabezado de hoy.
  - Sección B, justo debajo del título y antes del primer AD:
        Adjuntar a CADA prompt, en este orden:
          1. Foto del producto: <packshot>
          2. Imagen de referencia: <referencia>        (solo si hay referencia)
  - Sección E, debajo de la línea "Lanzamiento: …":
        CONFIGURACIÓN IGUAL EN TODOS LOS CONJUNTOS:
        · <cada línea de plan["config_meta"]>
        · Mensaje prellenado de WhatsApp (se configura a mano en Ads Manager): <mensaje_prellenado>
        Total del día: <plan["presupuesto"]["total_dia_cuenta_texto"]>
  - Sección E, línea de cada conjunto: donde hoy dice "presupuesto US$<presupuesto_usd>/día"
    pasa a decir "presupuesto <presupuesto_cuenta_texto>/día" y, solo si
    plan["presupuesto"]["moneda_cuenta"] no es "USD", agrega " (US$<presupuesto_usd>)".
  - Sección F: si plan["lanzamiento"]["registrado"] es True, en lugar del comando de
    LANZAMIENTO imprime:
        LANZAMIENTO ya registrado: <lanzamiento.fecha> · campaña <lanzamiento.campana_registrada>
    El comando de CAMBIO_BOT no cambia.

PASO 8 — test_gen_manual.py
  - Agrega a los datos falsos las claves nuevas (encabezado, mensaje_prellenado, packshot,
    referencia, config_meta, presupuesto_cuenta_texto, moneda_cuenta, total_dia_cuenta_texto,
    lanzamiento.registrado) y comprueba en el test de render: la primera línea es el
    encabezado; packshot, referencia, cada línea de config_meta y el mensaje prellenado salen
    TEXTUALES; con registrado=True sale "LANZAMIENTO ya registrado" y NO sale
    "--evento LANZAMIENTO"; con registrado=False sale el comando.
  - En el test que tolera opcionales vacíos: sin ninguna de las claves nuevas, render_manual
    no lanza excepción.
  - En el test real de OVULOS: la primera línea del manual es igual a la primera línea de
    PRODUCTOS/OVULOS_PURITY/2_DATA_PRODUCTO.txt, y el manual contiene
    "Advantage+ Audience: OFF", "Ubicación: Colombia", "OVULOSPURITY_PACKSHOT.png",
    "ligera__Camila-Recomienda__15_" y "LANZAMIENTO ya registrado: 2026-09-30".
  - El test de CLEARSTEM no cambia: sigue bloqueando y nombrando INFOGRAFIAS.md y BLOQUES_BOT.md.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python Ads/_TOOLS/test_gen_manual.py → todo pasa.
  2. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  3. python evals/run_baseline.py → mismo resultado que antes (27 PASS + 1 conocido, FAIL=0).
  4. python Ads/_TOOLS/gen_manual.py OVULOS_PURITY → exit 0; guarda la salida en
     _OPERADOR/LIMPIEZA/3B3A_OVULOS_manual.txt.
  5. python Ads/_TOOLS/gen_manual.py CLEARSTEM --validar → lista de bloqueos, exit 1.
  6. git status --short → tuyos solo los 4 .py (más los archivos de _OPERADOR/LIMPIEZA/).
     PRODUCTOS/ y VISTAS/ no deben tener cambios tuyos.
  7. Commit 2 (solo gen_manual.py y test_gen_manual.py, sin push, sin atribución):
     git commit -m "feat(manual): canonical header, fixed Meta config, prefilled message and reference images"

SI ALGO NO CUADRA (importar flujo desde gen_lanzador da import circular, TOKEN_FASE no tiene la
  forma descrita, el nombre de campaña de OVULOS no es EXTERNA_OVULOSPURITY_TEST_20260930,
  reunir("OVULOS_PURITY") da bloqueos, un test viejo falla): DETENTE, no improvises ni agregues
  valores por defecto, y reporta qué encontraste.

ENTREGA: los chequeos 1 a 6, los dos hashes, la salida del `git diff --no-index --stat` del
  chequeo intermedio, y de _OPERADOR/LIMPIEZA/3B3A_OVULOS_manual.txt: el número de líneas, las
  primeras 12 líneas, la sección E desde "E. ESTRUCTURA EN META" hasta el primer conjunto
  inclusive, y la sección F completa.
```

#### PARTE 3B-3B — LAS ETAPAS ESCRIBEN SUS DATOS Y EL MANUAL DE FASE 1 SE GENERA

No pasar hasta que Claude verifique la 3B-3A. Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: cambiar la prosa de 3 agentes y 1 skill para que, en FASE 1, los bloques del bot y los
prompts de infografías se escriban una sola vez en su archivo de datos y 1_HACER_MANUAL.txt lo
genere gen_manual.py. No se toca código ni datos.

Archivos que puedes modificar (SOLO estos 4):
  .claude/agents/ETAPA-4.md
  .claude/agents/ETAPA-5.md
  .claude/agents/ETAPA-GUARDAR-PRODUCTO.md
  .claude/skills/fase-1-angulos/SKILL.md
PROHIBIDO: tocar CLAUDE.md, Ads/, PRODUCTOS/, DOCTRINA/, evals/ y cualquier otro agente o skill.
PROHIBIDO: reescribir, resumir o reordenar texto que esta guía no nombra.
Cada cambio es un reemplazo literal: busca el texto «ANTES» exacto; si no aparece tal cual,
  DETENTE y reporta (no busques uno parecido).

ANTES DE EMPEZAR
  1. git status --short .claude/agents .claude/skills/fase-1-angulos → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.
  3. python evals/run_baseline.py → anota la línea TOTAL=… completa.

───────── ETAPA-4.md ─────────

CAMBIO 4.1 — frontmatter
  ANTES:   tools: Read
  DESPUÉS: tools: Read, Write

CAMBIO 4.2 — input de FASE 1: dentro de <input_fase1>, después de la línea
  `  <producto>[nombre del producto de ETAPA-1]</producto>` agrega estas dos líneas:
    <producto_key>[llave del sistema]</producto_key>
    <carpeta_producto>[slug_carpeta de _DIM_PRODUCTOS.csv — lo pasa el orquestador, nunca se adivina]</carpeta_producto>

CAMBIO 4.3 — output de FASE 1: dentro del bloque de código, reemplaza desde la línea
  `INFOGRAFÍAS DEL BOT — 3 PROMPTS (+ IMAGEN 4 anti-imitación opcional)` hasta la línea
  `[Texto completo de la plantilla con todas las [VARIABLES] reemplazadas — atributos reales vs defectos de imitación]`
  (ambas inclusive; la línea de ═══ de arriba se queda) por:
    INFOGRAFÍAS DEL BOT — escritas en PRODUCTOS/[carpeta_producto]/INFOGRAFIAS.md
    ══════════════════════════════════════════════════════
    Infografías escritas: 1, 2, 3 [y 4 si se pidió]

CAMBIO 4.4 — sección nueva, inmediatamente ANTES del título `### FASE 2` de la sección Output:

    #### Infografías del bot — se ESCRIBEN en archivo, no se devuelven en el output

    Con **Write**, crear `PRODUCTOS/[carpeta_producto]/INFOGRAFIAS.md` (sobrescribe el que
    exista). Es el **único** archivo que esta etapa escribe. Sin `<carpeta_producto>`: detener
    (invariante 4).

    Formato exacto — cada marcador va solo en su línea, sin nada antes del primero:

        <<INFOGRAFIA:1>>
        [IMAGEN 1 — 10 BENEFICIOS: texto completo de la plantilla, todas las [VARIABLES] reemplazadas]

        <<INFOGRAFIA:2>>
        [IMAGEN 2 — ANTES/DESPUÉS + INGREDIENTES + MODO DE USO: texto completo]

        <<INFOGRAFIA:3>>
        [IMAGEN 3 — RESULTADOS CLÍNICOS: PASO 1 — FOTO BASE y PASO 2 — DISEÑO EN CANVA, completos]

        <<INFOGRAFIA:4>>
        [IMAGEN 4 — ANTI-IMITACIÓN: solo si el operador la pidió; si no, este bloque no se escribe]

    Las infografías 1, 2 y 3 son obligatorias: sin ellas `Ads/_TOOLS/gen_manual.py` bloquea el
    manual. El archivo lleva solo prompts listos para pegar, sin citas de clase ni explicación.
    En el output se informa qué infografías quedaron escritas; los prompts no se repiten ahí.

───────── ETAPA-5.md ─────────

CAMBIO 5.1 — frontmatter
  ANTES:   tools: Read
  DESPUÉS: tools: Read, Write

CAMBIO 5.2 — tabla del Rol
  ANTES:   | **Los bloques de juicio** — los 4 campos del catálogo, testimonios, audio, texto de M2, FAQ | los `<<BLOQUE:x>>` que marca la plantilla |
  DESPUÉS: | **Los bloques de juicio** — los 4 campos del catálogo, testimonios, audio, texto de M2, FAQ | `PRODUCTOS/[carpeta_producto]/BLOQUES_BOT.md`, un `<<BLOQUE:nombre>>` por bloque; `gen_flujo_bot.py` los inserta en la plantilla |

CAMBIO 5.3 — input: después de la línea `  <producto_key>[llave del sistema]</producto_key>`
  agrega:
    <carpeta_producto>[slug_carpeta de _DIM_PRODUCTOS.csv — lo pasa el orquestador, nunca se adivina]</carpeta_producto>

CAMBIO 5.4 — sección Conexión
  ANTES (3 líneas):
    Entrega las 9 frases del ángulo → `PRODUCTOS/_DIM_FLUJO_BOT.csv`
    Entrega los bloques de juicio → los `<<BLOQUE:x>>` de la plantilla
    Después: `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` renderiza el flujo completo.
  DESPUÉS:
    Entrega las 9 frases del ángulo → en el output, para `PRODUCTOS/_DIM_FLUJO_BOT.csv`
    Escribe los bloques de juicio → `PRODUCTOS/[carpeta_producto]/BLOQUES_BOT.md`, con **Write**
    Entrega `<<BLOQUE:propuestas_valor>>` → en el output (va a `2_DATA_PRODUCTO.txt`, nunca a `BLOQUES_BOT.md`)
    Después: `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` inserta los bloques y renderiza el flujo completo.

    ### Formato de `BLOQUES_BOT.md`

    Es el **único** archivo que esta etapa escribe (sobrescribe el que exista). Sin
    `<carpeta_producto>`: detener (invariante 4). Cada marcador va solo en su línea y su texto
    es todo lo que sigue hasta el próximo marcador:

        <<BLOQUE:descripcion>>
        <<BLOQUE:modo_de_uso>>
        <<BLOQUE:caracteristicas>>
        <<BLOQUE:contenido>>
        <<BLOQUE:testimonios>>
        <<BLOQUE:audio>>
        <<BLOQUE:m2>>
        <<BLOQUE:faq_venta>>
        <<BLOQUE:faq_postventa>>

    Los nueve son obligatorios y no se admite otro nombre: `gen_flujo_bot.py` rechaza un nombre
    repetido o desconocido y deja como pendiente el que falte. El texto va ya en la persona del
    mercado (voseo en GT, tuteo en CO): el generador no lo transforma. En el output se informa
    qué bloques quedaron escritos; su texto no se repite ahí.

    En FASE 2 el archivo lleva el **BRAZO A** (el flujo vigente del producto). El BRAZO B se
    entrega completo en el output.

───────── ETAPA-GUARDAR-PRODUCTO.md ─────────

CAMBIO G.1 — inmediatamente DESPUÉS de la línea que empieza con
  `> Es el único archivo que el operador abre para ejecutar.` y su línea en blanco, agrega:

    > **FASE 1 — este archivo NO se escribe con Write: lo GENERA el código.** Orden obligatorio:
    > 1. Escribir `2_DATA_PRODUCTO.txt` (su primera línea es el encabezado único).
    > 2. Correr `python Ads/_TOOLS/gen_manual.py [producto_key] --escribir`.
    > 3. Si imprime `BLOQUEADO — falta:`, NO escribir el manual a mano ni completar lo que
    >    falta: devolver al orquestador cada línea tal cual (cada una nombra el dato y su
    >    dueño) y detener. Se vuelve a correr cuando el dueño produjo el dato.
    >
    > El generador copia el plan de `_PLAN.json`, el flujo de `gen_flujo_bot.py` con
    > `BLOQUES_BOT.md`, y los prompts de `INFOGRAFIAS.md`. Un error en el manual se corrige en
    > el dato de origen y se regenera; nunca editando `1_HACER_MANUAL.txt`.
    >
    > La plantilla de abajo aplica solo al cierre de FASE 2, hasta que el generador cubra esa fase.

CAMBIO G.2 — fila 9 de la tabla del gate
  ANTES:   transcribe **verbatim** el `<<BLOQUE:propuestas_valor>>` de 1_HACER_MANUAL — mismo texto, mismo orden, sin resumir (invariante 3) |
  DESPUÉS: transcribe **verbatim** el `<<BLOQUE:propuestas_valor>>` que entregó `etapa-5` — mismo texto, mismo orden, sin resumir (invariante 3) |

───────── .claude/skills/fase-1-angulos/SKILL.md ─────────

CAMBIO S.1 — PASO 4, viñeta de etapa-4
  ANTES:   del operador (días de resultado, dosis, momento de uso, estadísticas, FAQs). Output: 6 copies +
             **ad-imagen** (Prompt Maestro) para los 6 ángulos (F1 es TODO IMAGEN) + **3 infografías del
             bot** e IMAGEN 4 opcional.
  DESPUÉS: del operador (días de resultado, dosis, momento de uso, estadísticas, FAQs), `producto_key` y
             `carpeta_producto` (el `slug_carpeta` de `_DIM_PRODUCTOS.csv`). Output: 6 copies +
             **ad-imagen** (Prompt Maestro) para los 6 ángulos (F1 es TODO IMAGEN). Las **3 infografías
             del bot** (e IMAGEN 4 opcional) las escribe la etapa en
             `PRODUCTOS/[carpeta_producto]/INFOGRAFIAS.md`; no vuelven en el output.

CAMBIO S.2 — PASO 4, viñeta de etapa-5
  ANTES:   `producto_key`, `<pagina_asignada>`. Output: **las 9 frases del ángulo** para
  DESPUÉS: `producto_key`, `carpeta_producto`, `<pagina_asignada>`. Output: **las 9 frases del ángulo** para
  y en la misma viñeta:
  ANTES:   son suyos**: los declara `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`.
  DESPUÉS: son suyos**: los declara `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`. Los bloques de juicio los escribe la
             etapa en `PRODUCTOS/[carpeta_producto]/BLOQUES_BOT.md`; no vuelven en el output.

CAMBIO S.3 — PASO 6
  ANTES:   - `1_HACER_MANUAL.txt` — **todo lo que el operador ejecuta a mano**, en orden y listo para copiar/pegar.
  DESPUÉS: - `1_HACER_MANUAL.txt` — **todo lo que el operador ejecuta a mano**. No se escribe con Write: lo
             genera `python Ads/_TOOLS/gen_manual.py [producto_key] --escribir` después de escribir
             `2_DATA_PRODUCTO.txt`. Si bloquea, nombra qué falta y quién lo produce: se produce ese dato
             y se vuelve a correr; nunca se completa a mano.

CHEQUEOS FINALES (todos deben cumplirse)
  1. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  2. python evals/run_baseline.py → la misma línea TOTAL=… que anotaste.
  3. rg -n "^tools:" .claude/agents/ETAPA-4.md .claude/agents/ETAPA-5.md → "tools: Read, Write" en los dos.
  4. rg -c "INFOGRAFIA:" .claude/agents/ETAPA-4.md → 4.
     rg -c "BLOQUES_BOT.md" .claude/agents/ETAPA-5.md → 5 o más.
     rg -c "gen_manual.py" .claude/agents/ETAPA-GUARDAR-PRODUCTO.md .claude/skills/fase-1-angulos/SKILL.md → al menos 1 en cada uno.
  5. git diff --stat → solo los 4 archivos; ninguno pierde más de 25 líneas.
  6. Commit en la rama actual, solo esos 4 archivos, sin push, sin atribución:
     git commit -m "feat(etapas): stages persist bot blocks and infographics, FASE 1 manual is generated"

SI ALGO NO CUADRA (un texto «ANTES» no aparece exacto, pytest o los evals cambian de
  resultado): DETENTE y reporta el cambio que no pudiste aplicar.

ENTREGA: los chequeos 1 a 5, el hash del commit y el `git diff` completo de los 4 archivos.
```

3B-3B HECHA 30-sep (commit `4e5eb60`, diff revisado línea por línea por Claude; pytest 56, evals
27 PASS + 1 conocido). La prueba real es la primera FASE 1 que corra después; vuelta atrás:
`git revert 4e5eb60`.

#### PARTE 3B-3C — LOS DUEÑOS NUEVOS, EN EL MAPA DE `CLAUDE.md`

Copiar el bloque y pasárselo a la IA ejecutora.

```
TAREA: agregar 3 filas a la tabla «MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ» de CLAUDE.md (el
de la raíz del repo). Nada más.

Archivo que puedes modificar (SOLO este): CLAUDE.md
PROHIBIDO: tocar cualquier otra línea de CLAUDE.md, renumerar invariantes, o tocar
  .claude/skills/reglas-sistema/ a mano.

ANTES DE EMPEZAR
  1. git status --short CLAUDE.md → vacío.
  2. python -m pytest Ads/_TOOLS -q → 56 passed.

CAMBIO — busca la fila de la tabla que empieza exactamente con
    | Infografías del bot: motor compartido |
  e inserta, inmediatamente DESPUÉS de esa fila (sin línea en blanco), estas 3 filas:

| Bloques de juicio del bot, por producto (los 4 campos del catálogo, testimonios, audio, M2, FAQ) | `PRODUCTOS/[carpeta]/BLOQUES_BOT.md` — lo escribe `etapa-5`; lo inserta `Ads/_TOOLS/gen_flujo_bot.py` |
| Prompts de infografías del bot, por producto | `PRODUCTOS/[carpeta]/INFOGRAFIAS.md` — lo escribe `etapa-4` |
| `1_HACER_MANUAL.txt` de FASE 1: se GENERA, nunca se tipea ni se edita a mano | `Ads/_TOOLS/gen_manual.py` (plan de `gen_lanzador.py` + flujo de `gen_flujo_bot.py` + `INFOGRAFIAS.md`; bloquea nombrando qué falta y quién lo produce) |

CHEQUEOS FINALES
  1. git diff --stat CLAUDE.md → 3 inserciones, 0 borrados.
  2. python -m pytest Ads/_TOOLS -q → 56 passed, 0 failed.
  3. git status --short .claude/skills/reglas-sistema → vacío (esa skill sale de otras
     secciones de CLAUDE.md; si cambió, DETENTE y reporta).
  4. Commit en la rama actual, solo CLAUDE.md, sin push, sin atribución:
     git commit -m "docs(claude-md): declare owners of bot blocks, infographics and the generated manual"

SI ALGO NO CUADRA (la fila ancla no aparece, un hook modifica otros archivos, un test falla):
  DETENTE y reporta.

ENTREGA: los chequeos 1 a 3 y el hash del commit.
```

Queda pendiente después de la 3B-3 (no entra en estas guías):

- El mensaje prellenado que deriva `gen_flujo_bot.py` dice «con registro INVIMA»; OVULOS se lanzó
  sin esa frase porque el registro no está. Decidir si el mercado CO lo lleva mientras no haya INVIMA.
- `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5 y el PASO 5 de la skill `fase-1-angulos` todavía enuncian
  la fórmula 7 × $/conversación como regla; con el CSV como dueño pasa a ser el criterio para
  recalibrar la fila, no un cálculo por producto. Redacción a cargo del operador.
- El manual de FASE 2 y FASE 4 sigue tipeado (`gen_lanzador.py` solo lee `_PLAN.json`).
- La «entrega interactiva en el chat» vuelve a tipear el manual completo en la conversación; es la
  salida más cara que queda. Es preferencia declarada del operador: decide él.
- `lanzador_html.py` y `app_html.py` tienen su propia copia del checklist de Meta (Parte 5).
- La hora del plan es el literal «4:00 AM» y el CSV trae `tz_offset` de Guatemala (para CO va a
  mano, ya declarado en `_faltantes` de OVULOS).
- `gen_publicacion.py` tiene `countries: ["GT"]` fijo y bloquea cuentas que no facturan en USD (Parte 2C).

## Hallazgos que originaron la 3B-3

Resueltos así: 1 → 3B-3A paso 4 · 2 y 3 → paso 6 · 4 → paso 1 · 5 → sin cambio (ver decisiones) ·
6 → paso 3 · 7 → paso 2 · 8 → 3B-3B · 9 → sigue fuera de la limpieza.

Comparación del manual generado (`_OPERADOR/LIMPIEZA/3B2_OVULOS_manual.txt`, 1.243 líneas) contra el
tipeado de OVULOS (1.298 líneas). El generado trae las REGLAS del bot y los pendientes del lanzador,
que el tipeado no traía. Le falta lo que el tipeado sí traía y hoy no tiene dueño en datos:

1. Configuración fija de Meta por conjunto: Advantage+ Audience OFF, desmarcar anuncios
   multianunciantes y «personas de WhatsApp con edad desconocida», CTA «Enviar mensaje», destino
   WhatsApp, revisar «Maximizar conversaciones» justo antes de publicar, cero «- Copia», no aceptar
   recomendaciones. Candidato a dueño: `_PARAMETROS_PUBLICACION.csv` + una lista fija en
   `gen_lanzador.py`.
2. Mensaje prellenado del anuncio: lo deriva `gen_flujo_bot.py` (sección 2.6 de la plantilla); el
   manual debe imprimirlo en la sección E.
3. Imagen de referencia de cada prompt de anuncio (packshot / referencia F1): `_DIM_ENVASE.csv` y
   `_DIM_REFERENCIA_F1.csv`.
4. Presupuesto de FASE 1 con dos respuestas: `_PARAMETROS_PUBLICACION.csv` dice 2.99 fijo (lo que
   usó el manual tipeado y el lanzamiento de OVULOS) y `gen_lanzador.py` aplica 7 × $/conversación
   acotado a 2.99–3.95 (da 3.95, usando el costo por conversación del portafolio de GT para un
   producto de CO). Dejar un solo dueño.
5. `anuncios_por_conjunto`: 1 en `_PARAMETROS_PUBLICACION.csv`, 2 en `ETAPA-6.md`.
6. Monto del presupuesto en la moneda de la cuenta (el tipeado daba COP; el generado da US$).
7. `gen_lanzador.py` recalcula la fecha y el nombre de campaña cada día, aun después del
   LANZAMIENTO (muestra TEST_20261001 para una campaña lanzada como TEST_20260930).
8. Quién escribe `BLOQUES_BOT.md` e `INFOGRAFIAS.md` en un producto nuevo: `etapa-5` y `etapa-4`
   solo tienen `Read`; hoy el contenido viaja por el orquestador a `etapa-guardar-producto`.
   Cambiar prosa de etapas exige correr `evals/run_baseline.py` antes y después.
9. Fuera de la limpieza, pendiente de OVULOS: `0_INPUTS_CONGELADOS.md`, `1_HACER_MANUAL.txt` y
   `2_DATA_PRODUCTO.txt` siguen con la escalera vieja; `verificar_producto.py` no compara la escalera.

---

## PARTE 1 — INVENTARIO (solo lectura) · HECHA

Bloque que se le pasó a la IA ejecutora.

```
TAREA: inventario del SISTEMA. Es SOLO LECTURA: no modifiques, muevas ni borres ningún archivo
existente. Los únicos archivos que creas son los 3 de "SALIDAS".
Carpeta de trabajo: la raíz del repo SISTEMA.

SALIDAS (crear la carpeta _OPERADOR/LIMPIEZA/):
  1. _OPERADOR/LIMPIEZA/INVENTARIO.csv
  2. _OPERADOR/LIMPIEZA/DESVIOS.md
  3. _OPERADOR/LIMPIEZA/GRAFO.txt

─── SALIDA 1: INVENTARIO.csv ───
Una fila por archivo del ALCANCE. Escribir con el módulo csv de Python (campos con comas entre
comillas). Columnas, en este orden:
  ruta          ruta relativa con barras /
  tipo          AGENTE | SKILL | DOCTRINA | SCRIPT | TEST | DATO | VISTA | APP | OTRO
  taller        NUCLEO | FABRICA | OPERACION | PANTALLA | HERRAMIENTA
  lo_leen       rutas de los archivos que lo mencionan, separadas por " ; " (máx. 10)
  n_lectores    cuántos archivos lo mencionan (sin contarse a sí mismo)
  tokens        tamaño en bytes / 3.6, redondeado (solo para .md; vacío en el resto)
  ultimo_commit fecha de `git log -1 --format=%ad --date=short -- <ruta>`
  estado        VIVO | DUPLICADO | MUERTO | DUDA
  evidencia     una línea que justifique el estado

ALCANCE (solo esto):
  .claude/agents/*.md · .claude/skills/*/SKILL.md · .claude/settings.json · CLAUDE.md
  DOCTRINA/** (todos los archivos) · Ads/_TOOLS/*.py y *.md
  PRODUCTOS/_*.csv y PRODUCTOS/_*.json (solo la raíz de PRODUCTOS)
  VISTAS/* · y UNA fila por carpeta para: app/backend, app/frontend, warehouse, evals, db, odd
FUERA DEL ALCANCE: carpetas de producto, Ads/MEDIA_*, Ads/_INGESTA, Ads/_SWIPE,
  Ads/1.2 Transcripcion videos, _CONOCIMIENTO, _ROADMAP, _SKILLS_FUENTE, _RESPALDOS, INFPRODUCTOS.

CÓMO SABER QUIÉN LO LEE: buscar el NOMBRE del archivo (sin carpeta) en todo el repo con
  rg -l --fixed-strings "<nombre>" --glob "!_RESPALDOS/**" --glob "!_CONOCIMIENTO/**"
  y descontar el propio archivo. Un TEST cuenta como lector.

CÓMO ASIGNAR EL TALLER (por defecto; si la evidencia dice otra cosa, ponlo y explícalo):
  NUCLEO: FLUJO.json, flujo.py, decidir.py, costear.py, mercado.py, alias.py, registrar_evento.py,
    verificar_*.py, PRODUCTOS/_DIM_*.csv, _FACT_*.csv, _PARAMETROS_*.csv, _EVENTOS.csv, CLAUDE.md
  FABRICA: agentes etapa-producto, 0, 1, 1b, 2, 3, 4, 5, 6, 9, render, guardar-producto;
    skills buscar-producto, fase-1-angulos, fase-2-conceptos, generar-conceptos,
    generar-imagenes-chatgpt, publicar-meta; gen_plan, gen_flujo_bot, gen_publicacion,
    gen_lanzador, armar_prompts_*; DOCTRINA COPYWRITING_ADS, PLANTILLAS_*, PARAMETRIZACION_ADS
  OPERACION: agentes etapa-7, 10, 11; skills ciclo-diario, recopilar-lucidsales, fase-3-flujo,
    fase-4-escalado; ingerir_*, bajar_lucidsales, gasto.py; DOCTRINA CALENDARIO_ESCALADO,
    ESCALADO_PLAYBOOK, DATA_PLAYBOOK, CONTABILIDAD
  PANTALLA: app/, VISTAS/, gen_app.py, app_html.py, lanzador_html.py
  HERRAMIENTA: gen_grafo.py, tests, evals, warehouse, db, odd

CÓMO ASIGNAR EL ESTADO:
  VIVO       tiene al menos un lector, o lo nombra CLAUDE.md, DOCTRINA/FLUJO.json,
             VISTAS/_MANIFIESTO.json o un hook de .claude/settings.json.
  DUPLICADO  repite una regla o un dato que vive en otro archivo. En evidencia: el otro archivo
             y la regla repetida en pocas palabras. Solo si lo leíste en los dos archivos.
  MUERTO     cero lectores Y no lo nombra ninguno de los 4 de VIVO.
  DUDA       cualquier caso en que no estés seguro. Nunca adivines: usa DUDA.

─── SALIDA 2: DESVIOS.md ───
Buscar con rg en Ads/_TOOLS/*.py, .claude/**, DOCTRINA/** y anotar cada hallazgo como
"ruta:línea — texto — por qué es un desvío". Cuatro secciones:

  A. BLOQUEOS QUE MANDAN A HACERLO A MANO
     rg -n -i "BLOQUEADO|a mano|manualmente|hazlo manual" 
     Anotar solo los casos en que el texto dice que, si falla, el operador lo resuelva a mano.

  B. LITERALES DE MERCADO METIDOS EN CÓDIGO O PLANTILLA (deberían salir de _DIM_MERCADOS.csv)
     rg -n "Guatemala|Colombia|GTQ|COP|INTERRAPIDISIMO|ENVIA|Cargo Expreso|Forza|MSPAS|INVIMA" Ads/_TOOLS/*.py DOCTRINA/PLANTILLAS_*.md
     rg -n "\b(vos|sabés|pagás|podés|tenés|Contame|Decime|Confirmame)\b" Ads/_TOOLS/*.py DOCTRINA/PLANTILLAS_*.md
     rg -n "\"Q\"|'Q'|Q%|Q{" Ads/_TOOLS/*.py
     Excluir los tests y las líneas que LEEN el valor desde _DIM_MERCADOS.

  C. REGEX DE PROHIBICIONES SIN \b AL INICIO
     rg -n "PROHIBIDO|prohibid" Ads/_TOOLS/*.py y revisar cada patrón: anotar los que pueden
     calzar dentro de otra palabra (ejemplo real: "cura" calza en "frescura").

  D. MISMA REGLA ESCRITA EN DOS LUGARES
     Solo los casos que encontraste al llenar DUPLICADO en el inventario, agrupados por regla.

─── SALIDA 3: GRAFO.txt ───
  python Ads/_TOOLS/gen_grafo.py > _OPERADOR/LIMPIEZA/GRAFO.txt
  (sin --escribir: no debe tocar ningún otro archivo)

─── CHEQUEOS ANTES DE ENTREGAR ───
  1. python -c "import csv;r=list(csv.DictReader(open('_OPERADOR/LIMPIEZA/INVENTARIO.csv',encoding='utf-8')));print(len(r))"
     debe imprimir el número de filas sin error.
  2. Ninguna fila con estado vacío; ninguna MUERTO o DUPLICADO sin evidencia.
  3. git status: los únicos cambios nuevos son los 3 archivos de _OPERADOR/LIMPIEZA/.
     Si aparece cualquier otro archivo modificado por ti, revertirlo y avisar.

ENTREGA: un resumen de 10 líneas máximo con: total de filas, cuántas por estado, cuántas por
taller, y los 5 hallazgos más graves de DESVIOS.md. No propongas arreglos: eso es la Parte 2.
```
