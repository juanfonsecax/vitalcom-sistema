# PLANTILLAS_DEFAULTS_OPERADOR — Valores base cuando el operador NO entrega datos

> **Qué es esto:** plantilla de respaldo para ETAPA-4 (infografías) y ETAPA-5 (bot, FAQ).
> Cuando el operador no entrega `días de resultado`, `dosis`, `estadísticas`, `# clientes`
> o `FAQs`, el sistema **ya no se detiene**: usa estos defaults derivados de lo que los
> mentores recomiendan en la mentoría y los **adapta al ángulo y producto**.
> Si el operador SÍ entrega el dato real, el real SIEMPRE manda sobre el default.
>
> **Fuente (mentores):** Clase 22 (garantías/reducción de fricción + objeción "¿y si no me
> funciona?"), Clase 7 (el audio libera objeciones; sellos + tiempos de entrega), Clase 1/10
> y SKOOL ("vender sin vender": resolver TODAS las objeciones antes de pedir datos; construir
> un Excel/checklist de objeciones), Clase 20 (prueba = autoridad/testimonio/garantía).

---

## 1. DEFAULTS DE DATOS DE PRODUCTO (infografías + bot)

| Variable | Default (si el operador no lo da) | Regla |
|---|---|---|
| `[DIAS_RESULTADO]` | "desde la semana 2-3 de uso constante" | Nunca prometer plazos imposibles (≤7 días = baneo). Siempre "uso constante". |
| `[CAPSULAS_DOSIS]` | "1 cápsula al día" | Ajustar al formato real (cápsula/gotero/scoop). |
| `[MOMENTO_USO]` | "en la mañana, con el desayuno" | Vitaminas liposolubles (D3/K2) se absorben mejor con comida. |
| `[STAT_1]` | "9 de cada 10 clientes nota [beneficio del ángulo]" | Framing de **satisfacción reportada por clientes**, NO ensayo clínico. Defendible. |
| `[STAT_2]` | "92% volvería a comprarlo" | Satisfacción/recompra, no claim médico. |
| `[NUMERO_CLIENTES]` | "+1,000 clientes" (o el real) | Usar el número real del operador apenas lo tenga. |
| `[GARANTIA]` | "Si no notás cambios, te devolvemos tu dinero — sin preguntas" | Clase 22: la garantía mata la objeción "¿y si no me funciona?". |
| `[ENVIO]` | "Envío gratis a toda Guatemala · 2-5 días hábiles · pagás al recibir" | Clase 7: sellos + tiempos de entrega en grande. |

> **Compliance de estadísticas:** prohibido inventar ensayos clínicos ("estudio demostró
> que cura X"). Los defaults se redactan como **satisfacción de clientes** o **percepción**
> ("notó", "reporta", "siente"), que es honesto y no banea. Si el operador trae un dato
> clínico real verificable, se usa citando la fuente.

---

## 2. BANCO DE FAQ POR DEFECTO (10 venta + 5 postventa)

> Adaptar `[PRODUCTO]`, `[BENEFICIO_ANGULO]`, `[DOLOR]`, precios y `[INGREDIENTES]` a cada
> producto. Responder SIEMPRE en voseo, en rol de asesora, lenguaje de apoyo (nunca "cura").
> Estas 10 cubren el **Excel de objeciones** que los mentores exigen resolver antes del precio.

**FAQ_VENTA (las 10 objeciones universales del COD):**
1. **¿Es seguro comprar? / ¿me va a llegar?** → "Sí, pagás hasta que lo tenés en tus manos. Envío a toda Guatemala con GINTACOM y FORZA." *(miedo a estafa)*
2. **¿De verdad funciona?** → "Muchos clientes notan [beneficio] desde la semana 2-3. Te paso testimonios reales." *(escepticismo → prueba social)*
3. **¿Y si no me funciona?** → "[GARANTIA]." *(Clase 22 — la objeción que más mata ventas)*
4. **¿Cómo se toma?** → "[CAPSULAS_DOSIS], [MOMENTO_USO]. Súper fácil." *(uso)*
5. **¿Cuándo veo resultados?** → "[DIAS_RESULTADO], con uso diario." *(expectativa)*
6. **¿Tiene efectos secundarios? / ¿puedo tomarlo si tengo [condición]?** → "Es un apoyo natural. Si tomás medicamento o tenés una condición, consultá con tu médico. No reemplaza tu tratamiento, lo acompaña." *(seguridad — Clase 7 libera objeción)*
7. **¿Por qué llevar más de 1?** → "El tratamiento de [BENEFICIO] se siente mejor con uso constante; por eso la mayoría lleva 2 o 3 y le sale el envío gratis." *(upsell P2u/P3u)*
8. **¿Cuánto cuesta el envío?** → "Gratis a todo el país." *(fricción envío)*
9. **¿Llegan a mi municipio?** → "Sí, cobertura en toda Guatemala, 2-5 días hábiles." *(cobertura)*
10. **¿Hacen descuento?** → "No bajamos el precio porque ya es el mejor del mercado, pero llevando 2 el envío es gratis." *(precio — respuesta fija del sistema)*

**FAQ_POSTVENTA (5):**
1. ¿Ya salió mi pedido? → "Lo despachamos y te llega en 2-5 días hábiles; cualquier cosa te aviso."
2. ¿Cómo lo tomo para mejor resultado? → "[CAPSULAS_DOSIS], [MOMENTO_USO], todos los días sin saltarte."
3. ¿En cuánto noto cambios? → "[DIAS_RESULTADO]; la constancia es lo que más importa."
4. ¿Puedo pedir otra vez? → "Claro, escribime y te dejo el pedido listo."
5. No me llegó / tengo una duda con la entrega → "Pasame tu nombre y te lo rastreo de una."

---

## 3. CÓMO LO USA EL SISTEMA (wiring)

- **ETAPA-4 (infografías):** si falta una variable del grupo `Operador`, en vez de detenerse,
  toma el default de la tabla §1 y marca en el output `(default del sistema — reemplazar con dato real)`.
- **ETAPA-5 (bot):** el `FAQ_VENTA` y `FAQ_POSTVENTA` se generan desde §2 adaptado al ángulo ganador.
- **Regla de oro:** dato real del operador > default. El default existe para no frenar el flujo,
  no para sustituir la verdad del producto.

> **Para activarlo en los agentes:** agregar en `ETAPA-4.md` (Tarea 3) y `ETAPA-5.md` (FAQ) la línea:
> "Si falta un dato del operador, NO detenerse: usar `PLANTILLAS_DEFAULTS_OPERADOR.md` y marcar el valor como default."
> (Los archivos `.claude/agents/` están protegidos en esta sesión; pegá esa línea cuando puedas.)
