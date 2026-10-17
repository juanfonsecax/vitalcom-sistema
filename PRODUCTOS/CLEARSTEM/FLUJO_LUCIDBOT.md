════════════════════════════════════════════════════════════
FLUJO LUCIDBOT — CLEARSTEM | ANTI_FALSIFICACION
Guatemala | Sanarte | 2026-10-16
════════════════════════════════════════════════════════════
>> TEMPORIZADOR entre mensajes: 2-3 segundos SIEMPRE. Nunca 15 ni más.
>> Si se simula que "una asesora está llegando", máximo 5 seg SOLO en ese primer beat.
>> Un silencio largo es la ventana para que el cliente se vaya con la competencia.
>> TRATAMIENTO DE PERSONA de este flujo: voseo.
>> ANTES DE LANZAR: si el producto se importó de Superbodega, LucidBot queda DESACTIVADO
>> y el mensaje inicial no sale. Activarlo es un paso MANUAL (clase 16-ago).

>> ══ MENSAJE PRELLENADO DEL ANUNCIO — se configura a mano en Ads Manager, no en LucidBot ══
>> El anuncio Click-to-WhatsApp lleva un mensaje prellenado: el texto que el cliente manda al
>> tocar el anuncio. El MCP `ads_create_creative` no tiene campo para esto (DOCTRINA/MCP_PLAYBOOK.md
>> / skill `publicar-meta` paso 3): se configura A MANO en Ads Manager, por anuncio.
>> El enrutamiento del chat al producto es por el ID del anuncio/conjunto (integración
>> LucidBot), nunca por este texto (dato operador 23-sep): el mensaje puede cambiar libremente
>> sin romper la atribución. Nombrar el producto + su registro sanitario genera confianza y
>> sube conversaciones por click al anuncio.
>> Hola, quiero más información de CLEARSTEM con registro MSPAS

═══════════════ FICHA DEL PRODUCTO (catálogo de LucidBot) ═══════════════
>> Los 4 campos de abajo se pegan TAL CUAL en la ficha de producto de LucidBot.
>> La información del producto va ACÁ y NUNCA en las reglas (clase 16-ago).

DESCRIPCIÓN:
¿Compraste un suplemento para el acné y nunca supiste si era el original? CLEARSTEM Mindbodyskin original es el suplemento de fórmula americana que trabaja el acné hormonal desde adentro, ese que sale en la barbilla y la mandíbula y no se quita con cremas ni con jabones. El DIM apoya el equilibrio de tus hormonas, que es la raíz del problema; la cúrcuma y el glutatión ayudan a desinflamar; y el 5-HTP ayuda con el estrés que dispara los brotes. Llega sellado, con 90 cápsulas y sin hormonas añadidas. Entre la semana 2 y 3 empezás a notar cambios en tu piel, y el cambio se queda. Vegano y sin gluten.

MODO DE USO:
Solo 2 a 3 cápsulas al día, todas juntas con tu primera comida. Una sola toma: sin cremas, sin jabones especiales, sin rutinas de 6 pasos. Entre la semana 2 y 3 de uso constante empezás a notar los primeros cambios, y con los meses el resultado se asienta.

CARACTERÍSTICAS TÉCNICAS:
BENEFICIOS
- Producto original, con su sello íntegro y fórmula americana
- Apoya el equilibrio de tus hormonas desde adentro
- Ayuda a reducir los brotes de la barbilla y la mandíbula
- Ayuda a desinflamar los granos que duelen por debajo
- Ayuda a regular la grasa de la piel
- Ayuda a disminuir las manchas que dejan los brotes
- Ayuda con el estrés que dispara los brotes
- Apoya la función de tu hígado
- Sin hormonas añadidas
- Vegano y sin gluten
- Una sola toma al día: sin cremas ni rutinas
- Los primeros cambios se notan entre la semana 2 y 3
- 90 cápsulas por frasco

INGREDIENTES Y LO QUE HACE CADA UNO
- DIM: apoya el equilibrio hormonal, la raíz del acné de mandíbula
- Cúrcuma: ayuda a desinflamar los granos que duelen por debajo
- Glutatión: ayuda a desinflamar y apoya a tu hígado a limpiar
- 5-HTP: ayuda con el estrés que dispara los brotes
- Raíz de diente de león: apoya la función del hígado
- Vitamina A biodisponible: apoya la renovación de la piel
- Vitamina B5: apoya la regulación de la grasa de la piel

CONTENIDO DEL PAQUETE:
Tratamiento de ~30 días: 1 frasco original y sellado de CLEARSTEM Mindbodyskin con 90 cápsulas (a 3 cápsulas al día, un mes completo). Con 2 frascos tenés el tratamiento de ~60 días y con 3 frascos el tratamiento completo de ~90 días. Envío gratis a toda Guatemala.

═══════════════════════ MENSAJE INICIAL ═══════════════════════

ELEMENTO 1 — TEXTO · SALUDO
¡Hola! 👋 Bienvenida/o a *Sanarte*, estamos encantados de tenerte por acá. En un momento una asesora se pondrá en contacto con vos. ✨
>> FIJO. No cambia por ángulo ni por producto.
>> NO lleva el nombre de la asesora — se revela en el audio o en el cierre.
>> NO lleva el dolor del ángulo, NO lleva el nombre del producto, NO lleva ninguna pregunta.
>> Lleva la TIENDA, nunca la fanpage: el nombre de la tienda es el que el cliente ve después
>> en la guía, en las novedades y en el cobro contraentrega.

ELEMENTO 2 — VIDEO 1 · AUTORIDAD: ‹DECLARAR: video_1 — operador / Ads/MEDIA_[PK]›
>> NIVEL DE CONCIENCIA 3A del angulo ganador (conoce el producto, teme comprar): reducir friccion desde el arranque — contraentrega, garantia, prueba social.
ELEMENTO 3 — VIDEO 2 · UGC: ‹DECLARAR: video_2 — operador / Ads/MEDIA_[PK]›

INFOGRAFÍAS (2): ‹DECLARAR: lista_infografias — operador / Ads/MEDIA_[PK]›
>> Las plantillas visuales son de DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md. Acá solo se declaran.
>> Van SIN PRECIO, en 1080x1350 (4:5).
>> LO QUE MÁS MUEVE EL CIERRE VA ACÁ: muchas PROPUESTAS DE VALOR, no ingredientes sueltos.
>> Fórmula de cada una: [problema concreto del avatar] -> [qué hace el producto] -> [resultado].
>> Van DENTRO de las infografías (imagen), nunca en el texto que se pega en LucidBot — por eso
>> <<BLOQUE:propuestas_valor>> es una lista de trabajo para armar las imágenes, no un campo que
>> se copie. Una propuesta por línea, 6-8 (clase 22-ago regla D). `etapa-guardar-producto` las
>> persiste verbatim en `PRODUCTOS/[PK]/2_DATA_PRODUCTO.txt`, sección "PROPUESTAS DE VALOR"
>> (`ETAPA-GUARDAR-PRODUCTO.md`), y `gen_flujo_bot.py` las lee y cuenta SOLO de ahí, sin flag:
>> menos de 6 BLOQUEA, sin la sección queda PENDIENTE (aviso, no bloquea). `--propuestas ARCHIVO`
>> sigue existiendo como override manual de una sola corrida (probar antes de persistir).
<<BLOQUE:propuestas_valor>>
>> Dentro del bot no hay límite de compliance ni de umbral cognitivo: la prioridad es CONVERTIR.
>> ORDEN SEGÚN EL BUYER TYPE del avatar: nicho EMOCIONAL -> la prueba de transformación
>> (antes/después o momento) va PRIMERO y los ingredientes después. Nicho TÉCNICO -> los
>> ingredientes con su mecanismo van primero.
>> La 1ª lleva un TÍTULO de dolor o deseo congruente con el anuncio, nunca el nombre del
>> producto ni la palabra "BENEFICIOS": es genérica y la gente escanea.
>> La de CONFIANZA abre con "PAGÁS AL RECIBIR" y lleva el sello de 90 días de garantía junto a
>> eso: es el reductor de fricción que responde "¿y si no me funciona?".

TEXTO · TRANSICIÓN A TESTIMONIOS
A continuación te muestro lo que dicen quienes ya lo tienen en casa 👇
>> FIJO.

TESTIMONIOS (2 · fuente REAL):
>> FUENTE: REAL. Los 2 testimonios son capturas reales de clientas de WhatsApp que ya convierten (decisión del operador 25-jul): se usan tal cual, NO se redactan ni se retocan. Cubren las 2 objeciones que más pesan en este ángulo: "¿es original? ¿me va a llegar?" y "¿funciona? ¿por qué más de 1?". No se pega el número de teléfono de las clientas en ningún lado.

TESTIMONIO 1 · RECEPCIÓN + ORIGINAL (captura real de la clienta de recompra)
Globo principal: tenía dudas pero me di cuenta que es el original y necesito otro porque he visto resultados
Imagen dentro de la captura: la foto o video de los dos frascos que ella misma mandó.
>> Va primero: ataca de frente la objeción crítica de este ángulo (el miedo a la copia) y de paso muestra RECOMPRA, que es la prueba más fuerte de que funciona.

TESTIMONIO 2 · RESULTADO + CANTIDAD (captura real de la clienta de los 3 frascos)
Globo 1: hace 3 semanas me llegaron los 3 cabal jaja, yo dudé si pedir 1 o los 3 pero qué bueno que pedí los 3
Imagen dentro de la captura: la foto de su piel.
Globo 2: ya voy en la semana 3 y carita ya se ve diferente… hasta mi hermana me dijo que le guarde uno porque como que es de familia
>> Resuelve "¿funciona?" y "¿por qué llevar más de 1?" en una sola captura, con timeline creíble (semana 3).

>> RESERVA, NO CUENTA EN n_testimonios (el CSV dice 2). Si baja la conversación, sumar como TESTIMONIO 3 (comentarios de Facebook, objeción "¿a otros les sirvió de verdad?") y cambiar n_testimonios a 3 en _DIM_FLUJO_BOT.csv. Son textos REDACTADOS: si se activan, fuente_testimonios deja de ser REAL puro y hay que declararlo.
>> Comentario 1 (María José Xoyón): a mi me lo recomendo mi dermatologa cuando le dije q ya no queria mas antibioticos. voy en el mes y medio y la diferencia se nota
>> Comentario 2 (Andrea Súchite): yo tenia acne desde los 19 y ya tengo 31. probe de todo. esto es lo unico q me ha aguantado sin q vuelva peor al dejarlo
>> Comentario 3 (Kevin Morales): sirve para hombres? tengo en la mandibula y la espalda
>> Respuesta (Diana Ruiz): si va, mi hermano lo esta tomando. es hormonal igual
>> Comentario 4 sugerido para este ángulo (Lucía Pérez): yo vi q habia copias en tiktok y me dio miedo pedir. me llego sellado y es el original, voy en la semana 3 y ya se nota

AUDIO (45-55 seg):
Hola, claro que sí, te cuento. Con lo viral que se hizo CLEARSTEM salieron muchas copias, así que lo primero: lo que te llega es el original, fórmula americana, 90 cápsulas y su sello íntegro. Es para el acné hormonal, ese de la barbilla y la mandíbula que no se va con cremas, porque trabaja desde adentro: el DIM apoya el equilibrio de tus hormonas, que es la raíz del problema, y la cúrcuma con glutatión ayudan a desinflamar. Las copias no traen la fórmula completa, y en un suplemento hormonal la dosis lo es todo. Vas a notar cambios en tu piel entre la semana 2 y 3, y el cambio se queda. Olvidate de volver a gastar en algo que no funciona. Imaginate salir en las fotos sin pensar en cómo se ve tu piel: es la mejor decisión que podés tomar por vos. Lleva DIM, vitamina A, B5, cúrcuma, diente de león, 5-HTP y glutatión.
>> Va DIRECTO después del último testimonio. NO hay texto de puente ni presentación previa.
>> SIN PRECIO y SIN contraentrega. La asesora se presenta DENTRO del audio.

ELEMENTO FINAL — CIERRE → PREGUNTA DE UBICACIÓN
Hola, soy Laura, estaré atendiéndote el día de hoy 😊 Contame, ¿desde qué municipio y departamento nos escribís?
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

Me alegra que estés dando el paso de cuidar tu piel desde adentro — es una gran decisión por vos.

Confirmo que tenemos cobertura completa ahí, con envíos a toda Guatemala y *pago contraentrega*. Las entregas tardan de 2 a 5 días hábiles. 🚚

¿Deseás conocer nuestros precios?
>> El refuerzo de este turno VALIDA la decisión del cliente. Una línea, sin producto y sin precio.
>> "¿Deseás conocer nuestros precios?" es el 2º sí: nadie dice no a esta pregunta.

INTERACCIÓN 2 — PRESENTACIÓN DE PRECIOS
¡Claro! 😊

Ya sabés que el acné hormonal *no se quita con cremas ni con jabones, y menos con una imitación barata* — vuelve siempre al mismo lugar, y una copia sin la fórmula completa te cuesta meses y plata.

Y lo que más pesa no es el precio: es *que te estafen otra vez, perder meses más con la piel igual y no volver a confiar en nada.*

CLEARSTEM actúa *desde la raíz* con DIM para tus hormonas y cúrcuma con glutatión para desinflamar. Por eso ya son *más de 12,000 personas* con resultados reales.

Cuando trabajás con el original *desde la raíz, el cambio sí se mantiene.* ✨

OFERTAS HASTA AGOTAR

1️⃣ Tratamiento 1 mes (1 frasco) → Q198 + 🛻 ENVÍO TOTALMENTE GRATIS

2️⃣ Tratamiento 2 meses (2 frascos) → Q289 + 🎁 ENVÍO TOTALMENTE GRATIS
   OFERTA IRRESISTIBLE 🥰👇

3️⃣ Tratamiento 3 meses (3 frascos) → Q389 + 🎁🎁 ENVÍO TOTALMENTE GRATIS
   LA MÁS ELEGIDA ⭐ (tratamiento completo) — y lo mejor, pagás al recibir 😊

Los cambios llegan entre la semana 2 y 3 y se asientan con los meses: por eso el de 3 es el que más piden, y con él tenés tu tratamiento completo del original sin volver a buscarlo.

¿Confirmame tu municipio y departamento? 😊
>> Es el turno de refuerzo MÁS FUERTE y el único que vuelve a hablar del producto.
>> Va CORTO: el cliente ya leyó todo lo de arriba. No re-explicar, solo empujar al paso siguiente.
>> Una sola presentación de precios. Sin filtro "rápido o normal".
>> Confirmar la ubicación una 2ª vez es el 3er sí: ya la dijo, pero repetirla avanza el cierre.
>> La escalera se deriva de _DIM_PRECIOS.csv. Ningún precio se escribe a mano acá.

INTERACCIÓN 3 — PEDIDO DE DATOS
¡Perfecto! Tranqui, no arriesgás nada: pagás solo cuando tengas el producto en tus manos, y llevás *90 días de garantía*. 🙌

Antes de continuar con la compra asegurate de que vas a permanecer en casa los próximos 5 días, o que algún familiar o amigo te reciba el producto en la dirección que indicarás.

En caso de no ser así, podés solicitar que tu envío se haga a la agencia principal de GINTACOM y FORZA de tu municipio.

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
- Producto: CLEARSTEM — {OPCIÓN}
- Total a pagar: Q{TOTAL} al recibir

¿Confirmás que los datos están correctos?
>> FIJO y universal.

INTERACCIÓN 5 — CIERRE FINAL
¡Listo, {NOMBRE}! Tu pedido fue tomado exitosamente.

Tu CLEARSTEM está en camino. La entrega tarda de 2 a 5 días hábiles en {MUNICIPIO}.

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
Ese es el testimonio de una de nuestras últimas clientas 💜

La mayoría se lleva el de 3 porque la piel empieza a cambiar entre la semana 2 y 3 y el resultado se asienta con los meses; así tenés tu tratamiento completo del original sin tener que volver a buscarlo.

¿Te aparto el de 1 mes (Q198) o el de 3 meses (Q389)?
>> Los precios del M2 son LITERALES: este bloque se inserta después de resolver las variables de la plantilla, así que no admite variables con llaves dobles. Salen de _DIM_PRECIOS.csv: 1x Q198 y 3x Q389.01 (la escalera del flujo redondea a Q389). Si _DIM_PRECIOS cambia, hay que actualizar este bloque.
>> AUDIO TESTIMONIO DEL M2 (50-60 seg, voz de una CLIENTA, no de la asesora; hay que grabarlo o clonarlo en Lucid). Sin precio, sin transportadora, sin mencionar el bot ni el anuncio. Hablarlo imperfecto: muletillas chapinas, una frase que se corrige, ritmo desigual. A la tienda se le habla de "ustedes". Guion sugerido:
>> "Hola, buenas, quería agradecerles por el producto, y por el detalle también, la verdad. Me llegó bien, sellado, original original, porque yo andaba con miedo de que fuera falso, uno ya ni sabe, ¿verdad? Ya llevo como tres semanas tomándolo y quedé súper satisfecha, o sea, la piel ya no se me ve tan inflamada, antes me levantaba y era lo primero que revisaba en el espejo, y ahorita ya no. Hasta mi esposo me dice que se me ve distinta la cara. Se los recomiendo bastante, y les recomiendo a ustedes también, la tienda, porque cumplieron. Y no es el primer producto que les compro, ya me habían llegado otros y todo bien. Mi hermana también les compra. Así que muy recomendados de verdad."
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
P: ¿Es el original? ¿Cómo sé que no es una copia?
R: Sí, es CLEARSTEM Mindbodyskin original, de fórmula americana, frasco de 90 cápsulas y con su sello íntegro. Lo recibís sellado y lo revisás antes de pagar: pagás solo cuando lo tenés en tus manos. 🙌

P: ¿Me va a llegar? ¿Es seguro comprar?
R: Sí. Enviamos a toda Guatemala por GINTACOM y FORZA y pagás hasta que el producto está en tus manos, así que no arriesgás nada. El envío es gratis y tarda de 2 a 5 días hábiles.

P: ¿De verdad funciona?
R: La mayoría empieza a notar cambios entre la semana 2 y 3 de uso constante, y el resultado se asienta con los meses. Por eso te mostramos testimonios reales de clientas, incluida una que ya nos volvió a comprar.

P: ¿Y si no me funciona?
R: Tenés 90 días de garantía. Probás con tranquilidad: tu inversión está protegida.

P: ¿Cómo se toma?
R: De 2 a 3 cápsulas al día, juntas, con tu primera comida. Una sola toma, sin cremas ni rutinas. Súper fácil.

P: ¿Cuándo voy a ver resultados?
R: Entre la semana 2 y 3 empezás a notar cambios, siempre con uso diario y constante. Ojo: muchas personas lo dejan antes de la semana 3 y por eso creen que no funcionó. La constancia es lo que cuenta.

P: ¿Tiene hormonas? ¿Sirve si dejé los anticonceptivos o tengo SOP o resistencia a la insulina?
R: No aporta hormonas: apoya el equilibrio de las tuyas con DIM, un compuesto que viene de vegetales como el brócoli. Muchas clientas con SOP o que dejaron las pastillas lo usan porque apoya lo que está detrás del acné, la regla desordenada y el vello. Acompaña tu tratamiento, no lo reemplaza; si tomás medicación, estás embarazada o dando pecho, consultalo primero con tu doctora.

P: ¿Sirve para hombres?
R: Sí. El acné hormonal de la mandíbula y la espalda funciona igual en hombres, y CLEARSTEM apoya el equilibrio hormonal en ambos casos. Muchos de nuestros clientes son hombres. 😊

P: ¿Por qué me conviene llevar más de 1?
R: Porque el acné hormonal necesita constancia: el cambio se nota desde la semana 2 y 3 y se asienta con los meses. Con 3 frascos tenés el tratamiento completo del original y te sale mucho más conveniente por frasco, con envío gratis.

P: ¿Hacen descuento?
R: El precio de 1 unidad no lo puedo bajar porque ya es el mejor del mercado para un producto original. Pero llevando 2 o 3 te sale mucho más conveniente por frasco y el envío es gratis.
P: ¿Ya salió mi pedido?
R: Lo despachamos y te llega en 2 a 5 días hábiles. Cualquier cosa me escribís y te aviso. 😊

P: ¿Cómo verifico que es el original cuando me llegue?
R: Revisá que el frasco venga con su sello íntegro, que diga CLEARSTEM Mindbodyskin y que traiga 90 cápsulas. Si algo no te cuadra, avisame antes de pagar y lo revisamos.

P: ¿Cómo lo tomo para tener mejor resultado?
R: De 2 a 3 cápsulas al día con tu primera comida, todos los días y sin saltarte. La constancia es lo que más importa.

P: ¿En cuánto tiempo voy a notar cambios?
R: Entre la semana 2 y 3 de uso constante. El resultado se asienta con los meses, así que no lo dejes antes de la semana 3.

P: Tengo una duda con la entrega o quiero pedir otra vez.
R: Pasame tu nombre y te rastreo el pedido de una. Y si querés pedir de nuevo, escribime y te lo dejo listo. 💜
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

[IMPORTANTE: Si el cliente indicó que reclama en agencia u oficina, ese dato reemplaza la dirección. No preguntar dirección de casa ni barrio. Indicale que su pedido será enviado a la agencia principal de GINTACOM y FORZA de su municipio.]

[IMPORTANTE: Si el cliente escribió una palabra mal, corregila sin pedirle que la corrija. Hacelo de forma natural, sin hacer notar el error.]

[IMPORTANTE: NUNCA insistir en la misma pregunta más de 2 veces, y CAMBIÁ EL ENFOQUE en el 2do intento en vez de repetir igual. Ej. ubicación — 1ra vez: "Decime tu municipio para confirmarte cobertura." 2da vez: "Con tu municipio te confirmo si te llega con pago contraentrega." Después, cambiar de tema.]

[IMPORTANTE: Si el cliente eligió la opción de 1 unidad, persuadilo de llevar 2 o más por el mayor ahorro que representa.]

[IMPORTANTE: Si el cliente solicita descuento por una sola unidad, NO bajar el precio de 1 unidad. Respondé: "El precio de 1 unidad no lo puedo bajar porque ya es el mejor del mercado. Pero si llevás 2, te sale mucho más conveniente y el envío es totalmente gratis."]

[IMPORTANTE: Si el cliente pregunta "¿hasta cuándo está la promoción?" respondé: "Tenemos ese precio hasta agotar existencias."]

[IMPORTANTE: Si el cliente dice que hará el pedido después, respondé solamente: "¡Súper, no hay problema! Estaremos atentos a cuando desees realizar tu pedido."]

[IMPORTANTE: Si el cliente pregunta por ubicación o tienda física: "Nuestro centro de distribución trabaja solo por envíos y no tenemos atención al público. Hacemos entregas a casi toda Guatemala por GINTACOM y FORZA, según cobertura."]

[IMPORTANTE: Si el cliente envía GIFs, stickers o imágenes, respondé de forma amable sin describir el contenido visual.]

[IMPORTANTE: Si el cliente solicita audios, respondé: "En este momento no puedo enviarte audios pues el micrófono del celular está fallando."]

[IMPORTANTE: Una vez cerrada y confirmada la venta, solo respondé preguntas del cliente. No continuás intentando vender.]

[IMPORTANTE: TODO el texto usa voseo. La confirmación de dirección usa "municipio y departamento", no "ciudad" a secas.]

[IMPORTANTE: El audio NUNCA menciona precio.]

>> REGLAS CONDICIONALES — agregar SOLO las que apliquen a este producto (salen de etapa-1b):
>>   · Producto sensible o íntimo: "Tu pedido va en empaque 100% discreto, sin indicar el
>>     contenido por fuera."
>>   · Restricciones propias: contraindicaciones, edad mínima, no apto en embarazo o lactancia,
>>     sabor, etc.
>>   · Precio al por mayor (6+ unidades), si el operador lo autoriza y declaró el precio.