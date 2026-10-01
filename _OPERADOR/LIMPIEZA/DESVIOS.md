# DESVIOS — Parte 1 (solo lectura, 2026-09-30)

Metodo: `rg -n -i "BLOQUEADO|a mano|manualmente|hazlo manual"` sobre `Ads/_TOOLS`, `.claude`, `DOCTRINA`;
literales de mercado con los tres `rg` de la hoja de ruta; `rg -n "PROHIBIDO|prohibid"` en `Ads/_TOOLS/*.py`.
Excluidos: `test_*.py`, `_fixtures/**` y lineas que LEEN desde `_DIM_MERCADOS.csv` / `mercado.py`
(se citan como excluidas cuando aplica). Formato por hallazgo: `ruta:linea — texto — por que es desvio`.

## A. BLOQUEOS QUE MANDAN A HACERLO A MANO

1. `Ads/_TOOLS/cargar_cuenta.py:70-71` — "F1.publicar queda bloqueado y se pauta a mano (dueno: Meta, rollout; _DIM_CUENTAS.csv)" — por que: el gate de cuenta sin MCP bloquea la publicacion y el camino es pautar a mano; se pierde lo que `gen_publicacion.py` garantizaria (paquete, verificacion, ad_id).
2. `Ads/_TOOLS/cargar_cuenta.py:78-79` — "las piezas se cargan a mano a la biblioteca de la cuenta (solo GTR 7 la sube)" — por que: sin `sube_media_local=SI` el gate manda a subir media a mano; el nombre/hash queda fuera del control del codigo (caso real 08-sep: 10 anuncios con la pieza equivocada por nombre reusado).
3. `Ads/_TOOLS/gen_publicacion.py:78-81` — "el operador sube las piezas A MANO a la biblioteca de medios ... Es el camino de MCP_PLAYBOOK Paso C/D y el unico que corre sin pantalla" — por que: el modo `biblioteca` es estructuralmente manual (dos volcados antes/despues); el paquete no puede garantizar image_hash sin el operador.
4. `Ads/_TOOLS/gen_publicacion.py:143` — "se devuelven para que el paquete le diga al operador que las agregue a mano" — por que: variantes de copy/titulo que la API no acepta se resuelven a mano en Ads Manager.
5. `DOCTRINA/PLANTILLAS_FLUJO_BOT.md:179-182` — "MENSAJE PRELLENADO DEL ANUNCIO — se configura a mano en Ads Manager ... se configura A MANO en Ads Manager, por anuncio" — por que: `ads_create_creative` no tiene campo para ese texto; cada anuncio necesita un paso manual fuera de LucidBot y fuera del verificador.
6. `.claude/skills/publicar-meta/SKILL.md:72-73` — tabla: mensaje prellenado "se configura A MANO" + subida manual salvo `sube_media_local=SI` — por que: la skill declara el desvio manual como parte del procedimiento.
7. `DOCTRINA/MCP_PLAYBOOK.md:95` — "El operador sube los assets a mano a la biblioteca" — por que: paso C/D manual como precondicion de publicar.
8. `DOCTRINA/MCP_PLAYBOOK.md:189` — "Activar: lo hace el operador manualmente a las 4 AM" — por que: la activacion es un paso manual programado fuera de codigo.
9. `DOCTRINA/MCP_PLAYBOOK.md:216` — "1 texto/anuncio via MCP, el resto lo agrega el operador a mano" — por que: limite de API convertido en trabajo manual por anuncio.
10. `DOCTRINA/COPYWRITING_ADS.md:118` — "Las otras 2 se pegan a mano en 'Agregar opcion de texto'. El sistema igual entrega las 3" — por que: el sistema entrega 3 textos pero 2 viven solo pegados a mano; ninguna verificacion los cubre.
11. `Ads/_TOOLS/gen_app.py:513` — "no se pudo producir PRODUCTOS/_LANZADOR.json — corre gen_lanzador.py a mano y mira el error" — por que: si el generador falla, el camino es correrlo a mano; no hay dato de entrada declarado que el operador pueda aportar por via escrita.
12. `Ads/_TOOLS/alta_producto.py:388` — "renombralos a mano (quitando el sufijo .tmp) para terminar el alta" — por que: un fallo a mitad del alta deja `.tmp` que solo se resuelve renombrando a mano.
13. `Ads/_TOOLS/editar_producto.py:232-243` — "quedaron en `.tmp` para terminar el reemplazo a mano ... renombralo a mano" — por que: mismo patron que 12 en edicion de producto.
14. `Ads/_TOOLS/gen_flujo_bot.py:376-378` — "angulo_nombre ambiguo entre varios angulos de FASE 2 ... se agrega a faltan" + `:644-648` "BLOQUEADO — falta N dato(s)" — por que: un angulo empatado (dato que solo abre el titulo del flujo) bloquea el flujo ENTERO en vez de salir parcial; es el patron del caso OVULOS_PURITY del 29-sep (flujo salio sin REGLAS por un gate de titulo). `armar_prompts_fase2.py` (clase `Bloqueado` con campo `dato`) y el propio `gen_flujo_bot.py:646-647` ("lo produce: ...") hacen lo correcto al declarar dueno, pero este gate puntual bloquea de mas.
No son desvio (se revisaron y se excluyen): `armar_prompts_fase2.py` (todos los `raise Bloqueado` traen `dato=` con el CSV/fuente que lo produce); `flujo.py:1313` (marca BLOQUEADO como estado, no manda a manual); `decidir.py` / `gen_dashboard.py` / `gen_lanzador.py` donde "a mano" aparece en frases que PROHIBEN escribir a mano.

## B. LITERALES DE MERCADO EN CODIGO O PLANTILLA (deberian salir de `_DIM_MERCADOS.csv`)

Regla de exclusion aplicada: fuera tests (`test_*.py`), fixtures (`_fixtures/**`) y lineas que leen el mercado (`_DIM_MERCADOS`, `perfil_mercado`, `perfil_de_producto`, `registro_de_perfil`, `mercado.py`).

### B1. Pais / moneda / transportadora / regulador
1. `Ads/_TOOLS/escribir_fichas.py:71` — `"mercado": "Guatemala"` — por que: mercado hardcodeado en la ficha; deberia salir del mercado del producto.
2. `Ads/_TOOLS/alta_producto.py:418` — `ap.add_argument("--moneda", default="GTQ", ...)` — por que: la moneda default de la cuenta asume GT; el mercado/tasa deberian proponerse desde `_DIM_MERCADOS.csv`.
3. `Ads/_TOOLS/app_html.py:22` — `titulo = app.get("titulo", "VitalCom Guatemala")` — por que: marca de pais en el titulo default de la pantalla.
4. `Ads/_TOOLS/app_html.py:721` — `<span class="brand-tag">Guatemala</span>` — por que: etiqueta de pais fija en el HTML generado.
5. `Ads/_TOOLS/app_html.py:787` — "Banco Canonico Validado del Mercado GT (111 piezas, 22 familias) ... en Guatemala" — por que: el banco de creativos declara mercado GT en literal dentro del HTML.
6. `Ads/_TOOLS/costear.py:187` — "The start-up rule (1u vs 2x1) is calibrated on Guatemala logistics in quetzales" + `:231` "esta calibrada para Guatemala; no aplica a este mercado" — por que: la regla de arranque fija pais y moneda en codigo en vez de parametrize por mercado.
7. `Ads/_TOOLS/gen_lanzador.py:287` — "el maximo en Guatemala es %d, ideal 2" — por que: tope de conjuntos con literal de pais (duplicado con B-D, ver D).
8. `Ads/_TOOLS/gen_plan.py:268` — "la regla de Guatemala permite max 3 (ideal 2)" — por que: misma regla que 7, literal de pais en otro script.
9. `Ads/_TOOLS/gen_dashboard.py:2006` — "El negocio cobra en quetzales (Guatemala) y paga la publicidad en dolares (Meta)" — por que: monedas y pais fijos en el HTML del dashboard.
10. `Ads/_TOOLS/gen_dashboard.py:2052` — `<th>Inv. GTQ</th>` / `CPA real` — por que: columna rotulada en GTQ fijo.
11. `Ads/_TOOLS/gen_dashboard.py:2135` — "Guatemala −Q0.33 vs Peten +Q1.15 — FORZA cobra casi tarifa plana nacional" — por que: transportadora y fletes GT fijos en texto del dashboard.
12. `DOCTRINA/PLANTILLAS_FLUJO_BOT.md:76-77,82` — tabla `{{pais}}` Guatemala/Colombia, `{{transportadoras}}` GINTACOM y FORZA / INTERRAPIDISIMO y ENVIA — por que: valores de mercado escritos en la plantilla; el codigo los lee bien (`resolver()` desde `_DIM_MERCADOS.csv`), pero la plantilla los duplica como literales.
13. `DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md:529,537` — "Ministerio de Salud Publica y Asistencia Social de Guatemala" / "Registro Mercantil de Guatemala" — por que: sellos fijos GT en la especificacion de pieza (el propio archivo avisa que para otro mercado se deriva de `mercado.py`, pero el juego GT queda escrito).
14. `DOCTRINA/PLANTILLAS_FLUJO_BOT.md:147` — "GT → registro MSPAS, CO → registro INVIMA" — por que: mapa regulador-por-mercado en prosa; el codigo (`mercado.py:registro_de_perfil`) ya lo deriva del CSV, la prosa lo duplica.
Excluidas (leen mercado): `mercado.py` completo, `armar_prompts_fase2.py:21-24` (cita `[REG_MSPAS]/[REG_INVIMA]` + "leido por mercado.registro_de_perfil()"), `PLANTILLAS_INFOGRAFIAS_FLUJO.md:524` (deriva sellos de `mercado.py`), `PLANTILLAS_DEFAULTS_OPERADOR.md:33-34` (duenos de los numeros reales, no literales de mercado).

### B2. Persona / voseo en codigo (deberia salir de `persona` del mercado: GT voseo, CO tuteo)
1. `Ads/_TOOLS/gen_flujo_bot.py:217` — "y lo mejor, pagas al recibir" (texto con voseo implicito en plantilla de codigo) — por que: persona fija en el generador.
2. `Ads/_TOOLS/datos_producto.py:132` — "Decinos cuanto te cuesta ... (lo que pagas al proveedor ...)" — por que: prompt al operador en voseo fijo.
3. `Ads/_TOOLS/gen_dashboard.py:1894,2100,2126` — "Que tenes que hacer", "lo maximo que podes pagar", "no tenes derecho" — por que: UI del dashboard en voseo fijo.
4. `Ads/_TOOLS/lanzador_html.py:529,579-580` — "podes pegar", "no lo decis vos, lo decide la data", "Lo unico que tenes que hacer" — por que: UI del lanzador en voseo fijo.
5. `Ads/_TOOLS/gen_pl.py:422` — "El negocio gano ... y vos sacaste ..." — por que: reporte P&L en voseo fijo.
6. `DOCTRINA/PLANTILLAS_FLUJO_BOT.md:208,254,269,280,294,302,306,345,407` — "con vos", "Contame", "por vos", "Ya sabes", "Confirmame", "pagas ... tenes", "podes", "tenes ... disfrutes", "Decime" — por que: toda la plantilla del bot en voseo; para CO deberia salir tuteo desde el mercado.
Excluida (parametriza bien): `DOCTRINA/PLANTILLAS_ADS_SECCIONES/04_PROMPT_CONTROL_FASE1.md:100` ("en la persona del mercado: tuteo → ...").

### B3. Simbolo `Q` hardcodeado (deberia salir de `simbolo` del mercado: GT `Q`, CO `$`)
1. `Ads/_TOOLS/armar_prompts_fase2.py:140` — `lambda v: f"Q{float(v):.0f}"` (fallback sin perfil) — por que: si no hay perfil, el monto sale en Q aunque el producto sea CO.
2. `Ads/_TOOLS/gen_finanzas.py:62` — `def q(n, simbolo="Q")` — por que: default Q en el formateador de finanzas.
3. `Ads/_TOOLS/gen_flujo_bot.py:354` — `v["simbolo"] or "Q"` — por que: fallback Q en la escalera de ofertas.
4. `Ads/_TOOLS/ingerir_lucidsales.py:498` — `simbolo = perfil["simbolo"] if perfil else "Q"` — por que: fallback Q sin perfil.
5. `Ads/_TOOLS/gen_dashboard.py:461-462` — `def q(n): return "Q{...}"` / `q1` — por que: todo el dashboard formatea en Q fijo.
6. `Ads/_TOOLS/costear.py:200` — `def imprimir(d, Q="Q")` + `:195,228` mensajes `Q{costo}` — por que: impresiones de costeo en Q fijo.
7. `Ads/_TOOLS/decidir.py:656,674,694,713,729,761,778,793,1092,1108` — `f"APAGAR: Gasto Q{...}`, `CPA Q{...} ... BE Q{...}` — por que: acciones del motor con Q fijo (un producto CO tambien se reporta en Q).
8. `Ads/_TOOLS/flujo.py:505,709,718` — `"CPA Q%s"`, `"ESCALAR %.0fv CPA Q%s"` — por que: estados del flujo con Q fijo.
9. `Ads/_TOOLS/perfilar_angulos.py:307,312,482,493-494,579-580,585` — `"CPA Q%.1f"`, `"BE Q%.2f"`, `"gasto Q%.0f"` — por que: perfiles con Q fijo.
10. `Ads/_TOOLS/gen_pl.py:58,207-208,282,286,314-315` — `def q(n): return "Q{...}"`, `"= Q%.2f"`, `"× Q%.2f"` — por que: P&L con Q fijo.
11. `Ads/_TOOLS/app_html.py:980,1111-1112`, `lanzador_html.py:303,621` — `'Q'+cpa.toFixed`, `'Q'+be.toFixed` — por que: pantallas con Q fijo en JS.
12. `Ads/_TOOLS/atribuir.py:168,220,246,256-257`, `firma.py:102,134,137`, `verificar_monedas.py:88,108,140,157` — prints con `Q%.2f` — por que: diagnosticos con Q fijo (en `verificar_monedas` el propio script lee la tasa de `_PARAMETROS_FINANZAS.csv`, pero el simbolo sigue fijo).

## C. REGEX DE PROHIBICIONES SIN `\b` AL INICIO

1. `Ads/_TOOLS/gen_flujo_bot.py:127-131` — `PROHIBIDO = [(r"cu[aá]l de estas situaciones se parece", ...), (r"(?:cura|curar|elimina el|erradica)\b", ...)]` — por que: ninguno de los dos patrones lleva `\b` al inicio. El segundo calza dentro de otra palabra: `cura\b` calza al final de "frescura" ("...frescura" termina en cura + fin de palabra) y `curar` calza al final de "procurar"; `elimina el`/`erradica` sin `\b` inicial tambien pueden calzar tras otra letra. El caso "cura en frescura" es el ejemplo real de la hoja de ruta. `for patron, motivo in PROHIBIDO:` en `:597` aplica estos patrones sobre el texto renderizado, asi que un falso positivo RECHAZA un flujo valido (`:658-662`).
2. Revisados y OK (con `\b` o sin riesgo de subpalabra en este alcance): no hay mas listas `PROHIBIDO` en `Ads/_TOOLS/*.py` no-test fuera de `gen_flujo_bot.py`; los `rg "prohibid"` restantes son comentarios (`flujo.py:54,980,1011`, `decidir.py:235`), mensajes de validacion (`gen_app.py:290,373`) y tests (`test_gen_flujo_bot.py:43-47`, `test_gen_app.py:306`, `test_evals_baseline.py:112`, `test_gate_entrada.py:89`).

## D. MISMA REGLA ESCRITA EN DOS LUGARES

En el inventario no se marco ningun `DUPLICADO` verificado (regla: solo si se leyo en ambos archivos). Candidatos para la Parte 2, NO verificados aun:
1. Tope de conjuntos con precio con literal Guatemala: `Ads/_TOOLS/gen_plan.py:268` vs `Ads/_TOOLS/gen_lanzador.py:287` (ver B1.7-8).
2. `TASA_COP_USD = 3152.5` en `ingerir_lucidsales.py:80`, `ingerir_meta.py:85` e `ingestar_unificado.py:57` (mas `bajar_meta_insights.py:107` que la reusa por import): mismo numero en tres archivos; por leer si es una sola fuente o tres copias.
3. `TASAS_A_USD = {"COP": ...}` en `ingerir_lucidsales.py` vs `ingerir_meta.py:88`: mismo mapa en dos ingestas.
