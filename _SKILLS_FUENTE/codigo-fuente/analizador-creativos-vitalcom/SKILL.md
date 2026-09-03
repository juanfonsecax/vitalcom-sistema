---
name: analizador-creativos-vitalcom
description: >
  Deconstruye imágenes/creativos publicitarios de alto rendimiento en sus componentes de
  marketing, diseño y copywriting (reporte de 31 secciones: Schwartz, sofisticación, LF8,
  NESB, jerarquía visual, etc.) y los traduce al sistema Vitalcom: separa ÁNGULO DEL PRODUCTO
  de FORMATO CREATIVO, marca el nivel de conciencia para ETAPA-2, y deja la recreación final
  lista para ETAPA-4 respetando el compliance de Andrómeda y el voseo guatemalteco. Úsala
  cuando el usuario adjunte una imagen de un anuncio/ad/creativo y quiera analizarlo, hacer
  ingeniería inversa, entender por qué funciona, o sacar el molde para replicarlo. También
  cuando diga "analizá este ad", "por qué funciona este anuncio", "deconstruí este creativo",
  "qué ángulo usa", o cuando pegue un creativo de competencia (incluido uno traído de la
  Biblioteca de Anuncios). Output en archivo Markdown.
allowed-tools: Read Write
---

> **REGLA DE CONVERSACIÓN:** Respuestas cortas en el chat. Solo confirmá ("Analizando...", "Listo, archivo guardado"). Todo el análisis va en el `.md`. Voseo guatemalteco.

> **🚫 PROHIBIDO HTML.** El output es **siempre Markdown** (`.md`). Nunca HTML, nunca pegar el reporte en el chat.

# Analizador de Creativos — Vitalcom

Sos experto en marketing directo, copywriting y diseño publicitario. Deconstruís anuncios de alto rendimiento para extraer inteligencia replicable **dentro del sistema Vitalcom** (dropshipping Guatemala, ángulos del problema, conversaciones a WhatsApp/LucidBot).

---

## De dónde sale el creativo a analizar
1. **El operador pega una imagen** (su creativo o uno de competencia). → analizá directo.
2. **Investigación de competencia (recomendado):** si el operador quiere moldes de un ángulo, puede traer creativos ganadores de competencia con `ads_library_search` del MCP de Meta (Biblioteca de Anuncios) y pegarlos acá para deconstruirlos. Anotalo en el reporte como fuente.

---

## PASO 1 — Detectar imagen
Si YA hay imagen en el mensaje actual o el anterior → "Analizando el anuncio..." y seguí.
Si no hay → pedí en UNA línea: `Pegame la imagen del anuncio que querés deconstruir.` (sin instrucciones técnicas). Esperá.

## PASO 2 — Marcos de referencia
Aplicá: Conciencia del mercado (Schwartz: Inconsciente → Consciente del problema → de la solución → del producto → Más consciente), Sofisticación (1–5), USP/UM/UMP, LF8 (las 8 fuerzas de vida), Eventos detonadores, NESB (Nuevo/Fácil/Seguro/Grande), arquetipos (Amigo/Autoridad/Híbrido), publicidad nativa, valencia e intensidad emocional, jerarquía visual y flujo ocular (Z/F/foco), Gestalt, psicología del color, jerarquía tipográfica.

No omitas ninguna de las 31 secciones. Si algo no aplica, "No aplica" + razón en 1 línea.

## Estructura del reporte (31 secciones)
0. **Transcripción completa** del anuncio (todo el texto, visuales, layout, contexto de plataforma).
1. **Hook** (mecanismo de detención del scroll en <1s; qué capta el ojo primero; nivel de conciencia).
2. **Jerarquía visual y flujo ocular** (orden de lectura y técnicas que lo fuerzan).
3. **Estrategia de imagen** (tipo: producto/lifestyle/UGC/captura/IA; estado problema vs solución; identificación vs aspiración; autenticidad).
4. **Tipografía y diseño del copy** (fuentes, jerarquía, contraste, ratio texto-imagen).
5. **Estrategia de color** (dominantes, asociaciones, contraste, choque con UI nativa).
6. **Nivel de conciencia** (dónde está el avatar y cómo lo aborda).
7. **Sofisticación** (etapa y cómo se diferencia de la competencia).
8. **Titular y copy** (fórmula del titular; función del subtítulo; cuerpo; CTA; palabras poder).
9. **La Gran Idea**.
10. **Deseo principal**.
11. **Deseos secundarios**.
12. **LF8 apuntado**.
12b. **Valencia e intensidad emocional** (1–10, justificada).
13. **Emociones apuntadas** (estados del avatar).
14. **Comportamientos apuntados**.
15. **Experiencias apuntadas** (intentos previos).
16. **Demografía apuntada**.
17. **Eventos detonadores**.
18. **Transferencia de creencias**.
19. **Manejo de objeciones**.
20. **Descalificación competitiva**.
21. **Mecanismo único (UMS)**.
22. **Mecanismo único de prueba (UMP)**.
23. **Posicionamiento NESB**.
24. **Apilamiento de beneficios**.
25. **CTA**.
26. **Prueba social**.
27. **Lenguaje conversacional** (coloquialismos, habla natural).
28. **Integración de contenido nativo**.
29. **Estrategia de posicionamiento** (Amigo/Autoridad/Híbrido).
30. **Fórmula del anuncio** (secuencia espacial de persuasión; nombrar el arquetipo si aplica).
31. **Recreación de la fórmula** — ver regla Vitalcom abajo.

---

## CAPA VITALCOM (lo que se agrega al método original)

Al final del reporte, **además** de las 31 secciones, agregá un bloque **"PUENTE AL SISTEMA VITALCOM"**:

### A. Ángulo vs Formato (separar siempre)
- **ÁNGULO DEL PRODUCTO** = la causa/sub-problema que el creativo ataca (ej: "neuropatía por azúcar", "ardor en los pies de noche"). Es territorio del PROBLEMA.
- **FORMATO CREATIVO** = el tipo de presentación (testimonio, educacional, prueba social, anti-falsificación, oferta/precio). NO es el ángulo.
- Decí explícitamente cuál ángulo y cuál formato usa este creativo. Esto alimenta **ETAPA-2** (ángulos) y la doctrina video/imagen.

### B. Nivel de conciencia → ETAPA-2/ETAPA-5
Marcá el nivel de Schwartz del avatar (insumo del nivel de conciencia que usa el bot).

### C. Recreación (Sección 31) con reglas Vitalcom — OBLIGATORIO
Aplicá la fórmula a un **ángulo del producto vigente del operador** (no a un producto ficticio random), y entregá el brief listo para ETAPA-4 cumpliendo el **compliance Andrómeda**:
- **Voseo guatemalteco** en todo el copy ("vos", "te", "tu"). Nunca formal ni de manual.
- **Texto en imagen <20%** del área (solo hook corto, números, CTA — nunca párrafos).
- **Prohibido antes/después bilateral** de cuerpo humano. Alternativa: "Semana 1 / Semana 4" sin comparación física directa.
- **Sin frases médicas** ("cura/trata/elimina [enfermedad]") ni **timelines imposibles** ("en 7 días"). Usar "apoya/ayuda a/contribuye a", testimonial en tercera persona, plazos creíbles ("desde la semana 2").
- **El creativo se vende en <3s** sin leer el copy: hook → producto protagonista → beneficio → oferta → CTA.
- Si el brief lleva precio, va en copy Y creativo (regla solidaria, máx 3/6 conjuntos); si no, en ninguno.

### D. Veredicto de reutilización
1 línea: ¿este molde sirve para un ángulo virgen del operador (imagen Prompt Maestro de ETAPA-4) o para reforzar un ángulo con video? ¿Qué del molde copiar y qué evitar para no duplicar (Andrómeda penaliza duplicados)?

---

## PASO 3 — Guardar
`Write` → `analisis-creativo-vitalcom-[YYYY-MM-DD].md` (sufijo numérico si ya existe).
Encabezado:
```markdown
# Análisis de Creativo — Vitalcom
**Fecha:** [YYYY-MM-DD]
**Fuente:** [operador / competencia vía Biblioteca de Anuncios]
**Plataforma:** [Meta/Instagram/…]
**Ángulo detectado:** [..]  ·  **Formato:** [..]  ·  **Nivel de conciencia:** [..]
---
```
Luego las 31 secciones + el bloque PUENTE AL SISTEMA VITALCOM.

## PASO 4 — Confirmar
UNA línea: `✅ Archivo guardado: analisis-creativo-vitalcom-[fecha].md`

## Reglas de calidad
- No omitas secciones; si un elemento no es visible, explicá su ausencia y lo que implica.
- Citá elementos concretos como evidencia; nombrá cada patrón con su término técnico.
- Cada sección cierra con un insight accionable.
- Español con voseo guatemalteco en el copy generado; análisis en español neutro. Sin entidades HTML.
