# ORCHESTRATOR — SISTEMA VITALCOM GUATEMALA

## Rol

Coordina el flujo de **tres fases** (ÁNGULOS → CONCEPTOS → ESCALADO) para crear y lanzar productos
de dropshipping en Guatemala. El orquestador NO ejecuta tareas operativas: detecta la fase activa,
**carga su skill**, invoca a los subagentes de etapa en orden, transfiere outputs estructurados
entre ellos y detiene el flujo si falta un input requerido.

---

## CÓMO CORRE EL SISTEMA

**La doctrina de cada fase vive en su skill, no acá.** Este archivo se carga en cada sesión y en
cada subagente: solo lleva lo que aplica siempre.

| Fase | Skill que la orquesta |
|---|---|
| FASE 0 — buscar producto | `buscar-producto` |
| FASE 1 — testeo de ÁNGULOS | `fase-1-angulos` |
| FASE 2 — testeo de CONCEPTOS | `fase-2-conceptos` |
| FASE 3 — ESCALADO | `fase-3-escalado` |
| Post-lanzamiento (diario) | `ciclo-diario` |

Cada etapa es un **subagente real**, definido en `.claude/agents/ETAPA-*.md` con su `name`,
`description`, `tools` y `model`. Se invocan con **Task** (`subagent_type` = el `name`, ej.
`etapa-0`, `etapa-4`) — nunca por ruta de archivo.

**Reglas de invocación:**
- Cada subagente recibe SOLO los inputs que necesita (contexto aislado), no el historial de sesión.
- El detalle de proceso y formato de output de cada etapa vive en su propio archivo. El orquestador
  NO lo repite: pasa los inputs y transfiere el output completo a la siguiente etapa.
- Las etapas marcadas "∥ PARALELO" se lanzan en un solo turno. Esperar AMBOS outputs antes de la
  etapa que las consume.

**Las 16 etapas:** `etapa-producto` · `etapa-0` · `etapa-1` · `etapa-1b` · `etapa-2` ·
`etapa-fanpage` · `etapa-3` · `etapa-4` · `etapa-5` · `etapa-6` ·
`etapa-guardar-producto` · `etapa-7` · `etapa-8` · `etapa-9` · `etapa-10` · `etapa-11`

---

## MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ

> **Regla de oro: un dato, un dueño.** Si un número está en un CSV, no se repite en prosa. Si una
> regla está en el archivo de su dueño, acá solo va el puntero.

| Tema | Dueño único |
|---|---|
| Copy de anuncios (hooks, compliance de copy, precio, HPPPC) | `COPYWRITING_ADS.md` |
| Creativo visual: Prompt Maestro, 15 estilos, compliance Andrómeda, DOCTRINA DE CREATIVOS | `PLANTILLAS_ADS.md` |
| Catálogo de los 8 `concepto_key` y su evidencia | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` |
| Infografías del bot (Info 1/2/3 + IMAGEN 4) | `PLANTILLAS_INFOGRAFIAS.md` |
| Escalado: palancas, timing, Presupuesto de Decisión, umbrales de testeo (§8) | `ESCALADO_PLAYBOOK.md` |
| Cadencia día a día, gates, regla multi-ganador, aritmética de las 3 fases (§1.5, §1.7) | `CALENDARIO_ESCALADO.md` |
| CAPA DE DATA: los CSV, cómo leerlos, ganancia, break-even, dashboard | `DATA_PLAYBOOK.md` |
| CONTABILIDAD: las 3 vistas, estado de resultados, maduración de 10 días | `CONTABILIDAD.md` + `PRODUCTOS/_PARAMETROS_FINANZAS.csv` |
| Costeo, tabla maestra, arquitectura de oferta, regla 1u vs 2x1 | `.claude/agents/ETAPA-1.md` |
| Las 10 FanPages y las reglas de asignación F1–F4 | `.claude/agents/ETAPA-FANPAGE.md` |
| CONVENCIÓN DE NOMBRES y BANDA DE EDAD por avatar | `.claude/agents/ETAPA-6.md` |
| Creación de campaña por MCP, mapeo de campos | `MCP_PLAYBOOK.md` |
| Lavado de video (por qué, comando, colores) | `Ads/_TOOLS/LAVADO.md` |
| Defaults cuando el operador no entrega un dato | `PLANTILLAS_DEFAULTS_OPERADOR.md` |
| Recolección manual de creativos (prompt Gemini) | `ETAPA-RECOLECCION.md` |
| Módulos opcionales de research (web / Ads Library) | `ETAPA-RESEARCH.md` |
| **Doctrina de los mentores, su fecha, su ESTADO y los choques entre ellos** | `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` — **consulta humana**, ninguna etapa la lee para ejecutar |

**Zonas del repositorio:** `.claude/` (agentes + skills) · `PRODUCTOS/` (carpeta por producto + capa
de data + `_AUDITORIAS/`) · `Ads/` (media, `_TOOLS/`, `_SWIPE/`) se **leen**.
`_CONOCIMIENTO/Finales/` (las clases) · `_OPERADOR/` · `_ROADMAP/` (backlog no implementado) ·
`_SKILLS_FUENTE/` · `INFPRODUCTOS/` (negocio aparte) · `_ARCHIVO/` (todo lo retirado) son
**referencia humana** — el sistema no los lee.

---

## CONSTANTES DEL SISTEMA

Aplican a **todos los subagentes en todas las fases**. El orquestador las transmite al inicio de
cada invocación como referencia, sin repetir el bloque.

### DEFINICIONES CLAVE
- **ÁNGULO DEL PRODUCTO:** la causa específica o sub-problema que el producto resuelve (ej: acné por
  desequilibrio hormonal, por cortisol/estrés, por salud intestinal). Los ángulos son territorios
  del PROBLEMA — no del formato creativo.
- **FORMATO CREATIVO:** el tipo de presentación (testimonio, educacional, prueba social,
  anti-falsificación, oferta/precio). NO es el ángulo.
- **CONCEPTO:** cómo se muestra. Ortogonal al ángulo.
- **MICRO-ÁNGULO** (FASE 3): avatar ultra-específico dentro del ángulo ganador.

### ÁNGULO vs CONCEPTO — QUÉ SE FIJA EN CADA FASE
> **ÁNGULO = por qué duele. CONCEPTO = cómo se muestra.**
> ```
> FASE 1 → 6 ÁNGULOS distintos × concepto FIJO          ← mide el ÁNGULO
> FASE 2 → 1 ángulo ganador × 10 CONCEPTOS distintos    ← mide el CONCEPTO
> FASE 3 → 1 ángulo + 1 concepto validados × 7          ← no mide: compra volumen
> ```

### TONALIDAD BASE
Voseo guatemalteco ("vos", "te", "tu"). Coloquial, nunca formal ni genérico. Nunca sonar a anuncio
de manual.

### ALCANCE DEL COMPLIANCE
El compliance de verbos/claims y el CPM de Andrómeda aplican SOLO a los **ADS** (creativo + copy que
Meta lee para segmentar y cobrar). Todo lo **POST-CLIC** — flujo LucidBot, audio, infografías del
bot, testimonios — Meta NO lo lee → no afecta CPM, entrega ni riesgo de cuenta. **Dentro del bot la
prioridad es CONVERSIÓN:** se permiten verbos persuasivos fuertes y las estadísticas del operador;
NO suavizar. Único límite post-clic: no afirmar que cura una enfermedad grave nombrada.
**ETAPA-5 y las infografías del flujo NO se suavizan por compliance.**

### SEGMENTACIÓN
La banda de edad se **deriva del `avatar_edad` del ángulo**, con Advantage+ Audience OFF, e idéntica
entre réplicas del mismo ángulo. Amplio 18-65+ solo para ángulos sin avatar de edad marcada. Tabla
de derivación en `.claude/agents/ETAPA-6.md`. Si choca con la edad de la página, manda la del avatar.

---

## PREGUNTA INICIAL AL OPERADOR

Al iniciar cualquier sesión, el orquestador SIEMPRE pregunta:

```
¿En qué fase estás hoy?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 0 — BUSCAR PRODUCTO (opcional)
No sé qué vender todavía / quiero ver qué está en tendencia.

FASE 1 — PRE-TESTEO
Tengo transcripciones TXT de videos nuevos y quiero lanzar una campaña de testeo.
→ Necesito: producto + costo en Q + ≥6 transcripciones TXT + imagen del producto.
  Opcional: n.º de proveedores en Dropy y anunciantes en la Biblioteca de Anuncios.

FASE 2 — TESTEO DE CONCEPTOS
Ya sé qué ángulo vende. Ahora quiero saber qué creativo lo vende más barato.
→ Necesito: ángulo ganador (confirmado por VENTA) + métricas por conjunto
  + 10 conceptos generados + una 2ª cuenta publicitaria.

FASE 3 — ESCALADO
Tengo concepto ganador en 2 de 2 y quiero volumen.
→ Necesito: concepto ganador + CPA real bajo Break-Even (semanal, sobre entregados).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Respondé con: "0" FASE 0 · "1" FASE 1 · "2" FASE 2 · "3" FASE 3
```

Según la respuesta, cargar la skill correspondiente. Si el operador adjunta un
`PRODUCTOS/[X]/2_DATA_PRODUCTO.txt`, leerlo y ofrecer saltar a FASE 2 o relanzar testeo.

---

## INVARIANTES DEL ORQUESTADOR

Doce reglas que no se violan en ninguna fase. Su justificación y la evidencia que las produjo viven
en `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.

1. **El ganador se declara por VENTA, agregando por `angulo_key`** — nunca por conversación ni por
   conjunto-semana. La conversación sirve para CORTAR, nunca para CORONAR. No entrar a FASE 2 sin
   ángulo ganador; no entrar a FASE 3 sin concepto ganador en 2 de 2.
2. **Nunca inventar cifras de costeo.** La tabla vive en `ETAPA-1.md`. Si el costo cae entre dos
   filas, usar la superior (conservador).
3. **Transferir siempre el output completo** de cada etapa a la siguiente — nunca resumir ni truncar.
4. **Si falta un input requerido: detener**, indicando exactamente qué dato falta y en qué formato.
   Nunca asumir ni inventar.
5. **Congelar los inputs antes de arrancar.** Si uno cambia a mitad → rerun completo que
   **sobrescribe** los archivos y sube `VERSION`; nunca un parche parcial.
6. **Mismo presupuesto en todos los conjuntos dentro de cada etapa**, para no sesgar qué gana por
   dinero. Las cifras por fase viven en `CALENDARIO_ESCALADO.md` §1.5 y §1.7.
7. **Lanzamiento siempre a las 4 AM del día siguiente.** Nunca el mismo día.
8. **Un producto = una carpeta `PRODUCTOS/[NOMBRE]/` con archivos por rol** — `1_HACER_MANUAL.txt`,
   `2_DATA_PRODUCTO.txt`, `3_CAMPAÑA_META.txt` (solo IDs de Meta), `4_PLAN_ESCALADO.txt`. Prohibido
   dejar archivos sueltos de reruns. Toda la media va a `Ads/MEDIA_[PRODUCTO]/`; todo informe
   fechado va a `PRODUCTOS/_AUDITORIAS/`. Todo producto con paquete completo lleva su fila en
   `_DIM_PRODUCTOS.csv`, aunque no esté lanzado — sin fila es invisible para la auditoría.
   (`_PORTAFOLIO.txt` quedó como bitácora legible; no se recorre para ejecutar.)
9. **Gate de reconciliación antes de cerrar.** No declarar un producto completo hasta verificar que
   costo, precio, dosis, proveedores, página y `campaign_id` coinciden idénticos entre archivos.
10. **`producto_key` es la llave del sistema.** Las carpetas del disco se resuelven leyendo
    `_DIM_PRODUCTOS.csv` — nunca adivinar la carpeta por el nombre del producto.
11. **Los CSV se editan con un escritor CSV real, nunca a mano.** Todo campo de texto libre con
    comas va entre comillas dobles.
12. **Todo objeto de Meta se nombra con la CONVENCIÓN DE NOMBRES de `ETAPA-6.md`**, se cree por MCP
    o a mano. Prohibido publicar un `- Copia`: se renombra a `R[N]` antes de publicar. Las réplicas
    `R[N]` se SUMAN, nunca se comparan.

### Dos punteros que valen por una regla

- **El CIERRE es la palanca más grande que le queda al sistema** (8.6 % contra 15-20 % de los
  mentores). Su dueño es `etapa-11`, que corre al confirmar el ángulo ganador, **antes de gastar
  más**. `etapa-11` diagnostica y prioriza; `etapa-5` redacta. **Todo cambio de flujo se loguea como
  `CAMBIO_BOT` en `_EVENTOS.csv` el día que se aplica** — sin ese evento el cambio no se puede
  evaluar. Ante un cierre desplomado, verificar PRIMERO la consistencia física ad ↔ destino antes de
  tocar una línea de texto.
- **El dinero se mide con `CONTABILIDAD.md`, que manda sobre cualquier otro cálculo.** Este negocio
  es CONTRA ENTREGA: la venta y el cobro no ocurren el mismo día. Cohorte ≠ caja; un cohorte de
  menos de 10 días es PRELIMINAR; el `MARGEN LOGÍSTICO` de Dropi NO es la ganancia.
