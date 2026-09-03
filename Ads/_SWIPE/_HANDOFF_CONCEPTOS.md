# HANDOFF — CONCEPTOS CREATIVOS

> **Punto de entrada único de esta línea de trabajo.** Reemplaza la versión anterior (barrido del
> swipe → `_HANDOFF.md`, ya cerrado). Última actualización: **2026-08-19**.
>
> **Estado:** el catálogo de conceptos está **CERRADO y bajado al sistema**. Lo que sigue es
> (a) validarlo con data propia y (b) producir creativos con él.

---

## 0. QUÉ SE HIZO, EN UNA PÁGINA

1. **Se construyó el catálogo de conceptos** cruzando dos muestras independientes: 36 creativos elegidos por data (supervivencia + réplicas) y **111 favoritos elegidos a ojo por el operador**. 133 creativos únicos, 39 anunciantes. **76 % de los favoritos cayó dentro de los conceptos derivados por data** → el catálogo quedó validado por convergencia.
2. **Quedó en 8 conceptos.** Tres los aportó la selección manual (`C7_DESEO`, `C8_PROGRESION`, `C9_COMPARACION`), que la muestra por supervivencia no podía ver.
3. **Se resolvió una contradicción del sistema:** el Prompt Maestro mandaba rotar estilo anti-fatiga en cada ad, lo que hacía imposible medir el ángulo en FASE 1.
4. **Se bajó todo al sistema** — `concepto_key` en el CSV, regla de `ETAPA-2` reescrita, prompt nuevo, doctrina en `CLAUDE.md`.
5. **Se armaron 3 herramientas:** banco de creativos, verificador de huella y registro visual de testeos.

---

## 1. DECISIONES CERRADAS — no re-litigar

### 1.1 Ángulo ≠ Concepto, y qué se fija en cada fase
```
ÁNGULO  = por qué duele
CONCEPTO = cómo se muestra     ← son ortogonales

FASE 1 → 6 ÁNGULOS distintos × concepto FIJO (C2_BENEFICIOS)   ← mide el ÁNGULO
FASE 2 → 1 ángulo (el ganador) × 6 CONCEPTOS distintos          ← mide el CONCEPTO
```
En FASE 1 los 6 creativos comparten layout, paleta y estructura; cambian **solo hook, beneficios, props y avatar**. **No se rotan los 15 estilos anti-fatiga** (son de FASE 2). Con Andrómeda el creativo explica ~56 % del resultado — si ángulo y ejecución se mueven juntos, el testeo no mide nada.

> **No es iteración perezosa.** Iteración perezosa = misma imagen con otro título o color. Seis variantes del mismo concepto, con distinto hook y props, son **seis creativos únicos para Meta**, que detecta duplicados por huella de contenido, no por estructura.

### 1.2 Los 8 conceptos
`C1_OFERTA · C2_BENEFICIOS · C3_SINTOMA · C4_TRANSFORMACION · C5_PRUEBA · C7_DESEO · C8_PROGRESION · C9_COMPARACION`
(`C6_UNBOXING` se retiró: 2 casos en 133, es variante de C5.)

### 1.3 `concepto_control` de FASE 1 = **C2_BENEFICIOS, variante LIGERA**
Elegido por el operador el 19-ago entre 4 finalistas. Es el único que deja el hook sin competencia, usa íconos vectoriales (sirve para **problemas invisibles** como tinnitus o insomnio, donde no hay foto del síntoma) y se reproduce 6 veces cambiando solo texto.
**Descartados:** collage de síntomas y presentación densa (muestran 4-5 problemas a la vez → diluyen el ángulo), progresión (su dispositivo dominante no cambia entre ángulos, se repetiría 6 veces).

### 1.4 Rotación de FASE 2 (6 de los 8)
C2 (control, siempre) · C1 (BOFU, siempre) · C4 · C8 · C5 · + **rotativo**: C3 si el producto es de dolor, C7 si es de estética. C9 queda de reserva.

### 1.5 Las tres capas de producción
El precio **no es parte del layout**, es una variable que se enchufa.
| Capa | Valores |
|---|---|
| **LAYOUT** | `L1 CARTEL VERTICAL` (C1,C2,C3,C7) · `L2 PARTIDO` (C4,C8,C9) · `L3 NATIVO` (C5) |
| **BLOQUE DE PRECIO** | `sin precio` · `1 unidad` · `escalera 1/2/3` |
| **ESTÉTICA** | `cartel` · `orgánico-UGC` |

### 1.6 Metodología de producción: **image-to-image en dos pasos**
```
anuncio de la competencia
   ↓ UNA transformación fuerte (producto, paleta, props, tratamiento)
TU PLANTILLA MADRE  ← asset propio, verificado con check_huella.py
   ↓ image-to-image (cambia solo el texto)
los creativos del test
```
**Nunca subir a Meta la imagen de la competencia, ni un derivado que no pase el verificador.** Las 4 referencias finalistas son **anuncios vivos en Guatemala**: un clon cercano es baneo silencioso (CPM arriba, sin aviso).

---

## 2. ARCHIVOS Y DUEÑOS

| Archivo | Qué es |
|---|---|
| **`_CATALOGO_CONCEPTOS.md`** | **dueño único del CONCEPTO.** Firma, rol de embudo, evidencia y límites de cada uno. PARTE III = decisiones operativas |
| **`_BANCO_CREATIVOS/`** | 48 referencias en 8 carpetas + `_INDICE.csv` + `_LEEME.md`. **Referencias para producir, nunca creativos para pautar** |
| `_CLASIF_FAVORITOS.csv` | los 111 favoritos con `concepto_final`, días, réplicas, anunciante |
| `_ELEMENTOS.csv` | matriz 36 × 30 elementos observables. **Observación humana — no regenerar con script** |
| `_ETIQUETAS_MANUALES.csv` | el export crudo de la galería (los 111 con estrella) |
| `_WINNERS.html` / `_WINNERS_PORTABLE.html` | galería solo de los favoritos, filtrable por concepto y tienda. Se regenera con `gen_winners.py` (`--portable` incrusta las imágenes) |
| `_GALERIA.html` | la galería completa de 597. Se regenera con `gen_galeria.py` |

**Fuera de `_SWIPE/`:**

| Archivo | Qué es |
|---|---|
| `PLANTILLAS_ADS.md` | **PROMPT DE CONTROL FASE 1** (nivel de acabado, no esqueleto) + PROMPT MAESTRO FASE 2 + tabla de qué prompt va en cada fase |
| `Ads/_TOOLS/check_huella.py` | verifica que un creativo no comparta huella con la competencia. `--calibrar` mide el piso del banco |
| `Ads/_TOOLS/gen_testeos.py` | genera `PRODUCTOS/_TESTEOS.html` |
| `PRODUCTOS/_TESTEOS.csv` | definición de los experimentos y sus brazos (se edita a mano) |
| `PRODUCTOS/_TESTEOS.html` | registro visual de testeos con **medidor de evidencia** |

---

## 3. CAMBIOS YA APLICADOS AL SISTEMA

- `PRODUCTOS/_DIM_CONJUNTOS.csv` → columna **`concepto_key`** (25 cols, 93 filas en `SIN_CLASIFICAR`). Backup en `_ARCHIVO/_DIM_CONJUNTOS_pre_concepto_key_20260818.csv`. Dashboard regenerado, JOIN cierra al 100 %.
- `DATA_PLAYBOOK.md` §1 → vocabulario cerrado de `concepto_key` + la tensión con la regla 6.
- `.claude/agents/ETAPA-2.md` → regla de concepto reescrita (distingue iteración perezosa / concepto / variante) + declara `concepto_key`.
- `.claude/agents/ETAPA-4.md` → usa el PROMPT DE CONTROL en FASE 1, **no** elige estilo anti-fatiga, lo rotula en el output.
- `PLANTILLAS_ADS.md` → prompt de control nuevo; los 15 estilos marcados **solo FASE 2**.
- `CLAUDE.md` → sección ÁNGULO vs CONCEPTO + el catálogo entra al mapa de dueños.

---

## 4. LO QUE SIGUE ABIERTO

### Bloqueantes para arrancar el test T01
1. **`conjuntos_meta` está vacío** en los 4 brazos de `_TESTEOS.csv`. Cuando exista la campaña en Meta, llenar con los nombres exactos de los conjuntos → la página empieza a mostrar CPA sola.
2. **Falta el número de días de garantía** para el sello del creativo. Los defaults tienen la garantía como texto, no como días.
3. **El brazo A (collage de síntomas) hay que limpiarlo:** el original dice *"elimina hongos"* y lleva sello **REGISTRO-FDA US**. Ambos violan el compliance. Si se testea sucio, el resultado no dice nada del concepto.

### Decisiones pendientes del operador
4. **¿FASE 2 pasa de 6 microángulos a 6 conceptos?** Recomendado: sí. Implica tocar `ETAPA-3B` y `ETAPA-6` FASE 2. **Es lo que convierte el test T01 en parte del flujo normal en vez de un experimento aparte.**
5. **Tensión de FORMATO:** el swipe da **1:1 en 64 %** de los ganadores contra 17 % de 4:5, y el sistema manda *"4:5 único"*. Es el único choque con margen amplio. Pide un test, no un cambio a ciegas.
6. Nota en `_METODO.md`: "posición" es ranking relativo, no impresiones absolutas.

### Agenda
7. **Re-análisis del swipe ~2026-09-01** (ver `_HANDOFF.md`). La pregunta #1: **¿sobrevive C8_PROGRESION?** Hoy tiene 5 anunciantes y 7 réplicas pero **cero creativos con 21+ días** — tiene forma de tendencia emergente, no de ganador establecido. Calcular supervivencia **por `concepto_key`**.

---

## 5. EL TEST T01 (planificado, no lanzado)

```
Producto:      TINNIDROP   (ya validado: 175 ventas, CPA real Q44, P1u Q179)
Ángulo FIJO:   ME_DIJERON_NO_CURA   ← ya probado en IMAGEN (6 ventas), sin confusión de formato
Formato FIJO:  IMAGEN 4:5 · Precio FIJO · Página FIJA (Sanarte)
Variable:      el dispositivo visual
Brazos:        A collage-síntomas · B ligera · C densa · D progresión
```

**Ojo — la página lo avisa sola:** 3 de los 4 brazos son `C2_BENEFICIOS`. **Este test mide VARIANTE (cuánta información lleva el creativo), no CONCEPTO.** Es una pregunta válida, pero no valida el catálogo. Para validar concepto hacen falta 4 `concepto_key` distintos.

**Cuántas ventas hacen falta por brazo** (potencia para dos tasas de Poisson, α 5 %, potencia 80 %):
| Detectar | ventas/brazo | total | inversión |
|---|---|---|---|
| uno es **3×** mejor | ~10 | 40 | ~$230 |
| uno es **2×** mejor | ~25 | 100 | ~$570 |
| uno es **1.5×** mejor | ~80 | 320 | ~$1.830 |

A $5.98/conjunto/día y CPA Q44 → ~4 ventas/día → **las 100 ventas en unos 25 días**. El test **se paga solo**: cada venta deja ~Q94 de contribución.

**Reglas de lectura:** agregar por `concepto_key`, nunca por conjunto. Réplicas `R[N]` se **suman**, no se comparan. Corte por sangrado a los 10 días (0 ventas con gasto ≥ 2× CPA objetivo), pero **no coronar** hasta llegar al umbral.

---

## 6. TRAMPAS CONOCIDAS

- **La conversación sirve para CORTAR, nunca para CORONAR.** Evidencia propia: tinnidrop-1 tuvo **78 % de conversación y 0 ventas**; ME DIJERON 23 % y es de los que más vende. Nunca declarar ganador por CTR o % de chat.
- **Meta detecta duplicados por huella de contenido, no por estructura.** Pasar `check_huella.py` antes de subir cualquier creativo derivado.
- **El heredoc de Bash rompe** con acentos, comillas y backticks, y se trunca cerca de 20 KB. Para escribir `.md` largos usar la herramienta Write, no `cat <<EOF`.
- **`gen_dashboard.py` termina con exit code 1 en Windows** por un `⚠` que no encodea en cp1252 — el HTML ya se escribió bien. Workaround: `PYTHONIOENCODING=utf-8`.
- **`_WINNERS.html` (75 KB) necesita estar junto a `_IMG/`.** Para mandarlo por chat o abrirlo en otra máquina, usar `_WINNERS_PORTABLE.html` (10 MB, imágenes incrustadas).
- **Las etiquetas de la galería viven en el `localStorage` del navegador**, no en disco. Si no se exportan, se pierden. Los 111 ya están salvados en `_ETIQUETAS_MANUALES.csv`.
- **El texto NO predice el concepto.** El clasificador automático resolvió el 21 %; sobre los 111 favoritos dejó 101 en `REVISAR_VISUAL`. Hay que abrir las imágenes.

---

## 7. PRIMER MENSAJE PARA LA SESIÓN NUEVA

Copiar y pegar:

> Leé `Ads/_SWIPE/_HANDOFF_CONCEPTOS.md` completo, y después `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` PARTE III.
> Contexto: el catálogo de conceptos está cerrado y ya bajado al sistema. Estoy en la fase de producir
> los creativos del test T01 sobre TINNIDROP y de lanzarlo.
> [decime acá qué querés hacer primero]

Según lo que toque:

- **Producir los creativos de T01** → *"Armá la plantilla madre del brazo B (C2 ligera) para TINNIDROP con el PROMPT DE CONTROL de `PLANTILLAS_ADS.md`, y decime cómo verifico la huella antes de subir."*
- **Lanzar el test** → *"Ya creé la campaña. Estos son los nombres de los conjuntos: [...]. Llenalos en `_TESTEOS.csv` y regenerá la página."*
- **Cerrar el pendiente 4** → *"Pasemos FASE 2 de 6 microángulos a 6 conceptos. Tocá `ETAPA-3B` y `ETAPA-6`."*
- **Re-análisis del swipe (~1-sep)** → *"Corré el re-barrido de `_HANDOFF.md` y calculá supervivencia por `concepto_key`. Interesa sobre todo si C8_PROGRESION sobrevive."*
