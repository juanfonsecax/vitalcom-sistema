# ESCALADO_PLAYBOOK — CÓMO ESCALAN LOS MENTORES (fuente única)

> **📎 COMPAÑERO OBLIGATORIO: `DOCTRINA/CALENDARIO_ESCALADO.md`.** Este archivo es el **QUÉ** (palancas y por qué); el calendario es el **CUÁNDO** (el ritmo Día 0→3→6→7+ con gates de decisión y la REGLA DEL MULTI-GANADOR). ETAPA-7/8 leen los DOS: primero ubican al producto en su **ventana del calendario**, luego aplican la palanca de este playbook que corresponde a esa ventana. No usar uno sin el otro.

> Doctrina de escalado extraída **textual de las clases**. ETAPA-7 (lectura) y ETAPA-8 (decisión) se apoyan en este archivo. El sistema NO improvisa: aplica estas reglas contra la data real. Los importes de las clases están en COP (Colombia); el sistema opera en **Q (Guatemala)** y **$2.99/conjunto en ETAPA 1 · $5.98 en ETAPA 2** (ver `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5) — los montos COP son referencia de MÉTODO, no de cifra. Nota: 12,000-16,000 COP de las clases recientes = $2.96-$3.95 a la tasa 4,050, o sea el MISMO rango. Guatemala es mercado nuevo/barato (Clase 15/22).

> **⭐ REGLA DE RECENCIA (manda sobre todo lo demás):** clase con número mayor = más reciente = **manda**. La doctrina PRIMARIA de este archivo son las clases más nuevas: **Clase 22** (optimización de flujo — la más reciente), **Clase 20** (ángulos/HPPPC + réplica del ganador + interpretación de métricas), **Clase 19** (Andrómeda + estructura de anuncio ganador), **Clase 15** (escalado dedicado: Post ID, multicuenta, surfing 20% — la más reciente de escalado). Las clases viejas (**Clase 7** optimización, **Clase 8** escalado/Camilo, **Clase 11**) se usan SOLO como COMPLEMENTO, para lo que las recientes no cubren y **no contradicen** (ej. de Clase 8: CPA semanal/ponderado, CPA real sobre entregados, escalera de duplicación de conjunto, subir precio gradual — siguen válidas porque ninguna clase nueva las contradice). Si una clase nueva y una vieja chocan → gana la nueva.

---

## 0. FILOSOFÍA — dos escuelas, el sistema usa PROGRESIVA por default

- **Progresiva (Joaquín):** "El escalado es VALIDACIÓN PROGRESIVA, no agresividad inmediata. Prefiero validar para durar más en el tiempo." (Clase 15). ← **default del sistema** (encaja con COD/WhatsApp, low-budget, y protege de Andrómeda).
- **Agresiva (Mercy/Camilo):** duplicar fuerte y meter presupuesto rápido. Se usa SOLO cuando hay CPA real rentable sostenido + flujo de caja (Clase 8).
- Regla de oro de ambos: **"Se queman los ÁNGULOS, no los productos"** (Clase 8 caso chilají, Clase 19). Y **"paso más tiempo mandando a hacer creativos ganadores que mirando el dashboard"** (Clase 15).
- **Calibración Guatemala (operador, 2026-07):** la entrega COD es ~3 días (GINTACOM/FORZA), no 4-7 (Colombia). Por eso el gate de escalado fuerte baja de día 7 a **día 5** — lo más temprano que hay un lote de ventas ENTREGADAS confirmadas. Escalera: Paso 1 testeo (día 3 GATE #1) → Paso 2 FASE 2 dedicada (día 3-4) → Paso 3 escalado horizontal (día 5+, con CPA sobre entregados confirmado + volumen; nunca sobre 1-2 ventas). Ver `DOCTRINA/CALENDARIO_ESCALADO.md` Ventanas 2-4.

---

## 1. TIMING Y FASES — cuándo se decide qué (nunca por un día suelto)

- **Día 1 = DATA, no ventas.** Los **clics en el enlace** dicen qué ángulo tiene público. Dejar correr **2-3 días aunque el CPA sea alto** (el flujo aún no está optimizado). (Clase 15 Bloque 4).
- **CPA SEMANAL / PONDERADO, no diario** (Camilo, Clase 8): "el error #1 es apagar una campaña porque hoy no vendió". Las ventas no son iguales todos los días. `CPA ponderado = gasto de la semana ÷ ventas de la semana`. Un anuncio que vende, se deja prendido aunque un día el CPA suba.
- **Declarar ángulo ganador (día 3-5):** mejor **CPA real** (≤ CPA Base) + buen **% conversación por clic-enlace**. Si aún no hay CPA (tracking), usar **clics-enlace + % conv/clic-enlace** como proxy PROVISIONAL (no oficial).
- **"Tus productos tienen que venderte el primer día"** (Camilo): si con más presupuesto ningún anuncio del conjunto vendió a mediodía y ya gastó la mitad → se apaga (no se va a optimizar). Con low-budget se es más paciente (2-3 días).

---

## 1.5 PRESUPUESTO DE DECISIÓN — cuánto debe gastar un conjunto antes de que "0 ventas" cuente

> **Los valores vigentes viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y los ejecuta `Ads/_TOOLS/decidir.py`**
> (`umbral_conv_clic_enlace_pct`, `min_link_clicks_conv`, `max_pausas_por_dia`, `dias_min_cod_pausa_ventas`,
> `factor_tolerancia_pd`, `surfing_pct`). Este texto es la doctrina que los justifica; si difieren, manda el CSV
> y `verificar_guia_madre.py` lo canta. Desde el 09-sep-2026 ninguna etapa recalcula estos umbrales en prosa.

> **Por qué existe esta sección:** el sistema ya tenía los DÍAS (CALENDARIO) y la regla "gasto > Break-Even y 0 ventas → pausar" (§6), pero no CUANTIFICABA a $1.59 cuánto gasto/días necesita un conjunto para que su "0 ventas" sea un veredicto válido. Sin eso se mata a ganadores sub-testeados. Anclas: **Clase 5** (low-budget → esperar 2-3 días; "no apagar por un mal día, mirar el historial de 15 días"), **Clase 8** (Camilo: "tus productos tienen que venderte el primer día" y "gastó la mitad sin vender → apagar" — pero eso es a PRESUPUESTO ALTO), **Clase 11** (CPA SEMANAL/ponderado, no un día), + el **CPA Break-Even del costeo** (ETAPA-1).

**DOS SEÑALES QUE MADURAN A RITMOS DISTINTOS — no confundirlas:**

1. **CONVERSACIÓN (clics→chats): barata y RÁPIDA.** Confiable desde el **día 1-2** con poquísimo gasto. Es la señal para **matar temprano**: si un conjunto tiene **%conv/clic-enlace muy bajo** o **$/conversación caro** (trae clics pero no chats, o chats-morbo que no escriben) → problema de **anuncio/hook** → se apaga **sin esperar** a que gaste un Break-Even (Clase 20 "CTR bajo + caro → pausar"; Clase 8 "morbo que no vende → apagar").
   > **DEFINICIÓN NUMÉRICA de "conversación floja" (gate del criterio temprano — para que no sea a ojo):** al día 2-3, con **0 ventas**, se apaga por conversación si tiene ≥1 en rojo: (a) **%conv/clic-enlace <35%** 🔴 (el gate firme); (b) **CTR-enlace <1.5%** (hook débil — umbral ya usado en el sistema); (c) **$/conversación > 2× el del MEJOR conjunto de la misma campaña** (caro relativo y computable; no inventa un Q absoluto porque el costo varía por ticket/producto). El (a) es el principal; (b) y (c) refuerzan.

2. **VENTA / CPA: cara y LENTA.** El "0 ventas" **NO es veredicto** hasta que el conjunto acumuló **≥ 1 × CPA Break-Even de GASTO** *y* pasaron los **~3 días de maduración COD** (Guatemala). Debajo de ese umbral, cero ventas es estadísticamente esperable **hasta en un buen conjunto** — matarlo ahí es matar un ganador sub-testeado.

**EL PRESUPUESTO DE DECISIÓN (PD) — la cifra que faltaba:**
- **PD por CONJUNTO (piso para matar-POR-VENTAS) = 1 × CPA Break-Even.** Es el punto donde, si convirtiera al break-even, ya debería haber ≥1 venta. Debajo de eso NO se mata por ventas.
- A **$2.99/día (≈Q22.8)**, un conjunto tarda `Break-Even_Q ÷ 22.8` **días** en llegar a su PD — con 80% de entrega real son **3.3-4.3 días** según producto, lo que hace VÁLIDO el gate del día 3-5 de los mentores. (A $1.59 tardaba 5.0-6.5 días y el gate del día 3 llegaba con solo 46-60% del PD = decidir a ciegas.) Aun así, los perdedores se cortan por **CONVERSACIÓN** en el GATE del día 3 (más rápido y no depende de LucidSales), y solo se mata-por-ventas al que YA gastó su PD y sigue en 0 (el caso "buena conversación, 0 ventas" tipo ANIMO / ARAÑITAS).
- **PD de la CAMPAÑA (gate de definición) = 1 × Break-Even repartido entre los 6 conjuntos** = `Break-Even_Q ÷ (6 × 12.1)` días ≈ **1-3 días** → por eso el **GATE #1 cae en el día 3** (ya en el CALENDARIO): para entonces la campaña gastó ~1 Break-Even colectivo, suficiente para leer conversación + las primeras ventas de los ganadores.

**Tabla de PD por producto (a $2.99/día = Q22.8, tasa 7.62 · vigente desde 25-jul):**

| Producto | CPA Base Q | Break-Even Q (v2) | PD conjunto (1×BE) | Días @ $2.99 (entrega 0.8) | BE v1 (obsoleto) |
|---|---|---|---|---|---|
| VARICOSE 2x1 | 36.9 | **83.0** | Q83 | **4.6 días** | ~~Q79~~ |
| NUSAVA B12 | 31.3 | **76.9** | Q77 | **4.2 días** | ~~Q68.3~~ |
| TINNIDROP | 30.8 | **71.6** | Q72 | **3.9 días** | ~~Q60.5~~ |
| CLEARSTEM | 30.8 | **69.6** | Q70 | **3.8 días** | ~~Q60.5~~ |

> Los valores vivos están en `PRODUCTOS/_DIM_PRODUCTOS.csv` — esta tabla es el espejo legible. Si difieren, manda el CSV.

> ⚠️ **VARICOSE se costea por el PEDIDO, no por la unidad:** vende 2x1 (2 frascos de Q45 = Q90 de
> producto por pedido) → le toca la **fila Q90**, no la Q45. Historia de por qué esta tabla llegó a
> decir otra cosa y por qué el presupuesto subió de $1.59 a $2.99:
> `_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §1.5. Aritmética completa del
> presupuesto en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5.

> **Lectura:** el **ganador se declara solo** vendiendo bajo Base en los primeros días (MA2 de Varicose vendió a Q11.6 con ~$6 de gasto). El **perdedor** se corta por conversación en el día 3; solo se espera a su PD completo si tiene BUENA conversación pero 0 ventas (ahí el problema es cierre/ángulo, no alcance). **Nunca** se mata por el CPA de UN día — siempre semanal/ponderado (Clase 11).

**REGLA OPERATIVA (la que ejecuta el operador y ETAPA-8):**
- **Día 1-2:** no tocar. Solo mirar clics-enlace / conversación.
- **Día 3 (GATE #1):** (a) ganadores = ya venden ≤ Base → optimizar flujo + surfing; (b) perdedores por conversación (%conv/clic-enlace <35% o $/conv caro) → apagar (máx 2); (c) buena conversación + 0 ventas → **seguir hasta 1×BE de gasto** antes de decidir.
- **Matar-POR-VENTAS** solo cuando el conjunto pasó su PD (1×BE) con 0 ventas y ~3 días COD cumplidos.

---

## 2. SEÑALES DE DECISIÓN (qué mirar antes de mover)

| Señal | Umbral (Clase 7/15) | Qué significa |
|---|---|---|
| % conv/clic-enlace | <35% 🔴 · 35-49% 🟡 · **50-70% 🟢 súper escalable** | La MÁS importante: quién LLEGÓ al WhatsApp (no solo clic) |
| % conv/impresión | <1.5 🔴 · 1.5-3.49 🟡 · ≥3.5 🟢 | Termómetro temprano |
| CPA real vs Base/BE | 🟢 ≤ Base · 🟡 ≤ Break Even · 🔴 > BE | Rentabilidad (calcular semanal) |
| CTR | bajo = **hook/creativo malo** → cambiar hook | Diagnóstico de creativo |
| CPM | alto = **saturación o mala segmentación** → Ad Library + nuevo ángulo | Diagnóstico de ángulo |
| Frecuencia | ≥1.9 = fatiga → renovar creativo (mismo ángulo) | Desgaste del creativo |
| Muchos chats, pocas ventas | — | Problema de **cierre/flujo** (bot), no del ad |

**Interpretación por métricas — "separar el problema" (Clase 20, la más reciente; reemplaza la lectura vieja de Clase 7):** optimizar = ubicar en qué parte del embudo está el filtro (atención / confianza / cierre):
- **CTR alto + CPA bajo** → GANADOR → escalar con control + variaciones del mismo ángulo.
- **CTR/retención baja + cierre alto** (la oferta vende pero el creativo no detiene el scroll) → mejorar el **CREATIVO** (hook).
- **CTR muy alto + CPA alto** → el hook engancha pero la oferta/mensaje inicial/cierre falla → mejorar el **CIERRE/FLUJO** (ETAPA-5).
- **CTR muy bajo + caro** → no hay interés → **pausar**, replantear el dolor/prueba o probar otro ángulo.
- **Ganador = conversión RENTABLE, no likes** (optimizar por likes engaña: baja CPM pero encarece CPA).

> Referencia mercado Colombia (Clase 22/15): CPM bueno 6-10k COP · CPM ~20k = ángulo saturado/competido · ~10k = menos saturado (trabajable) · CTR ~3% · CPC ~150 COP. En Q/Guatemala son mucho más baratos — usar como cualitativo.

---

## 3. PALANCAS DE ESCALADO — en el orden que las aplican los mentores

> 🔴 **ESTRUCTURA DE ARRANQUE DEL ESCALADO — actualizada 2026-09-02.** El escalado (FASE 3) ya no
> arranca con 6 conjuntos de microángulos: arranca con **1-1-7** — una campaña, un conjunto, el
> creativo validado **siete veces** (Post ID o subido de cero), a **$15-18/día**. Fuente: M-A10
> (clase 22-ago). Spec completo en `.claude/agents/ETAPA-6.md` → *Output FASE 3*.
> Las palancas de abajo se aplican **sobre** esa estructura, no en vez de ella.
>
> **Cuatro reglas nuevas que gobiernan toda esta sección:**
> 1. **Duplicar SIEMPRE al presupuesto INICIAL, nunca al actual** (M-A12). Duplicar una campaña que
>    ya va en $60 a esos mismos $60 quema el aprendizaje y arranca cara. Por eso el presupuesto de
>    arranque se anota en `_EVENTOS.csv`: es el valor al que se duplica después.
> 2. **Muere la campaña, no el creativo** (M-B09). Tendencia de 7 días con CPA en alza sostenida →
>    apagar **la campaña** y relanzar **el creativo** en otra cuenta, en campaña nueva. *"Por algo
>    esa se murió"* — se apaga el envase, no el contenido. El creativo sigue vendiendo en sus copias.
> 3. **Movimientos graduales en cuentas jóvenes** (M-C06). Meta opera por confianza: crear muchas
>    campañas de golpe en una cuenta sin historial dispara limitaciones y hasta pérdida del perfil.
>    Si la cuenta no está acostumbrada a mucho volumen, se sube escalonado.
> 4. **El día que se lanza un testeo, las campañas vivas bajan y NO se toca nada** (M-C08). Es un
>    efecto conocido y se recupera solo al día siguiente. Apagar ese día destruye una campaña sana
>    por un artefacto de calendario.

Cuando hay ganador validado, se sube por esta escalera (no todas de golpe):

1. **Optimizar el flujo hacia el ángulo ganador** (Clase 15 + **Clase 22, la más reciente de flujo**): apuntar el bot de Lucid al ángulo con más clics, **apagar los conjuntos de ángulos que no funcionan** (a veces sirven 2-3). Sube la conversión y baja el CPA — "convertir más sin gastar más" (Clase 22). Esto va PRIMERO, antes de gastar más. **Cómo optimizar el flujo (Clase 22):** título impactante + beneficio + resultado deseado congruentes con el anuncio (si el flujo dice algo distinto a lo pauteado → efecto rebote, se sale); reducir fricción (garantía 30 días, CTA con beneficio, prueba social con imágenes de uso); 6-8 propuestas de valor (Problema+Solución+Resultado); respetar el **umbral cognitivo** (no saturar la imagen); **momentos** antes→después; responder en 2-3 seg (no 15). Detalle en ETAPA-5.
   > 🔴 **ESTA PALANCA YA TIENE DUEÑO Y MÉTODO (02-sep): `.claude/agents/ETAPA-11.md`.** Hasta hoy
   > estaba enumerada sin decir cómo se mide, con qué se compara ni quién la ejecuta — y era la
   > brecha más cara del sistema (choque C-10 de la matriz). `etapa-11` corre **al confirmar el
   > ángulo ganador**, mide el **CIERRE** (mensajes → ventas) por `angulo_key` con piso de
   > evidencia, separa el problema **pre-clic** del **post-clic**, audita la congruencia ad ↔ bot
   > punto por punto, lee los chats y entrega el **brief priorizado** a `etapa-5` — que escribe los
   > bloques de juicio y las frases del ángulo. El **texto fijo** del flujo es de
   > `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` y se renderiza con `Ads/_TOOLS/gen_flujo_bot.py`.
   > **El orden de los cambios no es libre:** propuestas de valor primero (M-F06), después fricción,
   > congruencia, oferta y FAQ.
   > **Y el cambio no se hace a ciegas:** se corre un **A/B de flujo** — brazo A el paraguas
   > optimizado, brazo B el dedicado al ganador, ruteados por **Post ID** a productos distintos del
   > catálogo de LucidBot. Diseño, `n` mínimo por brazo y reglas del test en el PASO 6 de
   > `ETAPA-11.md`.
   > ⚠️ **Nunca suavizar el flujo por compliance** — eso aplica solo a los ADS. Post-clic la
   > prioridad es conversión.
2. **Surfing del 20% diario** (Clase 8 y 15): cada mañana, a **TODO lo que vendió**, subir **+20%** del presupuesto del conjunto. Nunca más de 20% (desoptimiza). Es la optimización diaria por default.
   > ⚠️ **El +20 % VARIAS veces al día** (M-B03, clase 22-ago: subir cada 2-3 horas hasta las 2-3 PM
   > mientras el CPA siga bajo) está **CONGELADO**, no rechazado. Razón: APR-057 — la ventana
   > 14-16 ago subió el gasto **+63 %** y compró **0.3 ventas/día más**, partiendo la ganancia al
   > medio. El mentor escala rápido **porque tiene el banco de conceptos alimentando la campaña**;
   > copiar su cadencia sin su línea de producción reproduce el 14-16 de agosto.
   > **Se descongela cuando la fábrica (`etapa-9`) sostenga ≥6 creativos/día.** Ver choque C-02 de
   > `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.
3. **Renovar/crear creativos del ángulo ganador** (Camilo: "la variable #1 del éxito"): mandar a hacer **10-40 creativos** más del mismo ángulo con conceptos/formatos distintos. Ver §4. Es la palanca más importante para sostener CPA bajo al escalar.
4. **Duplicar el CONJUNTO ganador** (Clase 8, agresivo): 16k→32k→64k (o el equivalente en Q). Sube el CPA un poco; compensar con creativos nuevos. A veces se duplica ×4 y salen 5 conjuntos; no todos venden, 2-3 sí.
5. **Post ID / publicar en la página** para conservar **prueba social** (Clase 15 + Clase 8): el anuncio ganador acumula likes/comentarios. Duplicar con **Post ID** ("usar publicación existente") o —mejor hoy porque Meta a veces borra reacciones al duplicar— **publicar el creativo directo en la fanpage** y usar "crear anuncio con publicación existente"; al llevarlo a otra cuenta hereda las reacciones sin Post ID.
   > 🔴 **HECHO NUEVO DE PLATAFORMA (M-C07, clase 22-ago).** **En campañas con objetivo Ventas
   > (`OUTCOME_SALES`) Meta ya no deja extraer el Post ID** — los posts se volvieron dinámicos.
   > Tráfico e Interacción sí lo siguen dando. **Workaround:** duplicar el anuncio en una campaña
   > NUEVA (no dentro de la misma), esperar a que pase revisión y ahí sacar el Post ID.
   > **Consecuencia que hay que decidir junto con el objetivo:** si el sistema migra a
   > `OUTCOME_SALES`, esta palanca se pierde tal como está escrita. Las dos decisiones están
   > acopladas — ver choque C-03 de la matriz.
6. **Multicuenta** (Clase 15): el día 1 se lanza la MISMA campaña en **4 cuentas** (misma fanpage) porque cada cuenta segmenta distinto; el ganador se **riega hasta en 9 cuentas**. "Cuando vende en las 4, es súper winner."
7. **Multifanpage** (Clase 15 + Clase 8): validar el ganador en **fanpages distintas**; una fanpage que encarece se cambia por otra nueva (da mejores costos). Límite **250 anuncios/fanpage** (4 fanpages ≈ 1,000 anuncios).

> **⚠️ PÁGINAS vs CUENTAS — no confundir (la página NO segmenta, el creativo segmenta):**
> - **Testeo de ángulos (FASE 1):** 1 cuenta · **1 página** · 1 campaña · 6 conjuntos. Se testean ÁNGULOS, no cuentas ni páginas. No repartir el testeo entre 4 cuentas ni entre páginas distintas (confound + diluye prueba social).
> - **Multicuenta (validar ganador):** la MISMA campaña ganadora en 4 cuentas usando la **MISMA página**. La variable es la CUENTA (cada una siembra distinto), NO la página. Nunca una página distinta por cuenta.
> - **Multifanpage = reactivo, no inventario:** se agrega/cambia a otra página **del mismo nicho** SOLO cuando la página en uso se encarece (CPMs) o topa los 250 anuncios. No se arman 4 páginas por subnicho de arranque.
> - **Inventario de páginas:** 1 página fuerte por nicho (cargando varios productos del nicho — congruencia Clase 22) + 1-2 de reserva del mismo nicho ya calentadas (refresco multifanpage + redundancia anti-baneo). La página se asigna al BM para que las cuentas la usen. Nunca páginas comodín que mezclen nichos.
8. **Subir el precio gradual** (Clase 8): de a poco mientras siga vendiendo; cada incremento va directo al **margen neto** sin dañar la conversión, y puede sacar competencia.

> Validación multicuenta/fanpage: **NO se aumenta presupuesto en esa fase** — se valida que funcione a largo plazo (Clase 15 Q&A). El +20% es para lo ya validado.

---

## 4. REPLICAR EL CREATIVO GANADOR — el corazón (Clase 20 + Clase 19; complementa Clase 8)

No es "hacer más de lo mismo". Es entender **POR QUÉ ganó** y variar el concepto manteniendo lo que lo hace ganar. **La regla más reciente (Clase 20): "Se copia el POR QUÉ vendió, no el creativo."**

0. **DESARMAR la estructura del ganador (Clase 20, Bloque 8 — el método):** ante el anuncio/ángulo que gana, responder: ¿qué hace el **hook** que rompe el scroll (frase, gesto, visual, problema)? ¿qué **tipo de ángulo** es (problema-solución, comparación, autoridad, **emocional** —de los mejores—, oferta-escasez, mecanismo, antes/después)? ¿qué **prueba** usa? ¿qué **oferta**? ¿qué **CTA** pide? Eso es el "por qué vendió". Se **adapta con ética** (cambiar texto, promesa, prueba, voz), NUNCA se copia literal. Aplica igual a imagen y video. Fuentes de referencia: **Ad Library, Calodata, Calbu** + marcas de EE.UU. que facturan (Clase 19).
1. **Identificar el ÁNGULO ganador** (el problema/deseo que enganchó) — lo más difícil; una vez claro, "se hacen infinitas variaciones de concepto y vende sí o sí" (Clase 19/20). **Un creativo = UN ángulo dominante** (Clase 20); no mezclar.
2. **Conservar el ángulo, variar el CONCEPTO** (NO variaciones mínimas): cambiar diseño, fondo, textos/beneficios, **modelo** (blanca→morena, mujer→hombre), oferta ("2 frascos por Q…"), CTA. Montar lo idéntico **encarece el creativo** (Clase 8).
3. **Estructura del anuncio ganador** (Clase 19): **MARCA visible → HOOK de dolor/deseo → CUERPO con beneficio + "resultados que sí se sienten" (microángulos) → CTA con BENEFICIO (no el nombre) → PRUEBA SOCIAL → OFERTA de tratamiento** (1u/2u/3u, "la más elegida") + modo de uso.
4. **El creativo es la nueva segmentación (Andrómeda):** el copy se le escribe a **META**, no al cliente — cada beneficio/síntoma/avatar es una **señal** de segmentación. Apuntar a un **avatar amplio** ("si tenés más de 45…"). Repetir el ángulo principal.
5. **Formato:** las **imágenes escalan** igual o mejor que el video (muestran todo de inmediato) y se producen en masa (Gemini/Freepik hasta 100). Joaquín 80% imagen. Diversificar 9:16 / 1:1 / 4:5 (cada formato = otro público).
6. **Concepto de TESTIMONIO / momentos antes→después** (Clase 19): reseña 4-5 estrellas, punto A→punto B con el producto de puente. Convierte muchísimo.
7. **Fuente de conceptos:** investigación de mercado real (Reddit, Amazon, YouTube, TikTok, foros) — dolores, deseos, síntomas, momentos. Y **marcas de EE.UU. que facturan millones** para replicar estructura. Replicar hook ganador de la Ad Li
---

## 5. SATURACIÓN POR CUENTA — el test de si el ángulo VIAJA (obligatorio antes de meter volumen)

> Un ángulo ganador **NO rinde igual en todas las cuentas**. Nunca se lee agregado: se lee **cuenta
> por cuenta**. Esta sección la ejecuta ETAPA-8 antes de proponer cualquier duplicación, y ETAPA-7 la
> calcula. Historia (el caso TINNIDROP que originó la regla):
> `_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §5.

**PROCEDIMIENTO — matriz ÁNGULO × CUENTA:**
1. Armar la matriz: filas = ángulos, columnas = cuentas, celdas = ventas + CPA real de esa combinación.
2. Clasificar cada ángulo:
   · **VIAJA** → vende en ≥3 de N cuentas con CPA ≤ Break-Even → **es el activo de volumen.** Acá va la duplicación fuerte. ("Cuando vende en las 4 cuentas = súper winner", Clase 15.)
   · **LOCAL** → vende solo en 1-2 cuentas → **no regarlo a más cuentas todavía.** Duplicar SOLO dentro de las cuentas donde ya vendió.
   · **MURIENDO** → vendía antes y ahora está sobre Break-Even en la mayoría → es fatiga de CREATIVO, no de ángulo → va a §4 (renovar creativo), NO a duplicación.
3. **Detección de cuenta saturada:** si un ángulo rinde **≥2× peor** en una cuenta que su mediana en las otras, esa cuenta está SATURADA para ese ángulo. El volumen va a las frescas; en la saturada se apaga ese conjunto o se le mete creativo renovado.
4. **Nunca** proponer "regar a más cuentas" un ángulo que aún no probó que viaja. Distinción clave:
   · **Multicuenta = VALIDAR** si viaja → 1 copia por cuenta, presupuesto base, SIN subir nada.
   · **Duplicación = VOLUMEN** → solo donde ya vendió, ×N copias.

---

## 6. MATRIZ DE DUPLICACIÓN — cuánto volumen y dónde (lo que produce las ventas de mañana)

> Doctrina: Camilo (Clase 11) duplica el conjunto ganador **hasta 8-10 veces dentro de la misma campaña**; Mercy (SKOOL 6.2) duplica los conjuntos ganadores **×3-10 a las 9-10 AM**; Mercy 6.3 duplica la **campaña ×2 en borrador** (su original trajo 25 conversaciones a 636 y la copia idéntica 44 a 376). Duplicar **NO es subir presupuesto**: es "cada anuncio es un vendedor". El CPA se mantiene, el volumen se multiplica. Subir presupuesto vertical hace que "Meta gaste como loco" y encarece el CPA.

ETAPA-8 entrega la duplicación como **TABLA EXPLÍCITA**, nunca como "duplicá lo que funciona":

| Conjunto (ángulo) | Cuenta destino | ×N copias | $/día c/u | Ventas/día proyectadas | Por qué |
|---|---|---|---|---|---|

**REGLAS DE DIMENSIONAMIENTO:**
- Solo se duplica lo que tiene **CPA real ≤ CPA Base** (no basta estar bajo Break-Even).
- Copias por conjunto: **×3-4 por cuenta** como default; hasta **×10** si el CPA está a ≤50% del Base y hay caja.
- **NO duplicar en la cuenta saturada** para ese ángulo (§5).
- Presupuesto por copia = **el mismo del original**, sin subirlo. El único aumento permitido es el **surfing +20%** de la mañana siguiente (9-10 AM), y solo a lo que vendió.
- Al duplicar: **"duplicar la configuración original"** (nunca una recomendación de Meta) + marcar **"mostrar reacciones, comentarios y contenido compartido"** (hereda prueba social) + verificar que el objetivo siga en **"maximizar conversaciones"** (Meta lo revierte solo a "clics en el enlace") + destino WhatsApp + 2 anuncios adentro.
- **Proyección obligatoria:** `ventas/día ≈ (N × presupuesto_diario_$ × TASA) ÷ CPA_Q`. Sumar el total y declarar el gasto incremental.
- **Gate de rentabilidad:** cerrar con el neto proyectado `ganancia = ventas_proyectadas × (Break-Even − CPA_real)`. Si sale ≤0, NO duplicar.

---

## 7. FASE 3 — ENTREGABLE FIJO: `PRODUCTOS/[NOMBRE]/4_PLAN_ESCALADO.txt`

> El escalado necesita archivo y plantilla fija, igual que FASE 1: sin eso cada plan sale distinto.
> Historia: `_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §7.

**ESQUEMA DE ARCHIVOS POR PRODUCTO (fijo, no cambia entre productos):**
| Archivo | Rol | Cuándo se crea |
|---|---|---|
| `1_HACER_MANUAL.txt` | lo que el operador ejecuta a mano (bot, prompts, copies, checklist) | FASE 1 |
| `2_DATA_PRODUCTO.txt` | memoria del producto (costeo, ángulos, avatar, resultados) | FASE 1 |
| `3_CAMPAÑA_META.txt` | llave técnica: IDs de campaña/conjuntos/anuncios/creativos y Post IDs | al crear por MCP |
| **`4_PLAN_ESCALADO.txt`** | **el plan de FASE 3** — se SOBRESCRIBE en cada ciclo de escalado | al declarar ganador |

⚠️ El slot `3_` es **solo** para IDs de Meta. Nunca meter ahí el plan de escalado (historia:
`_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §7).

**PLANTILLA OBLIGATORIA de `4_PLAN_ESCALADO.txt`** (ETAPA-8 la llena; se sobrescribe, no se acumulan versiones):
```
[PRODUCTO] · PLAN DE ESCALADO FASE 3 · v[N] · [FECHA]
Cuenta madre · página · tasa · CPA Base Q.. · Break-Even Q..
CPA real semanal (LucidSales, del _FACT_VENTAS.csv) · integridad de ventana: X/7 días

0. VEREDICTO EN UNA LÍNEA: [escalar fuerte / escalar suave / solo renovar creativo / no escalar aún]
1. MATRIZ ÁNGULO × CUENTA (§5) — con clasificación VIAJA / LOCAL / MURIENDO y cuentas saturadas
2. APAGAR — lista exacta [campaña → conjunto] con gasto, ventas y motivo (conversación / ventas-tras-PD / sobre BE)
3. MATRIZ DE DUPLICACIÓN (§6) — tabla con ×N por cuenta + ventas y gasto proyectados + neto
4. SURFING +20% — a qué conjuntos, mañana 9-10 AM
5. POST ID / PUBLICACIÓN EN PÁGINA — IDs vigentes por ángulo ganador
6. CREATIVOS (§4) — el POR QUÉ ganó + brief de 3-5 conceptos nuevos para ETAPA-4
6b. BANCO DE MICROÁNGULOS (ETAPA-3, PASO 0 de fase-3-escalado) — los 8-12 MICROÁNGULOS del
    ángulo ganador con su frase de apertura, tal como los entregó ETAPA-3 (banco de copy de la
    expansión horizontal). Este bloque es lo que `flujo.py` verifica en `F3.plan` (T8-4,
    23-sep-2026): sin él, el output de ETAPA-3 no queda con ningún consumidor visible en disco.
7. PRECIO — subir gradual / mantener
8. ORDEN DE EJECUCIÓN — checklist numerado con [ ] para tildar
9. QUÉ APRENDIMOS — lo que NO volver a probar en este producto
```

**REGLAS DEL ENTREGABLE:**
- Se **sobrescribe** en cada ciclo y sube `v[N]`. Prohibido dejar `_V2`, `_SIMULACION`, `_COPIA` sueltos (misma regla que FASE 1).
- Todo número de VENTA sale de `PRODUCTOS/_FACT_VENTAS.csv` (la única que suma al P&L), nunca de una auditoría en prosa. Las señales de entrega (mensajes/clics/CPM) salen de `_FACT_ENTREGA.csv` y **no se suman al gasto** — reglas de lectura en `DOCTRINA/DATA_PLAYBOOK.md` §3.
- Si la ventana tiene días 🔴 en `_BITACORA_DATA.txt` → el plan se marca **PARCIAL** y no se declara ganador oficial ni se manda matar por ventas.
- El plan cierra actualizando `_GANANCIAS.txt` con el neto proyectado del movimiento.

---

## 7b. EXPLORACIÓN DE ÁNGULOS NUEVOS MIENTRAS SE ESCALA (F3.exploracion, P12)

Decisión del operador, 22-sep-2026: escalar el ganador no significa dejar de buscar el próximo.
Mientras F3 escala, corre en PARALELO un mini-F1 FIJO de `exploracion_n_angulos`
(`_PARAMETROS_DECISION.csv`, default 3) ángulos que el producto **nunca probó** — misma
exclusión que `reingreso_f1.py`/`_angulos_probados()` — cada uno en su propio conjunto ABO al
presupuesto por-adset de FASE 1 (`_PARAMETROS_PUBLICACION.csv` fase=3 brazo=EXPLORACION), TODO
EN IMAGEN, medido por VENTA agregando por `angulo_key` exactamente como F1 (invariante 1).

- **Arranca solo cuando F3 es rentable** (decidir.py en ESCALAR con volumen mínimo) — nunca
  antes: explorar sin caja no es prudencia, es apostar el escalado. Gate declarado en
  `DOCTRINA/FLUJO.json`, nodo `F3.exploracion` (`requiere`), evaluado por `flujo.gate_nodo()`.
- **No compite con el escalado ni lo bloquea**: es paralela, como `F2.etapa-11`. No consume el
  presupuesto de la campaña `ESCALA-*`; es una campaña `EXPLORA` propia.
- **Un ganador de la exploración entra a F2 como cualquier otro ganador de F1**: el gate
  F1→F2 (`angulo_ganador`) no distingue de qué conjunto salió la evidencia — no hay un camino
  paralelo nuevo que mantener, solo más conjuntos alimentando el mismo gate.
- Ejecutor: `etapa-2` (fichas de los ángulos nuevos) → `etapa-6` (`_PLAN_EXPLORACION.json`) →
  `etapa-guardar-producto` → `publicar-meta` con `Ads/_TOOLS/gen_publicacion.py --fase 3
  --brazo EXPLORACION`.

---

## 8. MÉTRICAS DE EVALUACIÓN DE TESTEO (umbrales canónicos — fuente única)

> **Los valores vigentes viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y los ejecuta `Ads/_TOOLS/decidir.py`**
> (`umbral_conv_clic_enlace_pct`, `min_link_clicks_conv`, `max_pausas_por_dia`, `dias_min_cod_pausa_ventas`,
> `factor_tolerancia_pd`, `surfing_pct`). Este texto es la doctrina que los justifica; si difieren, manda el CSV
> y `verificar_guia_madre.py` lo canta. Desde el 09-sep-2026 ninguna etapa recalcula estos umbrales en prosa.

> Movidas desde `CLAUDE.md` el 31-jul-2026. **Este archivo es el dueño**: `etapa-6`, `etapa-7` y `etapa-8` leen los umbrales de acá, no los duplican. Sirven para diagnosticar por qué un ángulo gana o falla; el orquestador las interpreta antes de activar `etapa-3`. El operador entrega los datos de los 6 conjuntos en estos términos.

**Métrica 1 — % Conversación por Clic en Enlace** *(la más importante)* — `Conversaciones ÷ Clics × 100`
- < 35% → problema en el flujo del bot o incoherencia anuncio-bot (revisar `etapa-5`)
- 35–49% → bueno / escalable
- ≥ 50% (50–70%) → excelente y súper escalable

(Clase 7 + Clase 15, Joaquín)

**Métrica 2 — % Conversación por Impresión** — `Conversaciones ÷ Impresiones × 100`
- 1.5% malo · 2.5% bueno · 3.5% excelente · 4.5%+ extraordinario

**Métrica 3 — CPA real** — `Gastado ÷ Ventas confirmadas`. Comparar contra el CPA Break Even (`DOCTRINA/DATA_PLAYBOOK.md` §4). Si CPA real > CPA Break Even → ángulo no rentable.

**Métricas de atención (CPM / CPC / Frecuencia)** *(referencia de mercado, no umbral duro)*
- CPM (Colombia/COP): bueno 6,000–10,000 · ~10,000 menos saturado (trabajable) · 17,000–20,000+ ángulo saturado/competido. Varía por ticket: ticket bajo (<100k) → CPM más bajo. (Clase 7 + 15 + 22, Joaquín)
- CPC (Colombia/COP): ~150–250. (Clase 15 actualiza a ~150; Clase 7 daba 200–250.) Ecuador y USA mucho más caros.
- Frecuencia: ≥1.9 → fatiga creativa (renovar creativo, Clase 4) · 2–3 con CPM/CPC caro → apagar (Clase 7).

> ⚠️ Estos números son de **Colombia (COP)**. El sistema opera en **Quetzales (Guatemala)** — mercado nuevo y más barato (Clase 15). Usar como referencia cualitativa, no como umbral fijo en Q. Las métricas % (conversación por clic/impresión) y el CPA contra Break Even sí son la base de decisión.

**Diagnóstico rápido:**

| Síntoma | Causa probable | Dónde actuar |
|---|---|---|
| Muchos clics, pocos chats | Anuncio o plantilla de inicio de conversación | `etapa-4` / config. del chat |
| Muchos chats, pocas ventas | Incoherencia anuncio-bot o flujo débil | `etapa-5` |
| CPM muy alto | Ángulo saturado o copy similar a competencia | `etapa-2` / nuevo ángulo |
| % conversación por clic < 35% | Llegan al chat pero no escriben | Revisar plantilla de inicio preescrita |
