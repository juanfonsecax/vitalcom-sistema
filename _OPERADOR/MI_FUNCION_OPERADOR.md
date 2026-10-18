# 🧑‍💻 MI FUNCIÓN EN EL SISTEMA — Guía del Operador (Vitalcom GT y CO)

> Esta es la parte que hace JUAN. El sistema hace todo lo demás. Detalle completo del sistema en
> `_OPERADOR/SISTEMA_COMPLETO_PARA_OTRA_IA.md`.

---

## EN UNA FRASE

**El sistema es el cerebro (estrategia). Yo soy las manos y los ojos.**
El sistema piensa los ángulos, escribe los copies, arma el flujo del bot, diseña y publica las
campañas (en PAUSA) y manda las órdenes de pausar/escalar. **Yo doy la materia prima, genero o reviso
las imágenes, configuro LucidBot, activo la campaña y confirmo cada orden.**
👉 **Nada se lanza solo y nada se toca en Meta sin mi confirmación, orden por orden.**

---

## LAS 4 FASES (QUÉ ME TOCA EN CADA UNA)

```
FASE 1 ÁNGULOS  →  FASE 2 CONCEPTOS  →  FASE 3 FLUJO LUCIDBOT  →  FASE 4 ESCALADO
(6 ángulos)        (10 conceptos)        (reescribir el bot)       (1-1-7 + horizontal)
```

La fase en la que está cada producto **no la decido yo: la dice la data**. Al empezar la sesión el
sistema corre `python Ads/_TOOLS/flujo.py --todo --escribir` y me dice en qué nodo está cada producto
y qué lo bloquea.

### 🟦 ANTES DE EMPEZAR — materia prima
- [ ] **Producto + mercado** (GT o CO) y **costo del proveedor en su moneda**.
- [ ] **Dosis / presentación** y **foto del frasco**.
- [ ] **≥6 transcripciones** de videos de competencia (ideal ~20: ~10 de TikTok + ~10 de Meta Ads Library),
      transcritas con Gemini y guardadas como `.txt` en `Ads/1.2 Transcripcion videos/[PRODUCTO]/`.
- [ ] Opcionales: copys de la competencia y N.º de anunciantes activos en la Biblioteca de Anuncios.

> Estos inputs se **congelan**: si cambian a mitad, es rerun completo.

### 🟩 FASE 1 — Ángulos
1. El sistema valida el producto, saca 6 ángulos, costea, asigna FanPage y escribe copies y bot.
2. Me deja `PRODUCTOS/[PRODUCTO]/1_HACER_MANUAL.txt` (se genera solo): **esa es mi lista**.
3. Yo: generar las **imágenes** (FASE 1 es todo imagen), las **3 infografías del bot**, **configurar
   LucidBot** campo por campo, y **activar a las 4 AM del día siguiente** (nunca el mismo día).
4. El sistema publica la estructura en Meta **en PAUSA** (si la cuenta tiene MCP; si no, la pauto a mano).
5. Estructura: 6 conjuntos, 1 anuncio cada uno, mismo presupuesto en los 6.

### 🟨 FASE 2 — Conceptos (cuando hay ángulo ganador por VENTA)
1. El sistema fabrica **10 conceptos** del ángulo ganador y deja los prompts.
2. Yo: **renderizar las imágenes** (o dejar que `etapa-render` las genere en ChatGPT web con mi sesión
   abierta) y marcarlas como generadas.
3. Se publican 3 campañas: A (1-1-5), B (1-1-5) y C (1-2-5, **en otra cuenta**). Activo a las 4 AM.
4. Gana el concepto que queda arriba en **2 de 2** apariciones.

### 🟧 FASE 3 — Flujo LucidBot
1. El sistema redacta la reescritura del flujo del bot hacia el ángulo+concepto ganador.
2. Yo **aplico el cambio en LucidBot a mano** y registro `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT` si
   decido saltármelo).
3. Se mide el cierre: hacen falta **≥30 mensajes** después del cambio y cierre **≥ el piso** para pasar
   a FASE 4. Si no llega, el producto se queda en FASE 3 para otra iteración.

### 🟥 FASE 4 — Escalado
1. El sistema arma el banco de microángulos y la campaña **1-1-7 CBO**; se publica en PAUSA.
2. Yo activo y, cada mañana, confirmo las órdenes de **surfing** (+20% máximo, una vez al día).
3. Palancas horizontales: Post ID, multicuenta, multifanpage. En paralelo corre una exploración de
   3 ángulos nuevos.

---

## 🔁 CADA DÍA (post-lanzamiento)

- El sistema **baja solo** ventas (LucidSales) y gasto/entrega (Meta) de noche y corre el motor
  `decidir.py`.
- Por la mañana veo en la app (pantalla **Hoy** y **Órdenes**) qué ordena el motor: PAUSAR / ESCALAR /
  RENOVAR / SEGUIR_MIDIENDO.
- **Yo confirmo cada orden una por una**; se ejecuta por MCP (o la hago a mano), se verifica contra Meta
  y queda registrada en `_EVENTOS.csv`.
- Si aparece la tarjeta **«Necesita Claude»**, es una tarea que la app no puede resolver sola
  (por ejemplo renombrar anuncios «- Copia» por MCP).
- **Colombia es manual:** yo entrego los exports de Meta y LucidSales.

---

## ✅ LO QUE YO HAGO / LO QUE HACE EL SISTEMA

| Lo hace el sistema | Lo hago yo |
|---|---|
| Validar producto, ángulos, voz del cliente | Recolectar creativos y transcribirlos |
| Costeo, break-even y precios (`costear.py`) | Dar costo, dosis y foto |
| Copies, bot, infografías (prompts), plan de campaña | Generar/renderizar imágenes |
| Publicar estructura en Meta (PAUSED) | Activar a las 4 AM |
| Bajar data, calcular CPA con intervalo y emitir órdenes | **Confirmar cada orden** |
| Medir cierre, fatiga, concepto ganador | Configurar y cambiar el flujo en LucidBot |

---

## 💡 SOBRE TESTEAR OFERTAS

En **FASE 1** se mide solo el **ángulo**: una sola oferta en los 6 conjuntos, si no se contamina la
data. Testear ofertas (combos, ancla de precio) tiene lugar **después**, con el ángulo ganador
(FASE 2 en adelante). «Subir el precio gradual» es una palanca de FASE 4.

---

## 📌 CHECKLIST CORTO

```
0. RECOLECTO  → ≥6 transcripciones + foto + costo + dosis (+ mercado)
1. FASE 1     → 1_HACER_MANUAL.txt: imágenes + infografías + LucidBot → activo 4 AM
2. FASE 2     → ángulo ganador por VENTA → 10 conceptos → activo 4 AM
3. FASE 3     → aplico el CAMBIO_BOT en LucidBot → mido el cierre
4. FASE 4     → 1-1-7 CBO + surfing diario con mi confirmación
   Cada día   → reviso las órdenes y confirmo una por una
              ⚠️ NADA SE LANZA SOLO. EL BOTÓN LO APRIETO YO.
```
