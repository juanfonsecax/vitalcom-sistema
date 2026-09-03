# 🧑‍💻 MI FUNCIÓN EN EL SISTEMA — Guía del Operador (Vitalcom Guatemala)

> **Para pegar en Notion y copiar al tablero.** Esta es la parte que hace JUAN. El sistema hace todo lo demás.

---

## EN UNA FRASE

**El sistema es el cerebro (estrategia). Yo soy las manos y los ojos.**
El sistema piensa los ángulos, escribe los copies, arma el flujo del bot y diseña la campaña.
**Yo le doy la materia prima, genero las imágenes, configuro el bot, subo todo a Meta y aprieto el botón.**
👉 **Nada se lanza solo. La campaña siempre la activo yo.**

---

## EL CICLO COMPLETO — MIS 5 MOMENTOS

```
[0] RECOLECTO  →  [1] ARRANCO  →  [2] EJECUTO FASE 1  →  [3] LANZO + MONITOREO  →  [4] FASE 2
   (materia prima)  (le doy inputs)   (1_HACER_MANUAL)      (4 AM + día sgte)     (ángulo ganador)
```

---

## 🟦 MOMENTO 0 — RECOLECTAR (antes de abrir el chat)

Esta es la única fase 100% manual. Junto la materia prima:

**Creativos (lo más importante):**
- [ ] **20 creativos** = **10 de TikTok** (frescura/hooks orgánicos) + **10 de Meta Ads Library** (validación: lo que la competencia ya pauta activo HOY).
- [ ] Mínimo absoluto: 12 (6+6). Menos de 6 → el sistema se detiene.
- [ ] **Diversidad de formatos** (no 20 testimonios): testimonio, educacional, prueba social, anti-falsificación, oferta/precio.

**Transcribir con Gemini:**
- [ ] Descargo los 20 videos a `Ads/1.1 Videos/[PRODUCTO]/`
- [ ] Abro `Ads/Prompt-Gemini.txt`, copio el prompt tal cual, lo pego en Gemini con los videos.
- [ ] Guardo cada `.txt` en `Ads/1.2 Transcripcion videos/[PRODUCTO]/` con el **mismo nombre y número** que el video (`5. Nusava B12.mp4` → `5. Nusava B12.txt`).

**Datos del producto (obligatorios):**
- [ ] **Imagen del producto** (foto del frasco) — siempre va en el chat.
- [ ] **Costo del proveedor en Q**.
- [ ] **Dosis / presentación** (ej. B12 5000 mcg, 1.5 ml sublingual).

**Opcionales (mejoran el resultado):**
- [ ] `Ads/COPYS_COMPETENCIA.txt` con el copy de los 10 anuncios de Meta.
- [ ] Pantallazo de la FanPage de 1-2 competidores fuertes.
- [ ] N.º de proveedores en Dropy + N.º de anunciantes activos en Ads Library (valida el producto).

---

## 🟩 MOMENTO 1 — ARRANCAR (abrir el chat y dar los inputs)

Abro el sistema y respondo **"1"** (Fase 1 — Pre-testeo). Después le entrego el bloque de **INPUTS CONGELADOS**. Estos se deciden UNA vez y no se cambian a mitad de camino (si cambian, es rerun completo):

```
PRODUCTO (nombre exacto):   ____________
COSTO_PROVEEDOR_Q:          Q______
DOSIS / PRESENTACIÓN:       ____________
IMAGEN_PRODUCTO:            (adjuntar en el chat)
INGREDIENTES:               ______ (o "pendiente")
PROVEEDORES_DROPY:          ___ (opcional)
ANUNCIANTES_AD_LIBRARY:     ___ (opcional)
TASA_USD_GTQ:               ____ (ej. 7.62)
MCP_ACCOUNT_ID / PAGE_ID / PIXEL_ID:  ____ (si se crea campaña por MCP)
```

> A partir de aquí el sistema trabaja solo: valida el producto, saca 6 ángulos, hace costeo, asigna FanPage, escribe los 6 copies y arma el flujo del bot.

---

## 🟨 MOMENTO 2 — EJECUTAR FASE 1 (mi lista la da el sistema)

Cuando el sistema termina, me deja una carpeta `PRODUCTOS/[PRODUCTO]/` con **`1_HACER_MANUAL.txt`**. Ese archivo ES mi lista de tareas. Lo que el sistema NO puede hacer y hago yo:

1. **Generar las imágenes-ad** de los ángulos sin video → copio el prompt del archivo en Gemini/ChatGPT **adjuntando la foto del frasco**. Las guardo en `Ads/MEDIA_[CUENTA]_[PRODUCTO]/`.
2. **Generar las 3 infografías del bot** (Info 1 beneficios / Info 2 uso / Info 3 confianza) con sus prompts.
3. **Configurar el flujo en LucidBot** copiando campo por campo la sección del archivo.
4. **Subir los creativos a Meta** y revisar los anuncios (preview, copy, precio donde toca).
5. **Activar/programar la campaña a las 4 AM del día siguiente.** ⚠️ Nada se activa solo.

> Si la campaña se crea por MCP, el sistema deja el esqueleto **en PAUSA**; los anuncios y el botón final los pongo yo.

---

## 🟧 MOMENTO 3 — LANZAR Y MONITOREAR

- [ ] Campaña programada a **4 AM del día siguiente** (nunca el mismo día).
- [ ] Estructura: **1 campaña, 6 conjuntos, 2 anuncios por conjunto** (mismo creativo duplicado — baja el CPA hasta 50%).
- [ ] Presupuesto: **$1.59 por conjunto** (igual en los 6, para no sesgar qué ángulo gana).
- [ ] **Al día siguiente (campaña ≥24h):** el sistema ya monitorea **solo cada mañana** (tarea programada, ~7 AM) — recorre `PRODUCTOS/_PORTAFOLIO.txt`, lee Meta por MCP (ETAPA-7) y me deja el **informe + PLAN DE ESCALADO** (ETAPA-8). También lo puedo pedir a mano: *"analizame el rendimiento de hoy"*.
- [ ] **Lo ejecuto yo:** el sistema recomienda (pausar X, subir 20% a Y, crear creativos del ganador Z, Post ID…). El botón lo aprieto yo — el sistema nunca toca campañas vivas.
- [ ] **Agregar otro producto al tracking:** le digo *"agregá [PRODUCTO] al tracking"* y entra al portafolio; la auditoría diaria lo audita junto con los demás.

Lo que YO entrego del monitoreo si no hay MCP: CTR, CPA real, mensajes y conversiones por cada uno de los 6 conjuntos.

---

## 🟥 MOMENTO 4 — FASE 2 (escalar el ganador)

Abro el sistema, respondo **"2"** y le doy:
- [ ] **Ángulo ganador** confirmado (uno de los 6).
- [ ] **Métricas del día** de los 6 conjuntos: CTR / CPA real / mensajes / conversiones.

> El sistema saca microángulos, 6 copies nuevos, el flujo del bot de un solo ángulo y la campaña de escalado. Yo vuelvo a ejecutar como en el Momento 2 (imágenes, bot, subir, activar 4 AM).

---

## ✅ LO QUE YA NO HAGO A MANO (antes vs. ahora)

| Antes lo hacía yo manual | Ahora lo hace el sistema |
|---|---|
| Validar el mercado / producto | ETAPA-PRODUCTO (automático) |
| Elegir ángulos y avatares | ETAPA-0/1B/2 (6 ángulos con voz real del cliente) |
| Escribir copies y hooks | ETAPA-4 (6 copies con metodología de los mentores) |
| Costeo y precios | ETAPA-1 (tabla fija, no se inventa) |
| Decidir la FanPage | ETAPA-FANPAGE (10 páginas, asignación automática) |
| Armar la estructura de campaña | ETAPA-6 (campaña + 6 conjuntos + 2 anuncios c/u) |
| Leer métricas y decidir ganador | ETAPA-7 (CPA real en Q, ranking, fatiga) |
| Decidir cómo escalar y qué creativos crear | ETAPA-8 (PLAN DE ESCALADO según los mentores) |
| Auditar el rendimiento cada mañana | Tarea programada (recorre el portafolio sola) |

**Sigo haciendo yo:** recolectar creativos + transcribir · generar imágenes/infografías · configurar LucidBot · subir a Meta · apretar activar · **ejecutar las decisiones de escalado** (subir presupuesto, crear los creativos nuevos, Post ID).

---

## 💡 SOBRE TESTEAR OFERTAS (tu duda del tablero)

Tu sistema viejo tenía 3 métodos de oferta (M1 precios normales, M2 una unidad cara para que el combo se vea barato, M3 solo 2x1 / 4x2). **El sistema nuevo usa UNA sola oferta en Fase 1 a propósito** — y está bien así:

- En **Fase 1 (testeo)** lo único que se mide es **qué ÁNGULO gana**. Si meto varias ofertas, contamino la data: no sabría si ganó el ángulo o ganó el precio. Por eso los 6 conjuntos llevan el mismo presupuesto y la misma oferta.
- **Testear ofertas SÍ tiene lugar — pero en Fase 2 o después,** ya con el ángulo ganador y el producto validado. Ahí tu lógica vieja sirve: M3 (combos) para productos que la gente ya conoce (magnesio, etc.), M2 (ancla de precio) para productos donde quiero subir el ticket. Tu intuición era correcta: **primero valido el producto, después pruebo ofertas.**

> Recomendación: el testeo de ofertas vive en **FASE 2 / escalado**, ya con el ángulo ganador. El `ESCALADO_PLAYBOOK.md` incluye "subir el precio gradual" como palanca, y ETAPA-8 (motor de escalado) decide cuándo. Hoy enfocate en el ciclo de arriba para no fragmentar la data.

---

## 📌 CHECKLIST CORTO PARA EL TABLERO

```
0. RECOLECTO  → 20 creativos (10 TikTok + 10 Meta) → transcribo en Gemini → foto + costo Q + dosis
1. ARRANCO    → chat → "1" → INPUTS CONGELADOS (producto, costo, dosis, imagen)
2. EJECUTO    → 1_HACER_MANUAL.txt: imágenes-ad + 3 infografías + LucidBot + subir a Meta
3. LANZO      → activo campaña 4 AM (6 conjuntos, 2 anuncios c/u, $1.59)
              → cada mañana el sistema audita solo (ETAPA-7 informe + ETAPA-8 plan de escalado) → yo ejecuto
4. FASE 2     → chat → "2" → ángulo ganador + métricas → escalo
              ⚠️ NADA SE LANZA SOLO. EL BOTÓN LO APRIETO YO.
```
