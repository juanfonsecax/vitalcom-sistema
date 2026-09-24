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

