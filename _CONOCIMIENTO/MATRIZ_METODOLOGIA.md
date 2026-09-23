# MATRIZ DE METODOLOGÍA — LO QUE DICEN LOS MENTORES

> **Qué es este archivo.** El índice único y fechado de la **doctrina externa**: todo lo que
> los mentores enseñan, con su fuente, su cifra original, su estado en nuestro sistema y el
> archivo que la implementa. Es la capa de **METODOLOGÍA**, no la capa de **SISTEMA**.
>
> **Qué NO es.** No es un archivo de reglas operativas. Ninguna etapa lo lee para ejecutar.
> Si querés saber *qué hace el sistema*, leé el archivo dueño (columna DUEÑO). Si querés saber
> *de dónde salió esa regla y qué tan reciente es la fuente*, leés acá.
>
> **Por qué existe.** Las clases se acumulan y se contradicen entre sí y contra nuestra data.
> Sin un registro fechado, cada clase nueva parece "la verdad" y se reescribe el sistema encima
> de decisiones que ya se habían tomado con evidencia. Esta matriz hace visible el choque en vez
> de aplanarlo.
>
> Última actualización: **2026-09-02** · Fuentes indexadas: **7 bloques** · Afirmaciones: **71**

---

## 0. REGLA DE PRECEDENCIA — cómo se resuelve un choque

```
NIVEL 4  DATA PROPIA (_APRENDIZAJES.csv · auditorías · CSV)     <- manda sobre todo
NIVEL 3  Clase 22-ago-2026 (Calet)                              <- la más reciente
NIVEL 2  Clase 16-ago-2026 (Calet + Joaquín)
NIVEL 1  Clases 1-22 del curso base (Mercy · Joaquín · Camilo · Pipe)
NIVEL 0  Currículo escrito SKOOL (Mercy Pardo, módulos 1-6)     <- la base
```

**Las tres reglas de resolución:**

1. **Entre mentores, gana el más reciente.** Una clase de agosto sobre una de junio, sin discusión:
   Meta cambia y la clase vieja describe una plataforma que ya no existe.
2. **Contra la data propia, gana la data propia — pero solo con muestra.** Un aprendizaje `APR-xxx`
   con n suficiente vence a cualquier mentor. Un aprendizaje de una sola observación **no**: ahí
   manda el mentor más reciente y el aprendizaje se marca como hipótesis a medir.
3. **Nunca se copia una CIFRA, se copia el MÉTODO.** Los mentores operan en Colombia, en pesos,
   con otro ticket y otro CPM. Toda cifra entra a esta matriz normalizada y marcada
   `NO-PORTAR` si depende del mercado de origen. Ver §4.

> **Corolario que hay que decir en voz alta:** que una afirmación esté acá **no significa que esté
> implementada**. La columna ESTADO es la que manda. `ADOPTADO` = está escrito en el archivo dueño.
> Todo lo demás es doctrina que todavía no es sistema.

**Vocabulario de la columna ESTADO:**

| ESTADO | Significa |
|---|---|
| `ADOPTADO` | Está escrito en el archivo dueño y las etapas lo ejecutan |
| `ADAPTADO` | Se tomó el método pero con parámetros propios (la cifra del mentor no aplica) |
| `PENDIENTE` | Decidido implementar, todavía no escrito. Lleva el bloque que lo va a escribir |
| `RECHAZADO` | Medido contra data propia y descartado. Lleva el `APR-xxx` que lo mata |
| `CONGELADO` | Correcto en teoría, bloqueado por una precondición que todavía no se cumple |
| `NO-PORTAR` | Cifra o práctica atada al mercado colombiano; no se traduce a Guatemala |
| `EN TEST` | Hay un experimento abierto en `_TESTEOS.csv` con su `test_id` |
| `SIN-EVALUAR` | Registrado, nadie lo miró todavía |

---

## 1. FUENTES INDEXADAS — ordenadas por fecha

> `VITALCOM_CLASES/` = `C:\Users\juand\Documents\VITALCOM_CLASES\` — fuera del repo (T9,
> 22-sep-2026: las clases salieron de `_CONOCIMIENTO/Finales/`, que ya no existe).

| ID | Fuente | Instructor | Fecha | Ubicación |
|---|---|---|---|---|
| **F0** | Currículo oficial SKOOL (módulos 1,2,3,5,6) | Mercy Pardo | sin fecha (base) | `VITALCOM_CLASES/SKOOL CLASES 2026 …txt` |
| **F1** | Clases 1-22 del curso | Mercy · Joaquín · Camilo · Pipe | sin fecha individual · ingesta 2026-06-15 | `VITALCOM_CLASES/Clase N - ….txt` |
| **F2** | Herramienta validación de productos | Mercy Pardo | sin fecha | `VITALCOM_CLASES/Herramienta - Validacion …txt` |
| **F3** | PDF Creativos que Venden — Prompt Maestro | Joaquín | sin fecha | `VITALCOM_CLASES/PDF Creativos …txt` |
| **F4** | **Clase 16-ago-2026** | Calet (+ Joaquín) | **2026-08-16** | `VITALCOM_CLASES/Clase 2026-08-16 …txt` |
| **F5** | **Clase 22-ago-2026** | Calet | **2026-08-22** | `VITALCOM_CLASES/Clase 2026-08-22 …txt` |
| **F6** | DATA PROPIA | — | continua | `PRODUCTOS/_APRENDIZAJES.csv` · `_AUDITORIAS/` |

> ⚠️ **Hallazgo sobre el orden (2026-09-02).** Las 22 clases del curso base **no están ordenadas
> por fecha**: están ordenadas por número de currículo y todas se ingirieron el mismo día. No
> tienen fecha adentro. Por eso la precedencia entre ellas **no se puede resolver por recencia** —
> se resuelve por instructor y por tema, y cuando dos clases del curso base se contradicen, el
> choque se registra en §3 y lo rompe la data propia, no la antigüedad.
>
> Las únicas dos fuentes con fecha real son F4 y F5. **A partir de ahora toda clase nueva entra
> con fecha en el nombre del archivo** (ver §6).

---

## 2. LA MATRIZ

### A · ESTRUCTURA DE CAMPAÑA

| ID | Afirmación | Fuente | Cifra original → normalizada | ESTADO | Dueño |
|---|---|---|---|---|---|
| **M-A01** | "Cada anuncio es un vendedor": más anuncios = más vendedores en la calle | F1·C6 Mercy | — | `ADOPTADO` | `ETAPA-6.md` |
| **M-A02** | Estructura de testeo **1×3×2** (1 campaña · 3 conjuntos · 2 anuncios duplicados), ABO | F1·C6 Mercy | 6.000 COP/conjunto → $1.48 | `ADAPTADO` — el sistema corre 1×6×2 a $2.99 | `ETAPA-6.md` |
| **M-A03** | 1 campaña · 1 conjunto · **7-10 anuncios distintos**; apagar los que no rinden | F1·C11 Camilo | — | `ADAPTADO` — es el antecedente directo del 1-1-5 | `ETAPA-6.md` |
| **M-A04** | Duplicar el anuncio **dentro** del conjunto baja el CPA ("darle opciones a Meta") | F1·C6 Mercy | — | `ADOPTADO` · variante duplicado-vs-2-conceptos **en prueba** desde 31-jul | `CLAUDE.md` regla 9 |
| **M-A05** | Cuando Meta "se enamora" de un anuncio → duplicar el **conjunto completo** | F1·C11 Camilo | — | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |
| **M-A06** | **Testeo = 1-1-5 ABO** (1 campaña · 1 conjunto · 5 anuncios) | **F4** | 16.000-25.000 COP/día → **$3.95-$6.17** · Q30-47 | `ADOPTADO` 02-sep — en FASE 2 (conceptos), **no** en el testeo de ángulos | `ETAPA-6.md` |
| **M-A07** | No se corre UNA sola 1-1-5: se corren **2-3 en paralelo** | **F4** | — | `ADOPTADO` 02-sep — son las campañas A, B y C | `ETAPA-6.md` |
| **M-A08** | ABO en testeo porque **reparte entre los 5 anuncios**; CBO corona uno solo | F4·F5 | — | `ADOPTADO` 02-sep **con guardarraíl `SIN_ENTREGA`** — `ETAPA-6` documenta lo contrario (Meta concentra igual). Ver choque C-09 | `ETAPA-6.md` |
| **M-A09** | **1-2-5**: los mismos 10 creativos corriendo dos veces en estructuras independientes | **F5** | 50.000 COP → **$12.35** | `ADOPTADO` 02-sep — es el mecanismo de **replicación**: gana en 2 de 2 | `ETAPA-6.md` |
| **M-A10** | **Escalado = 1-1-7 CBO**: el creativo validado ×7 (Post ID o subido de cero) | **F5** | 60.000-72.000 COP/día → **$14.8-$17.8** · Q113-136 | `ADOPTADO` 02-sep — es la estructura canónica de FASE 3 | `ETAPA-6.md` |
| **M-A11** | **1-7-7** masivo: 7 conjuntos × (anuncio + copia) → duplicar conjuntos → multiplicar campaña ×2..×6 | **F5** | 7.000 COP/conjunto → **$1.73** | `NO-PORTAR` hoy — 40+ conjuntos está fuera de escala del portafolio | — |
| **M-A12** | Duplicar la campaña ganadora **al presupuesto INICIAL**, nunca al actual | **F5** | — | `ADOPTADO` 02-sep | `ESCALADO_PLAYBOOK.md` |
| **M-A13** | En escalado **no apagar** anuncios: Meta ya optimiza bien | **F5** | — | `PENDIENTE` parcial — cierto a nivel conjunto (APR-055), falso a nivel cuenta/banda | `ETAPA-8.md` |
| **M-A14** | El primer día, **cada conjunto un ángulo distinto** | F1·C15 Joaquín | — | `ADOPTADO` — es la FASE 1 | `ETAPA-6.md` |
| **M-A15** | Un ángulo + un concepto por conjunto; no repetir ninguno dentro de la campaña de testeo | F1·C4 Joaquín | — | `ADOPTADO` | `CLAUDE.md` (ÁNGULO vs CONCEPTO) |
| **M-A16** | Lanzar la misma campaña en **4 cuentas a la vez** el primer día, misma fanpage | F1·C15 Joaquín | — | `ADAPTADO` — el sistema lo usa en escalado, no en día 1 | `ESCALADO_PLAYBOOK.md` §3.6 |

### B · PRESUPUESTO Y ESCALADO

| ID | Afirmación | Fuente | Cifra original → normalizada | ESTADO | Dueño |
|---|---|---|---|---|---|
| **M-B01** | Escalar por **VOLUMEN de anuncios**, no por presupuesto | F1·C6·C7 | — | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |
| **M-B02** | Surfing **+20 % una vez al día, solo hasta las 9-10 AM**; más tarde desoptimiza | F1·C11 Camilo | — | `ADOPTADO` | `CALENDARIO_ESCALADO.md` gate 3 |
| **M-B03** | Surfing **+20 % VARIAS veces al día**, hasta las 2-3 PM, con gate de CPA bajo | **F5** | — | `CONGELADO` — choca con M-B02 (la recencia lo favorece) pero APR-057 dice que el techo no se rompe con cadencia. Se descongela cuando la fábrica esté corriendo. Ver C-02 | `CALENDARIO_ESCALADO.md` |
| **M-B04** | El presupuesto **solo cambia la velocidad** del resultado, no el resultado | **F5** | — | `SIN-EVALUAR` — contradicho parcialmente por APR-057 (más gasto compró CPA, no ventas) | — |
| **M-B05** | El presupuesto **no se relaciona con el ticket** del producto | F1·C6 Mercy | 6.000 COP igual para un producto de 190.000 | `ADOPTADO` | `ETAPA-1.md` |
| **M-B06** | **CPA semanal/ponderado, nunca diario**; no apagar por un pico de un día | F1·C8·C11 | — | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §8 |
| **M-B07** | Techo para dejar de subir presupuesto: CPA sobre 10.000 COP → frenar | **F5** | 10.000 COP → **$2.47** | `NO-PORTAR` — su techo depende de su ticket. El sistema usa **Break-Even propio** por producto | `ETAPA-1.md` · `CONTABILIDAD.md` |
| **M-B08** | Campañas de hasta 500.000 COP/día | **F5** | → **$123/día** · Q940 | `NO-PORTAR` hoy — techo demostrado del portafolio entero: **Q597/día** (APR-057) | — |
| **M-B09** | Cuando la tendencia de 7 días sube el CPA, **matar la campaña y relanzar el CREATIVO en otra cuenta** — no la campaña | **F5** | — | `ADOPTADO` 02-sep — §3 del playbook | `ESCALADO_PLAYBOOK.md` |
| **M-B10** | Escalado **progresivo** (validar antes de agresivo) | F1·C15 Joaquín | caso Sandra: 16.000 → 28.000 al escalar de golpe | `ADOPTADO` | `CALENDARIO_ESCALADO.md` |
| **M-B11** | "Nosotros no testeamos, vendemos": salir a vender desde el día 1 con producto y ángulo ya validados | F1·C6·C8 Mercy | — | `RECHAZADO` para nuestro contexto — choca con M-B10 y con todo el diseño de FASE 1. Ver C-08 | — |
| **M-B12** | El **flujo de caja** es el límite real del escalado (retorno a 4-7 días) | F1·C8 | — | `ADOPTADO` | `CONTABILIDAD.md` |

### C · OBJETIVO DE CAMPAÑA Y COMPORTAMIENTO DE META

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-C01** | **Tráfico** es el objetivo favorito y SÍ vende con un embudo fuerte de WhatsApp | F1·C6 Mercy | `ADOPTADO` (hoy es el default: `OUTCOME_TRAFFIC`) | `MCP_PLAYBOOK.md` |
| **M-C02** | Ventas = público más calificado pero **CPA más alto**; Interacción = muchos mensajes y pocas ventas | F1·C11 Camilo | `SIN-EVALUAR` — contradicho por M-C03 | — |
| **M-C03** | **Objetivo Ventas (maximizar conversaciones) rinde mejor que Tráfico.** Tráfico optimiza por tráfico: trae 1.000 personas mal calificadas y a Meta le parece bien | **F5** | `EN TEST` — **T02** abierto en `_TESTEOS.csv` el 02-sep (estado PROPUESTO: falta que el operador fije producto y fecha). Ver C-01 | `ETAPA-6.md` · `_TESTEOS.csv` |
| **M-C04** | Probar los 3 objetivos, en cuentas distintas: cada cuenta se acostumbra a uno | F1·C11 · F5 | `EN TEST` — cae dentro de T02 | `_TESTEOS.csv` |
| **M-C05** | **No seguir NUNCA las recomendaciones de Meta** (apagar conjuntos, compartir presupuesto) | F1·C6 Mercy | `ADOPTADO` | `ETAPA-6.md` |
| **M-C06** | Meta funciona por **CONFIANZA**: muchos movimientos de golpe en una cuenta joven → limitación o pérdida del perfil. Hay que subir gradualmente | **F5** | `ADOPTADO` 02-sep — §3 del playbook · R3F-11 | `ESCALADO_PLAYBOOK.md` |
| **M-C07** | **El Post ID ya no se puede extraer en campañas de objetivo Ventas** (los posts se volvieron dinámicos). Workaround: duplicar en campaña NUEVA, esperar a que pase revisión, y ahí sacar el Post ID. Tráfico e Interacción sí lo siguen dando | **F5** | `ADOPTADO` 02-sep como advertencia acoplada a C-01 — §3.5 del playbook · R3F-12 | `ESCALADO_PLAYBOOK.md` §3.5 |
| **M-C08** | Lanzar una campaña de testeo **baja el rendimiento de las campañas vivas ese mismo día**; se recupera solo al día siguiente. **No apagar nada** | **F5** | `ADOPTADO` 02-sep — R3F-10 | `ETAPA-7.md` |
| **M-C09** | **Baneo silencioso**: Meta no banea, sube el CPM por malas prácticas acumuladas | F1·C4 | `ADOPTADO` | `Ads/_TOOLS/LAVADO.md` |

### D · CREATIVO Y CONCEPTOS

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-D01** | **"EL CREATIVO ES LA NUEVA SEGMENTACIÓN"** (Andrómeda): Meta lee el creativo, no usa intereses | F1·C19·C4 Joaquín | `ADOPTADO` | `PLANTILLAS_ADS.md` |
| **M-D02** | **Las iteraciones murieron, los conceptos reinan**: cambiar título/color/fuente ya no funciona | F1·C2 Joaquín | `ADOPTADO` | `_CATALOGO_CONCEPTOS.md` |
| **M-D03** | La **tipografía es irrelevante** frente al ángulo y la propuesta de valor | **F5** | `ADOPTADO` (refuerza M-D02) | `PLANTILLAS_ADS.md` |
| **M-D04** | **Banco de 500 marcas USA validadas** → Ad Library → swipe de conceptos → adaptar el producto propio con IA (**10 conceptos en un prompt, ~3 minutos**) | **F4** | `ADOPTADO` 02-sep — banco propio (111 piezas GT → 22 blueprints) **+ la línea de producción que faltaba** (`etapa-9`) y el lector que cierra el loop (`etapa-10`) | `Ads/_SWIPE/_BLUEPRINTS/` · skill `generar-conceptos` |
| **M-D05** | **Mantener el ÁNGULO validado y variar el CONCEPTO.** El ángulo es el qué duele; el concepto es el cómo se muestra | F4·F5 | `ADOPTADO` | `CLAUDE.md` (ÁNGULO vs CONCEPTO) |
| **M-D06** | Del **video ganador** se extraen los 3-4 ángulos que menciona su audio → se convierten en 3-4 imágenes | **F4** | `ADOPTADO` 02-sep — modo `DESDE_VIDEO` de `etapa-9` | `ETAPA-0.md` · `ETAPA-4.md` |
| **M-D07** | **Frecuencia 1.9+ = fatiga creativa**, hora de renovar | F1·C4 | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §8 |
| **M-D08** | Renovar creativos **en campañas nuevas**: cambiar el creativo de una campaña activa reinicia el aprendizaje | F1·C14 | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |
| **M-D09** | Diversificar conceptos = llegar a públicos distintos. **8-12 conceptos por campaña** | F1·C7·C19 | `ADOPTADO` — y desde el 02-sep con línea de producción: `etapa-9` produce ≥6/día y audita atascos | `ETAPA-6.md` |
| **M-D10** | El producto **grande y protagonista**; texto legible para un avatar de 55 años | F1·C14·C19 | `ADOPTADO` | `PLANTILLAS_ADS.md` |
| **M-D11** | **Títulos de 2-3 palabras**: la gente no lee | F1·C14 | `ADOPTADO` | `COPYWRITING_ADS.md` (título ≤27) |
| **M-D12** | Estructura del anuncio ganador: **marca → hook → cuerpo/beneficios → CTA → prueba social → oferta** | F1·C19 | `ADOPTADO` | `PLANTILLAS_ADS.md` |
| **M-D13** | **Umbral cognitivo**: no saturar la imagen, el cerebro no procesa todo de golpe. 6-8 propuestas de valor | F1·C22 | `ADOPTADO` | `PLANTILLAS_ADS.md` |
| **M-D14** | Meter **muchas** propuestas de valor en la imagen: "tantos beneficios que el cliente diga *este es el producto perfecto*" | **F5** | `SIN-EVALUAR` — **tensión directa con M-D13**. Es exactamente lo que mide el test T01 (ligera vs densa). Ver C-06 | `_TESTEOS.csv` T01 |
| **M-D15** | El creativo que a vos no te gusta suele ser el que más vende | F1·C14 Pipe | `ADOPTADO` | `PLANTILLAS_ADS.md` |
| **M-D16** | **Sin precio en el anuncio**: enfocarse en el ángulo permite vender más caro y filtra curiosos | **F5** | `SIN-EVALUAR` — hoy el sistema permite precio en máx. 3 de 6 copies | `COPYWRITING_ADS.md` |
| **M-D17** | Las **IMÁGENES escalan tan bien como los videos** | F1·C19 | `ADOPTADO` | `PLANTILLAS_ADS.md` (DOCTRINA DE CREATIVOS) |
| **M-D18** | Palabras que banean: "logra", "elimina", "sobrepeso", "transforma en X días" | F1·C14 | `ADOPTADO` | `PLANTILLAS_ADS.md` (compliance) |

### E · ÁNGULOS

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-E01** | **Se queman los ÁNGULOS, no los productos**; cambiar de ángulo revive un producto | F1·C8·C19 | `ADOPTADO` | `ETAPA-2.md` |
| **M-E02** | Todo ángulo se relaciona con **deseo + dolor + emoción**; si no toca uno de los tres, no funciona | F1·C2 | `ADOPTADO` | `ETAPA-2.md` |
| **M-E03** | Ángulo **directo** convierte 25 % contra 4 % del genérico ("ciática" vs "dolores musculares") | F1·C4 | `ADOPTADO` | `ETAPA-2.md` |
| **M-E04** | Buscar el ángulo que **nadie está tocando**: vuelve nuevo un producto viejo (el magnesio) | F1·C2 · **F5** | `ADOPTADO` | `ETAPA-1B.md` (voz del cliente) |
| **M-E05** | Los **productos saturados son mejores**: ya hay mercado, la diferencia está en el ángulo | F1·C4 | `ADOPTADO` | `ETAPA-PRODUCTO.md` |
| **M-E06** | **La OFERTA es un ángulo de venta también** (el 3×2, el multiplicador) | **F5** | `ADOPTADO` 02-sep — regla nueva en `ETAPA-2.md`; se registra como `angulo_key` propio | `ETAPA-2.md` · `_CATALOGO_CONCEPTOS.md` |
| **M-E07** | El **primer día se busca DATA, no ventas** | F1·C2·C15 | `ADOPTADO` | `CALENDARIO_ESCALADO.md` |
| **M-E08** | Identificar el ángulo es lo difícil; con el ángulo definido, las variaciones de concepto son infinitas | F1·C19 | `ADOPTADO` | `CLAUDE.md` |

### F · FLUJO DE VENTA Y CIERRE

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-F01** | **"Primero el flujo, después la estructura."** Con un buen cierre cualquier estructura vende; con mal cierre, ninguna. Umbral: **15-20 %** | **F4·F5** | `ADOPTADO` 02-sep — **dueño asignado.** El sistema sigue reprobando (**8.6 %** sobre la serie completa 17-jul→01-sep; 8.2 % en la ventana 17-20 ago), pero ya hay etapa que lo mide y lo ataca. Ver C-10 | **`ETAPA-11.md`** |
| **M-F02** | Optimizar el flujo = **convertir más sin gastar más** en publicidad (10 % → 15-22 %) | F1·C22 | `ADOPTADO` 02-sep — **ya tiene ejecutor**: `etapa-11` mide el cierre y entrega el brief; `etapa-5` redacta | **`ETAPA-11.md`** + `ETAPA-5.md` |
| **M-F03** | **Congruencia anuncio ↔ flujo** obligatoria; la incongruencia genera rebote | F1·C7 | `ADOPTADO` | `CLAUDE.md` (checklist FIN FASE 1) |
| **M-F04** | **Agregar valor, no bajar precio** (10-30 beneficios en el flujo) | F1·C7·C15 | `ADOPTADO` | `ETAPA-5.md` |
| **M-F05** | El **audio** es enganche innegociable (41-50 s) | F1·C7 | `ADOPTADO` | `ETAPA-5.md` |
| **M-F06** | Lo que más se optimiza del flujo son **las propuestas de valor** — no los hooks ni los testimonios | **F5** | `ADOPTADO` 02-sep — hechos operativos de LucidBot en `ETAPA-5.md` | `ETAPA-5.md` |
| **M-F07** | Con buena investigación de mercado desde el inicio, **casi no hay que tocar el flujo**: te vas directo a sacar creativos | **F5** | `ADOPTADO` (es la tesis de `etapa-1b` + `etapa-2`) | `ETAPA-1B.md` |
| **M-F08** | La **información del producto NO va en las reglas** del bot: va en su campo. Las reglas son solo conversacionales (cómo da el precio, cuándo pide la ciudad) | **F4** | `ADOPTADO` 02-sep — hechos operativos de LucidBot en `ETAPA-5.md` | `ETAPA-5.md` |
| **M-F09** | Al importar un producto de Superbodega, **LucidBot queda DESACTIVADO** y no manda el mensaje inicial | **F4** | `ADOPTADO` 02-sep — verificación previa al lanzamiento en `ETAPA-5.md` → `1_HACER_MANUAL.txt` | `ETAPA-GUARDAR-PRODUCTO.md` |
| **M-F10** | Arrancar con **5 FAQ generales** e ir agregando las que aparezcan en los chats reales | **F4** | `ADOPTADO` | `PLANTILLAS_DEFAULTS_OPERADOR.md` |
| **M-F11** | La oferta no es el precio, es el **valor**: "tratamiento de X cápsulas", "la más elegida" | F1·C7 | `ADOPTADO` | `ETAPA-5.md` |
| **M-F12** | Cuando la persona se sale del chat, **Meta la manda a tu competencia** | F1·C22 | `ADOPTADO` | `ETAPA-5.md` |

### G · MÉTRICAS

| ID | Afirmación | Fuente | Cifra | ESTADO | Dueño |
|---|---|---|---|---|---|
| **M-G01** | La métrica real es **% conversación por clic en el enlace**, no el CTR | F1·C7·C22 | **35-70 %** | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §8 |
| **M-G02** | A mayor % de conversión, **menor CPA**. El embudo es la palanca del CPA | F1·C6 | — | `ADOPTADO` | `DATA_PLAYBOOK.md` |
| **M-G03** | Se vende con **CTR bajo (0.80-0.90)** si el ángulo es ganador: no tocar lo que vende | F1·C7 | 0.80-0.90 | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §8 |
| **M-G04** | El **CPA real** se calcula sobre despachados y **entregados**, no sobre vendidos | F1·C8 | 100 → 70 → 60 | `ADOPTADO` | `CONTABILIDAD.md` · `_TASA_ENTREGA.csv` |
| **M-G05** | "Ganador" no significa 100 ventas: es el que **genera ventas o buenas métricas** (costo por mensaje, tráfico de calidad) | **F5** | — | `RECHAZADO` parcialmente — APR-002: la conversación **corta pero no corona**. Ver C-04 | `CLAUDE.md` regla 6 |
| **M-G06** | El truco para duplicar ventas es duplicar **impresiones** (más anuncios), no presupuesto | F1·C7 | — | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |

### H · ACTIVOS, CUENTAS Y FANPAGES

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-H01** | **Contingencia mandatoria**: los baneos son certeza, no posibilidad | F1·C11 Camilo | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |
| **M-H02** | **250 anuncios por fanpage** es el límite de circulación | F1·C6·C15 | `ADOPTADO` | `ETAPA-FANPAGE.md` |
| **M-H03** | Fanpages **por ROL**: una de testeo, una de escalado, una de prueba. Crear una casi a diario | **F5** | `SIN-EVALUAR` — el sistema asigna sus 10 fanpages por **categoría/avatar**, no por rol. Ver C-07 | `ETAPA-FANPAGE.md` |
| **M-H04** | **Publicar en la fanpage** es mejor que Post ID: la interacción queda en la página | F1·C11 Camilo | `SIN-EVALUAR` — choca con M-H05 | — |
| **M-H05** | **Post ID** acumula toda la prueba social en el anuncio ganador; el duplicado normal la pierde | F1·C15 Joaquín | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §3.5 |
| **M-H06** | **Multicuenta**: cada cuenta publicitaria se comporta distinto; probar siempre en varias | F1·C15 · **F5** | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §3.6 |
| **M-H07** | Iterar el ganador en **otra cuenta**: en la misma se encarece todo | F1·C11 | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` |
| **M-H08** | Guatemala tiene métricas muy buenas: mercado nuevo, sin saturación | F1·C15 | `ADOPTADO` (es la tesis del negocio) | `README.md` |

### I · GESTIÓN Y RENTABILIDAD

| ID | Afirmación | Fuente | ESTADO | Dueño |
|---|---|---|---|---|
| **M-I01** | Escalar no es gastar más para vender más: es **generar más rentabilidad** | F1·C8 | `ADOPTADO` | `CONTABILIDAD.md` |
| **M-I02** | Subir el precio de mil en mil va **directo al margen neto** | F1·C8 | `ADOPTADO` | `ESCALADO_PLAYBOOK.md` §3 |
| **M-I03** | **Máximo 1-2 productos a la vez** hasta tener agilidad; cinco a la vez es inmanejable | **F5** | `SIN-EVALUAR` — el portafolio tiene **8 productos**. Ver C-07 | `_PORTAFOLIO.txt` |
| **M-I04** | La **logística** es el verdadero diferenciador del escalado; 2 puntos de efectividad valen millones | F1·C8·C9 | `ADOPTADO` | `CONTABILIDAD.md` |
| **M-I05** | "En la repetición está el éxito": ver la clase 4-5 veces, ejecutar rápido | F1·C7·C22 | — | — |

---

## 3. BITÁCORA DE CHOQUES — dónde las fuentes se contradicen

> Esta sección es el corazón del archivo. Un choque **no se borra**: se registra, se resuelve y se
> deja la resolución fechada. Si mañana llega una clase que lo reabre, se agrega una línea, no se
> reescribe la historia.

### C-01 · OBJETIVO DE CAMPAÑA — Tráfico vs Ventas vs Interacción
- **Mercy (F1·C6):** Tráfico es el favorito y sí vende con embudo de WhatsApp fuerte.
- **Camilo (F1·C11):** Ventas trae público más calificado pero CPA más alto.
- **Calet (F5, 22-ago):** Ventas está rindiendo mejor; Tráfico trae 1.000 personas mal calificadas.
- **Data propia:** APR-002 — `tinnidrop-1` 78 % de conversación → **0 ventas**; `ANIMO` la más alta → 0 ventas. El patrón que describe Calet **existe en nuestros datos**.
- **⚠️ El matiz que ninguna clase menciona:** con destino WhatsApp y **sin CAPI**, "Ventas → maximizar conversaciones" optimiza por **el mismo evento** que Tráfico. `omni_purchase` devuelve "Not available": **Meta no ve ninguna venta nuestra**. El cambio de dropdown sin CAPI es cosmético — cambia la subasta, no la señal.
- **RESOLUCIÓN (2026-09-02):** `TEST GEMELO A/B` — una campaña `OUTCOME_SALES` contra una `OUTCOME_TRAFFIC`, mismo ángulo, creativo y presupuesto. Se registra en `_TESTEOS.csv`. **En paralelo se abre el frente CAPI como proyecto aparte** — sin él, el test mide poco.
- **ESTADO 02-sep:** registrado como **T02** en `_TESTEOS.csv` (brazo A `OUTCOME_TRAFFIC` control · brazo B `OUTCOME_SALES`), en estado `PROPUESTO` hasta que el operador fije producto y fecha. El default del sistema **sigue siendo `OUTCOME_TRAFFIC`** (`ETAPA-6.md` R3F-12).

### C-02 · CADENCIA DE SURFING — una vez al día vs varias veces al día
- **Camilo (F1·C11):** +20 % **solo hasta las 9-10 AM**; más tarde desoptimiza.
- **Calet (F5):** +20 % **varias veces al día** hasta las 2-3 PM, mientras el CPA siga bajo. Explícito: "eso no se desoptimiza, le estás diciendo a Meta que quieres más de lo que te está trayendo".
- **Data propia:** APR-057 — la ventana 14-16 ago subió el gasto **+63 %** y compró **0.3 ventas/día más**, partiendo la ganancia al medio. El techo demostrado es **Q597/día** de portafolio.
- **RESOLUCIÓN (2026-09-02):** `CONGELADO`. La razón de fondo: **Calet escala rápido porque tiene el banco de conceptos alimentando la campaña.** Copiar su cadencia sin su línea de producción es reproducir el 14-16 de agosto. Se descongela cuando la fábrica (BLOQUE C) esté produciendo ≥6 creativos/día.

### C-03 · POST ID vs PUBLICAR EN LA FANPAGE — y el hecho nuevo de plataforma
- **Camilo (F1·C11):** publicar en la fanpage es mejor, la interacción queda en la página.
- **Joaquín (F1·C15):** Post ID acumula toda la prueba social; el duplicado normal la pierde.
- **Calet (F5, 22-ago) — HECHO NUEVO:** **el objetivo Ventas ya no deja extraer el Post ID** (los posts se volvieron dinámicos). Tráfico e Interacción sí. Workaround de Joaquín: duplicar en campaña nueva, esperar revisión, sacar el Post ID ahí.
- **RESOLUCIÓN:** se mantiene Post ID (M-H05) **pero queda condicionado a C-01**: si el test gemelo corona `OUTCOME_SALES`, se pierde la palanca Post ID tal como está escrita hoy en `ESCALADO_PLAYBOOK.md` §3.5. **Las dos decisiones están acopladas y hay que tomarlas juntas.**

### C-04 · LA CONVERSACIÓN COMO SEÑAL DE GANADOR
- **Mentores (F1·C7, F5):** el ganador se identifica por ventas **o** por buenas métricas de conversación/costo por mensaje.
- **Data propia (APR-002):** `tinnidrop-1` 78 % conv → 0 ventas · `ANIMO` 68 % (la más alta) → 0 ventas · `ME DIJERON` 23 % → de los que más vende.
- **RESOLUCIÓN (vigente desde jul-2026):** **la conversación sirve para CORTAR, nunca para CORONAR.** Gana la data propia. Escrito en `CLAUDE.md` regla 6.

### C-05 · SEGMENTACIÓN AMPLIA vs BANDA DE EDAD
- **Andrómeda (F1·C19·C4):** el creativo segmenta, no hace falta segmentar por edad ni intereses → amplia 18-65+.
- **Data propia (APR-060):** banda 25+ → CPA **Q140.5**, cierre 3.1 % · banda 45-60 → CPA **Q31.7**, cierre 12.7 %. Experimento natural con el mismo ángulo, producto y creativo: `PERDIDA_AUDITIVA` pagó **Q473.6/venta** a 25+ y **Q30.6** a 45-60.
- **RESOLUCIÓN (2026-09-02):** gana la data propia. **La constante "amplia 18-65+" de `CLAUDE.md` se corrige**: la banda se deriva del avatar del ángulo. **Implementado el 02-sep** (`ETAPA-6.md` → BANDA DE EDAD · `CLAUDE.md` → SEGMENTACIÓN · `MCP_PLAYBOOK.md`). No contradice a Andrómeda en su núcleo — el creativo sigue segmentando; lo que se corrige es dejar de pagar impresiones a una banda que no compra.

### C-06 · DENSIDAD DEL CREATIVO — umbral cognitivo vs "muchas propuestas de valor"
- **Clase 22 (F1):** umbral cognitivo, no saturar la imagen, 6-8 propuestas de valor.
- **Calet (F5):** "colocarle en todas muchas propuestas de valor, muchas, atacando todo… tantos beneficios que el cliente diga *este es el producto perfecto*".
- **RESOLUCIÓN:** no se resuelve por doctrina — **ya está corriendo el test T01** en `_TESTEOS.csv` (variante `ligera` vs `densa` vs `colage-sintomas`, ángulo fijo). El resultado del T01 cierra este choque con data propia.

### C-07 · CUÁNTOS PRODUCTOS Y CUÁNTAS FANPAGES A LA VEZ
- **Calet (F5):** máximo **1-2 productos**; con cinco tuvo que optimizar cinco y se le fueron las métricas. Fanpages **por rol** (testeo / escalado / prueba), creando casi una al día.
- **Sistema hoy:** **8 productos** en `_PORTAFOLIO.txt`; 10 fanpages asignadas por **categoría/avatar** (`ETAPA-FANPAGE.md`), no por rol.
- **RESOLUCIÓN:** `SIN-EVALUAR`, con una observación propia: el dimensionamiento de la FASE 2 da **$24/día por producto** contra un techo de portafolio de Q597/día → **cabe UN solo producto en fase de conceptos a la vez.** Se llega a la misma conclusión que Calet por aritmética, no por doctrina.

### C-08 · TESTEAR vs VENDER DESDE EL DÍA 1
- **Mercy (F1·C6·C8):** "nosotros no testeamos, vendemos"; si otro ya lo vende, salí a vender.
- **Joaquín (F1·C15) y Calet (F4·F5):** el primer día se busca DATA; testeo masivo de creativos antes de escalar.
- **RESOLUCIÓN:** gana la línea Joaquín/Calet, que además es la que sostiene todo el diseño del sistema (FASE 1 = instrumento de medición). M-B11 queda `RECHAZADO` para nuestro contexto.

### C-09 · ¿ABO REPARTE ENTRE LOS ANUNCIOS DE UN CONJUNTO?
- **Calet (F4·F5):** ABO reparte el presupuesto entre los 5 anuncios; por eso el 1-1-5 sirve para testear creativos y el CBO no.
- **Camilo (F1·C11) y `ETAPA-6.md`:** "cuando Meta se enamora de un anuncio" concentra el presupuesto en uno y deja a los demás sin entrega — **exactamente lo contrario**.
- **RESOLUCIÓN:** se adopta el 1-1-5 igual, **pero con guardarraíl obligatorio**: un anuncio que no recibió entrega se marca **`SIN_ENTREGA`**, nunca `PERDEDOR`. Y el veredicto se toma por replicación (M-A09), no por una sola corrida. Sin ese guardarraíl, el 1-1-5 mata conceptos que nunca se testearon.

### C-10 · LA BRECHA DE CIERRE
- **Mentores (F4·F5):** el umbral es **15-20 %**. Con eso, cualquier estructura vende.
- **Data propia (17-20 ago):** portafolio **8.2 %** · NUSAVA 13.7 % · TINNIDROP 8.0 % · CLEARSTEM 4.9 %.
- **Aritmética:** los mismos 487 mensajes al 15 % serían **73 ventas en vez de 40** → CPA de Q52.5 a **Q28.8**. Ningún cambio de estructura de campaña se acerca a ese retorno.
- **RESOLUCIÓN:** el mentor tiene razón y el sistema tenía la prioridad invertida — había 8 archivos de doctrina sobre estructura y **ninguna etapa que optimizara el flujo contra data**.
- ✅ **CERRADO 02-sep: se construyó `etapa-11`** (optimizador de flujo). Handoff de origen en
  `_OPERADOR/HANDOFF_ETAPA-11_OPTIMIZADOR_FLUJO_2026-09-02.md`; agente en `.claude/agents/ETAPA-11.md`.

**LA VERIFICACIÓN QUE SE CORRIÓ ANTES DE CONSTRUIRLO** (serie 17-jul → 01-sep, 5,090 msj / 439
ventas, excluyendo VARICOSE ≥01-ago por el cambio de producto físico). Informe completo:
`PRODUCTOS/_AUDITORIAS/_VERIFICACION_BRECHA_CIERRE_20260902.txt`.

- **La hipótesis del paraguas quedó SIN TESTEAR, no refutada.** Clasificando por el número real de
  `angulo_key` que alimentan un mismo flujo (el nombre de campaña miente: la migración del 12-ago
  renombró a `…_ESCALA_…` campañas que siguen corriendo 2-3 ángulos):
  **dedicado 7.2 % · paraguas 9.0 %** — al revés de lo esperado; y dentro de TINNIDROP, el único
  producto con ambos regímenes y `n` usable, **7.96 % vs 8.32 %, Fisher p = 1.000**.
  ⚠️ **Pero `_EVENTOS.csv` no registra ni un `CAMBIO_BOT`** para NUSAVA/TINNIDROP/VARICOSE, y el
  ítem "configurar en LucidBot el flujo de UN SOLO ÁNGULO" del `1_HACER_MANUAL.txt` de NUSAVA
  quedó sin marcar → **no hay evidencia de que el flujo dedicado se haya cargado alguna vez.**
  Lo medido es "un ángulo apuntando al mismo paraguas", que no es la hipótesis.
- **Lo que SÍ quedó firme:**
  · **El ángulo explica 7× más varianza de cierre que el régimen del bot** — spread por ángulo
    5.9 %→18.1 % (12.2 pp) contra 1.8 pp por régimen y 4.2 pp por producto.
  · **Un mismo flujo cierra distinto según el ángulo que le manda tráfico, más allá de Poisson:**
    TINNIDROP χ²=22.6 df=4 **p=0.0002** · CLEARSTEM χ²=16.5 df=3 **p=0.0009**.
  · **La conversación no predice el cierre** (Pearson r=−0.23, p=0.54 entre ángulos) → refuerza
    APR-002 y el choque C-04.
  · **El premio:** llevar cada ángulo al cierre del mejor ángulo de SU producto = **+40 % de ventas
    sin gastar un quetzal más**. Al 15 % del mentor: **+324 ventas, CPA Q51.5 → Q29.6**.
  · ⚠️ **Límite que la data no puede salvar:** sin transcripciones de chat es imposible separar
    "el flujo cierra mal ese ángulo" de "ese ángulo trae tráfico que no compra" — las dos hipótesis
    predicen los mismos números. Por eso `etapa-11` toma exports de chat semanales como input, y
    sin ellos declara que su diagnóstico es de LOCALIZACIÓN y no de CAUSA.
- **CÓMO SE RESUELVE LA PARTE ABIERTA:** con un **A/B de flujo** — brazo A el paraguas optimizado,
  brazo B el dedicado al ángulo ganador, ruteados por **Post ID** a productos distintos del catálogo
  de LucidBot (mismo número, misma página, misma oferta). Es la primera vez que la doctrina
  "dedicado para escalar" se va a poner a prueba de verdad. `n` mínimo por brazo y reglas del test
  en `ETAPA-11.md` PASO 6.
- 🔴 **DEUDA DE INSTRUMENTACIÓN que este choque dejó al descubierto:** un cambio de flujo sin
  `CAMBIO_BOT` logueado en `_EVENTOS.csv` es un cambio que el sistema no puede evaluar. Queda como
  regla 24 de `CLAUDE.md`.

---

## 4. CIFRAS — normalización y qué se porta

**Parámetros de conversión usados en toda la matriz:**

```
COP -> USD :  4.050 COP = 1 USD      (tasa de referencia ago-2026)
USD -> GTQ :  1 USD = 7.62 Q          (TASA_USD_GTQ del sistema)
```

| Cifra del mentor | COP | USD | Q | ¿Se porta? |
|---|---|---|---|---|
| Conjunto de testeo Mercy (1×3×2) | 6.000 | $1.48 | Q11 | ❌ NO-PORTAR — es de 2025, mercado CO |
| Testeo 1-1-5 rápido | 25.000 | **$6.17** | Q47 | ✅ SÍ — dentro de la fórmula propia |
| Testeo 1-1-5 suave | 16.000 | **$3.95** | Q30 | ✅ SÍ |
| 1-2-5 (dos conjuntos) | 50.000 | **$12.35** | Q94 | ✅ SÍ |
| Escalado 1-1-7 CBO | 60-72.000 | **$14.8-17.8** | Q113-136 | ⚠️ CON GATE — solo con ganador confirmado |
| Conjunto del 1-7-7 masivo | 7.000 | $1.73 | Q13 | ❌ NO-PORTAR — implica 40+ conjuntos |
| Campaña escalada al tope | 500.000 | $123 | Q940 | ❌ NO-PORTAR — techo propio Q597/día (APR-057) |
| Techo de CPA para frenar | 10.000 | $2.47 | Q19 | ❌ NO-PORTAR — depende de su ticket. Usar **Break-Even propio** |

> **La regla que evita el error más caro:** una cifra de **presupuesto** sí se puede portar
> (es una decisión de velocidad). Una cifra de **CPA, cierre o ticket NO** — depende del precio
> del producto, del mercado y del costo del proveedor. `CONTABILIDAD.md` y `ETAPA-1.md` son los
> dueños de esos números y no aceptan cifras de clase.

---

## 5. LO QUE NO ESTÁ EN NINGUNA CLASE — doctrina propia

> Se ganó con plata y no tiene fuente externa. **Si un rediseño la pierde, se pierde el activo.**

| Doctrina propia | Fuente interna | Por qué ninguna clase la tiene |
|---|---|---|
| **La dispersión de Poisson por conjunto** (índice 1.12 = azar puro; por ángulo 2.99 = señal) | `CALENDARIO_ESCALADO.md` §1.5 · APR-055 | Ningún mentor mide varianza; deciden por conjunto y creen estar leyendo señal |
| **Agregar por `angulo_key`, nunca por conjunto-semana** | `CLAUDE.md` regla 6 | Consecuencia de lo anterior |
| **La conversación corta pero no corona** | APR-002 | Los mentores la usan para coronar (C-04) |
| **Banda de edad por avatar** | APR-060 | Contradice a Andrómeda; nadie lo mide (C-05) |
| **Cohorte ≠ caja · maduración de 10 días · el margen logístico de Dropi no es la ganancia** | `CONTABILIDAD.md` · APR-072/073 | Ningún mentor separa fecha de orden de fecha de entrega |
| **Compliance MSPAS / verbos prohibidos solo en ADS, nunca post-clic** | `CLAUDE.md` | Es específico de Guatemala y de nuestra lectura de riesgo |
| **Lavado anti-copyright por huella de contenido** | `Ads/_TOOLS/LAVADO.md` | Las clases mencionan el baneo silencioso pero no el mecanismo ni la contramedida |
| **`producto_key` como llave y `_DIM_PRODUCTOS.csv` como resolutor de carpetas** | `DATA_PLAYBOOK.md` §1.1 | Es infraestructura de data, no metodología de pauta |

---

## 6. PROTOCOLO — cómo se agrega una clase nueva

1. **El archivo entra con fecha en el nombre:** `Clase YYYY-MM-DD - Tema (Instructor).txt`, en
   `VITALCOM_CLASES/` (fuera del repo, ver nota en §1). Sin fecha en el nombre, la precedencia no
   se puede aplicar.
2. **Se agrega la fila a §1** (FUENTES) con su ID `F[N]` y su fecha.
3. **Se destila en afirmaciones**, una por idea, con su ID de dominio (`M-A17`, `M-D19`…).
   **Los IDs no se reciclan ni se renumeran** — una afirmación retirada queda con estado
   `RECHAZADO`, no se borra.
4. **Se busca el choque:** por cada afirmación nueva, ¿contradice alguna existente o algún
   `APR-xxx`? Si sí → entrada en §3 con resolución fechada. **Este es el paso que no se salta.**
5. **Toda cifra se normaliza** en §4 y se marca si se porta o no.
6. **Solo después** se toca el archivo dueño. La matriz registra; el archivo dueño ejecuta.
   Un cambio en la matriz sin cambio en el dueño deja la afirmación en `PENDIENTE`, y eso está bien:
   es visible.

> **Advertencia de mantenimiento.** Esta matriz **no reemplaza** a `VITALCOM_CLASES/`:
> las transcripciones completas siguen siendo la fuente. La matriz es el índice con estado.
> Si una afirmación acá contradice a su transcripción, gana la transcripción y se corrige acá.
