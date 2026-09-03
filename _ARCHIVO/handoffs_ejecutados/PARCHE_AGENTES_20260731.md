# ⛔ SUPERSEDIDO — usar `HANDOFF_CLAUDE_CODE_20260731.md`

> Este archivo quedó absorbido entero por `_OPERADOR/HANDOFF_CLAUDE_CODE_20260731.md`,
> que además trae la regla del duplicado, el test de diversidad conceptual y los huecos
> de data. **No ejecutes este; ejecutá el handoff.** Se conserva solo como registro.

---

# PARCHE A LOS ARCHIVOS DE AGENTE — 2026-07-31

Pegá esto TAL CUAL en una sesión nueva de Claude sobre la carpeta SISTEMA.
Son 2 ediciones quirúrgicas a archivos que quedaron protegidos en la sesión donde se
derivó el cambio. La doctrina ya está escrita en `CLAUDE.md`; esto solo la baja a los
agentes que la ejecutan.

---

## PROMPT PARA PEGAR

```
Hacé 2 ediciones quirúrgicas en los archivos de agente. No reescribas nada más,
no reformatees, no toques otras secciones. Al terminar, confirmá con Read que
quedaron aplicadas.

═══════════════════════════════════════════════════════════════════
EDICIÓN 1 — .claude/agents/ETAPA-2.md
═══════════════════════════════════════════════════════════════════
En el bloque "AVATAR" de la ficha de ángulo (donde está "Nivel de conciencia:"),
INMEDIATAMENTE DESPUÉS de la línea "Nivel de conciencia: [...]", insertá:

CLASIFICACIÓN MEDIBLE (vocabulario CERRADO — obligatorio, va tal cual a `_DIM_CONJUNTOS.csv`)
avatar_genero: [MUJER / HOMBRE / MIXTO]
avatar_edad: [25-35 / 35-45 / 45-60 / 60+]   ← el bucket DOMINANTE, no el rango completo
emocion_dominante: [MIEDO_FUTURO / VERGUENZA / RESIGNACION / FRUSTRACION_MEDICA / DESCONFIANZA / AGOTAMIENTO / CURIOSIDAD]
> · MIEDO_FUTURO = teme que empeore o sea irreversible · VERGUENZA = lo esconde de los demás
> · RESIGNACION = ya se rindió, cree que no tiene arreglo · FRUSTRACION_MEDICA = pagó especialistas y sigue igual
> · DESCONFIANZA = teme que el producto sea falso o no funcione · AGOTAMIENTO = cansado, sin energía, no aguanta más
> · CURIOSIDAD = no sabía que su problema tenía esa causa (ángulos educacionales / mecanismo único)
>
> **POR QUÉ.** ETAPA-2 produce una ficha rica (perfil, situación, dolor activo, deseo, miedos,
> frustraciones) pero hasta ahora solo sobrevivían `avatar` y `dolor_nucleo` como TEXTO LIBRE —
> 28 y 33 valores distintos en 54 conjuntos, imposibles de agregar. Toda esa investigación se
> usaba para escribir el copy y DESPUÉS SE PERDÍA: nunca se contrastaba contra quién compró.
> Estos 3 campos, con vocabulario cerrado, son lo que la vuelve aprendible y TRANSFERIBLE
> ENTRE PRODUCTOS (si la vergüenza vende en várices, se prueba vergüenza en acné).
>
> ⚠️ **ANDROMEDA (2026):** Meta ya NO segmenta por audiencia — el CREATIVO ES EL TARGETING.
> Andromeda lee el anuncio y de ahí deduce a quién mostrárselo; la calidad del creativo explica
> ~56% del resultado (más que segmentación + presupuesto + placement juntos) y el algoritmo
> IGNORA la definición de audiencia si las señales del creativo apuntan a otro lado. El avatar
> ya no se controla desde la cajita de segmentación: se controla desde lo que el creativo DICE
> y a quién RETRATA. Medirlo es lo único que queda para saber a quién le hablás de verdad.
>
> **CONSULTAR ANTES DE PROPONER ÁNGULOS:** abrí `PRODUCTOS/_DASHBOARD.html` → sección
> «Por qué funciona — cada producto». Trae el CPA real por emoción, género y edad, de este
> producto y del portafolio entero. Si una emoción ya fracasó 2 veces en la categoría, NO la
> vuelvas a proponer. Si viene ganando en otro producto del mismo nicho, es candidata a probar.

═══════════════════════════════════════════════════════════════════
EDICIÓN 2 — .claude/agents/ETAPA-GUARDAR-PRODUCTO.md
═══════════════════════════════════════════════════════════════════
En la SALIDA 4 (`_DIM_CONJUNTOS.csv`):

(a) Reemplazá el bloque de columnas por este (agrega 3 columnas después de `avatar`):

producto_key, conjunto_meta, cuenta_alias, campana_clave, fase, angulo_key, angulo_nombre,
avatar, avatar_genero, avatar_edad, emocion_dominante, dolor_nucleo, formato, tipo_hook,
nivel_conciencia, rol_embudo, rol_embudo_origen,
lleva_precio, creativo_id, origen_angulo, estado, verificado_en_csv, fecha_alta, notas

(b) En "Vocabularios controlados", agregá estas 3 entradas:

- `avatar_genero`: MUJER · HOMBRE · MIXTO
- `avatar_edad`: 25-35 · 35-45 · 45-60 · 60+ — el bucket DOMINANTE, no el rango completo
- `emocion_dominante`: MIEDO_FUTURO · VERGUENZA · RESIGNACION · FRUSTRACION_MEDICA · DESCONFIANZA · AGOTAMIENTO · CURIOSIDAD
  Los declara ETAPA-2 en su ficha de ángulo. **Nunca dejarlos vacíos**: si un ángulo viejo no
  los trae, se rellenan leyendo su ficha en `2_DATA_PRODUCTO.txt`. Son lo que convierte la
  investigación de avatar en algo agregable — sin ellos el avatar muere en el copy y no se
  contrasta nunca contra quién compró. Con Andromeda pesan más que antes: el creativo es el
  targeting, así que el avatar solo se puede medir por lo que el creativo dice y retrata.

═══════════════════════════════════════════════════════════════════
NO TOQUES NADA MÁS. La justificación completa ya está en CLAUDE.md
(sección CAPA DE DATA → `_DIM_CONJUNTOS.csv`) y los 54 conjuntos existentes
ya están rellenados. Esto solo hace que los PRÓXIMOS productos lo traigan solos.
```

---

## VERIFICACIÓN (corré esto después)

```
python Ads/_TOOLS/gen_dashboard.py
```

Debe imprimir `0 filas sin dimension`. Y en el dashboard, la sección
«Por qué funciona — cada producto» debe mostrar la emoción dominante de cada producto.

## ESTADO AL 31-JUL (ya hecho, no repetir)
- ✅ `_DIM_CONJUNTOS.csv` — 3 columnas agregadas y los 54 conjuntos rellenados
- ✅ `CLAUDE.md` — doctrina completa en CAPA DE DATA
- ✅ `gen_dashboard.py` — cortes por emoción/género/edad, global y por producto
- ⬜ `ETAPA-2.md` — pendiente (EDICIÓN 1)
- ⬜ `ETAPA-GUARDAR-PRODUCTO.md` — pendiente (EDICIÓN 2)
