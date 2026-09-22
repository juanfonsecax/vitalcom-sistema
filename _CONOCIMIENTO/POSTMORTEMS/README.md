# POSTMORTEMS — por qué existe cada regla

Consulta humana. **Ningún agente carga esta carpeta** (`gen_grafo.py` la trata como zona muerta), así
que lo que vive acá no cuesta tokens en ejecución.

Las reglas quedan en los prompts como directivas; la historia de cómo se descubrieron vive acá. Si
dudás de una regla antes de cambiarla, leé su incidente primero.

| Archivo | Qué guarda |
|---|---|
| `CLAUDE_MD_v1.1_completo.md` | CLAUDE.md íntegro antes de la poda del 22-sep-2026 (T1 de `optimizacion-sistema`), con todas sus historias. Incluye lo que ya traía el tag `v1.1-pre-poda` (16-sep-2026) más las filas EL FLUJO LUCIDBOT y LA APP WEB, agregadas entre el 16 y el 21-sep |

## Incidentes citados en CLAUDE.md v1.1

| Fecha | Incidente | Regla que dejó | Dónde vive la regla hoy |
|---|---|---|---|
| 06-sep-2026 | Banda de edad registrada solo como sufijo del nombre del conjunto; se perdía al renombrar | La banda real se escribe en un CSV | `PRODUCTOS/_DIM_BANDAS.csv` |
| 06-sep-2026 | Error de ventana: orden fechada hoy sobre data vieja | Contar desde el último día CON DATA y declarar el rezago | Invariante 13 · `decidir.py` |
| 06→08-sep-2026 | Campaña publicada sin escribir los `ad_id`; el sistema leyó "cero publicados" mientras Meta gastaba $23.46 en 10 anuncios con la pieza equivocada | El CSV no es evidencia del estado de Meta; snapshot antes de crear | `gen_publicacion.py` · `verificar_publicacion.py` · skill `publicar-meta` |
| 07-sep-2026 | `armar_prompts_fase2.py` tomó el primer archivo alfabético como packshot: 5 piezas de TINNIDROP con frasco verde y marca ajena | El packshot se declara; sin fila, exit 1 | `PRODUCTOS/_DIM_ENVASE.csv` |
| 07-sep-2026 | Tecleo simulado + `Enter` en ChatGPT falló de forma intermitente y silenciosa (6 generaciones medidas) | Inserción por `execCommand`, envío por `send-button` | skill `generar-imagenes-chatgpt` |
| 07-sep-2026 | Se confundieron los "3 días" de Calet (duración de campaña a $15-18/día = 20-30 ventas) con una ventana de cálculo | Tres relojes separados; un número de mentor es envoltorio de su presupuesto | Invariante 13 · `_PARAMETROS_DECISION.csv` · `GUIA_MADRE_PARAMETRIZADA.md` |
| 07-sep-2026 | Contrato real de la API de LucidSales medido en vivo (`x-token`, token de 12 h, paginación decorativa) | API directa en vez de xlsx manual | `bajar_lucidsales.py` |
| 08-sep-2026 | `ad_id` corrupto en 2 006 de 2 475 filas | El JOIN es por nombre; los renombrados se aliasan | `_ALIAS_CONJUNTOS.csv` · `alias.py` |
| 08-sep-2026 | Cuatro gates de doctrina que un modelo leyó y no aplicó | El flujo se declara como grafo con predicados | `DOCTRINA/FLUJO.json` · `test_flujo.py` |
| 09-sep-2026 | `_DIM_PRODUCTOS.fase` decía ESCALADO para un producto sin concepto ganador en 2 de 2 | La fase se deriva de la data | `flujo.py` · `_ESTADO_FLUJO.csv` |
| 09-sep-2026 | Decisión del operador | Ejecutar órdenes por MCP solo con confirmación, orden por orden | Invariante 13 |
| 16-ago-2026 | Calet: "115 para validar en ABO y después CBO para escalar"; en CBO Meta corona un solo anuncio | 1-1-5 solo en FASE 2 y en ABO | Constantes · `ETAPA-6.md` |
| APR-002 | `tinnidrop-1` 78 % conv → 0 ventas · `ANIMO` la más alta → 0 ventas · `ME DIJERON` 23 % → de los que más vende | La conversación no predice venta: el ángulo se testea con presupuesto protegido | Invariante 1 · Constantes |
| 16-ago y 22-ago-2026 | Las dos clases de Calet citadas en §0 de la plantilla del bot: el flujo va antes que la estructura de campaña, el objetivo es 15-20 % de cierre, con cierre bajo no se escala, y lo que más lo mueve son las PROPUESTAS DE VALOR. Estructura base tomada del flujo de CLEARSTEM (mejor cierre y mejor CPA del portafolio) | El flujo LucidBot queda declarado en CSV, no escrito en prosa; tres notaciones (`{{variable}}`, `<<BLOQUE:x>>`, `>>`) fijan qué es dato, qué es juicio de `etapa-5` y qué es instrucción que nunca se pega | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` · `Ads/_TOOLS/gen_flujo_bot.py` · `test_gen_flujo_bot.py` |
