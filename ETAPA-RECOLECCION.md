# ETAPA-RECOLECCIÓN — Manual del operador (PRE-ETAPA-0)

> Parte **manual** que hace el operador ANTES de abrir el sistema.
> Produce el input principal de FASE 1: las transcripciones TXT de los creativos.
> Objetivo: tener variación creativa suficiente para que ETAPA-0 elija los 6 mejores
> ángulos (validar primero, escalar después).

---

## 1. CUÁNTOS CREATIVOS DESCARGAR

**Por cada producto nuevo: 20 creativos = 10 TikTok + 10 Meta Ads Library.**
(21 también está bien — es lo que ya manejás.)

- Mínimo absoluto: 12 (6 + 6). Por debajo de 6 el sistema se detiene (pre-validación ETAPA-0).
- De los 20, ETAPA-0 selecciona 6 para testear. El resto queda en banco para escalar.

### La regla de saturación (cómo saber cuándo parar)
> **Descargá hasta que 3 videos seguidos NO te aporten un ángulo nuevo.** Ese es el punto
> de saturación y suele caer entre 15 y 20 creativos.

El número grande no existe por el testeo (solo se usan 6): existe para que la **muestra**
contenga todos los ángulos que el mercado ya probó. Si parás en 10, te podés perder el
ángulo que sí vendía.

**Ajuste por número de territorios:** contá cuántos territorios distintos de dolor tiene el
producto y multiplicá por 3-4 videos cada uno. Un producto de un solo territorio se satura
con 12-15; uno con 5-6 territorios (típico de los multi-beneficio: té, colágeno, multivitamínico)
necesita **20-24**, o vas a terminar con territorios de un solo video y sin alternativa para elegir.

### Por qué mitad y mitad
| Fuente | Función |
|---|---|
| **Meta Ads Library** (10) | VALIDACIÓN — lo que la competencia pauta activo HOY ya está probado que vende. Alimenta ETAPA-PRODUCTO y la saturación de ETAPA-2. |
| **TikTok / buscador** (10) | FRESCURA — hooks orgánicos y ángulos aún no quemados en Meta. Da los primeros 5 seg que ETAPA-0 usa como desempate. |

### Cómo buscar
- **Meta Ads Library:** filtrar por país, categoría, estado "Activo". Priorizar anuncios con muchos días corriendo o varias variaciones del mismo anunciante (señal de que escala = vende).
- **TikTok:** buscar por nombre del producto, problema/dolor y categoría. Priorizar videos con muchas vistas/comentarios de compra.
- Buscar **diversidad de formatos** (no 20 testimonios): testimonio personal, educacional, prueba social, anti-falsificación, oferta/precio.

---

## 2. CARPETAS Y NOMBRADO (estructura real del proyecto)

- `Ads/1.1 Videos/`              → videos descargados (lo que Gemini transcribe)
- `Ads/1.2 Transcripcion videos/` → los `.txt` que Gemini genera

Reglas:
1. Descargar los 20-21 videos a `Ads/1.1 Videos/`.
2. Gemini analiza todos y genera un `.txt` por video en `Ads/1.2 Transcripcion videos/`.
3. Nombre del video = nombre de la transcripción (mismo número):
   `5. Nusava B12.mp4` → `5. Nusava B12.txt`.
4. Numerar en orden (1, 2, 3 … 21).

---

## 3. PROMPT DEFINITIVO DE TRANSCRIPCIÓN PARA GEMINI

> **Fuente única:** el prompt vive en `Ads/Prompt-Gemini.txt`. Abrí ese archivo, copialo
> tal cual y pegalo en Gemini junto con los videos. No se duplica acá para evitar que las
> dos copias se desincronicen — si hay que cambiar el prompt, se cambia solo en ese archivo.

El prompt (**v2, 2026-08-01**) produce, por cada video, un `.txt` de **8 bloques**:

| Bloque | Contenido | Quién lo consume |
|---|---|---|
| 1 · HOOK MICROSCOPE | 0-10s desglosado cada 2s en VOZ / IMAGEN / OVERLAY + tipo y fuerza del hook | `etapa-0` (ranking), `etapa-4` (replicar el hook ganador) |
| 2 · CLASIFICACIÓN | dolor en 1ª persona, ángulo, formato, avatar + los 3 campos de vocabulario CERRADO (`avatar_genero`, `avatar_edad`, `emocion_dominante`) | `etapa-0`, `etapa-2`, `_DIM_CONJUNTOS.csv` |
| 3 · SEÑALES DE COMPRA | las **8** exactas que cuenta `etapa-0` + precio + palabras que banean | `etapa-0` (densidad) |
| 4 · TRANSCRIPCIÓN | literal, palabra por palabra | `etapa-2`, `etapa-4` |
| 5 · PERFIL EDITORIAL | duración, cortes/min, arco, subtítulos, música, producción | `etapa-4` (brief de creativo) |
| 6 · ANÁLISIS VISUAL | qué se ve, qué transmite, CTA literal | `etapa-2`, `etapa-4` |
| 7 · MOMENTOS CITABLES | 3-5 frases que funcionan solas | `etapa-4` (banco de hooks) |
| 8 · TRACCIÓN | **lo llena el operador**: fuente, días activo, anunciante, engagement | `etapa-0` (regla de video validado) |

> ⚠️ **Los bloques 1, 2, 3 y 8 son el contrato con `etapa-0`** — sus vocabularios son cerrados
> y sus 8 señales son las que calculan la densidad. Si se tocan, hay que tocar `ETAPA-0.md`
> en el mismo cambio. Los bloques 5 y 7 nacieron de lo que aporta la skill `/watch`
> (pacing editorial y hook microscope) y alimentan a `etapa-4`, no a `etapa-0`.
> Versión anterior en `_ARCHIVO/backups_agentes/Prompt-Gemini_BACKUP_2026-08-01_pre-v2.txt`.

---

## 4. EXTRAS QUE OPTIMIZAN EL SISTEMA (opcionales)

### A. Copy de los anuncios de Meta Ads Library — RECOMENDADO
El texto del anuncio está visible en Ads Library. Copiá el copy de los 10 de Meta en
`Ads/COPYS_COMPETENCIA.txt`.
- **Para qué:** alimenta ETAPA-4 (copy/hooks ya probados) y ETAPA-2 (saturación y redacción de cada ángulo).

### B. Pantallazo de la FanPage de la competencia — ÚTIL
Captura grande de 1-2 páginas fuertes del nicho (foto, bio, productos, tono).
- **Para qué:** ETAPA-FANPAGE (calibración de identidad/tono) y edad de segmentación. Pasarlo en el chat.

### C. Imagen del producto — OBLIGATORIO
Siempre en el chat (adjunta o link). La usa ETAPA-4 (Director de Arte: colores etiqueta/frasco) y ETAPA-1B.

### D. Datos de validación de mercado — OPCIONAL
Nº de proveedores en Dropy + nº de anunciantes activos en Ads Library → ETAPA-PRODUCTO.

---

## 5. CHECKLIST ANTES DE ABRIR EL SISTEMA

```
□ 20-21 creativos descargados (≈10 TikTok + 10 Meta Ads Library) — mín. 12
□ Punto de saturación alcanzado (3 videos seguidos sin ángulo nuevo) — sección 1
□ Cobertura por territorio: cada territorio de dolor tiene ≥3 videos para elegir
□ Diversidad de formatos (no todos testimonios)
□ Gemini transcribió todos con el PROMPT DEFINITIVO v2 (sección 3)
□ BLOQUE 8 (TRACCIÓN) completado a mano en cada .txt de Ads Library
  → días activo + anunciante + variaciones. Es lo que activa la regla de video validado.
□ Videos en Ads/1.1 Videos/[PRODUCTO]/  y  .txt en Ads/1.2 Transcripcion videos/[PRODUCTO]/ (mismo número)
□ Imagen del producto lista (OBLIGATORIO)
□ Costo del proveedor en Q
□ (Opcional) Ads/COPYS_COMPETENCIA.txt de los 10 de Meta
□ (Opcional) Pantallazo de FanPage de competencia
□ (Opcional) Nº proveedores Dropy + anunciantes activos
```

Con esto listo → abrir el sistema y responder "1" (FASE 1).
```
