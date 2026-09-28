# evals/ — baseline congelada de outputs reales, por etapa

Por qué existe: CLAUDE.md prohíbe podar la prosa de `.claude/agents/ETAPA-*.md`
hasta que exista un eval — y hasta hoy (T11, `odd/tasks/g07-cimientos.md`) no
existía ninguno, así que las 17 prompts quedaban congeladas para siempre. Esta
carpeta es ese eval: una foto de outputs REALES ya guardados en `PRODUCTOS/`,
más un assert determinista por etapa que dice si ese output cumple su propio
contrato. No mide "calidad de redacción" — mide que la ESTRUCTURA del output
(campos obligatorios, conteos, vocabulario cerrado, reglas duras de doctrina)
siga siendo la que la etapa promete.

## Qué hay acá

```
evals/
  promptfooconfig.yaml   ← la lista de tests: (etapa, producto, fixture, assert)
  run_baseline.py         ← runner puro-Python, no necesita promptfoo instalado
  fixtures/<etapa>/<producto>.{txt,json,md}
                           ← recorte o copia congelada de un output real de PRODUCTOS/
  asserts/<etapa>*.py      ← un assert determinista por etapa, firma python-assert de promptfoo:
                             def get_assert(output: str, context: dict) -> dict
```

Los fixtures son SOLO LECTURA de lo que ya está en `PRODUCTOS/`: nunca se
editan los CSV ni los archivos de producto desde acá — se copian o recortan
una vez, congelados con fecha 23-sep-2026.

## Cómo correrla

Sin promptfoo instalado (el camino de todos los días — no instala nada):

```bash
python evals/run_baseline.py
```

Con promptfoo real (opcional, para comparar contra la herramienta de
referencia — fija la versión, no la instala globalmente):

```bash
npx promptfoo@0.107.3 eval -c evals/promptfooconfig.yaml
```

El runner propio y `promptfoo eval` leen la MISMA config y deben coincidir en
qué test pasa y cuál falla: el provider `echo` + `assert type: python` es
compatible con ambos.

## Cobertura — 11 de las 17 etapas

| Etapa | Productos cubiertos | Fixture (fuente real) |
|---|---|---|
| etapa-producto | OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §VALIDACIÓN DE PRODUCTO |
| etapa-1 (costeo) | CLEARSTEM, NusavaB12, TINNIDROP, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §COSTEO |
| etapa-1b (componentes/voz) | NusavaB12, TINNIDROP, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §COMPONENTES / §VOZ DEL CLIENTE |
| etapa-2 (6 ángulos) | CLEARSTEM, NusavaB12, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §ÁNGULOS / §CONJUNTOS |
| etapa-fanpage (retargeted, T1 p2-simplificacion — ver nota abajo) | CLEARSTEM | `2_DATA_PRODUCTO.txt` §FANPAGE ASIGNADA |
| etapa-4 (copy FASE 1) | TINNIDROP | `1_HACER_MANUAL.txt` §PARTE 4 — MEDIA + COPIES DE LOS 6 CONJUNTOS (los 3 conjuntos nuevos) |
| etapa-6 (`_PLAN.json`) | CLEARSTEM, NusavaB12, TINNIDROP, OVULOS_PURITY | `_PLAN.json` completo |
| etapa-5 (bot LucidBot) | CLEARSTEM, TINNIDROP | `FLUJO_LUCIDBOT.md` completo |
| etapa-7 (monitor diario) | TINNIDROP | `_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt` §PASO 3 — bloque "Lectura cualitativa (ETAPA-7)" |
| etapa-7 fusionada (monitor + escalado, T3 p2-simplificacion) | TINNIDROP | `_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt` §PASO 3 completo, ver "Fusión T3" abajo |
| etapa-8 (plan de escalado, histórico — hoy es etapa-7) | TINNIDROP | `4_PLAN_ESCALADO.txt` (extracto) |
| etapa-9 (fábrica de conceptos) | TINNIDROP | `_DIM_CREATIVOS.csv`, tanda real (`producto_key=TINNIDROP`, `fecha_alta=2026-09-06`, 5 filas) |
| etapa-guardar-producto (invariante 8) | los 4 productos | manifiesto congelado de archivos de nivel superior en `PRODUCTOS/<P>/` |

Cada fixture nuevo (`etapa-4`, `etapa-7`, `etapa-9`) trae un `SOURCE.txt` en su
carpeta con la ruta exacta y la fecha del output real del que se recortó —
las demás etapas ya documentaban su fuente en esta misma tabla desde T11.

**Sin output real guardado en disco, por lo que no tienen fixture (6 de 17):**

| Etapa | Por qué no hay output guardado |
|---|---|
| etapa-0 | Selección de 6 videos: vive en la sesión, se consume por etapa-2/etapa-6 y no se persiste como archivo propio. Se buscó de nuevo en T3 (odd/tasks/p1-cimientos.md) en `2_DATA_PRODUCTO.txt` y en las carpetas de transcripciones — ningún producto tiene guardadas las 3 tablas de ETAPA-0.md (clasificación completa / agrupación por ángulo / ranking final); solo sobrevive el ranking de RE-TESTEO (etapa-7/8), que es un output distinto. |
| etapa-3 | Su banco de 8-12 microángulos históricamente no aterrizaba en disco (ver T8 item 4); hoy solo se exige que `4_PLAN_ESCALADO.txt` contenga la palabra "MICROÁNGULO" para pasar el gate `F4.plan` de `flujo.py` (ex-`F3.plan`; renombrado por las cuatro fases, 28-sep-2026) — ningún producto real está hoy en ese nodo (T8 lo confirma), así que no hay un `4_PLAN_ESCALADO.txt` real con esa sección para congelar. |
| etapa-10 | Brief de lectura concepto↔métrica (las 6 secciones de ETAPA-10.md, incluida la matriz ángulo×concepto y el brief EXPLOTAR/EXPLORAR/NO REPETIR para etapa-9): se entrega en sesión, se buscó de nuevo en T3 en `_AUDITORIAS/`, `_APRENDIZAJES.csv` y los HANDOFF de optimización — lo más cercano que persiste es el output de `atribuir.py` (código, no prosa de esta etapa) citado como `fuente` en `_APRENDIZAJES.csv`; no hay un informe propio guardado. |
| etapa-11 | Brief de cierre del bot: mismo caso que etapa-10, output de sesión consumido por etapa-5. |
| etapa-render | Produce imágenes PNG, no texto — fuera del alcance de un assert de contrato textual/JSON. |

Si una futura sesión localiza un output real guardado para alguna de estas
cinco, se agrega su fixture + assert siguiendo el mismo patrón — este README
y `promptfooconfig.yaml` son quienes registran la cobertura real, no una lista
aparte.

## Fallos conocidos documentados (no se debilitó ningún assert para taparlos)

`etapa-4 / TINNIDROP — FASE 1 todo-en-imagen`: uno de los 3 TÍTULOS del
conjunto "ME DIJERON QUE NO TIENE CURA" es literalmente `"¿Te dijeron que no
hay cura?"` — usa la palabra "cura", que `DOCTRINA/COPYWRITING_ADS.md`
§PRINCIPIO 7 lista para evitar, aunque sea una pregunta retórica citando la
objeción del cliente y no un claim afirmativo. Es un output real, presente
desde la línea base del repo (02-sep-2026); nunca se corrigió porque hasta
este eval no existía ningún chequeo automatizado de compliance de copy. El
assert quedó estricto: el hallazgo queda documentado en
`promptfooconfig.yaml` para que quien toque `ETAPA-4.md` decida si el título
se corrige, no se reescribió el fixture ni se relajó el assert para taparlo.

## Retargeting T1 (p2-simplificacion, 23-sep-2026) — `etapa-fanpage`

El agente `.claude/agents/ETAPA-FANPAGE.md` se eliminó: sus 10 páginas pasaron a
DATA en `PRODUCTOS/_DIM_FANPAGES.csv` y su JUICIO de asignación (reglas F1-F5)
se absorbió en `.claude/agents/ETAPA-2.md` §ASIGNACIÓN DE FANPAGE, que emite el
mismo bloque `<pagina_asignada>` que consumían ETAPA-4/5/6. El fixture
`fixtures/etapa-fanpage/CLEARSTEM.txt` sigue siendo el output REAL congelado
del agente extinto (no se reescribe: sigue probando el mismo contrato de
formato). Lo único que cambió es `asserts/etapa-fanpage.py`: antes cruzaba el
nombre de página contra la doctrina de `ETAPA-FANPAGE.md` (ya no existe); ahora
cruza contra `PRODUCTOS/_DIM_FANPAGES.csv` (columna `pagina_nombre`) — el
mismo catálogo cerrado, ahora en su dueño de datos. El assert no se debilitó:
sigue exigiendo que una de las 10 páginas reales aparezca citada en el output.
El ID del test (`etapa-fanpage / CLEARSTEM`) se mantiene por honestidad
histórica del fixture; su contrato de facto hoy es el `<pagina_asignada>` que
produce `etapa-2`.

## Fusión T3 (p2-simplificacion, 24-sep-2026) — `etapa-7` + `etapa-8`

`.claude/agents/ETAPA-8.md` se eliminó: su lógica de palancas (PASO 5 de la
nueva `ETAPA-7.md`) y su sección de aprendizajes se absorbieron en
`etapa-7`, que ya monitoreaba y ya era la etapa que `ciclo-diario` invocaba
en la misma pasada que `etapa-8` (nunca corrían separadas). Los dos fixtures
y asserts viejos (`fixtures/etapa-7/TINNIDROP.txt` + `asserts/etapa-7.py`,
`fixtures/etapa-8/TINNIDROP.txt` + `asserts/etapa-8.py`) se dejaron **sin
tocar y con la misma fuerza** — siguen probando sus contratos originales
sobre outputs reales e históricos.

Se agregó un tercer test, `etapa-7 fusionada / TINNIDROP`, que corre un solo
fixture contra **los dos asserts** (`promptfooconfig.yaml` ya soporta una
lista de `assert` por test; `run_baseline.py` los evalúa con AND lógico sin
tocar el runner). El fixture (`fixtures/etapa-7/TINNIDROP_FUSIONADO.txt`) es
real: el bloque completo de PASO 3 de `_AUDITORIA_DIARIA_20260908.txt`, de
cuando `ciclo-diario` ya corría `etapa-7` + `etapa-8` en la misma pasada y
las presentaba sin separación — es el output real más parecido a lo que hoy
produce la etapa fusionada.

El fixture fusionado es un output real de la etapa fusionada y pasa los dos
asserts (`etapa-7.py` y `etapa-8.py`) sin debilitar ninguno. Su fuente está en
`fixtures/etapa-7/SOURCE_FUSIONADO.txt`.

## Protocolo de poda (para cuando se toque un prompt de ETAPA-*.md)

1. Correr `python evals/run_baseline.py` ANTES de tocar nada — confirma que
   arranca en verde (27/28, con el fallo conocido de arriba).
2. Cambiar el prompt.
3. Re-correr la etapa sobre los MISMOS inputs congelados que produjeron el
   fixture (mismo producto, mismos insumos — nunca un producto nuevo, eso no
   prueba nada sobre la regresión).
4. Congelar el nuevo output como fixture de prueba (no pisar el fixture
   original todavía) y correr su assert.
5. Si pasa igual o mejor (nunca un fallo nuevo no documentado) → el nuevo
   output reemplaza al fixture viejo y el commit lo dice explícitamente
   ("evals: refresh fixture <etapa>/<producto> after prompt change").
6. Si falla algo que antes pasaba → el prompt se revierte o se corrige; el
   eval nunca se debilita para que el prompt nuevo pase.

## Gate en CI local

`Ads/_TOOLS/test_evals_baseline.py` corre `run_baseline.py` y además muta
un fixture real por assert clave (le rompe el `angulo_key`, le mete un
VIDEO en FASE 1, le borra el veredicto, le agrega un archivo suelto de
rerun) para confirmar que el assert correspondiente SÍ lo rechaza — sin esa
mitad negativa, un assert que siempre devuelve `pass: True` pasaría la gate
igual que uno real. Lo recoge el mismo comando que ya usa el resto del
repo: `python -m pytest Ads/_TOOLS -q -p no:cacheprovider`.
