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

## Cobertura — 8 de las 17 etapas

| Etapa | Productos cubiertos | Fixture (fuente real) |
|---|---|---|
| etapa-producto | OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §VALIDACIÓN DE PRODUCTO |
| etapa-1 (costeo) | CLEARSTEM, NusavaB12, TINNIDROP, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §COSTEO |
| etapa-1b (componentes/voz) | NusavaB12, TINNIDROP, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §COMPONENTES / §VOZ DEL CLIENTE |
| etapa-2 (6 ángulos) | CLEARSTEM, NusavaB12, OVULOS_PURITY | `2_DATA_PRODUCTO.txt` §ÁNGULOS / §CONJUNTOS |
| etapa-fanpage | CLEARSTEM | `2_DATA_PRODUCTO.txt` §FANPAGE ASIGNADA |
| etapa-6 (`_PLAN.json`) | CLEARSTEM, NusavaB12, TINNIDROP, OVULOS_PURITY | `_PLAN.json` completo |
| etapa-5 (bot LucidBot) | CLEARSTEM, TINNIDROP | `FLUJO_LUCIDBOT.md` completo |
| etapa-8 (plan de escalado) | TINNIDROP | `4_PLAN_ESCALADO.txt` (extracto) |
| etapa-guardar-producto (invariante 8) | los 4 productos | manifiesto congelado de archivos de nivel superior en `PRODUCTOS/<P>/` |

**Sin output real guardado en disco, por lo que no tienen fixture (9 de 17):**

| Etapa | Por qué no hay output guardado |
|---|---|
| etapa-0 | Selección de 6 videos: vive en la sesión, se consume por etapa-2/etapa-6 y no se persiste como archivo propio. |
| etapa-3 | Su banco de 8-12 microángulos históricamente no aterrizaba en disco (ver T8 item 4); hoy solo se exige que `4_PLAN_ESCALADO.txt` contenga la palabra "MICROÁNGULO" para pasar el gate `F3.plan` de `flujo.py` — ningún producto real está hoy en ese nodo (T8 lo confirma), así que no hay un `4_PLAN_ESCALADO.txt` real con esa sección para congelar. |
| etapa-4 (copy) | El copy final se funde dentro de `1_HACER_MANUAL.txt` sin una sección delimitada que se pueda atribuir solo a esta etapa sin arrastrar contenido de etapa-5/etapa-6. |
| etapa-7 | Monitor de métricas: su output es la lectura de `_DECISIONES.json` en la conversación, no un archivo propio. |
| etapa-9 | Su output es la consola de la tanda del día (texto de sesión) + filas en `_DIM_CREATIVOS.csv` (dato, no prosa de etapa) — no hay un artefacto de texto libre guardado por tanda. |
| etapa-10 | Brief de lectura concepto↔métrica: se entrega en sesión a etapa-9, no se encontró un archivo propio persistido por producto. |
| etapa-11 | Brief de cierre del bot: mismo caso que etapa-10, output de sesión consumido por etapa-5. |
| etapa-render | Produce imágenes PNG, no texto — fuera del alcance de un assert de contrato textual/JSON. |

Si una futura sesión localiza un output real guardado para alguna de estas
nueve, se agrega su fixture + assert siguiendo el mismo patrón — este README
y `promptfooconfig.yaml` son quienes registran la cobertura real, no una lista
aparte.

## Fallos conocidos documentados (no se debilitó ningún assert para taparlos)

`etapa-6 / {CLEARSTEM, NusavaB12, TINNIDROP} — FASE 1 todo-en-imagen`: están
marcados `expected_fail: true` en `promptfooconfig.yaml`. Los tres `_PLAN.json`
son de antes de la decisión del operador del 22-sep-2026 ("FASE 1 corre TODO
EN IMAGEN") y tienen conjuntos en VIDEO — exactamente el mismo hallazgo que
hoy reporta `python Ads/_TOOLS/gen_plan.py --validar` (10 errores
`formato != IMAGEN` preexistentes, ver `odd/tasks/g07-cimientos.md` T10). El
assert se dejó estricto a propósito: relanzar cualquiera de esos productos
exige regenerar el plan desde etapa-6, no reescribir el eval para que pase.

## Protocolo de poda (para cuando se toque un prompt de ETAPA-*.md)

1. Correr `python evals/run_baseline.py` ANTES de tocar nada — confirma que
   arranca en verde (24/27, con los 3 fallos conocidos de arriba).
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
