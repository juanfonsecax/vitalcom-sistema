# HANDOFF DE SESIÓN — 2026-09-03

> Para pegar al inicio de una sesión nueva de Claude Code y continuar sin re-derivar nada.
> Repo: `C:\Users\juand\Downloads\AGENTES LUCID\Profesional en Eccomerce gestion\SISTEMA`

---

## 0. CÓMO TRABAJAR EN ESTA SESIÓN (reglas que puso el operador)

- El sistema se auditó y optimizó el **2026-09-02**. Leer primero
  `PRODUCTOS/_AUDITORIAS/_AUDITORIA_SISTEMA_20260902.txt` y
  `PRODUCTOS/_AUDITORIAS/_AUDITORIA_INSTRUMENTOS_20260903.txt`.
- **Se puede proponer arquitectura, pero SIEMPRE con medición antes y después, y avisando antes de
  tocar.** Si una decisión parece rara, su razón está en esas dos auditorías.
- Las cifras de costeo salen de `Ads/_TOOLS/costear.py`. Nunca de memoria.
- Antes de cerrar un producto: `python Ads/_TOOLS/verificar_producto.py [PRODUCTO_KEY]`.
- Registro maestro: `PRODUCTOS/_DIM_PRODUCTOS.csv`. `_PORTAFOLIO.txt` es bitácora.
- **Medir siempre con** `python Ads/_TOOLS/gen_grafo.py --comparar`.

---

## 1. QUÉ SE HIZO HOY — 6 commits en `main`

```
(pendiente) Correcciones de estado del #4
b13b0cd  Los 15 documentos de doctrina se van a DOCTRINA/; la raíz baja de 19 sueltos a 4
59b5964  Cerrar los tres hallazgos: dos eran falsos positivos del propio gate
515f907  Registrar la auditoría de instrumentos externos dentro del propio sistema
3afe698  Partir PLANTILLAS_INFOGRAFIAS.md: el motor enruta, las plantillas se cargan aparte
4838e83  gen_grafo.py: el gate de reconciliación, pero del sistema
85887a9  Sacar las dos skills polizonas de .agents/
ab27fc6  (la auditoría del 2026-09-02, punto de partida)
```

### 1.1 Se evaluaron 5 repos externos como instrumento de auditoría. **Instalados: cero.**
`obra/superpowers`, `affaan-m/ECC`, `JuliusBrussee/caveman`, `Graphify-Labs/graphify`,
`mattpocock/skills`. Graphify y mattpocock se probaron de verdad en un worktree aislado, ya
eliminado. Detalle completo en `_AUDITORIA_INSTRUMENTOS_20260903.txt`.
**No volver a proponerlos sin leer esa auditoría primero.**

### 1.2 Herramienta nueva: `Ads/_TOOLS/gen_grafo.py`
El gate de reconciliación **del sistema** (el de producto es `verificar_producto.py`). Mide costo en
tokens, nodos dios, huérfanos, rutas muertas y `model: inherit`. `--comparar` da el delta contra
`PRODUCTOS/_AUDITORIAS/_LINEA_BASE_SISTEMA.json`. `--estricto` devuelve 1 si hay hallazgos.
**Hoy devuelve exit 0: sistema limpio.**

### 1.3 Ahorros medidos
```
FASE 1   325.624 → 290.594 → 292.595 tok     (split infografías −35k; reorg +1,7k)
FASE 2   389.181 → 354.592 → 356.973 tok
arranque en frío        6.064 → 6.256 tok
```
`PLANTILLAS_INFOGRAFIAS.md` se partió en motor + `_FLUJO` + `_OPCIONALES`.
Los 15 documentos de doctrina viven ahora en `DOCTRINA/`.

**Lección anotada:** al estimar el costo de una reescritura masiva hay que multiplicar por
HERENCIA, no por archivo. Se estimó +112 tok y salieron +1.717 (15×).

---

## 2. EL DIAGNÓSTICO DEL NEGOCIO (esto es lo que importa)

Base: 2026-07-01 → 2026-09-01, filas `rol_ventana = BASE` de `_FACT_VENTAS.csv`.

```
Gasto $5.603,65  ·  884 ventas  ·  10.824 conversaciones
CPA global $6,34  ·  CIERRE GLOBAL 8,17 %  ·  $0,52 por conversación
```

### La palanca #1, cuantificada
Cierre 8,17 % contra 15-20 % de los mentores. **Con el mismo gasto**, a 15 % serían **1.624 ventas
en vez de 884: +84 % de ingresos, cero dólares extra.** CPA caería de $6,34 a $3,45.

### Cierre por ángulo
```
TINNIDROP  3.002 msgs · 262 ventas · 8,73 % · CPA $6,48
   PERDIDA_AUDITIVA     1.446 msgs ·  85 v ·  5,88 % · $8,42   ← 3,5× tráfico, PEOR cierre
   DETERIORO_COGNITIVO    835 msgs ·  83 v ·  9,94 % · $6,66
   ACCESIBILIDAD_MEDICO   406 msgs ·  47 v · 11,58 % · $4,21   ← el GANADOR declarado
   ME_DIJERON_NO_CURA     195 msgs ·  22 v · 11,28 % · $6,38
CLEARSTEM  1.106 msgs · 124 ventas · 11,21 %
   ANTI_FALSIFICACION     188 msgs ·  34 v · 18,09 % · $5,98   ← ver corrección abajo
NUSAVA       893 msgs ·  62 ventas · 6,94 %
VARICOSE     391 msgs ·  13 ventas · 3,32 %  (producto muerto, ver §4)
```

**Dos hallazgos de esta tabla:**
1. El ganador declarado (`ACCESIBILIDAD_MEDICO`) recibe el 13 % del tráfico; el peor cierre recibe
   3,5× más presupuesto. Si se confirma, no es problema de texto del bot: es **asignación de
   presupuesto que no siguió al ganador que el propio sistema declaró.**
2. ⚠️ **CORREGIDO POR `etapa-11` (2026-09-03).** Se afirmó que el 18,09 % de
   `CLEARSTEM/ANTI_FALSIFICACION` probaba que "el 15-20 % es alcanzable con esta infraestructura de
   bot". **Es falso.** `_EVENTOS.csv` línea 15 registra `2026-07-10 · CLEARSTEM · CAMBIO_BOT · "Bot
   NUEVO del relanzamiento — VARIABLE DE CONFUSIÓN sin aislar"`, más un `CAMBIO_CREATIVO` el mismo
   día. CLEARSTEM corre **otro bot**, estrenado. La lectura correcta: *hay un bot y un ángulo que
   llegan a 18 % y nadie sabe cuál de los dos lo produjo.* Es argumento a favor del A/B, no prueba.
3. ⚠️ **El cierre de TINNIDROP es 8,29 %, no 8,73 %.** Las 13 filas `SIN_ATRIBUCION` tienen
   **0 mensajes y 1 venta cada una**: entran al numerador sin denominador. El JOIN cierra al 100 %
   de los mensajes y 95 % de las ventas.

---

## 3. EL DIAGNÓSTICO ESTRUCTURAL (una sola frase)

> **El sistema observa excepcionalmente bien y cierra el lazo el 14 % de las veces.**

| Detectado | Cerrado |
|---|---|
| 22 anomalías logueadas con precisión quirúrgica | 3 resueltas (14 %) |
| 8 creativos generados | 0 publicados en 39 días |
| 4 productos LISTO con paquete completo | 0 lanzados · 234 días-producto |
| 4 brazos del test T01 declarados CONFIRMADO | 0 existieron jamás |
| El cierre identificado como palanca #1 en `CLAUDE.md` | 1 `CAMBIO_BOT` en 61 días |

La detección es de primer nivel. Lo que falla es el cierre del lazo. **Cualquier propuesta de
agregar máquina al sistema debe justificarse contra este número.**

---

## 4. ESTADO DE LOS 5 PUNTOS DE ACCIÓN

Orden acordado con el operador. **Decidió: arreglar el cierre primero, dejar los 4 productos
parados.**

- **#1 · Arreglar el cierre — `etapa-11` COMPLETADA.** Informe:
  `PRODUCTOS/_AUDITORIAS/_FLUJO_TINNIDROP_20260903.txt` (653 líneas). **Leerlo antes de tocar nada
  del bot.** Su conclusión da vuelta la hipótesis de partida:

  > **TINNIDROP no tiene un problema de flujo demostrado: tiene un problema demostrado de A QUIÉN
  > le compra los mensajes.**

  · 🔴 **EL HALLAZGO.** `PERDIDA_AUDITIVA` corre en dos bandas de edad contra un avatar 45-60:
    **45-60 → 7,48 %** (69/923) · **25+ (GTR0) → 3,06 %** (16/523). Fisher **p=0,00044**. Mismo
    ángulo, mismo creativo, mismo bot, mismo número, misma cuenta. **Un texto de flujo idéntico no
    puede cerrar 7,48 % y 3,06 % a la vez** → es cuasi-experimento: para esa celda descarta el
    flujo como causa. En GTR7 a 45-60 el mismo ángulo cierra 9,13 %, sano.
  · 🔴 **ESA CELDA SIGUE PRENDIDA** al 01-sep: Q2.051 gastados a **CPA Q128 contra break-even
    Q71,56**, once días después de que `APR-060` registrara "25+ cierra 4× peor". En los últimos
    7 días es **el 49 % del tráfico del producto**. Es plata saliendo ahora.
  · **Reparto de presupuesto (16 días):** `PERDIDA_AUDITIVA` **62,6 % del gasto** cerrando 5,93 %
    a CPA Q71 = *exactamente* el break-even (margen cero) · `ACCESIBILIDAD_MEDICO` **9,2 %**
    cerrando 14,29 % a CPA Q30. Reasignar es de `etapa-8`, no de `etapa-11`.
  · **No hay cinco flujos que arreglar, hay uno.** Excluyendo `PERDIDA_AUDITIVA`: χ²=0,932, df=3,
    **p=0,818** — los otros cuatro son homogéneos a 10,54 %. El ganador declarado lo es por VENTA
    y por CPA, **no por superioridad de cierre demostrada** (empata con ME_DIJERON_NO_CURA).
  · **Desajustes ad↔bot citables** para el brazo A: C1 (el bot abre con "en un momento una asesora
    se pondrá en contacto" — saludo neutro que anuncia espera), C2 (INT 2 habla de mecanismo, el ad
    ganador habla de plata y médicos), C3 (el ad dice "+10.200", el bot "+12.000"), C5, C6.
    C4 (entrega) está congruente: no se toca.
  · **El A/B es viable sólo en TINNIDROP** (72,4 msj/día; n=358/brazo). Pero el brazo B a
    7,0 msj/día tardaría 51 días: **reasignar presupuesto no es sólo la palanca más rentable, es la
    precondición para que el test exista.**

  🔴 **GATE DURO ANTES DE QUE `etapa-5` ESCRIBA:** `1_HACER_MANUAL.txt` **no es el flujo actual**.
  Dice textual *"NO se rehace el bot. Se CONSERVA el bot que el operador ya tiene cargado"* y que
  el flujo de abajo queda como REFERENCIA/RESPALDO. **Todo el PASO 3 del informe es PROVISIONAL
  hasta que el operador exporte el flujo real de LucidBot.**

  `etapa-11` **no anexó filas a `_EVENTOS.csv`** — la regla 10 dice loguear *el día que se aplica*.
  Quedan listas en la sección 7 del informe con `[FECHA_APLICACION]`.
- **#2 · Los 12 creativos — CERRADO.** No era una fábrica detenida: los 8 de TINNIDROP **existían
  en disco desde el 26-jul** y estaban mal etiquetados. Corregidos a `GENERADO` + evento
  `CORRECCION_ESTADO`. Los 4 de CLEARSTEM sí faltan producir. **El cuello era PUBLICAR.**
- **#3 · Los 4 productos LISTO — DECISIÓN TOMADA: se quedan parados** hasta que el cierre esté
  arreglado, porque cada lanzamiento nuevo hereda la ineficiencia del 8 %.
  ⚠️ **Pendiente: registrar esa decisión** en `_DIM_PRODUCTOS.csv` (notas) y `_EVENTOS.csv`, para
  que sea un HOLD con condición de reingreso y no deriva.
  **7 de las 10 FanPages están libres**: el bloqueo no es escasez, es cableado manual en Meta.
- **#4 · Anomalías — DIAGNOSTICADO, correcciones pendientes.** Ver §5.
- **#5 · Congelar el sistema** hasta que corra una FASE 1 completa y el cierre se mueva.

---

## 5. LO QUE QUEDÓ ABIERTO, CONCRETO

### Correcciones de data que puede hacer Claude (no se hicieron por no pisar a `etapa-11`)
1. **VARICOSE** figura `VIVO/ESCALADO` en `_DIM_PRODUCTOS.csv` pero **no gasta desde el 11-ago**
   (últimas ventanas: $0,00). Pasar a `PAUSADO` con la evidencia. Su cierre de 3,32 % es el
   epitafio de un producto muerto, **no un problema vivo** — no contamina más los promedios.
2. **T01 en `_TESTEOS.csv`**: 4 brazos (A/B/C/D) en `CONFIRMADO` con `fecha_inicio 2026-08-20`,
   verificado en 10 días que **nunca existieron como conjunto**. Marcar que no arrancó **sin borrar
   los brazos** (no son duplicados).
3. **16 filas BASE sin `conjunto`** (13 TINNIDROP, 2 CLEARSTEM, 1 NUSAVA) arrastran 16 ventas sin
   ángulo atribuible. Documentar; **no inventar atribución.**

### Sólo puede hacerlo el operador
4. 🔴 **El conector MCP de Meta.** CONFIRMADO en esta sesión: la tarea programada nocturna corría
   **en Claude chat, no en Claude Code**, y por eso no tenía herramientas `ads_*` (el log dice
   "lo único expuesto es Google Drive"). **Recrear esa tarea programada en Claude Code cierra 6 de
   las 22 anomalías.**
5. 🔴 **`_FACT_ENTREGA.csv` congelada en 2026-08-25 — 9 días de atraso.** `_FACT_VENTAS` sí llega al
   01-09. En contraentrega **la entrega es el dinero**: falta el export de Dropi.

### Pregunta abierta que quedó sin responder
6. 🔴 **EXPORT SEMANAL DE CONVERSACIONES DE LUCIDBOT.** `etapa-11` lo declara *"el input más barato
   y de mayor retorno pendiente en todo el sistema"*. Sin chats se puede decir DÓNDE se pierde la
   venta pero nunca POR QUÉ, y las FAQ nuevas quedan **entregadas vacías a propósito** (proponerlas
   por intuición sería el "cambio sin evidencia" que el brief no admite).
7. **¿Con qué cadencia debe entregar cada fuente de data?** El operador venía pasando Meta,
   LucidSales, Dropi y tarjetas; las tarjetas y (cree que) Dropi eran mensuales. Hay que definir la
   cadencia **por fuente**, basada en para qué se usa cada una y en el ciclo de maduración de la COD
   (~10 días). **Esta era la siguiente pregunta cuando se cortó la sesión.**

---

## 6. OBJETIVO DE FONDO DEL OPERADOR (declarado, aún sin detallar)

Usar este sistema como **base replicable para escalar a muchos sistemas / muchos productos**, con
recolección de data sistemática que quede en forma clara y consultable. Dijo que lo explicaría en
extenso más adelante.

Señales del repo relevantes para eso, ya detectadas:
- **La capa de data es el activo real del proyecto**, más que las 16 etapas: 2.475 ventas, 406
  entregas, 78 aprendizajes, 65 eventos, 22 CSV **con dueño declarado**. Eso ya es un esquema de
  base de datos aunque nadie lo llamó así.
- El camino técnico hacia multi-operador sería CSV → SQLite con `operador_key`, y `costear.py` +
  `verificar_producto.py` como los dos primeros endpoints. **No dimensionado todavía.**

---

## 7. ADVERTENCIA PARA LA SESIÓN NUEVA

El riesgo dominante de este proyecto **no es que falte máquina: es que sobra detección y falta
cierre de lazo (14 %)**. Los últimos tres días se fueron en el meta-sistema —tokens, gates,
carpetas— y no movieron una sola cifra del negocio. Antes de proponer cualquier refactor, preguntar
qué número del §2 se va a mover.
