# Hoja de ruta — relanzar OVULOS_PURITY en GTR3 y registro sanitario pendiente (para el ejecutor)

Reglas del ejecutor: las de `_OPERADOR/HOJA_DE_RUTA_FINANZAS_2026-10-13.md` (Python del sistema, sin stash
ni cambio de rama, TDD, commits sin firma de IA, no push, preguntar ante cualquier decisión de negocio).

Ya hecho por el orquestador: `f04db5e` — OVULOS_PURITY pasó de EXTERNA a GTR3 (`581490137794343`, USD) en
`_DIM_PRODUCTOS.csv` con `cargar_cuenta.py`.

---

## TAREA 1 — Manual de FASE 1 de OVULOS para GTR3

**Problema:** `PRODUCTOS/OVULOS_PURITY/1_HACER_MANUAL.txt` sigue diciendo `EXTERNA_OVULOSPURITY_…` y presupuesto
en COP ($9.426/conjunto), porque los nombres y la plata salen del plan (`_PLAN.json` / `gen_lanzador.py`)
armado para EXTERNA. GTR3 es USD.

**Pasos:**
1. Leer cómo `gen_lanzador.py` y `gen_manual.py` derivan el prefijo del nombre (convención de
   `.claude/agents/ETAPA-6.md`) y la moneda/presupuesto (`_PARAMETROS_PUBLICACION.csv` fase 1 = $2.99 USD por
   conjunto; `_DIM_CUENTAS.csv` moneda de la cuenta).
2. Hacer que salgan de la cuenta ACTUAL del producto (`_DIM_PRODUCTOS.cuenta_alias` = GTR3), no de un valor
   guardado en el plan. Si el plan guarda la cuenta, regenerarlo con su escritor (`gen_plan.py`), nunca a mano.
   Mantener todo lo demás del plan igual (ángulos, copies, imágenes, edades, 2 anuncios por conjunto).
3. Los conjuntos viejos `EXTERNA_OVULOSPURITY_*` ya tienen historia (ventas de LucidSales, filas en
   `_DIM_CONJUNTOS.csv`). Los nuevos `GTR3_OVULOSPURITY_*` son conjuntos NUEVOS de los mismos ángulos: deben
   quedar en `_DIM_CONJUNTOS.csv` con el mismo `angulo_key` para que el ganador se agregue por ángulo
   (invariante 1). No usar `_ALIAS_CONJUNTOS.csv`: no es un renombre, es otra cuenta.
4. Regenerar `1_HACER_MANUAL.txt` con `gen_manual.py` y verificar: nombres `GTR3_OVULOSPURITY_<ANGULO>_R1`,
   presupuesto $2.99 USD por conjunto, mismas imágenes y copies.
5. `~/AppData/Local/Python/bin/python Ads/_TOOLS/flujo.py OVULOS_PURITY` no debe mostrar errores nuevos.
6. Confirmar con `bajar_meta_insights.py --dry-run` que, una vez creados, los conjuntos `GTR3_OVULOSPURITY_*`
   NO caerán como "sin-DIM excluidos" (es decir, que están en la dimensión).

**Commit:** `fix(lanzador): name and budget FASE 1 from the product's current account`

---

## TAREA 2 — Producto de Colombia sin número INVIMA todavía

**Problema:** la doctrina bloquea toda pieza de un producto CO sin número INVIMA
(`DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md`, `[REG_INVIMA]`; `Ads/_TOOLS/mercado.py` `registro_de_perfil`
lanza `RegistroFaltante`). El operador no tiene el número de OVULOS y lo está tramitando. Nunca se inventa ni
se reutiliza un número: lo correcto es que la pieza **no lleve sello de registro**, no que se frene.

**Regla (excepción por producto, no regla general):**
- Nueva columna en `PRODUCTOS/_DIM_PRODUCTOS.csv`: `registro_sanitario_estado` con valores `VIGENTE` (default,
  vacío = VIGENTE) o `EN_TRAMITE`.
- Con `EN_TRAMITE`, `registro_de_perfil` (o quien lo llame por producto) devuelve un registro vacío marcado
  `en_tramite=True` en vez de lanzar `RegistroFaltante`. Los generadores de piezas (`armar_prompts_fase2.py`,
  y cualquier otro que pida el registro — buscar con `rg "registro_de_perfil|RegistroFaltante"`) cambian la
  línea del registro por una instrucción explícita: "NO incluyas ningún sello ni número de registro
  sanitario". Nunca un número.
- Producto sin `EN_TRAMITE` y sin número: sigue bloqueando igual que hoy.
- Marcar OVULOS_PURITY como `EN_TRAMITE` con su escritor (o con `csv.DictWriter`), y documentar la excepción en
  `PLANTILLAS_DEFAULTS_OPERADOR.md` en la fila de `[REG_INVIMA]` (una frase, regla vigente).
- Tests: EN_TRAMITE → prompt sin sello y con la instrucción; sin EN_TRAMITE y sin número → sigue bloqueando;
  GT con MSPAS → sin cambios.

**Commit:** `feat(mercado): products with a pending sanitary registration ship without a seal`

---

## Al terminar

Reportar en pocas líneas: los 6 nombres de conjunto nuevos del manual, el presupuesto que quedó, y los commits.
No hacer push.
