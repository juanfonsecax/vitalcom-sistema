# PLANTILLAS_FLUJO_BOT — EL FLUJO LUCIDBOT, DECLARADO

> **Dueño único del TEXTO del flujo LucidBot.** Acá vive el layout completo: lo que es literal, lo
> que es variable y lo que es instrucción. Lo renderiza `Ads/_TOOLS/gen_flujo_bot.py` leyendo
> `PRODUCTOS/_DIM_FLUJO_BOT.csv`, `PRODUCTOS/_DIM_MERCADOS.csv` y `PRODUCTOS/_DIM_PRECIOS.csv`, y
> deja el resultado en `PRODUCTOS/[PK]/FLUJO_LUCIDBOT.md`.
>
> **Estructura base:** el flujo de CLEARSTEM — el mejor cierre y el mejor CPA del portafolio
> (12.8 % acumulado · 7.3 jul → 13.3 ago → **17.3 sep** · CPA Q42.9 contra BE Q105.9).
> **Doctrina:** las dos clases de agosto de Calet (16-ago y 22-ago), que son las más recientes
> sobre flujo y derogan cualquier versión anterior en lo que toquen (§0).

```bash
python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM          # renderiza el flujo del producto
python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --copy   # solo lo que se pega en Lucid
python Ads/_TOOLS/gen_flujo_bot.py --validar          # gate de todo el portafolio
```

---

## 0. LO QUE MANDAN LAS DOS CLASES DE AGOSTO

Son la fuente vigente. Las citas son textuales de la transcripción, no paráfrasis.

| # | Regla | Cita |
|---|---|---|
| **A** | **El flujo va ANTES que la estructura de campaña.** Ninguna estructura salva un flujo malo. | *"Ustedes lo que se deben preocupar ahorita más que estructura de campaña es el flujo de venta, porque al yo tener un flujo de venta, yo puedo colocar cualquier estructura y cualquier estructura me va a vender. Pero si yo tengo un mal flujo o un flujo desoptimizado, cualquier estructura que ustedes coloquen no les va a funcionar. Porque el tráfico va igual."* (16-ago) |
| **B** | **El objetivo de cierre es 15-20 %**, y la condición es ser rentable. | *"yo primero me tengo que enfocar es que mi porcentaje de conversión esté en un 18, en un 20, en un 15 y que yo sea rentable."* (16-ago) |
| **C** | **PROHIBIDO escalar con cierre bajo.** Escalar un cierre malo escala el error. | *"Uno no puede escalar algo. Si uno tiene un cierre de cinco, uno escala y va a escalar malos resultados, malas métricas… el cierre más bajo, por lo tanto las ventas van a ser bajas, el CPA se va a subir."* (22-ago) |
| **D** | **Lo que más mueve el cierre son las PROPUESTAS DE VALOR.** No los hooks, no los testimonios. Es la respuesta directa a *"¿en qué te centrás para optimizar el flujo?"*. | *"lo que yo más me centro es en las propuestas de valor, en las imágenes, colocarle en todas muchas propuestas de valor, atacando todo, resaltando lo que van a recibir, venderle el resultado, meterles muchos beneficios, convencerlo de decirle tantos beneficios, tantas propuestas de valor que el cliente diga: 'no, este es el producto perfecto y voy a comprarlo'."* (22-ago) |
| **E** | **Cierre bajo → primer diagnóstico es CONGRUENCIA anuncio ↔ flujo**, no reescribir copy. | *"si tú tienes un cierre bajo, uno empieza a analizar: bueno, qué anuncio está llegando, ver si ese anuncio concuerda con lo que tengo en el flujo, y ahí donde yo hago la optimización."* (22-ago) · *"el ángulo que tenemos del flujo no está muy encaminado al hígado graso… la gente de pronto llega y ahí pierde la emoción de comprar."* (16-ago) |
| **F** | **Un cambio de flujo se nota en HORAS, no en semanas.** Por eso se loguea el día que se aplica. | *"tú haces un cambio y eso se nota… si tú haces una buena optimización, optimizás en la mañana y ya al mediodía van a llegar más ventas, el cierre te va a subir porque hiciste esos cambios."* (22-ago) |
| **G** | **La investigación de mercado previa evita rehacer el flujo.** | *"Si tú haces una buena investigación de mercado, un análisis de mercado desde el inicio, probablemente no te toque cambiar casi ni siquiera el flujo. Tú te centras en sacar creativo."* (22-ago) |
| **H** | **Ningún flujo está terminado.** Aun uno que vende puede subir. | *"a veces uno dice: no, yo tengo mi flujo optimizado porque me llegan ventas — pero el flujo siempre puede subir más."* (22-ago) |
| **I** | **La información del producto NO va en las reglas.** Las reglas son solo CONVERSACIONALES. | *"la información de producto no va en la regla… en las reglas va reglas conversacionales: cómo le va a dar el precio, cómo le va a pedir la ciudad, cuándo se la va a pedir. En las reglas no va nada formativo."* (16-ago) |
| **J** | **LucidBot queda DESACTIVADO al importar de Superbodega.** El flujo se ve cargado y el mensaje inicial no sale. Activarlo es manual. | *"cuando se importan los productos, él solamente queda activado para el IA… traía desactivado LucidBot. Tienes que activarle LucidBot para que él mande lo del mensaje inicial."* (16-ago) |
| **K** | **Las FAQ crecen leyendo los chats reales.** No se quedan en el banco inicial. | *"yo le agrego por lo general cinco generales, y a medida que las personas… viendo el chat uno va agregándolas también."* (16-ago) |
| **L** | **El CIERRE no corona: corta.** Caso medido en clase — mismo creativo duplicado, mismo gasto: uno con 4 mensajes cerró 2 (50 %), el otro cerró al 25 % pero hizo 5 ventas. La orden fue diversificar conceptos del que **vendió más**, no del que cerró mejor. | *"el de dos ventas le llegaron cuatro mensajes y cerró dos, mientras que el otro estaba cerrando apenas al 25 %… — haz el ejercicio que acabamos de hacer: comienza a validar lo mismo que te está funcionando en diferentes conceptos."* (16-ago) |

> **Choque registrado (C-06).** La regla **D** pide *"muchas propuestas de valor, atacando todo"*;
> la Clase 22 pide no romper el **umbral cognitivo**. Se resuelve por ubicación: **dentro del bot
> manda D** (es post-clic, Meta no lo lee, la prioridad es conversión y no hay límite de
> compliance); **en el creativo del ad manda el umbral cognitivo**, y cuánta densidad soporta la
> imagen es materia del test T01.

---

## 1. LAS TRES NOTACIONES

Son tres y no se parecen entre sí. Ésa es toda la regla: **una forma, un significado.**

| Notación | Qué es | Quién la resuelve | Si falta |
|---|---|---|---|
| `{{variable}}` | Un valor que vive en un CSV | `gen_flujo_bot.py` lo sustituye | **BLOQUEA** con exit 1 y nombra al dueño |
| `<<BLOQUE:nombre>>` | Texto largo que exige juicio (audio, testimonios, FAQ) | `etapa-5` lo escribe | se marca pendiente |
| `>> ` al inicio de la línea | **INSTRUCCIÓN.** Le habla al operador o a `etapa-5`. **NUNCA se pega en LucidBot** | nadie: es una nota | — |

Todo lo demás es **literal**: se copia tal cual, para todos los productos, sin reescribir.

`--copy` imprime el flujo sin ninguna línea `>>`: es lo que se pega, y nada más.

**Dos formas que se parecen a un placeholder y no lo son — ninguna se toca:**
- `{CIUDAD}`, `{NOMBRE}`, `{TOTAL}` (llave simple) son **variables de LucidBot en tiempo de
  conversación**. Las resuelve el bot, no este sistema.
- `[IMPORTANTE: …]` es la **sintaxis literal del campo «Reglas»** de LucidBot. Es contenido, no
  un hueco por llenar.

---

## 2. DICCIONARIO DE VARIABLES

### 2.1 Del mercado — `PRODUCTOS/_DIM_MERCADOS.csv`

| Variable | GT | CO |
|---|---|---|
| `{{pais}}` | Guatemala | Colombia |
| `{{pais_cobertura}}` | toda Guatemala | toda Colombia |
| `{{persona}}` | voseo | tuteo |
| `{{simbolo}}` | Q | $ |
| `{{unidad_geo}}` | municipio y departamento | ciudad y departamento |
| `{{unidad_local}}` | municipio | ciudad |
| `{{transportadoras}}` | GINTACOM y FORZA | INTERRAPIDISIMO y ENVIA |
| `{{dias_entrega}}` | 2 a 5 días hábiles | 2 a 5 días hábiles |
| `{{dias_espera_casa}}` | 5 | 5 |

Todas bloquean.

### 2.2 De la tienda y el producto — `PRODUCTOS/_DIM_FLUJO_BOT.csv`

| Variable | Qué es | Lo produce | Bloquea |
|---|---|---|---|
| `{{nombre_tienda}}` | La **TIENDA**. Nunca la fanpage, nunca la asesora | operador | sí |
| `{{nombre_asesor}}` | Se revela en el audio o en el cierre, nunca en el saludo | operador | sí |
| `{{producto_display}}` | Nombre comercial | `_DIM_PRODUCTOS.csv` | sí |
| `{{envase}}` | frasco · paquete · unidad | operador | sí |
| `{{duracion_1u}}` | Duración de 1 unidad, ej. `1 mes` | operador | no |
| `{{dias_resultado}}` | `entre la semana 2 y 3` | `etapa-1b` / defaults | sí |
| `{{mecanismo_1}}` `{{mecanismo_2}}` | Ingrediente + qué hace | `etapa-1b` | sí |
| `{{prueba_social}}` | La cifra **con su unidad**, trazable a una fuente | operador | sí |
| `{{garantia_texto}}` | La política de garantía vigente, **una sola** | operador | sí |
| `{{n_infografias}}` `{{n_testimonios}}` | Cuántas piezas corre este flujo | operador | sí |
| `{{fuente_testimonios}}` | `REAL` o `REDACTADO` | operador | sí |

### 2.3 Del ángulo — las escribe `etapa-5` en el CSV

Son frases cortas. La oración que las envuelve es fija; la frase es el juicio.

| Variable | CLEARSTEM | TINNIDROP |
|---|---|---|
| `{{dolor_angulo}}` | el acné hormonal | ese zumbido |
| `{{solucion_fallida}}` | cremas ni con jabones | gotas comunes ni con lo de siempre |
| `{{recaida}}` | vuelve siempre al mismo lugar | *(opcional)* |
| `{{sintoma_superficial}}` | son los granos | es el sonido |
| `{{consecuencia_emocional}}` | evitar las fotos, la pena de que te vean de cerca, tener que planear el maquillaje todos los días | no poder dormir, concentrarte ni estar en paz |
| `{{area_cuidado}}` | tu piel desde adentro | tu descanso y tu salud auditiva |
| `{{verbo_tratar}}` | trabajás | lo tratás |
| `{{resultado_sostenido}}` | el cambio sí se mantiene | el alivio sí se siente |
| `{{razon_tier_alto}}` | *(ver CSV)* | *(opcional)* |

### 2.4 Los precios — derivados de `PRODUCTOS/_DIM_PRECIOS.csv`

`{{escalera_ofertas}}` **no se tipea**: se construye con las filas `ACTIVO` del producto y su
columna `etiqueta` (`1x` · `2x` · `3x` · `2X1` · `4X2`). Así la arquitectura de oferta sale del
CSV, y los productos de uso único no reciben una escalera de tres unidades iguales que
`ETAPA-1.md` Paso 2 prohíbe.

### 2.5 La apertura por nivel de conciencia — derivada de `PRODUCTOS/_DIM_CONJUNTOS.csv`

`{{apertura_nivel}}` **no se tipea ni lo escribe `etapa-5`**: `gen_flujo_bot.py` resuelve el
`nivel_conciencia` del ángulo ganador (`{{angulo_nombre}}`) sobre las filas `ACTIVO` de
`_DIM_CONJUNTOS.csv`, normalizado con los alias de `_DIM_VOCABULARIO.csv`, y arma la instrucción
desde el dict `NIVELES_APERTURA` — su único dueño de texto (`ETAPA-5.md` Paso 3 solo apunta acá).
Solo aplica al **flujo dedicado** (el producto ya tiene algún conjunto fuera de `FASE1`); en el
bot paraguas de FASE 1 la línea se omite sin bloquear.

| Nivel | Falta / ambiguo / en conflicto → | Se resuelve → |
|---|---|---|
| `1` / `2` / `3A` / `3B` | **BLOQUEA** con exit 1, nombrando qué se encontró en `_DIM_CONJUNTOS.csv` | instrucción `>>` antes de ELEMENTO 3, coherente con la apertura del anuncio |

`3` a secas es alias sucio **AMBIGUO** (`_DIM_VOCABULARIO.csv` lo mapea a `REVISAR`: no distingue
3A de 3B) y bloquea igual que si faltara.

---

## 3. LA PLANTILLA

```
════════════════════════════════════════════════════════════
FLUJO LUCIDBOT — {{producto_display}} | {{angulo_nombre}}
{{pais}} | {{nombre_tienda}} | {{fecha_generacion}}
════════════════════════════════════════════════════════════
>> TEMPORIZADOR entre mensajes: 2-3 segundos SIEMPRE. Nunca 15 ni más.
>> Si se simula que "una asesora está llegando", máximo 5 seg SOLO en ese primer beat.
>> Un silencio largo es la ventana para que el cliente se vaya con la competencia.
>> TRATAMIENTO DE PERSONA de este flujo: {{persona}}.
>> ANTES DE LANZAR: si el producto se importó de Superbodega, LucidBot queda DESACTIVADO
>> y el mensaje inicial no sale. Activarlo es un paso MANUAL (clase 16-ago).

═══════════════ FICHA DEL PRODUCTO (catálogo de LucidBot) ═══════════════
>> Los 4 campos de abajo se pegan TAL CUAL en la ficha de producto de LucidBot.
>> La información del producto va ACÁ y NUNCA en las reglas (clase 16-ago).

DESCRIPCIÓN:
<<BLOQUE:descripcion>>

MODO DE USO:
<<BLOQUE:modo_de_uso>>

CARACTERÍSTICAS TÉCNICAS:
<<BLOQUE:caracteristicas>>

CONTENIDO DEL PAQUETE:
<<BLOQUE:contenido>>

═══════════════════════ MENSAJE INICIAL ═══════════════════════

ELEMENTO 1 — TEXTO · SALUDO
¡Hola! 👋 Bienvenida/o a *{{nombre_tienda}}*, estamos encantados de tenerte por acá. En un momento una asesora se pondrá en contacto con vos. ✨
>> FIJO. No cambia por ángulo ni por producto.
>> NO lleva el nombre de la asesora — se revela en el audio o en el cierre.
>> NO lleva el dolor del ángulo, NO lleva el nombre del producto, NO lleva ninguna pregunta.
>> Lleva la TIENDA, nunca la fanpage: el nombre de la tienda es el que el cliente ve después
>> en la guía, en las novedades y en el cobro contraentrega.

ELEMENTO 2 — VIDEO 1 · AUTORIDAD: {{video_1}}
>> {{apertura_nivel}}
ELEMENTO 3 — VIDEO 2 · UGC: {{video_2}}

INFOGRAFÍAS ({{n_infografias}}): {{lista_infografias}}
>> Las plantillas visuales son de DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md. Acá solo se declaran.
>> Van SIN PRECIO, en 1080x1350 (4:5).
>> LO QUE MÁS MUEVE EL CIERRE VA ACÁ: muchas PROPUESTAS DE VALOR, no ingredientes sueltos.
>> Fórmula de cada una: [problema concreto del avatar] -> [qué hace el producto] -> [resultado].
>> Dentro del bot no hay límite de compliance ni de umbral cognitivo: la prioridad es CONVERTIR.
>> ORDEN SEGÚN EL BUYER TYPE del avatar: nicho EMOCIONAL -> la prueba de transformación
>> (antes/después o momento) va PRIMERO y los ingredientes después. Nicho TÉCNICO -> los
>> ingredientes con su mecanismo van primero.
>> La 1ª lleva un TÍTULO de dolor o deseo congruente con el anuncio, nunca el nombre del
>> producto ni la palabra "BENEFICIOS": es genérica y la gente escanea.
>> La de CONFIANZA abre con "PAGÁS AL RECIBIR" y lleva el sello de {{garantia_texto}} junto a
>> eso: es el reductor de fricción que responde "¿y si no me funciona?".

TEXTO · TRANSICIÓN A TESTIMONIOS
A continuación te muestro lo que dicen quienes ya lo tienen en casa 👇
>> FIJO.

TESTIMONIOS ({{n_testimonios}} · fuente {{fuente_testimonios}}):
<<BLOQUE:testimonios>>

AUDIO (45-55 seg):
<<BLOQUE:audio>>
>> Va DIRECTO después del último testimonio. NO hay texto de puente ni presentación previa.
>> SIN PRECIO y SIN contraentrega. La asesora se presenta DENTRO del audio.

ELEMENTO FINAL — CIERRE → PREGUNTA DE UBICACIÓN
Hola, soy {{nombre_asesor}}, estaré atendiéndote el día de hoy 😊 Contame, ¿desde qué {{unidad_geo}} nos escribís?
>> FIJO. Es el 1er sí: nadie da su ubicación sin intención de comprar.
>> Acá NO va una pregunta de opciones por dolor (A/B/C/D). El filtrado del avatar ya ocurrió
>> en el ANUNCIO: un ángulo bien definido es filtro automático. Preguntarlo otra vez agrega
>> fricción y carga cognitiva antes de haber dado valor.
>> Tampoco va "¿rápido o normal?" ni ninguna otra pregunta previa al 1er sí.

══════════════════════════ INTERACCIONES ══════════════════════════
>> En las frases clave usar *asterisco* de WhatsApp: dolor emocional, beneficio, prueba social,
>> garantía/contraentrega y "un solo mensaje". Refuerza sin saturar.
>> Cada turno lleva UN refuerzo corto y DISTINTO. Ninguno queda seco y logístico.

INTERACCIÓN 1 — AL RECIBIR LA UBICACIÓN
¡Qué bien, desde {CIUDAD}! 😊

Me alegra que estés dando el paso de cuidar {{area_cuidado}} — es una gran decisión por vos.

Confirmo que tenemos cobertura completa ahí, con envíos a {{pais_cobertura}} y *pago contraentrega*. Las entregas tardan de {{dias_entrega}}. 🚚

¿Deseás conocer nuestros precios?
>> El refuerzo de este turno VALIDA la decisión del cliente. Una línea, sin producto y sin precio.
>> "¿Deseás conocer nuestros precios?" es el 2º sí: nadie dice no a esta pregunta.

INTERACCIÓN 2 — PRESENTACIÓN DE PRECIOS
¡Claro! 😊

Ya sabés que {{dolor_angulo}} *no se quita con {{solucion_fallida}}* — {{recaida}}.

Y lo que más pesa no {{sintoma_superficial}}: es *{{consecuencia_emocional}}.*

{{producto_display}} actúa *desde la raíz* con {{mecanismo_1}} y {{mecanismo_2}}. Por eso tiene *{{prueba_social}}* de gente con resultados reales.

Cuando {{verbo_tratar}} *desde la raíz, {{resultado_sostenido}}.* ✨

OFERTAS HASTA AGOTAR

{{escalera_ofertas}}

{{razon_tier_alto}}

¿Confirmame tu {{unidad_geo}}? 😊
>> Es el turno de refuerzo MÁS FUERTE y el único que vuelve a hablar del producto.
>> Va CORTO: el cliente ya leyó todo lo de arriba. No re-explicar, solo empujar al paso siguiente.
>> Una sola presentación de precios. Sin filtro "rápido o normal".
>> Confirmar la ubicación una 2ª vez es el 3er sí: ya la dijo, pero repetirla avanza el cierre.
>> La escalera se deriva de _DIM_PRECIOS.csv. Ningún precio se escribe a mano acá.

INTERACCIÓN 3 — PEDIDO DE DATOS
¡Perfecto! Tranqui, no arriesgás nada: pagás solo cuando tengas el producto en tus manos, y llevás *{{garantia_texto}}*. 🙌

Antes de continuar con la compra asegurate de que vas a permanecer en casa los próximos {{dias_espera_casa}} días, o que algún familiar o amigo te reciba el producto en la dirección que indicarás.

En caso de no ser así, podés solicitar que tu envío se haga a la agencia principal de {{transportadoras}} de tu {{unidad_local}}.

Para continuar con la compra indicame los siguientes datos EN UN SOLO MENSAJE Y EN EL MISMO ORDEN:

1. Nombre
2. Apellido
3. Teléfono de LLAMADAS
4. Departamento
5. Municipio
6. Dirección exacta (o escribí OFICINA si reclamás en agencia)
7. Barrio
8. ¿Cuál opción preferís?
>> FIJO y universal. No se reescribe por producto.
>> El refuerzo de este turno es REVERSIÓN DE RIESGO y va en UNA sola línea: es el turno más
>> delicado y cargarlo de texto lo rompe.
>> El cierre es una INSTRUCCIÓN que da la compra por hecha ("la dirección que indicarás"),
>> nunca una pregunta abierta y nunca "¿querés comprar?".

INTERACCIÓN 4 — CONFIRMACIÓN DEL PEDIDO
¡Todo confirmado!

Resumen de tu pedido:
- Nombre: {NOMBRE} {APELLIDO}
- Teléfono: {TEL}
- Departamento: {DEPTO}
- Municipio: {MUNICIPIO}
- Dirección: {DIR}
- Barrio: {BARRIO}
- Producto: {{producto_display}} — {OPCIÓN}
- Total a pagar: {{simbolo}}{TOTAL} al recibir

¿Confirmás que los datos están correctos?
>> FIJO y universal.

INTERACCIÓN 5 — CIERRE FINAL
¡Listo, {NOMBRE}! Tu pedido fue tomado exitosamente.

Tu {{producto_display}} está en camino. La entrega tarda de {{dias_entrega}} en {MUNICIPIO}.

Recordá: solo pagás cuando lo tenés en tus manos. Si tenés alguna duda mientras tanto, acá estoy. ¡Que lo disfrutés mucho! 💜
>> FIJO y universal.
>> Una vez cerrada la venta, el bot solo responde preguntas. No sigue vendiendo.

═════════════ MENSAJES DE INACTIVIDAD (3) ═════════════
>> SON TRES, y esto SUPERSEDE el "máximo 2, primero a las 4-6 h" de la Clase 3. Motivo:
>> (a) el primer toque a los 30-60 min rinde 3-4x más que a las 12 h, y la secuencia estándar
>> es recordatorio / confianza / cierre dentro de las primeras 24 h; (b) Meta no penaliza por
>> cantidad de mensajes — la calificación del número se daña con BLOQUEOS y REPORTES, y tres
>> mensajes livianos con opt-out dañan menos que dos que provocan un bloqueo.
>> De la Clase 3 sigue vigente: respetar 7 AM-9 PM y reducir mensajes si la calificación baja.
>> Timing: 45 min / 5 h / ~23 h. El M3 se cuenta desde el último mensaje DEL CLIENTE: la ventana
>> de servicio de 24 h de WhatsApp se reinicia con cada mensaje suyo, no con los nuestros.
>> Si el M3 cae fuera de 7 AM-9 PM, se corre al día siguiente dentro de esa franja.
>> UNA sola pieza de media por mensaje (ninguna / video / audio). Nunca dos.
>> NINGUNO reprocha el silencio ("me dejaste en visto", "¿seguís ahí?"): el reproche activa culpa,
>> y la salida a la culpa en WhatsApp es BLOQUEAR. Si se busca sonar humano, la broma va sobre
>> la asesora, nunca sobre el cliente.
>> Si el número está en AMARILLO: correr solo M1 y M3. Omitir M2.
>> Si el cliente escribe STOP o toca el botón: marcar OPT-OUT.

M1 — 45 min · prompt de IA + video nuevo + texto fijo + botones "Hoy" / "Mañana"
>> FIJO y universal. Ya está cargado en Lucid. No se reescribe por producto.

M2 — 5 h · prompt de IA + audio testimonio + texto del producto + 2 botones de oferta
<<BLOQUE:m2>>
>> Ofrece SOLO DOS niveles (el bajo y el alto), nunca los tres: dos convierten mejor y el salto
>> al alto es donde está el margen.
>> El M2 todavía es venta activa: NO lleva botón de opt-out. Ofrecerlo acá regala leads
>> recuperables.

M3 — ~23 h · prompt de IA + texto fijo + botón "No me escribás más"
>> FIJO y universal. Ya está cargado en Lucid.
>> El M3 NO vende: se retira. Abre con una pregunta orientada al "NO" sobre el PROBLEMA del
>> cliente, no sobre el producto (ej. "¿Ya te resignaste al zumbido?"). El "no" da sensación
>> de autonomía y genera respuesta donde la presión no la genera.
>> El botón de opt-out va SOLO acá. Un reporte de spam cuesta 10-30x más en reputación que
>> un opt-out: si no le das salida fácil, el cliente usa "Reportar".

═══════════════════════════ FAQ ═══════════════════════════
<<BLOQUE:faq_venta>>
<<BLOQUE:faq_postventa>>
>> Se construyen desde el banco de dolor real [VOZ-REAL] de etapa-1b: las preguntas que la gente
>> HACE en reseñas y foros, no las inventadas.
>> Arrancan en ~5 generales y CRECEN leyendo los chats reales (clase 16-ago). Revisar chats es
>> parte de la operación, no un extra.
>> Compliance dentro del bot: lenguaje de apoyo ("apoya", "ayuda a"), nunca "cura/elimina/trata"
>> en una enfermedad grave nombrada. Fuera de eso, no se suaviza: la prioridad es conversión.

════════════ REGLAS CONVERSACIONALES (campo "Reglas" de LucidBot) ════════════
>> FIJAS y universales: se pegan igual para todo producto.
>> Acá va SOLO lo conversacional: cómo da el precio, cuándo pide la ubicación, cómo responde una
>> objeción. La ficha del producto va en SU campo, nunca acá (clase 16-ago).

[IMPORTANTE: Si el cliente envía parte de sus datos, dale tiempo para que escriba los faltantes. No seas insistente.]

[IMPORTANTE: Si el cliente ya envió sus datos, no preguntar nuevamente cuál producto desea comprar, ni preguntarle si están bien. Solo hacé el cierre agrupando los datos y resumiendo la compra con producto y precio.]

[IMPORTANTE: Si el cliente indicó que reclama en agencia u oficina, ese dato reemplaza la dirección. No preguntar dirección de casa ni barrio. Indicale que su pedido será enviado a la agencia principal de {{transportadoras}} de su {{unidad_local}}.]

[IMPORTANTE: Si el cliente escribió una palabra mal, corregila sin pedirle que la corrija. Hacelo de forma natural, sin hacer notar el error.]

[IMPORTANTE: NUNCA insistir en la misma pregunta más de 2 veces, y CAMBIÁ EL ENFOQUE en el 2do intento en vez de repetir igual. Ej. ubicación — 1ra vez: "Decime tu {{unidad_local}} para confirmarte cobertura." 2da vez: "Con tu {{unidad_local}} te confirmo si te llega con pago contraentrega." Después, cambiar de tema.]

[IMPORTANTE: Si el cliente eligió la opción de 1 unidad, persuadilo de llevar 2 o más por el mayor ahorro que representa.]

[IMPORTANTE: Si el cliente solicita descuento por una sola unidad, NO bajar el precio de 1 unidad. Respondé: "El precio de 1 unidad no lo puedo bajar porque ya es el mejor del mercado. Pero si llevás 2, te sale mucho más conveniente y el envío es totalmente gratis."]

[IMPORTANTE: Si el cliente pregunta "¿hasta cuándo está la promoción?" respondé: "Tenemos ese precio hasta agotar existencias."]

[IMPORTANTE: Si el cliente dice que hará el pedido después, respondé solamente: "¡Súper, no hay problema! Estaremos atentos a cuando desees realizar tu pedido."]

[IMPORTANTE: Si el cliente pregunta por ubicación o tienda física: "Nuestro centro de distribución trabaja solo por envíos y no tenemos atención al público. Hacemos entregas a casi {{pais_cobertura}} por {{transportadoras}}, según cobertura."]

[IMPORTANTE: Si el cliente envía GIFs, stickers o imágenes, respondé de forma amable sin describir el contenido visual.]

[IMPORTANTE: Si el cliente solicita audios, respondé: "En este momento no puedo enviarte audios pues el micrófono del celular está fallando."]

[IMPORTANTE: Una vez cerrada y confirmada la venta, solo respondé preguntas del cliente. No continuás intentando vender.]

[IMPORTANTE: TODO el texto usa {{persona}}. La confirmación de dirección usa "{{unidad_geo}}", no "ciudad" a secas.]

[IMPORTANTE: El audio NUNCA menciona precio.]

>> REGLAS CONDICIONALES — agregar SOLO las que apliquen a este producto (salen de etapa-1b):
>>   · Producto sensible o íntimo: "Tu pedido va en empaque 100% discreto, sin indicar el
>>     contenido por fuera."
>>   · Restricciones propias: contraindicaciones, edad mínima, no apto en embarazo o lactancia,
>>     sabor, etc.
>>   · Precio al por mayor (6+ unidades), si el operador lo autoriza y declaró el precio.
```

---

## 4. LOS BLOQUES DE JUICIO

Los escribe `etapa-5`, que es su dueño y tiene las reglas de redacción completas. La plantilla
solo declara dónde van y la regla dura que el gate sí puede verificar.

| Bloque | Qué es | Regla que el gate verifica |
|---|---|---|
| `descripcion` · `modo_de_uso` · `caracteristicas` · `contenido` | Los 4 campos del catálogo | nunca genéricos · framing "tratamiento de X días", nunca "1 frasco $X" |
| `testimonios` | 2-3 capturas con sus textos ya redactados | sin precio · sin verbos médicos prohibidos |
| `audio` | Guión de 45-55 seg | **sin precio** · sin contraentrega · segunda persona |
| `m2` | Texto del 2º mensaje de inactividad | dos niveles de oferta, nunca tres |
| `faq_venta` · `faq_postventa` | Preguntas reales del avatar | lenguaje de apoyo |

**`fuente_testimonios`.** Material real (`REAL`) gana a material fabricado (`REDACTADO`). La
columna existe para poder medir la diferencia.

---

## 5. PROHIBICIONES — EL GATE LAS RECHAZA

1. **Un `{{…}}` sin resolver** en la salida. Exit 1 con el nombre de la variable y su dueño.
2. **Pregunta filtro de dolor A/B/C/D** en cualquier elemento. El filtrado ya ocurrió en el ad.
3. **Dos plazos de garantía distintos en el mismo flujo.** Va **un solo** plazo, el vigente, igual en los tres escalones.
4. **Precio literal escrito en el texto.** Todo precio entra por `{{escalera_ofertas}}`.
5. **Cifra de prueba social sin unidad declarada.** "N reseñas" y "N unidades vendidas" no son
   lo mismo y no se fusionan.
6. **Nombre de la asesora en el saludo.** Se revela en el audio o en el cierre.
7. **Nombre de la fanpage en el saludo.** El saludo lleva la TIENDA.
8. **Verbos médicos** (`cura`, `elimina el`, `erradica`) en el texto renderizado.

---

## 6. CONEXIÓN

```
_DIM_MERCADOS.csv ┐
_DIM_FLUJO_BOT.csv├─→ gen_flujo_bot.py ─→ PRODUCTOS/[PK]/FLUJO_LUCIDBOT.md
_DIM_PRECIOS.csv  ┘    (esta plantilla)
```

| Qué | Dueño |
|---|---|
| El texto literal, las notaciones y las prohibiciones | este archivo |
| Los bloques de juicio y sus reglas de redacción | `.claude/agents/ETAPA-5.md` |
| Las plantillas visuales de las infografías | `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md` |
| Los precios | `PRODUCTOS/_DIM_PRECIOS.csv` (manda Dropi) |
| La política de garantía y las cifras de prueba social | el operador |
| El diagnóstico de por qué no cierra y el brief de qué cambiar | `.claude/agents/ETAPA-11.md` |
| Las reglas congeladas | `Ads/_TOOLS/test_gen_flujo_bot.py` |

**Todo cambio de flujo en un producto vivo se anexa como `CAMBIO_BOT` a `PRODUCTOS/_EVENTOS.csv`
el día que se aplica.** El efecto se nota en horas (regla F), así que sin la fecha del cambio no
hay forma de saber qué lo movió.

**Cuándo diagnostica y cuándo reescribe (mapea reglas A/E de arriba a `DOCTRINA/FLUJO.json`):**
el DIAGNÓSTICO de congruencia (regla E) va en `F2.etapa-11`, en paralelo al testeo de conceptos,
y registra `DIAGNOSTICO_CONGRUENCIA` — no
bloquea F2. La REESCRITURA (`CAMBIO_BOT`) corre DESPUÉS del concepto ganador confirmado en 2 de 2
y ANTES de entrar a FASE 3 (regla A: el flujo va antes que la estructura, y F3 es CBO — la
estructura más irreversible del sistema): gate en `F3.entrada`, que exige el `CAMBIO_BOT` (o un
`EXCEPCION_CAMBIO_BOT` si el operador decide saltárselo) fechado DESPUÉS del ganador, nunca uno
viejo que sea variable de confusión.
